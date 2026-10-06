"""Accession → stable gene resolution: the deliverable ``aging`` asked for first (REQ-AGING-4).

``xrefs.py`` *measured* this; this module *does* it, row by row, for any list of accessions.

The shape, and why each part of it is there:

* **One row per (accession, gene)**, never one gene per accession. 70 reviewed human accessions
  span more than one primary-assembly gene -- the core histones lead, ``P62805`` spans 14 -- and
  they are abundant in every run. A pick would be wrong exactly where it is most often read.
* **Keyed on the accession, never a display symbol.** The symbol travels beside the ENSG as a
  label. It is what ``aging`` stops reading the producer's ``Gene Name`` column in favour of.
* **Every outcome is typed** (:data:`OUTCOMES`). "We did not look", "the source has nothing", and
  "the source only knows it on an ALT haplotype" are different answers and must not share a null.
* **Restrictions are columns, never modes.** There is no flag that changes what a file contains;
  a consumer filters on ``outcome``, ``info_type`` or ``db_name`` and can see what it dropped.
* **Primary assembly only**, against the pinned GTF. Ensembl's xrefs reference ALT-haplotype and
  patch genes, which inflated the human multi-gene rate twentyfold (6.99% vs 0.36%) the first
  time we counted. That restriction needs the release's gene set, which is why resolution lives
  here and not in mzLib (``design/PLAN.md`` step 5 vs step 7).

**Provisional source.** v1 is meant to read the ``<dbReference>``s out of the search database
itself, keyed on ``(accession, search_database_sha256)``. Until ``aging`` confirms which bytes
their searches used (REQ-AGING-7), this resolves against Ensembl's own cross-reference dump. The
``source`` column says which; the two are to be cross-checked, not merged.

Run:
    python -m logs_orthology.resolve --reference            # every accession Ensembl knows
    python -m logs_orthology.resolve --accessions ids.tsv   # a list: accession[<TAB>contaminant]
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import gzip
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import astuple, dataclass, fields
from pathlib import Path
from typing import Iterable, Iterator

from . import sources
from .fetch import project_root
from .load import GeneInfo, load_genes
from .xrefs import SHORT, iter_xref

SOURCE = "ensembl_xref"

# ---------------------------------------------------------------------------------------------
# Outcomes
# ---------------------------------------------------------------------------------------------

#: Exactly one primary-assembly gene.
RESOLVED = "resolved"
#: More than one primary-assembly gene. One row per gene; ``n_genes`` says how many.
MULTI_GENE = "multi_gene"
#: The source links the accession only to genes outside the primary assembly (ALT haplotypes,
#: patches, scaffolds). Not the same as "no gene": the source has an answer, just not one on the
#: assembly every other row is counted against.
OFF_PRIMARY_ONLY = "off_primary_only"
#: A well-formed UniProt or RefSeq protein accession the source does not know, in this species.
NOT_IN_SOURCE = "not_in_source"
#: Not a shape we recognise, and not in the source either. Kept apart from ``not_in_source`` so a
#: decoy prefix or a mangled id is visible as a data problem rather than as a biology result.
UNRECOGNIZED = "unrecognized_accession"
#: Flagged a contaminant by the producer. Never mapped, even when it would resolve -- and never
#: silently dropped, so "we did not look" stays distinguishable from "there is nothing".
CONTAMINANT = "contaminant_not_mapped"

OUTCOMES = (RESOLVED, MULTI_GENE, OFF_PRIMARY_ONLY, NOT_IN_SOURCE, UNRECOGNIZED, CONTAMINANT)

#: Strongest evidence first. ``DIRECT`` is an assertion by the source; ``SEQUENCE_MATCH`` and
#: ``INFERRED_PAIR`` are inferences. For human RefSeq most links are the latter, so this column is
#: what stops an inference being reported as an assertion. Unknown types rank last, verbatim.
INFO_TYPE_RANK = {"DIRECT": 0, "SEQUENCE_MATCH": 1, "INFERRED_PAIR": 2}

# ---------------------------------------------------------------------------------------------
# Accession normalization
# ---------------------------------------------------------------------------------------------

#: UniProt's published accession grammar, with an optional isoform suffix.
RE_UNIPROT = re.compile(
    r"^([OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2})(?:-(\d+))?$"
)
#: RefSeq protein accessions, with an optional version. Ensembl's dump carries them unversioned.
RE_REFSEQ_PROTEIN = re.compile(r"^((?:NP|XP|YP|WP|AP)_\d+)(?:\.(\d+))?$")
#: mzLib's name for a proteoform with applied sequence variants: the entry's accession, then one
#: ``_{original}{position}{variant}`` token per variant, ordered by position
#: (``VariantApplication.GetAccession`` / ``SequenceVariation.SimpleString``). The original residues
#: are never empty; the variant residues are empty for a deletion. Either side may carry ``*``
#: (stop-gain ``Q5*``, stop-loss ``*70R``), as in mzLib #1382 since 5e323463f.
#: NOT the same as ``_{digits}``: that is ``ProteinDbLoader``'s load-collision counter, naming a
#: *different* entry whose accession collided, and it must never map back to the first entry.
RE_VARIANT_SUFFIX = re.compile(r"^(.+?)((?:_[A-Z*]+\d+[A-Z*]*)+)$")


@dataclass(frozen=True)
class Accession:
    """An accession as given, plus what can be said about it without any reference data.

    ``entry_accession`` is the **entry**, not "the canonical sequence". ``P12345-1`` is not
    necessarily the sequence UniProt displays for ``P12345``: the displayed isoform can carry any
    number. So ``entry_accession`` answers "same UniProt entry?" and nothing about sequence
    identity. Whether an isoform counts as the same protein is the consumer's call per question.
    """

    verbatim: str
    entry_accession: str
    #: UniProt isoform number, or ``None`` for an accession without a suffix.
    isoform: str | None
    #: RefSeq version, or ``None``.
    version: str | None
    namespace: str  # "uniprot" | "refseq" | "unrecognized"
    #: mzLib's applied-variant suffix without its leading ``_`` (``S70N`` or ``S70N_A80T``), or
    #: ``None``. A variant proteoform takes its entry's gene answer (0 of 31,943 differ, 016-logs §2).
    variant: str | None = None


def _parse_base(accession: str) -> Accession | None:
    m = RE_UNIPROT.match(accession)
    if m:
        return Accession(accession, m.group(1), m.group(2), None, "uniprot")
    m = RE_REFSEQ_PROTEIN.match(accession)
    if m:
        return Accession(accession, m.group(1), None, m.group(2), "refseq")
    return None


def normalize(accession: str) -> Accession:
    """Parse, never repair. Anything outside the grammar is ``unrecognized`` and kept verbatim.

    This is also the proteoform-to-entry rule (LOGS-D2): ``P12345_S70N`` is entry ``P12345``. The
    base is matched against a full accession grammar rather than cut at the first ``_``, which would
    break ``NP_000001``. A load-collision counter (``P12345_2``) matches no grammar and stays
    ``unrecognized``, as its own key; so do decoy and entrapment prefixes.
    """
    base = _parse_base(accession)
    if base is not None:
        return base
    m = RE_VARIANT_SUFFIX.match(accession)
    if m:
        base = _parse_base(m.group(1))
        if base is not None:
            return Accession(accession, base.entry_accession, base.isoform, base.version,
                             base.namespace, m.group(2)[1:])
    return Accession(accession, accession, None, None, "unrecognized")


# ---------------------------------------------------------------------------------------------
# The index
# ---------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Link:
    info_type: str
    db_name: str


def _best(links: set[Link]) -> Link:
    return min(links, key=lambda l: (INFO_TYPE_RANK.get(l.info_type, 99), l.info_type, l.db_name))


class XrefIndex:
    """accession → gene → the links the source gave, for one species and one release."""

    def __init__(self, species: str, rows: Iterable[dict], genes: dict[str, GeneInfo]):
        self.species = species
        self.genes = genes
        self.links: dict[str, dict[str, set[Link]]] = defaultdict(lambda: defaultdict(set))
        for r in rows:
            self.links[r["xref"]][r["gene_stable_id"]].add(Link(r["info_type"], r["db_name"]))
        self.links = {a: dict(g) for a, g in self.links.items()}

    @classmethod
    def from_ensembl(cls, species: str) -> "XrefIndex":
        def rows() -> Iterator[dict]:
            yield from iter_xref(species, "uniprot")
            # Protein accessions only: RefSeq_mRNA / ncRNA ids are not what a search reports.
            for r in iter_xref(species, "refseq"):
                if r["db_name"].startswith("RefSeq_peptide"):
                    yield r
        return cls(species, rows(), load_genes(species))

    def accessions(self) -> list[str]:
        return sorted(self.links)


# ---------------------------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Resolution:
    species: str
    taxon: int
    accession: str
    entry_accession: str
    isoform: str | None
    namespace: str
    #: How the accession met the source: ``exact``, ``entry`` (isoform suffix dropped to reach
    #: the entry), ``unversioned`` (RefSeq version dropped), or ``None`` if it never did.
    matched_on: str | None
    outcome: str
    #: Primary-assembly genes for this accession -- the same on every row of a multi-gene group.
    n_genes: int
    gene_id: str | None
    gene_symbol: str | None
    gene_biotype: str | None
    info_type: str | None
    db_name: str | None
    #: Off-primary genes the source also named and we did not emit. Visible, not corrected away.
    off_primary_genes: int
    source: str
    release: str


def _row(idx: XrefIndex, acc: Accession, matched_on, outcome, n_genes=0, gene=None,
         link: Link | None = None, off_primary=0) -> Resolution:
    info = idx.genes.get(gene) if gene else None
    return Resolution(
        species=idx.species, taxon=sources.TAXON_BY_SPECIES[idx.species],
        accession=acc.verbatim, entry_accession=acc.entry_accession, isoform=acc.isoform,
        namespace=acc.namespace, matched_on=matched_on, outcome=outcome, n_genes=n_genes,
        gene_id=gene, gene_symbol=info.symbol if info else None,
        gene_biotype=info.biotype if info else None,
        info_type=link.info_type if link else None, db_name=link.db_name if link else None,
        off_primary_genes=off_primary, source=SOURCE, release=sources.RELEASE,
    )


def resolve(idx: XrefIndex, accession: str, *, contaminant: bool = False) -> list[Resolution]:
    """Every row for one accession. Never empty: an accession always gets at least one outcome."""
    acc = normalize(accession)
    if contaminant:
        return [_row(idx, acc, None, CONTAMINANT)]

    matched_on, links = None, None
    if accession in idx.links:
        matched_on, links = "exact", idx.links[accession]
    elif acc.entry_accession != accession and acc.entry_accession in idx.links:
        matched_on = "entry" if acc.namespace == "uniprot" else "unversioned"
        links = idx.links[acc.entry_accession]

    if links is None:
        return [_row(idx, acc, None, UNRECOGNIZED if acc.namespace == "unrecognized"
                     else NOT_IN_SOURCE)]

    primary = sorted(g for g in links if g in idx.genes)
    off = len(links) - len(primary)
    if not primary:
        # No gene to emit, but the link still says what kind of accession this is and how the
        # source knew it -- without it a reviewed entry would be indistinguishable from TrEMBL.
        best = _best({l for ls in links.values() for l in ls})
        return [_row(idx, acc, matched_on, OFF_PRIMARY_ONLY, link=best, off_primary=off)]
    outcome = RESOLVED if len(primary) == 1 else MULTI_GENE
    return [_row(idx, acc, matched_on, outcome, len(primary), g, _best(links[g]), off)
            for g in primary]


def resolve_all(idx: XrefIndex, items: Iterable[tuple[str, bool]]) -> Iterator[Resolution]:
    for accession, contaminant in items:
        yield from resolve(idx, accession, contaminant=contaminant)


# ---------------------------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------------------------

COLUMNS = tuple(f.name for f in fields(Resolution))


def write_tsv(rows: Iterable[Resolution], path: Path) -> int:
    """Nulls are empty cells. Every null row still carries an ``outcome`` saying why."""
    path.parent.mkdir(parents=True, exist_ok=True)
    opener = gzip.open if path.suffix == ".gz" else open
    n = 0
    with opener(path, "wt", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(COLUMNS)
        for r in rows:
            w.writerow("" if v is None else v for v in astuple(r))
            n += 1
    return n


_TRUE = {"1", "true", "yes", "y", "t"}
_FALSE = {"", "0", "false", "no", "n", "f"}


def read_accessions(path: Path) -> Iterator[tuple[str, bool]]:
    """``accession[<TAB>contaminant]`` per line; ``#`` comments and blank lines skipped.

    An unreadable contaminant flag is an error, not a False: guessing "not a contaminant" would
    map through orthology exactly the entries the rule says must never be mapped.
    """
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            line = line.rstrip("\r\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            flag = parts[1].strip().lower() if len(parts) > 1 else ""
            if flag not in _TRUE | _FALSE:
                raise ValueError(f"{path}:{n}: contaminant flag {parts[1]!r} is not a boolean")
            yield parts[0], flag in _TRUE


def db_class(r: Resolution) -> str:
    """Coarse evidence class for the summary. Derived from the source's own db_name."""
    if r.namespace == "refseq":
        return "refseq_" + ("NP" if r.entry_accession.startswith("NP_") else
                            "XP" if r.entry_accession.startswith("XP_") else "other")
    return {"Uniprot/SWISSPROT": "uniprot_reviewed", "Uniprot_isoform": "uniprot_isoform",
            "Uniprot/SPTREMBL": "uniprot_unreviewed"}.get(r.db_name or "", "uniprot_no_link")


