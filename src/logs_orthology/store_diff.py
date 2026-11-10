"""Do the gene-resolution rows in dataRepo's store equal ours? (PXReprise PXR-O10, 012-PXReprise)

The store holds one ``logs.resolve_genes`` artefact per search database:
``_engine/logs.resolve_genes/<artefact>/gene_resolutions.parquet`` beside its ``run.json``. This
compares an artefact's rows, as a multiset over every column both tables have, with a reference:

* our ``tools/ResolveSearchDb`` table for the same database (entry rows only: the engine resolves
  entries, CLAUDE.md trap 16), where the rows must be identical, database sha256 included; or
* another artefact, for a later build of the same proteome (agingPTM-v4 against v3), where the rows
  must be identical apart from ``search_database_sha256``.

It also checks each artefact's provenance: ``definition_id``; the per-row input values against our
manifest's ``row_values`` (trap 17); the database sha256 in the rows against ``run.json`` and against
the file itself when it is on this machine; and ``run.json``'s ``engine_summary`` against the rows.

Run:
    python -m logs_orthology.store_diff --out results/store_diff_canonical \\
        rat=F:/aging_data/repo/store/_engine/logs.resolve_genes/ffadfcf207ba3037:results/search_db_rat_canonical-v3_e116.tsv \\
        rat-v4=F:/aging_data/repo/store/_engine/logs.resolve_genes/b69ca7d3fafc27d7:F:/aging_data/repo/store/_engine/logs.resolve_genes/ffadfcf207ba3037
"""

from __future__ import annotations

import argparse
import collections
import csv
import datetime as _dt
import hashlib
import json
import sys
from pathlib import Path

from .fetch import project_root

csv.field_size_limit(10_000_000)

SPECIES = {"human": "homo_sapiens", "mouse": "mus_musculus", "rat": "rattus_norvegicus"}
DB = "search_database_sha256"
ROW_VALUES = ("gene_set_release", "gene_set_sha256", "ensembl_xref_sha256")
MANIFEST = "results/resolver_inputs_e116.json"


def _cell(v) -> str:
    return "" if v is None else str(v).lower() if isinstance(v, bool) else str(v)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _artefact_rows(d: Path) -> tuple[list[str], list[dict]]:
    import pyarrow.parquet as pq  # noqa: PLC0415

    t = pq.read_table(d / "gene_resolutions.parquet")
    return t.schema.names, [{k: _cell(v) for k, v in r.items()} for r in t.to_pylist()]


def _table_rows(p: Path) -> tuple[list[str], list[dict]]:
    with open(p, encoding="utf-8", newline="") as fh:
        rd = csv.DictReader(fh, delimiter="\t")
        rows = [r for r in rd if r["accession"] == r["entry_accession"]]
        return list(rd.fieldnames or []), rows


def _rows(ref: Path) -> tuple[list[str], list[dict]]:
    return _artefact_rows(ref) if ref.is_dir() else _table_rows(ref)


def _one(rows: list[dict], col: str) -> list[str]:
    return sorted({r[col] for r in rows})


def provenance(species: str, d: Path, cols: list[str], rows: list[dict]) -> dict:
    run = json.loads((d / "run.json").read_text(encoding="utf-8"))
    manifest_path = project_root() / MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    want = next(s["row_values"] for s in manifest["species"] if s["species"] == SPECIES[species])

    outcome: dict[str, set] = collections.defaultdict(set)
    for r in rows:
        outcome[r["accession"]].add(r["outcome"])
    by_entry = collections.Counter(next(iter(o)) for o in outcome.values() if len(o) == 1)
    summary = run["engine_summary"]
    counts = {k: v for k, v in summary["outcome_counts"].items() if v}

    db_file = Path(run["input_files"]["search_database"])
    file_sha = _sha256(db_file) if db_file.exists() else None
    checks = {
        "definition_id": _one(rows, "definition_id") == [run["definition_id"]] == ["logs:DEF-GENE-RESOLUTION v1"],
        "row_values_match_manifest": all(_one(rows, k) == [want[k]] for k in ROW_VALUES),
        "rows_database_equals_run_json": _one(rows, DB) == [run["inputs"]["search_database"]],
        "database_file_hashes_to_it": None if file_sha is None else file_sha == run["inputs"]["search_database"],
        "one_outcome_per_entry": all(len(o) == 1 for o in outcome.values()),
        "engine_summary_matches_rows": (summary["record_count"], summary["protein_count"], counts)
                                       == (len(rows), len(outcome), dict(by_entry)),
        "checked_against_current_manifest": run["checked_against"]["logs_manifest_sha256"] == _sha256(manifest_path),
    }
    return {
        "artefact": run["artefact_id"], "written_utc": run["written_utc"],
        "search_database": db_file.name, DB: run["inputs"]["search_database"],
        "mzlib": run.get("release", {}).get("mzlib"), "datarepo": run.get("datarepo_version"),
        "requested_for": [b["dataset_id"] for b in run.get("requested_for", [])],
        "rows": len(rows), "entries": len(outcome), "outcome_by_entry": dict(sorted(by_entry.items())),
        "checks": checks,
    }


