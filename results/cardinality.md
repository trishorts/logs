# Cross-species orthology cardinality — ensembl_compara release 116

Generated 2026-09-22. Taxa: human (9606), mouse (10090), rat (10116).

Owed to `dataRepo` as **REQ-LOGS-4** (cardinality) and **REQ-LOGS-6** (the refusal
classes). Every number here is measured from the pinned inputs recorded in
`data/PROVENANCE.md`; none is estimated.

## The finding that changes what we promised

We told `dataRepo` we would separate *"no ortholog exists"* from *"no ortholog in this
release"*. **Compara does not support that distinction** — both present as an absent
edge, and nothing in the dump says whether the source looked and declined or never had
the chance. Rather than report a class we cannot derive, the refusal is decomposed by
**how far the inference got**:

| class | meaning |
|---|---|
| `no_edge_in_shared_tree` | In a gene tree that also contains target-species genes, but no ortholog edge to any of them. The source had the opportunity and did not call one — the closest thing to *no ortholog exists*. |
| `tree_lacks_target_species` | In a tree containing no target-species gene at all. The tree is the unit of inference, so there was nothing to compare against — closest to *not in this release*. |
| `not_in_any_tree` | In the release's gene set, but in no Compara tree. **No call was ever attempted.** |
| `not_in_gene_set` | Not in this release's gene set. Zero by construction here, since we enumerate *from* the gene set; non-zero only for externally supplied gene ids — which is exactly `dataRepo`'s case. |

The decomposition is strictly more honest than the one we promised and answers the same
question: whether a cross-species row can be stated, or must refuse itself.

## Gene sets

| species | genes in release | eligible | of which protein-coding | in a Compara gene tree |
|---|---:|---:|---:|---:|
| human | 78,941 | 20,543 | 20,131 | 19,690 |
| mouse | 78,348 | 22,311 | 21,818 | 22,045 |
| rat | 43,360 | 22,548 | 22,016 | 22,379 |

**Eligible is protein-coding *plus* immunoglobulin and T-cell-receptor gene segments.**
Compara trees those too, so excluding them would drop genes the source was willing to
consider — wrong in the direction that flatters the result. Counting *all* biotypes would
be wrong the other way, treating a lncRNA that was never eligible as a failed lookup.

## Homology rows

- **1,001,934** rows with both ends in our three taxa
- **1,001,934** distinct homologies after deduplicating on `homology_id`
- **0** rows were duplicates across the three genome-specific files

### Why all three files must be read — measured, not assumed

The provider's README warns that each genome-specific file holds only *an arbitrary
subset* of that genome's orthologies. It is worse than "subset" suggests:

| species pair | orthologies found in — |
|---|---|
| human <-> mouse | `mus_musculus` **23,764** |
| human <-> rat | `homo_sapiens` **22,105** |
| mouse <-> rat | `mus_musculus` **40,027** |

**Each species pair lives entirely in one file, and not necessarily the obvious one.**
Every human↔mouse orthology is in the *mouse* dump; the human dump contains none of them.
Reading only the human file would have lost **100%** of human↔mouse and **100%** of
mouse↔rat — not a shortfall, a total miss, and one that would have looked like a
complete result. The zero duplicate count below is the other half of the same fact: the
files partition the homologies rather than overlapping, so the union is exact.

### Homology types in scope

| type | count |
|---|---:|
| `other_paralog` | 750,996 |
| `within_species_paralog` | 164,992 |
| `ortholog_one2one` | 49,567 |
| `ortholog_many2many` | 28,897 |
| `ortholog_one2many` | 7,432 |
| `gene_split` | 50 |

### Confidence

`{'high': 47567, 'low': 38329}` — `null` is **the source declining to qualify the call**,
which is not the same statement as low confidence and must not collapse into it.

## Pairwise

### human->mouse

20,543 eligible (protein-coding) source genes.

| outcome | genes | % |
|---|---:|---:|
| `has_ortholog` | 17,826 | 86.77% |
| `no_edge_in_shared_tree` | 531 | 2.58% |
| `tree_lacks_target_species` | 1,333 | 6.49% |
| `not_in_any_tree` | 853 | 4.15% |

| relationship type | genes |
|---|---:|
| `ortholog_one2one` | 16,335 |
| `ortholog_one2many` | 999 |
| `ortholog_many2many` | 492 |

Distinct partners per gene: `{'1': 16931, '2': 422, '3': 128, '4': 77, '5': 46, '6': 22, '7': 24, '8': 19, '9': 18, '10': 16, '11': 4, '12': 12, '13': 10, '14': 18, '15': 1, '16': 2, '17': 3, '18': 4, '19': 2, '21': 1, '22': 1, '23': 17, '25': 1, '26': 1, '27': 3, '28': 6, '35': 2, '54': 1, '58': 11, '87': 22, '105': 1}`

### human->rat

20,543 eligible (protein-coding) source genes.

| outcome | genes | % |
|---|---:|---:|
| `has_ortholog` | 17,519 | 85.28% |
| `no_edge_in_shared_tree` | 613 | 2.98% |
| `tree_lacks_target_species` | 1,558 | 7.58% |
| `not_in_any_tree` | 853 | 4.15% |

| relationship type | genes |
|---|---:|
| `ortholog_one2one` | 15,847 |
| `ortholog_one2many` | 1,218 |
| `ortholog_many2many` | 454 |

