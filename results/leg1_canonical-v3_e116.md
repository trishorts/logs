# Leg 1 on the canonical-v3 search databases: is the UniProt entry its gene's tree protein?

`python -m logs_orthology.alignment_check --databases canonical-v3`, against `Compara.116.protein_default.aa.fasta.gz` (sha256 `6550e2957259c89a…`).

Entries x genes from the agrees view (no isoforms). An entry count, not a residue rate.

| species | entry x gene | identical | differs | gene in no tree | other |
|---|---:|---:|---:|---:|---:|
| homo_sapiens | 19,627 | 17,914 (91.3%) | 1,572 (8.0%) | 141 | 0 |
| homo_sapiens, Swiss-Prot | 19,411 | 17,800 (91.7%) | 1,567 (8.1%) | 44 | 0 |
| homo_sapiens, TrEMBL | 216 | 114 (52.8%) | 5 (2.3%) | 97 | 0 |
| mus_musculus | 19,553 | 17,085 (87.4%) | 2,398 (12.3%) | 70 | 0 |
| mus_musculus, Swiss-Prot | 15,832 | 13,705 (86.6%) | 2,082 (13.2%) | 45 | 0 |
| mus_musculus, TrEMBL | 3,721 | 3,380 (90.8%) | 316 (8.5%) | 25 | 0 |
| rattus_norvegicus | 14,819 | 11,463 (77.4%) | 3,277 (22.1%) | 79 | 0 |
| rattus_norvegicus, Swiss-Prot | 4,960 | 2,841 (57.3%) | 2,117 (42.7%) | 2 | 0 |
| rattus_norvegicus, TrEMBL | 9,859 | 8,622 (87.5%) | 1,160 (11.8%) | 77 | 0 |
