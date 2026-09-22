# Cross-Species Protein and Gene Association

## Conversation transcript and consolidated workflow

This document captures the discussion about associating proteins/genes across organisms—especially human, mouse, and rat—and the recommended workflow for combining proteomics datasets. The first section preserves the initial question and conceptual guidance; the second captures the project-specific recommendations.

---

# Part 1. Initial question

**User:**  
I have a project where I need to associate proteins (genes) between organisms. Particularly human, mouse and rat. But maybe others. Can you give me some insight into how this is routinely done?

## Assistant response: Cross-species orthology mapping

For a project involving human, mouse, rat, and potentially other organisms, the problem is generally called **cross-species orthology mapping**.

It's routine in comparative genomics, transcriptomics, and proteomics, but there are important distinctions—particularly when associating experimentally identified proteins rather than simply comparing gene names.

The key point is that there is no universally correct one-to-one mapping between genes or proteins across species. Many genes have a clear counterpart in another organism, but others have undergone gene duplication, gene loss, or sequence divergence. A good mapping strategy preserves that biological reality rather than forcing every protein into a single match.

## 1. Distinguish the types of association

| Relationship | Meaning | Typical use |
|---|---|---|
| Orthologs | Genes diverged through a speciation event | Comparing human gene X with its mouse or rat counterpart |
| Paralogs | Genes related through a gene duplication event | Distinguishing members of a protein family |
| Homologs | Genes or proteins sharing evolutionary ancestry | Broad sequence similarity searches |
| Isoforms | Different protein products from the same gene | Matching individual proteomics identifications |

Orthology is usually the relationship wanted for cross-species biological comparisons. However, orthologs are not necessarily functionally identical, and one-to-many orthology is common.

If a gene duplicated in the rodent lineage after the human–rodent divergence, one human gene may correspond to two mouse genes. Both can be legitimate orthologs of the human gene, but neither is necessarily a unique, interchangeable substitute for the human gene.

Ensembl Compara models these relationships using gene trees, distinguishing speciation from duplication events.

## 2. Commonly used resources

| Resource | Role |
|---|---|
| Ensembl Compara | Gene-level orthology across many species; one-to-one, one-to-many, many-to-many relationships; stable IDs and confidence information |
| NCBI Gene / Orthologs | Useful for RefSeq accessions, Gene IDs, and orthology relationships |
| Alliance of Genome Resources | Orthology alongside curated biological knowledge, gene function, phenotype, and model-organism annotations |
| HGNC / HCOP | Standardized gene symbols and curated human-to-model-organism associations; HCOP integrates predictions from multiple sources |

Useful links:

- Ensembl: https://www.ensembl.org
- Ensembl REST API: https://rest.ensembl.org
- Ensembl BioMart: https://www.ensembl.org/biomart/martview
- NCBI Gene: https://www.ncbi.nlm.nih.gov/gene/
- NCBI Datasets: https://www.ncbi.nlm.nih.gov/datasets/
- Alliance of Genome Resources: https://www.alliancegenome.org/
- HGNC: https://www.genenames.org/
- HCOP: https://www.genenames.org/tools/hcop/

Ensembl supports bulk retrieval through BioMart and programmatic access through REST and Compara APIs. NCBI Datasets provides orthology data and access to gene-related information. UniProt ID Mapping is useful for bulk accession conversion.

## 3. How mapping is commonly done

### Approach A: Input is gene symbols or gene IDs

Query an orthology resource using the source gene ID and species, then retrieve target ortholog(s).

Example:

`Human ENSG... → Mouse ENSMUSG... → Rat ENSRNOG...`

Keep stable identifiers and orthology type. Do not rely on gene symbols alone.

### Approach B: Input is protein accessions or sequences

For proteomics, map the protein accession to its source gene first, then perform gene-level orthology mapping. If the accession cannot be resolved, sequence similarity searches can identify candidate homologs, but a BLAST hit alone does not establish orthology.

