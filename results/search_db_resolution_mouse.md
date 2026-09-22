# Search-database resolution: both sources side by side

Generated 2026-09-22 from `search_db_mouse_e116.tsv` (mzLib `EnsemblGeneResolver`), search database sha256 `fb52debf545202553ede1616c3c9f859632abbbf8dd71c2393133ca616813c37`, against the Ensembl 116 primary-assembly GTF.

**17,277 base entries** (722 further rows are sequence-variant proteoforms, resolved through their entry and not counted here).

| outcome | Ensembl xref | search XML's own links |
|---|---:|---:|
| `resolved` | 15,494 | 15,474 |
| `multi_gene` | 123 | 124 |
| `off_primary_only` | 0 | 0 |
| `not_in_source` | 1,660 | 1,679 |

The multi-gene difference is not an error in either source. UniProt links an accession to every Ensembl transcript encoding it (readthrough genes, unnamed novel genes, identical paralogs); Ensembl's xref assigns it where Ensembl's mapping puts it. Every gene row carries `ensembl_xref_agrees`, so neither is dropped:

| XML multi-gene accessions, by number of genes the xref agrees with | accessions |
|---|---:|
| 1 | 1 |
| 2 | 92 |
| 3 | 10 |
| 4 | 8 |
| 6 | 1 |
| 7 | 1 |
| 8 | 1 |
| 9 | 9 |
| 13 | 1 |

No gene id in either source: **1,640**. No xref gene but the XML links one (UniProt/Ensembl drift): **20**. The reverse, the xref resolves an entry whose XML links no gene in the set: **39**.

**Parity:** for 17,277 of 17,277 base entries, the genes the xref agrees with are exactly the genes `resolve.py` finds.
