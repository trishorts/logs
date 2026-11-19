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

import collections
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


RAT_XML = Path("F:/aging_data/db/uniprotkb_proteome_UP000002494_AND_revi_2026-09-22.xml")


def test_rat_cause_as_sent_in_022_to_datarepo_and_013_to_aging():
    """dataRepo 020 counted rat by ``outcome`` (the XML's view: 48.6% gene-less). 022/013 answered
    that aging's view, any ``ensembl_xref_agrees`` row, keeps 4,908 of 8,228, and split the 725
    recovered entries by XML outcome. The id-series counts need the search XML itself."""
    import collections
    import re
    rat = _search_db_species("_rat")
    with_gene = rat["xref_view"]["resolved"] + rat["xref_view"]["multi_gene"]
    assert (with_gene, rat["parity_identical"]) == (4908, 8228), "022-logs §1, 013-logs §1"
    rescued_not_in_source = rat["xml_unresolved_but_xref_resolves"] - rat["xml_off_primary_only_but_xref_resolves"]
    assert rescued_not_in_source == 204, "022-logs §1"
    if not RAT_XML.exists():
        print(f"        (series counts not checked: {RAT_XML} is absent on this machine)")
        return
    series: collections.Counter = collections.Counter()
    for entry in RAT_XML.read_text(encoding="utf-8").split("<entry ")[1:]:
        series.update({g[:12] for g in re.findall(r'<property type="gene ID" value="(ENSRNOG\d+)', entry)})
    assert series == {"ENSRNOG00000": 4227, "ENSRNOG00060": 4122,
                      "ENSRNOG00055": 4119, "ENSRNOG00065": 4106}, "022-logs §1"


