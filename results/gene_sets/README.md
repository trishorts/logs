# Compact Ensembl gene tables

One file per (species, Ensembl release): the gene rows of the primary-assembly GTF (stable id,
version, biotype, symbol, seq region) and the GTF's provenance in a `#!key value` header. Written by
mzLib's `EnsemblGeneSetWriter` and read by `EnsemblGeneSetReader` (branch `feat/ensembl-gene-resolution`,
PR #1338). A gene set read from a table is the set read from its GTF, provenance included, so a
resolution keyed against either carries the **GTF's** sha256.

| file | genes | bytes | sha256 | source GTF (sha256, see `data/PROVENANCE.md`) | build |
|---|---:|---:|---|---|---|
| `Homo_sapiens.GRCh38.116.genes.tsv.gz` | 78,941 | 523,218 | `e72d3b85328a572a7de92581297268ec50e97dd4cd4123c1358a7dc6c931d65f` | `Homo_sapiens.GRCh38.116.gtf.gz` (`ed992f0eac7197d9…`, 141,121,632 B) | GRCh38.p14 |
| `Mus_musculus.GRCm39.116.genes.tsv.gz` | 78,348 | 592,067 | `06d91f92289211867af002de7166c8ce3f70ef31e5a373a3528afb4022670d50` | `Mus_musculus.GRCm39.116.gtf.gz` (`5c29fd9e3157cf40…`, 107,856,522 B) | GRCm39 |
| `Rattus_norvegicus.GRCr8.116.genes.tsv.gz` | 43,360 | 288,926 | `426ea43ebeceb27003e3c5597fb5411932b52118b2ad91bfed6d2328efc95995` | `Rattus_norvegicus.GRCr8.116.gtf.gz` (`e025aa7eeefa74e8…`, 23,181,146 B) | GRCr8 |

**Rebuild** (reads the table back and refuses to report success unless it is the same set):

```powershell
dotnet run --project tools/BuildGeneSet -c Release -- data/compara/<Species.Assembly>.116.gtf.gz results/gene_sets/<Species.Assembly>.116.genes.tsv.gz
```

The output is deterministic: rebuilding the human table gave the same sha256.

**Checked on real data (2026-09-22):** resolving aging's human search database
(`760984e8…`, 52,359 proteins, 53,232 rows) with `tools/ResolveSearchDb` against the human table
gives output byte-identical to `results/search_db_human_e116.tsv`, which was resolved against the GTF.
