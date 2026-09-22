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

| species | genes in release | protein-coding | in a Compara gene tree |
|---|---:|---:|---:|
| human | 78,941 | 20,131 | 19,690 |
| mouse | 78,348 | 21,818 | 22,045 |
| rat | 43,360 | 22,016 | 22,379 |

Protein-coding is the eligible set: Compara's `protein_default` collection is built from
protein-coding genes, so counting other biotypes as *no ortholog found* would inflate the
refusal classes with genes that were never considered.

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

20,131 eligible (protein-coding) source genes.

| outcome | genes | % |
|---|---:|---:|
| `has_ortholog` | 17,691 | 87.88% |
| `no_edge_in_shared_tree` | 448 | 2.23% |
| `tree_lacks_target_species` | 1,272 | 6.32% |
| `not_in_any_tree` | 720 | 3.58% |

| relationship type | genes |
|---|---:|
| `ortholog_one2one` | 16,314 |
| `ortholog_one2many` | 931 |
| `ortholog_many2many` | 446 |

Distinct partners per gene: `{'1': 16855, '2': 416, '3': 122, '4': 70, '5': 42, '6': 21, '7': 22, '8': 19, '9': 10, '10': 14, '11': 4, '12': 4, '13': 10, '14': 15, '15': 1, '16': 2, '17': 3, '18': 4, '19': 2, '22': 1, '23': 17, '25': 1, '26': 1, '27': 3, '28': 6, '35': 2, '54': 1, '87': 22, '105': 1}`

### human->rat

20,131 eligible (protein-coding) source genes.

| outcome | genes | % |
|---|---:|---:|
| `has_ortholog` | 17,390 | 86.38% |
| `no_edge_in_shared_tree` | 529 | 2.63% |
| `tree_lacks_target_species` | 1,492 | 7.41% |
| `not_in_any_tree` | 720 | 3.58% |

| relationship type | genes |
|---|---:|
| `ortholog_one2one` | 15,832 |
| `ortholog_one2many` | 1,183 |
| `ortholog_many2many` | 375 |

Distinct partners per gene: `{'1': 16389, '2': 563, '3': 167, '4': 80, '5': 39, '6': 19, '7': 19, '8': 13, '9': 8, '10': 9, '11': 5, '12': 8, '13': 23, '15': 2, '16': 2, '18': 14, '19': 1, '21': 1, '22': 1, '23': 3, '28': 1, '36': 1, '37': 22}`

### mouse->human

21,818 eligible (protein-coding) source genes.

| outcome | genes | % |
|---|---:|---:|
| `has_ortholog` | 18,646 | 85.46% |
| `no_edge_in_shared_tree` | 1,227 | 5.62% |
| `tree_lacks_target_species` | 1,687 | 7.73% |
| `not_in_any_tree` | 258 | 1.18% |

| relationship type | genes |
|---|---:|
| `ortholog_one2one` | 16,314 |
| `ortholog_one2many` | 1,708 |
| `ortholog_many2many` | 624 |

Distinct partners per gene: `{'1': 17825, '2': 391, '3': 124, '4': 64, '5': 8, '6': 47, '7': 6, '8': 14, '9': 24, '10': 7, '13': 14, '16': 23, '17': 4, '19': 3, '21': 4, '22': 88}`

### mouse->rat

21,818 eligible (protein-coding) source genes.

| outcome | genes | % |
|---|---:|---:|
| `has_ortholog` | 20,198 | 92.57% |
| `no_edge_in_shared_tree` | 748 | 3.43% |
| `tree_lacks_target_species` | 614 | 2.81% |
| `not_in_any_tree` | 258 | 1.18% |

| relationship type | genes |
|---|---:|
| `ortholog_one2one` | 17,340 |
| `ortholog_one2many` | 1,583 |
| `ortholog_many2many` | 1,275 |

Distinct partners per gene: `{'1': 18397, '2': 859, '3': 233, '4': 201, '5': 76, '6': 59, '7': 48, '8': 23, '9': 8, '10': 16, '11': 52, '17': 14, '18': 1, '19': 5, '20': 10, '23': 2, '26': 8, '28': 2, '41': 91, '57': 53, '156': 40}`

### rat->human

22,016 eligible (protein-coding) source genes.

| outcome | genes | % |
|---|---:|---:|
| `has_ortholog` | 18,553 | 84.27% |
| `no_edge_in_shared_tree` | 1,580 | 7.18% |
| `tree_lacks_target_species` | 1,735 | 7.88% |
| `not_in_any_tree` | 148 | 0.67% |

| relationship type | genes |
|---|---:|
| `ortholog_one2one` | 15,841 |
| `ortholog_one2many` | 2,217 |
| `ortholog_many2many` | 495 |

Distinct partners per gene: `{'1': 17869, '2': 359, '3': 135, '4': 54, '5': 10, '6': 29, '7': 5, '8': 3, '9': 11, '11': 2, '13': 18, '16': 13, '17': 2, '19': 3, '21': 2, '22': 38}`

### rat->mouse

22,016 eligible (protein-coding) source genes.

| outcome | genes | % |
|---|---:|---:|
| `has_ortholog` | 20,339 | 92.38% |
| `no_edge_in_shared_tree` | 1,089 | 4.95% |
| `tree_lacks_target_species` | 440 | 2.00% |
| `not_in_any_tree` | 148 | 0.67% |

| relationship type | genes |
|---|---:|
| `ortholog_one2one` | 17,362 |
| `ortholog_one2many` | 1,689 |
| `ortholog_many2many` | 1,288 |

Distinct partners per gene: `{'1': 18732, '2': 684, '3': 245, '4': 78, '5': 76, '6': 49, '7': 17, '8': 41, '9': 17, '10': 34, '11': 4, '12': 19, '13': 2, '14': 34, '16': 2, '17': 2, '22': 13, '23': 1, '24': 21, '28': 7, '29': 2, '40': 156, '53': 57, '79': 4, '91': 41, '102': 1}`

## Triples — the number that does not follow from the pairs

- human protein-coding genes: **20,131**
- one2one to **both** rodents: **15,539**
- **clean 1:1:1** (and the mouse and rat partners are also one2one with each other): **15,494** (76.97%)
- one2one to both rodents but the rodent pair is **not** one2one: **45**

That last row is the whole reason to measure triples separately: those genes look clean
from every pairwise angle and are not clean as a set. A join built on pairwise evidence
alone would treat them as interchangeable.

### Joint classes

| human → mouse | human → rat | genes |
|---|---|---:|
| `one2one` | `one2one` | 15,539 |
| `none` | `none` | 2,269 |
| `one2many` | `one2many` | 649 |
| `one2one` | `one2many` | 389 |
| `one2one` | `none` | 386 |
| `many2many` | `many2many` | 302 |
| `one2many` | `one2one` | 156 |
| `none` | `one2one` | 137 |
| `many2many` | `one2many` | 116 |
| `one2many` | `many2many` | 68 |
| `one2many` | `none` | 58 |
| `none` | `one2many` | 29 |
| `many2many` | `none` | 28 |
| `none` | `many2many` | 5 |
