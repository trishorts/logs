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

## `logs:DEF-ORTHOLOGY v1`: the orthology store

**Status:** proposed 2026-09-27 and sent to dataRepo (025) before it was built; built the same day.
**Published 2026-10-05**, after dataRepo answered LOGS-D4 (029): they read the Parquet in place, so
what we guarantee is the **file contract** below, not a column contract for their catalog.
**Implementation:** mzLib PR #1381 (branch `feat/compara-orthology-store`, `code/mzLib-orthology-store`).
`UsefulProteomicsDatabases.Ensembl` reads the dumps (`ComparaHomologyDump`, `ComparaGeneTreeContent`),
builds `OrthologySnapshot`, and writes it with `OrthologySnapshotWriter` (Parquet.Net). The writer sat
in its own `OrthologyStore` project until 2026-10-05, when review folded it into
`UsefulProteomicsDatabases`; the snapshot it writes is byte-identical. The on-disk format is
`ensembl-orthology-snapshot` format 1, which is this definition. Our driver is
`tools/BuildOrthologySnapshot`.
**Checked (2026-09-27, human/mouse/rat 116):** the C# views, the DuckDB views and `cardinality.py`
agree on all six pair-status distributions, on 23,764 human-mouse rows and on 15,508 all-one-to-one
human genes. A rebuild is byte-identical.

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
  manifest.json                         format + version, snapshot_id, release, species, gene_set_sha256, inputs and files with sha256
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

Every SQL macro takes the snapshot directory as its first argument (`root`), omitted below.

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
- **`species_set3(a, b, c)`** in SQL, and **`OrthologySnapshot.SpeciesSet(species…)`** for any
  number of species in mzLib: the one-gene-per-species tuples in which **every pair** has an
  ortholog row. The flag `all_one2one` is set when every one of those rows is `ortholog_one2one`.
  A tuple is never formed by chaining (A~B and B~C does not give A~C), because Compara's pairwise
  calls are not transitive.

### The file contract (what `format_version` 1 promises)

A consumer that reads a snapshot in place (dataRepo, LOGS-D4 (a)) may rely on the following for
every snapshot whose manifest says `format = ensembl-orthology-snapshot` and `format_version = 1`:

- **Layout.** The paths above: `manifest.json`, `genes/<species>.parquet`,
  `members/<species>.parquet`, `pairs/<a>__<b>.parquet` with `a <= b` in ordinal order, and
  `views.sql`. Every species in `manifest.species` has a genes file, a members file, and a pair file
  with every species, itself included.
- **Columns.** The names, order and types in the three tables above, with nulls exactly where the
  tables say a column is nullable.
- **Views.** `views.sql` defines `orthologs(root, a, b)`, `pair_status(root, a, b)` and
  `species_set3(root, a, b, c)` as DuckDB table macros, where `root` is the snapshot directory the
  caller passes. They have the output columns described above. `pair_status` emits the four
  in-gene-set statuses; `not_in_gene_set` is for the consumer to assign to a gene id the snapshot's
  `genes` file does not hold. The helper macro `orthology_pair_file` is not part of the contract.
- **Integrity.** `manifest.json` lists every other file with its sha256, row count and size, and
  every input with its sha256. A snapshot is never changed after it is written.

**What changes the version.** Removing or renaming a file, column or view; changing a column's type
or nullability; or changing what a status means. Each of these makes format 2, and a v1 reader
must refuse a format it does not know rather than guess. **What does not:** a new species list, a
new release, or a new source (each is a new snapshot under the same format), and a view or column
**added** to the end of a table. A consumer must select columns by name, not by position.

**What is not promised.** `group_id` across releases (it is never stable), the bytes of `views.sql`
beyond the macros' names and outputs, and the Parquet encoding details (row groups, compression).
The data is CC-BY-4.0 and `views.sql` is mzLib's LGPL-3.0 (`LICENSING.md`).

### What it does not do

- It does not map protein accessions. That is `DEF-GENE-RESOLUTION`: join its `gene_id` to
  `genes.gene_id`, after checking that its `gene_set_sha256` is the snapshot's GTF sha256.
- It does not merge sources. NCBI, Alliance or HCOP would each be a separate `<source>-<release>`
  snapshot with the same layout, and would never be unioned into one unqualified answer.
- It does not provide residue-level correspondence (ptmQtl). That is built on top of this store and
  is defined separately, as `DEF-RESIDUE-CORRESPONDENCE` below.

