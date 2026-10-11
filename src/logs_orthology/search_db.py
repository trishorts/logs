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

With ``--xml`` (the search XML the table was resolved from), the entries are also split by UniProt
dataset (Swiss-Prot / TrEMBL), by whether they name a primary gene, and by whether they carry an
Ensembl ``dbReference`` (PXReprise 006, PXR-O6: canonical proteomes mix the two datasets).

Run:
    dotnet run --project tools/ResolveSearchDb -c Release -- <search.xml> <gtf.gz> <uniprot.tsv.gz> <out.tsv>
    python -m logs_orthology.search_db <out.tsv> [--species mus_musculus --out results/search_db_resolution_mouse]
                                                 [--xml <search.xml>]
"""

from __future__ import annotations

import argparse
import collections
import csv
import datetime as _dt
import json
import re
import sys
from pathlib import Path

from . import sources
from .fetch import project_root
from .resolve import XrefIndex, normalize, resolve

csv.field_size_limit(10_000_000)

_DATASET = re.compile(r'<entry\b[^>]*\bdataset="([^"]+)"')
_CREATED = re.compile(r'<entry\b[^>]*\bcreated="(\d{4})')


def scan_entries(xml: Path) -> dict[str, dict]:
    """Per UniProt entry, keyed by its first accession: its dataset, the year UniProt created it,
    whether its ``<gene>`` has a primary name, and whether it carries an Ensembl ``dbReference``.
    Reads the XML line by line, as UniProt writes it; ``type="primary"`` occurs only on gene names."""
    out: dict[str, dict] = {}
    cur = None
    with open(xml, encoding="utf-8") as fh:
        for line in fh:
            s = line.lstrip()
            if s.startswith("<entry"):
                m, c = _DATASET.match(s), _CREATED.match(s)
                cur, acc = {"dataset": m.group(1) if m else None, "created": c.group(1) if c else None,
                            "primary_gene_name": False, "ensembl_dbreference": False}, None
            elif cur is None:
                continue
            elif s.startswith("<accession>") and acc is None:
                acc = s[len("<accession>"):s.index("<", len("<accession>"))]
                out[acc] = cur
            elif s.startswith("<name") and 'type="primary"' in s:
                cur["primary_gene_name"] = True
            elif s.startswith('<dbReference type="Ensembl"'):
                cur["ensembl_dbreference"] = True
            elif s.startswith("</entry>"):
                cur = None
    return out


def _by_dataset(entries: dict[str, dict], agreeing: dict[str, set], xml_outcome: dict[str, str],
                xref_outcome: dict[str, str]) -> dict:
    """Coverage per UniProt dataset. ``agrees_view`` counts genes the Ensembl xref agrees with
    (the v1 view, CLAUDE.md trap 19), never ``outcome``."""
    out = {}
    for ds in sorted({e["dataset"] for e in entries.values()}):
        accs = [a for a, e in entries.items() if e["dataset"] == ds]
        no_name = [a for a in accs if not entries[a]["primary_gene_name"]]
        no_ens = [a for a in accs if not entries[a]["ensembl_dbreference"]]
        neither = [a for a in accs if not entries[a]["primary_gene_name"] and not entries[a]["ensembl_dbreference"]]
        silent = [a for a in accs if _xref_silent_xml_resolves(a, xml_outcome, xref_outcome)]
        out[ds] = {
            "entries": len(accs),
            "agrees_view": {"one_gene": sum(len(agreeing[a]) == 1 for a in accs),
                            "several_genes": sum(len(agreeing[a]) > 1 for a in accs),
                            "no_gene": sum(not agreeing[a] for a in accs)},
            "xml_view": dict(collections.Counter(xml_outcome[a] for a in accs)),
            "xref_view": dict(collections.Counter(xref_outcome[a] for a in accs)),
            "no_primary_gene_name": {"entries": len(no_name), "with_agreeing_gene": sum(bool(agreeing[a]) for a in no_name),
                                     "xml_view": dict(collections.Counter(xml_outcome[a] for a in no_name))},
            "no_ensembl_dbreference": {"entries": len(no_ens), "with_agreeing_gene": sum(bool(agreeing[a]) for a in no_ens)},
            "neither": {"entries": len(neither), "with_agreeing_gene": sum(bool(agreeing[a]) for a in neither)},
            "xref_silent_xml_resolves": {"entries": len(silent),
                                         "created": dict(sorted(collections.Counter(entries[a]["created"] for a in silent).items()))},
        }
    return out


def _xref_silent_xml_resolves(a: str, xml_outcome: dict[str, str], xref_outcome: dict[str, str]) -> bool:
    """Ensembl's xref does not know the accession at all (``not_in_source``: silent, not a
    disagreement), and the search XML links it to a gene in the set."""
    return xref_outcome[a] == "not_in_source" and xml_outcome[a] in ("resolved", "multi_gene")


def summarize(cs_table: Path, species: str = "homo_sapiens", xml: Path | None = None) -> dict:
    base_rows: dict[str, list[dict]] = collections.defaultdict(list)
    variants = 0
    sha = None
    with open(cs_table, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            sha = sha or r["search_database_sha256"]
            if normalize(r["accession"]).variant is not None:
                # A proteoform's own rows, not the genes the xref adds to it.
                variants += r["source"] != "ensembl_xref"
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

    extra = {}
    if xml is not None:
        entries = scan_entries(xml)
        if set(entries) != set(base_rows):
            raise SystemExit(f"{xml.name}: {len(entries):,} entries but {len(base_rows):,} base entries in "
                             f"{cs_table.name}; the table was not resolved from this XML")
        extra = {"search_xml": xml.name, "by_dataset": _by_dataset(entries, agreeing, xml_outcome, xref_outcome)}

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
        "xml_off_primary_only_but_xref_resolves": sum(
            1 for a in base_rows
            if xml_outcome[a] == "off_primary_only" and xref_outcome[a] in ("resolved", "multi_gene")),
        "xml_unresolved_but_xref_resolves": sum(
            1 for a in base_rows
            if xml_outcome[a] in ("not_in_source", "off_primary_only") and xref_outcome[a] in ("resolved", "multi_gene")),
        "parity_identical": identical,
        "parity_differ": len(base_rows) - identical,
        "parity_differ_xml_has_no_ensembl_link": sum(1 for a in differ if xml_outcome[a] == "not_in_source"),
        # A view a v2 could define (PXR-O7, 2026-10-11): the xref agrees, or it has never heard of
        # the accession and the XML links a gene. Not a v1 view; counted here so its cost is known.
        "agree_or_silent_covered": sum(
            1 for a in base_rows if agreeing[a] or _xref_silent_xml_resolves(a, xml_outcome, xref_outcome)),
        **extra,
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
        f"| outcome | Ensembl xref{' (sent in 005-logs)' if s['source_table'] == 'search_db_human_e116.tsv' else ''} | search XML's own links |",
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
        f"with are exactly the genes `resolve.py` finds" + (
            "." if s["parity_differ"] == 0 else
            f"; the {s['parity_differ']:,} others are entries whose XML carries no Ensembl link at all."
            if s["parity_differ_xml_has_no_ensembl_link"] == s["parity_differ"] else "; " +
            f"of the {s['parity_differ']:,} others, {s['parity_differ_xml_has_no_ensembl_link']:,} are entries whose "
            "XML carries no Ensembl link at all and the rest disagree on the genes themselves."),
        "",
    ]
    if "by_dataset" in s:
        bd = s["by_dataset"]
        L += [
            f"## By UniProt dataset (`{s['search_xml']}`)",
            "",
            "Coverage is the agrees view: an entry counts when the Ensembl xref agrees with at least one of its genes.",
            "",
            "| dataset | entries | one gene | several genes | no gene | covered | no primary gene name (of which covered) "
            "| no Ensembl dbReference (of which covered) | neither (of which covered) |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for ds, d in bd.items():
            av, n = d["agrees_view"], d["entries"]
            cov = av["one_gene"] + av["several_genes"]
            L.append(f"| {ds} | {n:,} | {av['one_gene']:,} | {av['several_genes']:,} | {av['no_gene']:,} | "
                     f"{cov / n:.1%} | {d['no_primary_gene_name']['entries']:,} ({d['no_primary_gene_name']['with_agreeing_gene']:,}) | "
                     f"{d['no_ensembl_dbreference']['entries']:,} ({d['no_ensembl_dbreference']['with_agreeing_gene']:,}) | "
                     f"{d['neither']['entries']:,} ({d['neither']['with_agreeing_gene']:,}) |")
        L += ["",
              "**Ensembl's xref has never heard of the accession, but the XML links a gene** (silent, not a "
              "disagreement; the agrees view drops these):",
              "",
              "| dataset | entries | created by UniProt in |",
              "|---|---:|---|"]
        for ds, d in bd.items():
            sv = d["xref_silent_xml_resolves"]
            L.append(f"| {ds} | {sv['entries']:,} | " + ", ".join(f"{y}: {n:,}" for y, n in sv["created"].items()) + " |")
        n = s["base_entries"]
        av = s["xref_view"].get("resolved", 0) + s["xref_view"].get("multi_gene", 0)
        L += ["",
              f"Covered: agrees view **{av:,}** ({av / n:.1%}); agrees-or-silent (not a v1 view) "
              f"**{s['agree_or_silent_covered']:,}** ({s['agree_or_silent_covered'] / n:.1%}).",
              ""]
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("table", type=Path, help="output of tools/ResolveSearchDb")
    ap.add_argument("--species", default="homo_sapiens", choices=sorted(sources.TAXA))
    ap.add_argument("--out", default="results/search_db_resolution")
    ap.add_argument("--xml", type=Path, help="the search XML, to split coverage by UniProt dataset")
    args = ap.parse_args(argv)
    s = summarize(args.table, args.species, args.xml)
    stem = project_root() / args.out
    stem.with_suffix(".json").write_text(json.dumps(s, indent=2), encoding="utf-8")
    stem.with_suffix(".md").write_text(render(s), encoding="utf-8")
    print(json.dumps({k: s[k] for k in ("base_entries", "xref_view", "xml_view", "parity_identical")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
