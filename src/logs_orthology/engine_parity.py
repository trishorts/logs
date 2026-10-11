"""Does dataRepo's ``logs.resolve_genes`` engine give our reference rows on a search database?

The engine calls pyMzLib's ``resolve_genes`` (dataRepo ``engines/logs.py``). This runs that same call
on each database and compares its rows, as a multiset, with the entry rows ``tools/ResolveSearchDb``
wrote (mzLib's C# resolver). pyMzLib resolves ENTRIES (CLAUDE.md trap 16), so the C# table's variant
proteoform rows are left out. Answered PXReprise PXR-O7 for agingPTM-v3 (2026-10-11).

Run (pyMzLib installed; the XMLs on this machine):
    python -m logs_orthology.engine_parity --out results/engine_parity_canonical-v3 \
        human=F:/aging_data/db/UP000005640_all_genecentric_2026_03_agingPTM-v3.xml:results/search_db_human_canonical-v3_e116.tsv \
        mouse=...  rat=...
"""

from __future__ import annotations

import argparse
import collections
import csv
import datetime as _dt
import json
import sys
from pathlib import Path

from .fetch import project_root

csv.field_size_limit(10_000_000)

GENE_SETS = {"human": "Homo_sapiens.GRCh38", "mouse": "Mus_musculus.GRCm39", "rat": "Rattus_norvegicus.GRCr8"}
KEY = ("accession", "outcome", "gene_id", "source", "ensembl_xref_agrees", "search_database_sha256", "gene_set_sha256")


def _cell(v) -> str:
    return "" if v is None else str(v).lower() if isinstance(v, bool) else str(v)


def compare(species: str, xml: Path, cs_table: Path) -> dict:
    import pymzlib  # noqa: PLC0415
    import pymzlib.proteins as proteins  # noqa: PLC0415

    root, gs = project_root(), GENE_SETS[species]
    res = proteins.resolve_genes(xml, gene_set=root / f"results/gene_sets/{gs}.116.genes.tsv.gz",
                                 xref=root / f"data/compara/{gs}.116.uniprot.tsv.gz")
    recs = list(res.records)
    get = (lambda r, k: r[k]) if recs and isinstance(recs[0], dict) else (lambda r, k: getattr(r, k))
    py = collections.Counter(tuple(_cell(get(r, k)) for k in KEY) for r in recs)
    cs: collections.Counter = collections.Counter()
    with open(cs_table, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            if r["accession"] == r["entry_accession"]:
                cs[tuple(r[k] for k in KEY)] += 1
    return {
        "species": species, "search_xml": xml.name, "reference_table": cs_table.name,
        "pymzlib": pymzlib.__version__, "mzlib": str(pymzlib.bridge_version()["mzlib"]),
        "pymzlib_rows": sum(py.values()), "reference_entry_rows": sum(cs.values()),
        "entries": len({k[0] for k in py}),
        "only_pymzlib": sum((py - cs).values()), "only_reference": sum((cs - py).values()),
        "identical": py == cs,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("runs", nargs="+", help="species=<search.xml>:<ResolveSearchDb table>")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    out = {"generated": _dt.date.today().isoformat(), "compared_on": list(KEY), "species": []}
    for run in args.runs:
        species, paths = run.split("=", 1)
        xml, table = paths.rsplit(":", 1)
        out["species"].append(compare(species, Path(xml), project_root() / table))
        print(json.dumps(out["species"][-1]))
    (project_root() / args.out).with_suffix(".json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    return 0 if all(s["identical"] for s in out["species"]) else 1


if __name__ == "__main__":
    sys.exit(main())