---

## `logs:DEF-RESIDUE-CORRESPONDENCE v1`: residue to homologous residue (PROPOSED, BEING BUILT)

**Status:** proposed 2026-10-05 and sent to ptmQtl (007) before anything was built, as 005 promised.
On 2026-10-06 `/oracle mzLib` ran (`design/ORACLE_residue_correspondence.md`: no aligner and no MSA
reader in mzLib), and the two building blocks were written:
- the pairwise aligner for legs 1 and 3 is mzLib #1428 (`Omics.SequenceAlignment.PairwiseAligner`,
  BLOSUM62, open 11, extend 1, free end gaps). On 3,000 random pairs it gives the same optimal score
  as Biopython (`tools/AlignerOracle`). The `aligner` column carries its `Id`;
- the leg-2 reader is `ComparaGeneTreeAlignment` on branch `feat/compara-gene-tree-alignment`.
  It is stacked on #1381, so it stays a draft in the trishorts fork until #1381 merges.

**Compara's alignment, pinned and checked** (`Compara.116.protein_default.aa.fasta.gz`, 908 MB, MD5
verified; `results/alignment_check_e116.md`):
- it holds 54,308 alignments, one per gene tree, and every row of an alignment has the same width;
- every `protein_a`/`protein_b` in the store, and every member's canonical protein, is in it exactly once;
- **not every store row has a shared alignment.** `other_paralog` rows relate genes in different
  trees, so they never share an alignment. **760 ortholog rows also join genes in two trees** (478
  human~mouse, 278 human~rat, 4 mouse~rat), so there is no column to cross. That case gets its own
  refusal, `no_shared_alignment` (below).

**Leg 1 at entry grain** (canonical entries x genes, agrees view): the UniProt entry's sequence is
identical to its gene's tree protein for human 91.6%, mouse 86.5% and rat 57.2% of pairs. Where they
are identical, leg 1 is the identity and `not_on_ensembl_protein` cannot occur. The residue rate needs
the aligner, and it is reported with the first build.

**Reviewed by ptmQtl (008, 2026-10-05): no changes requested.** 008 answered the two open questions:

- **LOGS-P5, which target databases:** six, not three. aging's three reviewed proteomes plus their
  three `_agingPTM-v1` builds, which have their own sha256 and cover 50 of ptmQtl's 92 datasets.
  Rows are written under each database's own `search_database_sha256`. A build that holds the same
  entries, sequences and sequence variants as its base proteome is aligned **once**, and its rows
  are written under both keys. Measured 2026-10-06 (`python -m logs_orthology.db_equivalence`,
  `results/search_db_equivalence.md`): **all three builds qualify.** Each holds the same entries as its
  base (20,416 / 17,277 / 8,228), with identical sequences and sequence variants, and differs only in
  `modified residue` features (human 56,282 -> 59,564, mouse 50,617 -> 51,372, rat 27,265 -> 30,134). aging's isoform databases give the `isoform` edges.
- **LOGS-P6, `substituted` rows:** kept, with both residues.

| species | search database | `search_database_sha256` |
|---|---|---|
| human | `uniprotkb_proteome_UP000005640_AND_revi_2026_09_18.xml` | `760984e8…` |
| human | `uniprotkb_proteome_UP000005640_AND_revi_2026_09_18_agingPTM-v1.xml` | `eaefbb7e…` |
| mouse | `uniprotkb_proteome_UP000000589_AND_revi_2026-09-22.xml` | `fb52debf…` |
| mouse | `uniprotkb_proteome_UP000000589_AND_revi_2026-09-22_agingPTM-v1.xml` | `26ea83c2…` |
| rat | `uniprotkb_proteome_UP000002494_AND_revi_2026-09-22.xml` | `abf612c9…` |
| rat | `uniprotkb_proteome_UP000002494_AND_revi_2026-09-22_agingPTM-v1.xml` | `caf342e1…` |

### What it answers

Given a residue of a protein in a search database, which residue of another protein corresponds to
it, through **one** stated relationship and **one** stated alignment, or, if none does, **where the
chain stopped**. The store's rules all apply: source and release on every row, one relationship per
row, no transitive closure, one-to-many kept, and a refusal is typed, never the nearest residue.

### The residue key (003-logs, 005-logs)

`(search_database_sha256, accession, position)`, with `position` 1-based on that entry's own sequence
as that database holds it. An isoform that a database holds as its own entry (`P02751-8`) is keyed on
its own sequence; nothing is moved to the canonical to store it (aging 018 agrees: positions differ).

