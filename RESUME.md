# RESUME - logs

## What this is

**logs** - homologs, orthologs, paralogs, and any other *-logs*. A generic engineering project that
builds a **versioned, gene-centric cross-species orthology layer** for large multi-organism
proteomics studies.

Given protein identifications from different species (UniProt / RefSeq accessions, thousands to tens
of thousands), it resolves them to stable gene identifiers, assigns orthology from a release-pinned
source, and exposes the relationships **without collapsing one-to-many orthology**. Downstream
analyses choose their resolution - all orthologs, strict one-to-one, orthogroup-level, or unresolved
- rather than having that choice baked into a lookup table.

## Why it exists

There is no universally correct one-to-one mapping between genes or proteins across species. Gene
duplication, gene loss, and divergence mean a human gene may map to two mouse genes, or to none.
Gene-symbol tables and best-hit mapping flatten that and are not reproducible across database
releases. This project keeps the biology and the provenance.

## Scope discipline

Generic infrastructure, **not** an analysis for one study.

- `aging` (organelles in aging, large-scale multi-organism proteomics) is the **first consumer**, not
  the design driver.
- `dataRepo` is the near-term generic neighbour; the accession-resolution seam between us is unsettled.
- A requirement arriving from a consuming project must be **generalized** before it lands in the design.

## Locked design constraints

Carried from the inception discussion (`design/problem-statement.md`, full source in
`design/sources/`):

- Stable IDs are primary keys; gene symbols are display labels only.
- One orthology relationship per row - never a single-valued `human -> mouse` column.
- Retain all orthologs; collapsing is an analysis-stage decision.
- **No transitive closure as the orthology algorithm** - connected components of the pairwise graph
  are not gene families.
- Source + release + provenance travel with every relationship; snapshots are comparable, not overwritten.
- Unresolved / ambiguous are first-class outcomes with a recorded reason.
- Protein-inference ambiguity stays separate from orthology ambiguity.
- New species are added by importing records, not by changing the schema.

## Pick up at

**`/grill-me` on `design/problem-statement.md`.** Three decisions gate everything downstream:

1. **Implementation home** - a component inside `mzLib` (reaches MetaMorpheus/FlashLFQ and native C#),
   a standalone versioned service/DB, or something `dataRepo` owns. Run `/oracle mzLib` before any
   code is written.
2. **Orthology source of record** - Ensembl Compara primary is the working assumption; decide how
   NCBI Orthologs / Alliance / HCOP support is stored alongside it without merging into one
   unqualified "truth".
3. **The `dataRepo` seam** - does `dataRepo` own protein-accession resolution and identifier storage,
   or do we? `design/threads/OWNERSHIP.md` currently flags this as an unclaimed possible collision.

Then announce the two claimed capabilities to peers via `threads.py new`, and open the seam question
with `dataRepo`.

<!-- BEGIN GENERATED -- render_resume.py owns this block; edit state.yaml, not here -->

**logs** &middot; phase **INCEPTION** (1/10) &middot; created 2026-09-22 &middot; rendered 2026-09-22

| | |
|---|---|
| Commits | 0 |
| Sync | not synced -- no remote recorded |
| Locked decisions | 2 |
| Open gaps | 4 |

<!-- END GENERATED -->
