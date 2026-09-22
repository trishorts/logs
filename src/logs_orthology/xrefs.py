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
from .load import load_gene_set

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
    """Bucket a key -> set-of-genes map into 0 / 1 / 2 / 3 / 4+ distinct genes.

    **The zero bucket is not decoration.** An accession that resolves to no gene in the set we
    are measuring against is a real outcome, and an earlier version of this function let ``n=0``
    fall through the chain into ``4+`` — turning "resolved to nothing" into "maximally
    ambiguous", which is the worst possible direction for that error to go.
    """
    out: Counter[str] = Counter()
    for genes in counts.values():
        n = len(genes)
        out["0" if n == 0 else "1" if n == 1 else "2" if n == 2 else "3" if n == 3 else "4+"] += 1
    return {k: out.get(k, 0) for k in ("0", "1", "2", "3", "4+")}


def measure_uniprot(species: str, primary: set[str]) -> dict:
    """Accession → gene, counted against the **primary assembly** gene set.

    ``primary`` is the set of gene ids in the primary-assembly GTF. Restricting to it is not a
    detail — it is the difference between a real answer and a wrong one.

    Ensembl's xref dumps reference genes on ALT haplotypes and patches. A locus such as KIR is
    represented on many alternate haplotypes, so one curated protein appears to map to two dozen
    "genes" that are the same gene described repeatedly. Measured on human release 116, counting
    raw gene ids puts the multi-gene rate at **6.99%**; counting primary-assembly genes puts it
    at **0.36%** — a twentyfold difference, and the unrestricted number is the wrong one.

    The effect is human-only here (mouse and rat xrefs reference no off-primary genes at all), so
    an unrestricted measurement also invents a species difference that does not exist.
    """
    genes_by_acc: dict[str, set[str]] = defaultdict(set)
    raw_by_acc: dict[str, set[str]] = defaultdict(set)
    db_of_acc: dict[str, set[str]] = defaultdict(set)
    info_types: Counter[str] = Counter()
    isoform_rows = 0
    isoform_accs: set[str] = set()
    rows = 0
    off_primary_genes: set[str] = set()

    for r in iter_xref(species, "uniprot"):
        rows += 1
        acc, gene = r["xref"], r["gene_stable_id"]
        raw_by_acc[acc].add(gene)
        if gene in primary:
            genes_by_acc[acc].add(gene)
        else:
            off_primary_genes.add(gene)
        db_of_acc[acc].add(r["db_name"])
        info_types[r["info_type"]] += 1
        if RE_ISOFORM.match(acc):
            isoform_rows += 1
            isoform_accs.add(acc)

    # Accessions that exist only off the primary assembly resolve to nothing here. That is a real
    # outcome and gets its own count rather than quietly becoming a "1".
    for acc in raw_by_acc:
        genes_by_acc.setdefault(acc, set())

    reviewed = {a for a, dbs in db_of_acc.items() if "Uniprot/SWISSPROT" in dbs}
    dist_all = _dist(genes_by_acc)
    dist_rev = _dist({a: g for a, g in genes_by_acc.items() if a in reviewed})
    dist_rev_raw = _dist({a: g for a, g in raw_by_acc.items() if a in reviewed})
    total = len(genes_by_acc)

    return {
        "rows": rows,
        "distinct_accessions": total,
        "distinct_genes": len({g for gs in genes_by_acc.values() for g in gs}),
        "reviewed_accessions": len(reviewed),
        "unreviewed_accessions": total - len(reviewed),
        # DISTINCT accessions. Until 2026-09-22 this key held the ROW count (one row per
        # transcript), and 007-logs reported that row count as accessions: 35,202 rows is 25,177
        # accessions. Corrected in 008-logs; the row count is kept under its own, honest name.
        "isoform_suffixed_accessions": len(isoform_accs),
        "isoform_suffixed_rows": isoform_rows,
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
        "reviewed_resolving_to_nothing": sum(1 for a in reviewed if not genes_by_acc[a]),
        # The same distribution computed WITHOUT the primary-assembly restriction, kept so the
        # size of the ALT/patch artifact is visible rather than merely corrected away.
        "genes_per_accession_reviewed_unrestricted": dist_rev_raw,
        "off_primary_genes_referenced": len(off_primary_genes),
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


def measure_refseq(species: str, primary: set[str]) -> dict:
    genes_by_acc: dict[str, set[str]] = defaultdict(set)
    db_names: Counter[str] = Counter()
    protein_acc: dict[str, set[str]] = defaultdict(set)
    np_acc: set[str] = set()
    xp_acc: set[str] = set()
    info_types: Counter[str] = Counter()

    for r in iter_xref(species, "refseq"):
        acc = r["xref"]
        db_names[r["db_name"]] += 1
        gene = r["gene_stable_id"]
        if gene in primary:
            genes_by_acc[acc].add(gene)
        if RE_NP.match(acc) or RE_XP.match(acc):
            protein_acc.setdefault(acc, set())
            if gene in primary:
                protein_acc[acc].add(gene)
            info_types[r["info_type"]] += 1
            (np_acc if RE_NP.match(acc) else xp_acc).add(acc)

    dist = _dist(protein_acc)
    # NP_ and XP_ separately. 007-logs quoted the COMBINED single-gene rate (96.90%) against the
    # NP_ count, as if it were the curated rate; curated NP_ alone is far cleaner. The combined
    # figure stays because it is what the table in 007 actually showed.
    dist_np = _dist({a: g for a, g in protein_acc.items() if a in np_acc})
    dist_xp = _dist({a: g for a, g in protein_acc.items() if a in xp_acc})
    info_np: Counter[str] = Counter()
    info_xp: Counter[str] = Counter()
    for r in iter_xref(species, "refseq"):
        if RE_NP.match(r["xref"]):
            info_np[r["info_type"]] += 1
        elif RE_XP.match(r["xref"]):
            info_xp[r["info_type"]] += 1
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
        "genes_per_np_accession": dist_np,
        "genes_per_np_accession_pct": {
            k: round(100 * v / len(np_acc), 3) for k, v in dist_np.items()
        } if np_acc else {},
        "genes_per_xp_accession": dist_xp,
        "genes_per_xp_accession_pct": {
            k: round(100 * v / len(xp_acc), 3) for k, v in dist_xp.items()
        } if xp_acc else {},
        "info_type_np": dict(info_np.most_common()),
        "info_type_xp": dict(info_xp.most_common()),
    }


