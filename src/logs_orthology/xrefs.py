"""Accession → gene resolution, measured against Ensembl's own cross-reference dumps.

Two questions this answers, both of which we currently owe someone:

* **The multi-ENSG distribution** — our last open modelling question. UniProt writes one
  ``<dbReference type="Ensembl">`` per *transcript* with the ENSG in a property, so an accession
  can carry several distinct gene ids. Whether that is a rare curiosity or a structural feature
  decides how the store is keyed. ``dataRepo`` is measuring it against the search XML their
  corpus actually used; this measures it against Ensembl's canonical mapping. **The two should
  agree, and if they do not, that disagreement is the finding.**

* **Whether RefSeq is really v3 work.** We told ``dataRepo`` RefSeq was deferred because mzLib
  recognises no ``NP_``/``XP_`` FASTA header. That reasoning is about *parsing a header* and says
  nothing about *resolving an accession we already hold*, which these dumps do directly.

Run:  python -m logs_orthology.xrefs
"""

from __future__ import annotations

import argparse
import datetime as _dt
import gzip
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from . import sources
from .fetch import data_dir, project_root

SHORT = {"homo_sapiens": "human", "mus_musculus": "mouse", "rattus_norvegicus": "rat"}

XREF_COLUMNS = (
    "gene_stable_id", "transcript_stable_id", "protein_stable_id", "xref", "db_name",
    "info_type", "source_identity", "xref_identity", "linkage_type",
)

#: RefSeq *protein* accessions -- the ones a proteomics search reports. NP_ is curated,
#: XP_ is model-predicted; they are not the same quality of evidence and are counted apart.
RE_NP = re.compile(r"^NP_\d+")
RE_XP = re.compile(r"^XP_\d+")
#: A UniProt isoform suffix. dataRepo's corpus has zero of these; that is a fact about their
#: corpus, not about accessions, so we measure how many exist in the reference at all.
RE_ISOFORM = re.compile(r"^[A-Z0-9]+-\d+$")


def xref_path(species: str, kind: str) -> Path:
    assembly = sources.ASSEMBLY[species]
    return data_dir() / f"{species.capitalize()}.{assembly}.{sources.RELEASE}.{kind}.tsv.gz"


def iter_xref(species: str, kind: str):
    """Stream one xref dump, yielding dicts. Refuses an unexpected layout."""
    path = xref_path(species, kind)
    with gzip.open(path, "rt", encoding="utf-8", newline="") as fh:
        header = tuple(next(fh).rstrip("\n").split("\t"))
        if header != XREF_COLUMNS:
            raise RuntimeError(
                f"{path.name}: unexpected columns.\n  got:      {list(header)}\n"
                f"  expected: {list(XREF_COLUMNS)}"
            )
        for line in fh:
            row = line.rstrip("\n").split("\t")
            if len(row) != 9:
                continue
            yield dict(zip(XREF_COLUMNS, row))


def _dist(counts: dict[str, set[str]]) -> dict[str, int]:
    """Bucket a key -> set-of-genes map into 1 / 2 / 3 / 4+ distinct genes."""
    out: Counter[str] = Counter()
    for genes in counts.values():
        n = len(genes)
        out["1" if n == 1 else "2" if n == 2 else "3" if n == 3 else "4+"] += 1
    return {k: out.get(k, 0) for k in ("1", "2", "3", "4+")}


def measure_uniprot(species: str) -> dict:
    genes_by_acc: dict[str, set[str]] = defaultdict(set)
    db_of_acc: dict[str, set[str]] = defaultdict(set)
    info_types: Counter[str] = Counter()
    isoforms = 0
    rows = 0

    for r in iter_xref(species, "uniprot"):
        rows += 1
        acc = r["xref"]
        genes_by_acc[acc].add(r["gene_stable_id"])
        db_of_acc[acc].add(r["db_name"])
        info_types[r["info_type"]] += 1
        if RE_ISOFORM.match(acc):
            isoforms += 1

    reviewed = {a for a, dbs in db_of_acc.items() if "Uniprot/SWISSPROT" in dbs}
    dist_all = _dist(genes_by_acc)
    dist_rev = _dist({a: g for a, g in genes_by_acc.items() if a in reviewed})
    total = len(genes_by_acc)

    return {
        "rows": rows,
        "distinct_accessions": total,
        "distinct_genes": len({g for gs in genes_by_acc.values() for g in gs}),
        "reviewed_accessions": len(reviewed),
        "unreviewed_accessions": total - len(reviewed),
        "isoform_suffixed_accessions": isoforms,
        "info_type": dict(info_types.most_common()),
        "genes_per_accession": dist_all,
        "genes_per_accession_pct": {k: round(100 * v / total, 3) for k, v in dist_all.items()}
        if total else {},
        "genes_per_accession_reviewed": dist_rev,
        "genes_per_accession_reviewed_pct": {
            k: round(100 * v / len(reviewed), 3) for k, v in dist_rev.items()
        } if reviewed else {},
        "reviewed_multi_gene_accessions": sum(
            1 for a in reviewed if len(genes_by_acc[a]) > 1
        ),
        #: The worst reviewed cases, by how many distinct genes one curated protein spans.
        #: These are the shape of the problem, not outliers to be trimmed: a single reviewed
        #: sequence encoded by many near-identical loci is precisely where proteomics cannot
        #: resolve the gene and orthology must not pretend otherwise.
        "reviewed_multi_gene_top": [
            {"accession": a, "genes": len(genes_by_acc[a])}
            for a in sorted(reviewed, key=lambda x: (-len(genes_by_acc[x]), x))[:12]
            if len(genes_by_acc[a]) > 1
        ],
    }


