# dataRepo's v2 gene resolutions against our own mzLib 1.0.598 run (same files)

Generated 2026-11-19 by `logs_orthology.store_diff`. Each `logs.resolve_genes` artefact in dataRepo's store is compared, as a multiset of rows on every column both sides have, with our `tools/ResolveSearchDb` table for the same database (entry rows), or, for a later build of the same proteome, with the earlier artefact (every column but `search_database_sha256`).

| run | artefact | database | reference | store rows | only store | only reference | same database | identical |
|---|---|---|---|---:|---:|---:|---|---|
| mouse-UP000000589_all_genecentric_2026_03_agingPTM-v8 | `019f43a553cd1843` | `UP000000589_all_genecentric_2026_03_agingPTM-v8.xml` (`a57e0e81e057`) | `019f43a553cd1843.tsv` | 22,383 | 0 | 0 | yes | **yes** |
| rat-aging_isoforms_peroxisome_rat | `0243c0db137890d0` | `aging_isoforms_peroxisome_rat.xml` (`860896cb56cb`) | `0243c0db137890d0.tsv` | 1 | 0 | 0 | yes | **yes** |
| rat-UP000002494_all_genecentric_2026_03_agingPTM-v4 | `0af7d9ff9cf9cbef` | `UP000002494_all_genecentric_2026_03_agingPTM-v4.xml` (`0f606b275fc6`) | `0af7d9ff9cf9cbef.tsv` | 22,464 | 0 | 0 | yes | **yes** |
| human-aging_isoforms_tier1-2_human_agingPTM-v1 | `13048465ff835ae8` | `aging_isoforms_tier1-2_human_agingPTM-v1.xml` (`2a0de7bc4e47`) | `13048465ff835ae8.tsv` | 53 | 0 | 0 | yes | **yes** |
| human-UP000005640_all_genecentric_2026_03_agingPTM-v8 | `1b2ee314f677fe99` | `UP000005640_all_genecentric_2026_03_agingPTM-v8.xml` (`c1a9e88f9af0`) | `1b2ee314f677fe99.tsv` | 21,139 | 0 | 0 | yes | **yes** |
| human-aging_isoforms_tier3_compartment_human_agingPTM-v4 | `1e472a92ecba503a` | `aging_isoforms_tier3_compartment_human_agingPTM-v4.xml` (`30b8d7ca54df`) | `1e472a92ecba503a.tsv` | 35 | 0 | 0 | yes | **yes** |
| rat-UP000002494_all_genecentric_2026_03_agingPTM-v8 | `20c3aebf3812befd` | `UP000002494_all_genecentric_2026_03_agingPTM-v8.xml` (`b79e85c2e620`) | `20c3aebf3812befd.tsv` | 22,464 | 0 | 0 | yes | **yes** |
| rat-aging_isoforms_rat_agingPTM-v7 | `23e1bf9c09befc9e` | `aging_isoforms_rat_agingPTM-v7.xml` (`bd6880566fa4`) | `23e1bf9c09befc9e.tsv` | 43 | 0 | 0 | yes | **yes** |
| mouse-aging_isoforms_mouse | `24d2e5d5088b4958` | `aging_isoforms_mouse.xml` (`4d3ac6446e3a`) | `24d2e5d5088b4958.tsv` | 72 | 0 | 0 | yes | **yes** |
| human-UP000005640_all_genecentric_2026_03_agingPTM-v3 | `368bb52ad817eee8` | `UP000005640_all_genecentric_2026_03_agingPTM-v3.xml` (`fd80cf8839f8`) | `368bb52ad817eee8.tsv` | 21,139 | 0 | 0 | yes | **yes** |
| mouse-aging_isoforms_mouse_agingPTM-v7 | `393df3091d621178` | `aging_isoforms_mouse_agingPTM-v7.xml` (`f36fa7cfddbd`) | `393df3091d621178.tsv` | 72 | 0 | 0 | yes | **yes** |
| mouse-aging_isoforms_tier3_compartment_mouse | `421d05d396b4c972` | `aging_isoforms_tier3_compartment_mouse.xml` (`be08bf25b790`) | `421d05d396b4c972.tsv` | 17 | 0 | 0 | yes | **yes** |
| human-UP000005640_all_genecentric_2026_03_agingPTM-v6 | `42659048f199d9ab` | `UP000005640_all_genecentric_2026_03_agingPTM-v6.xml` (`b87d37b574ff`) | `42659048f199d9ab.tsv` | 21,139 | 0 | 0 | yes | **yes** |
| human-aging_isoforms_human_agingPTM-v6 | `519416a532202b3f` | `aging_isoforms_human_agingPTM-v6.xml` (`d1e037ca887b`) | `519416a532202b3f.tsv` | 116 | 0 | 0 | yes | **yes** |
| mouse-UP000000589_all_genecentric_2026_03_agingPTM-v7 | `523e69f5d4388735` | `UP000000589_all_genecentric_2026_03_agingPTM-v7.xml` (`23470872c8b2`) | `523e69f5d4388735.tsv` | 22,383 | 0 | 0 | yes | **yes** |
| rat-aging_isoforms_tier3_compartment_rat | `52f03bb38dd213be` | `aging_isoforms_tier3_compartment_rat.xml` (`bce8d883fb6f`) | `52f03bb38dd213be.tsv` | 12 | 0 | 0 | yes | **yes** |
| human-aging_isoforms_tier1-2_human_agingPTM-v4 | `593e5851cf081b19` | `aging_isoforms_tier1-2_human_agingPTM-v4.xml` (`94736cd8077f`) | `593e5851cf081b19.tsv` | 53 | 0 | 0 | yes | **yes** |
| human-uniprotkb_proteome_UP000005640_AND_revi_2026_09_18_agingPTM-v1 | `5fc9bdba38f07094` | `uniprotkb_proteome_UP000005640_AND_revi_2026_09_18_agingPTM-v1.xml` (`eaefbb7e6914`) | `5fc9bdba38f07094.tsv` | 20,899 | 0 | 0 | yes | **yes** |
| mouse-aging_isoforms_tier1-2_mouse_agingPTM-v1 | `6dfc7dea2c4e4ff7` | `aging_isoforms_tier1-2_mouse_agingPTM-v1.xml` (`d1f6be915b69`) | `6dfc7dea2c4e4ff7.tsv` | 22 | 0 | 0 | yes | **yes** |
| mouse-UP000000589_all_genecentric_2026_03_agingPTM-v4 | `6f0de085cef695ea` | `UP000000589_all_genecentric_2026_03_agingPTM-v4.xml` (`f9cdd188fd7f`) | `6f0de085cef695ea.tsv` | 22,383 | 0 | 0 | yes | **yes** |
| mouse-aging_isoforms_peroxisome_mouse | `7017678f987260c5` | `aging_isoforms_peroxisome_mouse.xml` (`5332711b2e3e`) | `7017678f987260c5.tsv` | 1 | 0 | 0 | yes | **yes** |
| human-aging_isoforms_human | `72edc8cbdfad3be0` | `aging_isoforms_human.xml` (`6fdf086563aa`) | `72edc8cbdfad3be0.tsv` | 116 | 0 | 0 | yes | **yes** |
| mouse-aging_isoforms_mouse_agingPTM-v6 | `7471a3ceee8aa722` | `aging_isoforms_mouse_agingPTM-v6.xml` (`6709e22a3c05`) | `7471a3ceee8aa722.tsv` | 72 | 0 | 0 | yes | **yes** |
| mouse-uniprotkb_proteome_UP000000589_AND_revi_2026-09-22_agingPTM-v1 | `77b8ed07a1336c35` | `uniprotkb_proteome_UP000000589_AND_revi_2026-09-22_agingPTM-v1.xml` (`26ea83c286fa`) | `77b8ed07a1336c35.tsv` | 17,556 | 0 | 0 | yes | **yes** |
| mouse-UP000000589_all_genecentric_2026_03_agingPTM-v5 | `7d0c3a9acf0c857e` | `UP000000589_all_genecentric_2026_03_agingPTM-v5.xml` (`e4e510a553a2`) | `7d0c3a9acf0c857e.tsv` | 22,383 | 0 | 0 | yes | **yes** |
| mouse-UP000000589_all_genecentric_2026_03_agingPTM-v3 | `8a080b380401f5cc` | `UP000000589_all_genecentric_2026_03_agingPTM-v3.xml` (`3c4ac3fb481e`) | `8a080b380401f5cc.tsv` | 22,383 | 0 | 0 | yes | **yes** |
| mouse-aging_isoforms_mouse_agingPTM-v5 | `911838b0acf587e5` | `aging_isoforms_mouse_agingPTM-v5.xml` (`1de3b3f91247`) | `911838b0acf587e5.tsv` | 72 | 0 | 0 | yes | **yes** |
| human-UP000005640_all_genecentric_2026_03_agingPTM-v4 | `91758cc68ef966ea` | `UP000005640_all_genecentric_2026_03_agingPTM-v4.xml` (`c11a9bc3d6c5`) | `91758cc68ef966ea.tsv` | 21,139 | 0 | 0 | yes | **yes** |
| human-aging_isoforms_human_agingPTM-v7 | `921cea527c7512b9` | `aging_isoforms_human_agingPTM-v7.xml` (`934ab32f6fbc`) | `921cea527c7512b9.tsv` | 116 | 0 | 0 | yes | **yes** |
| mouse-UP000000589_all_genecentric_2026_03_agingPTM-v6 | `a2f92189a6122b88` | `UP000000589_all_genecentric_2026_03_agingPTM-v6.xml` (`db47863bb689`) | `a2f92189a6122b88.tsv` | 22,383 | 0 | 0 | yes | **yes** |
| human-uniprotkb_proteome_UP000005640_AND_revi_2026_09_18 | `b310d4b6da85561c` | `uniprotkb_proteome_UP000005640_AND_revi_2026_09_18.xml` (`760984e8d402`) | `b310d4b6da85561c.tsv` | 20,899 | 0 | 0 | yes | **yes** |
| mouse-aging_isoforms_tier3_compartment_mouse_agingPTM-v4 | `c1a1a3cbb277339b` | `aging_isoforms_tier3_compartment_mouse_agingPTM-v4.xml` (`013802ee85a6`) | `c1a1a3cbb277339b.tsv` | 17 | 0 | 0 | yes | **yes** |
| rat-UP000002494_all_genecentric_2026_03_agingPTM-v3 | `d0dbb1a8f7d7d42f` | `UP000002494_all_genecentric_2026_03_agingPTM-v3.xml` (`7f08fd3c9eac`) | `d0dbb1a8f7d7d42f.tsv` | 22,464 | 0 | 0 | yes | **yes** |
| mouse-aging_isoforms_tier1-2_mouse_agingPTM-v3 | `dd663145147cc5f4` | `aging_isoforms_tier1-2_mouse_agingPTM-v3.xml` (`25e3737826af`) | `dd663145147cc5f4.tsv` | 22 | 0 | 0 | yes | **yes** |
| human-aging_isoforms_tier1-2_human_agingPTM-v3 | `dfb8069801112a5c` | `aging_isoforms_tier1-2_human_agingPTM-v3.xml` (`e887b4d5fa27`) | `dfb8069801112a5c.tsv` | 53 | 0 | 0 | yes | **yes** |
| mouse-aging_isoforms_tier1-2_mouse_agingPTM-v4 | `e82b35a62c763309` | `aging_isoforms_tier1-2_mouse_agingPTM-v4.xml` (`e617fa376f74`) | `e82b35a62c763309.tsv` | 22 | 0 | 0 | yes | **yes** |
| human-aging_isoforms_tier3_compartment_human | `eb3208d8c2c35269` | `aging_isoforms_tier3_compartment_human.xml` (`4d3d1c9bba00`) | `eb3208d8c2c35269.tsv` | 35 | 0 | 0 | yes | **yes** |
| rat-aging_isoforms_tier1-2_rat_agingPTM-v4 | `f0dafaa7b77172c8` | `aging_isoforms_tier1-2_rat_agingPTM-v4.xml` (`5e204e6770ca`) | `f0dafaa7b77172c8.tsv` | 17 | 0 | 0 | yes | **yes** |
| rat-aging_isoforms_rat | `f54e13e66ecb9e06` | `aging_isoforms_rat.xml` (`ea4a2360e651`) | `f54e13e66ecb9e06.tsv` | 43 | 0 | 0 | yes | **yes** |
| rat-aging_isoforms_tier1-2_rat_agingPTM-v3 | `f70a1ced5dabb901` | `aging_isoforms_tier1-2_rat_agingPTM-v3.xml` (`57be2589cd3e`) | `f70a1ced5dabb901.tsv` | 17 | 0 | 0 | yes | **yes** |
| human-aging_isoforms_peroxisome_human | `fabfc60811774908` | `aging_isoforms_peroxisome_human.xml` (`31804be05b1a`) | `fabfc60811774908.tsv` | 1 | 0 | 0 | yes | **yes** |

