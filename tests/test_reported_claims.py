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


def _search_db() -> dict:
    return json.loads((RESULTS / "search_db_resolution.json").read_text(encoding="utf-8"))


def test_search_db_first_pass_as_sent_to_aging_in_005():
    """005-logs §1: every entry of the human search database, resolved against Ensembl 116's xref.

    Produced by an ad-hoc run when sent; now re-derived from committed code (tools/ResolveSearchDb +
    logs_orthology.search_db).
    """
    s = _search_db()
    assert s["search_database_sha256"] == "760984e8d402ade6b1105b811532bdd4041e33e66bb5dc204402d4d6a7be8838"
    assert s["base_entries"] == 20416
    assert s["xref_view"] == {"resolved": 19257, "multi_gene": 69, "off_primary_only": 62, "not_in_source": 1028}
    assert s["not_in_source_in_both"] == 1012, "005 §1: no Ensembl link in UniProt's own entry either"
    assert s["xref_not_in_source_but_xml_resolves"] == 16, "005 §1: UniProt 2026_09 / Ensembl 116 drift"


def test_human_gene_table_as_corrected_in_012():
    """011-logs §4 said 563 KB, measured on an awk prototype. The table mzLib's writer builds is
    523,218 bytes; 012-logs corrected it. 78,941 genes was sent in 011 and did not move."""
    import gzip
    import hashlib
    path = RESULTS / "gene_sets" / "Homo_sapiens.GRCh38.116.genes.tsv.gz"
    assert path.stat().st_size == 523218, "sent to dataRepo in 012-logs"
    assert hashlib.sha256(path.read_bytes()).hexdigest() ==         "e72d3b85328a572a7de92581297268ec50e97dd4cd4123c1358a7dc6c931d65f", "sent in 012-logs"
    lines = gzip.decompress(path.read_bytes()).decode("utf-8").splitlines()
    header = [l for l in lines if l.startswith("#!")]
    assert "#!source-file Homo_sapiens.GRCh38.116.gtf.gz" in header
    assert any(l.startswith("#!source-sha256 ed992f0eac7197d9") for l in header)
    assert len(lines) - len(header) - 1 == 78941, "sent in 011-logs §4"


def _search_db_species(name: str) -> dict:
    return json.loads((RESULTS / f"search_db_resolution{name}.json").read_text(encoding="utf-8"))


def test_xref_filter_parity_as_corrected_in_008_to_aging():
    """007-logs told aging the agrees==true filter recovers Ensembl's answer for 20,412 of 20,416. It
    was unpinned. After #1338 3bb04188 added the xref-only gene rows it is 20,416; 008-logs corrected it."""
    s = _search_db_species("")
    assert (s["parity_identical"], s["base_entries"]) == (20416, 20416), "sent to aging in 008-logs §3"
    assert s["xml_unresolved_but_xref_resolves"] == 4


def test_rodent_resolution_as_sent_to_aging_in_008():
    mouse, rat = _search_db_species("_mouse"), _search_db_species("_rat")
    assert mouse["search_database_sha256"].startswith("fb52debf")
    assert rat["search_database_sha256"].startswith("abf612c9")
    assert mouse["xml_view"] == {"resolved": 15474, "multi_gene": 124, "not_in_source": 1679}
    assert mouse["xref_view"] == {"resolved": 15494, "multi_gene": 123, "not_in_source": 1660}
    assert rat["xml_view"] == {"resolved": 4182, "multi_gene": 45, "off_primary_only": 950, "not_in_source": 3051}
    assert rat["xref_view"] == {"resolved": 4864, "multi_gene": 44, "not_in_source": 3320}
    assert (mouse["xml_unresolved_but_xref_resolves"], rat["xml_unresolved_but_xref_resolves"]) == (39, 725)
    assert rat["xml_off_primary_only_but_xref_resolves"] == 521, "008-logs §4"
    assert (mouse["parity_identical"], rat["parity_identical"]) == (17277, 8228)


def test_human_search_db_table_as_delivered_in_015():
    """015-logs handed dataRepo this file as the reference output their pyMzLib run will be diffed
    against. Written by tools/ResolveSearchDb at #1338 2f40c40c (LF line endings), gzipped with
    mtime 0 so the .gz is reproducible too. Counts per accession are PROTEOFORMS (52,359), not the
    20,416 entries the entry-level counts above describe."""
    import collections
    import csv
    import gzip
    import hashlib
    import io
    path = RESULTS / "search_db_human_e116.tsv.gz"
    gz = path.read_bytes()
    assert (len(gz), hashlib.sha256(gz).hexdigest()) == (
        728807, "e6ebada561a70d0e39d7e2e1cd36dfad1ac2ac29d8fabd7234ba611e905b6f17"), "015-logs"
    tsv = gzip.decompress(gz)
    assert (len(tsv), hashlib.sha256(tsv).hexdigest()) == (
        18074372, "2deb06ee9b1bfd1b63208299485e9908c44d99b127f5b5f7b04932c77f0c6d18"), "015-logs"
    rows = list(csv.DictReader(io.StringIO(tsv.decode("utf-8"), newline=""), delimiter="\t"))
    assert len(rows) == 53239
    outcome = {r["accession"]: r["outcome"] for r in rows}
    assert collections.Counter(outcome.values()) == {
        "resolved": 50026, "not_in_source": 1520, "multi_gene": 660, "off_primary_only": 153}, "015-logs §2"
    null_rows = collections.Counter(r["accession"] for r in rows if r["gene_id"] == "")
    assert set(null_rows.values()) == {1}, "015-logs §2: at most one null-gene row per accession"
    assert sum(1 for r in rows if r["source"] == "ensembl_xref") == 7, "015-logs §2: 4 entries, 7 proteoforms"


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
