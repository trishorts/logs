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

**Ownership** (thread `dataRepo` 001–007, seven messages). Ours: the orthology store, the analysis
views, **accession → source gene resolution**, and **canonical accession normalization**. Theirs:
verbatim identifier storage. Their argument for handing us resolution is the best case for this
project — of 20,022 distinct accessions, five carry different gene spellings in different datasets,
so `gene` is not a function of `accession` in their store.

**Taxa confirmed:** human 9606, mouse 10090, rat 10116. **Corpus:** 100% UniProt XML, one database,
one sha256 across all nine datasets — so v1 reads cross-references off the search database with no
network in the hot path.

**Implementation home locked** (`design/ORACLE.md`). The project *splits*: accession→gene **extends
mzLib** (every UniProt `<dbReference>` is already on `Protein.DatabaseReferences` and never read
back by type); the ID-mapping client is a natural sibling to `ProteinDbRetriever`; the **relational
store stays here**, because mzLib has no self-managed on-disk database and
`ControlledVocabulary.cs:25-27` argues against exactly this.

## What was measured

Both from pinned Ensembl 116 (`data/PROVENANCE.md`; 16 files, 673 MB, 15 of 16 checksum-verified).

**Orthology cardinality** — `results/cardinality.md`:

- **75.49%** of eligible human genes are a clean 1:1:1 across the three taxa. **Design a
  cross-species join for ~75%, not 95%.**
- **45 genes** are one2one to *both* rodents while the rodents are **not** one2one with each other —
  clean from every pairwise angle, not clean as a set. This is the whole reason triples were
  measured separately; a join built on pairwise evidence treats them as interchangeable.
- **2,539** human genes have no rodent ortholog at all. Mouse↔rat is the easy join (91.98%);
  anything crossing to human is not.

**Accession → gene** — `results/accession_resolution.md`:

- Multi-gene accessions are **rare (0.36% of reviewed human) but concentrated**: all four core
  histones are in the top seven, `P62805` (H4) spanning 14 real loci. A sub-1% rate landing on
  proteins abundant in every run — a sampled test set will miss it.
- **RefSeq is not deferred.** 69,569 curated human `NP_` accessions, **99.58%** single-gene (96.90% is
  `NP_`+`XP_` combined — corrected in 008-logs). Curated `NP_` links are 76.6% `DIRECT`; predicted
  `XP_` are only 14.1% — carry `info_type` per row or you report an inference as an assertion.

## Things that will bite you here

Each of these cost real time today.

1. **Ensembl's genome-specific Compara dumps *partition*, they do not overlap — and each species
   pair lives entirely in one file, not the obvious one.** Every human↔mouse orthology is in the
   **mouse** dump; the human dump has none. Download the file named after your species and you get
   a complete-looking result missing 100% of human↔mouse.
2. **A denominator is a claim.** Two were wrong in one afternoon. `protein_coding` is *not* the
   eligible set — Compara also trees IG/TR gene segments. And counting raw gene ids from the xref
   dumps includes ALT haplotypes, which inflated the multi-gene rate twentyfold (6.99% vs 0.36%)
   and manufactured a human-vs-rodent difference that does not exist.
3. **Never name an entity from memory.** `Q5JQC4` was written up as KIR2DL5A from recall; it is
   CT47A1. Resolve identifiers against the data every time.
4. **`Protein.NcbiTaxonomyId`'s shape does not transfer to gene ids.** UniProt writes one
   `dbReference` per *transcript* with the ENSG in a `<property>`, so `FirstOrDefault(...)?.Id` is a
   category error — it needs `SelectMany(Properties)` and a `Distinct()`.
5. **Numbers sent to a partner are a contract.** `tests/test_reported_claims.py` pins every one; if
   a re-run moves it, that test fails and we owe a correction.

## Pick up at

**The search-XML source for the resolver** — second half of `design/PLAN.md` step 5.

