# Oracle (mzLib): residue correspondence, 2026-10-06

Run before any aligner code (CLAUDE.md rule 20; `/oracle mzLib`, Deep mode).

**Searched:** `smith/master @ b1e925ff9` (0 d old), clone `E:\GitClones\mzLib` (master, 13 behind).
**Open PRs:** 77 open in smith-chem-wisc/mzLib. None adds sequence alignment. #1123 (TopDownEngine)
and #1387 are retention-time alignment, and #786 is peak alignment. #1381, our own PR, is the
Compara store this work builds on. #1339 touches `VariantApplication`'s indel index arithmetic.

## Verdict: ADD-NEW, in two homes, stacked on #1381

| need | prior art on master | verdict |
|---|---|---|
| pairwise protein alignment (BLOSUM62, affine gaps), giving a residue position map | **none**. Searched NeedlemanWunsch, SmithWaterman, Blosum, SubstitutionMatrix, GapPenalty, EditDistance, Levenshtein, PositionMap and ~20 more. `PeptideWithSetModifications.GetPercentIdentity` (:1326) is private and compares equal-length strings position by position for decoys. It does not align | ADD-NEW in `Omics` (alphabet-generic; Omics owns BioPolymer and VariantApplication) |
| gapped MSA FASTA reader (Compara `aa.fasta.gz`) | **none**. `ProteinDbLoader.LoadProteinFasta` is unusable for this: `SanitizeAminoAcidSequence` (:579) turns every `-` into `X`, a bare `>ENSP…` header throws unless an `accessionRegex` is passed (:308), and repeated ids are renamed `_2` (:347) | ADD-NEW in `UsefulProteomicsDatabases/Ensembl`, e.g. `ComparaGeneTreeAlignment.Load` |
| variant to parent positions (the `variant` edge) | **partial**. `VariantApplication.RestoreModificationIndex` (:110) and `IsSequenceVariantModification` (:91) apply a length-delta shift with kept flanks. They work only on a Protein that mzLib built by applying variants | REUSE for the `variant` edge. Wrap it; do not re-derive the delta rule |

## Conventions the new code must match (from #1381 and master's Ensembl readers)

- **Failure:** a missing file throws `FileNotFoundException("<what> not found.", path)`. Malformed
  content throws `InvalidDataException("{fileName} line {n}: {what}")`. Every row is checked,
  whether or not it is kept: #1381's review found this as a defect. The class summary lists every refusal.
- **Absence:** `TryGet…(id, out x)`. An empty collection is `Array.Empty<T>()`. One enum outcome per
  input, never a bare null. NRT is not enabled; document null in XML.
- **Types:** `public sealed record` rows. A sealed container with a private constructor and a static
  `Load`/`Build`. `StringComparer.Ordinal`. The outcome enum is mapped to snake_case by an explicit
  switch (`_ => throw ArgumentOutOfRangeException`), and a test pins the names.
- **Provenance:** `SourceFileName`, `SourceSha256` (the bytes as read) and `Release`, parsed from the
  file name and null when absent. `RequireRelease` at Build. The MSA's proteins are checked against the
  store's `protein_a/b` and `CanonicalProteinId`.
- **gz:** `EnsemblFile.OpenText`/`Sha256` exist only in #1381, so stack on `feat/compara-orthology-store`.
- **Tests:** a synthetic gz in a GUID temp directory, with no checked-in Ensembl fixtures. Malformed
  input is tested from a `[TestCaseSource]` table of `(text, "line N: …")`. Real 116 data is
  `[Explicit]` behind an env var. The test-name dot rule is binding (`Check-TestNameHygiene.ps1`).

## Facts about the file, measured (not from the README)

`results/alignment_check_e116.md`, produced by `python -m logs_orthology.alignment_check`.
