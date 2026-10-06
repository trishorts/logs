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
9. **A row's `gene_set_sha256` is the GTF's sha256, not the gene-set table's** (the table's
   `#!source-sha256` header). The manifest gives both; check rows against its `row_values`.
10. **Read the partner's charter before promising a seam.** 015 and 016 promised S4 through
    QuantProject after charter v0.2 had already replaced the registry; 017 withdrew it.
11. **Count a gene view by the view, not by `outcome`.** `outcome` reports the search XML's links;
    the `ensembl_xref_agrees` view adds the xref-only rows. dataRepo's "48.6% of rat lost" was the
    XML's view; aging's own view keeps 59.6% of rat entries (022-logs).

## Pick up at

**Next action:** run the thread inbox. Replies are owed on **dataRepo 031** (DATAREPO-75: add a
read-in-place orthology engine to `datarepo run`; DATAREPO-76: build it now or wait for a consumer) and
possibly **ptmQtl 009** (outcome 13 `no_shared_alignment`; one alignment for both sha keys of each
agingPTM-v1 pair). Then check the board against the PRs:

```powershell
gh pr view 1381 --repo smith-chem-wisc/mzLib --json state,reviewDecision,comments   # orthology store
gh pr view 1382 --repo smith-chem-wisc/mzLib --json state,reviewDecision,comments   # VariantApplication.ParseAccession
gh pr view 1428 --repo smith-chem-wisc/mzLib --json state,reviewDecision,comments   # PairwiseAligner (opened 2026-10-06)
gh pr view 8 --repo trishorts/mzLib --json state,isDraft                            # ComparaGeneTreeAlignment, fork draft on 1381
```

#1381 is at `6b3c4a26` (a master merge on top of pcruzparri's two fixes, `d5319af` and `b21aa4d`).
That push dismissed nbollis's approval, so the six referees were re-requested on 2026-10-06. It needs a
re-approval and pcruzparri's re-review. CI is green.

**On a merge:**
- move that PR's board #19 card to Shipped;
- for #1381:
  - drop the pre-release flag (`gh release edit orthology-compara-116-b63a3331 --repo trishorts/logs --prerelease=false`);
  - rebase **trishorts/mzLib#8** onto smith/master and open it upstream with `ready for review` +
    `ready-for-agent`, the six referees (acesnik, Alexander-Sol, pcruzparri, zhuoxinshi, RayMSMS, nbollis)
    and a board card;
  - tell dataRepo (031 promised it);
- for #1382: run `/bridge-oracle pyMzLib` to project `ParseAccession`, then tell dataRepo (022 promised this).

**Stacked PRs stay drafts in the fork until their base merges** (user, 2026-10-06).

**The next build is the residue-correspondence builder** (`DEF-RESIDUE-CORRESPONDENCE v1`, now 13
outcomes, in `design/DEFINITIONS.md`). Its pieces exist:
- legs 1 and 3 use the aligner in #1428;
- leg 2 uses the reader in fork #8;
- the `variant` edge reuses `VariantApplication.RestoreModificationIndex` (oracle).

The oracle verdict and the conventions to match are in `design/ORACLE_residue_correspondence.md`. Run
`/oracle mzLib` again for the builder's home before writing it. 009 promised ptmQtl the residue-level
`not_on_ensembl_protein` rate with the first build. The by-entry rates (91.6 / 86.5 / 57.2%) are pinned.

**Waiting on others:**
- reviews of #1381 (re-approval + pcruzparri), #1382 and #1428;
- dataRepo on DATAREPO-75/76; ptmQtl on 009 (no ask, but a new outcome).

**State on 2026-10-06.**
- **Compara's alignment is pinned and checked** (`results/alignment_check_e116.md`):
  - it holds 54,308 alignments, and every store protein is in it once;
  - 760 ortholog rows (and every `other_paralog` row) join genes in two trees, hence `no_shared_alignment`.
