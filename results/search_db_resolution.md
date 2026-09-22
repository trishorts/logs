# Search-database resolution: both sources side by side

Generated 2026-09-22 from `search_db_human_e116.tsv` (mzLib `EnsemblGeneResolver`), search database sha256 `760984e8d402ade6b1105b811532bdd4041e33e66bb5dc204402d4d6a7be8838`, against the Ensembl 116 primary-assembly GTF.

**20,416 base entries** (32,337 further rows are sequence-variant proteoforms, resolved through their entry and not counted here).

| outcome | Ensembl xref (sent in 005-logs) | search XML's own links |
|---|---:|---:|
| `resolved` | 19,257 | 18,988 |
| `multi_gene` | 69 | 350 |
| `off_primary_only` | 62 | 62 |
| `not_in_source` | 1,028 | 1,016 |

The multi-gene difference is not an error in either source. UniProt links an accession to every Ensembl transcript encoding it (readthrough genes, unnamed novel genes, identical paralogs); Ensembl's xref assigns it where Ensembl's mapping puts it. Every gene row carries `ensembl_xref_agrees`, so neither is dropped:

| XML multi-gene accessions, by number of genes the xref agrees with | accessions |
|---|---:|
| 1 | 281 |
| 2 | 56 |
| 3 | 6 |
| 5 | 2 |
| 6 | 1 |
| 7 | 1 |
| 10 | 1 |
| 12 | 1 |
| 14 | 1 |

No gene id in either source: **1,012**. No xref gene but the XML links one (UniProt/Ensembl drift): **16**.

**Parity:** for 20,412 of 20,416 base entries, the genes the xref agrees with are exactly the genes `resolve.py` finds; the 4 others are entries whose XML carries no Ensembl link at all.
