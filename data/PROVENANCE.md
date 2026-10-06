# Data provenance — logs

Every data input is recorded here so the repo is **reproducible-by-reference** even though large raw
files are gitignored. One row per dataset/file (or logical group).

| Dataset | Local path | Source / origin | Repository accession | Acquired | Checksum (SHA-256) | Notes |
|---|---|---|---|---|---|---|
| _example_ | `data/raw/run1.raw` | Smith lab, Velos | MassIVE MSV000000000 | YYYY-MM-DD | `…` | top-down Jurkat |

Rules:
- Raw spectra / databases are **gitignored** — this table is their record. Do not commit the bytes.
- Public re-analyses: cite the original accession; deposit new results (see `massive-reanalysis-upload`).
- Fill the checksum at acquisition: `Get-FileHash -Algorithm SHA256 <path>`.

## Ensembl Compara release 116 — fetched 2026-09-22

Pinned inputs for the cross-species orthology snapshot. The bytes are gitignored; this
table is their record. A release bump is a **new snapshot**, never an in-place update.

| File | Local path | Source URL | Bytes | MD5 (published) | Verified | SHA-256 |
|---|---|---|---|---|---|---|
| `homology:homo_sapiens` | `data/compara/homo_sapiens.protein_default.homologies.tsv.gz` | <https://ftp.ensembl.org/pub/release-116/tsv/ensembl-compara/homologies/homo_sapiens/Compara.116.protein_default.homologies.tsv.gz> | 109,478,724 | `59857f48bbbdf6812999d58d7a24ccc4` | ✅ | `fc101ab6e9096609…` |
| `homology:mus_musculus` | `data/compara/mus_musculus.protein_default.homologies.tsv.gz` | <https://ftp.ensembl.org/pub/release-116/tsv/ensembl-compara/homologies/mus_musculus/Compara.116.protein_default.homologies.tsv.gz> | 111,917,367 | `8f9870f0f12ece5032f8e62117de9924` | ✅ | `5ebd0a7bd141840d…` |
| `homology:rattus_norvegicus` | `data/compara/rattus_norvegicus.protein_default.homologies.tsv.gz` | <https://ftp.ensembl.org/pub/release-116/tsv/ensembl-compara/homologies/rattus_norvegicus/Compara.116.protein_default.homologies.tsv.gz> | 111,039,932 | `fcf26dfca645aba1d2e272c9df6629db` | ✅ | `46e82b641aa9f8c1…` |
| `gene_tree_content` | `data/compara/vertebrates.GeneTree_content.default.e116.txt.gz` | <https://ftp.ensembl.org/pub/release-116/compara/vertebrates.GeneTree_content.default.e116.txt.gz> | 79,035,816 | `(not published)` | — *(none published)* | `83cbb4bf64234087…` |

**Redundancy caveat, from the provider's own README:** each genome-specific homology file
contains *an arbitrary subset* of the orthologies involving that genome. The human file
alone does **not** hold every human↔mouse orthology. All three taxa are fetched and
unioned; taking one would undercount silently.

## Ensembl release 116 — fetched 2026-09-22

Pinned inputs for the cross-species orthology snapshot. The bytes are gitignored; this
table is their record. A release bump is a **new snapshot**, never an in-place update.

