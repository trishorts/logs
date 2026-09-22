"""Streaming loaders for the pinned inputs.

The homology dumps are ~110 MB gzipped each and expand to several GB, so everything here
streams and filters as it reads. Nothing loads a whole file into memory.
"""

from __future__ import annotations

import csv
import gzip
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from . import sources
from .fetch import data_dir

# ---------------------------------------------------------------------------------------------
# Gene sets (from GTF)
# ---------------------------------------------------------------------------------------------

_GENE_ID = re.compile(rb'gene_id "([^"]+)"')
_BIOTYPE = re.compile(rb'gene_biotype "([^"]+)"')


def load_gene_set(species: str) -> dict[str, str]:
    """``ENSG -> gene_biotype`` for every gene in this release's annotation.

    This is the denominator. Without it, *"the source never attempted a call"* and *"no such
    gene"* are indistinguishable -- the empty-vs-unknown collapse we promised to avoid.
    """
    assembly = sources.ASSEMBLY[species]
    path = data_dir() / f"{species.capitalize()}.{assembly}.{sources.RELEASE}.gtf.gz"
    genes: dict[str, str] = {}
    with gzip.open(path, "rb") as fh:
        for line in fh:
            if line.startswith(b"#"):
                continue
            # column 3 is the feature type; only 'gene' rows carry the gene-level biotype
            parts = line.split(b"\t", 3)
            if len(parts) < 3 or parts[2] != b"gene":
                continue
            m = _GENE_ID.search(line)
            if not m:
                continue
            b = _BIOTYPE.search(line)
            genes[m.group(1).decode()] = b.group(1).decode() if b else "unknown"
    return genes


_GENE_NAME = re.compile(rb'gene_name "([^"]+)"')


@dataclass(frozen=True)
class GeneInfo:
    biotype: str
    #: Display label only -- never a key. ``None`` when the GTF carries no ``gene_name``, which
    #: is common for novel lncRNAs and is not the same as an empty string.
    symbol: str | None


def load_genes(species: str) -> dict[str, GeneInfo]:
    """``ENSG -> GeneInfo`` for the primary-assembly gene set: :func:`load_gene_set` plus symbols.

    Kept separate so the denominator used by every measurement already sent to a partner is
    produced by exactly the code that produced it.
    """
    assembly = sources.ASSEMBLY[species]
    path = data_dir() / f"{species.capitalize()}.{assembly}.{sources.RELEASE}.gtf.gz"
    genes: dict[str, GeneInfo] = {}
    with gzip.open(path, "rb") as fh:
        for line in fh:
            if line.startswith(b"#"):
                continue
            parts = line.split(b"\t", 3)
            if len(parts) < 3 or parts[2] != b"gene":
                continue
            m = _GENE_ID.search(line)
            if not m:
                continue
            b = _BIOTYPE.search(line)
            n = _GENE_NAME.search(line)
            genes[m.group(1).decode()] = GeneInfo(
                biotype=b.group(1).decode() if b else "unknown",
                symbol=n.group(1).decode() if n else None,
            )
    return genes


# ---------------------------------------------------------------------------------------------
# Gene trees
# ---------------------------------------------------------------------------------------------

@dataclass
class TreeIndex:
    """Which tree each gene sits in, and which of our taxa each tree contains."""

    tree_of_gene: dict[str, str] = field(default_factory=dict)
    species_in_tree: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))

    def tree_contains(self, tree_id: str, species: str) -> bool:
        return species in self.species_in_tree.get(tree_id, ())


