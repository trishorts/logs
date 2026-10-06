"""Does an agingPTM-v1 search database hold the same proteins as the proteome it was built from?

ptmQtl 008 (LOGS-P5) asks for residue correspondence on six search databases: aging's three
reviewed proteomes and the three ``_agingPTM-v1`` builds of them, which add GPTMD-found
``modified residue`` features (aging ``results/ptm_db_2026-09-27``). A residue key is
``(search_database_sha256, accession, position)``, so if a build holds the same entries with the
same sequences and the same sequence variants as its base, one alignment serves both keys. ptmQtl
asked us to say which we did, because their join keys on the sha.

This compares each pair entry by entry and states, from the files rather than from the build's
description:

* the entries (by first accession) in one file and not the other;
* entries whose ``<sequence>`` differs;
* entries whose ``sequence variant`` features differ (they make the ``P12345_S70N`` proteoforms,
  whose positions are keys too);
* entries that differ in anything other than ``modified residue`` features.

Run:  python -m logs_orthology.db_equivalence [--db-dir F:/aging_data/db]
      -> results/search_db_equivalence.{json,md}
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from .fetch import project_root, sha256_of

NS = "{http://uniprot.org/uniprot}"

#: (species, base file, agingPTM-v1 file); hashes as ptmQtl 008 gives them (prefixes) are checked.
PAIRS = [
    ("human", "uniprotkb_proteome_UP000005640_AND_revi_2026_09_18.xml",
     "uniprotkb_proteome_UP000005640_AND_revi_2026_09_18_agingPTM-v1.xml", "760984e8", "eaefbb7e"),
    ("mouse", "uniprotkb_proteome_UP000000589_AND_revi_2026-09-22.xml",
     "uniprotkb_proteome_UP000000589_AND_revi_2026-09-22_agingPTM-v1.xml", "fb52debf", "26ea83c2"),
    ("rat", "uniprotkb_proteome_UP000002494_AND_revi_2026-09-22.xml",
     "uniprotkb_proteome_UP000002494_AND_revi_2026-09-22_agingPTM-v1.xml", "abf612c9", "caf342e1"),
]


def _strip(e: ET.Element) -> None:
    """Drop formatting whitespace so a re-serialized file compares equal to its source."""
    if e.text is not None and not e.text.strip():
        e.text = None
    if e.tail is not None and not e.tail.strip():
        e.tail = None
    for c in e:
        _strip(c)


def _digest(e: ET.Element) -> str:
    return hashlib.sha256(ET.tostring(e, encoding="utf-8")).hexdigest()


def summarize(path: Path) -> dict[str, dict]:
    """first accession -> {seq, variants, rest, mods} for every entry in a UniProt XML."""
    out: dict[str, dict] = {}
    for _, e in ET.iterparse(path, events=("end",)):
        if e.tag != NS + "entry":
            continue
        acc = e.find(NS + "accession").text
        seq = "".join(e.find(NS + "sequence").text.split())
        feats = e.findall(NS + "feature")
        variants = sorted(_digest(f) for f in feats if f.get("type") == "sequence variant")
        mods = [f for f in feats if f.get("type") == "modified residue"]
        for f in mods:
            e.remove(f)
        _strip(e)
        if acc in out:
            raise ValueError(f"{path.name}: accession {acc} appears twice")
        out[acc] = {
            "seq": hashlib.sha256(seq.encode()).hexdigest(),
            "variants": hashlib.sha256("".join(variants).encode()).hexdigest(),
            "n_variants": len(variants),
            "rest": _digest(e),
            "mods": len(mods),
        }
        e.clear()
    return out


def compare(base: dict, built: dict) -> dict:
    shared = base.keys() & built.keys()
    seq = sorted(a for a in shared if base[a]["seq"] != built[a]["seq"])
    var = sorted(a for a in shared if base[a]["variants"] != built[a]["variants"])
    rest = sorted(a for a in shared if base[a]["rest"] != built[a]["rest"])
    gained = sorted(a for a in shared if built[a]["mods"] != base[a]["mods"])
    return {
        "entries_base": len(base),
        "entries_built": len(built),
        "only_in_base": sorted(base.keys() - built.keys()),
        "only_in_built": sorted(built.keys() - base.keys()),
        "sequence_differs": seq,
        "sequence_variants_differ": var,
        "differs_beyond_modified_residues": rest,
        "entries_with_changed_modified_residue_count": len(gained),
        "modified_residues_base": sum(v["mods"] for v in base.values()),
        "modified_residues_built": sum(v["mods"] for v in built.values()),
        "sequence_variant_features": sum(v["n_variants"] for v in base.values()),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db-dir", default="F:/aging_data/db")
    args = ap.parse_args(argv)
    db = Path(args.db_dir)
    results = []
    for species, base_name, built_name, base_prefix, built_prefix in PAIRS:
        bp, tp = db / base_name, db / built_name
        bsha, tsha = sha256_of(bp), sha256_of(tp)
        if not bsha.startswith(base_prefix) or not tsha.startswith(built_prefix):
            raise SystemExit(f"{species}: sha256 {bsha[:8]}/{tsha[:8]} is not 008's {base_prefix}/{built_prefix}")
        print(f"{species}: reading {base_name} and {built_name}", file=sys.stderr)
        r = compare(summarize(bp), summarize(tp))
        r.update(species=species, base_file=base_name, base_sha256=bsha,
                 built_file=built_name, built_sha256=tsha)
        r["same_proteins"] = not (r["only_in_base"] or r["only_in_built"] or r["sequence_differs"]
                                  or r["sequence_variants_differ"])
        results.append(r)

    root = project_root()
    (root / "results" / "search_db_equivalence.json").write_text(
        json.dumps({"db_dir": str(db), "pairs": results}, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# agingPTM-v1 builds against their base proteomes",
        "",
        "Generated by `python -m logs_orthology.db_equivalence` (entry by entry, keyed on the first",
        "accession). Answers ptmQtl 008: may one alignment serve both search-database sha256 keys?",
        "",
        "| species | base | build | entries base / build | only in one | sequence differs | variants differ | differs beyond `modified residue` | `modified residue` base -> build | same proteins |",
        "|---|---|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {r['species']} | `{r['base_sha256'][:8]}…` | `{r['built_sha256'][:8]}…` "
            f"| {r['entries_base']:,} / {r['entries_built']:,} "
            f"| {len(r['only_in_base']) + len(r['only_in_built'])} | {len(r['sequence_differs'])} "
            f"| {len(r['sequence_variants_differ'])} | {len(r['differs_beyond_modified_residues'])} "
            f"| {r['modified_residues_base']:,} -> {r['modified_residues_built']:,} "
            f"| {'yes' if r['same_proteins'] else 'NO'} |")
    (root / "results" / "search_db_equivalence.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
