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

**First, re-check #1336:** `gh pr view 1336 --repo smith-chem-wisc/mzLib --json state,reviewDecision`.
It was **APPROVED** on 2026-09-22.

- **If it has merged:** in `code/mzLib-ensembl-genes`, rebase `feat/ensembl-gene-resolution` onto
  `smith/master`. Re-run `dotnet test … --filter "FullyQualifiedName~TestEnsembl|FullyQualifiedName~TestProteinAccession"`,
  where 62 should pass. Then **open the resolution PR** from `trishorts`.
- **If it is still open:** the branch stays stacked, and nothing is blocked.

**Then the user's choice, left open at close:**

- **(a) MetaMorpheus output.** Write the resolution into a long-format table in MetaMorpheus's output
  (one row per (accession, gene)). dataRepo's 009 §6 says nothing reaches them otherwise. It is a
  separate MetaMorpheus PR: run `/oracle MetaMorpheus` first.
- **(b) Open a `go` thread.** `threads.py new --to go`. The content is that our branch is stacked on
  their #1336 and uses its idiom in `Protein.cs`; ask for a warning before any force-push.

**Where the port stands:** `Protein.EnsemblGeneReferences`, `EnsemblGeneSet.LoadGtf`,
`ProteinAccession.Parse`, `EnsemblGeneResolver` + `GeneResolutionTsv`, and `EnsemblXrefTable`, which
feeds a per-gene `ensembl_xref_agrees` column. Pins and context are in `code/PINNED.md`.

- **On aging's search database:** 20,416 entries (52,359 proteoforms, since variants are applied)
  resolve to 18,988 `resolved`, 350 `multi_gene`, 62 `off_primary_only` and 1,016 `not_in_source`
  from the XML's own links.
- **Filtering `ensembl_xref_agrees = true`** gives Ensembl's view (69 multi-gene) and matches
  `resolve.py` for 20,412/20,416.
- **Reproduce with** `dotnet run --project tools/ResolveSearchDb -c Release -- <search.xml> <gtf.gz> <uniprot.tsv.gz> results/search_db_human_e116.tsv`,
  then `python -m logs_orthology.search_db results/search_db_human_e116.tsv`. The decompressed XML is
  not in the repo: decompress `E:/CodeReview/go/data/raw/uniprotkb_proteome_UP000005640_AND_revi_2026_09_18.xml.gz`
  and check its sha256 is `760984e8…a7be8838`.

**Waiting on:**

- aging: reply to 007 (the table's two views).
- dataRepo: reply to 010.
- mzLib **#1337** (our occupancy N-terminal fix) needs review.
- The rodent searches (aging 006: about a day). They un-defer the **store** (PLAN step 6), which
  stays in `logs`.

**Not yet done on purpose:** the occupancy-manuscript findings have not been sent to Peter; that is
the user's call. The pass found the Met-removed N-terminal bug (now #1337), the wrong mzLib version
(1.0.586; 1.1.9 uses 1.0.588) and wording errors. The details are in the journal entry for this
session.

Sanity-check the inputs still reproduce before changing anything:

```powershell
$env:PYTHONPATH = "E:\CodeReview\logs\src"
python tests/test_reported_claims.py    # 16 claims already sent to a partner
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
| Commits | 40 |
| Sync | [`trishorts/logs`](https://github.com/trishorts/logs) |
| Locked decisions | 29 |
| Open gaps | 5 |
| Gate items skipped | 2 |

**Worktrees** -- details in `code/PINNED.md`

| Worktree | Branch | HEAD | Pin | Status |
|---|---|---|---|---|
| `code/mzLib-ensembl-genes` | feat/ensembl-gene-resolution | `c1365ade` | `c1365ade` | at pin |
| `code/mzLib-occupancy-nterm` | fix/occupancy-met-cleaved-nterm | `e3282169` | `e3282169` | at pin |

<!-- END GENERATED -->