def load_tree_index(gene_species: dict[str, str]) -> TreeIndex:
    """Read the gene-tree content dump, keeping only genes of our taxa.

    ``gene_species`` maps ``ENSG -> species`` for every gene in our three gene sets. Genes from
    the other ~200 vertebrates in the file are skipped: we only need to know whether a tree
    contains a human, mouse or rat gene.

    Having this file is what lets us honour the locked constraint against deriving groups by
    transitive closure -- a tree id is a grouping *the source asserts*, not one we infer from
    pairwise edges.
    """
    idx = TreeIndex()
    path = data_dir() / f"vertebrates.GeneTree_content.default.e{sources.RELEASE}.txt.gz"
    with gzip.open(path, "rt", encoding="utf-8", newline="") as fh:
        for row in csv.reader(fh, delimiter="\t"):
            if len(row) < 3:
                continue
            tree_id, gene_id = row[0], row[2]
            sp = gene_species.get(gene_id)
            if sp is None:
                continue
            idx.tree_of_gene[gene_id] = tree_id
            idx.species_in_tree[tree_id].add(sp)
    return idx


# ---------------------------------------------------------------------------------------------
# Homologies
# ---------------------------------------------------------------------------------------------

HOMOLOGY_COLUMNS = (
    "gene_stable_id", "protein_stable_id", "species", "identity", "homology_type",
    "homology_gene_stable_id", "homology_protein_stable_id", "homology_species",
    "homology_identity", "dn", "ds", "goc_score", "wga_coverage", "is_high_confidence",
    "homology_id",
)


@dataclass(frozen=True, slots=True)
class Homology:
    gene_a: str
    species_a: str
    gene_b: str
    species_b: str
    homology_type: str
    identity_a: float | None
    identity_b: float | None
    goc_score: float | None
    wga_coverage: float | None
    is_high_confidence: bool | None
    homology_id: str
    #: Which genome-specific dump this row came from. Kept because the allocation of a homology
    #: to one file or the other is *arbitrary* and load-bearing: measuring it is what proves the
    #: union is necessary rather than merely recommended.
    source_file: str = ""


def _num(v: str) -> float | None:
    if v in ("", "NULL", "\\N"):
        return None
    try:
        return float(v)
    except ValueError:
        return None


def _bool(v: str) -> bool | None:
    """``is_high_confidence`` is NULL for many rows -- that is *the source declining to say*.

    It must not collapse to False. A refusal to qualify a call and a call qualified as
    low-confidence are different statements, and only one of them is evidence.
    """
    if v in ("", "NULL", "\\N"):
        return None
    return v not in ("0", "false", "False")


def iter_homologies(paths: list[Path], keep_species: set[str]) -> Iterator[Homology]:
    """Stream homologies whose *both* ends are in ``keep_species``.

    Reads every supplied file. Per the provider's README, a genome-specific file holds only an
    arbitrary subset of that genome's orthologies, so all three taxa must be read and unioned;
    the caller deduplicates on ``homology_id``.
    """
    for path in paths:
        with gzip.open(path, "rt", encoding="utf-8", newline="") as fh:
            header = next(fh).rstrip("\n").split("\t")
            if tuple(header) != HOMOLOGY_COLUMNS:
                raise RuntimeError(
                    f"{path.name}: unexpected columns.\n  got:      {header}\n"
                    f"  expected: {list(HOMOLOGY_COLUMNS)}\n"
                    "The dump's layout changed; re-read the README before trusting any count."
                )
            # Plain split rather than csv.reader: these dumps are unquoted TSV and this is ~2x
            # faster over tens of millions of rows. The header check above is what makes it safe.
            for line in fh:
                row = line.rstrip("\n").split("\t")
                if len(row) != 15:
                    continue
                if row[2] not in keep_species or row[7] not in keep_species:
                    continue
                yield Homology(
                    gene_a=row[0], species_a=row[2],
                    gene_b=row[5], species_b=row[7],
                    homology_type=row[4],
                    identity_a=_num(row[3]), identity_b=_num(row[8]),
                    goc_score=_num(row[11]), wga_coverage=_num(row[12]),
                    is_high_confidence=_bool(row[13]),
                    homology_id=row[14],
                    source_file=path.name,
                )


def homology_paths() -> list[Path]:
    return [data_dir() / sf.local_name for sf in sources.homology_files()]
