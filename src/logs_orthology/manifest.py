"""Manifest of the resolver's reference inputs, one entry per (species, release).

Promised to dataRepo in 015-logs §1. Under option (a) (dataRepo's D24) they RUN the released
resolver and we DEFINE it, so they need to know exactly which two files a run reads, and which
values its rows will then carry. Those are not the same hashes, and that is the trap:

* A run reads the **gene-set table** (``results/gene_sets/``), but every row's
  ``gene_set_sha256`` is the sha256 of the **GTF** the table was built from (it is in the table's
  ``#!source-sha256`` header). Checking rows against the table's own sha256 would fail on every row.
* A run reads **Ensembl's UniProt xref dump**, and every row's ``ensembl_xref_sha256`` is that
  file's sha256. Without the file ``ensembl_xref_agrees`` is empty, and that column is aging's
  default gene view (aging 009 §1).

Every value is computed from the files on disk and nothing is typed in. The gene-set header is
cross-checked against the GTF itself when it is present, and every sha256 is checked against
``data/PROVENANCE.md``.

Run:  python -m logs_orthology.manifest   -> results/resolver_inputs_e116.{json,md}
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import subprocess
import sys
from pathlib import Path

from . import sources
from .fetch import project_root, sha256_of

#: The mzLib release that first carries the resolver (#1338, merged 2026-09-23 as 5d772a23).
MZLIB_RELEASE = "1.0.592"
MZLIB_PR = 1338
MZLIB_MERGE_COMMIT = "5d772a23bc75daf1e488fb1fdf17703ab320ad50"

REPO_URL = "https://github.com/trishorts/logs"


def _header(path: Path) -> dict[str, str]:
    """The ``#!key value`` provenance header of a gene-set table."""
    out: dict[str, str] = {}
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            if not line.startswith("#!"):
                break
            key, _, value = line[2:].rstrip("\n").partition(" ")
            out[key] = value
    return out


def _gene_count(path: Path) -> int:
    with gzip.open(path, "rt", encoding="utf-8") as f:
        body = [ln for ln in f if not ln.startswith("#!")]
    return len(body) - 1  # column header


def _last_commit(path: Path) -> str:
    r = subprocess.run(["git", "log", "-1", "--format=%H", "--", str(path)],
                       cwd=project_root(), capture_output=True, text=True, check=True)
    commit = r.stdout.strip()
    if not commit:
        raise SystemExit(f"{path} is not committed; a manifest cannot point at it")
    return commit


def _provenance_prefixes() -> dict[str, str]:
    """local filename -> the sha256 prefix recorded in data/PROVENANCE.md."""
    text = (project_root() / "data" / "PROVENANCE.md").read_text(encoding="utf-8")
    out: dict[str, str] = {}
    for m in re.finditer(r"`data/compara/([^`]+)`.*?`([0-9a-f]{16})…`", text):
        out[m.group(1)] = m.group(2)
    return out


def _check_provenance(name: str, sha: str, recorded: dict[str, str]) -> None:
    if name not in recorded:
        raise SystemExit(f"{name}: not in data/PROVENANCE.md")
    if not sha.startswith(recorded[name]):
        raise SystemExit(f"{name}: sha256 {sha} does not match PROVENANCE {recorded[name]}…")


