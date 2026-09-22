# Code worktrees — logs

| worktree | repo | branch | based on | purpose |
|---|---|---|---|---|
| `code/mzLib-ensembl-genes` | mzLib (`E:\GitClones\mzLib`) | `feat/ensembl-gene-resolution` | `trishorts:feat/go-terms-accessor @ 118a2ffd` (PR #1336, OPEN) | Port accession -> gene resolution to C# (PLAN step 5). **Stacked on #1336**: retarget to master and rebase once #1336 merges. Push to `origin` (trishorts fork). |

Test oracle for the port: `src/logs_orthology/resolve.py` + `tests/test_resolve.py`.