`src/logs_orthology/resolve.py` exists (2026-09-22). It gives one row per (accession, gene) with six
typed outcomes, restricted to the primary assembly, and carries the strongest `info_type` per pair
and `entry_accession`/`isoform` beside the verbatim accession. Today it resolves against the
**Ensembl 116 xref**, and it reconciles exactly with `xrefs.py` on reviewed human
(19,251 + 70 + 62 = 19,383). `tests/test_resolve.py` has 16 contracts.

Next: read the ENSGs out of the search XML's `<dbReference type="Ensembl">` (in
`<property type="gene ID">`, **versioned**). Key rows on `(accession, search_database_sha256)`, set
`source` per row, and cross-check against the xref. Do not key on the hash until **REQ-AGING-7**
confirms it. The local copy is `E:\CodeReview\go\data\raw\…2026_09_18.xml.gz` (decompressed
sha `760984e8d402ade6b110…`; dataRepo only ever quoted the first 16 characters).

**Owed first:** the numbers in 005-logs (20,416 entries → 19,257 / 69 / 62 / 1,028 not in source,
of which 1,012 have no Ensembl link in UniProt either) came from a scratchpad run. The XML reader
must reproduce them, and `test_reported_claims.py` must pin them.

**Why the order changed:** `aging` 002 said compare, not pool; rodents are months away (so the
store, step 6, is deferred); and they want resolution more than orthology.

**Corrections sent today:** 008-logs to dataRepo — `NP_` is 99.58% single-gene (96.90% was
`NP_`+`XP_` combined); `NP_` links are 76.6% `DIRECT`; isoform-suffixed accessions are 25,177, not
35,202 (that figure was rows). The `NP_` link-quality correction also went to aging, in 005.

Sanity-check the inputs still reproduce before changing anything:

```powershell
$env:PYTHONPATH = "E:\CodeReview\logs\src"
python tests/test_reported_claims.py    # 15 numbers already sent to a partner
python tests/test_resolve.py            # 16 resolver contracts
python tests/test_contracts.py          # 10 contract tests
```

**Also waiting** (nothing blocking):

- `dataRepo` **REQ-DATAREPO-7** — the distinct-ENSG distribution over *their* XML. Our prediction is
  on the record: ~99%. If theirs is materially worse, they likely have our ALT-haplotype trap.
- `dataRepo` **REQ-DATAREPO-4/5/6** — is the database file retained or only its sha; are we a
  blocker or an improvement; do they want the mzLib half early. REQ-AGING-4 answered the third from
  the consumer side: yes, resolution first.
- `aging` **REQ-AGING-5/6** (003-logs) — do isoform suffixes exist in their data at all (dataRepo
  counted zero); table vs call, versioned vs stable ENSG. **REQ-AGING-7** (004) — full sha256 of the
  search XML. **REQ-AGING-8** (005) — UniProt gene name as a label for the ~1,012 with no gene id?
- **mzLib PR #1336** must merge before any mzLib-side code starts — it sets the pattern.

## Documents in `design/`

- `problem-statement.md` — the distilled problem and the eight locked constraints.
- `sources/cross_species_orthology_discussion.md` — the seed discussion, verbatim.
- `ORACLE.md` — the mzLib survey and the three-way split verdict.
- `PLAN.md` — ordered steps and the standing rules.
- `threads/OWNERSHIP.md` — capability ownership; both inception collisions closed.
- `threads/dataRepo/`, `threads/aging/` — correspondence.

<!-- BEGIN GENERATED -- render_resume.py owns this block; edit state.yaml, not here -->

**logs** &middot; phase **BUILD** (4/10) &middot; created 2026-09-22 &middot; rendered 2026-09-22

| | |
|---|---|
| Commits | 30 |
| Sync | [`trishorts/logs`](https://github.com/trishorts/logs) |
| Locked decisions | 23 |
| Open gaps | 10 |
| Gate items skipped | 2 |

<!-- END GENERATED -->