def measure_entrez(species: str, primary: set[str]) -> dict:
    genes_by_id: dict[str, set[str]] = defaultdict(set)
    for r in iter_xref(species, "entrez"):
        genes_by_id.setdefault(r["xref"], set())
        if r["gene_stable_id"] in primary:
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
        print("  gene set (primary assembly)")
        primary = set(load_gene_set(species))
        print("  uniprot"); u = measure_uniprot(species, primary)
        print("  refseq");  r = measure_refseq(species, primary)
        print("  entrez");  e = measure_entrez(species, primary)
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

    a("## 0 · A correction, stated before the numbers")
    a("")
    a("An earlier version of this measurement counted **every** gene id in the xref dump. Ensembl")
    a("references genes on ALT haplotypes and patches, where a locus such as KIR appears on many")
    a("alternate haplotypes — so one curated protein looked as though it mapped to two dozen")
    a("genes that are in fact the same gene described repeatedly.")
    a("")
    h = r["species"].get("human", {}).get("uniprot", {})
    if h:
        raw = h.get("genes_per_accession_reviewed_unrestricted", {})
        rev = h.get("genes_per_accession_reviewed", {})
        nrev = h.get("reviewed_accessions", 0)
        multi_raw = sum(v for k, v in raw.items() if k not in ("0", "1"))
        multi_pri = sum(v for k, v in rev.items() if k not in ("0", "1"))
        a("| reviewed human accessions | multi-gene | rate |")
        a("|---|---:|---:|")
        a(f"| counting every gene id | {multi_raw:,} | **{100*multi_raw/nrev:.2f}%** |")
        a(f"| counting primary-assembly genes | {multi_pri:,} | **{100*multi_pri/nrev:.2f}%** |")
        a("")
        a(f"**{multi_raw - multi_pri:,} of the {multi_raw:,} apparent multi-gene cases were ALT or")
        a("patch duplicates.** Everything below counts primary-assembly genes only. The effect is")
        a(f"human-specific — the human xref dump references {h.get('off_primary_genes_referenced', 0):,}")
        a("off-primary genes while mouse and rat reference none — so the unrestricted measurement")
        a("also invented a species difference that does not exist.")
        a("")

    a("## 1 · The multi-gene question")
    a("")
    a("UniProt accession → distinct **primary-assembly** Ensembl gene ids:")
    a("")
    a("| species | accessions | → 0 | → 1 | → 2 | → 3 | → 4+ | % exactly one |")
    a("|---|---:|---:|---:|---:|---:|---:|---:|")
    for sp, d in r["species"].items():
        u = d["uniprot"]
        g = u["genes_per_accession"]
        a(f"| {sp} | {u['distinct_accessions']:,} | {g['0']:,} | {g['1']:,} | {g['2']:,} | "
          f"{g['3']:,} | {g['4+']:,} | **{u['genes_per_accession_pct']['1']:.2f}%** |")
    a("")
    a("Restricted to **reviewed** (SwissProt) accessions, which is what a curated search database")
    a("contains:")
    a("")
    a("| species | reviewed | multi-gene | resolving to nothing | % exactly one |")
    a("|---|---:|---:|---:|---:|")
    for sp, d in r["species"].items():
        u = d["uniprot"]
        a(f"| {sp} | {u['reviewed_accessions']:,} | {u['reviewed_multi_gene_accessions']:,} | "
          f"{u['reviewed_resolving_to_nothing']:,} | "
          f"**{u['genes_per_accession_reviewed_pct'].get('1', 0):.2f}%** |")
    a("")
    a("**The multi-gene case is rare — well under 1% — but it is not evenly spread.** The genuine")
    a("cases are almost entirely histone clusters and a few cancer/testis antigen families: one")
    a("protein sequence genuinely encoded by many loci on the primary assembly.")
    a("")
    a("The worst genuine reviewed human cases:")
    a("")
    a("| accession | distinct primary genes |")
    a("|---|---:|")
    for row in r["species"].get("human", {}).get("uniprot", {}).get(
            "reviewed_multi_gene_top", []):
        a(f"| `{row['accession']}` | {row['genes']} |")
    a("")
    a("`P62805` is histone H4 — one protein sequence, 14 real loci, peptides that cannot")
    a("distinguish them, and abundant in essentially every proteomics experiment. So although the")
    a("*rate* is below 1%, the affected proteins are not obscure. A rare class with high abundance")
    a("is exactly the one a sampled test set will miss.")
    a("")
    a("## 2 · RefSeq")
    a("")
    a("| species | RefSeq protein accessions | `NP_` curated | `NP_` → one gene | `XP_` predicted "
      "| `XP_` → one gene | combined → one gene |")
    a("|---|---:|---:|---:|---:|---:|---:|")
    for sp, d in r["species"].items():
        f = d["refseq"]
        a(f"| {sp} | {f['protein_accessions']:,} | {f['np_curated']:,} | "
          f"**{f['genes_per_np_accession_pct'].get('1', 0):.2f}%** | {f['xp_predicted']:,} | "
          f"{f['genes_per_xp_accession_pct'].get('1', 0):.2f}% | "
          f"{f['genes_per_protein_accession_pct'].get('1', 0):.2f}% |")
    a("")
    a("`NP_` is curated and `XP_` is model-predicted. They are not the same quality of evidence")
    a("and are counted apart so a resolution rate cannot be inflated -- or deflated -- by")
    a("predictions. **Correction (008-logs):** 007-logs quoted the combined human rate, 96.90%,")
    a("against the `NP_` count as though it were the curated rate. It is not; see the `NP_` column.")
    a("")
    a("How each link was made, by accession class (xref rows, i.e. per transcript):")
    a("")
    a("| species | class | " + " | ".join(("DIRECT", "SEQUENCE_MATCH", "INFERRED_PAIR")) + " |")
    a("|---|---|---:|---:|---:|")
    for sp, d in r["species"].items():
        f = d["refseq"]
        for cls, key in (("`NP_`", "info_type_np"), ("`XP_`", "info_type_xp")):
            c = f.get(key, {})
            a(f"| {sp} | {cls} | " + " | ".join(f"{c.get(t, 0):,}" for t in
                                              ("DIRECT", "SEQUENCE_MATCH", "INFERRED_PAIR")) + " |")
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
    a("| species | distinct accessions with an isoform suffix (`P12345-2`) | xref rows |")
    a("|---|---:|---:|")
    for sp, d in r["species"].items():
        u = d["uniprot"]
        a(f"| {sp} | **{u['isoform_suffixed_accessions']:,}** | {u.get('isoform_suffixed_rows', 0):,} |")
    a("")
    a("**Correction (008-logs):** 007-logs reported the row count (one row per transcript) as")
    a("the accession count.")
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
