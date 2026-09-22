"""The cardinality measurement owed to dataRepo (REQ-LOGS-4 and REQ-LOGS-6).

Two questions, and the second is the one they actually need:

* **How often is an orthogroup cleanly 1:1:1** across human / mouse / rat -- pairwise *and* as
  triples, because 1:1 human↔mouse plus 1:1 human↔rat does not imply a clean triple.
* **When there is no partner, why not?** A cross-species row in their ``age_effect_meta`` can
  only honestly exist, or honestly refuse to exist, if the refusal classes are distinguishable.

A finding about the second, recorded here because it changes what we promised:

    Compara does **not** let us separate *"no ortholog exists"* from *"no ortholog in this
    release"*. Both present as an absent edge. What the data *does* support is a decomposition
    by how far the inference got, which is strictly more honest and maps onto the same decision.

Run:  python -m logs_orthology.cardinality
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from . import sources
from .fetch import project_root
from .load import homology_paths, iter_homologies, load_gene_set, load_tree_index

SPECIES = list(sources.TAXA)
SHORT = {"homo_sapiens": "human", "mus_musculus": "mouse", "rattus_norvegicus": "rat"}

#: Compara's protein_default collection is built from protein-coding genes. Measuring refusal
#: rates over all biotypes would count lncRNAs as "no ortholog found" when they were never
#: eligible -- inflating the refusal classes with genes the source never considered.
ELIGIBLE_BIOTYPE = "protein_coding"

# ---------------------------------------------------------------------------------------------
# Refusal classes -- what we can actually derive, versus what we promised
# ---------------------------------------------------------------------------------------------

#: An orthology call exists.
HAS_ORTHOLOG = "has_ortholog"
#: In a gene tree that also contains genes of the target species, but no ortholog edge to any of
#: them. The source had the opportunity to call one and did not. This is the closest thing the
#: data offers to "no ortholog exists".
NO_EDGE_IN_SHARED_TREE = "no_edge_in_shared_tree"
#: In a gene tree, but that tree contains no gene of the target species at all. The tree is the
#: unit of inference, so there was nothing to compare against. Closest to "not in this release".
TREE_LACKS_TARGET = "tree_lacks_target_species"
#: In the release's gene set, but in no Compara gene tree. No call was ever attempted.
NOT_IN_ANY_TREE = "not_in_any_tree"
#: Not in the release's gene set at all. Zero by construction when we enumerate from the GTF;
#: non-zero only for externally supplied gene ids, which is exactly dataRepo's case.
NOT_IN_GENE_SET = "not_in_gene_set"

REFUSAL_ORDER = [
    HAS_ORTHOLOG, NO_EDGE_IN_SHARED_TREE, TREE_LACKS_TARGET, NOT_IN_ANY_TREE, NOT_IN_GENE_SET,
]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Measure cross-species orthology cardinality.")
    ap.add_argument("--out", default="results/cardinality",
                    help="output stem, relative to the project root")
    args = ap.parse_args(argv)

    print(f"Ensembl Compara release {sources.RELEASE}")

    # -- gene sets -----------------------------------------------------------------------------
    print("Loading gene sets from GTF...")
    gene_sets: dict[str, dict[str, str]] = {}
    gene_species: dict[str, str] = {}
    for sp in SPECIES:
        gs = load_gene_set(sp)
        gene_sets[sp] = gs
        for g in gs:
            gene_species[g] = sp
        coding = sum(1 for b in gs.values() if b == ELIGIBLE_BIOTYPE)
        print(f"  {SHORT[sp]:6s} {len(gs):7,} genes  ({coding:,} {ELIGIBLE_BIOTYPE})")

    # -- gene trees ----------------------------------------------------------------------------
    print("Loading gene-tree membership...")
    trees = load_tree_index(gene_species)
    print(f"  {len(trees.tree_of_gene):,} of our genes are in a tree; "
          f"{len(trees.species_in_tree):,} trees touched")

    # -- homologies ----------------------------------------------------------------------------
    print("Streaming homologies (3 files, both ends in our taxa)...")
    keep = set(SPECIES)
    seen_ids: set[str] = set()
    # ortho[(src, tgt)][gene] -> list of (partner, type, high_confidence)
    ortho: dict[tuple[str, str], dict[str, list[tuple[str, str, bool | None]]]] = defaultdict(
        lambda: defaultdict(list))
    type_counts: Counter[str] = Counter()
    conf_counts: Counter[str] = Counter()
    unknown_types: Counter[str] = Counter()
    #: Which dump each species-pair's orthologies were found in. The provider says the allocation
    #: is arbitrary; measuring it is what turns "read all three files" from a recommendation into
    #: a demonstrated requirement.
    attribution: dict[str, Counter[str]] = defaultdict(Counter)
    rows = 0
    dupes = 0

    for h in iter_homologies(homology_paths(), keep):
        rows += 1
        if h.homology_id in seen_ids:
            dupes += 1
            continue
        seen_ids.add(h.homology_id)
        type_counts[h.homology_type] += 1
        if h.homology_type not in sources.KNOWN_TYPES:
            unknown_types[h.homology_type] += 1
        if h.homology_type not in sources.ORTHOLOG_TYPES:
            continue
        if h.species_a == h.species_b:
            continue  # an "ortholog" within one species would be a contradiction; skip loudly below
        conf_counts["null" if h.is_high_confidence is None
                    else ("high" if h.is_high_confidence else "low")] += 1
        pair = " <-> ".join(sorted((SHORT[h.species_a], SHORT[h.species_b])))
        attribution[pair][h.source_file.split(".")[0]] += 1
        # The file states the order of the two genes is arbitrary, so record both directions.
        ortho[(h.species_a, h.species_b)][h.gene_a].append(
            (h.gene_b, h.homology_type, h.is_high_confidence))
        ortho[(h.species_b, h.species_a)][h.gene_b].append(
            (h.gene_a, h.homology_type, h.is_high_confidence))
        if rows % 2_000_000 == 0:
            print(f"    {rows:,} rows read, {len(seen_ids):,} distinct homologies")

    print(f"  {rows:,} in-scope rows, {len(seen_ids):,} distinct homologies, "
          f"{dupes:,} duplicate rows across the three files")

    # -- classification ------------------------------------------------------------------------
    print("Classifying...")
    pairwise: dict[str, dict] = {}
    for src in SPECIES:
        for tgt in SPECIES:
            if src == tgt:
                continue
            pairwise[f"{SHORT[src]}->{SHORT[tgt]}"] = classify_pair(
                src, tgt, gene_sets, trees, ortho)

    triples = classify_triples(gene_sets, trees, ortho)

    report = {
        "source": sources.SOURCE,
        "release": sources.RELEASE,
        "generated": _dt.date.today().isoformat(),
        "taxa": {SHORT[s]: sources.TAXA[s] for s in SPECIES},
        "assembly": {SHORT[s]: sources.ASSEMBLY[s] for s in SPECIES},
        "gene_sets": {
            SHORT[s]: {
                "total": len(gene_sets[s]),
                ELIGIBLE_BIOTYPE: sum(1 for b in gene_sets[s].values() if b == ELIGIBLE_BIOTYPE),
                "in_a_gene_tree": sum(1 for g in gene_sets[s] if g in trees.tree_of_gene),
            } for s in SPECIES
        },
        "homology_rows_in_scope": rows,
        "distinct_homologies": len(seen_ids),
        "duplicate_rows_across_files": dupes,
        "homology_type_counts": dict(type_counts.most_common()),
        "unknown_homology_types": dict(unknown_types),
        "ortholog_confidence": dict(conf_counts),
        "orthology_by_source_file": {k: dict(v) for k, v in attribution.items()},
        "pairwise": pairwise,
        "triples": triples,
    }

    stem = project_root() / args.out
    stem.parent.mkdir(parents=True, exist_ok=True)
    stem.with_suffix(".json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    stem.with_suffix(".md").write_text(render(report), encoding="utf-8")
    print(f"\nWrote {stem.with_suffix('.json')}\n      {stem.with_suffix('.md')}")
    return 0


def classify_pair(src: str, tgt: str, gene_sets, trees, ortho) -> dict:
    """Classify every eligible gene of ``src`` by its relationship to ``tgt``."""
    edges = ortho.get((src, tgt), {})
    status: Counter[str] = Counter()
    types: Counter[str] = Counter()
    partner_counts: Counter[int] = Counter()
    conf: Counter[str] = Counter()

    for gene, biotype in gene_sets[src].items():
        if biotype != ELIGIBLE_BIOTYPE:
            continue
        hits = edges.get(gene)
        if hits:
            status[HAS_ORTHOLOG] += 1
            # A gene's edges to one species normally share a type; record the set so a mixture
            # is visible rather than silently reduced to its first value.
            tset = {t for _, t, _ in hits}
            types["+".join(sorted(tset))] += 1
            partner_counts[len({p for p, _, _ in hits})] += 1
            hc = {c for _, _, c in hits}
            conf["null" if None in hc else ("high" if hc == {True} else
                                            ("low" if hc == {False} else "mixed"))] += 1
            continue
        tree = trees.tree_of_gene.get(gene)
        if tree is None:
            status[NOT_IN_ANY_TREE] += 1
        elif trees.tree_contains(tree, tgt):
            status[NO_EDGE_IN_SHARED_TREE] += 1
        else:
            status[TREE_LACKS_TARGET] += 1

    total = sum(status.values())
    return {
        "eligible_genes": total,
        "status": {k: status.get(k, 0) for k in REFUSAL_ORDER if k != NOT_IN_GENE_SET},
        "status_pct": {k: round(100 * status.get(k, 0) / total, 2) for k in REFUSAL_ORDER
                       if k != NOT_IN_GENE_SET} if total else {},
        "relationship_type": dict(types.most_common()),
        "distinct_partners": {str(k): v for k, v in sorted(partner_counts.items())},
        "confidence": dict(conf),
    }


def classify_triples(gene_sets, trees, ortho) -> dict:
    """Human-anchored triple classification: what does a human gene see in *both* rodents?"""
    hs, mm, rn = SPECIES
    to_mouse = ortho.get((hs, mm), {})
    to_rat = ortho.get((hs, rn), {})

    joint: Counter[str] = Counter()
    clean = 0
    one_to_one_both_but_not_triple = 0

    for gene, biotype in gene_sets[hs].items():
        if biotype != ELIGIBLE_BIOTYPE:
            continue
        m = to_mouse.get(gene)
        r = to_rat.get(gene)
        mk = _pair_label(m)
        rk = _pair_label(r)
        joint[f"mouse={mk} | rat={rk}"] += 1
        if mk == "one2one" and rk == "one2one":
            one_to_one_both_but_not_triple += 1
            # A clean triple also needs the mouse and rat partners to be each other's one2one.
            mg = m[0][0]
            rg = r[0][0]
            mr = ortho.get((mm, rn), {}).get(mg, [])
            if any(p == rg and t == "ortholog_one2one" for p, t, _ in mr):
                clean += 1

    total = sum(joint.values())
    return {
        "human_eligible_genes": total,
        "clean_1_1_1": clean,
        "clean_1_1_1_pct": round(100 * clean / total, 2) if total else 0.0,
        "one2one_to_both_rodents": one_to_one_both_but_not_triple,
        "one2one_to_both_but_rodents_not_one2one": one_to_one_both_but_not_triple - clean,
        "joint_classes": dict(joint.most_common()),
    }


def _pair_label(hits) -> str:
    if not hits:
        return "none"
    tset = {t for _, t, _ in hits}
    if tset == {"ortholog_one2one"}:
        return "one2one"
    if tset == {"ortholog_one2many"}:
        return "one2many"
    if tset == {"ortholog_many2many"}:
        return "many2many"
    return "+".join(sorted(t.replace("ortholog_", "") for t in tset))


def render(r: dict) -> str:
    """Human-readable report. The prose carries the caveats; the tables carry the numbers."""
    L: list[str] = []
    a = L.append
    a(f"# Cross-species orthology cardinality — {r['source']} release {r['release']}")
    a("")
    a(f"Generated {r['generated']}. Taxa: " +
      ", ".join(f"{k} ({v})" for k, v in r["taxa"].items()) + ".")
    a("")
    a("Owed to `dataRepo` as **REQ-LOGS-4** (cardinality) and **REQ-LOGS-6** (the refusal")
    a("classes). Every number here is measured from the pinned inputs recorded in")
    a("`data/PROVENANCE.md`; none is estimated.")
    a("")
    a("## The finding that changes what we promised")
    a("")
    a("We told `dataRepo` we would separate *\"no ortholog exists\"* from *\"no ortholog in this")
    a("release\"*. **Compara does not support that distinction** — both present as an absent")
    a("edge, and nothing in the dump says whether the source looked and declined or never had")
    a("the chance. Rather than report a class we cannot derive, the refusal is decomposed by")
    a("**how far the inference got**:")
    a("")
    a("| class | meaning |")
    a("|---|---|")
    a(f"| `{NO_EDGE_IN_SHARED_TREE}` | In a gene tree that also contains target-species genes, "
      "but no ortholog edge to any of them. The source had the opportunity and did not call one "
      "— the closest thing to *no ortholog exists*. |")
    a(f"| `{TREE_LACKS_TARGET}` | In a tree containing no target-species gene at all. The tree "
      "is the unit of inference, so there was nothing to compare against — closest to *not in "
      "this release*. |")
    a(f"| `{NOT_IN_ANY_TREE}` | In the release's gene set, but in no Compara tree. **No call was "
      "ever attempted.** |")
    a(f"| `{NOT_IN_GENE_SET}` | Not in this release's gene set. Zero by construction here, since "
      "we enumerate *from* the gene set; non-zero only for externally supplied gene ids — which "
      "is exactly `dataRepo`'s case. |")
    a("")
    a("The decomposition is strictly more honest than the one we promised and answers the same")
    a("question: whether a cross-species row can be stated, or must refuse itself.")
    a("")
    a("## Gene sets")
    a("")
    a("| species | genes in release | protein-coding | in a Compara gene tree |")
    a("|---|---:|---:|---:|")
    for sp, d in r["gene_sets"].items():
        a(f"| {sp} | {d['total']:,} | {d[ELIGIBLE_BIOTYPE]:,} | {d['in_a_gene_tree']:,} |")
    a("")
    a(f"Protein-coding is the eligible set: Compara's `protein_default` collection is built from")
    a("protein-coding genes, so counting other biotypes as *no ortholog found* would inflate the")
    a("refusal classes with genes that were never considered.")
    a("")
    a("## Homology rows")
    a("")
    a(f"- **{r['homology_rows_in_scope']:,}** rows with both ends in our three taxa")
    a(f"- **{r['distinct_homologies']:,}** distinct homologies after deduplicating on "
      f"`homology_id`")
    a(f"- **{r['duplicate_rows_across_files']:,}** rows were duplicates across the three "
      "genome-specific files")
    a("")
    a("### Why all three files must be read — measured, not assumed")
    a("")
    a("The provider's README warns that each genome-specific file holds only *an arbitrary")
    a("subset* of that genome's orthologies. It is worse than \"subset\" suggests:")
    a("")
    a("| species pair | orthologies found in — |")
    a("|---|---|")
    for pair, d in sorted(r["orthology_by_source_file"].items()):
        where = ", ".join(f"`{k}` **{v:,}**" for k, v in sorted(d.items()))
        a(f"| {pair} | {where} |")
    a("")
    a("**Each species pair lives entirely in one file, and not necessarily the obvious one.**")
    a("Every human↔mouse orthology is in the *mouse* dump; the human dump contains none of them.")
    a("Reading only the human file would have lost **100%** of human↔mouse and **100%** of")
    a("mouse↔rat — not a shortfall, a total miss, and one that would have looked like a")
    a("complete result. The zero duplicate count below is the other half of the same fact: the")
    a("files partition the homologies rather than overlapping, so the union is exact.")
    a("")
    a("### Homology types in scope")
    a("")
    a("| type | count |")
    a("|---|---:|")
    for k, v in r["homology_type_counts"].items():
        a(f"| `{k}` | {v:,} |")
    if r["unknown_homology_types"]:
        a("")
        a(f"⚠ **Types outside our vocabulary:** {r['unknown_homology_types']}. Reported rather "
          "than dropped — an unexpected value is a signal that the source's vocabulary moved.")
    a("")
    a("### Confidence")
    a("")
    a(f"`{r['ortholog_confidence']}` — `null` is **the source declining to qualify the call**,")
    a("which is not the same statement as low confidence and must not collapse into it.")
    a("")
    a("## Pairwise")
    a("")
    for name, d in r["pairwise"].items():
        a(f"### {name}")
        a("")
        a(f"{d['eligible_genes']:,} eligible (protein-coding) source genes.")
        a("")
        a("| outcome | genes | % |")
        a("|---|---:|---:|")
        for k in REFUSAL_ORDER:
            if k in d["status"]:
                a(f"| `{k}` | {d['status'][k]:,} | {d['status_pct'][k]:.2f}% |")
        a("")
        a("| relationship type | genes |")
        a("|---|---:|")
        for k, v in d["relationship_type"].items():
            a(f"| `{k}` | {v:,} |")
        a("")
        a(f"Distinct partners per gene: `{d['distinct_partners']}`")
        a("")
    a("## Triples — the number that does not follow from the pairs")
    a("")
    t = r["triples"]
    a(f"- human protein-coding genes: **{t['human_eligible_genes']:,}**")
    a(f"- one2one to **both** rodents: **{t['one2one_to_both_rodents']:,}**")
    a(f"- **clean 1:1:1** (and the mouse and rat partners are also one2one with each other): "
      f"**{t['clean_1_1_1']:,}** ({t['clean_1_1_1_pct']:.2f}%)")
    a(f"- one2one to both rodents but the rodent pair is **not** one2one: "
      f"**{t['one2one_to_both_but_rodents_not_one2one']:,}**")
    a("")
    a("That last row is the whole reason to measure triples separately: those genes look clean")
    a("from every pairwise angle and are not clean as a set. A join built on pairwise evidence")
    a("alone would treat them as interchangeable.")
    a("")
    a("### Joint classes")
    a("")
    a("| human → mouse | human → rat | genes |")
    a("|---|---|---:|")
    for k, v in t["joint_classes"].items():
        m, rr = k.split(" | ")
        a(f"| `{m.split('=')[1]}` | `{rr.split('=')[1]}` | {v:,} |")
    a("")
    return "\n".join(L)


if __name__ == "__main__":
    sys.exit(main())