def summarize(rows: list[Resolution]) -> dict:
    """Per accession, not per row: a 14-gene histone is one accession with one outcome."""
    per_acc: dict[str, Resolution] = {}
    for r in rows:
        per_acc.setdefault(r.accession, r)
    by_class: dict[str, Counter] = defaultdict(Counter)
    info_by_class: dict[str, Counter] = defaultdict(Counter)
    matched: Counter = Counter()
    for r in per_acc.values():
        by_class[db_class(r)][r.outcome] += 1
        matched[r.matched_on or "none"] += 1
    for r in rows:
        if r.info_type:
            info_by_class[db_class(r)][r.info_type] += 1
    return {
        "accessions": len(per_acc),
        "rows": len(rows),
        "outcomes": dict(Counter(r.outcome for r in per_acc.values())),
        "outcomes_by_class": {k: dict(v) for k, v in sorted(by_class.items())},
        "matched_on": dict(matched),
        #: Per emitted row, i.e. per (accession, gene), using the strongest link for that pair.
        #: Not comparable with xref-dump row counts, which are per transcript.
        "info_type_by_class": {k: dict(v) for k, v in sorted(info_by_class.items())},
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Resolve protein accessions to stable gene ids.")
    ap.add_argument("--species", default="homo_sapiens", choices=sorted(sources.TAXA))
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--reference", action="store_true",
                     help="resolve every accession the source knows, and summarize")
    src.add_argument("--accessions", type=Path, help="accession[<TAB>contaminant] per line")
    ap.add_argument("--out", type=Path, help="output .tsv or .tsv.gz")
    args = ap.parse_args(argv)

    print(f"indexing {SOURCE} {sources.RELEASE} for {args.species}...")
    idx = XrefIndex.from_ensembl(args.species)
    short = SHORT[args.species]

    if args.accessions:
        out = args.out or args.accessions.with_suffix(".resolved.tsv")
        n = write_tsv(resolve_all(idx, read_accessions(args.accessions)), out)
        print(f"wrote {n:,} rows -> {out}")
        return 0

    rows = list(resolve_all(idx, ((a, False) for a in idx.accessions())))
    stem = project_root() / "results" / f"resolution_{short}_e{sources.RELEASE}"
    out = args.out or stem.with_suffix(".tsv.gz")
    write_tsv(rows, out)
    report = {"source": SOURCE, "release": sources.RELEASE, "species": args.species,
              "generated": _dt.date.today().isoformat(), **summarize(rows)}
    stem.with_suffix(".json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"wrote {len(rows):,} rows -> {out}\n      {stem.with_suffix('.json')}")
    print(json.dumps(report["outcomes_by_class"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