| File | Local path | Bytes | Checksum | Verified | SHA-256 |
|---|---|---|---|---|---|
| [`homology:homo_sapiens`](https://ftp.ensembl.org/pub/release-116/tsv/ensembl-compara/homologies/homo_sapiens/Compara.116.protein_default.homologies.tsv.gz) | `data/compara/homo_sapiens.protein_default.homologies.tsv.gz` | 109,478,724 | `md5:59857f48bbbdf6812999d58d7a24ccc4` | ✅ | `fc101ab6e9096609…` |
| [`homology:mus_musculus`](https://ftp.ensembl.org/pub/release-116/tsv/ensembl-compara/homologies/mus_musculus/Compara.116.protein_default.homologies.tsv.gz) | `data/compara/mus_musculus.protein_default.homologies.tsv.gz` | 111,917,367 | `md5:8f9870f0f12ece5032f8e62117de9924` | ✅ | `5ebd0a7bd141840d…` |
| [`homology:rattus_norvegicus`](https://ftp.ensembl.org/pub/release-116/tsv/ensembl-compara/homologies/rattus_norvegicus/Compara.116.protein_default.homologies.tsv.gz) | `data/compara/rattus_norvegicus.protein_default.homologies.tsv.gz` | 111,039,932 | `md5:fcf26dfca645aba1d2e272c9df6629db` | ✅ | `46e82b641aa9f8c1…` |
| [`gene_tree_content`](https://ftp.ensembl.org/pub/release-116/compara/vertebrates.GeneTree_content.default.e116.txt.gz) | `data/compara/vertebrates.GeneTree_content.default.e116.txt.gz` | 79,035,816 | `none:(not published)` | — *(none published)* | `83cbb4bf64234087…` |
| [`gtf:homo_sapiens`](https://ftp.ensembl.org/pub/release-116/gtf/homo_sapiens/Homo_sapiens.GRCh38.116.gtf.gz) | `data/compara/Homo_sapiens.GRCh38.116.gtf.gz` | 141,121,632 | `sum:49151 137815` | ✅ | `ed992f0eac7197d9…` |
| [`gtf:mus_musculus`](https://ftp.ensembl.org/pub/release-116/gtf/mus_musculus/Mus_musculus.GRCm39.116.gtf.gz) | `data/compara/Mus_musculus.GRCm39.116.gtf.gz` | 107,856,522 | `sum:42607 105329` | ✅ | `5c29fd9e3157cf40…` |
| [`gtf:rattus_norvegicus`](https://ftp.ensembl.org/pub/release-116/gtf/rattus_norvegicus/Rattus_norvegicus.GRCr8.116.gtf.gz) | `data/compara/Rattus_norvegicus.GRCr8.116.gtf.gz` | 23,181,146 | `sum:48460 22638` | ✅ | `e025aa7eeefa74e8…` |
| [`xref:uniprot:homo_sapiens`](https://ftp.ensembl.org/pub/release-116/tsv/homo_sapiens/Homo_sapiens.GRCh38.116.uniprot.tsv.gz) | `data/compara/Homo_sapiens.GRCh38.116.uniprot.tsv.gz` | 2,124,003 | `sum:362 2075` | ✅ | `f1e26db23b0771f7…` |
| [`xref:refseq:homo_sapiens`](https://ftp.ensembl.org/pub/release-116/tsv/homo_sapiens/Homo_sapiens.GRCh38.116.refseq.tsv.gz) | `data/compara/Homo_sapiens.GRCh38.116.refseq.tsv.gz` | 4,240,814 | `sum:28948 4142` | ✅ | `cf243992943c3c54…` |
| [`xref:entrez:homo_sapiens`](https://ftp.ensembl.org/pub/release-116/tsv/homo_sapiens/Homo_sapiens.GRCh38.116.entrez.tsv.gz) | `data/compara/Homo_sapiens.GRCh38.116.entrez.tsv.gz` | 6,093,982 | `sum:28782 5952` | ✅ | `745945cbafa5d6c7…` |
| [`xref:uniprot:mus_musculus`](https://ftp.ensembl.org/pub/release-116/tsv/mus_musculus/Mus_musculus.GRCm39.116.uniprot.tsv.gz) | `data/compara/Mus_musculus.GRCm39.116.uniprot.tsv.gz` | 1,164,777 | `sum:4997 1138` | ✅ | `19b91eefd8cc3946…` |
| [`xref:refseq:mus_musculus`](https://ftp.ensembl.org/pub/release-116/tsv/mus_musculus/Mus_musculus.GRCm39.116.refseq.tsv.gz) | `data/compara/Mus_musculus.GRCm39.116.refseq.tsv.gz` | 2,403,940 | `sum:28927 2348` | ✅ | `1d642d944f129854…` |
| [`xref:entrez:mus_musculus`](https://ftp.ensembl.org/pub/release-116/tsv/mus_musculus/Mus_musculus.GRCm39.116.entrez.tsv.gz) | `data/compara/Mus_musculus.GRCm39.116.entrez.tsv.gz` | 3,156,296 | `sum:40039 3083` | ✅ | `2e02010598e4c649…` |
| [`xref:uniprot:rattus_norvegicus`](https://ftp.ensembl.org/pub/release-116/tsv/rattus_norvegicus/Rattus_norvegicus.GRCr8.116.uniprot.tsv.gz) | `data/compara/Rattus_norvegicus.GRCr8.116.uniprot.tsv.gz` | 778,837 | `sum:57512 761` | ✅ | `8b1c91f3d88bfafe…` |
| [`xref:refseq:rattus_norvegicus`](https://ftp.ensembl.org/pub/release-116/tsv/rattus_norvegicus/Rattus_norvegicus.GRCr8.116.refseq.tsv.gz) | `data/compara/Rattus_norvegicus.GRCr8.116.refseq.tsv.gz` | 1,765,514 | `sum:64112 1725` | ✅ | `2598a0b3f89efb4d…` |
| [`xref:entrez:rattus_norvegicus`](https://ftp.ensembl.org/pub/release-116/tsv/rattus_norvegicus/Rattus_norvegicus.GRCr8.116.entrez.tsv.gz) | `data/compara/Rattus_norvegicus.GRCr8.116.entrez.tsv.gz` | 712,176 | `sum:15990 696` | ✅ | `621fd12fe992d6f1…` |

**Redundancy caveat, from the provider's own README:** each genome-specific homology
file holds *an arbitrary subset* of the orthologies involving that genome. The human
file alone does **not** contain every human↔mouse orthology. All three taxa are fetched
and unioned; taking one would undercount silently.

**Checksum note:** Ensembl publishes MD5 under `tsv/ensembl-compara/`, but only the
classic BSD `sum` (16-bit checksum + 1 KiB block count) under `gtf/` and `tsv/`. Both
are checked; the kind actually used is recorded per row above. The gene-tree content
dump has no published checksum at all, which is recorded rather than glossed.

## Ensembl release 116 — fetched 2026-10-06

Pinned inputs for the cross-species orthology snapshot. The bytes are gitignored; this
table is their record. A release bump is a **new snapshot**, never an in-place update.

| File | Local path | Bytes | Checksum | Verified | SHA-256 |
|---|---|---|---|---|---|
| [`gene_tree_alignment`](https://ftp.ensembl.org/pub/release-116/emf/ensembl-compara/homologies/Compara.116.protein_default.aa.fasta.gz) | `data/compara/Compara.116.protein_default.aa.fasta.gz` | 908,157,830 | `md5:39f5742f5d9d597f2396ec7c462a6c53` | ✅ | `6550e2957259c89a…` |

**Redundancy caveat, from the provider's own README:** each genome-specific homology
file holds *an arbitrary subset* of the orthologies involving that genome. The human
file alone does **not** contain every human↔mouse orthology. All three taxa are fetched
and unioned; taking one would undercount silently.

**Checksum note:** Ensembl publishes MD5 under `tsv/ensembl-compara/`, but only the
classic BSD `sum` (16-bit checksum + 1 KiB block count) under `gtf/` and `tsv/`. Both
are checked; the kind actually used is recorded per row above. The gene-tree content
dump has no published checksum at all, which is recorded rather than glossed.
