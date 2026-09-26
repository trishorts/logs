"""Contracts for accession -> gene resolution (``logs_orthology.resolve``).

As in ``test_contracts.py``, each test pins a distinction that would otherwise collapse into a
confidently wrong answer: an isoform read as the canonical sequence, a contaminant mapped, an ALT
haplotype counted as a second gene, an inference reported as an assertion.

The last test reconciles the resolver against ``xrefs.py``'s independent measurement on the real
pinned data, and is skipped when the data is absent.

Run:  python tests/test_resolve.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from logs_orthology import resolve as R  # noqa: E402
from logs_orthology.load import GeneInfo  # noqa: E402

GENES = {
    "ENSG_A": GeneInfo("protein_coding", "GENEA"),
    "ENSG_B": GeneInfo("protein_coding", "GENEB"),
    "ENSG_C": GeneInfo("protein_coding", None),
}


def _x(acc, gene, info="DIRECT", db="Uniprot/SWISSPROT"):
    return {"xref": acc, "gene_stable_id": gene, "info_type": info, "db_name": db}


def _idx(*rows):
    return R.XrefIndex("homo_sapiens", rows, GENES)


# ---------------------------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------------------------

def test_isoform_is_split_from_entry_not_equated_with_canonical():
    """``-1`` is an isoform number, not "the canonical sequence" -- UniProt displays any isoform."""
    a = R.normalize("P12345-1")
    assert (a.entry_accession, a.isoform, a.namespace) == ("P12345", "1", "uniprot")
    assert a.verbatim == "P12345-1"
    assert R.normalize("P12345").isoform is None


def test_refseq_version_is_split_off():
    a = R.normalize("NP_000537.3")
    assert (a.entry_accession, a.version, a.namespace) == ("NP_000537", "3", "refseq")


def test_normalize_parses_and_never_repairs():
    """A prefixed or lower-cased id is a data problem to surface, not one to fix silently."""
    for bad in ("CON__P02768", "p12345", " P12345", "sp|P12345|X_HUMAN", "DECOY_P12345"):
        a = R.normalize(bad)
        assert a.namespace == "unrecognized" and a.entry_accession == bad


def test_variant_proteoform_maps_to_its_entry():
    """LOGS-D2 (dataRepo 018 §1): mzLib names an applied-variant proteoform ``{entry}_{SimpleString}``,
    one token per variant, ordered by position."""
    for acc, entry, variant in (("O14994_S470N", "O14994", "S470N"),
                                ("P12345_S70N_A80T", "P12345", "S70N_A80T"),
                                ("P12345_AB70", "P12345", "AB70"),          # a deletion
                                ("P12345_T70TAG", "P12345", "T70TAG")):     # an anchored insertion
        a = R.normalize(acc)
        assert (a.entry_accession, a.variant, a.namespace, a.verbatim) == (entry, variant, "uniprot", acc)
    a = R.normalize("P12345-2_S70N")
    assert (a.entry_accession, a.isoform, a.variant) == ("P12345", "2", "S70N")
    assert R.normalize("P12345").variant is None


def test_load_collision_counter_is_never_mapped_to_the_first_entry():
    """dataRepo 018 §1: ``P12345_2`` is ProteinDbLoader's counter for a *different* entry whose
    accession collided. Mapping it to ``P12345`` would give it another protein's genes."""
    for acc in ("P12345_2", "P12345_10", "P12345_S70N_2", "NP_000537_2"):
        a = R.normalize(acc)
        assert (a.namespace, a.entry_accession, a.variant) == ("unrecognized", acc, None), acc
    rows = R.resolve(_idx(_x("P11111", "ENSG_A")), "P11111_2")
    assert [r.outcome for r in rows] == [R.UNRECOGNIZED]


def test_refseq_underscore_is_not_a_variant_suffix():
    """"Text before the first ``_``" would turn ``NP_000537`` into ``NP``."""
    a = R.normalize("NP_000537.3_R72P")
    assert (a.entry_accession, a.version, a.variant, a.namespace) == ("NP_000537", "3", "R72P", "refseq")
    assert R.normalize("NP_000537").variant is None


def test_decoy_and_entrapment_prefixes_stay_unrecognized():
    for acc in ("DECOY_P12345", "DECOY_P12345_S70N", "Random_P12345", "DECOY_Random_P12345"):
        assert R.normalize(acc).namespace == "unrecognized", acc


def test_variant_resolves_through_its_entry():
    rows = R.resolve(_idx(_x("P11111", "ENSG_A")), "P11111_S70N")
    assert [(r.accession, r.entry_accession, r.matched_on, r.outcome, r.gene_id) for r in rows] == \
        [("P11111_S70N", "P11111", "entry", R.RESOLVED, "ENSG_A")]


# ---------------------------------------------------------------------------------------------
# Outcomes
# ---------------------------------------------------------------------------------------------

def test_every_accession_gets_at_least_one_row():
    idx = _idx(_x("P11111", "ENSG_A"))
    for acc in ("P11111", "P99999", "garbage", "NP_1.1"):
        rows = R.resolve(idx, acc)
        assert rows and all(r.outcome in R.OUTCOMES for r in rows)


def test_multi_gene_is_one_row_per_gene_never_a_pick():
    rows = R.resolve(_idx(_x("P11111", "ENSG_B"), _x("P11111", "ENSG_A")), "P11111")
    assert [r.gene_id for r in rows] == ["ENSG_A", "ENSG_B"]
    assert {r.outcome for r in rows} == {R.MULTI_GENE}
    assert {r.n_genes for r in rows} == {2}


