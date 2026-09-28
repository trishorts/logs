# Code worktrees — logs

| worktree | repo | branch | pinned | based on | PR |
|---|---|---|---|---|---|
| `code/mzLib-ensembl-genes` | mzLib (`E:\GitClones\mzLib`) | `feat/ensembl-gene-resolution` (pushed to `origin` = trishorts) | `2f40c40c8b179a2d64a0063ab3a3a37ed410f87b` | `smith/master @ 588c2249` (#1336 merged 2026-09-22) | [#1338](https://github.com/smith-chem-wisc/mzLib/pull/1338) MERGED 2026-09-23 (`5d772a23`), mzLib 1.0.592 |
| `code/mzLib-occupancy-nterm` | mzLib | `fix/occupancy-met-cleaved-nterm` (pushed to `origin` = trishorts) | `815423f7` | `smith/master @ 588c2249` | [#1337](https://github.com/smith-chem-wisc/mzLib/pull/1337) MERGED 2026-09-23 (`b4361297`), mzLib 1.0.592 |
| `code/mzLib-orthology-store` | mzLib | `feat/compara-orthology-store` (pushed to `origin` = trishorts) | `16c6a8d9` | `smith/master @ 636d25c5` (2026-09-27) | [#1381](https://github.com/smith-chem-wisc/mzLib/pull/1381) opened 2026-09-28, board #19 In review |
| `code/mzLib-proteoform-accession` | mzLib | `feat/proteoform-accession` (pushed to `origin` = trishorts) | `7faba057` | `smith/master @ 636d25c5` (2026-09-28) | [#1382](https://github.com/smith-chem-wisc/mzLib/pull/1382) opened 2026-09-28, board #19 In review |

**`mzLib-ensembl-genes`** is the C# port of accession → gene resolution (PLAN step 5). The user moved
it into mzLib on 2026-09-22. #1336 merged on 2026-09-22; the branch was rebased onto master (GO commit dropped, commits reworded
to `type(scope):`) and opened as #1338. A seventh commit, `34e20ca6`, adds `EnsemblGeneSetReader`/
`EnsemblGeneSetWriter` (the compact gene table, `results/gene_sets/`). An eighth, `3bb04188`, emits a
`source = ensembl_xref` row for each gene only Ensembl's xref links (rat: 725 entries); 78 Ensembl/accession
tests pass, 836 in the broader filter. Two review fixes followed on 2026-09-23 (Alexander-Sol's automated review):
`2c30027b` makes `GeneResolutionTsv` refuse a tab or line break in a cell and write `
`, and `2f40c40c`
stops Ensembl references with an empty transcript id collapsing into one. 91 Ensembl/accession/TsvWriter
tests pass. nbollis approved; the PR still shows review-required. The Python prototype and test oracle
are `src/logs_orthology/resolve.py` + `tests/test_resolve.py`. `tools/ResolveSearchDb` builds against
this worktree by relative path.

**`mzLib-occupancy-nterm`** is not `logs` scope. It fixes `ModificationOccupancyCalculator` dropping
protein N-terminal mods on Met-removed N-termini, and was found while checking the occupancy
manuscript against the code. It is isolated from master and test-first; the full offline suite
passes (6,607/0/32). Peter's #1286/#1287 rewrite the same file, and the user chose not to wait for them.

**Both PRs merged on 2026-09-23 and ship in mzLib 1.0.592** (2026-09-24). The worktrees are kept at their pins. Their `origin` branches are 8 and 6 commits ahead. For #1338 those commits are two merges from master and the master commits they brought in; #1337 was not checked. No resolver file differs between `2f40c40c` and the merged head. New resolver work starts from `smith/master`, not from these branches. pyMzLib 0.2.0 projects #1338 as `proteins.resolve_genes()`.

**`mzLib-orthology-store`** is the orthology store (PLAN step 6, `logs:DEF-ORTHOLOGY v1`), moved into C# on 2026-09-27 at the user's instruction ("anything of substance should be in C# in mzLib"). The readers and `OrthologySnapshot` are in `UsefulProteomicsDatabases.Ensembl`. The Parquet writer is the new `OrthologyStore` project, which adds Parquet.Net 6.1.0 (the user approved the NuGet). `tools/BuildOrthologySnapshot` builds against it by relative path. The independent check is `src/logs_orthology/cardinality.py`, whose pinned figures the C# and DuckDB views reproduce exactly.

**`mzLib-proteoform-accession`** ports `resolve.normalize()`'s proteoform-to-entry rule (LOGS-D2) to `MzLibUtil.ProteoformAccession` (additive; `ProteinAccession.Parse` unchanged). Parity with `normalize()`: 78,774 accessions from our three reference tables, 0 differ. pyMzLib still has to project it before dataRepo can call it.
