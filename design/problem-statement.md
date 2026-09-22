# logs - problem statement

*Written 2026-09-22 at project inception. Distilled from
`design/sources/cross_species_orthology_discussion.md` (the full seed discussion, kept verbatim).*

## The problem

Large proteomics studies increasingly span multiple organisms - human, mouse, rat, and others.
Combining those datasets requires associating proteins (and the genes behind them) across species.
There is **no universally correct one-to-one mapping** between genes or proteins across species:
gene duplication, gene loss, and sequence divergence mean a single human gene may legitimately
correspond to two mouse genes, or to none.

Most ad-hoc solutions flatten this - a gene-symbol lookup table, a "best hit", a single
`human -> mouse` column. Each of those silently discards biology and is not reproducible across
database releases.

## What this project builds

A **generic, versioned, gene-centric cross-species orthology layer**: infrastructure any
multi-organism proteomics project can depend on, not an analysis for one study.

Three deliberately independent layers:

1. **Accession resolution** - what gene and protein does this UniProt / RefSeq accession represent
   in its source organism? (isoform suffixes preserved, RefSeq versions preserved, ambiguity flagged
   rather than resolved by guessing)
2. **Orthology assignment** - which orthology group(s) does that gene belong to, and what are its
   pairwise relationships to genes in other species? (Ensembl Compara primary; NCBI Orthologs /
   Alliance / HCOP as independent support, stored separately, never merged into one unqualified
   "truth")
3. **Cross-species analysis views** - how downstream analyses join, aggregate, or compare quantitative
   data: all-orthologs, strict one-to-one, orthogroup-level, or unresolved - chosen by the analysis,
   not forced by the mapping layer.

Keeping the layers independent means orthology data can be updated (new Ensembl release) without
redoing protein identification or rewriting original quantitative datasets.

## Hypothesis / claim to be tested

> A release-versioned, many-to-many orthology store keyed on stable gene identifiers - with
> accession resolution, orthology assignment, and analysis resolution as separate layers - can join
> multi-organism proteomics datasets at a stated, auditable resolution, and will recover
> cross-species relationships that gene-symbol or best-hit mapping silently loses.

Measurable consequences: accession resolution rate, unique-gene resolution rate, orthology coverage
per species pair, one-to-many frequency, cross-source agreement, and the count of relationships
recovered relative to a symbol-based baseline.

## Non-negotiable design constraints (from the seed discussion)

- **Stable identifiers are primary keys; gene symbols are display labels only.** Symbols change and
  are not unique across species.
- **One relationship per row.** Never a `human_gene -> mouse_gene` single-valued column.
- **Retain all orthologs.** One-to-many and many-to-many are preserved and exposed; collapsing is an
  analysis-stage decision.
- **Do not use transitive closure as the orthology algorithm.** Pairwise orthology is not an
  equivalence relation; connected components of the pairwise graph are not gene families. Use the
  source's gene-tree / orthogroup structure, and if a derived group is produced, version and document
  its grouping method.
- **Everything is versioned.** Source, release, and provenance travel with every relationship, so a
  future release can be *compared* with the previous snapshot rather than overwriting it.
- **Unresolved and ambiguous are first-class outcomes**, recorded with a reason (obsolete accession,
  unreviewed record, missing gene association, taxonomic mismatch, genuinely unresolved), not dropped.
- **Protein-inference ambiguity is kept separate from orthology ambiguity.** If peptides are shared
  between paralogs, the source identification was already ambiguous; orthology mapping cannot recover
  what the peptides did not resolve, and must not appear to.
- **New species are added by importing records, not by changing the schema.**

## Scope

**In scope:** the mapping layer, its ETL, its QC, its versioned snapshots, and the API/exports other
projects consume.

**Out of scope:** the biology of any particular study; quantitative normalization; statistical
testing across species. Those belong to the consuming project.

## Consumers and neighbours

| Project | Relationship |
|---|---|
| `aging` | First real consumer - large-scale proteomics of organelles in aging, multi-organism. Drives requirements but must not narrow the design. |
| `dataRepo` | Near-term neighbour, also generic. Seam to settle: who owns accession resolution and identifier storage. |
| `mzLib` | The lab's C# library. Candidate implementation home if this belongs in the mainland rather than a standalone service - resolve with `/oracle mzLib` before writing code. |
| `go`, `sdrf`, `pride`, `qc`, `pep` | Adjacent generic infrastructure projects; expect thread traffic about identifier and annotation seams. |

## Open questions at inception

Tracked as gaps in `.project/state.yaml`:

1. Implementation home: mzLib component vs standalone service vs dataRepo-owned.
2. Orthology source of record and how independent sources are stored alongside it.
3. The `dataRepo` seam for accession resolution.
4. Species set beyond the MVP taxa (human 9606, mouse 10090, rat 10116).

## Starting reference architecture

Carried forward from the seed discussion as a *starting point to be grilled*, not a locked design:
`ProteinAccession`, `Gene`, `OrthologyGroup`, `OrthologyGroupMember`, `OrthologyRelationship`, with a
six-stage ETL (ingest -> resolve -> normalize -> retrieve orthology -> build groups/relationships ->
validate and publish a versioned snapshot) and a QC report at every stage. See the seed document for
the column-level detail.
