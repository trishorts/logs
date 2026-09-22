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
- `dataRepo` is the near-term generic neighbour and our first channel; the accession-resolution seam
  between us is **settled** (see below).
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

## What the first day settled

**Ownership (thread `dataRepo` 001 → 002, both closed).** `dataRepo` opened the channel on the day we
were created and answered both collisions rather than asking about them. Ours: the orthology store,
the analysis views, **accession → source gene resolution**, and **canonical accession normalization**.
Theirs: verbatim identifier storage. Their evidence for handing us resolution is the best argument
for this project we have — over 20,022 distinct accessions in their corpus, **five carry different
gene spellings in different datasets**, so in their store `gene` is not even a function of `accession`.

**Taxa confirmed:** human 9606, mouse 10090, rat 10116. Generic framing retained.

**Two modelling decisions locked** before any code exists — see `.project/state.yaml`:
a group and a pairwise relationship are **two objects** (a member's `role` in a group cannot carry
`relationship_type`, because one2one/one2many describe a *pair*); and an orthogroup id is **not stable
across source releases**, so the honest key is `(source, release, group_id)`.

**mzLib survey done** (`design/ORACLE.md`). The headline: every UniProt `<dbReference>` is already
parsed and kept on `Protein.DatabaseReferences` — Ensembl, GeneID, RefSeq, HGNC, MGI, RGD — and mzLib
simply never reads them back by type. Accession→gene is ~70% solved for the XML path and 0% for
RefSeq protein.

## Pick up at

**`/grill-me` on `design/problem-statement.md`**, now with two of the original three gating questions
resolved. What remains:

1. **Implementation home.** The oracle says the project *splits*: accession→gene EXTENDs mzLib, the
   ID-mapping client is a natural mzLib sibling, and the versioned relational store does **not**
   belong in mzLib (it would be its first self-managed on-disk database and its first DB dependency
   outside vendor-file reading). Confirm or reject that split.
2. **Orthology source of record** — Compara primary is the working assumption; decide how
   NCBI/Alliance/HCOP support is stored without merging into one unqualified "truth".
3. **Multi-ENSG semantics** — UniProt writes one Ensembl reference per *transcript*, ENSG in a
   property, so a protein can carry several. This is where one-to-many first bites, and it is a
   modelling decision, not plumbing.

**Owed out:** `REQ-LOGS-4` — the joint cardinality of Compara orthogroups across 9606/10090/10116.
`dataRepo` will design their cross-species join against that number, so it gets **measured, not
estimated**. Pairwise is not enough: 1:1 human↔mouse plus 1:1 human↔rat does not imply a clean triple.

**Waiting on:** `REQ-DATAREPO-1` — is their corpus UniProt-XML- or FASTA-derived? XML means the
cross-references were present at search time and v1 is mostly reading them back. FASTA means only
`GN=` survived and the UniProt ID Mapping API is on the critical path, which is a different project.

<!-- BEGIN GENERATED -- render_resume.py owns this block; edit state.yaml, not here -->

**logs** &middot; phase **INCEPTION** (1/10) &middot; created 2026-09-22 &middot; rendered 2026-09-22

| | |
|---|---|
| Commits | 11 |
| Sync | [`trishorts/logs`](https://github.com/trishorts/logs) |
| Locked decisions | 14 |
| Open gaps | 5 |

<!-- END GENERATED -->
