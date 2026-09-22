"""Release-pinned Ensembl Compara sources.

Every relationship this project stores must carry the source and release it came from, so a
snapshot can be *compared* with a later one rather than silently overwritten. That starts here:
the inputs are pinned to a release, fetched from a fixed URL, and verified against the MD5 the
provider publishes alongside them.

Nothing in this module talks to the network. `fetch.py` does that.
"""

from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------------------------
# The pin. Bump this deliberately, as a reviewed change, and expect a new snapshot -- never an
# in-place update of an existing one.
# ---------------------------------------------------------------------------------------------

SOURCE = "ensembl_compara"
RELEASE = "116"

FTP_BASE = f"https://ftp.ensembl.org/pub/release-{RELEASE}"
HOMOLOGY_BASE = f"{FTP_BASE}/tsv/ensembl-compara/homologies"

USER_AGENT = "logs-orthology/0.1 (UW-Madison Smith lab; research; cross-species orthology)"

# MVP taxa, confirmed by the user 2026-09-22 and matching dataRepo's D5 scope.
# Ensembl production names -> NCBI taxonomy id.
TAXA: dict[str, int] = {
    "homo_sapiens": 9606,
    "mus_musculus": 10090,
    "rattus_norvegicus": 10116,
}

#: Assembly name as it appears in this release's filenames. Part of the pin: an assembly change
#: is at least as significant as a release change and must not pass unnoticed.
ASSEMBLY: dict[str, str] = {
    "homo_sapiens": "GRCh38",
    "mus_musculus": "GRCm39",
    "rattus_norvegicus": "GRCr8",
}

TAXON_BY_SPECIES = dict(TAXA)
SPECIES_BY_TAXON = {v: k for k, v in TAXA.items()}


@dataclass(frozen=True)
class SourceFile:
    """One pinned input file."""

    key: str
    url: str
    #: Path of the provider's MD5 manifest, relative to nothing -- a full URL.
    md5_manifest: str
    #: The name this file is listed under inside that manifest.
    md5_name: str
    #: Local filename under data/compara/.
    local_name: str
    description: str


def homology_files() -> list[SourceFile]:
    """The per-genome protein homology dumps, one per taxon.

    **Why all three and not just human.** The provider's README is explicit:

        To eliminate redundancy, each genome-specific homology TSV file contains an arbitrary
        subset of orthologies involving the given genome. To access all available orthologies
        between two genomes ... you will need to download the genome-specific files of both
        genomes.

    So the human file alone does *not* contain every human-mouse orthology. Taking it alone
    would undercount silently -- the result would look complete and be wrong, which is the
    failure mode this project exists to avoid. We take all three and union them.
    """
    out: list[SourceFile] = []
    for species in TAXA:
        name = f"Compara.{RELEASE}.protein_default.homologies.tsv.gz"
        out.append(
            SourceFile(
                key=f"homology:{species}",
                url=f"{HOMOLOGY_BASE}/{species}/{name}",
                md5_manifest=f"{HOMOLOGY_BASE}/{species}/MD5SUM",
                md5_name=name,
                local_name=f"{species}.protein_default.homologies.tsv.gz",
                description=(
                    f"Pairwise protein homologies involving {species}, gene-tree collection "
                    f"'default', Ensembl Compara release {RELEASE}."
                ),
            )
        )
    return out


def gene_tree_file() -> SourceFile:
    """Gene-tree membership: which genes belong to which Compara gene tree.

    This is the *orthogroup* source, and having it is what lets us keep our locked constraint
    against deriving groups by transitive closure over pairwise edges. A gene tree id
    (``ENSGT...``) is a group the source asserts; it is not something we infer.

    Columns (no header): ``tree_id, protein_stable_id, gene_stable_id, is_canonical``.
    """
    name = f"vertebrates.GeneTree_content.default.e{RELEASE}.txt.gz"
    return SourceFile(
        key="gene_tree_content",
        url=f"{FTP_BASE}/compara/{name}",
        md5_manifest="",  # not published in compara/CHECKSUMS for this file -- see fetch.py
        md5_name=name,
        local_name=name,
        description=(
            f"Gene-tree membership for the vertebrates 'default' collection, Ensembl Compara "
            f"release {RELEASE}. tree_id / protein_stable_id / gene_stable_id / is_canonical."
        ),
    )