def test_rat_agrees_view_losses_as_sent_in_024_to_datarepo():
    """dataRepo 023 reported 44 rat entries the XML resolves but the agrees view drops. 024 said
    why: not one of the 44 accessions is in Ensembl's rat UniProt xref. For 42, Ensembl links the
    gene to TrEMBL entries only; the other 2 genes have no UniProt xref. Counted over ENTRIES:
    the table's variant proteoform rows would make it 45."""
    import collections
    import csv
    import gzip
    with open(RESULTS / "search_db_rat_e116.tsv", encoding="utf-8", newline="") as f:
        by: dict[str, list] = collections.defaultdict(list)
        for r in csv.DictReader(f, delimiter="\t"):
            if r["accession"] == r["entry_accession"]:
                by[r["accession"]].append(r)
    lost = {a: rs[0]["gene_id"] for a, rs in by.items()
            if rs[0]["outcome"] in ("resolved", "multi_gene")
            and not any(r["ensembl_xref_agrees"] == "true" for r in rs)}
    assert len(lost) == 44, "024-logs, dataRepo 023 §2"
    xref = ROOT / "data/compara/Rattus_norvegicus.GRCr8.116.uniprot.tsv.gz"
    if not xref.exists():
        print(f"        (xref split not checked: {xref} is absent on this machine)")
        return
    accs: set = set()
    gene_dbs: dict[str, set] = collections.defaultdict(set)
    with gzip.open(xref, "rt", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            accs.add(r["xref"])
            gene_dbs[r["gene_stable_id"]].add(r["db_name"])
    assert not accs & set(lost), "024-logs: none of the 44 is in Ensembl's xref"
    split = collections.Counter(
        "trembl_only" if gene_dbs.get(g) == {"Uniprot/SPTREMBL"} else
        "no_xref" if not gene_dbs.get(g) else "other" for g in lost.values())
    assert split == {"trembl_only": 42, "no_xref": 2}, "024-logs"
    assert {a for a, g in lost.items() if not gene_dbs.get(g)} == {"P62959", "Q5XI51"}, "024-logs"


SNAPSHOT = ROOT / "snapshots" / "compara-116"


def test_first_orthology_snapshot_as_sent_in_026():
    """026-logs told dataRepo the first ``logs:DEF-ORTHOLOGY v1`` snapshot exists (mzLib #1381,
    ``tools/BuildOrthologySnapshot``). Its manifest pins every file by sha256; these are the numbers
    the message quoted. The snapshot is gitignored and machine-local."""
    manifest = SNAPSHOT / "manifest.json"
    if not manifest.exists():
        print(f"        (not checked: {manifest} is absent on this machine)")
        return
    m = json.loads(manifest.read_text(encoding="utf-8"))
    assert (m["format"], m["format_version"], m["release"]) == ("ensembl-orthology-snapshot", 1, "116"), "026-logs"
    assert m["snapshot_id"].startswith("b63a3331eb87c93e"), "026-logs"
    assert m["species"] == ["homo_sapiens", "mus_musculus", "rattus_norvegicus"]
    assert m["gene_set_sha256"] == {  # the GTF sha256s, as in 016's manifest
        "homo_sapiens": "ed992f0eac7197d9627bda618f8f831ba355c95bd5d0796af785387d462828b6",
        "mus_musculus": "5c29fd9e3157cf40fdbbf76ab25bfe7f79aa61313e0b672664ddb0cb251c02e1",
        "rattus_norvegicus": "e025aa7eeefa74e896fdfdf760d01166d8e3ba9d99ba1de2f1b004925f41d338"}, "026-logs"
    rows = {f["path"]: f.get("rows") for f in m["files"]}
    assert rows == {
        "genes/homo_sapiens.parquet": 78941, "genes/mus_musculus.parquet": 78348,
        "genes/rattus_norvegicus.parquet": 43360,
        "members/homo_sapiens.parquet": 19690, "members/mus_musculus.parquet": 22045,
        "members/rattus_norvegicus.parquet": 22379,
        "pairs/homo_sapiens__homo_sapiens.parquet": 141173, "pairs/homo_sapiens__mus_musculus.parquet": 23764,
        "pairs/homo_sapiens__rattus_norvegicus.parquet": 22105, "pairs/mus_musculus__mus_musculus.parquet": 373904,
        "pairs/mus_musculus__rattus_norvegicus.parquet": 40027,
        "pairs/rattus_norvegicus__rattus_norvegicus.parquet": 400961, "views.sql": None}, "026-logs"
    assert (len(m["files"]), sum(f["bytes"] for f in m["files"])) == (13, 9004379), "026-logs"
    assert m["build_checks"]["identical_duplicate_rows_dropped"] == 0, "026-logs"
    import hashlib
    for f in m["files"]:
        assert hashlib.sha256((SNAPSHOT / f["path"]).read_bytes()).hexdigest() == f["sha256"], f["path"]
    # 027-logs / 016-logs: the published release, tag orthology-compara-116-b63a3331. Its tar is
    # reproducible (sorted names, zeroed mtime and owners), so a rebuild from the snapshot must match.
    tar = ROOT / "snapshots" / "_release" / "compara-116.tar"
    if tar.exists():
        assert hashlib.sha256(tar.read_bytes()).hexdigest() == \
            "b1d682a51e7e5759cd72719713d4a00a03b07b9ee033b8bdf8f0f54fd7fb747b", "release asset, 027-logs"
    assert hashlib.sha256(manifest.read_bytes()).hexdigest() == \
        "fd0a9d8f5d211a91bdafd4c843ee4f0085be8cf0d7ff4fc779c5e6ebda5074aa", "release asset, 027-logs"


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


def test_resolver_input_manifest_as_sent_in_016():
    """The per-(species, release) manifest promised in 015 §1, sent in 016-logs."""
    import csv
    import gzip
    import hashlib
    doc = json.loads((RESULTS / "resolver_inputs_e116.json").read_text(encoding="utf-8"))
    assert doc["resolver"]["mzlib_release"] == "1.0.592", "016-logs"
    want = {  # species: (gene-set table sha256, row gene_set_sha256 = GTF, xref sha256)
        "homo_sapiens": ("e72d3b85328a572a7de92581297268ec50e97dd4cd4123c1358a7dc6c931d65f",
                         "ed992f0eac7197d9627bda618f8f831ba355c95bd5d0796af785387d462828b6",
                         "f1e26db23b0771f7a5778067af20683de63d863b1c0834aa564d5d036ec85864"),
        "mus_musculus": ("06d91f92289211867af002de7166c8ce3f70ef31e5a373a3528afb4022670d50",
                         "5c29fd9e3157cf40fdbbf76ab25bfe7f79aa61313e0b672664ddb0cb251c02e1",
                         "19b91eefd8cc3946a47c092a69ec065f1f2304a08927d91efd1f61c7840c6f91"),
        "rattus_norvegicus": ("426ea43ebeceb27003e3c5597fb5411932b52118b2ad91bfed6d2328efc95995",
                              "e025aa7eeefa74e896fdfdf760d01166d8e3ba9d99ba1de2f1b004925f41d338",
                              "8b1c91f3d88bfafe2d4bb67a43f2a79d1f494bb56d48690a0cbd736a44030eda"),
    }
    got = {e["species"]: (e["inputs"]["gene_set"]["sha256"], e["row_values"]["gene_set_sha256"],
                          e["row_values"]["ensembl_xref_sha256"]) for e in doc["species"]}
    assert got == want, "016-logs"
    for e in doc["species"]:
        gs = e["inputs"]["gene_set"]
        assert hashlib.sha256((ROOT / gs["path"]).read_bytes()).hexdigest() == gs["sha256"], gs["path"]
    # The manifest's human row values are what every row of the table delivered in 015 carries.
    with gzip.open(RESULTS / "search_db_human_e116.tsv.gz", "rt", encoding="utf-8", newline="") as f:
        seen = {(r["gene_set_release"], r["gene_set_sha256"], r["ensembl_xref_sha256"])
                for r in csv.DictReader(f, delimiter="\t")}
    assert seen == {("116", want["homo_sapiens"][1], want["homo_sapiens"][2])}, seen


def test_entry_vs_proteoform_split_as_sent_in_016():
    """016 §2: pyMzLib 0.2.0 writes the entry-level rows; the rest are variant proteoforms whose
    rows equal their entry's in every column but ``accession``."""
    import csv
    import gzip
    with gzip.open(RESULTS / "search_db_human_e116.tsv.gz", "rt", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    entry = [r for r in rows if "_" not in r["accession"]]
    variant = [r for r in rows if "_" in r["accession"]]
    assert (len(entry), len({r["accession"] for r in entry})) == (20899, 20416), "016-logs §2"
    assert (len(variant), len({r["accession"] for r in variant})) == (32340, 31943), "016-logs §2"
    cols = [c for c in rows[0] if c != "accession"]
    answers: dict[str, set] = {}
    for r in rows:
        answers.setdefault(r["accession"], set()).add(tuple(r[c] for c in cols))
    differ = [a for a in {r["accession"] for r in variant}
              if answers.get(a.split("_", 1)[0]) != answers[a]]
    assert differ == [], "016-logs §2: no variant proteoform differs from its entry"


def test_file_partition_as_sent_in_006():
    """Every human<->mouse orthology lives in the mouse dump; the human dump has none."""
    attrib = _cardinality()["orthology_by_source_file"]
    hm = attrib["human <-> mouse"]
    assert list(hm) == ["mus_musculus"], hm
    assert hm["mus_musculus"] == 23764


# ---------------------------------------------------------------------------------------------
# Sent to ptmQtl in 009-logs
# ---------------------------------------------------------------------------------------------

def test_agingptm_builds_hold_the_same_proteins_as_sent_in_009():
    """One alignment serves both sha keys: the builds differ only in modified-residue features."""
    pairs = {p["species"]: p for p in json.loads(
        (RESULTS / "search_db_equivalence.json").read_text(encoding="utf-8"))["pairs"]}
    expected = {  # entries, modified residues base -> build, build sha prefix
        "human": (20416, 56282, 59564, "eaefbb7e"),
        "mouse": (17277, 50617, 51372, "26ea83c2"),
        "rat": (8228, 27265, 30134, "caf342e1"),
    }
    for sp, (entries, before, after, sha) in expected.items():
        p = pairs[sp]
        assert p["same_proteins"] and p["differs_beyond_modified_residues"] == [], sp
        assert p["entries_base"] == p["entries_built"] == entries, sp
        assert (p["modified_residues_base"], p["modified_residues_built"]) == (before, after), sp
        assert p["built_sha256"].startswith(sha), sp


def _alignment_check() -> dict:
    return json.loads((RESULTS / "alignment_check_e116.json").read_text(encoding="utf-8"))


def test_compara_alignment_holds_the_store_as_sent_in_009():
    a = _alignment_check()
    assert a["format"]["stats"]["alignments"] == 54308
    assert a["format"]["ragged_alignments"] == 0 and a["format"]["n_duplicate"] == 0
    s = a["store"]
    assert s["members"] == 64114 and s["members_missing"] == 0
    assert s["pair_rows_protein_missing"] == 0
    assert s["alignments_holding_two_trees"] == 0


def test_orthologs_without_a_shared_alignment_as_sent_in_009():
    split = _alignment_check()["store"]["split_rows_by_type_pair_tree"]
    orth = {k: v for k, v in split.items() if k.startswith("ortholog")}
    assert sum(orth.values()) == 760
    assert all(k.endswith("|different_trees") for k in orth), "every split ortholog joins two trees"
    by_pair = {}
    for k, v in orth.items():
        by_pair[k.split("|")[1]] = by_pair.get(k.split("|")[1], 0) + v
    assert by_pair == {"homo_sapiens~mus_musculus": 478, "homo_sapiens~rattus_norvegicus": 278,
                       "mus_musculus~rattus_norvegicus": 4}
    assert sum(v for k, v in split.items() if k.startswith("other_paralog|")) == 750996


def test_leg1_entry_identity_as_sent_in_009():
    leg1 = _alignment_check()["leg1_entry_vs_tree_protein"]
    expected = {"homo_sapiens": (19446, 17812), "mus_musculus": (15855, 13714), "rattus_norvegicus": (4967, 2841)}
    for sp, (pairs, identical) in expected.items():
        assert (leg1[sp]["entry_gene_pairs"], leg1[sp]["identical"]) == (pairs, identical), sp


def test_canonical_v3_resolution_as_sent_in_010_to_pxreprise():
    """010-logs answered PXR-O6/O7 on the agingPTM-v3 canonical databases (PXReprise 007): coverage per
    view, the TrEMBL questions, the accessions Ensembl 116's xref has never heard of, and pyMzLib
    0.2.0 (the engine's call) against the C# rows. Counts are ENTRIES."""
    expected = {  # sha, entries, agrees, xml, agree-or-silent, TrEMBL, TrEMBL silent
        "human": ("fd80cf88", 20652, 19505, 19526, 19532, 323, 11),
        "mouse": ("3c4ac3fb", 21860, 19130, 20215, 20254, 4641, 1105),
        "rat": ("7f08fd3c", 21471, 14714, 17474, 18203, 13258, 3445),
    }
    for sp, (sha, n, agrees, xml, aos, trembl, silent) in expected.items():
        s = _search_db_species(f"_{sp}_canonical-v3")
        cov = lambda v: v.get("resolved", 0) + v.get("multi_gene", 0)  # noqa: E731
        assert s["search_database_sha256"].startswith(sha), sp
        assert (s["base_entries"], s["parity_identical"]) == (n, n), sp
        assert (cov(s["xref_view"]), cov(s["xml_view"]), s["agree_or_silent_covered"]) == (agrees, xml, aos), sp
        t = s["by_dataset"]["TrEMBL"]
        assert (t["entries"], t["xref_silent_xml_resolves"]["entries"]) == (trembl, silent), sp
        assert t["no_ensembl_dbreference"]["entries"] == 0, f"{sp}: every TrEMBL entry links Ensembl"
    rat, mouse = _search_db_species("_rat_canonical-v3"), _search_db_species("_mouse_canonical-v3")
    created = rat["by_dataset"]["TrEMBL"]["xref_silent_xml_resolves"]["created"]
    assert created.get("2025", 0) + created.get("2026", 0) == 3442, "rat: created 2025-2026"
    assert mouse["by_dataset"]["TrEMBL"]["xref_silent_xml_resolves"]["created"] == {"2025": 45, "2026": 1060}
    assert rat["not_in_source_in_both"] == 2840
    unnamed = {sp: _search_db_species(f"_{sp}_canonical-v3")["by_dataset"]["TrEMBL"]["no_primary_gene_name"]
               for sp in ("human", "mouse", "rat")}
    assert unnamed["rat"] == {"entries": 853, "with_agreeing_gene": 138, "xml_view": {"resolved": 813, "multi_gene": 40}}
    assert unnamed["mouse"] == {"entries": 45, "with_agreeing_gene": 14, "xml_view": {"resolved": 44, "multi_gene": 1}}
    assert unnamed["human"] == {"entries": 129, "with_agreeing_gene": 58, "xml_view": {"resolved": 66, "off_primary_only": 63}}
    parity = json.loads((RESULTS / "engine_parity_canonical-v3.json").read_text(encoding="utf-8"))["species"]
    assert {p["species"]: (p["pymzlib"], p["pymzlib_rows"], p["identical"]) for p in parity} == {
        "human": ("0.2.0", 21139, True), "mouse": ("0.2.0", 22383, True), "rat": ("0.2.0", 22464, True)}


def test_store_resolutions_equal_ours_as_sent_in_017_to_pxreprise():
    """017-logs closed PXR-O10: every canonical (agingPTM v3-v8) ``logs.resolve_genes`` artefact in the
    store equals our rows. v3 is compared with our C# tables; every later build and every mzLib 1.0.595
    re-run is compared with v3, on all columns except the database sha256. Each passes every provenance
    check. It also corrected 013: rat's 3,042 is the XML view's ``not_in_source``, a different set from
    the 3,445 xref-silent TrEMBL entries 013 compared it with."""
    runs = {r["label"]: r for r in json.loads(
        (RESULTS / "store_diff_canonical.json").read_text(encoding="utf-8"))["runs"]}
    assert len(runs) == 21
    assert all(r["identical"] and r["only_store"] == r["only_reference"] == 0 for r in runs.values())
    assert all(v is True for r in runs.values() for v in r["provenance"]["checks"].values())
    assert {k for k, r in runs.items() if r["same_database"]} == {
        f"{sp}-v3-mzlib1.0.59{v}" for sp in ("human", "mouse", "rat") for v in (3, 5)}
    assert sorted({r["provenance"]["mzlib"] for r in runs.values()}) == ["1.0.593", "1.0.595"]
    assert runs["rat-v3-mzlib1.0.593"]["provenance"]["outcome_by_entry"] == {
        "multi_gene": 153, "not_in_source": 3042, "off_primary_only": 955, "resolved": 17321}
    rat = _search_db_species("_rat_canonical-v3")["by_dataset"]
    assert rat["Swiss-Prot"]["no_ensembl_dbreference"]["entries"] == 3042
    assert rat["TrEMBL"]["no_ensembl_dbreference"]["entries"] == 0
    assert rat["TrEMBL"]["xref_silent_xml_resolves"]["entries"] == 3445
    v8 = runs["human-v8-mzlib1.0.595"]["provenance"]["search_database_sha256"]
    assert v8.startswith("c1a9e88f9af099af"), "human v8 is byte-identical to v7 (PXReprise 016)"
    v7 = Path("F:/aging_data/db/UP000005640_all_genecentric_2026_03_agingPTM-v7.xml")
    if v7.exists():
        import hashlib
        assert hashlib.sha256(v7.read_bytes()).hexdigest() == v8, "the v8 artefact covers human v7"


def test_pymzlib_080_resolves_as_before_as_sent_in_033_to_datarepo():
    """033-logs told dataRepo that pyMzLib 0.8.0 (mzLib 1.0.597, whose #1501 changes how dbReferences are read)
    gives ``logs.resolve_genes`` the same rows: every column of our C# tables, all three canonical v3 databases."""
    runs = json.loads((RESULTS / "engine_parity_canonical-v3_pymzlib-0.8.0.json").read_text(encoding="utf-8"))["species"]
    assert {r["species"]: (r["pymzlib"], r["pymzlib_rows"], len(r["compared_on"]), r["identical"]) for r in runs} == {
        "human": ("0.8.0", 21139, 19, True), "mouse": ("0.8.0", 22383, 19, True), "rat": ("0.8.0", 22464, 19, True)}
    assert all(r["mzlib"].endswith("4a183123ab41ed341361099d1ad93a281ea678fb") for r in runs), "mzLib 1.0.597's tag"


def test_canonical_v3_views_as_sent_in_010_reproduced_by_mzlib():
    """010-logs's agrees, agrees-or-silent and TrEMBL-silent counts came from a Python re-reading of the
    xref (search_db.py). On 2026-11-10 mzLib's own resolver (branch feat/ensembl-xref-agreement,
    tools/XrefAgreementCounts) reproduced every one. This pins the C# counts, so a decision rests on them."""
    runs = {r["label"]: r for r in json.loads(
        (RESULTS / "xref_agreement_canonical-v3_e116.json").read_text(encoding="utf-8"))["runs"]}
    expected = {  # sha, entries, agrees, agrees-or-silent, TrEMBL silent
        "human": ("fd80cf88", 20652, 19505, 19532, 11),
        "mouse": ("3c4ac3fb", 21860, 19130, 20254, 1105),
        "rat": ("7f08fd3c", 21471, 14714, 18203, 3445),
    }
    for sp, (sha, n, agrees, aos, silent) in expected.items():
        r = runs[sp]
        assert r["search_database_sha256"].startswith(sha), sp
        assert (r["all"]["entries"], r["all"]["agrees"], r["all"]["agrees_or_silent"]) == (n, agrees, aos), sp
        assert r["by_dataset"]["TrEMBL"]["with_a_silent_row"] == silent, sp
        assert r["rows_where_agreement_contradicts_the_v1_boolean"] == 0, sp
        assert r["all"]["disagrees_only"] == 0, f"{sp}: no entry is left out only because Ensembl disagrees"
    created = runs["rat"]["by_dataset"]["TrEMBL"]["silent_by_created_year"]
    assert created.get("2025", 0) + created.get("2026", 0) == 3442


def test_leg1_on_canonical_v3_as_sent_in_010_to_ptmqtl():
    """009 warned ptmQtl that rat refuses more often at leg 1 (57.2% of reviewed entries identical to
    their tree protein). 010 corrected it for the canonical agingPTM-v3 databases: rat's TrEMBL
    entries are mostly Ensembl's own translations. Agrees view, entry x gene pairs."""
    leg = json.loads((RESULTS / "leg1_canonical-v3_e116.json").read_text(encoding="utf-8"))["leg1_entry_vs_tree_protein"]
    expected = {"homo_sapiens": (19627, 17914), "mus_musculus": (19553, 17085), "rattus_norvegicus": (14819, 11463)}
    for sp, (pairs, identical) in expected.items():
        assert (leg[sp]["entry_gene_pairs"], leg[sp]["identical"]) == (pairs, identical), sp
    rat = leg["rattus_norvegicus"]["by_dataset"]
    assert (rat["TrEMBL"]["entry_gene_pairs"], rat["TrEMBL"]["identical"]) == (9859, 8622)
    assert (rat["Swiss-Prot"]["entry_gene_pairs"], rat["Swiss-Prot"]["identical"]) == (4960, 2841)
    xml = Path("F:/aging_data/db/UP000002494_all_genecentric_2026_03_agingPTM-v3.xml")
    if not xml.exists():
        print(f"        (Ensembl-consortium count not checked: {xml} is absent on this machine)")
        return
    import collections
    import re
    cites: collections.Counter = collections.Counter()
    ds = ens = None
    with open(xml, encoding="utf-8") as fh:
        for line in fh:
            s = line.lstrip()
            if s.startswith("<entry"):
                ds, ens = re.search(r'dataset="([^"]+)"', s).group(1), False
            elif s.startswith('<consortium name="Ensembl"'):
                ens = True
            elif s.startswith("</entry>"):
                cites[(ds, ens)] += 1
    assert cites == {("TrEMBL", True): 13258, ("Swiss-Prot", False): 8213}, "010-logs to ptmQtl"


def test_v2_artefacts_equal_ours_as_sent_in_037_to_datarepo():
    """037-logs did the diff dataRepo 036 asked for: its 41 first v2 artefacts (mzLib 1.0.598, one per searched
    database, human 15, mouse 17, rat 9). (A) Each equals aging's v1 artefact for the same database on every v1
    column (all but definition_id). (B) Each equals our own mzLib 1.0.598 run on the same file, with our gene sets
    and xrefs, on every column, ensembl_xref_agreement included. 036's outcome-by-agreement table is reproduced."""
    a = json.loads((RESULTS / "store_diff_v2_against_v1.json").read_text(encoding="utf-8"))["runs"]
    b = json.loads((RESULTS / "store_diff_v2_against_mzlib-1.0.598.json").read_text(encoding="utf-8"))["runs"]
    for runs in (a, b):
        assert len(runs) == 41
        assert all(r["identical"] and r["only_store"] == r["only_reference"] == 0 for r in runs)
        assert all(v is True for r in runs for v in r["provenance"]["checks"].values())
        assert {r["provenance"]["mzlib"] for r in runs} == {"1.0.598"}
        assert sorted(collections.Counter(r["species"] for r in runs).values()) == [9, 15, 17]
    assert all(r["ignored_columns"] == ["definition_id"] and "ensembl_xref_agreement" not in r["compared_on"]
               and len(r["compared_on"]) == 18 and r["same_database"] for r in a)
    assert all(len(r["compared_on"]) == 19 for r in b)
    assert all(r["same_database"] and "ensembl_xref_agreement" in r["compared_on"] for r in b)
    total: collections.Counter = collections.Counter()
    for r in a:
        total.update(r["agreement_by_outcome"])
    assert dict(total) == {
        "resolved|agrees": 285567, "resolved|silent": 16969, "resolved|disagrees": 71,
        "multi_gene|agrees": 7638, "multi_gene|silent": 1053, "multi_gene|disagrees": 2303,
        "off_primary_only|agrees": 1589, "off_primary_only|null": 3637,
        "not_in_source|agrees": 1079, "not_in_source|null": 26794}, "dataRepo 036's table"
    assert sum(total.values()) == sum(r["store_rows"] for r in b) == 346700


def test_orthologs_on_aging_catalog_as_sent_in_020_to_pxreprise():
    """020-logs answered PXR-O13 on aging's catalog 4e486c3dcf0aa01c, which registers our snapshot as artefact
    0fe30fe8d4edc728 (019 said it held none). The real orthology join gives GFAP's partners, and a gene symbol
    matched across organisms (019's stand-in) gives the same partner accessions for 80.6% (mouse) and 67.7%
    (rat) of 16,306 human accessions. Most symbol partners that orthology cannot reach resolve to no gene."""
    r = json.loads((RESULTS / "catalog_orthologs_4e486c3dcf0aa01c.json").read_text(encoding="utf-8"))
    snap = r["snapshot"]
    assert (snap["artefact_id"], snap["release"]["logs"], snap["manifest_matches_registration"]) == (
        "0fe30fe8d4edc728", "orthology-compara-116-b63a3331", True)
    steps = {s["step"]: s["rows"] for s in r["one_accession"]["steps"]}
    assert [g[0] for g in steps["accession -> gene"]] == ["ENSG00000131095"]
    assert [(o[1], o[2]) for o in steps["gene -> orthologs in mus_musculus"]] == [("ENSMUSG00000020932", "ortholog_one2one")]
    assert [(o[1], o[2]) for o in steps["gene -> orthologs in rattus_norvegicus"]] == [("ENSRNOG00000002919", "ortholog_one2one")]
    assert [a[1] for a in steps["partner genes -> accessions"]] == ["P03995", "P47819"]
    sv = r["symbol_vs_orthology"]
    assert (sv["denominator"]["human_accessions"], sv["denominator"]["human_genes"]) == (16306, 16196)
    m, rt = sv["species"]["mus_musculus"], sv["species"]["rattus_norvegicus"]
    assert sum(m["classes"].values()) == sum(rt["classes"].values()) == 16306
    assert (m["classes"]["same"], rt["classes"]["same"]) == (13141, 11036)
    gained = lambda c: c["only_orthology"] + c["symbol_subset_of_orthologs"]  # noqa: E731
    assert (gained(m["classes"]), gained(rt["classes"])) == (874, 1057), "partners only orthology finds"

    def why(sp, prefix):
        return sum(v["pairs"] for k, v in sp["symbol_partners_by_reason"].items() if k.startswith(prefix))
    assert (why(m, "partner_has_no_gene"), why(rt, "partner_has_no_gene")) == (1126, 2834)
    assert rt["symbol_partners_by_reason"]["partner_has_no_gene:off_primary_only"]["pairs"] == 344
    assert (why(m, "human_gene_has_no_ortholog"), why(rt, "human_gene_has_no_ortholog")) == (284, 260)
    assert (why(m, "partner_gene_not_an_ortholog"), why(rt, "partner_gene_not_an_ortholog")) == (70, 115)
    beyond = lambda c: c["only_symbol"] + c["symbol_adds_non_orthologs"]  # noqa: E731
    other = lambda c: c["disjoint"] + c.get("overlapping_different", 0)  # noqa: E731
    assert (beyond(m["classes"]), beyond(rt["classes"])) == (1376, 2971), "partners only the symbol adds"
    assert (other(m["classes"]), other(rt["classes"])) == (91, 168)
    assert (m["classes"]["neither"], rt["classes"]["neither"]) == (824, 1074)
    ifna13 = next(e for e in m["examples"]["symbol_subset_of_orthologs"] if e[1] == "IFNA13")
    assert (len(ifna13[2]), len(ifna13[3])) == (1, 10), "IFNA13: 1 mouse partner by name, 10 by orthology"
    assert r["engine_artefacts"]["logs.resolve_genes"] == 42
    catalog = Path(r["catalog"])
    if catalog.exists():  # the two examples 020 named: reviewed mouse entries that resolve to no gene
        import duckdb
        con = duckdb.connect()
        con.execute(f"ATTACH '{catalog.as_posix()}' AS cat (READ_ONLY)")
        got = dict(con.execute("""select accession, list(distinct outcome order by outcome) from cat.gene_resolutions
            where accession in ('Q9QXJ1', 'Q9Z223') and gene_id is null group by 1""").fetchall())
        assert got == {"Q9QXJ1": ["not_in_source"], "Q9Z223": ["not_in_source"]}
        assert con.execute("select count(*) from cat.gene_resolutions where accession in ('Q9QXJ1', 'Q9Z223') "
                           "and gene_id is not null").fetchone()[0] == 0


def test_pxreprise_26_bridge_as_sent_in_023_to_pxreprise():
    """023-logs reviewed smith-chem-wisc/PXReprise#26 (PXR-O14) by re-running its protein_orthologs SQL, word for word
    at a3195c166, on aging's catalog 4e486c3dcf0aa01c (v1 resolutions). 811 held accessions have a no-gene row and an
    Ensembl-xref gene row, so the bridge answers 1,622 (accession, target species) pairs both `no_gene` and with a gene.
    Widening partners to every searched database's accessions would fill 21 of 18,670 empty partner rows."""
    r = json.loads((RESULTS / "catalog_bridge_review_4e486c3dcf0aa01c.json").read_text(encoding="utf-8"))
    b = r["bridge"]
    assert (r["pr_head"][:9], r["snapshot"]["artefact_id"], r["snapshot"]["manifest_matches_registration"]) == (
        "a3195c166", "0fe30fe8d4edc728", True)
    assert b["definition_ids"] == {"logs:DEF-GENE-RESOLUTION v1": 42}
    assert (b["rows"], b["accessions"], b["rows_equal_distinct_keys"], b["protein_index_duplicate_accessions"]) == (
        182580, 64211, True, 0)
    assert {k: v["rows"] for k, v in b["status"].items()} == {
        "has_ortholog": 155058, "no_gene": 13754, "tree_lacks_target_species": 7185,
        "no_edge_in_shared_tree": 5535, "not_in_any_tree": 1048}
    assert (b["not_in_gene_set_rows"], b["genes_in_every_direction"]) == (0, True)
    assert [(g[0], g[5], g[2]) for g in b["gfap"]] == [
        ("mus_musculus", "P03995", "ortholog_one2one"), ("rattus_norvegicus", "P47819", "ortholog_one2one")]
    assert (b["held_accessions_no_gene_row_and_gene_row"], b["bridge_pairs_no_gene_and_a_gene"]) == (811, 1622)
    assert b["their_gene_rows_by_source"] == {"ensembl_xref": 811}
    assert b["their_outcomes"] == {"not_in_source": 282, "off_primary_only": 529}
    assert ["A0A0G2K2P5", "not_in_source", "ENSRNOG00000011077", "ensembl_xref"] in b["examples"]
    with_gene = {k: v for k, v in b["no_gene_outcomes_by_status"].items() if not k.endswith("|no_gene")}
    assert sum(with_gene.values()) == 1801, "rows whose outcome links no gene, followed through Ensembl's gene"
    assert (b["partner_rows_by_outcome"]["not_in_source"], b["partner_rows_by_outcome"]["off_primary_only"]) == (608, 1058)
    assert b["ortholog_rows_no_partner_accession"] == 18670
    assert b["of_which_a_searched_database_holds_an_accession"] == {"rows": 21, "partner_genes": 13}


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
