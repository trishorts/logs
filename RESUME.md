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

Each of these cost real time on 2026-09-22.

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
6. **Pin a number when you send it, not later.** 007's "20,412 of 20,416" was never pinned, so when
   it moved nothing failed; it was caught only by reading. And never send a prototype's measurement:
   "563 KB" came from an awk extract, and the real file is 523 KB (corrected in 012).
7. **UniProt's rat XML links four Ensembl gene-id series** (`ENSRNOG00000…` is GRCr8; `…00055`,
   `…00060` and `…00065` are other annotations, none in the gene set). Without the gene set, most rat
   proteins look multi-gene. With it, 950 look `off_primary_only`, and Ensembl's xref rescues 521 of
   them.
8. **mzLib PR house style:** open against smith-chem-wisc, start the body with the
   `<!-- project-of-origin -->` "Project of origin" line, and use `type(scope): summary` commits.

## Pick up at

**1. Run the thread inbox** (`python "$env:USERPROFILE/.claude/skills/project/assets/threads.py" inbox`).
dataRepo owes an acknowledgement of 015 (it answered L1/L2/L3 and asked
LOGS-DR1, their row diff once their first pyMzLib run exists). aging 009 was judged to need no reply, but the inbox still flags aging as REPLY NEEDED (last=009-aging); read 009 and either reply or record why not.

**2. Deliver what 015 promised dataRepo.** It is small and it is owed:
- **A manifest per (species, release)** naming both resolver inputs with path and sha256: the
  gene-set table (`results/gene_sets/`) and Ensembl's `<Species>.<Assembly>.116.uniprot.tsv.gz` xref
  dump (source URL and sha in `data/PROVENANCE.md`). Without the xref dump, `ensembl_xref_agrees` is
  empty, and that column is aging's default view.
- **Charter seam S4:** a definition id for the resolution, registered with QuantProject. No channel
  to QuantProject is open yet. Open one (`threads.py new --to QuantProject`) carrying the concrete
  ask.

**3. Re-check #1338:** `gh pr view 1338 -R smith-chem-wisc/mzLib --json state,reviewDecision,mergeable`.
It has 10 commits and one approval (nbollis), and still shows as review-required. Alexander-Sol's
automated review is answered on the PR: two fixes (`2c30027b`, `2f40c40c`) and one finding refuted.
Nothing downstream can start until it merges and ships in an mzLib release. After that comes the
pyMzLib verb, which pyMzLib owns (charter S9). Run `/bridge-oracle pyMzLib` if we draft it.

**4. Next piece of work: PLAN step 6, the orthology store** (`design/PLAN.md`; its design notes are in
the `state.yaml` gaps). The rodent data it was waiting for now exists: aging's mouse and rat databases
are resolved (`results/search_db_resolution_{mouse,rat}.md`).

**Decided, do not re-open:**

- **dataRepo runs the resolution (option (a), user rule D24; accepted in 015).** We define the logic,
  the inputs and the release; dataRepo runs our released code through pyMzLib. Our human table
  (`results/search_db_human_e116.tsv.gz`, pinned) is only a **reference output** for their first run.
- **The table's key is `(search_database_sha256, gene_set_release, accession, gene_id)`.** 011 said
  `gene_stable_id`, and 015 corrected it. Accessions are proteoforms. Decoys never appear, and the
  contaminant database is not run.
- **Resolution does not go into MetaMorpheus output (user).**
- **Genes only Ensembl's xref links are emitted as rows** with `source = ensembl_xref`, carrying the
  XML's outcome (#1338 `3bb04188`).
- **The GTF is replaced by a compact gene table** (`EnsemblGeneSetReader`/`Writer`,
  `results/gene_sets/`). Its output is byte-identical to the GTF's.

**Open, and your call:**

- dataRepo has **not** been told the rat finding (four id series; 725 xref-only entries).
- The `go` thread is still unopened. Its content was the #1336 stack, which has since merged, so it
  may no longer be needed.
- The occupancy-manuscript findings have not been sent to Peter. mzLib #1337 is **approved** (nbollis),
  and Alexander-Sol's review is answered: the CNBr limit is documented as a non-goal in `815423f7`,
  not guarded in code. It waits on a merge; re-check with `gh pr view 1337 -R smith-chem-wisc/mzLib`.
  The worktree is level with its origin branch at `815423f7`.

**Where the resolution stands.** On aging's three reviewed-proteome search databases, counted in
entries, not proteoforms:

| | entries | resolved | multi-gene | off-primary only | no gene | xref resolves, XML does not |
|---|---:|---:|---:|---:|---:|---:|
| human (`760984e8…`), XML view | 20,416 | 18,988 | 350 | 62 | 1,016 | 4 |
| mouse (`fb52debf…`), XML view | 17,277 | 15,474 | 124 | 0 | 1,679 | 39 |
| rat (`abf612c9…`), XML view | 8,228 | 4,182 | 45 | 950 | 3,051 | 725 |

- By Ensembl's xref, 59.6% of rat entries resolve against 94.7% of human. That comes from the
  reference data, not from the searches.
- **Reproduce with:**
  `dotnet run --project tools/ResolveSearchDb -c Release -- <search.xml> results/gene_sets/<Species>.<Assembly>.116.genes.tsv.gz data/compara/<Species>.<Assembly>.116.uniprot.tsv.gz results/search_db_<sp>_e116.tsv`,
  then `python -m logs_orthology.search_db results/search_db_<sp>_e116.tsv --species <species> --out results/search_db_resolution_<sp>`.
  Omit `--out` and `--species` for human.
- **The XMLs:** human is `F:/aging_data/db/uniprotkb_proteome_UP000005640_AND_revi_2026_09_18.xml`.
  Mouse and rat are beside it, dated `2026-09-22`, and their `.gz` sources are in `F:/aging_data/db/src/`.

Sanity-check before changing anything:

```powershell
$env:PYTHONPATH = "E:\CodeReview\logs\src"
python tests/test_reported_claims.py    # 20 claims already sent to a partner
python tests/test_resolve.py            # 16 resolver contracts
python tests/test_contracts.py          # 10 contract tests
```

## Documents in `design/`

- `problem-statement.md` — the distilled problem and the eight locked constraints.
- `sources/cross_species_orthology_discussion.md` — the seed discussion, verbatim.
- `ORACLE.md` — the mzLib survey and the three-way split verdict.
- `PLAN.md` — ordered steps and the standing rules.
- `threads/OWNERSHIP.md` — capability ownership; both inception collisions closed.
- `threads/dataRepo/`, `threads/aging/` — correspondence.
- Outside `design/`: `results/gene_sets/README.md` records the compact gene tables and how to rebuild them.

<!-- BEGIN GENERATED -- render_resume.py owns this block; edit state.yaml, not here -->

**logs** &middot; phase **BUILD** (4/10) &middot; created 2026-09-22 &middot; rendered 2026-09-23

| | |
|---|---|
| Commits | 54 |
| Sync | [`trishorts/logs`](https://github.com/trishorts/logs) |
| Locked decisions | 36 |
| Open gaps | 8 |
| Gate items skipped | 2 |

**Worktrees** -- details in `code/PINNED.md`

| Worktree | Branch | HEAD | Pin | Status |
|---|---|---|---|---|
| `code/mzLib-ensembl-genes` | feat/ensembl-gene-resolution | `2f40c40c` | `2f40c40c` | at pin |
| `code/mzLib-occupancy-nterm` | fix/occupancy-met-cleaved-nterm | `815423f7` | `815423f7` | at pin |

<!-- END GENERATED -->
