# Code worktrees — logs

| worktree | repo | branch | pinned | based on | PR |
|---|---|---|---|---|---|
| `code/mzLib-ensembl-genes` | mzLib (`E:\GitClones\mzLib`) | `feat/ensembl-gene-resolution` (pushed to `origin` = trishorts) | `c1365ade405d4c75e47591312e750c6d1da2ed4a` | `trishorts:feat/go-terms-accessor @ 118a2ffd` (**#1336**, approved 2026-09-22) | none yet |
| `code/mzLib-occupancy-nterm` | mzLib | `fix/occupancy-met-cleaved-nterm` (pushed to `origin` = trishorts) | `e3282169d4de3a2b2db8dcf7760e2da3597f509f` | `smith/master @ 890036fb` | [#1337](https://github.com/smith-chem-wisc/mzLib/pull/1337) |

**`mzLib-ensembl-genes`** is the C# port of accession → gene resolution (PLAN step 5). The user moved
it into mzLib on 2026-09-22. It has six commits on #1336, and 62 tests pass. It is **stacked**: when
#1336 merges, rebase onto master, retarget, then open the PR. The Python prototype and test oracle
are `src/logs_orthology/resolve.py` + `tests/test_resolve.py`. `tools/ResolveSearchDb` builds against
this worktree by relative path.

**`mzLib-occupancy-nterm`** is not `logs` scope. It fixes `ModificationOccupancyCalculator` dropping
protein N-terminal mods on Met-removed N-termini, and was found while checking the occupancy
manuscript against the code. It is isolated from master and test-first; the full offline suite
passes (6,607/0/32). Peter's #1286/#1287 rewrite the same file, and the user chose not to wait for them.