### Edges (`edge_kind`)

| edge_kind | from -> to | alignment |
|---|---|---|
| `homolog` | a residue of gene G's entry -> a residue of gene H's entry, where the store holds a G~H row | three legs, below |
| `isoform` | an isoform entry (`P02751-8`) -> its canonical entry (`P02751`) | our pairwise alignment of the two UniProt sequences |
| `variant` | a sequence-variant proteoform (`P12345_S70N`) -> its entry | none for a substitution; an indel needs our pairwise alignment. A guard: ptmQtl 004 found 0 variant sites |

**A `homolog` row is three coordinate changes along one relationship, not three relationships:**
1. UniProt entry of G -> G's canonical Ensembl protein (our pairwise alignment);
2. that protein -> H's canonical Ensembl protein, through the column of Compara's gene-tree alignment;
3. H's Ensembl protein -> each UniProt entry of H in the target database (our pairwise alignment).

Legs 1 and 3 change coordinates within one gene. Only leg 2 crosses a homology edge, and that edge is
one `homology_id` from the store. This is why a row is not a transitive closure. Each leg's positions
are carried, so a consumer can see which leg failed.

### Row (one per source residue x target gene x target entry; never a pick)

| column | meaning |
|---|---|
| `search_database_sha256`, `accession`, `position`, `residue` | the source residue (the key, plus the residue read from the database) |
| `edge_kind` | `homolog`, `isoform` or `variant` |
| `target_search_database_sha256`, `target_accession` | the target entry |
| `target_position`, `target_residue` | null exactly when `outcome` is a refusal |
| `outcome` | exactly one value (below) |
| `gene_id`, `target_gene_id` | the genes, from `DEF-GENE-RESOLUTION` rows under the agrees view |
| `homology_id`, `relationship_type`, `orthology_snapshot_id` | `homolog` rows only: the store row, verbatim, and the snapshot it came from |
| `ensembl_protein`, `ensembl_position`, `target_ensembl_protein`, `target_ensembl_position` | `homolog` rows only: legs 1 and 2, null after the leg that failed |
| `msa_sha256` | the Compara alignment file's sha256 (`homolog` rows) |
| `aligner` | the id of our pairwise method and its parameters, versioned like a definition |
| `gene_set_sha256`, `target_gene_set_sha256` | as in `DEF-GENE-RESOLUTION`, so the rows can be checked against both gene resolutions and the snapshot |

### Outcomes (`outcome`)

| value | meaning |
|---|---|
| `identical` | aligned, and the target residue is the same amino acid |
| `substituted` | aligned, and the residue differs (S to T, say). Whether that conserves the site is ptmQtl's call, not ours |
| `residue_mismatch` | the residue the caller supplied is not at that position in the source entry. The coordinates are wrong, so nothing is mapped |
| `position_out_of_range` | the position is beyond the source sequence |
| `gene_not_resolved` | the source accession has no gene in the agrees view; the resolution's own `outcome` is carried |
| `no_homolog` | the store holds no row of the requested kind between the genes; the store's `pair_status` is carried |
| `not_on_ensembl_protein` | leg 1: the residue sits where the UniProt entry and G's Ensembl protein differ |
| `no_shared_alignment` | leg 2: the store relates G and H, but their proteins are in different Compara alignments (different gene trees), so no column joins them. Always true of `other_paralog`; true of 760 ortholog rows in 116 |
| `gap_in_target` | leg 2: the alignment column is a gap in H's protein |
| `not_on_target_entry` | leg 3: H's Ensembl residue has no counterpart in that UniProt entry |
| `target_gene_not_in_database` | H has no entry in the target database |
| `isoform_specific` | an `isoform` edge: the residue is in a region the canonical entry does not have (fibronectin EDA/EDB/IIICS, lamin C's C-terminus) |
| `variant_changed_span` | a `variant` edge: the residue is inside the changed span of an indel |

A refusal row keeps every column known up to the failure, so "no ortholog", "ortholog, but a gap" and
"we never got as far as the alignment" stay distinguishable.

### What it does not do

- It does not call conservation, and it does not judge whether a modification is shared. That is
  ptmQtl's (their 001).
- It does not chain: a mouse residue reaches a rat residue through the mouse~rat row, never through
  human.
- It does not pick one target when a gene has several orthologs or a target gene several entries.