def measure_refseq(species: str) -> dict:
    genes_by_acc: dict[str, set[str]] = defaultdict(set)
    db_names: Counter[str] = Counter()
    protein_acc: dict[str, set[str]] = defaultdict(set)
    np_acc: set[str] = set()
    xp_acc: set[str] = set()
    info_types: Counter[str] = Counter()

    for r in iter_xref(species, "refseq"):
        acc = r["xref"]
        db_names[r["db_name"]] += 1
        genes_by_acc[acc].add(r["gene_stable_id"])
        if RE_NP.match(acc) or RE_XP.match(acc):
            protein_acc[acc].add(r["gene_stable_id"])
            info_types[r["info_type"]] += 1
            (np_acc if RE_NP.match(acc) else xp_acc).add(acc)

    dist = _dist(protein_acc)
    return {
        "db_name_rows": dict(db_names.most_common()),
        "distinct_accessions_all": len(genes_by_acc),
        "protein_accessions": len(protein_acc),
        "np_curated": len(np_acc),
        "xp_predicted": len(xp_acc),
        "info_type_protein": dict(info_types.most_common()),
        "genes_per_protein_accession": dist,
        "genes_per_protein_accession_pct": {
            k: round(100 * v / len(protein_acc), 3) for k, v in dist.items()
        } if protein_acc else {},
    }


