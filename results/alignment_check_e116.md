# Compara 116 gene-tree alignment, checked against the store

`Compara.116.protein_default.aa.fasta.gz` (sha256 `6550e2957259c89a…`), by `python -m logs_orthology.alignment_check`.

## Format

- 54,308 alignments separated by `//`, 4,229,614 sequences; 0 alignments have rows of unequal length.
- Ours: human 19,690, mouse 22,045, rat 22,379; 0 appear more than once.

## The store's proteins

- Pair rows: 1,001,934; a protein missing from the alignment: 0; the two proteins in different alignments: 751,756.
- Split rows, by relationship type, species pair and whether the two genes share a gene tree:
  - `ortholog_many2many|homo_sapiens~mus_musculus|different_trees`: 405
  - `ortholog_many2many|homo_sapiens~rattus_norvegicus|different_trees`: 193
  - `ortholog_one2many|homo_sapiens~mus_musculus|different_trees`: 68
  - `ortholog_one2many|homo_sapiens~rattus_norvegicus|different_trees`: 78
  - `ortholog_one2one|homo_sapiens~mus_musculus|different_trees`: 5
  - `ortholog_one2one|homo_sapiens~rattus_norvegicus|different_trees`: 7
  - `ortholog_one2one|mus_musculus~rattus_norvegicus|different_trees`: 4
  - `other_paralog|homo_sapiens~homo_sapiens|different_trees`: 128,020
  - `other_paralog|mus_musculus~mus_musculus|different_trees`: 295,997
  - `other_paralog|rattus_norvegicus~rattus_norvegicus|different_trees`: 326,979
- Members (one canonical protein per gene): 64,114; missing: 0.
- Alignments holding the members of two trees: 0.
- Our proteins in the alignment that are not a member's canonical protein: 0.

## Leg 1, by entry: is the UniProt entry's sequence its gene's tree protein?

Entries x genes from the agrees view (canonical entries, no isoforms). An entry count, not a residue rate.

| species | entry x gene | identical | differs | gene in no tree | other |
|---|---:|---:|---:|---:|---:|
| homo_sapiens | 19,446 | 17,812 (91.6%) | 1,588 (8.2%) | 46 | 0 |
| mus_musculus | 15,855 | 13,714 (86.5%) | 2,096 (13.2%) | 45 | 0 |
| rattus_norvegicus | 4,967 | 2,841 (57.2%) | 2,124 (42.8%) | 2 | 0 |