def gtf_files() -> list[SourceFile]:
    """Per-species GTF -- the authoritative gene set for this release, with biotypes.

    Needed for two things the homology dump cannot tell us on its own:

    * **The denominator.** A gene absent from every Compara gene tree is only interesting if we
      know it exists in the release at all. Without the gene set, "no call was ever attempted"
      and "no such gene" are indistinguishable -- the empty-vs-unknown failure in the exact
      place we promised dataRepo we would keep them apart.
    * **Biotype.** The ``protein_default`` collection contains only protein-coding genes. A
      lncRNA with no ortholog is an artefact of which collection we read, not a finding about
      conservation. Reporting the two together would inflate the refusal classes with genes that
      were never eligible.
    """
    out: list[SourceFile] = []
    for species, assembly in ASSEMBLY.items():
        name = f"{assembly}.{RELEASE}.gtf.gz"
        # Ensembl capitalises the species in GTF filenames: Homo_sapiens.GRCh38.116.gtf.gz
        fname = f"{species.capitalize()}.{name}"
        out.append(
            SourceFile(
                key=f"gtf:{species}",
                url=f"{FTP_BASE}/gtf/{species}/{fname}",
                md5_manifest=f"{FTP_BASE}/gtf/{species}/CHECKSUMS",
                md5_name=fname,
                local_name=fname,
                description=f"Gene annotation for {species} ({assembly}), Ensembl {RELEASE}.",
            )
        )
    return out


#: Cross-reference dumps: Ensembl stable id -> external accession. Small (2-6 MB each).
XREF_KINDS = ("uniprot", "refseq", "entrez")


def xref_files() -> list[SourceFile]:
    """Ensembl's own stable-id -> external-accession dumps.

    These matter beyond orthology. They are an **independent route** to accession -> gene, and a
    cross-check on the cross-references a UniProt XML carries: if the two disagree for an
    accession, that is a finding, not noise.

    ``refseq`` is the notable one. We told dataRepo that RefSeq protein accessions were
    unrecoverable and deferred them to v3, on the grounds that mzLib recognises no ``NP_``/``XP_``
    FASTA header. That reasoning was about *parsing a header*; it does not apply to resolving an
    accession we already hold, which this file does directly. Re-measure before repeating the
    claim.
    """
    out: list[SourceFile] = []
    for species, assembly in ASSEMBLY.items():
        for kind in XREF_KINDS:
            fname = f"{species.capitalize()}.{assembly}.{RELEASE}.{kind}.tsv.gz"
            out.append(
                SourceFile(
                    key=f"xref:{kind}:{species}",
                    url=f"{FTP_BASE}/tsv/{species}/{fname}",
                    md5_manifest=f"{FTP_BASE}/tsv/{species}/CHECKSUMS",
                    md5_name=fname,
                    local_name=fname,
                    description=(
                        f"Ensembl stable id -> {kind} accession for {species} ({assembly}), "
                        f"release {RELEASE}."
                    ),
                )
            )
    return out


def all_files() -> list[SourceFile]:
    return [*homology_files(), gene_tree_file(), *gtf_files(), *xref_files()]


# ---------------------------------------------------------------------------------------------
# Relationship vocabulary, kept verbatim from the source.
# ---------------------------------------------------------------------------------------------

#: Compara's ``homology_type`` values that are orthologies (between species).
ORTHOLOG_TYPES = frozenset(
    {"ortholog_one2one", "ortholog_one2many", "ortholog_many2many"}
)

#: Values that are paralogies (within a species, or gene-duplication derived).
PARALOG_TYPES = frozenset(
    {"within_species_paralog", "other_paralog", "gene_split"}
)

#: Values seen that are neither -- kept so an unexpected one is loud rather than silently
#: dropped. Populated defensively; the loader reports anything outside the union.
HOMOEOLOG_TYPES = frozenset(
    {"homoeolog_one2one", "homoeolog_one2many", "homoeolog_many2many"}
)

KNOWN_TYPES = ORTHOLOG_TYPES | PARALOG_TYPES | HOMOEOLOG_TYPES