For UniProt accessions, retain both the UniProt accession and corresponding Ensembl or NCBI Gene ID.

### Approach C: Input is a large collection of proteins from multiple species

Download orthology tables for all organisms of interest and build a reusable mapping database. This avoids querying each protein individually and supports consistent mappings across experiments.

## 4. Preserve one-to-many mappings

A mapping table should not assume a one-to-one relationship, such as:

`HumanGene → MouseGene`

Instead, use a relational table in which each orthologous relationship is a separate row.

| Human gene | Mouse gene | Orthology type |
|---|---|---|
| HGENE1 | MGENE1 | One-to-one |
| HGENE2 | MGENE2a | One-to-many |
| HGENE2 | MGENE2b | One-to-many |

This preserves valid relationships rather than arbitrarily selecting one mouse gene.

For a robust pipeline, retain:

- Source and target taxonomy IDs
- Source and target stable gene IDs
- Protein accession(s), if applicable
- Orthology source and release/version
- Orthology type
- Confidence or supporting evidence, where available

Gene symbols are useful display labels, but should not be primary keys. They can change and are not guaranteed to be unique across species.

## 5. Initial recommendation for a proteomics project

Build the system around **stable gene identifiers and explicit orthology relationships**, not a universal gene-symbol conversion.

A practical architecture:

1. **Input protein identifications** — UniProt / RefSeq / Ensembl protein accessions.
2. **Resolve protein → source gene** — preserve isoforms and accession mappings.
3. **Orthology lookup** — Ensembl Compara, with optional NCBI / HCOP support.
4. **Cross-species association table** — stable IDs, orthology type, evidence, and mapping provenance.

Do not automatically discard one-to-many mappings. Expose them to downstream analysis and let the application decide whether it requires strict one-to-one associations or can accommodate gene families.

For example, comparing human and mouse protein abundance might use one-to-one orthology for a conservative analysis, while exploratory analysis may retain one-to-many relationships. Those are different analytical choices, not different truths about the biology.

---

# Part 2. Project-specific details and recommended implementation

**User:**  
My project details:
- Input: UniProt or RefSeq protein accessions
- Goal: Combine datasets from different organisms
- Scale: Thousands to tens of thousands
- Orthology handling: Retain all orthologs

Please recommend a concrete mapping workflow and data model.

## Assistant response: Recommended workflow

For this use case—combining proteomics datasets from human, mouse, rat, and potentially many other organisms, starting with UniProt or RefSeq accessions—I would build a **versioned, many-to-many protein-to-orthology mapping system**.

The goal is to map each experimentally identified protein to one or more evolutionarily supported orthology groups, while preserving the original accession, species, and protein-level identity.

Separate the system into three layers:

1. **Accession resolution:** What gene and protein does this UniProt or RefSeq accession represent in its source organism?
2. **Orthology assignment:** Which orthology group(s) does that gene belong to, and what are its relationships to genes in other species?
3. **Cross-species analysis:** How should those relationships be used when joining, aggregating, or comparing quantitative proteomics data?

Keep these layers independent. That makes it possible to update orthology data without redoing protein identification or rewriting original quantitative datasets.

## 1. Data sources and retrieval strategy

Use **Ensembl Compara as the primary orthology authority**, UniProt and NCBI for accession resolution, and NCBI ortholog data as an independent comparison source where useful.

| Task | Recommended source |
|---|---|
| UniProt accession → gene / Ensembl ID | UniProt ID Mapping |
| RefSeq accession → gene / Ensembl ID | NCBI Datasets, NCBI Gene |
| Gene → orthologs across species | Ensembl Compara |
| Independent orthology support | NCBI Orthologs, Alliance / HCOP |
| Protein sequence verification | UniProt / RefSeq |

For this scale, download or batch-process mappings and store them locally rather than making a live web request every time a dataset is imported.

Useful endpoints and documentation:

