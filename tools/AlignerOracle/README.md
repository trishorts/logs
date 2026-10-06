# AlignerOracle

Checks mzLib's `Omics.SequenceAlignment.PairwiseAligner` against an independent implementation:
Biopython's `Align.PairwiseAligner`, with BLOSUM62, a gap open of -12 for the first residue and
-1 for each further residue (the same cost as mzLib's open 11 + extend 1), in global mode with
end gaps both free and charged.

```
python biopython_pairs.py                 # -> pairs.tsv: 3,000 random related pairs and Biopython's optimal score
dotnet run -c Release -- pairs.tsv        # mzLib's score for each; prints how many differ
```

2026-10-06, mzLib branch `feat/protein-pairwise-alignment`, Biopython 1.87: **3,000 pairs, 0 differ**.
The project reference points at the `code/` worktree; after the PR merges, point it at the mzLib package.
