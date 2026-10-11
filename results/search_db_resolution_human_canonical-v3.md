# Search-database resolution: both sources side by side

Generated 2026-10-11 from `search_db_human_canonical-v3_e116.tsv` (mzLib `EnsemblGeneResolver`), search database sha256 `fd80cf8839f8c1551bddc2d24905df6098188196934f4f43fa8c3e9a276eb14c`, against the Ensembl 116 primary-assembly GTF.

**20,652 base entries** (32,296 further rows are sequence-variant proteoforms, resolved through their entry and not counted here).

| outcome | Ensembl xref | search XML's own links |
|---|---:|---:|
| `resolved` | 19,434 | 19,174 |
| `multi_gene` | 71 | 352 |
| `off_primary_only` | 149 | 162 |
| `not_in_source` | 998 | 964 |

The multi-gene difference is not an error in either source. UniProt links an accession to every Ensembl transcript encoding it (readthrough genes, unnamed novel genes, identical paralogs); Ensembl's xref assigns it where Ensembl's mapping puts it. Every gene row carries `ensembl_xref_agrees`, so neither is dropped:

| XML multi-gene accessions, by number of genes the xref agrees with | accessions |
|---|---:|
| 1 | 281 |
| 2 | 58 |
| 3 | 6 |
| 5 | 2 |
| 6 | 1 |
| 7 | 1 |
| 10 | 1 |
| 12 | 1 |
| 14 | 1 |

No gene id in either source: **960**. No xref gene but the XML links one (UniProt/Ensembl drift): **27**. The reverse, the xref resolves an entry whose XML links no gene in the set: **6**.

**Parity:** for 20,652 of 20,652 base entries, the genes the xref agrees with are exactly the genes `resolve.py` finds.

## By UniProt dataset (`UP000005640_all_genecentric_2026_03_agingPTM-v3.xml`)

Coverage is the agrees view: an entry counts when the Ensembl xref agrees with at least one of its genes.

| dataset | entries | one gene | several genes | no gene | covered | no primary gene name (of which covered) | no Ensembl dbReference (of which covered) | neither (of which covered) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Swiss-Prot | 20,329 | 19,222 | 69 | 1,038 | 94.9% | 135 (2) | 964 (4) | 133 (0) |
| TrEMBL | 323 | 212 | 2 | 109 | 66.3% | 129 (58) | 0 (0) | 0 (0) |

**Ensembl's xref has never heard of the accession, but the XML links a gene** (silent, not a disagreement; the agrees view drops these):

| dataset | entries | created by UniProt in |
|---|---:|---|
| Swiss-Prot | 16 | 2002: 2, 2003: 1, 2006: 3, 2007: 3, 2008: 5, 2017: 1, 2026: 1 |
| TrEMBL | 11 | 2025: 3, 2026: 8 |

Covered: agrees view **19,505** (94.4%); agrees-or-silent (not a v1 view) **19,532** (94.6%).