def build(verify_gtf: bool = True) -> list[dict]:
    root = project_root()
    recorded = _provenance_prefixes()
    xrefs = {sf.key: sf for sf in sources.xref_files()}
    gtfs = {sf.key: sf for sf in sources.gtf_files()}
    entries = []
    for species, assembly in sources.ASSEMBLY.items():
        rel = sources.RELEASE
        table = root / "results" / "gene_sets" / f"{species.capitalize()}.{assembly}.{rel}.genes.tsv.gz"
        hdr = _header(table)
        gtf_sf = gtfs[f"gtf:{species}"]
        if hdr.get("source-file") != gtf_sf.local_name or hdr.get("release") != rel:
            raise SystemExit(f"{table.name}: header {hdr} does not name {gtf_sf.local_name}, release {rel}")
        gtf_sha = hdr["source-sha256"]
        _check_provenance(gtf_sf.local_name, gtf_sha, recorded)
        gtf_path = root / "data" / "compara" / gtf_sf.local_name
        if verify_gtf and gtf_path.exists() and sha256_of(gtf_path) != gtf_sha:
            raise SystemExit(f"{table.name}: header sha256 is not the sha256 of {gtf_path}")

        xref_sf = xrefs[f"xref:uniprot:{species}"]
        xref_path = root / "data" / "compara" / xref_sf.local_name
        xref_sha = sha256_of(xref_path)
        _check_provenance(xref_sf.local_name, xref_sha, recorded)

        table_rel = table.relative_to(root).as_posix()
        commit = _last_commit(table)
        entries.append({
            "species": species,
            "ncbi_taxonomy_id": sources.TAXA[species],
            "ensembl_release": rel,
            "assembly": assembly,
            "genome_build": hdr.get("genome-build"),
            "inputs": {
                "gene_set": {
                    "role": "gene set: the resolver's <gtf.gz | genes.tsv.gz> argument",
                    "path": table_rel,
                    "url": f"{REPO_URL}/raw/{commit}/{table_rel}",
                    "commit": commit,
                    "bytes": table.stat().st_size,
                    "sha256": sha256_of(table),
                    "genes": _gene_count(table),
                    "built_from": {"file": gtf_sf.local_name, "url": gtf_sf.url, "sha256": gtf_sha},
                },
                "ensembl_uniprot_xref": {
                    "role": "Ensembl's UniProt xref: the resolver's <uniprot.tsv.gz> argument",
                    "file": xref_sf.local_name,
                    "url": xref_sf.url,
                    "bytes": xref_path.stat().st_size,
                    "sha256": xref_sha,
                },
            },
            # What every row of a run over these inputs carries. Check rows against THESE.
            "row_values": {
                "gene_set_release": rel,
                "gene_set_sha256": gtf_sha,
                "ensembl_xref_sha256": xref_sha,
            },
        })
    return entries


def render(doc: dict) -> str:
    r = doc["resolver"]
    lines = [
        f"# Resolver inputs: Ensembl {doc['ensembl_release']}",
        "",
        f"Resolver: mzLib **{r['mzlib_release']}** (#{r['pr']}, merge `{r['merge_commit'][:8]}`). "
        "One entry per species. A run reads the two files under *inputs*; each row it writes carries",
        "the values under *row values*. **`gene_set_sha256` in a row is the GTF's sha256, not the table's.**",
        "Generated by `python -m logs_orthology.manifest`; do not edit by hand.",
        "",
        "| species | taxon | input | file | bytes | sha256 |",
        "|---|---:|---|---|---:|---|",
    ]
    for e in doc["species"]:
        gs, xr = e["inputs"]["gene_set"], e["inputs"]["ensembl_uniprot_xref"]
        lines.append(f"| {e['species']} | {e['ncbi_taxonomy_id']} | gene set ({gs['genes']:,} genes) | "
                     f"[`{Path(gs['path']).name}`]({gs['url']}) | {gs['bytes']:,} | `{gs['sha256']}` |")
        lines.append(f"| | | UniProt xref | [`{xr['file']}`]({xr['url']}) | {xr['bytes']:,} | `{xr['sha256']}` |")
    lines += ["", "## Row values", "",
              "| species | `gene_set_release` | `gene_set_sha256` (= GTF) | `ensembl_xref_sha256` |",
              "|---|---|---|---|"]
    for e in doc["species"]:
        v = e["row_values"]
        lines.append(f"| {e['species']} | {v['gene_set_release']} | `{v['gene_set_sha256']}` | "
                     f"`{v['ensembl_xref_sha256']}` |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--no-verify-gtf", action="store_true",
                    help="skip re-hashing the GTFs (the header is still checked against PROVENANCE)")
    args = ap.parse_args(argv)
    doc = {
        "manifest_version": 1,
        "source": "ensembl",
        "ensembl_release": sources.RELEASE,
        "resolver": {"mzlib_release": MZLIB_RELEASE, "pr": MZLIB_PR, "merge_commit": MZLIB_MERGE_COMMIT},
        "species": build(verify_gtf=not args.no_verify_gtf),
    }
    out = project_root() / "results" / f"resolver_inputs_e{sources.RELEASE}"
    out.with_suffix(".json").write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8", newline="\n")
    out.with_suffix(".md").write_text(render(doc), encoding="utf-8", newline="\n")
    print(render(doc))
    return 0


if __name__ == "__main__":
    sys.exit(main())
