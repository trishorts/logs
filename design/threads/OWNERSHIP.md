# Capability ownership - logs

One owner per capability. Two claims, or none, is a **collision**: raise it in both threads at once
rather than letting two projects build their own version. Protocol: the `project` skill's
`references/threads.md`.

| Capability | Owner | Status | Source message |
|---|---|---|---|
| Cross-species gene orthology store (groups + pairwise relationships, versioned by source release) | logs | claimed 2026-09-22 | *(inception - not yet announced to peers)* |
| Orthology analysis views (all-orthologs / one-to-one / orthogroup / unresolved) | logs | claimed 2026-09-22 | *(inception - not yet announced to peers)* |
| Protein accession -> source gene resolution (UniProt / RefSeq) | **UNCLAIMED - possible collision with `dataRepo`** | open | *(to raise)* |
| Identifier storage / canonical accession normalization | **UNCLAIMED - possible collision with `dataRepo`** | open | *(to raise)* |
| GO / functional annotation across species | likely `go` | open | *(to confirm)* |

## Notes

- `logs` question-ID prefix is `LOGS-` (e.g. `LOGS-Q1`); requests to us are `REQ-LOGS-n`. The prefix
  names **who must answer**, not who asked.
- Nothing here is announced yet. The first outbound messages should claim the two orthology
  capabilities explicitly and open the accession-resolution seam with `dataRepo`.
