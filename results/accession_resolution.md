# Accession → gene resolution — Ensembl release 116 cross-reference dumps

Generated 2026-09-22. Measured from Ensembl's own stable-id → external-accession
dumps, pinned and checksum-verified in `data/PROVENANCE.md`.

Two questions: **how often does one accession mean more than one gene** (our last open
modelling question), and **is RefSeq actually expensive** (a claim we made and should
re-test).

## 1 · The multi-gene question

UniProt accession → distinct Ensembl gene ids:

| species | accessions | → 1 gene | → 2 | → 3 | → 4+ | % exactly one |
|---|---:|---:|---:|---:|---:|---:|
| human | 111,285 | 105,476 | 4,630 | 302 | 877 | **94.78%** |
| mouse | 65,181 | 64,780 | 320 | 33 | 48 | **99.39%** |
| rat | 48,663 | 48,480 | 144 | 23 | 16 | **99.62%** |

Restricted to **reviewed** (SwissProt) accessions, which is what a curated search database
contains:

| species | reviewed accessions | multi-gene | % exactly one gene |
|---|---:|---:|---:|
| human | 19,383 | 1,354 | **93.01%** |
| mouse | 15,579 | 123 | **99.21%** |
| rat | 4,896 | 44 | **99.10%** |

**Curation does not reduce the ambiguity — in human it slightly increases it.** A reviewed
entry is one curated protein sequence, and a protein encoded by several near-identical
loci gets one record spanning all of them. Filtering to SwissProt therefore does not make
the multi-gene case go away.

The worst reviewed human cases, which are the shape of the problem rather than outliers:

| accession | distinct genes |
|---|---:|
| `P43628` | 24 |
| `Q99706` | 22 |
| `P43626` | 21 |
| `Q5JQC4` | 17 |
| `P43630` | 14 |
| `P62805` | 14 |
| `P43631` | 13 |
| `P24071` | 12 |
| `P43632` | 12 |
| `B6A8C7` | 10 |
| `O75175` | 10 |
| `O95167` | 10 |

`P62805` is histone H4 — one protein sequence, 14 loci, and peptides that cannot
distinguish them. It is abundant in essentially every proteomics experiment. This is the
protein-inference ambiguity our design keeps separate from orthology ambiguity, and it is
not a corner case.

## 2 · RefSeq

| species | RefSeq protein accessions | `NP_` curated | `XP_` predicted | % → exactly one gene |
|---|---:|---:|---:|---:|
| human | 161,484 | 69,569 | 91,915 | **97.13%** |
| mouse | 94,258 | 49,218 | 45,040 | **99.96%** |
| rat | 78,259 | 24,255 | 54,004 | **99.96%** |

`NP_` is curated and `XP_` is model-predicted. They are not the same quality of evidence
and are counted apart so a resolution rate cannot be inflated by predictions.

## 3 · NCBI GeneID

| species | distinct GeneIDs | % → exactly one Ensembl gene |
|---|---:|---:|
| human | 34,781 | **92.69%** |
| mouse | 30,096 | **99.50%** |
| rat | 23,795 | **98.69%** |

## 4 · Isoform suffixes

| species | accessions with an isoform suffix (`P12345-2`) |
|---|---:|
| human | 35,202 |
| mouse | 10,215 |
| rat | 794 |

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
