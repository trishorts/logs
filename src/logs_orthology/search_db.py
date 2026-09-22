"""The resolution of one real search database, from both sources, side by side.

Input is the table ``tools/ResolveSearchDb`` writes with mzLib's ``EnsemblGeneResolver`` (links read
from the search XML's own ``<dbReference type="Ensembl">``, plus a per-gene ``ensembl_xref_agrees``
column). This module re-resolves the same base entries with ``resolve.py`` against Ensembl's xref
dump and reports:

* **the xref view** -- what ``005-logs`` sent ``aging`` (20,416 entries: 19,257 / 69 / 62 / 1,028);
* **the XML view** -- what the search database itself links (multi-gene is 350, because UniProt links
  readthrough genes, unnamed novel genes and identical paralogs too);
* **parity** -- per base entry, the C# genes the xref agrees with against ``resolve.py``'s genes.

Base entries are the proteins whose accession is itself a UniProt or RefSeq accession; the
sequence-variant proteoforms ``LoadProteinXML`` adds (``P12345_S70N``) are counted separately.

Run:
    dotnet run --project tools/ResolveSearchDb -c Release -- <search.xml> <gtf.gz> <uniprot.tsv.gz> <out.tsv>
    python -m logs_orthology.search_db <out.tsv> [--species mus_musculus --out results/search_db_resolution_mouse]
"""

from __future__ import annotations

import argparse
import collections
import csv
import datetime as _dt
import json
import sys
from pathlib import Path

from . import sources
from .fetch import project_root
from .resolve import XrefIndex, normalize, resolve

csv.field_size_limit(10_000_000)


def summarize(cs_table: Path, species: str = "homo_sapiens") -> dict:
    base_rows: dict[str, list[dict]] = collections.defaultdict(list)
    variants = 0
    sha = None
    with open(cs_table, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            sha = sha or r["search_database_sha256"]
            if normalize(r["accession"]).namespace == "unrecognized":
                variants += 1
                continue
            base_rows[r["accession"]].append(r)

    xml_outcome = {a: rows[0]["outcome"] for a, rows in base_rows.items()}
    agreeing = {a: {r["gene_id"] for r in rows if r["ensembl_xref_agrees"] == "true"} for a, rows in base_rows.items()}

    idx = XrefIndex.from_ensembl(species)
    xref_outcome, xref_genes = {}, {}
    for a in base_rows:
        rows = resolve(idx, a)
        xref_outcome[a] = rows[0].outcome
        xref_genes[a] = {r.gene_id for r in rows if r.gene_id}

    multi_by_agreeing = collections.Counter(
        len(agreeing[a]) for a, o in xml_outcome.items() if o == "multi_gene")
    identical = sum(1 for a in base_rows if agreeing[a] == xref_genes[a])
    both_nis = sum(1 for a in base_rows if xml_outcome[a] == xref_outcome[a] == "not_in_source")
    differ = [a for a in base_rows if agreeing[a] != xref_genes[a]]

    return {
        "species": species,
        "source_table": cs_table.name,
        "search_database_sha256": sha,
        "gene_set": f"Ensembl {sources.RELEASE} primary-assembly GTF",
        "generated": _dt.date.today().isoformat(),
        "base_entries": len(base_rows),
        "sequence_variant_rows": variants,
        "xref_view": dict(collections.Counter(xref_outcome.values())),
        "xml_view": dict(collections.Counter(xml_outcome.values())),
        "xml_multi_gene_by_xref_agreeing_genes": {str(k): v for k, v in sorted(multi_by_agreeing.items())},
        "not_in_source_in_both": both_nis,
        "xref_not_in_source_but_xml_resolves": sum(
            1 for a in base_rows if xref_outcome[a] == "not_in_source" and xml_outcome[a] in ("resolved", "multi_gene")),
        "xml_unresolved_but_xref_resolves": sum(
            1 for a in base_rows
            if xml_outcome[a] in ("not_in_source", "off_primary_only") and xref_outcome[a] in ("resolved", "multi_gene")),
        "parity_identical": identical,
        "parity_differ": len(base_rows) - identical,
        "parity_differ_xml_has_no_ensembl_link": sum(1 for a in differ if xml_outcome[a] == "not_in_source"),
    }


def render(s: dict) -> str:
    xv, mv = s["xref_view"], s["xml_view"]
    order = ("resolved", "multi_gene", "off_primary_only", "not_in_source")
    L = [
        "# Search-database resolution: both sources side by side",
        "",
        f"Generated {s['generated']} from `{s['source_table']}` (mzLib `EnsemblGeneResolver`), search database "
        f"sha256 `{s['search_database_sha256']}`, against the {s['gene_set']}.",
        "",
        f"**{s['base_entries']:,} base entries** ({s['sequence_variant_rows']:,} further rows are sequence-variant "
        "proteoforms, resolved through their entry and not counted here).",
        "",
        f"| outcome | Ensembl xref{' (sent in 005-logs)' if s.get('species', 'homo_sapiens') == 'homo_sapiens' else ''} | search XML's own links |",
        "|---|---:|---:|",
        *[f"| `{o}` | {xv.get(o, 0):,} | {mv.get(o, 0):,} |" for o in order],
        "",
        "The multi-gene difference is not an error in either source. UniProt links an accession to every "
        "Ensembl transcript encoding it (readthrough genes, unnamed novel genes, identical paralogs); "
        "Ensembl's xref assigns it where Ensembl's mapping puts it. Every gene row carries "
        "`ensembl_xref_agrees`, so neither is dropped:",
        "",
        "| XML multi-gene accessions, by number of genes the xref agrees with | accessions |",
        "|---|---:|",
        *[f"| {k} | {v:,} |" for k, v in s["xml_multi_gene_by_xref_agreeing_genes"].items()],
        "",
        f"No gene id in either source: **{s['not_in_source_in_both']:,}**. "
        f"No xref gene but the XML links one (UniProt/Ensembl drift): **{s['xref_not_in_source_but_xml_resolves']:,}**. "
        f"The reverse, the xref resolves an entry whose XML links no gene in the set: "
        f"**{s['xml_unresolved_but_xref_resolves']:,}**.",
        "",
        f"**Parity:** for {s['parity_identical']:,} of {s['base_entries']:,} base entries, the genes the xref agrees "
        f"with are exactly the genes `resolve.py` finds; " + (
            f"the {s['parity_differ']:,} others are entries whose XML carries no Ensembl link at all."
            if s["parity_differ_xml_has_no_ensembl_link"] == s["parity_differ"] else
            f"of the {s['parity_differ']:,} others, {s['parity_differ_xml_has_no_ensembl_link']:,} are entries whose "
            "XML carries no Ensembl link at all and the rest disagree on the genes themselves."),
        "",
    ]
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("table", type=Path, help="output of tools/ResolveSearchDb")
    ap.add_argument("--species", default="homo_sapiens", choices=sorted(sources.TAXA))
    ap.add_argument("--out", default="results/search_db_resolution")
    args = ap.parse_args(argv)
    s = summarize(args.table, args.species)
    stem = project_root() / args.out
    stem.with_suffix(".json").write_text(json.dumps(s, indent=2), encoding="utf-8")
    stem.with_suffix(".md").write_text(render(s), encoding="utf-8")
    print(json.dumps({k: s[k] for k in ("base_entries", "xref_view", "xml_view", "parity_identical")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