## Provenance checks

| run | mzLib | definition | row values = manifest | rows' db = run.json | file hashes to it | summary = rows | checked against current manifest |
|---|---|---|---|---|---|---|---|
| mouse-UP000000589_all_genecentric_2026_03_agingPTM-v8 | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| rat-aging_isoforms_peroxisome_rat | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| rat-UP000002494_all_genecentric_2026_03_agingPTM-v4 | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| human-aging_isoforms_tier1-2_human_agingPTM-v1 | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| human-UP000005640_all_genecentric_2026_03_agingPTM-v8 | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| human-aging_isoforms_tier3_compartment_human_agingPTM-v4 | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| rat-UP000002494_all_genecentric_2026_03_agingPTM-v8 | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| rat-aging_isoforms_rat_agingPTM-v7 | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| mouse-aging_isoforms_mouse | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| human-UP000005640_all_genecentric_2026_03_agingPTM-v3 | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| mouse-aging_isoforms_mouse_agingPTM-v7 | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| mouse-aging_isoforms_tier3_compartment_mouse | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| human-UP000005640_all_genecentric_2026_03_agingPTM-v6 | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| human-aging_isoforms_human_agingPTM-v6 | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| mouse-UP000000589_all_genecentric_2026_03_agingPTM-v7 | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| rat-aging_isoforms_tier3_compartment_rat | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| human-aging_isoforms_tier1-2_human_agingPTM-v4 | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| human-uniprotkb_proteome_UP000005640_AND_revi_2026_09_18_agingPTM-v1 | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| mouse-aging_isoforms_tier1-2_mouse_agingPTM-v1 | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| mouse-UP000000589_all_genecentric_2026_03_agingPTM-v4 | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| mouse-aging_isoforms_peroxisome_mouse | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| human-aging_isoforms_human | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| mouse-aging_isoforms_mouse_agingPTM-v6 | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| mouse-uniprotkb_proteome_UP000000589_AND_revi_2026-09-22_agingPTM-v1 | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| mouse-UP000000589_all_genecentric_2026_03_agingPTM-v5 | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| mouse-UP000000589_all_genecentric_2026_03_agingPTM-v3 | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| mouse-aging_isoforms_mouse_agingPTM-v5 | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| human-UP000005640_all_genecentric_2026_03_agingPTM-v4 | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| human-aging_isoforms_human_agingPTM-v7 | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| mouse-UP000000589_all_genecentric_2026_03_agingPTM-v6 | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| human-uniprotkb_proteome_UP000005640_AND_revi_2026_09_18 | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| mouse-aging_isoforms_tier3_compartment_mouse_agingPTM-v4 | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| rat-UP000002494_all_genecentric_2026_03_agingPTM-v3 | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| mouse-aging_isoforms_tier1-2_mouse_agingPTM-v3 | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| human-aging_isoforms_tier1-2_human_agingPTM-v3 | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| mouse-aging_isoforms_tier1-2_mouse_agingPTM-v4 | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| human-aging_isoforms_tier3_compartment_human | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| rat-aging_isoforms_tier1-2_rat_agingPTM-v4 | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| rat-aging_isoforms_rat | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| rat-aging_isoforms_tier1-2_rat_agingPTM-v3 | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| human-aging_isoforms_peroxisome_human | 1.0.598 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

