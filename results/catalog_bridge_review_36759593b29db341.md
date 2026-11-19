
## The table the catalog serves (`ca61ffbaa`)

The catalog already holds `protein_orthologs`. We recomputed it independently, from `gene_resolutions`, `protein_genes`
and the snapshot's own macros, and compared the rows on (protein_accession, species, resolution_outcome, resolution_source, resolution_xref_agreement, gene_id, target_species, status, relationship_type, partner_gene, partner_accession, partner_resolution_source, partner_xref_agreement).

- Served: 180,930 rows over 64,198 accessions. Recomputed: 180,930 rows. Only served:
  0; only recomputed: 0.
- (accession, target species) pairs both `no_gene` and with a gene: 0.
- Definition columns: [['logs:DEF-GENE-RESOLUTION v2', 'logs:DEF-ORTHOLOGY v1', 180930]].
- Statuses: {'has_ortholog': 155056, 'no_gene': 12126, 'tree_lacks_target_species': 7183, 'no_edge_in_shared_tree': 5535, 'not_in_any_tree': 1030}.
- The catalog's orthology checks: {'true': 15}.
- GFAP P14136: [['mus_musculus', 'P03995', 'ortholog_one2one', 'search_database_dbreference', 'agrees', 'search_database_dbreference', 'agrees'], ['rattus_norvegicus', 'P47819', 'ortholog_one2one', 'search_database_dbreference', 'agrees', 'search_database_dbreference', 'agrees']].

What the definition's views leave out:

- Rows by `resolution_xref_agreement`: {'agrees': 144352, 'disagrees': 1278, 'silent': 23174, 'None': 12126}; accessions with a gene Ensembl disagrees with:
  346.
- (accession, species) with genes but none in v2's default view (agrees or silent): [['P60484-2', 'homo_sapiens', ['ENSG00000171862'], ['disagrees']]];
  none in the search database's view (only Ensembl's xref): 811.
- Partner rows by `partner_xref_agreement`: {'agrees': 117016, 'disagrees': 678, 'silent': 18690}; ortholog rows whose every partner accession
  Ensembl disagrees with: 138.

The snapshot: pair rows by the dump they came from: {'homo_sapiens__mus_musculus': {'mus_musculus.protein_default.homologies.tsv.gz': 23764}, 'homo_sapiens__rattus_norvegicus': {'homo_sapiens.protein_default.homologies.tsv.gz': 22105}, 'mus_musculus__rattus_norvegicus': {'mus_musculus.protein_default.homologies.tsv.gz': 40027}}. Human
PTEN (ENSG00000171862): {'mus_musculus': 'no_edge_in_shared_tree', 'rattus_norvegicus': 'no_edge_in_shared_tree'}, with
0 rows in the human-mouse and human-rat pair files.
# smith-chem-wisc/PXReprise#26 re-run on catalog 36759593b29db341

The PR's `protein_orthologs` SQL at `a3195c166`, word for word, on catalog `36759593b29db341` (read-only), with the
four snapshot tables rebuilt from snapshot artefact `53618fead1317848`'s own macros. Gene resolutions:
`logs:DEF-GENE-RESOLUTION v2` (41 artefacts). Built in 1.07 s.

- 182,552 rows over 64,198 accessions; one row per key: True
  (`protein_index` has 0 duplicate accessions).
- GFAP P14136: mus_musculus P03995 (ortholog_one2one, high confidence True); rattus_norvegicus P47819 (ortholog_one2one, high confidence True).
- `not_in_gene_set`: 0 rows. Every gene is in `gene_ortholog_status` in every direction:
  True.

| status | rows | accessions |
|---|---:|---:|
| has_ortholog | 155,056 | 54,746 |
| no_gene | 13,748 | 6,874 |
| tree_lacks_target_species | 7,183 | 5,148 |
| no_edge_in_shared_tree | 5,535 | 4,111 |
| not_in_any_tree | 1,030 | 510 |

## Answered both `no_gene` and with a gene

811 held accessions have a no-gene row and a gene row (counted straight from
`gene_resolutions`). Their gene rows by source: {'ensembl_xref': 811}; their outcomes: {'not_in_source': 282, 'off_primary_only': 529}.
The bridge answers 1,622 (accession, target species) pairs both ways.

- Rows whose outcome links no gene, by status: {'not_in_source|has_ortholog': 651, 'not_in_source|no_edge_in_shared_tree': 4, 'not_in_source|no_gene': 11520, 'not_in_source|tree_lacks_target_species': 8, 'off_primary_only|has_ortholog': 1104, 'off_primary_only|no_edge_in_shared_tree': 20, 'off_primary_only|no_gene': 2228, 'off_primary_only|tree_lacks_target_species': 14}.
- Partner rows by the partner's outcome: {'multi_gene': 7363, 'not_in_source': 608, 'off_primary_only': 1058, 'resolved': 127355}.

| accession | outcome | gene_id | source |
|---|---|---|---|
| A0A096MIX6 | off_primary_only |  | search_database_dbreference |
| A0A096MIX6 | off_primary_only | ENSRNOG00000083187 | ensembl_xref |
| A0A0G2JTY4 | off_primary_only |  | search_database_dbreference |
| A0A0G2JTY4 | off_primary_only | ENSRNOG00000054264 | ensembl_xref |
| A0A0G2K2P5 | not_in_source |  | search_database_dbreference |
| A0A0G2K2P5 | not_in_source | ENSRNOG00000011077 | ensembl_xref |

## Partners

18,672 ortholog rows have no partner accession. For 23 of them
(14 partner genes), some searched database holds an accession of the gene that no search held.