Distinct partners per gene: `{'1': 16424, '2': 577, '3': 188, '4': 87, '5': 49, '6': 20, '7': 23, '8': 13, '9': 8, '10': 11, '11': 5, '12': 13, '13': 23, '14': 1, '15': 3, '16': 3, '18': 14, '19': 4, '20': 1, '21': 1, '22': 1, '23': 4, '26': 5, '28': 1, '33': 2, '35': 3, '36': 1, '37': 22, '43': 11, '51': 1}`

### mouse->human

22,311 eligible (protein-coding) source genes.

| outcome | genes | % |
|---|---:|---:|
| `has_ortholog` | 18,908 | 84.75% |
| `no_edge_in_shared_tree` | 1,268 | 5.68% |
| `tree_lacks_target_species` | 1,869 | 8.38% |
| `not_in_any_tree` | 266 | 1.19% |

| relationship type | genes |
|---|---:|
| `ortholog_one2one` | 16,335 |
| `ortholog_one2many` | 1,806 |
| `ortholog_many2many` | 767 |

Distinct partners per gene: `{'1': 17932, '2': 436, '3': 147, '4': 64, '5': 29, '6': 53, '7': 6, '8': 14, '9': 25, '10': 7, '11': 58, '13': 14, '16': 23, '17': 4, '18': 1, '19': 3, '21': 4, '22': 88}`

### mouse->rat

22,311 eligible (protein-coding) source genes.

| outcome | genes | % |
|---|---:|---:|
| `has_ortholog` | 20,521 | 91.98% |
| `no_edge_in_shared_tree` | 796 | 3.57% |
| `tree_lacks_target_species` | 728 | 3.26% |
| `not_in_any_tree` | 266 | 1.19% |

| relationship type | genes |
|---|---:|
| `ortholog_one2one` | 17,385 |
| `ortholog_one2many` | 1,640 |
| `ortholog_many2many` | 1,496 |

Distinct partners per gene: `{'1': 18480, '2': 902, '3': 260, '4': 205, '5': 81, '6': 64, '7': 61, '8': 33, '9': 39, '10': 38, '11': 53, '12': 6, '14': 36, '15': 8, '16': 13, '17': 14, '18': 1, '19': 5, '20': 10, '23': 2, '26': 16, '28': 2, '41': 91, '48': 8, '57': 53, '156': 40}`

### rat->human

22,548 eligible (protein-coding) source genes.

| outcome | genes | % |
|---|---:|---:|
| `has_ortholog` | 18,874 | 83.71% |
| `no_edge_in_shared_tree` | 1,647 | 7.30% |
| `tree_lacks_target_species` | 1,858 | 8.24% |
| `not_in_any_tree` | 169 | 0.75% |

| relationship type | genes |
|---|---:|
| `ortholog_one2one` | 15,847 |
| `ortholog_one2many` | 2,355 |
| `ortholog_many2many` | 672 |

Distinct partners per gene: `{'1': 18010, '2': 418, '3': 170, '4': 59, '5': 42, '6': 33, '7': 5, '8': 3, '9': 12, '11': 43, '13': 18, '16': 13, '17': 2, '18': 3, '19': 3, '21': 2, '22': 38}`

### rat->mouse

22,548 eligible (protein-coding) source genes.

| outcome | genes | % |
|---|---:|---:|
| `has_ortholog` | 20,733 | 91.95% |
| `no_edge_in_shared_tree` | 1,188 | 5.27% |
| `tree_lacks_target_species` | 458 | 2.03% |
| `not_in_any_tree` | 169 | 0.75% |

| relationship type | genes |
|---|---:|
| `ortholog_one2one` | 17,385 |
| `ortholog_one2many` | 1,757 |
| `ortholog_many2many` | 1,591 |

Distinct partners per gene: `{'1': 18813, '2': 746, '3': 332, '4': 94, '5': 87, '6': 67, '7': 19, '8': 110, '9': 34, '10': 34, '11': 4, '12': 29, '13': 5, '14': 34, '16': 2, '17': 2, '18': 9, '22': 13, '23': 1, '24': 30, '28': 7, '29': 2, '40': 156, '53': 57, '79': 4, '91': 41, '102': 1}`

## Triples — the number that does not follow from the pairs

- human protein-coding genes: **20,543**
- one2one to **both** rodents: **15,553**
- **clean 1:1:1** (and the mouse and rat partners are also one2one with each other): **15,508** (75.49%)
- one2one to both rodents but the rodent pair is **not** one2one: **45**

That last row is the whole reason to measure triples separately: those genes look clean
from every pairwise angle and are not clean as a set. A join built on pairwise evidence
alone would treat them as interchangeable.

### Joint classes

| human → mouse | human → rat | genes |
|---|---|---:|
| `one2one` | `one2one` | 15,553 |
| `none` | `none` | 2,539 |
| `one2many` | `one2many` | 681 |
| `one2one` | `one2many` | 391 |
| `one2one` | `none` | 391 |
| `many2many` | `many2many` | 348 |
| `one2many` | `one2one` | 157 |
| `none` | `one2one` | 137 |
| `many2many` | `one2many` | 116 |
| `one2many` | `many2many` | 95 |
| `one2many` | `none` | 66 |
| `none` | `one2many` | 30 |
| `many2many` | `none` | 28 |
| `none` | `many2many` | 11 |
