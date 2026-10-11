# Search-database resolution: both sources side by side

Generated 2026-10-11 from `search_db_rat_canonical-v3_e116.tsv` (mzLib `EnsemblGeneResolver`), search database sha256 `7f08fd3c9eac4efe0e0402b305aa5af43f155644094b6df93643afa3baeafe93`, against the Ensembl 116 primary-assembly GTF.

**21,471 base entries** (198 further rows are sequence-variant proteoforms, resolved through their entry and not counted here).

| outcome | Ensembl xref | search XML's own links |
|---|---:|---:|
| `resolved` | 14,632 | 17,321 |
| `multi_gene` | 82 | 153 |
| `off_primary_only` | 0 | 955 |
| `not_in_source` | 6,757 | 3,042 |

The multi-gene difference is not an error in either source. UniProt links an accession to every Ensembl transcript encoding it (readthrough genes, unnamed novel genes, identical paralogs); Ensembl's xref assigns it where Ensembl's mapping puts it. Every gene row carries `ensembl_xref_agrees`, so neither is dropped:

| XML multi-gene accessions, by number of genes the xref agrees with | accessions |
|---|---:|
| 0 | 67 |
| 1 | 25 |
| 2 | 49 |
| 3 | 7 |
| 4 | 3 |
| 5 | 2 |

No gene id in either source: **2,840**. No xref gene but the XML links one (UniProt/Ensembl drift): **3,489**. The reverse, the xref resolves an entry whose XML links no gene in the set: **729**.

**Parity:** for 21,471 of 21,471 base entries, the genes the xref agrees with are exactly the genes `resolve.py` finds.

## By UniProt dataset (`UP000002494_all_genecentric_2026_03_agingPTM-v3.xml`)

Coverage is the agrees view: an entry counts when the Ensembl xref agrees with at least one of its genes.

| dataset | entries | one gene | several genes | no gene | covered | no primary gene name (of which covered) | no Ensembl dbReference (of which covered) | neither (of which covered) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Swiss-Prot | 8,213 | 4,857 | 44 | 3,312 | 59.7% | 113 (43) | 3,042 (202) | 65 (2) |
| TrEMBL | 13,258 | 9,775 | 38 | 3,445 | 74.0% | 853 (138) | 0 (0) | 0 (0) |

**Ensembl's xref has never heard of the accession, but the XML links a gene** (silent, not a disagreement; the agrees view drops these):

| dataset | entries | created by UniProt in |
|---|---:|---|
| Swiss-Prot | 44 | 1986: 1, 1989: 2, 1990: 2, 1992: 1, 1993: 1, 1994: 3, 1995: 1, 1996: 2, 1997: 1, 1998: 1, 2000: 1, 2001: 2, 2004: 3, 2005: 5, 2006: 7, 2007: 4, 2008: 3, 2009: 1, 2016: 2, 2026: 1 |
| TrEMBL | 3,445 | 2004: 3, 2025: 2,713, 2026: 729 |

Covered: agrees view **14,714** (68.5%); agrees-or-silent (not a v1 view) **18,203** (84.8%).
