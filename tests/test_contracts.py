"""Tests for the contracts that carry meaning, not the code that merely runs.

Each test here pins a distinction that, if it collapsed, would produce a confidently wrong
answer rather than an error. That is the failure mode this project is built to avoid, so it is
the failure mode worth testing.

Run:  python -m pytest tests -q      (or: python tests/test_contracts.py)
"""

from __future__ import annotations

import gzip
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from logs_orthology import sources  # noqa: E402
from logs_orthology.cardinality import _pair_label  # noqa: E402
from logs_orthology.fetch import bsd_sum  # noqa: E402
from logs_orthology.load import HOMOLOGY_COLUMNS, _bool, _num, iter_homologies  # noqa: E402


# ---------------------------------------------------------------------------------------------
# The empty-vs-unknown contract
# ---------------------------------------------------------------------------------------------

def test_null_confidence_is_not_false():
    """`is_high_confidence` NULL means *the source declined to say*.

    Collapsing it to False would turn a refusal to qualify a call into a statement that the call
    is weak. Those are different claims and only one of them is evidence.
    """
    assert _bool("NULL") is None
    assert _bool("") is None
    assert _bool("\\N") is None
    assert _bool("1") is True
    assert _bool("0") is False
    # The distinction that matters: None is not False.
    assert _bool("NULL") is not False


def test_null_numerics_are_none_not_zero():
    """A missing GOC score is not a GOC score of zero."""
    assert _num("NULL") is None
    assert _num("") is None
    assert _num("0") == 0.0
    assert _num("41.5335") == 41.5335
    # The trap: `None == 0` is False, but code that does `float(x or 0)` or `x if x else 0`
    # turns an absent score into a real one. Pin that they stay distinguishable.
    assert _num("NULL") != _num("0")


# ---------------------------------------------------------------------------------------------
# Relationship labelling
# ---------------------------------------------------------------------------------------------

def test_pair_label_distinguishes_absence_from_every_relationship():
    assert _pair_label([]) == "none"
    assert _pair_label(None) == "none"
    assert _pair_label([("G1", "ortholog_one2one", True)]) == "one2one"
    assert _pair_label([("G1", "ortholog_one2many", True),
                        ("G2", "ortholog_one2many", None)]) == "one2many"


def test_pair_label_does_not_hide_a_mixture():
    """A gene whose edges to one species carry *different* types must not reduce to the first.

    Reducing silently is how a one2many becomes a one2one in a report.
    """
    label = _pair_label([("G1", "ortholog_one2one", True),
                         ("G2", "ortholog_one2many", True)])
    assert "+" in label
    assert label != "one2one"


# ---------------------------------------------------------------------------------------------
# The source vocabulary
# ---------------------------------------------------------------------------------------------

def test_dist_gives_zero_its_own_bucket():
    """Regression: an accession resolving to NO gene must not land in `4+`.

    The original chained conditional had no zero case, so `n == 0` fell through to the final
    `else` — recording "resolved to nothing" as "maximally ambiguous". That is the worst
    available direction for the error, because it inflates exactly the class the design treats
    as a warning sign.
    """
    from logs_orthology.xrefs import _dist

    d = _dist({"a": set(), "b": {"G1"}, "c": {"G1", "G2"}})
    assert d["0"] == 1
    assert d["1"] == 1
    assert d["2"] == 1
    assert d["4+"] == 0


def test_eligible_biotypes_are_more_than_protein_coding():
    """Compara's protein trees also contain IG/TR gene segments.

    Measured on release 116: 279 human, 485 mouse, 511 rat. Restricting the denominator to
    `protein_coding` drops genes the source was willing to consider, which biases every refusal
    rate in the flattering direction.
    """
    assert "protein_coding" in sources.ELIGIBLE_BIOTYPES
    assert "IG_V_gene" in sources.ELIGIBLE_BIOTYPES
    assert "TR_V_gene" in sources.ELIGIBLE_BIOTYPES
    # but not everything -- a lncRNA was never eligible and must not count as a failed lookup
    assert "lncRNA" not in sources.ELIGIBLE_BIOTYPES
    assert "processed_pseudogene" not in sources.ELIGIBLE_BIOTYPES


def test_ortholog_and_paralog_vocabularies_are_disjoint():
    """A paralog must never be counted as an ortholog. They answer different questions."""
    assert not (sources.ORTHOLOG_TYPES & sources.PARALOG_TYPES)
    assert "within_species_paralog" not in sources.ORTHOLOG_TYPES
    assert "ortholog_one2one" in sources.ORTHOLOG_TYPES


# ---------------------------------------------------------------------------------------------
# Checksums
# ---------------------------------------------------------------------------------------------

def test_bsd_sum_matches_a_known_value(tmp_path: Path):
    """Pin the algorithm against a hand-checked case.

    1024 NUL bytes: each byte adds 0 and the rotation of 0 is 0, so the checksum is 0 and the
    file is exactly one 1 KiB block.
    """
    p = tmp_path / "z.bin"
    p.write_bytes(b"\0" * 1024)
    assert bsd_sum(p) == "0 1"

    # One byte over a block boundary must round *up*, not truncate -- an off-by-one here would
    # silently fail every verification against the provider's manifest.
    p2 = tmp_path / "z2.bin"
    p2.write_bytes(b"\0" * 1025)
    assert bsd_sum(p2) == "0 2"

    p3 = tmp_path / "a.bin"
    p3.write_bytes(b"\x01")
    assert bsd_sum(p3) == "1 1"


# ---------------------------------------------------------------------------------------------
# The reader refuses a changed layout
# ---------------------------------------------------------------------------------------------

def test_homology_reader_refuses_unexpected_columns(tmp_path: Path):
    """If the dump's layout changes, fail loudly rather than mis-index every row.

    Positional parsing against a moved column is exactly the defect dataRepo found in their own
    producer. The header check is what stops us repeating it.
    """
    p = tmp_path / "bad.tsv.gz"
    with gzip.open(p, "wt", encoding="utf-8", newline="") as fh:
        fh.write("gene_stable_id\tsomething_else\n")
        fh.write("ENSG1\tx\n")
    try:
        list(iter_homologies([p], {"homo_sapiens"}))
    except RuntimeError as e:
        assert "unexpected columns" in str(e)
    else:
        raise AssertionError("a changed layout must raise, not parse")


def test_homology_reader_accepts_the_pinned_layout(tmp_path: Path):
    p = tmp_path / "ok.tsv.gz"
    row = ["ENSG1", "ENSP1", "homo_sapiens", "90.0", "ortholog_one2one",
           "ENSMUSG1", "ENSMUSP1", "mus_musculus", "88.0", "NULL", "NULL",
           "NULL", "NULL", "NULL", "42"]
    with gzip.open(p, "wt", encoding="utf-8", newline="") as fh:
        fh.write("\t".join(HOMOLOGY_COLUMNS) + "\n")
        fh.write("\t".join(row) + "\n")
        # a row whose far end is out of scope must be dropped
        out = list(row)
        out[7] = "danio_rerio"
        fh.write("\t".join(out) + "\n")

    got = list(iter_homologies([p], {"homo_sapiens", "mus_musculus"}))
    assert len(got) == 1
    h = got[0]
    assert h.gene_a == "ENSG1" and h.gene_b == "ENSMUSG1"
    assert h.homology_type == "ortholog_one2one"
    # NULL confidence survives as None, which is the whole point of the first test in this file.
    assert h.is_high_confidence is None
    assert h.goc_score is None


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