def compare(label: str, artefact: Path, ref: Path) -> dict:
    species = label.split("-", 1)[0]
    cols, rows = _artefact_rows(artefact)
    ref_cols, ref_rows = _rows(ref)
    shared = [c for c in cols if c in ref_cols and c != DB]
    key = lambda r: tuple(r[c] for c in shared)  # noqa: E731
    store, other = collections.Counter(map(key, rows)), collections.Counter(map(key, ref_rows))
    store_db, ref_db = _one(rows, DB), _one(ref_rows, DB)
    # Against our table the database must be the same file; against another artefact (a later build,
    # or the same database re-run on a newer mzLib) only the rows apart from it are compared.
    rows_equal = store == other
    return {
        "label": label, "species": SPECIES[species],
        "reference": ref.name if ref.is_dir() else (
            str(ref.relative_to(project_root())) if ref.is_relative_to(project_root()) else str(ref)).replace("\\", "/"),
        "reference_kind": "artefact" if ref.is_dir() else "logs table (entry rows)",
        "compared_on": shared,
        "only_in_store_columns": [c for c in cols if c not in ref_cols],
        "only_in_reference_columns": [c for c in ref_cols if c not in cols],
        "store_rows": len(rows), "reference_rows": len(ref_rows),
        "only_store": sum((store - other).values()), "only_reference": sum((other - store).values()),
        "store_database": store_db, "reference_database": ref_db,
        "same_database": store_db == ref_db,
        "identical": rows_equal and (store_db == ref_db or ref.is_dir()),
        "provenance": provenance(species, artefact, cols, rows),
    }


def render(out: dict) -> str:
    lines = [
        "# The store's gene resolutions against ours (PXR-O10)", "",
        f"Generated {out['generated']} by `logs_orthology.store_diff`. Each `logs.resolve_genes` artefact in "
        "dataRepo's store is compared, as a multiset of rows on every column both sides have, with our "
        "`tools/ResolveSearchDb` table for the same database (entry rows), or, for a later build of the same "
        "proteome, with the earlier artefact (every column but `search_database_sha256`).", "",
        "| run | artefact | database | reference | store rows | only store | only reference | same database | identical |",
        "|---|---|---|---|---:|---:|---:|---|---|",
    ]
    for s in out["runs"]:
        p = s["provenance"]
        lines.append(f"| {s['label']} | `{p['artefact']}` | `{p['search_database']}` (`{p[DB][:12]}`) | "
                     f"`{s['reference']}` | {s['store_rows']:,} | {s['only_store']:,} | {s['only_reference']:,} | "
                     f"{'yes' if s['same_database'] else 'no'} | **{'yes' if s['identical'] else 'NO'}** |")
    lines += ["", "## Provenance checks", "",
              "| run | mzLib | definition | row values = manifest | rows' db = run.json | file hashes to it | "
              "summary = rows | checked against current manifest |",
              "|---|---|---|---|---|---|---|---|"]
    mark = lambda v: "—" if v is None else "✓" if v else "✗"  # noqa: E731
    for s in out["runs"]:
        c, p = s["provenance"]["checks"], s["provenance"]
        lines.append(f"| {s['label']} | {p['mzlib']} | {mark(c['definition_id'])} | {mark(c['row_values_match_manifest'])} | "
                     f"{mark(c['rows_database_equals_run_json'])} | {mark(c['database_file_hashes_to_it'])} | "
                     f"{mark(c['engine_summary_matches_rows'] and c['one_outcome_per_entry'])} | "
                     f"{mark(c['checked_against_current_manifest'])} |")
    lines += ["", "## Outcomes by entry (the search XML's view)", "",
              "| run | entries | resolved | multi_gene | off_primary_only | not_in_source |", "|---|---:|---:|---:|---:|---:|"]
    for s in out["runs"]:
        p = s["provenance"]
        o = p["outcome_by_entry"]
        lines.append(f"| {s['label']} | {p['entries']:,} | {o.get('resolved', 0):,} | {o.get('multi_gene', 0):,} | "
                     f"{o.get('off_primary_only', 0):,} | {o.get('not_in_source', 0):,} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("runs", nargs="+", help="<species>[-label]=<artefact dir>:<logs table | artefact dir>")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    root = project_root()
    out = {"generated": _dt.date.today().isoformat(), "runs": []}
    for run in args.runs:
        label, paths = run.split("=", 1)
        artefact, ref = _split_paths(paths)
        ref_path = Path(ref) if Path(ref).is_absolute() else root / ref
        out["runs"].append(compare(label, Path(artefact), ref_path))
        s = out["runs"][-1]
        print(json.dumps({k: s[k] for k in ("label", "store_rows", "only_store", "only_reference", "same_database", "identical")}
                         | {"checks": s["provenance"]["checks"]}))
    base = root / args.out
    base.with_suffix(".json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    base.with_suffix(".md").write_text(render(out), encoding="utf-8")
    ok = all(s["identical"] and all(v is not False for v in s["provenance"]["checks"].values()) for s in out["runs"])
    return 0 if ok else 1


def _split_paths(paths: str) -> tuple[str, str]:
    """``F:/a/b:results/x.tsv`` or ``F:/a/b:F:/c/d``: split on the colon that is not a drive's."""
    cut = next(i for i in range(len(paths)) if paths[i] == ":" and i > 1 and paths[i + 1:i + 2] not in ("/", "\\"))
    return paths[:cut], paths[cut + 1:]


if __name__ == "__main__":
    sys.exit(main())
