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

## 2026-09-22 (second session) — the plan reordered twice, resolution moved into mzLib, and an occupancy bug fixed on the way

**Replies turned the plan over.** aging's 002 said compare, not pool; that rodents were months away;
and that they wanted accession→gene more than orthology. The store was deferred and resolution
brought forward (003 to aging). Their 006 corrected the timeline the same day: the user had mixed
mouse and rat into the batch, so rodents are about a day away and the store is un-deferred. 006 also
confirmed the full search-database hash (`760984e8…a7be8838`, over the decompressed XML) and answered
REQ-AGING-5..8. The user then moved accession→gene resolution into **mzLib**. `resolve.py`, written
this session as a Python prototype, became the test oracle for the C# port.

**Three errors in numbers already sent, all one mistake.** Building the resolver exposed that 007 to
dataRepo pooled `NP_` with `XP_` and counted xref rows as accessions: curated `NP_` is 99.58%
single-gene, not 96.9%; `NP_` links are 76.6% `DIRECT`, not "mostly inference"; and isoform-suffixed
accessions number 25,177, not 35,202. Corrected in 008 to dataRepo, with the `NP_` point repeated to
aging in 005. The pinned-claims test caught the isoform change as designed.

**The port** (`code/mzLib-ensembl-genes`, stacked on #1336, test-first): `Protein.EnsemblGeneReferences`
in #1336's idiom, `EnsemblGeneSet.LoadGtf`, `ProteinAccession.Parse`, `EnsemblGeneResolver` with
`GeneResolutionTsv`, and `EnsemblXrefTable` for a per-gene `ensembl_xref_agrees` column. Running it on
the real search database turned up two things. First, `LoadProteinXML` expands 20,416 entries into
52,359 proteins because sequence variants are applied, and 504 of those had been misreported; they
now resolve through `ConsensusVariant`. Second, the two sources mean different things by
"multi-gene": UniProt's XML links readthrough genes, novel genes and identical paralogs, giving 350
multi-gene entries against Ensembl's xref's 69. The user chose to report the XML's links as they are
and add the agreement column. Filtering `agrees = true` reproduces `resolve.py` for 20,412 of 20,416
entries. 005's numbers now come from committed code (`tools/ResolveSearchDb` +
`logs_orthology.search_db`) and are pinned. dataRepo's 009 showed that the XML carries the
ALT-haplotype trap (87.6% single-ENSG). We reproduced it at 87.11%, and the port's primary-assembly
gene-set input is exactly their fork's first branch.

**Out of scope, fixed anyway.** The user asked for a review of Peter's occupancy manuscript against
the code, so both oracles ran on it. The pass found that `ModificationOccupancyCalculator` drops
protein N-terminal mods on Met-removed N-termini from both sides of the ratio, and that the paper
cites the wrong mzLib version (1.0.586; MetaMorpheus 1.1.9 uses 1.0.588), among smaller wording
errors. The user had the fix opened from `logs` as an isolated TDD PR from their fork: **mzLib #1337**
(two red tests to green, two guards, full offline suite 6,607/0/32). The manuscript findings have
not been sent to Peter.

## 2026-09-22 (third session) — #1338 opened, resolution kept out of MetaMorpheus, compact gene tables, and rat's four gene-id series

**#1336 merged, #1338 made presentable.** #1336 was squash-merged at 19:58, which left the resolution
branch carrying the old GO commit and conflicting. It was rebased onto `smith/master` with that commit
dropped (the merged GO code was identical), and all commits were reworded to the house commit style
(`type(scope): summary`, `~/.claude/skills/apply-review-fixes/references/commit-style.md`). The PR had
been opened against the fork with no description; the user re-opened it on smith-chem-wisc as **#1338**.
Its description now starts with the `<!-- project-of-origin -->` / `> **Project of origin:** \`logs\``
marker that #1337 uses. That house style is now a feedback memory.

