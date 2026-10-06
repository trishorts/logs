"""Check Compara's gene-tree peptide alignment against the store, before any aligner is written.

``DEF-RESIDUE-CORRESPONDENCE v1`` (``design/DEFINITIONS.md``) crosses a homology edge through a
column of ``Compara.116.protein_default.aa.fasta.gz``. The definition was written from the
README alone. This states, from the file:

1. **Format.** Gapped FASTA, one alignment per gene tree, alignments separated by ``//`` (README),
   headers a bare Ensembl protein id. Every row of one alignment has the same length.
2. **The store's proteins are in it.** Every ``protein_a``/``protein_b`` of the snapshot's pair
   files, and every ``canonical_protein_id`` of its members, appears exactly once, and both
   proteins of each pair row sit in the same alignment. Each alignment holds the proteins of one
   ``source_group_id`` (the members' tree), never two.
3. **How often leg 1 is the identity.** For each search-database entry whose gene the agrees view
   resolves, is the entry's sequence identical to its gene's tree protein? Where it is, leg 1 needs
   no alignment; where it is not, ``not_on_ensembl_protein`` is possible. This is an ENTRY count,
   not a residue rate: the residue rate needs the aligner.

The ungapped human/mouse/rat tree proteins are written to
``data/compara/tree_proteins_e116.tsv.gz`` (gitignored, derived) for the aligner's tests.

Run:  python -m logs_orthology.alignment_check [--db-dir F:/aging_data/db]
      -> results/alignment_check_e116.{json,md}
"""

from __future__ import annotations

import argparse
import collections
import csv
import gzip
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import duckdb

from . import sources
from .fetch import data_dir, project_root, sha256_of

PREFIX = {"homo_sapiens": "ENSP0", "mus_musculus": "ENSMUSP", "rattus_norvegicus": "ENSRNOP"}
NS = "{http://uniprot.org/uniprot}"

#: The three base search databases (ptmQtl 008); the agingPTM-v1 builds are covered by
#: db_equivalence, which shows whether their sequences are the same.
SEARCH_DBS = {
    "homo_sapiens": ("uniprotkb_proteome_UP000005640_AND_revi_2026_09_18.xml", "search_db_human_e116.tsv"),
    "mus_musculus": ("uniprotkb_proteome_UP000000589_AND_revi_2026-09-22.xml", "search_db_mouse_e116.tsv"),
    "rattus_norvegicus": ("uniprotkb_proteome_UP000002494_AND_revi_2026-09-22.xml", "search_db_rat_e116.tsv"),
}


def species_of(pid: str) -> str | None:
    # ENSP0 must not match ENSMUSP/ENSRNOP; those start ENSM/ENSR, so the order is safe.
    for sp, p in PREFIX.items():
        if pid.startswith(p):
            return sp
    return None


def read_alignment(path: Path) -> tuple[dict, dict]:
    """protein -> (block, ungapped sequence) for our species, and format statistics."""
    proteins: dict[str, tuple[int, str]] = {}
    stats = collections.Counter()
    dup: list[str] = []
    ragged: list[int] = []
    block, pid, parts, widths = 0, None, [], set()

    def flush():
        nonlocal pid, parts
        if pid is None:
            return
        aligned = "".join(parts)
        widths.add(len(aligned))
        stats["sequences"] += 1
        sp = species_of(pid)
        if sp:
            stats[f"sequences:{sp}"] += 1
            if pid in proteins:
                dup.append(pid)
            proteins[pid] = (block, aligned.replace("-", ""))
        pid, parts = None, []

    with gzip.open(path, "rt") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            if line == "//":
                flush()
                if len(widths) > 1:
                    ragged.append(block)
                widths = set()
                block += 1
                continue
            if line.startswith(">"):
                flush()
                pid = line[1:].split()[0]
            else:
                parts.append(line)
        flush()
        if widths:
            block += 1
    stats["alignments"] = block
    return proteins, {"stats": dict(stats), "duplicate_proteins": dup[:20], "n_duplicate": len(dup),
                      "ragged_alignments": len(ragged)}


