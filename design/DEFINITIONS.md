# logs definitions

Charter seam S4 (v0.2): each engine publishes a definition id for every quantity it produces, in its
own namespace, and there is no central registry. A stored result names the definition it was
computed under with `definition_id = logs:<ID> v<N>`.

**Versioning.** The version changes when the method changes, meaning that the same inputs could
give different rows. Changing an input, such as a new Ensembl release, a new gene set or a new
search database, does **not** change the id. Every row carries the sha256s of its inputs, so two
runs under one id are comparable exactly when those columns match.

---

## `logs:DEF-GENE-RESOLUTION v1`: protein accession to stable Ensembl gene

**Status:** published 2026-09-24. **Implementation:** mzLib `EnsemblGeneResolver` (#1338, first
released in mzLib **1.0.592**). pyMzLib 0.2.0 projects it as `proteins.resolve_genes()`, and our
tool is `tools/ResolveSearchDb`. **Row schema:** mzLib `GeneResolutionTsv.Schema`. Read column names
from the schema, not from this page.

### What it answers

For each protein in a search database, the question is which stable Ensembl gene or genes it is a
product of, **counted against one pinned Ensembl gene set**. The answer is a property of the
database, not of a search. It is computed once per (search database, gene set, xref), on stored
files.

### Inputs (per species, per Ensembl release)

1. **The search database**, meaning the decompressed file the search read. Every row carries its
   sha256 as `search_database_sha256`. For real answers the database should be UniProt XML: a FASTA
   carries no gene links, so every protein in it is `not_in_source`.
2. **The gene set**: Ensembl's **primary-assembly** GTF, or the compact table built from it
   (`results/gene_sets/`). Both give identical rows. Rows carry `gene_set_release`, and
   `gene_set_sha256` is **the GTF's sha256**, including when the table was read.
3. **Ensembl's UniProt xref dump** (`<Species>.<Assembly>.<release>.uniprot.tsv.gz`). Rows carry its
   sha256 as `ensembl_xref_sha256`. The verb treats it as optional, **but this definition requires
   it.** Without it, `ensembl_xref_agrees` is empty in every row, and a run is then not a v1 run.

The inputs for Ensembl 116 (human, mouse and rat) are listed with sha256s in
`results/resolver_inputs_e116.{json,md}`.

### Method

- **Gene links come from the search database itself.** For UniProt, these are the entry's
  `<dbReference type="Ensembl">` gene ids, taken from every transcript reference, not only the first.
- **Each linked gene is counted against the gene set.** A gene on the gene set's assembly counts. A
  gene outside it (an ALT haplotype, patch or scaffold) is left out of `n_genes` and counted in
  `off_primary_genes`.
- **Ensembl's xref is a second opinion, not a replacement.** Each gene row records whether Ensembl
  links the same accession to that gene (`ensembl_xref_agrees`). A gene that only Ensembl links gets
  its own row with `source = ensembl_xref`, and it **does not change the accession's `outcome`**.
  `outcome` and `n_genes` always describe the search database's own links.
- **Never a pick.** There is one row per (accession, gene), and an accession with no gene gets exactly
  one outcome row with an empty `gene_id`. No cell joins several genes.
- **Decoys are not resolved.** The database is loaded with no decoys, so a `DECOY_` accession joins
  to no row. A protein loaded as a contaminant is `contaminant_not_mapped` and is never mapped.

### Outcomes (`outcome`, exactly one per accession)

| value | meaning |
|---|---|
| `resolved` | exactly one gene on the gene set's assembly |
| `multi_gene` | more than one gene on that assembly: one row per gene, never a pick |
| `off_primary_only` | linked only to genes outside the gene set (ALT haplotype, patch, scaffold) |
| `not_in_source` | a well-formed accession the database links to no gene |
| `unrecognized_accession` | not a UniProt or RefSeq accession, and linked to nothing |
| `contaminant_not_mapped` | loaded as a contaminant; never mapped, never dropped |

### Views (filters, not modes)

- **The search database's view:** `source = search_database_dbreference`.
- **Ensembl's view:** `ensembl_xref_agrees = true`. This is aging's default gene view (aging 009 §1).
  Name the view whenever you quote a multi-gene count: for human 116 it is 350 entries in the search
  database's view and 69 in Ensembl's.

### Proteoforms

A sequence-variant proteoform that mzLib derives from an entry (`P12345_S70N`) has **its entry's
answer**, in every column except `accession`. This was measured on human Ensembl 116: none of the
31,943 variant proteoforms in aging's human database differs from its entry (pinned in
`tests/test_reported_claims.py`). Whether a table lists proteoforms or only entries is a question of
how it joins, not of the definition. That choice is open with dataRepo as LOGS-D2. Mapping a
proteoform accession to its entry is ours to define (accession normalization, OWNERSHIP). For
UniProt it is the text before the first `_`. That rule does not hold for RefSeq (`NP_000001`).
