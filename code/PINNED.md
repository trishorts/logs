# Code worktrees — logs

| worktree | repo | branch | pinned | based on | PR |
|---|---|---|---|---|---|
| `code/mzLib-ensembl-genes` | mzLib (`E:\GitClones\mzLib`) | `feat/ensembl-gene-resolution` (pushed to `origin` = trishorts) | `2f40c40c8b179a2d64a0063ab3a3a37ed410f87b` | `smith/master @ 588c2249` (#1336 merged 2026-09-22) | [#1338](https://github.com/smith-chem-wisc/mzLib/pull/1338) MERGED 2026-09-23 (`5d772a23`), mzLib 1.0.592 |
| `code/mzLib-occupancy-nterm` | mzLib | `fix/occupancy-met-cleaved-nterm` (pushed to `origin` = trishorts) | `815423f7` | `smith/master @ 588c2249` | [#1337](https://github.com/smith-chem-wisc/mzLib/pull/1337) MERGED 2026-09-23 (`b4361297`), mzLib 1.0.592 |
| `code/mzLib-orthology-store` | mzLib | `feat/compara-orthology-store` (pushed to `origin` = trishorts) | `6b3c4a26` | master merged in 2026-10-06 (`6b3c4a26`) | [#1381](https://github.com/smith-chem-wisc/mzLib/pull/1381) MERGED 2026-10-06 (squash `11c85118`), board #19 Shipped |
| `code/mzLib-residue-aligner` | mzLib | `feat/protein-pairwise-alignment` (pushed to `origin` = trishorts) | `2a5f418b6c4f7410588b866ba18b13791b6c2e52` | `smith/master @ b1e925ff` | [#1428](https://github.com/smith-chem-wisc/mzLib/pull/1428) MERGED 2026-10-10 (`8fc0840e`), board #19 Shipped |
| `code/mzLib-gene-tree-alignment` | mzLib | `feat/compara-gene-tree-alignment` (pushed to `origin` = trishorts) | `c96fafee03bf2e0e76347c22e38a6908ea8f1409` | `smith/master @ 8fc0840e` (rebased 2026-10-11) | [#1465](https://github.com/smith-chem-wisc/mzLib/pull/1465) opened 2026-10-11, board #19 In review, six referees; was fork draft trishorts/mzLib#8 (closed) |
| `code/mzLib-proteoform-accession` | mzLib | `feat/proteoform-accession` (pushed to `origin` = trishorts) | `5e323463f54eca14f4c261dbdcf792be713b4519` | `smith/master @ 2b16b41c` (rebased 2026-09-30) | [#1382](https://github.com/smith-chem-wisc/mzLib/pull/1382) opened 2026-09-28, board #19 In review; Alexander-Sol approved 2026-10-08, needs a second approval; PR head `620e8ab0` is a master merge on top of the pin |

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

**`mzLib-orthology-store`** is the orthology store (PLAN step 6, `logs:DEF-ORTHOLOGY v1`), moved into C# on 2026-09-27 at the user's instruction ("anything of substance should be in C# in mzLib"). The readers and `OrthologySnapshot` are in `UsefulProteomicsDatabases.Ensembl`. The Parquet writer (Parquet.Net 6.1.0, user-approved NuGet) was first its own `OrthologyStore` project; on 2026-10-05 review (nbollis) folded it into `UsefulProteomicsDatabases/Ensembl` (`2c1fd05`, snapshot byte-identical), and `e1d7b57` bumped `ZstdSharp.Port` to 0.8.8, the floor Parquet.Net needs (MetaMorpheus restore failed NU1605 on 0.8.7). On 2026-10-06 pcruzparri's review was addressed: `d5319af` stops comparing a GTF's file-name number with the Compara release (Ensembl 116 names the yeast/worm/fly GTFs `.63.`), and `b21aa4d` checks dump values on rows that are not kept; the snapshot is still byte-identical. `tools/BuildOrthologySnapshot` builds against `UsefulProteomicsDatabases.csproj` by relative path. The independent check is `src/logs_orthology/cardinality.py`, whose pinned figures the C# and DuckDB views reproduce exactly.

**`mzLib-proteoform-accession`** ports `resolve.normalize()`'s proteoform-to-entry rule (LOGS-D2) to `VariantApplication.ParseAccession` in Omics, beside `GetAccession` whose inverse it is (moved there 2026-09-30 at the user's request from `MzLibUtil`; returns an `Omics.BioPolymer.ProteoformAccession` with the verbatim accession, parent entry and applied variants, stripping nothing; `ProteinAccession.Parse` unchanged). Parity with `normalize()`: 78,774 accessions from our three reference tables, 0 differ. pyMzLib still has to project it before dataRepo can call it.

**`mzLib-residue-aligner`** (2026-10-06) is `Omics.SequenceAlignment`: `PairwiseAligner` (global, affine, Gotoh; BLOSUM62 / open 11 / extend 1 / free end gaps by default), `PairwiseAlignment` (1-based maps, a gap maps to nothing) and `SubstitutionMatrix` (NCBI format, BLOSUM62 embedded verbatim). These are legs 1 and 3 of `DEF-RESIDUE-CORRESPONDENCE`. It has 23 tests, and its scores match Biopython on 3,000 pairs (`tools/AlignerOracle`, which builds against this worktree by relative path). It is not stacked.

**`mzLib-gene-tree-alignment`** (2026-10-06) is `UsefulProteomicsDatabases.Ensembl.ComparaGeneTreeAlignment`, leg 2. It reads Compara's `aa.fasta.gz`, keeping the canonical proteins of a `ComparaGeneTreeContent`, and `MapResidue` returns one `ComparaColumnOutcome`. It has 16 tests: 15 in the suite and one `[Explicit]` on real 116 data (54,308 alignments, 64,114 proteins, 33 s). It waited as a fork draft (trishorts/mzLib#8) while #1381 was open. **#1381 was squash-merged**, so the branch still carried #1381's old commits; on 2026-10-11 only #8's own commit was moved (`git rebase --onto smith/master 6b3c4a262`; the Ensembl directory was identical between #8's base and master), giving `c96fafee0`. That was force-pushed to our fork (`--force-with-lease`) and opened upstream as #1465. The pre-rebase commit `7e5920597` is kept on the local branch `backup/compara-gene-tree-alignment-pre-rebase` (not pushed); delete it once #1465 merges.

**Merged worktrees** (`mzLib-orthology-store`, `mzLib-residue-aligner`) are historical pins like the 1.0.592 ones: their `origin` branches carry later master merges (residue-aligner is 22 behind), and new work starts from `smith/master`, which now holds the store (`11c85118`) and the aligner (`8fc0840e`).

**`mzLib-ensembl-genes` still matches the resolver that shipped** (checked 2026-10-11): between `2f40c40c` and smith/master no resolver file differs, and `ProteinDbLoader`/`ProteinXmlEntry` differ only in an entrapment refactor and RNA code. So `tools/ResolveSearchDb`, which builds against this worktree, measures what mzLib 1.0.594 and pyMzLib 0.2.0 run (`results/engine_parity_canonical-v3.json`: identical rows on the three canonical v3 databases).