def entry_sequences(xml: Path) -> dict[str, str]:
    out = {}
    for _, e in ET.iterparse(xml, events=("end",)):
        if e.tag == NS + "entry":
            out[e.find(NS + "accession").text] = "".join(e.find(NS + "sequence").text.split())
            e.clear()
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db-dir", default="F:/aging_data/db")
    args = ap.parse_args(argv)
    root = project_root()
    snap = root / "snapshots" / f"compara-{sources.RELEASE}"
    aln = data_dir() / sources.gene_tree_alignment_file().local_name

    print("reading the alignment ...", file=sys.stderr)
    proteins, fmt = read_alignment(aln)

    with gzip.open(data_dir() / f"tree_proteins_e{sources.RELEASE}.tsv.gz", "wt", newline="") as fh:
        fh.write("protein_id\talignment_index\tsequence\n")
        for pid, (b, seq) in sorted(proteins.items()):
            fh.write(f"{pid}\t{b}\t{seq}\n")

    # 2. the store's proteins
    con = duckdb.connect()
    pairs = con.sql(f"select protein_a, protein_b, relationship_class, relationship_type, gene_a, gene_b, "
                    f"species_a, species_b from '{snap.as_posix()}/pairs/*.parquet'").fetchall()
    members = con.sql(f"select species, gene_id, source_group_id, canonical_protein_id from '{snap.as_posix()}/members/*.parquet'").fetchall()
    tree_of_gene = {m[1]: m[2] for m in members}
    store = {"pair_rows": len(pairs), "pair_rows_protein_missing": 0, "pair_rows_split_across_alignments": 0}
    # A split row has no shared column. Which relationships, and are the genes in different trees?
    split = collections.Counter()
    for a, b, cls, typ, ga, gb, sa, sb in pairs:
        if a not in proteins or b not in proteins:
            store["pair_rows_protein_missing"] += 1
        elif proteins[a][0] != proteins[b][0]:
            store["pair_rows_split_across_alignments"] += 1
            same_tree = tree_of_gene.get(ga) == tree_of_gene.get(gb)
            split[f"{typ}|{sa}~{sb}|{'same_tree' if same_tree else 'different_trees'}"] += 1
    store["split_rows_by_type_pair_tree"] = dict(sorted(split.items()))
    missing_members = [m for m in members if m[3] not in proteins]
    tree_by_block: dict[int, set] = collections.defaultdict(set)
    canonical_by_gene = {}
    for sp, gene, tree, pid in members:
        canonical_by_gene[gene] = pid
        if pid in proteins:
            tree_by_block[proteins[pid][0]].add(tree)
    member_ids = {m[3] for m in members}
    store.update(
        members=len(members),
        members_missing=len(missing_members),
        members_missing_examples=[m[3] for m in missing_members[:10]],
        alignments_holding_two_trees=sum(1 for t in tree_by_block.values() if len(t) > 1),
        our_proteins_in_alignment=len(proteins),
        our_proteins_not_a_member_canonical=len(set(proteins) - member_ids),
    )

    # 3. leg 1 at entry grain
    leg1 = {}
    db = Path(args.db_dir)
    for sp, (xml_name, table) in SEARCH_DBS.items():
        xml = db / xml_name
        if not xml.exists():
            leg1[sp] = {"skipped": f"{xml} not present"}
            continue
        print(f"{sp}: reading {xml_name} ...", file=sys.stderr)
        seqs = entry_sequences(xml)
        pairs_eg = set()
        with open(root / "results" / table, encoding="utf-8") as fh:
            for row in csv.DictReader(fh, delimiter="\t"):
                if row["ensembl_xref_agrees"] == "true" and row["gene_id"] and not row["isoform"]:
                    pairs_eg.add((row["entry_accession"], row["gene_id"]))
        c = collections.Counter()
        for entry, gene in pairs_eg:
            pid = canonical_by_gene.get(gene)
            if pid is None:
                c["gene_in_no_tree"] += 1
            elif pid not in proteins:
                c["tree_protein_not_in_alignment"] += 1
            elif entry not in seqs:
                c["entry_not_in_database"] += 1
            elif seqs[entry] == proteins[pid][1]:
                c["identical"] += 1
            else:
                c["differs"] += 1
        leg1[sp] = {"search_database": xml_name, "search_database_sha256": sha256_of(xml),
                    "entry_gene_pairs": len(pairs_eg), **dict(c)}

    out = {"alignment_file": aln.name, "alignment_sha256": sha256_of(aln), "format": fmt,
           "store": store, "leg1_entry_vs_tree_protein": leg1,
           "snapshot_manifest_sha256": sha256_of(snap / "manifest.json")}
    (root / "results" / f"alignment_check_e{sources.RELEASE}.json").write_text(
        json.dumps(out, indent=2) + "\n", encoding="utf-8")

    s = fmt["stats"]
    md = [
        f"# Compara {sources.RELEASE} gene-tree alignment, checked against the store",
        "",
        f"`{aln.name}` (sha256 `{out['alignment_sha256'][:16]}…`), by `python -m logs_orthology.alignment_check`.",
        "",
        "## Format",
        "",
        f"- {s['alignments']:,} alignments separated by `//`, {s['sequences']:,} sequences; "
        f"{fmt['ragged_alignments']} alignments have rows of unequal length.",
        f"- Ours: human {s.get('sequences:homo_sapiens', 0):,}, mouse {s.get('sequences:mus_musculus', 0):,}, "
        f"rat {s.get('sequences:rattus_norvegicus', 0):,}; {fmt['n_duplicate']} appear more than once.",
        "",
        "## The store's proteins",
        "",
        f"- Pair rows: {store['pair_rows']:,}; a protein missing from the alignment: "
        f"{store['pair_rows_protein_missing']:,}; the two proteins in different alignments: "
        f"{store['pair_rows_split_across_alignments']:,}.",
        "- Split rows, by relationship type, species pair and whether the two genes share a gene tree:",
        *[f"  - `{k}`: {v:,}" for k, v in store["split_rows_by_type_pair_tree"].items()],
        f"- Members (one canonical protein per gene): {store['members']:,}; missing: {store['members_missing']:,}.",
        f"- Alignments holding the members of two trees: {store['alignments_holding_two_trees']:,}.",
        f"- Our proteins in the alignment that are not a member's canonical protein: "
        f"{store['our_proteins_not_a_member_canonical']:,}.",
        "",
        "## Leg 1, by entry: is the UniProt entry's sequence its gene's tree protein?",
        "",
        "Entries x genes from the agrees view (canonical entries, no isoforms). An entry count, not a residue rate.",
        "",
        "| species | entry x gene | identical | differs | gene in no tree | other |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for sp, r in leg1.items():
        if "skipped" in r:
            md.append(f"| {sp} | skipped: {r['skipped']} | | | | |")
            continue
        n = r["entry_gene_pairs"]
        other = r.get("tree_protein_not_in_alignment", 0) + r.get("entry_not_in_database", 0)
        md.append(f"| {sp} | {n:,} | {r.get('identical', 0):,} ({100*r.get('identical', 0)/n:.1f}%) "
                  f"| {r.get('differs', 0):,} ({100*r.get('differs', 0)/n:.1f}%) "
                  f"| {r.get('gene_in_no_tree', 0):,} | {other:,} |")
    (root / "results" / f"alignment_check_e{sources.RELEASE}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
