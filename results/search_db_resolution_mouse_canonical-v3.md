# Search-database resolution: both sources side by side

Generated 2026-10-11 from `search_db_mouse_canonical-v3_e116.tsv` (mzLib `EnsemblGeneResolver`), search database sha256 `3c4ac3fb481e8ff1430d3f7a7aab4c2c83d44ae1de117ea942c8aefd5ffb4cc6`, against the Ensembl 116 primary-assembly GTF.

**21,860 base entries** (714 further rows are sequence-variant proteoforms, resolved through their entry and not counted here).

| outcome | Ensembl xref | search XML's own links |
|---|---:|---:|
| `resolved` | 18,893 | 19,942 |
| `multi_gene` | 237 | 273 |
| `off_primary_only` | 0 | 0 |
| `not_in_source` | 2,730 | 1,645 |

The multi-gene difference is not an error in either source. UniProt links an accession to every Ensembl transcript encoding it (readthrough genes, unnamed novel genes, identical paralogs); Ensembl's xref assigns it where Ensembl's mapping puts it. Every gene row carries `ensembl_xref_agrees`, so neither is dropped:

| XML multi-gene accessions, by number of genes the xref agrees with | accessions |
|---|---:|
| 0 | 37 |
| 1 | 1 |
| 2 | 183 |
| 3 | 17 |
| 4 | 13 |
| 5 | 3 |
| 6 | 4 |
| 7 | 2 |
| 8 | 1 |
| 9 | 10 |
| 13 | 1 |
| 23 | 1 |

No gene id in either source: **1,606**. No xref gene but the XML links one (UniProt/Ensembl drift): **1,124**. The reverse, the xref resolves an entry whose XML links no gene in the set: **39**.

**Parity:** for 21,860 of 21,860 base entries, the genes the xref agrees with are exactly the genes `resolve.py` finds.

## By UniProt dataset (`UP000000589_all_genecentric_2026_03_agingPTM-v3.xml`)

Coverage is the agrees view: an entry counts when the Ensembl xref agrees with at least one of its genes.

| dataset | entries | one gene | several genes | no gene | covered | no primary gene name (of which covered) | no Ensembl dbReference (of which covered) | neither (of which covered) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Swiss-Prot | 17,219 | 15,471 | 123 | 1,625 | 90.6% | 262 (102) | 1,645 (39) | 160 (0) |
| TrEMBL | 4,641 | 3,422 | 114 | 1,105 | 76.2% | 45 (14) | 0 (0) | 0 (0) |

**Ensembl's xref has never heard of the accession, but the XML links a gene** (silent, not a disagreement; the agrees view drops these):

| dataset | entries | created by UniProt in |
|---|---:|---|
| Swiss-Prot | 19 | 1994: 3, 1995: 2, 1996: 1, 2000: 1, 2001: 1, 2003: 1, 2005: 1, 2006: 3, 2007: 2, 2008: 3, 2026: 1 |
| TrEMBL | 1,105 | 2025: 45, 2026: 1,060 |

Covered: agrees view **19,130** (87.5%); agrees-or-silent (not a v1 view) **20,254** (92.7%).
