# NOTE from the E:\CodeReview sweep → logs, 2026-10-06

**Topic:** Alexander-Sol's 10-06 reviews on logs' two mzLib PRs were addressed today from inside this
project (worktrees `code/mzLib-proteoform-accession`, `code/mzLib-residue-aligner`; recorded in
`.project/journal.md` and `state.yaml`, logs commit `7f950d3`). This note exists so a live logs session
sees it without reading the journal.

## #1382 — ParseAccession (behaviour change)
- **Stop-gain / stop-loss accessions now parse** (`5e323463f`). The suffix pattern in
  `VariantApplication.cs` is `_[A-Z*]+\d+[A-Z*]*`, so `P12345_Q5*` and `P12345_*70R` split into entry +
  applied variants instead of coming back `Unrecognized`. Before, any VCF/SnpEff `stop_gained` proteoform
  could not be linked to its entry.
- Round-trip test now compares `AppliedVariants` to the real suffix and the joined `SimpleString()`s,
  and includes a `G11*` stop-gain. 44/44 across TestProteoformAccession, VariantApplication, ProteinAccession.
- **Same gap fixed in our Python oracle:** `resolve.py`'s variant-suffix pattern now allows `*`
  (21/21 resolver tests, 29/29 reported claims still pass). Any earlier logs number that counted
  Unrecognized proteoform accessions may have included stop-gain variants — re-check if quoted.

## #1428 — PairwiseAligner (contract tightened)
- Constructor refuses `maxCells > Array.MaxLength` (`ArgumentOutOfRangeException`) (`2a5f418b6`).
- **`Align` now throws `ArgumentException` on `-` or `.`** in either sequence. Relevant for the planned
  Compara gene-tree step: strip gaps from alignment rows before calling `Align`. 27/27 tests.

Both PRs have a reply to Alexander-Sol. #1382's CHANGES_REQUESTED stands until he re-reviews; #1428 is approved.
