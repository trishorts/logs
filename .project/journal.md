# Journal - logs

Append-only. One line per phase change, locked decision, or consciously-skipped gate item.

- 2026-09-22 - project created (`/project init logs`), phase INCEPTION. Seeded
  `design/problem-statement.md` from the cross-species orthology workflow discussion
  (`C:\Users\trish\Downloads\cross_species_protein_orthology_workflow.md`).
- 2026-09-22 - decision: name is "logs" (homo-/ortho-/para-logs). Question-ID prefix LOGS-.
- 2026-09-22 - decision: generic engineering scope; `aging` is the first consumer, `dataRepo` the
  near-term neighbour. Interproject threads enabled.
- 2026-09-22 - /oracle mzLib run (3 investigators + open-PR sweep, smith/master @ 0b614b4b).
  Findings in `design/ORACLE.md`. Verdict: the layers split - accession->gene EXTENDs mzLib
  (the cross-references are already in `Protein.DatabaseReferences`, just never read back by
  type), the ID-mapping client is a natural mzLib sibling, and the versioned relational
  orthology STORE does not belong in mzLib (it would be its first self-managed on-disk database
  and its first DB dependency outside vendor-file reading). Gaps sharpened accordingly; nothing
  locked yet - the split is the user's call.