**Resolution will not go into MetaMorpheus output (user decision).** The earlier plan (option (a), and
our 010 §3 to dataRepo) was a MetaMorpheus output table. The objection that settled it: the resolution
depends only on the search database and a release-pinned gene set, never on the search, so putting it
in MetaMorpheus makes every search carry a GTF to recompute one table. aging's nine datasets share one
XML, so that is one run, not nine. 011 to dataRepo withdrew 010 §3 and proposed that they run the mzLib
resolver once per `(search_database_sha256, gene_set_release)` through pyMzLib (already an optional
dependency of theirs), or that we deliver the table. It named the principle it collides with, their
009 §6 "we never resolve it ourselves", and asked REQ-DATAREPO-8/9/10: who runs it, whether the table
shape and key suit them, and whether the XML is reachable at resolution time.

**The GTF is too big to ask anyone to carry, so there is now a compact gene table.** The human GTF is
141 MB compressed and 4.66 GB unzipped, for 78,941 gene rows. An `/oracle mzLib` pass found no existing
writer for a table with a metadata header, so, at the user's request, a paired
`EnsemblGeneSetReader`/`EnsemblGeneSetWriter` was added in the `MslReader`/`MslWriter` idiom (#1338
`34e20ca6`). A table read back carries the **GTF's** provenance, so resolution rows are keyed
identically, and on aging's human XML the output is byte-identical to resolving against the GTF. The
tables are in `results/gene_sets/`: human 523 KB, mouse 592 KB, rat 289 KB. They are built by
`tools/BuildGeneSet`, and `tools/ResolveSearchDb` accepts either form. We had already told dataRepo
"563 KB", which came from an awk prototype; 012 corrected it, and the real figure is pinned.

**Rodents resolved, and rat broke a promise we had made.** aging's mouse (`UP000000589`, XML
`fb52debf…`) and rat (`UP000002494`, XML `abf612c9…`) databases were checked to be byte-for-byte
decompressions of the `.gz` files whose hashes aging recorded. Mouse is healthy: 15,474 resolved, and
the XML and xref nearly agree. Rat looked wrong, so the measurement was suspected first. UniProt's rat
XML links each protein to genes in **four Ensembl id series**. Only `ENSRNOG00000…` is the GRCr8 gene
set; the `…00055/00060/00065` series (about 4,200 genes each) are other rat annotations, none in the set.
The gene set was right to refuse them (950 entries are `off_primary_only`). But Ensembl's xref resolved
725 rat entries whose XML links no gene in the set, and the resolver dropped those genes because it
took genes only from the XML. That made 007's promise to aging, "neither is dropped", false for rat.

The user thought the project had already answered this, and it had, mostly. Three recorded commitments
decided it: the multi-gene decision (the XML's links as they are, xref as a column), standing rule 3
(rows, never a run-time switch), and 007's promise that filtering `ensembl_xref_agrees = true` recovers
Ensembl's answer. The one open point was the outcome of an entry that gains a gene only from the xref;
the user confirmed it keeps the XML's. #1338 `3bb04188` adds a `source = ensembl_xref` row per such gene,
held to the same gene set and carrying the XML's outcome. On all three databases the
`search_database_dbreference` rows are unchanged row for row, and the agreement filter now matches
`resolve.py` for every entry (human 20,416, mouse 17,277, rat 8,228).

**A sent number that nothing guarded.** 007 told aging "20,412 of 20,416"; it is now 20,416, and the
claims test had never pinned it. 008 to aging corrects it and reports both rodent resolutions. Every
number in 008 was then pinned, including the 521 off-primary rat entries the xref rescues, which had
come from an ad-hoc script and was moved into `search_db.py` so the pin reads committed code. Two
drafting errors were caught before sending: "roughly half" of human coverage (it is 59.6% vs 94.7%),
and a rounding to 59.7%. `search_db.py` gained `--species`, the reverse-drift metric, and a counted,
no longer asserted, parity explanation.