- **The agingPTM-v1 builds are the same proteins as their bases** (`results/search_db_equivalence.md`),
  so ptmQtl's six databases need three alignments.
- **The orthology store is not active in any consumer yet.** The released tar is readable today (dataRepo
  029), and #1381 is needed only to build new snapshots. aging is the operator and gets it through
  dataRepo's runner. PXReprise sees it only through dataRepo's catalog.

**State on 2026-10-05.**
- **LOGS-D4 is closed: dataRepo reads the Parquet in place** (029). `DEF-ORTHOLOGY v1` is published
  with an explicit **file contract** (layout, columns, views, integrity, and what bumps
  `format_version`), sent as 030.
- **The store (PLAN step 6) is built** in mzLib #1381, branch `feat/compara-orthology-store` @
  `b21aa4dd` (the writer now lives in `UsefulProteomicsDatabases/Ensembl`), and **released**: pre-release
  [`orthology-compara-116-b63a3331`](https://github.com/trishorts/logs/releases/tag/orthology-compara-116-b63a3331),
  human, mouse and rat, Ensembl 116, 13 files, 9.0 MB.
  - The C# views, the DuckDB `views.sql` and `cardinality.py` agree on every pinned figure.
  - A rebuild is byte-identical.
  - Rebuild with `tools/BuildOrthologySnapshot`. `snapshots/` is gitignored and pinned by
    `test_first_orthology_snapshot_as_sent_in_026`.
- **The proteoform-to-entry rule is in mzLib #1382** (`VariantApplication.ParseAccession`, beside
  `GetAccession`, `f773e76a`). It returns the parent entry AND the applied variants; nothing is
  stripped. It matches `normalize()` on 78,774 accessions.
- **The repo is public**, MIT for code and CC-BY-4.0 for data (`LICENSING.md`).
- **LOGS-D1 to D4 and P4 are closed; P5 and P6 are open.** Partners have been told: dataRepo
  024-030, aging 015-017, ptmQtl 005-007, pride 003. aging 018 (their searches DO include small
  isoform databases) needed no reply; it agrees with the residue key.

**Decided, do not re-open:**

- **#1382 stays a PR, beside its producer (user, 2026-09-30).** The user had read it as stripping
  the variant suffix; it keeps it. Say plainly in any description that the variants are returned.

- **The store's shape (user, 2026-09-27).**
  - A builder plus snapshots, taking any Ensembl species list.
  - One Parquet file per species pair, plus gene-tree members.
  - N-way views check every pair and never chain.
  - Paralogs are included and typed.
- **Hosting (user, 2026-09-28).** This repo is public, and snapshots are its GitHub releases, with a
  Zenodo DOI once a snapshot is cited. The partner thread copies are public too, by the user's
  explicit choice.
- **Substance goes in C# in mzLib (user, 2026-09-27).** The Python in `src/` is measurement and test
  oracle. Parquet.Net is approved as an mzLib dependency. It sat in its own `OrthologyStore` project
  until review (2026-10-05) folded it into `UsefulProteomicsDatabases`: mzLib ships as one package,
  so a separate project isolated nothing.
- **dataRepo runs the resolution (option (a), user rule D24; accepted in 015).** We define the logic,
  the inputs and the release; dataRepo runs our released code through pyMzLib. Our human table
  (`results/search_db_human_e116.tsv.gz`, pinned) is only a **reference output** for their first run.
- **The table's key is `(search_database_sha256, gene_set_release, accession, gene_id)`.** 011 said
  `gene_stable_id`, and 015 corrected it. Decoys never appear, and the contaminant database is not
  run. Whether accessions are entries or proteoforms is **open** (LOGS-D2). A variant proteoform
  always has its entry's answer: 0 of 31,943 differ.
- **S4 is our own namespace, not a QuantProject registry** (charter v0.2). The id is
  `logs:DEF-GENE-RESOLUTION v1`. It pins the method, not the inputs. **A v1 run requires the xref
  input**, even though pyMzLib makes `xref=` optional.
