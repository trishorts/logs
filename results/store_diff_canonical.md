# The store's gene resolutions against ours (PXR-O10)

Generated 2026-11-10 by `logs_orthology.store_diff`. Each `logs.resolve_genes` artefact in dataRepo's store is compared, as a multiset of rows on every column both sides have, with our `tools/ResolveSearchDb` table for the same database (entry rows), or, for a later build of the same proteome, with the earlier artefact (every column but `search_database_sha256`).

| run | artefact | database | reference | store rows | only store | only reference | same database | identical |
|---|---|---|---|---:|---:|---:|---|---|
| human-v3-mzlib1.0.593 | `75344a8616a35136` | `UP000005640_all_genecentric_2026_03_agingPTM-v3.xml` (`fd80cf8839f8`) | `results/search_db_human_canonical-v3_e116.tsv` | 21,139 | 0 | 0 | yes | **yes** |
| human-v3-mzlib1.0.595 | `e0cda413d1a4c8af` | `UP000005640_all_genecentric_2026_03_agingPTM-v3.xml` (`fd80cf8839f8`) | `75344a8616a35136` | 21,139 | 0 | 0 | yes | **yes** |
| human-v4-mzlib1.0.593 | `7f7f2b684146b23e` | `UP000005640_all_genecentric_2026_03_agingPTM-v4.xml` (`c11a9bc3d6c5`) | `75344a8616a35136` | 21,139 | 0 | 0 | no | **yes** |
| human-v4-mzlib1.0.595 | `47d9df50be4d3ca7` | `UP000005640_all_genecentric_2026_03_agingPTM-v4.xml` (`c11a9bc3d6c5`) | `75344a8616a35136` | 21,139 | 0 | 0 | no | **yes** |
| human-v6-mzlib1.0.595 | `5b01c0f81e893087` | `UP000005640_all_genecentric_2026_03_agingPTM-v6.xml` (`b87d37b574ff`) | `75344a8616a35136` | 21,139 | 0 | 0 | no | **yes** |
| human-v8-mzlib1.0.595 | `9bb4a3f829d9b9b3` | `UP000005640_all_genecentric_2026_03_agingPTM-v8.xml` (`c1a9e88f9af0`) | `75344a8616a35136` | 21,139 | 0 | 0 | no | **yes** |
| mouse-v3-mzlib1.0.593 | `d4f02774cd6fa77f` | `UP000000589_all_genecentric_2026_03_agingPTM-v3.xml` (`3c4ac3fb481e`) | `results/search_db_mouse_canonical-v3_e116.tsv` | 22,383 | 0 | 0 | yes | **yes** |
| mouse-v3-mzlib1.0.595 | `c7af1b4d1e83c061` | `UP000000589_all_genecentric_2026_03_agingPTM-v3.xml` (`3c4ac3fb481e`) | `d4f02774cd6fa77f` | 22,383 | 0 | 0 | yes | **yes** |
| mouse-v4-mzlib1.0.593 | `d1ea170e2d0a0bb4` | `UP000000589_all_genecentric_2026_03_agingPTM-v4.xml` (`f9cdd188fd7f`) | `d4f02774cd6fa77f` | 22,383 | 0 | 0 | no | **yes** |
| mouse-v4-mzlib1.0.595 | `b37e102402514d33` | `UP000000589_all_genecentric_2026_03_agingPTM-v4.xml` (`f9cdd188fd7f`) | `d4f02774cd6fa77f` | 22,383 | 0 | 0 | no | **yes** |
| mouse-v5-mzlib1.0.593 | `599c784722448a08` | `UP000000589_all_genecentric_2026_03_agingPTM-v5.xml` (`e4e510a553a2`) | `d4f02774cd6fa77f` | 22,383 | 0 | 0 | no | **yes** |
| mouse-v5-mzlib1.0.595 | `aa212cd1f4b94e27` | `UP000000589_all_genecentric_2026_03_agingPTM-v5.xml` (`e4e510a553a2`) | `d4f02774cd6fa77f` | 22,383 | 0 | 0 | no | **yes** |
| mouse-v6-mzlib1.0.595 | `34a6a17d4cd77e4d` | `UP000000589_all_genecentric_2026_03_agingPTM-v6.xml` (`db47863bb689`) | `d4f02774cd6fa77f` | 22,383 | 0 | 0 | no | **yes** |
| mouse-v7-mzlib1.0.595 | `70e547e92fc7729f` | `UP000000589_all_genecentric_2026_03_agingPTM-v7.xml` (`23470872c8b2`) | `d4f02774cd6fa77f` | 22,383 | 0 | 0 | no | **yes** |
| mouse-v8-mzlib1.0.595 | `45b3ce0c75057c5e` | `UP000000589_all_genecentric_2026_03_agingPTM-v8.xml` (`a57e0e81e057`) | `d4f02774cd6fa77f` | 22,383 | 0 | 0 | no | **yes** |
| rat-v3-mzlib1.0.593 | `ffadfcf207ba3037` | `UP000002494_all_genecentric_2026_03_agingPTM-v3.xml` (`7f08fd3c9eac`) | `results/search_db_rat_canonical-v3_e116.tsv` | 22,464 | 0 | 0 | yes | **yes** |
| rat-v3-mzlib1.0.595 | `1a850d2e796bbb07` | `UP000002494_all_genecentric_2026_03_agingPTM-v3.xml` (`7f08fd3c9eac`) | `ffadfcf207ba3037` | 22,464 | 0 | 0 | yes | **yes** |
| rat-v4-mzlib1.0.593 | `b69ca7d3fafc27d7` | `UP000002494_all_genecentric_2026_03_agingPTM-v4.xml` (`0f606b275fc6`) | `ffadfcf207ba3037` | 22,464 | 0 | 0 | no | **yes** |
| rat-v4-mzlib1.0.595 | `ccbcc0c1e724ddba` | `UP000002494_all_genecentric_2026_03_agingPTM-v4.xml` (`0f606b275fc6`) | `ffadfcf207ba3037` | 22,464 | 0 | 0 | no | **yes** |
| rat-v6-mzlib1.0.595 | `903bc694bc8448de` | `UP000002494_all_genecentric_2026_03_agingPTM-v6.xml` (`9bbfd9ed282f`) | `ffadfcf207ba3037` | 22,464 | 0 | 0 | no | **yes** |
| rat-v8-mzlib1.0.595 | `40176de704370439` | `UP000002494_all_genecentric_2026_03_agingPTM-v8.xml` (`b79e85c2e620`) | `ffadfcf207ba3037` | 22,464 | 0 | 0 | no | **yes** |

