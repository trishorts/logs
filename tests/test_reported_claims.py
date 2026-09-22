"""Pin every number we have **sent to another project**.

A number in our own report can be corrected by re-running. A number in a partner's thread is
already in their design notes, and possibly in their schema. So once we send one, it becomes a
contract: if a re-run moves it, we owe a correction, and we should find that out from a failing
test rather than from them.

This is the durable form of the lesson that produced it. On 2026-09-22 two denominators were
wrong at once — ``protein_coding`` alone as the eligible set, and raw gene ids (including ALT
haplotypes) as the multi-gene denominator — and one of the resulting numbers had already been
sent in ``006-logs``. These tests exist so the second time is noisy.

Each assertion names the message it was quoted in. **Do not "fix" a failure by editing the
expected value.** A failure means either the measurement changed (send a correction, then update
here) or the code regressed (fix the code).

Run:  python tests/test_reported_claims.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

RESULTS = ROOT / "results"


def _cardinality() -> dict:
    return json.loads((RESULTS / "cardinality.json").read_text(encoding="utf-8"))


def _xrefs() -> dict:
    return json.loads((RESULTS / "accession_resolution.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------------------------
# Sent in 007-logs (which itself corrected 006-logs)
# ---------------------------------------------------------------------------------------------

def test_clean_triple_rate_as_sent_in_007():
    c = _cardinality()
    assert c["triples"]["clean_1_1_1_pct"] == 75.49, "sent to dataRepo in 007-logs §0"
    assert c["triples"]["clean_1_1_1"] == 15508


def test_look_clean_but_arent_as_sent_in_006_and_007():
    """The one number that survived the denominator correction unchanged, in both messages."""
    c = _cardinality()
    assert c["triples"]["one2one_to_both_but_rodents_not_one2one"] == 45


def test_pairwise_ortholog_rates_as_sent_in_007():
    pw = _cardinality()["pairwise"]
    assert pw["human->mouse"]["status_pct"]["has_ortholog"] == 86.77
    assert pw["human->rat"]["status_pct"]["has_ortholog"] == 85.28
    assert pw["mouse->rat"]["status_pct"]["has_ortholog"] == 91.98


def test_eligible_gene_counts_as_sent_in_007():
    gs = _cardinality()["gene_sets"]
    assert gs["human"]["eligible"] == 20543, "007-logs §0 correction table"
    assert gs["human"]["protein_coding"] == 20131, "the wrong denominator sent in 006-logs"


def test_no_rodent_ortholog_count_as_sent_in_007():
    assert _cardinality()["triples"]["joint_classes"]["mouse=none | rat=none"] == 2539


def test_multi_gene_rate_as_sent_in_007():
    """0.36%, not the 6.99% our first (wrong) measurement produced."""
    hu = _xrefs()["species"]["human"]["uniprot"]
    assert hu["reviewed_accessions"] == 19383
    assert hu["reviewed_multi_gene_accessions"] == 70
    assert hu["genes_per_accession_reviewed_pct"]["1"] == 99.319
    raw = hu["genes_per_accession_reviewed_unrestricted"]
    unrestricted_multi = sum(v for k, v in raw.items() if k not in ("0", "1"))
    assert unrestricted_multi == 1354, "the artifact size quoted in 007-logs §1"


def test_no_species_difference_in_multi_gene_rate():
    """'Human is much worse than the rodents' was retracted in 007-logs §1.

    If this ever fails, either the artifact is back or Ensembl changed something real. Both are
    worth stopping for.
    """
    sp = _xrefs()["species"]
    rates = {k: sp[k]["uniprot"]["genes_per_accession_reviewed_pct"]["1"] for k in sp}
    assert all(99.0 <= v <= 99.5 for v in rates.values()), rates
    assert max(rates.values()) - min(rates.values()) < 0.5, rates


def test_only_human_references_off_primary_genes():
    sp = _xrefs()["species"]
    assert sp["human"]["uniprot"]["off_primary_genes_referenced"] == 3274
    assert sp["mouse"]["uniprot"]["off_primary_genes_referenced"] == 0
    assert sp["rat"]["uniprot"]["off_primary_genes_referenced"] == 0


def test_refseq_retraction_as_sent_in_007():
    """The claim that overturned our own 'RefSeq is v3' deferral."""
    hr = _xrefs()["species"]["human"]["refseq"]
    assert hr["np_curated"] == 69569
    assert hr["genes_per_protein_accession_pct"]["1"] == 96.897


def test_isoform_suffix_count_as_corrected_in_008():
    """007-logs §4 sent 35,202 as ACCESSIONS; it was xref ROWS. Corrected in 008-logs §3."""
    hu = _xrefs()["species"]["human"]["uniprot"]
    assert hu["isoform_suffixed_accessions"] == 25177, "008-logs §3"
    assert hu["isoform_suffixed_rows"] == 35202, "the number 007-logs sent, under its true name"


def test_refseq_np_rate_as_corrected_in_008():
    """007 quoted the NP_+XP_ rate beside the NP_ count. Split in 008-logs §1."""
    hr = _xrefs()["species"]["human"]["refseq"]
    assert hr["genes_per_np_accession_pct"]["1"] == 99.579, "008-logs §1: NP_ 99.58%"
    assert hr["genes_per_np_accession"]["1"] == 69276
    assert hr["genes_per_xp_accession_pct"]["1"] == 94.867, "008-logs §1: XP_ 94.87%"
    assert hr["genes_per_protein_accession_pct"]["1"] == 96.897, "007 §3 table, combined"


def test_refseq_link_quality_as_corrected_in_008():
    """Mostly-inferred is true of XP_, false of NP_ (008-logs §2; also said to aging in 003)."""
    hr = _xrefs()["species"]["human"]["refseq"]
    assert hr["info_type_np"] == {"DIRECT": 60727, "INFERRED_PAIR": 17987, "SEQUENCE_MATCH": 582}
    assert hr["info_type_xp"]["DIRECT"] == 24884


def test_reviewed_off_primary_only_as_sent_in_007_and_003():
    """62 reviewed human accessions resolve to no primary-assembly gene (007 §2; aging 003)."""
    hu = _xrefs()["species"]["human"]["uniprot"]
    assert hu["reviewed_resolving_to_nothing"] == 62


def test_histones_are_the_multi_gene_story():
    """All four core histones in the top seven genuine multi-gene accessions (007-logs §2)."""
    top = _xrefs()["species"]["human"]["uniprot"]["reviewed_multi_gene_top"]
    by_acc = {row["accession"]: row["genes"] for row in top}
    assert by_acc.get("P62805") == 14, "histone H4"
    assert by_acc.get("P68431") == 10, "histone H3.1"
    assert by_acc.get("P0C0S8") == 5, "histone H2A"
    assert by_acc.get("P62807") == 5, "histone H2B"


def test_file_partition_as_sent_in_006():
    """Every human<->mouse orthology lives in the mouse dump; the human dump has none."""
    attrib = _cardinality()["orthology_by_source_file"]
    hm = attrib["human <-> mouse"]
    assert list(hm) == ["mus_musculus"], hm
    assert hm["mus_musculus"] == 23764


if __name__ == "__main__":
    import traceback

    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
        except Exception:
            failed += 1
            print(f"  FAIL  {fn.__name__}")
            traceback.print_exc()
    print(f"\n{len(fns) - failed}/{len(fns)} reported claims still hold")
    sys.exit(1 if failed else 0)