- **Resolution does not go into MetaMorpheus output (user).**
- **Genes only Ensembl's xref links are emitted as rows** with `source = ensembl_xref`, carrying the
  XML's outcome (#1338 `3bb04188`).
- **The GTF is replaced by a compact gene table** (`EnsemblGeneSetReader`/`Writer`,
  `results/gene_sets/`). Its output is byte-identical to the GTF's.

**Open, and your call:**

- The occupancy-manuscript findings have not been sent to Peter. mzLib #1337 **merged** on
  2026-09-23 and is in 1.0.592. The CNBr limit is documented as a non-goal, not guarded in code.
- The `go` thread was dropped: its only content was the #1336 stack, and both PRs have merged.
- Whether the MIT copyright holder should be the lab or UW-Madison rather than Trish Shortreed
  (`LICENSE`).

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
python tests/test_reported_claims.py    # 29 claims already sent to a partner
python -m logs_orthology.manifest       # regenerate results/resolver_inputs_e116.{json,md}
python tests/test_resolve.py            # 21 resolver contracts
python tests/test_contracts.py          # 10 contract tests
```

## Documents in `design/`

- `problem-statement.md` — the distilled problem and the eight locked constraints.
- `sources/cross_species_orthology_discussion.md` — the seed discussion, verbatim.
- `ORACLE.md` — the mzLib survey and the three-way split verdict.
- `PLAN.md` — ordered steps and the standing rules.
- `DEFINITIONS.md` — our definition ids (charter S4): `logs:DEF-GENE-RESOLUTION v1`, `logs:DEF-ORTHOLOGY v1` (the store, published with its file contract) and `logs:DEF-RESIDUE-CORRESPONDENCE v1` (proposed, being built, 13 outcomes).
- `ORACLE_residue_correspondence.md` — the 2026-10-06 `/oracle mzLib` verdict for the aligner and the Compara reader, and the conventions they match.
- `threads/OWNERSHIP.md` — capability ownership; both inception collisions closed.
- `threads/dataRepo/`, `threads/aging/`, `threads/ptmQtl/`, `threads/pride/` — correspondence (public since 2026-09-28).
- Outside `design/`: `LICENSING.md` says which license covers what.
- Outside `design/`: `tools/AlignerOracle/README.md` checks #1428's aligner against Biopython.
- Outside `design/`: `results/gene_sets/README.md` records the compact gene tables and how to rebuild them.

<!-- BEGIN GENERATED -- render_resume.py owns this block; edit state.yaml, not here -->

**logs** &middot; phase **BUILD** (4/10) &middot; created 2026-09-22 &middot; rendered 2026-10-06

| | |
|---|---|
| Commits | 115 |
| Sync | [`trishorts/logs`](https://github.com/trishorts/logs) |
| Locked decisions | 49 |
| Open gaps | 9 |
| Gate items skipped | 2 |

**Worktrees** -- details in `code/PINNED.md`

| Worktree | Branch | HEAD | Pin | Status |
|---|---|---|---|---|
| `code/mzLib-ensembl-genes` | feat/ensembl-gene-resolution | `2f40c40c` | `2f40c40c` | at pin |
| `code/mzLib-occupancy-nterm` | fix/occupancy-met-cleaved-nterm | `815423f7` | `815423f7` | at pin |
| `code/mzLib-orthology-store` | feat/compara-orthology-store | `6b3c4a26` | `6b3c4a26` | at pin |
| `code/mzLib-proteoform-accession` | feat/proteoform-accession | `f773e76a` | `f773e76a` | at pin |
| `code/mzLib-residue-aligner` | feat/protein-pairwise-alignment | `284311ef` | `284311ef` | at pin |
| `code/mzLib-gene-tree-alignment` | feat/compara-gene-tree-alignment | `7e592059` | `7e592059` | at pin |

<!-- END GENERATED -->
