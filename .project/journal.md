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
- 2026-09-22 - first thread traffic. dataRepo opened the channel (001-dataRepo) on the day we were
  created, answering both collisions we had flagged rather than asking about them: accession->gene
  resolution is ours (their `gene` column is MetaMorpheus`s Gene string stored verbatim - five of
  20,022 accessions disagree with themselves across datasets), and identifier storage splits from
  normalization, storage theirs and normalization ours. Replied 002-logs, answering 4 of their 5.
  Ownership collisions CLOSED; taxa confirmed 9606/10090/10116; two modelling decisions locked
  (group vs relationship are two objects; group ids are not stable across releases). REQ-LOGS-4
  left open on cardinality - to be measured, not estimated. Asked REQ-DATAREPO-1..3, of which
  REQ-DATAREPO-1 (XML- vs FASTA-derived corpus) decides our v1 scope.
- 2026-09-22 - user: "ask questions. answer questions. express your needs openly" - a lesson about
  all partners, not just dataRepo. Posted 005-logs stating the three needs we had not stated
  (blocker vs improvement; do they want the mzLib half early; "generic" is unfalsified), and
  opened the aging channel (001-logs) - our first consumer, whom we had only heard through
  dataRepo. Rule added to CLAUDE.md so it governs the next session.
- 2026-09-22 - BUILD begins. Fetched and verified 16 pinned Ensembl 116 files (673 MB, 15 of 16
  checksum-verified). Measured REQ-LOGS-4/6 and posted 006-logs: 76.97% clean 1:1:1, 45 genes
  clean pairwise but not as a triple, 2,269 human genes with no rodent ortholog at all. Corrected
  two of the four refusal classes we had promised - one underivable from Compara, one empty in
  this release. Found and made reproducible the file-partition trap (all human-mouse orthologies
  live in the MOUSE dump; the human dump has none). 8/8 contract tests green.