def test_off_primary_genes_do_not_count_as_extra_genes():
    """The ALT-haplotype trap: one locus on many haplotypes is one gene, not twenty."""
    rows = R.resolve(_idx(_x("P11111", "ENSG_A"), _x("P11111", "ENSG_ALT1"),
                          _x("P11111", "ENSG_ALT2")), "P11111")
    assert len(rows) == 1 and rows[0].outcome == R.RESOLVED and rows[0].gene_id == "ENSG_A"
    assert rows[0].off_primary_genes == 2, "dropped, but visibly"


def test_off_primary_only_is_not_not_in_source_and_keeps_its_evidence():
    (r,) = R.resolve(_idx(_x("P11111", "ENSG_ALT1")), "P11111")
    assert r.outcome == R.OFF_PRIMARY_ONLY and r.gene_id is None
    assert r.db_name == "Uniprot/SWISSPROT", "reviewed must stay distinguishable from TrEMBL"
    assert r.off_primary_genes == 1


def test_contaminant_is_never_mapped_even_when_it_would_resolve():
    (r,) = R.resolve(_idx(_x("P02768", "ENSG_A")), "P02768", contaminant=True)
    assert r.outcome == R.CONTAMINANT and r.gene_id is None


def test_not_in_source_and_unrecognized_are_different_outcomes():
    idx = _idx(_x("P11111", "ENSG_A"))
    assert R.resolve(idx, "Q99999")[0].outcome == R.NOT_IN_SOURCE
    assert R.resolve(idx, "DECOY_P11111")[0].outcome == R.UNRECOGNIZED


def test_exact_isoform_beats_entry_and_fallback_is_recorded():
    idx = _idx(_x("P11111-2", "ENSG_A", db="Uniprot_isoform"), _x("P11111", "ENSG_B"))
    (exact,) = R.resolve(idx, "P11111-2")
    assert (exact.gene_id, exact.matched_on) == ("ENSG_A", "exact")
    (fallback,) = R.resolve(idx, "P11111-3")
    assert (fallback.gene_id, fallback.matched_on) == ("ENSG_B", "entry")
    assert fallback.accession == "P11111-3", "the verbatim accession is never rewritten"


def test_refseq_versioned_input_meets_unversioned_source():
    (r,) = R.resolve(_idx(_x("NP_000001", "ENSG_A", db="RefSeq_peptide")), "NP_000001.4")
    assert (r.outcome, r.matched_on) == (R.RESOLVED, "unversioned")


def test_strongest_link_wins_per_pair_and_inference_is_not_upgraded():
    idx = _idx(_x("NP_1", "ENSG_A", "SEQUENCE_MATCH", "RefSeq_peptide"),
               _x("NP_1", "ENSG_A", "DIRECT", "RefSeq_peptide"),
               _x("NP_2", "ENSG_B", "INFERRED_PAIR", "RefSeq_peptide"))
    assert R.resolve(idx, "NP_1")[0].info_type == "DIRECT"
    assert R.resolve(idx, "NP_2")[0].info_type == "INFERRED_PAIR"


def test_missing_symbol_is_none_not_empty_string():
    assert R.resolve(_idx(_x("P11111", "ENSG_C")), "P11111")[0].gene_symbol is None


def test_unreadable_contaminant_flag_is_an_error_not_false(tmp_path: Path):
    p = tmp_path / "ids.tsv"
    p.write_text("P11111\ttrue\nP22222\n# comment\nP33333\tmaybe\n", encoding="utf-8")
    it = R.read_accessions(p)
    assert next(it) == ("P11111", True)
    assert next(it) == ("P22222", False)
    try:
        next(it)
    except ValueError:
        pass
    else:
        raise AssertionError("'maybe' must not be read as 'not a contaminant'")


def test_tsv_round_trip_keeps_nulls_as_empty_cells(tmp_path: Path):
    p = tmp_path / "out.tsv"
    R.write_tsv(R.resolve(_idx(), "Q99999"), p)
    header, row = p.read_text(encoding="utf-8").splitlines()
    cells = dict(zip(header.split("\t"), row.split("\t")))
    assert cells["outcome"] == R.NOT_IN_SOURCE and cells["gene_id"] == ""


# ---------------------------------------------------------------------------------------------
# Reconciliation with the independent measurement (real data)
# ---------------------------------------------------------------------------------------------

def test_resolver_reproduces_the_measured_reviewed_human_numbers():
    """Two code paths, one answer: 19,383 reviewed = 19,251 resolved + 70 multi + 62 off-primary.

    ``xrefs.py`` counted these; the resolver emits them row by row. If they ever disagree, one of
    them is wrong and the numbers already sent in 007-logs and 003-logs are in question.
    """
    from logs_orthology.xrefs import xref_path
    if not xref_path("homo_sapiens", "uniprot").exists():
        print("    (skipped: pinned Ensembl data not present)")
        return
    idx = R.XrefIndex.from_ensembl("homo_sapiens")
    rows = list(R.resolve_all(idx, ((a, False) for a in idx.accessions())))
    s = R.summarize(rows)["outcomes_by_class"]["uniprot_reviewed"]
    assert s == {R.RESOLVED: 19251, R.MULTI_GENE: 70, R.OFF_PRIMARY_ONLY: 62}
    h4 = [r for r in rows if r.accession == "P62805"]
    assert len(h4) == 14 and {r.outcome for r in h4} == {R.MULTI_GENE}


if __name__ == "__main__":
    import traceback

    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    tmp = Path(__file__).resolve().parent / "_tmp"
    tmp.mkdir(exist_ok=True)
    failed = 0
    for fn in fns:
        try:
            fn(tmp) if fn.__code__.co_argcount else fn()
            print(f"  PASS  {fn.__name__}")
        except Exception:
            failed += 1
            print(f"  FAIL  {fn.__name__}")
            traceback.print_exc()
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