- Ensembl Compara gene homology endpoint: https://rest.ensembl.org/documentation/info/homology_species_gene_id
- UniProt ID Mapping API: https://www.uniprot.org/help/id_mapping_prog
- NCBI ortholog data packages: https://www.ncbi.nlm.nih.gov/datasets/docs/v2/how-tos/genes/download-ortholog-data-package/

Ensembl’s homology endpoint can return orthologs filtered by target species and includes orthology classifications.

## 2. Recommended relational data model

Use a small relational schema. SQLite is sufficient for a local application or research pipeline at this scale; PostgreSQL is an option if this becomes a shared service.

The key design decision is that **protein records, gene records, and orthology groups are separate entities**.

### `ProteinAccession`

| Column | Purpose |
|---|---|
| `protein_key` | Internal primary key |
| `database` | UniProtKB, RefSeq, etc. |
| `accession` | Original accession |
| `accession_version` | RefSeq version, when present |
| `taxon_id` | NCBI Taxonomy ID |
| `gene_id` | Resolved internal gene key |
| `mapping_status` | Exact, ambiguous, unresolved |

Preserve the original accession exactly as supplied. For RefSeq, retain the versioned accession as well as a normalized accession for lookup. For UniProt, preserve isoform suffixes such as `-2`.

### `Gene`

| Column | Purpose |
|---|---|
| `gene_key` | Internal primary key |
| `taxon_id` | NCBI Taxonomy ID |
| `gene_id_namespace` | Ensembl, NCBI Gene, etc. |
| `gene_id` | Stable source identifier |
| `symbol` | Display label |
| `description` | Optional annotation |

Unique constraint: `(taxon_id, gene_id_namespace, gene_id)`.

### `OrthologyGroup`

| Column | Purpose |
|---|---|
| `orthogroup_id` | Internal stable key |
| `source` | Ensembl Compara, OrthoFinder, etc. |
| `source_group_id` | Original source group ID |
| `release` | Database release |
| `taxonomic_scope` | Scope used to define the group |

Create your own internal `orthogroup_id` and preserve the original source’s group ID separately. This supports multiple orthology sources without conflating their identifiers.

### `OrthologyGroupMember`

| Column | Purpose |
|---|---|
| `orthogroup_id` | Group key |
| `gene_key` | Member gene |
| `taxon_id` | Species |
| `source` | Evidence source |
| `release` | Source release |

This is a many-to-many junction table. Do not enforce one gene per species per group—some orthogroups contain multiple co-orthologs in the same species.

### `OrthologyRelationship`

| Column | Purpose |
|---|---|
| `gene_a_key` | First gene |
| `gene_b_key` | Second gene |
| `relationship_type` | One-to-one, one-to-many, many-to-many |
| `source` | Ensembl Compara, etc. |
| `source_release` | Release |
| `confidence` | Source-provided confidence |
| `identity_a_to_b` | Sequence identity, if available |
| `identity_b_to_a` | Reciprocal identity, if available |

Store each unordered pair once, using a canonical ordering of the internal gene keys. Keep source-provided directional identity fields in their corresponding source/target context if retained.

## 3. Processing pipeline

Implement this as a reproducible ETL pipeline (extract, transform, load), with each stage producing a persisted table and QC report.

1. **Ingest protein accessions**
   - Import input files.
   - Preserve each dataset’s protein identifier and species.
   - Normalize whitespace and known accession formatting.
   - Deduplicate lookup requests.

2. **Resolve accessions to genes**
   - Batch-map UniProt and RefSeq accessions to source gene IDs.
   - Retain all legitimate mappings.
   - Flag ambiguous or unresolved accessions.
   - Do not silently choose one gene when the source maps to several.

3. **Normalize gene identities**
   - Resolve gene IDs to a consistent namespace, preferably Ensembl stable gene IDs for Compara integration.
   - Retain original NCBI Gene IDs and source identifiers.

4. **Retrieve orthology data**
   - Retrieve orthology relationships for all source genes and target species.
   - For a reusable multi-species system, prefer a release-wide bulk dataset over querying each gene individually.

