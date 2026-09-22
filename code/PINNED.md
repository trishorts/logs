# Code worktrees — logs

| worktree | repo | branch | pinned | based on | PR |
|---|---|---|---|---|---|
| `code/mzLib-ensembl-genes` | mzLib (`E:\GitClones\mzLib`) | `feat/ensembl-gene-resolution` (pushed to `origin` = trishorts) | `3bb04188` (pushed) | `smith/master @ 588c2249` (#1336 merged 2026-09-22) | [#1338](https://github.com/smith-chem-wisc/mzLib/pull/1338) |
| `code/mzLib-occupancy-nterm` | mzLib | `fix/occupancy-met-cleaved-nterm` (pushed to `origin` = trishorts) | `e3282169d4de3a2b2db8dcf7760e2da3597f509f` | `smith/master @ 890036fb` | [#1337](https://github.com/smith-chem-wisc/mzLib/pull/1337) |

**`mzLib-ensembl-genes`** is the C# port of accession → gene resolution (PLAN step 5). The user moved
it into mzLib on 2026-09-22. #1336 merged on 2026-09-22; the branch was rebased onto master (GO commit dropped, commits reworded
to `type(scope):`) and opened as #1338. A seventh commit, `34e20ca6`, adds `EnsemblGeneSetReader`/
`EnsemblGeneSetWriter` (the compact gene table, `results/gene_sets/`). An eighth, `3bb04188`, emits a
`source = ensembl_xref` row for each gene only Ensembl's xref links (rat: 725 entries); 78 Ensembl/accession
tests pass, 836 in the broader filter. The Python prototype and test oracle
are `src/logs_orthology/resolve.py` + `tests/test_resolve.py`. `tools/ResolveSearchDb` builds against
this worktree by relative path.

**`mzLib-occupancy-nterm`** is not `logs` scope. It fixes `ModificationOccupancyCalculator` dropping
protein N-terminal mods on Met-removed N-termini, and was found while checking the occupancy
manuscript against the code. It is isolated from master and test-first; the full offline suite
passes (6,607/0/32). Peter's #1286/#1287 rewrite the same file, and the user chose not to wait for them.