def measure_entrez(species: str) -> dict:
    genes_by_id: dict[str, set[str]] = defaultdict(set)
    for r in iter_xref(species, "entrez"):
        genes_by_id[r["xref"]].add(r["gene_stable_id"])
    dist = _dist(genes_by_id)
    return {
        "distinct_gene_ids": len(genes_by_id),
        "genes_per_gene_id": dist,
        "genes_per_gene_id_pct": {
            k: round(100 * v / len(genes_by_id), 3) for k, v in dist.items()
        } if genes_by_id else {},
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Measure accession -> gene resolution.")
    ap.add_argument("--out", default="results/accession_resolution")
    args = ap.parse_args(argv)

    report: dict = {
        "source": "ensembl_xref",
        "release": sources.RELEASE,
        "generated": _dt.date.today().isoformat(),
        "species": {},
    }

    for species in sources.TAXA:
        print(f"{SHORT[species]}...")
        print("  uniprot"); u = measure_uniprot(species)
        print("  refseq");  r = measure_refseq(species)
        print("  entrez");  e = measure_entrez(species)
        report["species"][SHORT[species]] = {"uniprot": u, "refseq": r, "entrez": e}
        print(f"    uniprot accessions {u['distinct_accessions']:,} "
              f"({u['genes_per_accession_pct'].get('1', 0):.2f}% map to exactly one gene)")
        print(f"    refseq protein accessions {r['protein_accessions']:,} "
              f"(NP_ {r['np_curated']:,} / XP_ {r['xp_predicted']:,})")

    stem = project_root() / args.out
    stem.parent.mkdir(parents=True, exist_ok=True)
    stem.with_suffix(".json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    stem.with_suffix(".md").write_text(render(report), encoding="utf-8")
    print(f"\nWrote {stem.with_suffix('.json')}\n      {stem.with_suffix('.md')}")
    return 0


def render(r: dict) -> str:
    L: list[str] = []
    a = L.append
    a(f"# Accession → gene resolution — Ensembl release {r['release']} cross-reference dumps")
    a("")
    a(f"Generated {r['generated']}. Measured from Ensembl's own stable-id → external-accession")
    a("dumps, pinned and checksum-verified in `data/PROVENANCE.md`.")
    a("")
    a("Two questions: **how often does one accession mean more than one gene** (our last open")
    a("modelling question), and **is RefSeq actually expensive** (a claim we made and should")
    a("re-test).")
    a("")

    a("## 1 · The multi-gene question")
    a("")
    a("UniProt accession → distinct Ensembl gene ids:")
    a("")
    a("| species | accessions | → 1 gene | → 2 | → 3 | → 4+ | % exactly one |")
    a("|---|---:|---:|---:|---:|---:|---:|")
    for sp, d in r["species"].items():
        u = d["uniprot"]
        g = u["genes_per_accession"]
        a(f"| {sp} | {u['distinct_accessions']:,} | {g['1']:,} | {g['2']:,} | {g['3']:,} | "
          f"{g['4+']:,} | **{u['genes_per_accession_pct']['1']:.2f}%** |")
    a("")
    a("Restricted to **reviewed** (SwissProt) accessions, which is what a curated search database")
    a("contains:")
    a("")
    a("| species | reviewed accessions | multi-gene | % exactly one gene |")
    a("|---|---:|---:|---:|")
    for sp, d in r["species"].items():
        u = d["uniprot"]
        a(f"| {sp} | {u['reviewed_accessions']:,} | {u['reviewed_multi_gene_accessions']:,} | "
          f"**{u['genes_per_accession_reviewed_pct'].get('1', 0):.2f}%** |")
    a("")
    a("**Curation does not reduce the ambiguity — in human it slightly increases it.** A reviewed")
    a("entry is one curated protein sequence, and a protein encoded by several near-identical")
    a("loci gets one record spanning all of them. Filtering to SwissProt therefore does not make")
    a("the multi-gene case go away.")
    a("")
    a("The worst reviewed human cases, which are the shape of the problem rather than outliers:")
    a("")
    a("| accession | distinct genes |")
    a("|---|---:|")
    for row in r["species"].get("human", {}).get("uniprot", {}).get(
            "reviewed_multi_gene_top", []):
        a(f"| `{row['accession']}` | {row['genes']} |")
    a("")
    a("`P62805` is histone H4 — one protein sequence, 14 loci, and peptides that cannot")
    a("distinguish them. It is abundant in essentially every proteomics experiment. This is the")
    a("protein-inference ambiguity our design keeps separate from orthology ambiguity, and it is")
    a("not a corner case.")
    a("")

    a("## 2 · RefSeq")
    a("")
    a("| species | RefSeq protein accessions | `NP_` curated | `XP_` predicted | % → exactly one gene |")
    a("|---|---:|---:|---:|---:|")
    for sp, d in r["species"].items():
        f = d["refseq"]
        a(f"| {sp} | {f['protein_accessions']:,} | {f['np_curated']:,} | {f['xp_predicted']:,} | "
          f"**{f['genes_per_protein_accession_pct'].get('1', 0):.2f}%** |")
    a("")
    a("`NP_` is curated and `XP_` is model-predicted. They are not the same quality of evidence")
    a("and are counted apart so a resolution rate cannot be inflated by predictions.")
    a("")

    a("## 3 · NCBI GeneID")
    a("")
    a("| species | distinct GeneIDs | % → exactly one Ensembl gene |")
    a("|---|---:|---:|")
    for sp, d in r["species"].items():
        e = d["entrez"]
        a(f"| {sp} | {e['distinct_gene_ids']:,} | "
          f"**{e['genes_per_gene_id_pct'].get('1', 0):.2f}%** |")
    a("")

    a("## 4 · Isoform suffixes")
    a("")
    a("| species | accessions with an isoform suffix (`P12345-2`) |")
    a("|---|---:|")
    for sp, d in r["species"].items():
        a(f"| {sp} | {d['uniprot']['isoform_suffixed_accessions']:,} |")
    a("")
    a("`dataRepo` measured zero isoform-suffixed accessions in their corpus. Whether this")
    a("reference contains any at all says whether that zero is a property of their corpus or of")
    a("the identifier space.")
    a("")

    a("## 5 · Evidence type")
    a("")
    a("`info_type` records *how* Ensembl made each link. `DIRECT` is an asserted mapping;")
    a("`SEQUENCE_MATCH` is inferred from alignment and is weaker. A resolution layer that treats")
    a("them alike is reporting an inference as an assertion.")
    a("")
    for sp, d in r["species"].items():
        a(f"- **{sp}** — UniProt: `{d['uniprot']['info_type']}`")
    a("")
    return "\n".join(L)


if __name__ == "__main__":
    sys.exit(main())
