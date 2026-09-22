# Search-database resolution: both sources side by side

Generated 2026-09-22 from `search_db_rat_e116.tsv` (mzLib `EnsemblGeneResolver`), search database sha256 `abf612c90f0a3c202d4e6353c5465bd22a5800990abb947d5ea9b43ad198dd89`, against the Ensembl 116 primary-assembly GTF.

**8,228 base entries** (198 further rows are sequence-variant proteoforms, resolved through their entry and not counted here).

| outcome | Ensembl xref | search XML's own links |
|---|---:|---:|
| `resolved` | 4,864 | 4,182 |
| `multi_gene` | 44 | 45 |
| `off_primary_only` | 0 | 950 |
| `not_in_source` | 3,320 | 3,051 |

The multi-gene difference is not an error in either source. UniProt links an accession to every Ensembl transcript encoding it (readthrough genes, unnamed novel genes, identical paralogs); Ensembl's xref assigns it where Ensembl's mapping puts it. Every gene row carries `ensembl_xref_agrees`, so neither is dropped:

| XML multi-gene accessions, by number of genes the xref agrees with | accessions |
|---|---:|
| 0 | 1 |
| 1 | 9 |
| 2 | 27 |
| 3 | 6 |
| 4 | 1 |
| 5 | 1 |

No gene id in either source: **2,847**. No xref gene but the XML links one (UniProt/Ensembl drift): **44**. The reverse, the xref resolves an entry whose XML links no gene in the set: **725**.

**Parity:** for 7,479 of 8,228 base entries, the genes the xref agrees with are exactly the genes `resolve.py` finds; of the 749 others, 204 are entries whose XML carries no Ensembl link at all and the rest disagree on the genes themselves.