## Outcomes by entry (the search XML's view)

| run | entries | resolved | multi_gene | off_primary_only | not_in_source |
|---|---:|---:|---:|---:|---:|
| mouse-UP000000589_all_genecentric_2026_03_agingPTM-v8 | 21,860 | 19,942 | 273 | 0 | 1,645 |
| rat-aging_isoforms_peroxisome_rat | 1 | 1 | 0 | 0 | 0 |
| rat-UP000002494_all_genecentric_2026_03_agingPTM-v4 | 21,471 | 17,321 | 153 | 955 | 3,042 |
| human-aging_isoforms_tier1-2_human_agingPTM-v1 | 49 | 45 | 0 | 0 | 4 |
| human-UP000005640_all_genecentric_2026_03_agingPTM-v8 | 20,652 | 19,174 | 352 | 162 | 964 |
| human-aging_isoforms_tier3_compartment_human_agingPTM-v4 | 28 | 21 | 0 | 0 | 7 |
| rat-UP000002494_all_genecentric_2026_03_agingPTM-v8 | 21,471 | 17,321 | 153 | 955 | 3,042 |
| rat-aging_isoforms_rat_agingPTM-v7 | 34 | 12 | 0 | 0 | 22 |
| mouse-aging_isoforms_mouse | 56 | 39 | 0 | 0 | 17 |
| human-UP000005640_all_genecentric_2026_03_agingPTM-v3 | 20,652 | 19,174 | 352 | 162 | 964 |
| mouse-aging_isoforms_mouse_agingPTM-v7 | 56 | 39 | 0 | 0 | 17 |
| mouse-aging_isoforms_tier3_compartment_mouse | 11 | 5 | 0 | 0 | 6 |
| human-UP000005640_all_genecentric_2026_03_agingPTM-v6 | 20,652 | 19,174 | 352 | 162 | 964 |
| human-aging_isoforms_human_agingPTM-v6 | 104 | 92 | 0 | 0 | 12 |
| mouse-UP000000589_all_genecentric_2026_03_agingPTM-v7 | 21,860 | 19,942 | 273 | 0 | 1,645 |
| rat-aging_isoforms_tier3_compartment_rat | 8 | 2 | 0 | 0 | 6 |
| human-aging_isoforms_tier1-2_human_agingPTM-v4 | 49 | 45 | 0 | 0 | 4 |
| human-uniprotkb_proteome_UP000005640_AND_revi_2026_09_18_agingPTM-v1 | 20,416 | 18,988 | 350 | 62 | 1,016 |
| mouse-aging_isoforms_tier1-2_mouse_agingPTM-v1 | 18 | 13 | 0 | 0 | 5 |
| mouse-UP000000589_all_genecentric_2026_03_agingPTM-v4 | 21,860 | 19,942 | 273 | 0 | 1,645 |
| mouse-aging_isoforms_peroxisome_mouse | 1 | 1 | 0 | 0 | 0 |
| human-aging_isoforms_human | 104 | 92 | 0 | 0 | 12 |
| mouse-aging_isoforms_mouse_agingPTM-v6 | 56 | 39 | 0 | 0 | 17 |
| mouse-uniprotkb_proteome_UP000000589_AND_revi_2026-09-22_agingPTM-v1 | 17,277 | 15,474 | 124 | 0 | 1,679 |
| mouse-UP000000589_all_genecentric_2026_03_agingPTM-v5 | 21,860 | 19,942 | 273 | 0 | 1,645 |
| mouse-UP000000589_all_genecentric_2026_03_agingPTM-v3 | 21,860 | 19,942 | 273 | 0 | 1,645 |
| mouse-aging_isoforms_mouse_agingPTM-v5 | 56 | 39 | 0 | 0 | 17 |
| human-UP000005640_all_genecentric_2026_03_agingPTM-v4 | 20,652 | 19,174 | 352 | 162 | 964 |
| human-aging_isoforms_human_agingPTM-v7 | 104 | 92 | 0 | 0 | 12 |
| mouse-UP000000589_all_genecentric_2026_03_agingPTM-v6 | 21,860 | 19,942 | 273 | 0 | 1,645 |
| human-uniprotkb_proteome_UP000005640_AND_revi_2026_09_18 | 20,416 | 18,988 | 350 | 62 | 1,016 |
| mouse-aging_isoforms_tier3_compartment_mouse_agingPTM-v4 | 11 | 5 | 0 | 0 | 6 |
| rat-UP000002494_all_genecentric_2026_03_agingPTM-v3 | 21,471 | 17,321 | 153 | 955 | 3,042 |
| mouse-aging_isoforms_tier1-2_mouse_agingPTM-v3 | 18 | 13 | 0 | 0 | 5 |
| human-aging_isoforms_tier1-2_human_agingPTM-v3 | 49 | 45 | 0 | 0 | 4 |
| mouse-aging_isoforms_tier1-2_mouse_agingPTM-v4 | 18 | 13 | 0 | 0 | 5 |
| human-aging_isoforms_tier3_compartment_human | 28 | 21 | 0 | 0 | 7 |
| rat-aging_isoforms_tier1-2_rat_agingPTM-v4 | 15 | 3 | 0 | 0 | 12 |
| rat-aging_isoforms_rat | 34 | 12 | 0 | 0 | 22 |
| rat-aging_isoforms_tier1-2_rat_agingPTM-v3 | 15 | 3 | 0 | 0 | 12 |
| human-aging_isoforms_peroxisome_human | 1 | 1 | 0 | 0 | 0 |

