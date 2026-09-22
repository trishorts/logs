# PLAN — logs

*Written 2026-09-22, after the mzLib survey (`design/ORACLE.md`) and the first four messages with
`dataRepo`. The goal and the constraints were settled before this; what follows is the ordered
work.*

## Research goal, one sentence

Build a release-versioned, gene-centric cross-species orthology layer that joins multi-organism
proteomics datasets at a stated, auditable resolution — preserving one-to-many orthology and
distinguishing every reason a join can fail — and show that it recovers relationships that
gene-symbol or best-hit mapping silently loses.

## The shape, settled

Three layers, three homes (locked 2026-09-22):

| Layer | Home | Why |
|---|---|---|
| Accession → source gene | **mzLib** — computed views over `Protein.DatabaseReferences` | The data is already there and never read back by type |
| Accession normalization | **mzLib** — `MzLibUtil\ClassExtensions.cs` | Pure string work, no reference data, reachable from all three omics |
| Network ID-mapping client | **mzLib** — `UsefulProteomicsDatabases\` | A natural sibling to `ProteinDbRetriever` / `PrideArchiveClient` |
| **Orthology store + analysis views** | **`logs`** | Would be mzLib's first self-managed on-disk database and its first DB dependency outside vendor-file reading |

## Ordered steps

Test-first where there is a contract to pin. The rule throughout: **a number we have not measured
does not go in a deliverable**, and a distinction we cannot derive is reported as underivable
rather than approximated.

### ✅ 1. Pin and fetch the sources — *done*

`src/logs_orthology/sources.py`, `fetch.py`. Release 116, 16 files, 673 MB, checksum-verified
against whatever the provider publishes (MD5 where available, BSD `sum` where not, and recorded as
unverified where neither). Provenance appended to `data/PROVENANCE.md`.

Two things this step already caught, both of which would have produced a confidently wrong result:

- **The genome-specific homology files each hold an arbitrary subset.** The human file alone does
  not contain every human↔mouse orthology. All three taxa are fetched and unioned.
- **Ensembl's `CHECKSUMS` under `gtf/` and `tsv/` is BSD `sum`, not MD5.** A parser looking for
  MD5 finds nothing and reports "unverified" — which is safe — but the files *are* verifiable, and
  leaving them unchecked would have been a choice, not a limitation.

### ✅ 2. The cardinality measurement owed to `dataRepo` — *running*

`src/logs_orthology/cardinality.py` → `results/cardinality.{md,json}`.

Answers `REQ-LOGS-4` (pairwise and triple cardinality) and `REQ-LOGS-6` (the refusal classes).
Carries one correction we owe them: **Compara does not support the "no ortholog exists" versus
"no ortholog in this release" distinction we promised.** The refusal is decomposed instead by how
far the inference got — shared tree with no edge, tree lacking the target species, no tree at all,
not in the gene set — which is derivable and answers the same question.

### 3. Report back, including the correction

Post the numbers to `dataRepo` with the underivable-distinction correction stated plainly, not
buried. They are designing `age_effect_meta`'s cross-species join against these numbers.

### 4. Accession → gene, measured before it is built

The xref dumps (`uniprot`, `refseq`, `entrez` per species) are already fetched. Before writing any
mzLib code:

- **Measure the multi-ENSG distribution.** Our last open modelling question. `dataRepo` is
  measuring it against their search XML; we can measure it independently against Ensembl's own
  xref dump, and *the two should agree*. If they disagree, that is a finding about which source to
  trust, and it is better found now than after a schema depends on it.
- **Re-measure the RefSeq claim.** We told `dataRepo` RefSeq was v3 because mzLib parses no
  `NP_`/`XP_` FASTA header. That reasoning is about *parsing a header* and does not apply to
  *resolving an accession we already hold* — which `Homo_sapiens.GRCh38.116.refseq.tsv.gz` does
  directly. If RefSeq turns out to be cheap, say so and correct the deferral.

### 5. The store

Only after step 4's numbers exist, because they decide the keying:

- `Gene`, `ProteinAccession`, `OrthologyGroup`, `OrthologyGroupMember`, `OrthologyRelationship`
- Group id is **ours**, with the source's `ENSGT…` preserved beside it. Keyed
  `(source, release, group_id)` — never promised stable across releases.
- Relationship rows carry `relationship_type`, confidence, GOC score, WGA coverage, and both
  identity percentages, verbatim.
- Every unresolved outcome carries its class, including *contaminant, not mapped*.

### 6. The mzLib contribution

Follows PR #1336's merged pattern — a computed view over `DatabaseReferences`, a `const` type
string, no parser change, no constructor parameter. **Wait for #1336 to merge first**; two
independently written typed views over the same list is precisely the duplication the oracle
exists to prevent.

Note the projection differs from `NcbiTaxonomyId`: Ensembl writes one `dbReference` per
*transcript* with the ENSG in a `<property>`, so `FirstOrDefault(...)?.Id` is a category error
here. It needs `SelectMany(Properties)` and a `Distinct()`.

### 7. Validate the "generic" claim

Currently unfalsified rather than demonstrated — every requirement we hold comes from one
consumer and one corpus. Either find a second, unrelated consumer, or say plainly that generic is
aspirational. `aging` (`REQ-AGING-1`) may change the picture; a second consumer would settle it.

## Standing rules for this work

1. **Measured, never estimated.** A partner designing a join against our number is entitled to a
   number we actually computed.
2. **Say when a distinction is underivable** rather than approximating it. Step 2 is the first
   instance and will not be the last.
3. **Emit the rows; never a run-time switch that changes what a file contains.** No
   `--one-to-one-only`.
4. **A contaminant is never mapped, and never silently dropped** — it resolves to an explicit
   *contaminant, not mapped* outcome.
5. **Read the provider's README before trusting a file.** Two of this session's three real traps
   were documented in one and would have been invisible in the data.
6. **A denominator is a claim, and it must be checked like one.** Twice in one afternoon a
   plausible-sounding reference set was the wrong one:
   - *"Count the distinct gene ids an accession maps to."* Ensembl's xref dumps include ALT
     haplotypes and patches, where one locus is described many times over. That put the
     multi-gene rate at **6.99%**; restricted to the primary assembly it is **0.36%** — a
     twentyfold error, in the direction that makes the finding sound more interesting. It also
     manufactured a species difference (human "much worse than" rodents) that does not exist,
     because only the human dump references off-primary genes.
   - *"Compara's `protein_default` collection is protein-coding."* It also contains
     immunoglobulin and T-cell-receptor gene segments — 279 human, 485 mouse, 511 rat. Excluding
     them dropped genes the source *had* considered.

   Both were caught by asking *what is actually in this set?* rather than by re-reading the code.
   Before dividing by anything, enumerate it and look at what is there.
7. **Never name an entity from memory in a deliverable.** `Q5JQC4` was written up as KIR2DL5A
   from recall; it is CT47A1. Resolve identifiers against the data, every time — the cost of
   looking it up is a minute and the cost of not is a wrong claim in someone else's schema.
8. **When a result is surprising, suspect the measurement first.** "Human is dramatically worse
   than mouse" was surprising and wrong. The surprise was the signal.
