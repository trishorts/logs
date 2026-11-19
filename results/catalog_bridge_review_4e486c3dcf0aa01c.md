# smith-chem-wisc/PXReprise#26 re-run on catalog 4e486c3dcf0aa01c

The PR's `protein_orthologs` SQL at `a3195c166`, word for word, on catalog `4e486c3dcf0aa01c` (read-only), with the
four snapshot tables rebuilt from snapshot artefact `0fe30fe8d4edc728`'s own macros. Gene resolutions:
`logs:DEF-GENE-RESOLUTION v1` (42 artefacts). Built in 0.85 s.

- 182,580 rows over 64,211 accessions; one row per key: True
  (`protein_index` has 0 duplicate accessions).
- GFAP P14136: mus_musculus P03995 (ortholog_one2one, high confidence True); rattus_norvegicus P47819 (ortholog_one2one, high confidence True).
- `not_in_gene_set`: 0 rows. Every gene is in `gene_ortholog_status` in every direction:
  True.

| status | rows | accessions |
|---|---:|---:|
| has_ortholog | 155,058 | 54,747 |
| no_gene | 13,754 | 6,877 |
| tree_lacks_target_species | 7,185 | 5,149 |
| no_edge_in_shared_tree | 5,535 | 4,111 |
| not_in_any_tree | 1,048 | 518 |

## Answered both `no_gene` and with a gene

811 held accessions have a no-gene row and a gene row (counted straight from
`gene_resolutions`). Their gene rows by source: {'ensembl_xref': 811}; their outcomes: {'not_in_source': 282, 'off_primary_only': 529}.
The bridge answers 1,622 (accession, target species) pairs both ways.

- Rows whose outcome links no gene, by status: {'not_in_source|has_ortholog': 651, 'not_in_source|no_edge_in_shared_tree': 4, 'not_in_source|no_gene': 11526, 'not_in_source|tree_lacks_target_species': 8, 'off_primary_only|has_ortholog': 1104, 'off_primary_only|no_edge_in_shared_tree': 20, 'off_primary_only|no_gene': 2228, 'off_primary_only|tree_lacks_target_species': 14}.
- Partner rows by the partner's outcome: {'multi_gene': 7363, 'not_in_source': 608, 'off_primary_only': 1058, 'resolved': 127359}.

| accession | outcome | gene_id | source |
|---|---|---|---|
| A0A096MIX6 | off_primary_only |  | search_database_dbreference |
| A0A096MIX6 | off_primary_only | ENSRNOG00000083187 | ensembl_xref |
| A0A0G2JTY4 | off_primary_only |  | search_database_dbreference |
| A0A0G2JTY4 | off_primary_only | ENSRNOG00000054264 | ensembl_xref |
| A0A0G2K2P5 | not_in_source |  | search_database_dbreference |
| A0A0G2K2P5 | not_in_source | ENSRNOG00000011077 | ensembl_xref |

## Partners

18,670 ortholog rows have no partner accession. For 21 of them
(13 partner genes), some searched database holds an accession of the gene that no search held.