## `ensembl_xref_agreement` (rows)

| run | agrees | silent | disagrees | null | pairs with `ensembl_xref_agrees` |
|---|---:|---:|---:|---:|---|
| mouse-UP000000589_all_genecentric_2026_03_agingPTM-v8 | 19,553 | 1,183 | 2 | 1,645 | ✓ |
| rat-aging_isoforms_peroxisome_rat | 1 | 0 | 0 | 0 | ✓ |
| rat-UP000002494_all_genecentric_2026_03_agingPTM-v4 | 14,819 | 3,581 | 67 | 3,997 | ✓ |
| human-aging_isoforms_tier1-2_human_agingPTM-v1 | 49 | 0 | 0 | 4 | ✓ |
| human-UP000005640_all_genecentric_2026_03_agingPTM-v8 | 19,627 | 27 | 359 | 1,126 | ✓ |
| human-aging_isoforms_tier3_compartment_human_agingPTM-v4 | 27 | 0 | 1 | 7 | ✓ |
| rat-UP000002494_all_genecentric_2026_03_agingPTM-v8 | 14,819 | 3,581 | 67 | 3,997 | ✓ |
| rat-aging_isoforms_rat_agingPTM-v7 | 20 | 1 | 0 | 22 | ✓ |
| mouse-aging_isoforms_mouse | 51 | 4 | 0 | 17 | ✓ |
| human-UP000005640_all_genecentric_2026_03_agingPTM-v3 | 19,627 | 27 | 359 | 1,126 | ✓ |
| mouse-aging_isoforms_mouse_agingPTM-v7 | 51 | 4 | 0 | 17 | ✓ |
| mouse-aging_isoforms_tier3_compartment_mouse | 11 | 0 | 0 | 6 | ✓ |
| human-UP000005640_all_genecentric_2026_03_agingPTM-v6 | 19,627 | 27 | 359 | 1,126 | ✓ |
| human-aging_isoforms_human_agingPTM-v6 | 102 | 1 | 1 | 12 | ✓ |
| mouse-UP000000589_all_genecentric_2026_03_agingPTM-v7 | 19,553 | 1,183 | 2 | 1,645 | ✓ |
| rat-aging_isoforms_tier3_compartment_rat | 6 | 0 | 0 | 6 | ✓ |
| human-aging_isoforms_tier1-2_human_agingPTM-v4 | 49 | 0 | 0 | 4 | ✓ |
| human-uniprotkb_proteome_UP000005640_AND_revi_2026_09_18_agingPTM-v1 | 19,446 | 16 | 359 | 1,078 | ✓ |
| mouse-aging_isoforms_tier1-2_mouse_agingPTM-v1 | 17 | 0 | 0 | 5 | ✓ |
| mouse-UP000000589_all_genecentric_2026_03_agingPTM-v4 | 19,553 | 1,183 | 2 | 1,645 | ✓ |
| mouse-aging_isoforms_peroxisome_mouse | 1 | 0 | 0 | 0 | ✓ |
| human-aging_isoforms_human | 102 | 1 | 1 | 12 | ✓ |
| mouse-aging_isoforms_mouse_agingPTM-v6 | 51 | 4 | 0 | 17 | ✓ |
| mouse-uniprotkb_proteome_UP000000589_AND_revi_2026-09-22_agingPTM-v1 | 15,855 | 20 | 2 | 1,679 | ✓ |
| mouse-UP000000589_all_genecentric_2026_03_agingPTM-v5 | 19,553 | 1,183 | 2 | 1,645 | ✓ |
| mouse-UP000000589_all_genecentric_2026_03_agingPTM-v3 | 19,553 | 1,183 | 2 | 1,645 | ✓ |
| mouse-aging_isoforms_mouse_agingPTM-v5 | 51 | 4 | 0 | 17 | ✓ |
| human-UP000005640_all_genecentric_2026_03_agingPTM-v4 | 19,627 | 27 | 359 | 1,126 | ✓ |
| human-aging_isoforms_human_agingPTM-v7 | 102 | 1 | 1 | 12 | ✓ |
| mouse-UP000000589_all_genecentric_2026_03_agingPTM-v6 | 19,553 | 1,183 | 2 | 1,645 | ✓ |
| human-uniprotkb_proteome_UP000005640_AND_revi_2026_09_18 | 19,446 | 16 | 359 | 1,078 | ✓ |
| mouse-aging_isoforms_tier3_compartment_mouse_agingPTM-v4 | 11 | 0 | 0 | 6 | ✓ |
| rat-UP000002494_all_genecentric_2026_03_agingPTM-v3 | 14,819 | 3,581 | 67 | 3,997 | ✓ |
| mouse-aging_isoforms_tier1-2_mouse_agingPTM-v3 | 17 | 0 | 0 | 5 | ✓ |
| human-aging_isoforms_tier1-2_human_agingPTM-v3 | 49 | 0 | 0 | 4 | ✓ |
| mouse-aging_isoforms_tier1-2_mouse_agingPTM-v4 | 17 | 0 | 0 | 5 | ✓ |
| human-aging_isoforms_tier3_compartment_human | 27 | 0 | 1 | 7 | ✓ |
| rat-aging_isoforms_tier1-2_rat_agingPTM-v4 | 5 | 0 | 0 | 12 | ✓ |
| rat-aging_isoforms_rat | 20 | 1 | 0 | 22 | ✓ |
| rat-aging_isoforms_tier1-2_rat_agingPTM-v3 | 5 | 0 | 0 | 12 | ✓ |
| human-aging_isoforms_peroxisome_human | 1 | 0 | 0 | 0 | ✓ |
