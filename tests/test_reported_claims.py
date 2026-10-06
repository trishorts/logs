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
