# Licensing

This repository holds two kinds of work under two licenses.

| what | license | file |
|---|---|---|
| **Code:** `src/`, `tools/`, `tests/`, and any other source code | MIT | [`LICENSE`](LICENSE) |
| **Data and documentation:** `results/`, `design/`, and the orthology snapshots published as this repository's releases (their Parquet tables and `manifest.json`) | Creative Commons Attribution 4.0 International (CC-BY-4.0) | [`LICENSE-DATA`](LICENSE-DATA) |

Copyright (c) 2026 Trish Shortreed.

## Two exceptions

- **`views.sql` inside a snapshot is not ours to relicense.** It is written by mzLib's
  `OrthologySnapshotWriter` and is part of [mzLib](https://github.com/smith-chem-wisc/mzLib), which is
  licensed under the GNU LGPL v3.0.
- **The source data is Ensembl's.** The snapshots and several tables in `results/` are derived from
  Ensembl and Ensembl Compara (https://www.ensembl.org), which place no restrictions on their data.
  CC-BY-4.0 covers what this project added: the selection, the structure, the refusal classes and
  the checks. Please cite Ensembl as well.

## How to attribute

For a snapshot, give the release tag and the tar's sha256, which identify it exactly. For example:

> Orthology snapshot `orthology-compara-116-b63a3331` (sha256 `b1d682a5…`), trishorts/logs,
> https://github.com/trishorts/logs, CC-BY-4.0; derived from Ensembl Compara release 116.

A snapshot cited in a publication will also get a Zenodo DOI, and that DOI is the one to cite.