5. **Build groups and relationships**
   - Store source orthology groups and pairwise relationships separately.
   - Preserve one-to-many and many-to-many relationships, source confidence, and relationship classifications.

6. **Validate and publish**
   - Run QC.
   - Record unresolved cases.
   - Check species coverage.
   - Publish a versioned mapping snapshot for reproducible downstream analysis.

### Important: do not use transitive closure as the orthology algorithm

Suppose human gene A is orthologous to mouse genes B and C, and mouse gene C is orthologous to rat genes D and E.

It is tempting to infer that all five genes belong to one equivalence class. But pairwise orthology is not a simple equivalence relation: duplication events and lineage-specific gene loss can make naïve transitive grouping misleading.

Use the source’s gene-tree or orthogroup structure when available. Retain pairwise orthology calls as their own evidence. If you derive a cross-species group, document the grouping method and version rather than assuming every connected component is a biologically interchangeable gene family.

## 4. Use in cross-species proteomics analysis

Do not immediately collapse every protein in every dataset to orthogroup-level abundance. Create a mapping layer that lets downstream analyses choose their resolution.

| Analysis level | What gets compared | Main caveat |
|---|---|---|
| Protein accession | Specific protein products | Isoforms and accession differences complicate matching |
| Gene | Gene-level abundance | Protein inference may not uniquely resolve genes |
| One-to-one ortholog | Conserved gene pairs | Excludes valid co-orthologs |
| Orthogroup | Related genes across species | May combine duplicated genes with divergent functions |

For this project, retain all orthologs in the database, but support multiple analysis views:

- **All orthologs:** for discovery and annotation.
- **One-to-one orthologs:** for conservative cross-species comparisons.
- **Orthogroup-level:** for analyses where the biological question supports combining co-orthologs.
- **Unresolved / ambiguous:** retained as explicit outcomes rather than discarded.

A key proteomics caveat: if peptides are shared between paralogs, the source protein inference may already be ambiguous. Orthology mapping cannot recover gene-specific abundance that the peptides themselves did not resolve. Keep protein inference ambiguity separate from orthology ambiguity.

## 5. Quality control

| QC metric | What it tells you |
|---|---|
| Accession resolution rate | Fraction of input accessions mapped to a gene |
| Unique gene resolution rate | Fraction resolving to exactly one gene |
| Orthology coverage | Fraction of genes with at least one ortholog in target species |
| One-to-many frequency | How often orthology is not one-to-one |
| Unmapped species pairs | Whether a species is missing from the source release |
| Cross-source agreement | Whether independent databases support the relationship |

Track why an accession failed to map: obsolete accession, unreviewed record, missing gene association, taxonomic mismatch, or genuinely unresolved identity. These cases have different implications.

## 6. First implementation (MVP)

### Human + mouse + rat

- UniProt and RefSeq accession ingestion
- NCBI Taxonomy IDs for species identity:
  - Human: `9606`
  - Mouse: `10090`
  - Rat: `10116`
- Accession-to-gene resolution with source provenance
- Ensembl Compara orthology import
- Pairwise relationship table + orthogroup membership table
- SQLite database with versioned imports
- CSV export for mapped proteins and orthology relationships
- QC report for unresolved and ambiguous mappings

### Expand to other organisms

Add new species by importing their gene and orthology records, not by rewriting the schema. Keep source and release metadata so a future Ensembl update can be compared with the previous snapshot.

Ensembl Compara is an excellent starting point, but its orthology groups and NCBI’s ortholog sets are not guaranteed to be identical. Retain source-specific calls rather than merging them into a single unqualified “truth.” If you later need a consensus mapping, make that a separately versioned layer with explicit rules.

## Bottom line

Build a local, versioned, gene-centric orthology database; preserve all accession and gene relationships; and defer decisions about collapsing co-orthologs until the analysis stage. This gives you the flexibility to combine proteomics datasets without throwing away biologically meaningful relationships.
