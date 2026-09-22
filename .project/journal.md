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
- 2026-09-22 - user: "check your work". Two wrong denominators found, one of which had already
  been sent. (1) Eligible set was protein_coding alone; Compara also trees IG/TR gene segments,
  so every cardinality rate was ~1pt off - clean 1:1:1 76.97 -> 75.49. Corrected to dataRepo in
  007-logs. (2) Multi-gene rate counted raw gene ids including ALT haplotypes: 6.99% vs 0.36%
  restricted to the primary assembly, a 20x error, and it manufactured a "human much worse than
  rodents" difference that does not exist. Caught before sending. (3) _dist bucketed zero genes
  as 4+. All three pinned by regression tests. New file tests/test_reported_claims.py pins every
  number SENT TO A PARTNER, so a future re-run that moves one fails loudly instead of leaving a
  wrong number in their schema.

## 2026-09-22 — session close-out: inception to first measurements in one day

The project was created this morning from a seed discussion and ended the day with pinned data,
working code, two measured deliverables, seven messages to one peer and an opened channel to a
second. The narrative worth keeping is mostly about what turned out to be wrong.

**What the day produced.** A `/project` scaffold; the problem statement distilled from the seed doc
with eight locked constraints; an `/oracle mzLib` survey (`design/ORACLE.md`) that split the project
three ways; `design/PLAN.md`; a release-pinned fetcher over Ensembl 116 (16 files, 673 MB, 15 of 16
checksum-verified); streaming loaders; the cardinality measurement owed to `dataRepo`; the accession
-> gene resolution measurement; and 22 tests across two suites.

**The oracle changed the shape of the project.** The expectation was "build a thing, maybe in
mzLib". The answer was that it splits: accession->gene *extends* mzLib because every UniProt
`<dbReference>` is already parsed onto `Protein.DatabaseReferences` and simply never read back by
type; the ID-mapping client is a natural sibling to `ProteinDbRetriever`; and the relational store
does **not** belong there, because mzLib has no self-managed on-disk database and
`ControlledVocabulary.cs:25-27` pre-emptively argues against exactly this. The counter-argument we
would have to make — an orthology map is a *join table*, not a lookup vocabulary — is real but not
worth spending at inception on an unproven schema.

**Four things we got wrong, in the order we found them.**

1. *The dataRepo hypothesis.* We guessed their five self-disagreeing accessions came from different
   search databases. Identical sha256 across all nine datasets killed it outright. What they found
   instead was better: a ragged `|`-join in the producer TSV, 182 rows, 60 affected accessions.
   Recorded as wrong in the thread rather than dropped quietly.
2. *The contaminant flag.* We told them it was unclaimed and producer-side. It already existed and
   travelled end to end. We had asserted an absence we had not checked.
3. *The eligible denominator.* We claimed Compara's `protein_default` collection "is built from
   protein-coding genes". It also trees IG/TR gene segments — 279 human, 485 mouse, 511 rat — so
   every cardinality rate was about a point off **in a message already sent**. Clean 1:1:1 went
   76.97% -> 75.49%.
4. *The multi-gene denominator.* Ensembl's xref dumps reference ALT-haplotype and patch genes, where
   one locus is described many times over. Counting raw gene ids gave a 6.99% multi-gene rate;
   restricted to the primary assembly it is 0.36% — a twentyfold error — and it manufactured a
   "human is much worse than the rodents" species difference that does not exist, because only the
   human dump references off-primary genes. Caught one commit before sending, which was luck rather
   than process, so it was reported to `dataRepo` anyway.

(3) and (4) were both found only because the user said *"check your work"*. Neither would have been
caught by re-reading the code; both needed enumerating what the reference set actually contained.

**What the measurements say.** 75.49% of eligible human genes are a clean 1:1:1 across
9606/10090/10116 — design a cross-species join for ~75%, not 95%. 45 genes are one2one to *both*
rodents while the rodents are not one2one with each other: clean from every pairwise angle, not
clean as a set, and the entire reason triples were measured separately. 2,539 human genes have no
rodent ortholog at all. Multi-gene accessions are rare (0.36% reviewed human) but concentrated —
all four core histones are in the top seven, H4 spanning 14 real loci — so a sub-1% rate lands on
proteins abundant in every run. RefSeq was wrongly deferred to v3 and the deferral is retracted:
69,569 curated human `NP_` accessions, 96.9% single-gene, from a 4 MB file already on disk.

**The trap worth carrying to any project that touches Compara.** The genome-specific homology dumps
*partition* rather than overlap, and each species pair lives entirely in one file — not the obvious
one. Every human-mouse orthology is in the **mouse** dump; the human dump has none. Downloading the
file named after your species yields a complete-looking result missing 100% of human-mouse. Only
caught by reading the provider README before the data.

**Method changes made permanent.** `design/PLAN.md` gained four standing rules (a denominator is a
claim; never name an entity from memory; when a result is surprising suspect the measurement; read
the README first). `tests/test_reported_claims.py` pins every number *sent to a partner*, so a
re-run that moves one fails loudly instead of leaving a wrong number in their schema.

**Phase.** Recorded as BUILD. SURVEY was skipped entirely — no literature review was run — logged in
`skip_log` rather than left implicit.
