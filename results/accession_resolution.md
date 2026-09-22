# Accession → gene resolution — Ensembl release 116 cross-reference dumps

Generated 2026-09-22. Measured from Ensembl's own stable-id → external-accession
dumps, pinned and checksum-verified in `data/PROVENANCE.md`.

Two questions: **how often does one accession mean more than one gene** (our last open
modelling question), and **is RefSeq actually expensive** (a claim we made and should
re-test).

## 0 · A correction, stated before the numbers

An earlier version of this measurement counted **every** gene id in the xref dump. Ensembl
references genes on ALT haplotypes and patches, where a locus such as KIR appears on many
alternate haplotypes — so one curated protein looked as though it mapped to two dozen
genes that are in fact the same gene described repeatedly.

| reviewed human accessions | multi-gene | rate |
|---|---:|---:|
| counting every gene id | 1,354 | **6.99%** |
| counting primary-assembly genes | 70 | **0.36%** |

**1,284 of the 1,354 apparent multi-gene cases were ALT or
patch duplicates.** Everything below counts primary-assembly genes only. The effect is
human-specific — the human xref dump references 3,274
off-primary genes while mouse and rat reference none — so the unrestricted measurement
also invented a species difference that does not exist.

## 1 · The multi-gene question

UniProt accession → distinct **primary-assembly** Ensembl gene ids:

| species | accessions | → 0 | → 1 | → 2 | → 3 | → 4+ | % exactly one |
|---|---:|---:|---:|---:|---:|---:|---:|
| human | 111,285 | 2,273 | 108,754 | 225 | 17 | 16 | **97.73%** |
| mouse | 65,181 | 0 | 64,780 | 320 | 33 | 48 | **99.39%** |
| rat | 48,663 | 0 | 48,480 | 144 | 23 | 16 | **99.62%** |

Restricted to **reviewed** (SwissProt) accessions, which is what a curated search database
contains:

| species | reviewed | multi-gene | resolving to nothing | % exactly one |
|---|---:|---:|---:|---:|
| human | 19,383 | 70 | 62 | **99.32%** |
| mouse | 15,579 | 123 | 0 | **99.21%** |
| rat | 4,896 | 44 | 0 | **99.10%** |

**The multi-gene case is rare — well under 1% — but it is not evenly spread.** The genuine
cases are almost entirely histone clusters and a few cancer/testis antigen families: one
protein sequence genuinely encoded by many loci on the primary assembly.

The worst genuine reviewed human cases:

| accession | distinct primary genes |
|---|---:|
| `P62805` | 14 |
| `Q5JQC4` | 12 |
| `P68431` | 10 |
| `Q0WX57` | 7 |
| `Q9ULZ0` | 6 |
| `P0C0S8` | 5 |
| `P62807` | 5 |
| `A1L429` | 3 |
| `O14599` | 3 |
| `P0DN86` | 3 |
| `P23610` | 3 |
| `Q6IEY1` | 3 |

`P62805` is histone H4 — one protein sequence, 14 real loci, peptides that cannot
distinguish them, and abundant in essentially every proteomics experiment. So although the
*rate* is below 1%, the affected proteins are not obscure. A rare class with high abundance
is exactly the one a sampled test set will miss.

## 2 · RefSeq

| species | RefSeq protein accessions | `NP_` curated | `NP_` → one gene | `XP_` predicted | `XP_` → one gene | combined → one gene |
|---|---:|---:|---:|---:|---:|---:|
| human | 161,484 | 69,569 | **99.58%** | 91,915 | 94.87% | 96.90% |
| mouse | 94,258 | 49,218 | **99.96%** | 45,040 | 99.96% | 99.96% |
| rat | 78,259 | 24,255 | **99.94%** | 54,004 | 99.97% | 99.96% |

`NP_` is curated and `XP_` is model-predicted. They are not the same quality of evidence
and are counted apart so a resolution rate cannot be inflated -- or deflated -- by
predictions. **Correction (008-logs):** 007-logs quoted the combined human rate, 96.90%,
against the `NP_` count as though it were the curated rate. It is not; see the `NP_` column.

How each link was made, by accession class (xref rows, i.e. per transcript):

| species | class | DIRECT | SEQUENCE_MATCH | INFERRED_PAIR |
|---|---|---:|---:|---:|
| human | `NP_` | 60,727 | 582 | 17,987 |
| human | `XP_` | 24,884 | 98,567 | 53,562 |
| mouse | `NP_` | 39,176 | 2,569 | 9,225 |
| mouse | `XP_` | 17,751 | 222 | 27,246 |
| rat | `NP_` | 14,412 | 3,980 | 7,276 |
| rat | `XP_` | 21,052 | 50 | 32,937 |

## 3 · NCBI GeneID

| species | distinct GeneIDs | % → exactly one Ensembl gene |
|---|---:|---:|
| human | 34,781 | **97.57%** |
| mouse | 30,096 | **99.50%** |
| rat | 23,795 | **98.69%** |

## 4 · Isoform suffixes

| species | distinct accessions with an isoform suffix (`P12345-2`) | xref rows |
|---|---:|---:|
| human | **25,177** | 35,202 |
| mouse | **8,667** | 10,215 |
| rat | **778** | 794 |

**Correction (008-logs):** 007-logs reported the row count (one row per transcript) as
the accession count.

`dataRepo` measured zero isoform-suffixed accessions in their corpus. Whether this
reference contains any at all says whether that zero is a property of their corpus or of
the identifier space.

## 5 · Evidence type

`info_type` records *how* Ensembl made each link. `DIRECT` is an asserted mapping;
`SEQUENCE_MATCH` is inferred from alignment and is weaker. A resolution layer that treats
them alike is reporting an inference as an assertion.

- **human** — UniProt: `{'DIRECT': 159011, 'SEQUENCE_MATCH': 17844}`
- **mouse** — UniProt: `{'DIRECT': 76806, 'SEQUENCE_MATCH': 10936}`
- **rat** — UniProt: `{'DIRECT': 38263, 'SEQUENCE_MATCH': 13688}`
