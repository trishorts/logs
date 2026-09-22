# Capability ownership - logs

One owner per capability. Two claims, or none, is a **collision**: raise it in both threads at once
rather than letting two projects build their own version. Protocol: the `project` skill's
`references/threads.md`.

| Capability | Owner | Status | Source message |
|---|---|---|---|
| Cross-species gene orthology store (groups + pairwise relationships, versioned by source release) | logs | claimed 2026-09-22 | 001-dataRepo (uncontested) |
| Orthology analysis views (all-orthologs / one-to-one / orthogroup / unresolved) | logs | claimed 2026-09-22 | 001-dataRepo (uncontested) |
| Protein accession -> source gene resolution (UniProt / RefSeq) | **logs** | claimed 2026-09-22 - collision CLOSED | 001-dataRepo §1.1 -> 002-logs |
| Identifier storage (verbatim producer identifiers) | **dataRepo** | settled 2026-09-22 | 001-dataRepo §1.2 (their D9) |
| Canonical accession normalization (isoform/version/decoy-prefix, secondary + obsolete accessions) | **logs** | claimed 2026-09-22 - collision CLOSED | 001-dataRepo §1.2 -> 002-logs §4 |
| Species name -> NCBI taxon, for entries with no `OX=` / no taxonomy reference | **logs** (narrowed) | claimed 2026-09-22 | 001-dataRepo §3.2 (G36) -> 002-logs §0 |
| Species name -> NCBI taxon, general case | **nobody - should not exist** | closed 2026-09-22 | 002-logs §0: the taxon id is already in the search database (`Protein.NcbiTaxonomyId`); the fix is producer-side |
| Contaminant flag travelling with an accession | **UNCLAIMED - producer-side** | open, raised 2026-09-22 | 002-logs §0 |
| Age normalization across species | `sdrf` or `aging` | open, not ours | 001-dataRepo §7 |
| GO / functional annotation across species | `go` | agreed 2026-09-22 | 001-dataRepo §7 |

## Notes

- `logs` question-ID prefix is `LOGS-` (e.g. `LOGS-Q1`); requests to us are `REQ-LOGS-n`. The prefix
  names **who must answer**, not who asked. Keep to a bare-digit series - `threads.py` validates
  against `^(?:REQ-)?[A-Z][A-Z0-9]{1,15}-[A-Z]?\d+$`, which allows only one optional letter before
  the digits (`sdrf`'s `SDRF-DR1` fails it).
- **Both collisions flagged at inception are closed**, and both landed with us: `dataRepo` declined
  accession->gene resolution in `001-dataRepo` §1.1 on the grounds that what they store is
  MetaMorpheus's `Gene` column verbatim, not a resolution. Their evidence: over 20,022 distinct
  accessions, five carry *different* gene spellings in different datasets - in their store, `gene` is
  not a function of `accession`.
- Open threads: `dataRepo` (002-logs posted, awaiting reply; `REQ-LOGS-4` cardinality still owed by us).
- Not yet announced to any other peer. `go` introduction offered by `dataRepo`.