## Provenance checks

| run | mzLib | definition | row values = manifest | rows' db = run.json | file hashes to it | summary = rows | checked against current manifest |
|---|---|---|---|---|---|---|---|
| human-v3-mzlib1.0.593 | 1.0.593 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| human-v3-mzlib1.0.595 | 1.0.595 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| human-v4-mzlib1.0.593 | 1.0.593 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| human-v4-mzlib1.0.595 | 1.0.595 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| human-v6-mzlib1.0.595 | 1.0.595 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| human-v8-mzlib1.0.595 | 1.0.595 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| mouse-v3-mzlib1.0.593 | 1.0.593 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| mouse-v3-mzlib1.0.595 | 1.0.595 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| mouse-v4-mzlib1.0.593 | 1.0.593 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| mouse-v4-mzlib1.0.595 | 1.0.595 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| mouse-v5-mzlib1.0.593 | 1.0.593 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| mouse-v5-mzlib1.0.595 | 1.0.595 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| mouse-v6-mzlib1.0.595 | 1.0.595 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| mouse-v7-mzlib1.0.595 | 1.0.595 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| mouse-v8-mzlib1.0.595 | 1.0.595 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| rat-v3-mzlib1.0.593 | 1.0.593 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| rat-v3-mzlib1.0.595 | 1.0.595 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| rat-v4-mzlib1.0.593 | 1.0.593 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| rat-v4-mzlib1.0.595 | 1.0.595 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| rat-v6-mzlib1.0.595 | 1.0.595 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| rat-v8-mzlib1.0.595 | 1.0.595 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

## Outcomes by entry (the search XML's view)

| run | entries | resolved | multi_gene | off_primary_only | not_in_source |
|---|---:|---:|---:|---:|---:|
| human-v3-mzlib1.0.593 | 20,652 | 19,174 | 352 | 162 | 964 |
| human-v3-mzlib1.0.595 | 20,652 | 19,174 | 352 | 162 | 964 |
| human-v4-mzlib1.0.593 | 20,652 | 19,174 | 352 | 162 | 964 |
| human-v4-mzlib1.0.595 | 20,652 | 19,174 | 352 | 162 | 964 |
| human-v6-mzlib1.0.595 | 20,652 | 19,174 | 352 | 162 | 964 |
| human-v8-mzlib1.0.595 | 20,652 | 19,174 | 352 | 162 | 964 |
| mouse-v3-mzlib1.0.593 | 21,860 | 19,942 | 273 | 0 | 1,645 |
| mouse-v3-mzlib1.0.595 | 21,860 | 19,942 | 273 | 0 | 1,645 |
| mouse-v4-mzlib1.0.593 | 21,860 | 19,942 | 273 | 0 | 1,645 |
| mouse-v4-mzlib1.0.595 | 21,860 | 19,942 | 273 | 0 | 1,645 |
| mouse-v5-mzlib1.0.593 | 21,860 | 19,942 | 273 | 0 | 1,645 |
| mouse-v5-mzlib1.0.595 | 21,860 | 19,942 | 273 | 0 | 1,645 |
| mouse-v6-mzlib1.0.595 | 21,860 | 19,942 | 273 | 0 | 1,645 |
| mouse-v7-mzlib1.0.595 | 21,860 | 19,942 | 273 | 0 | 1,645 |
| mouse-v8-mzlib1.0.595 | 21,860 | 19,942 | 273 | 0 | 1,645 |
| rat-v3-mzlib1.0.593 | 21,471 | 17,321 | 153 | 955 | 3,042 |
| rat-v3-mzlib1.0.595 | 21,471 | 17,321 | 153 | 955 | 3,042 |
| rat-v4-mzlib1.0.593 | 21,471 | 17,321 | 153 | 955 | 3,042 |
| rat-v4-mzlib1.0.595 | 21,471 | 17,321 | 153 | 955 | 3,042 |
| rat-v6-mzlib1.0.595 | 21,471 | 17,321 | 153 | 955 | 3,042 |
| rat-v8-mzlib1.0.595 | 21,471 | 17,321 | 153 | 955 | 3,042 |
