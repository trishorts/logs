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
12. **`ensembl_xref_agrees = false` means two different things.** Either Ensembl links the accession to
    another gene, or Ensembl's xref has never heard of the accession. On the canonical v3 databases, every
    dropped TrEMBL row is the second kind: accessions UniProt created after Ensembl 116's xref (rat 3,445).
    Tell them apart by the xref view's `not_in_source`, which is `search_db.py`'s `agree_or_silent_covered`.
13. **A squash-merged base leaves its old commits on a stacked branch.** #1381 merged as one commit, so #8's
    branch still carried #1381's history. Move only your own commits: `git rebase --onto smith/master <old base>`.

## Pick up at

**Next action:** run the thread inbox. Nothing is owed by us. Four answers are owed **to** us, and each one
decides work:
- **ptmQtl LOGS-P7** (010-logs): which search databases get residue rows, and the join key under their D35
  (sites pool by 15-residue window; the database is provenance only). **The builder's database list waits on this.**
- **aging REQ-AGING-9** (021-logs): would they take a v2 "agrees or silent" gene view as their default? If yes,
  run `/oracle mzLib` for a marker in `EnsemblGeneResolver`, then write `DEF-GENE-RESOLUTION v2`.
- **PXReprise PXR-O9** (009-logs: where the orthology snapshot is hosted under D41, with its licences) and
  **PXR-O10** (010-logs: tell us when the first canonical bundle is resolved). On O10, diff its rows against
  `results/search_db_<sp>_canonical-v3_e116.tsv`, which is machine-local; rebuild it with the commands below.

Then check the open PRs:

```powershell
gh pr view 1465 --repo smith-chem-wisc/mzLib --json state,reviewDecision,comments   # ComparaGeneTreeAlignment (opened 2026-10-11)
gh pr view 1382 --repo smith-chem-wisc/mzLib --json state,reviewDecision,comments   # VariantApplication.ParseAccession
gh pr checks 1465 --repo smith-chem-wisc/mzLib
```

- **#1382** has one approval (Alexander-Sol, 2026-10-08), green CI and no conflicts. It is blocked only on a
  second approval. The user chose (2026-10-11) not to nudge.
- **#1465** is #8's single commit rebased onto master (`c96fafee0`), with the six referees requested.

**On a merge:**
- move that PR's board #19 card to Shipped;
- for #1382: run `/bridge-oracle pyMzLib` to project `ParseAccession`, then tell dataRepo (022 promised this);
- for #1465: delete the local branch `backup/compara-gene-tree-alignment-pre-rebase` in
  `code/mzLib-gene-tree-alignment`.

**Stacked PRs stay drafts in the fork until their base merges** (user, 2026-10-06).

