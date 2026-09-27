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

---

## `logs:DEF-ORTHOLOGY v1`: the orthology store (PROPOSED)

**Status:** proposed 2026-09-27 and sent to dataRepo before it is built. Not built yet.
**Implementation:** the logs builder (PLAN step 6). It is not yet written, and its home is not yet
chosen: run `/oracle mzLib` first.

### What it answers

Given two species, which genes are homologous, as the source asserts them, with every relationship
kept as its own row. Given a set of species, which one-gene-per-species tuples are orthologous in
**every** pair. The store never picks a gene, never collapses one-to-many, and never infers a group
by chaining pairs.

### The product

A **builder** takes any list of Ensembl species and a release, with every input pinned by sha256.
It writes a **snapshot**. Prebuilt snapshots are published as GitHub releases, and any snapshot
cited in a paper gets a Zenodo DOI. A snapshot is never updated in place: a new release, or a new
species list, is a new snapshot.

### Layout of a snapshot

```
<source>-<release>/                     e.g. compara-116/
  manifest.json                         definition, builder version, species, every input and output file with sha256
  genes/<species>.parquet               one row per gene of the species' primary-assembly gene set
  members/<species>.parquet             one row per gene in a gene tree (gene -> group)
  pairs/<species_a>__<species_b>.parquet    species_a <= species_b; species_a == species_b holds that species' paralogs
  views.sql                             the views below, as DuckDB table macros over the Parquet files
```

Species are Ensembl production names (`homo_sapiens`). The unit is the **species pair** because
Compara asserts relationships only pairwise. Triples and larger sets are views, never stored.

### `genes/<species>.parquet`

The rows of the primary-assembly gene set (the gene-set table's columns, verbatim): `gene_id`,
`gene_version`, `gene_biotype`, `gene_name` (nullable), `seq_region`, plus `species`. The manifest
records the GTF's sha256 per species. This is the value a `DEF-GENE-RESOLUTION` row carries as
`gene_set_sha256`, so a consumer can check that a resolution and a snapshot use the same gene set.

### `members/<species>.parquet`

`gene_id`, `species`, `group_id`, `source_group_id`, `canonical_protein_id`.

- `source_group_id` is Compara's gene-tree id (`ENSGT…`), verbatim.
- `group_id` is **ours**: `<source>-<release>:<source_group_id>`. It is unique across sources and
  releases, and it is **never promised stable across releases**.
- In Ensembl 116, each gene is in exactly one tree and has exactly one canonical protein, so this
  is one row per treed gene. The builder refuses a release in which that stops being true, rather
  than choosing.
- A gene with no row here is `not_in_any_tree`.

### `pairs/<species_a>__<species_b>.parquet`

One row per relationship the source asserts. Values are verbatim, and the source's `NULL` stays
null, never 0.

| column | type | meaning |
|---|---|---|
| `homology_id` | string | the source's id for the relationship; unique within the snapshot |
| `relationship_type` | string | Compara's `homology_type`, verbatim (`ortholog_one2one`, `other_paralog`, …) |
| `relationship_class` | string | `ortholog`, `paralog` or `homoeolog`, derived from `relationship_type` |
| `species_a`, `species_b` | string | as in the file name |
| `gene_a`, `protein_a`, `identity_a` | string, string, double | species_a's side; identity is Compara's percentage for that side |
| `gene_b`, `protein_b`, `identity_b` | string, string, double | species_b's side |
| `dn`, `ds` | double, nullable | verbatim |
| `goc_score` | int32, nullable | verbatim |
| `wga_coverage` | double, nullable | verbatim |
| `is_high_confidence` | bool, nullable | null means the source declined to say, not false |
| `source_dump` | string | which genome-specific dump held the row (provenance) |

- **Orientation.** In a cross-species file, the `_a` side is always `species_a`. The builder swaps
  sides where the source listed them the other way round, and each identity moves with its gene.
- **Paralogs are included and typed.** Every paralog type observed in 116 is within one species, so
  paralogs sit in the `<species>__<species>` file. The builder refuses a paralog row that crosses
  species, and refuses a `homology_type` it does not know.
- **Every pair is read from both species' dumps.** Ensembl's README says that each genome-specific
  dump holds an arbitrary subset of that genome's relationships. So the builder reads both dumps,
  keeps the rows for the pair, and deduplicates on `homology_id`. If the same id appears with
  different content, the build fails.

### Views (`views.sql`; filters and joins, not stored)

- **`orthologs(a, b)`**: the pair file's ortholog rows, oriented so species `a`'s gene comes first.
- **`pair_status(a, b)`**: one row per gene of `a`, with exactly one status:

  | status | meaning |
  |---|---|
  | `has_ortholog` | at least one ortholog row to a gene of `b` |
  | `no_edge_in_shared_tree` | the gene's tree contains a gene of `b`, but the source called no ortholog |
  | `tree_lacks_target_species` | the gene's tree contains no gene of `b`, so there was nothing to compare |
  | `not_in_any_tree` | in the gene set, but in no gene tree; no call was attempted |

  `not_in_gene_set` is the fifth status. It applies only to a gene id supplied from outside, such
  as a `gene_resolutions` row resolved against a different gene set. The view carries
  `gene_biotype`, so the denominator is **the consumer's choice, and it must be named**: it is not
  the same as `protein_coding` (rule 2).
- **`species_set(species…)`**: the one-gene-per-species tuples in which **every pair** has an
  ortholog row. The flag `all_one2one` is set when every one of those rows is `ortholog_one2one`.
  A tuple is never formed by chaining (A~B and B~C does not give A~C), because Compara's pairwise
  calls are not transitive.

### What it does not do

- It does not map protein accessions. That is `DEF-GENE-RESOLUTION`: join its `gene_id` to
  `genes.gene_id`, after checking that its `gene_set_sha256` is the snapshot's GTF sha256.
- It does not merge sources. NCBI, Alliance or HCOP would each be a separate `<source>-<release>`
  snapshot with the same layout, and would never be unioned into one unqualified answer.
- It does not provide residue-level correspondence (ptmQtl). That is built on top of this store and
  is defined separately.