**The next build is the residue-correspondence builder** (`DEF-RESIDUE-CORRESPONDENCE v1`, 13 outcomes, in
`design/DEFINITIONS.md`), written on smith/master. Its pieces:
- legs 1 and 3 use `Omics.SequenceAlignment.PairwiseAligner` (#1428, merged);
- leg 2 uses `ComparaGeneTreeAlignment` (#1465, in review). Stack on #1465's branch, or wait for it to merge;
- the `variant` edge reuses `VariantApplication.RestoreModificationIndex` (oracle).

The oracle verdict and conventions are in `design/ORACLE_residue_correspondence.md`. Run `/oracle mzLib` again
for the builder's home before writing it. 009 promised ptmQtl the residue-level `not_on_ensembl_protein` rate
with the first build. Pinned by-entry leg-1 rates: reviewed 91.6 / 86.5 / 57.2%, and canonical v3
91.3 / 87.4 / 77.4% (h/m/r).

**dataRepo 032 needs no reply now.** When residue rows exist, tell dataRepo **and** PXReprise how they reach the
repository. Under D41 that is probably an engine keyed per search database and run at ingest, like
`logs.resolve_genes`.

**Waiting on others:** the four answers above, and reviews of #1382 and #1465.

**State on 2026-10-11.**
- **#1381 merged** (2026-10-06, squash `11c85118`) and **#1428 merged** (2026-10-10, `8fc0840e`). Both cards are
  Shipped, and the release is no longer a pre-release.
- **PXReprise now owns how the pipeline publishes** (their D41). Every search moves to UniProt's canonical
  gene-centric proteomes (their D38), and the searched files are **agingPTM-v3**: human `fd80cf88…`, mouse
  `3c4ac3fb…`, rat `7f08fd3c…`.
- **Gene resolution on canonical v3** (`results/search_db_resolution_<sp>_canonical-v3.md`, sent as 010-logs):

  | | reviewed, agrees view | canonical, agrees view | canonical, UniProt's links | canonical, agrees or silent |
  |---|---:|---:|---:|---:|
  | human | 94.7% | 94.4% (19,505 / 20,652) | 94.5% | 94.6% |
  | mouse | 90.4% | 87.5% (19,130 / 21,860) | 92.5% | 92.7% |
  | rat | 59.6% (4,908) | 68.5% (14,714 / 21,471) | 81.4% | 84.8% |

  - pyMzLib 0.2.0, the engine's call, gives our C# rows exactly (`results/engine_parity_canonical-v3.json`).
  - The gap between the columns is **3,445 rat and 1,105 mouse TrEMBL accessions that Ensembl 116's xref has never
    heard of**, created by UniProt in 2025-2026.
  - Every canonical TrEMBL entry carries an Ensembl dbReference.
- **Leg 1 on canonical** (`results/leg1_canonical-v3_e116.md`): rat is 77.4% exact. All 13,258 canonical rat
  TrEMBL entries cite the Ensembl consortium, and 87.5% of them are identical to the tree protein. Rat
  Swiss-Prot is unchanged at 57.3%.
- **Known gap:** `LICENSING.md` is not inside the release tar (PXR-O9).

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

- **Canonical v3 resolves on `DEF-GENE-RESOLUTION v1` unchanged (user, 2026-10-11).** The first canonical
  delivery does not wait for a v2. "Agrees or silent" is proposed, not promised, and waits on aging
  (REQ-AGING-9). Rejected: UniProt's links as the default (human multi-gene 71 -> 352), and a newer Ensembl
  (it re-pins everything, and the lag recurs).
- **Gene resolution and residue rows are per search database, not per deposit** (PXR-O8, 2026-10-11). Nothing
  of ours reads PSMs or needs a corpus-wide recompute at publish.

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
- **Canonical v3** (2026-10-11): the same two commands on `F:/aging_data/db/UP0000*_all_genecentric_2026_03_agingPTM-v3.xml`,
  writing `results/search_db_<sp>_canonical-v3_e116.tsv`, with `--xml <the XML> --out results/search_db_resolution_<sp>_canonical-v3`.
  Then run `python -m logs_orthology.engine_parity` (pyMzLib against the C# rows) and
  `python -m logs_orthology.alignment_check --databases canonical-v3` (leg 1). The usage is in each module's docstring.
- **The XMLs:** human is `F:/aging_data/db/uniprotkb_proteome_UP000005640_AND_revi_2026_09_18.xml`.
  Mouse and rat are beside it, dated `2026-09-22`, and their `.gz` sources are in `F:/aging_data/db/src/`.

Sanity-check before changing anything:

```powershell
$env:PYTHONPATH = "E:\CodeReview\logs\src"
python tests/test_reported_claims.py    # 31 claims already sent to a partner
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
- `threads/dataRepo/`, `threads/aging/`, `threads/ptmQtl/`, `threads/pride/`, `threads/PXReprise/` — correspondence (public since 2026-09-28; PXReprise since 2026-10-07).
- `NOTE_FROM_CodeReview_2026-10-06_alexsol-review-fixes.md` — a sweep note that Alexander-Sol's 2026-10-06 reviews of #1382 and #1428 were addressed (already in the journal; kept as the cross-session signal).
- Outside `design/`: `LICENSING.md` says which license covers what.
- Outside `design/`: `tools/AlignerOracle/README.md` checks #1428's aligner against Biopython.
- Outside `design/`: `results/gene_sets/README.md` records the compact gene tables and how to rebuild them.

<!-- BEGIN GENERATED -- render_resume.py owns this block; edit state.yaml, not here -->

**logs** &middot; phase **BUILD** (4/10) &middot; created 2026-09-22 &middot; rendered 2026-10-11

| | |
|---|---|
| Commits | 134 |
| Sync | [`trishorts/logs`](https://github.com/trishorts/logs) |
| Locked decisions | 52 |
| Open gaps | 10 |
| Gate items skipped | 2 |

**Worktrees** -- details in `code/PINNED.md`

| Worktree | Branch | HEAD | Pin | Status |
|---|---|---|---|---|
| `code/mzLib-ensembl-genes` | feat/ensembl-gene-resolution | `2f40c40c` | `2f40c40c` | at pin |
| `code/mzLib-occupancy-nterm` | fix/occupancy-met-cleaved-nterm | `815423f7` | `815423f7` | at pin |
| `code/mzLib-orthology-store` | feat/compara-orthology-store | `6b3c4a26` | `6b3c4a26` | at pin |
| `code/mzLib-proteoform-accession` | feat/proteoform-accession | `5e323463` | `5e323463` | at pin |
| `code/mzLib-residue-aligner` | feat/protein-pairwise-alignment | `2a5f418b` | `2a5f418b` | at pin |
| `code/mzLib-gene-tree-alignment` | feat/compara-gene-tree-alignment | `c96fafee` | `c96fafee` | at pin |

<!-- END GENERATED -->
