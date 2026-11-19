"""Review measurement: PXReprise's ``protein_orthologs`` bridge (smith-chem-wisc/PXReprise#26), re-run on a catalog.

The PR builds five orthology tables into a dataRepo catalog. We re-run its bridge SQL here, word for word, as it stands at
the PR head named in ``PR_HEAD``, on a catalog opened read-only. The four snapshot tables it reads are rebuilt as TEMP
tables from the registered snapshot's own ``views.sql`` macros, as the PR does. Nothing is written to the catalog.

What it measures, for PXR-O14 (PXReprise 022):

- the bridge's size and statuses, and GFAP's answer;
- **contradictions:** (accession, target species) pairs that the bridge answers both ``no_gene`` and with a gene. This
  happens when the search database links no gene but Ensembl's xref does: ``logs:DEF-GENE-RESOLUTION`` then writes a
  no-gene row and a ``source = ensembl_xref`` row, and the second does not change ``outcome``. The same count is also
  taken straight from ``gene_resolutions``, without the PR's SQL;
- **partners:** ortholog rows with no partner accession, and how many of them some searched database could have
  supplied (the PR offers only accessions some search held);
- whether ``not_in_gene_set`` can occur, and whether the ``protein_index`` join fans rows out.

Run: ``python -m logs_orthology.catalog_bridge_review <catalog.duckdb>`` ->
``results/catalog_bridge_review_<catalog_id>.{json,md}``.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from .catalog_orthologs import connect
from .fetch import project_root

PR = "smith-chem-wisc/PXReprise#26"
PR_HEAD = "a3195c166ad7feb522bc8f01c26bbda183efd3af"

# CatalogOrthology.cs at PR_HEAD: OrthologySources and ProteinOrthologsSelect, unchanged except that the snapshot's
# artefact id literal is a placeholder.
SOURCES = """
        SELECT g.accession, s.species, g.outcome, g.gene_id,
               array_to_string(list_sort(list(DISTINCT g.definition_id)), '; ') AS definition_id
        FROM gene_resolutions g
        JOIN orthology_species s ON s.gene_set_sha256 = g.gene_set_sha256
        WHERE EXISTS (SELECT 1 FROM protein_genes pg WHERE pg.artefact_id = g.artefact_id AND pg.protein_accession = g.accession)
        GROUP BY g.accession, s.species, g.gene_set_sha256, g.outcome, g.gene_id"""
BRIDGE = f"""
        WITH resolutions AS ({SOURCES}
        ),
        asked AS (
            SELECT r.accession, r.species, r.outcome, r.gene_id, r.definition_id, t.species AS target_species,
                   CASE WHEN r.gene_id IS NULL THEN 'no_gene'
                        WHEN g.gene_id IS NULL THEN 'not_in_gene_set'
                        ELSE st.status END AS status
            FROM resolutions r
            JOIN orthology_species t ON t.species <> r.species
            LEFT JOIN orthology_genes g ON g.species = r.species AND g.gene_id = r.gene_id
            LEFT JOIN gene_ortholog_status st
                   ON st.species = r.species AND st.gene_id = r.gene_id AND st.target_species = t.species
        ),
        partners AS (
            SELECT accession, species, gene_id, array_to_string(list_sort(list(DISTINCT outcome)), '; ') AS outcome
            FROM resolutions WHERE gene_id IS NOT NULL
            GROUP BY accession, species, gene_id
        )
        SELECT a.accession AS protein_accession, a.species, a.outcome AS resolution_outcome, a.gene_id,
               a.target_species, a.status, o.relationship_type, o.is_high_confidence, o.partner_gene,
               pg.gene_name AS partner_gene_name, p.accession AS partner_accession, p.outcome AS partner_resolution_outcome,
               CASE WHEN p.accession IS NOT NULL THEN coalesce(pi.n_datasets_1pct, 0) END AS partner_n_datasets_1pct,
               a.definition_id, 'ARTEFACT_ID' AS artefact_id
        FROM asked a
        LEFT JOIN gene_orthologs o
               ON o.species = a.species AND o.partner_species = a.target_species
              AND o.gene = CASE WHEN a.status = 'has_ortholog' THEN a.gene_id END
        LEFT JOIN orthology_genes pg ON pg.species = o.partner_species AND pg.gene_id = o.partner_gene
        LEFT JOIN partners p ON p.species = o.partner_species AND p.gene_id = o.partner_gene
        LEFT JOIN protein_index pi ON pi.protein_accession = p.accession
        ORDER BY a.accession, a.species, a.gene_id NULLS FIRST, a.target_species, o.partner_gene, p.accession"""


def _snapshot_tables(con, root: str) -> list[str]:
    """The four tables the bridge reads from the snapshot, as TEMP tables, filled through the snapshot's macros."""
    manifest = json.loads((Path(root) / "manifest.json").read_text(encoding="utf-8"))
    species = manifest["species"]
    con.execute("create temp table orthology_species (species varchar, gene_set_sha256 varchar)")
    for s in species:
        con.execute("insert into orthology_species values (?, ?)", [s, manifest["gene_set_sha256"][s]])
    con.execute("create temp table orthology_genes as select gene_id, gene_version, gene_biotype, gene_name, seq_region, "
                "species from read_parquet(?)", [[f"{root}/genes/{s}.parquet" for s in species]])
    con.execute("create temp table gene_orthologs (species varchar, partner_species varchar, relationship_type varchar, "
                "gene varchar, partner_gene varchar, is_high_confidence boolean)")
    con.execute("create temp table gene_ortholog_status (species varchar, gene_id varchar, target_species varchar, status varchar)")
    for a in species:
        for b in (s for s in species if s != a):
            con.execute(f"insert into gene_orthologs select '{a}', '{b}', relationship_type, gene, partner_gene, "
                        f"is_high_confidence from orthologs('{root}', '{a}', '{b}')")
            con.execute(f"insert into gene_ortholog_status select '{a}', gene_id, '{b}', status "
                        f"from pair_status('{root}', '{a}', '{b}')")
    return species


def review(con, root: str) -> dict:
    for t in ("gene_resolutions", "protein_genes", "protein_index"):
        con.execute(f"create temp view {t} as select * from cat.{t}")
    species = _snapshot_tables(con, root)
    one = lambda sql: con.execute(sql).fetchone()  # noqa: E731
    t0 = time.perf_counter()
    con.execute(f"create temp table po as {BRIDGE}")
    seconds = round(time.perf_counter() - t0, 2)
    out: dict = {"species": species, "bridge_seconds": seconds}
    out["tables"] = dict(zip(["orthology_genes", "gene_orthologs", "gene_ortholog_status"], one(
        "select (select count(*) from orthology_genes), (select count(*) from gene_orthologs), "
        "(select count(*) from gene_ortholog_status)")))
    out["rows"], out["accessions"] = one("select count(*), count(distinct protein_accession) from po")
    out["rows_equal_distinct_keys"] = one(
        "select count(*) = count(distinct (protein_accession, species, gene_id, target_species, partner_gene, "
        "partner_accession, resolution_outcome)) from po")[0]
    out["protein_index_duplicate_accessions"] = one(
        "select count(*) from (select protein_accession from protein_index group by 1 having count(*) > 1)")[0]
    out["status"] = {s: {"rows": n, "accessions": a} for s, n, a in con.execute(
        "select coalesce(status, 'NULL'), count(*), count(distinct protein_accession) from po group by 1 order by 2 desc").fetchall()}
    out["gfap"] = [list(r) for r in con.execute(
        "select target_species, status, relationship_type, is_high_confidence, partner_gene, partner_accession "
        "from po where protein_accession = 'P14136' order by 1, 6").fetchall()]

    # Contradictions, in the bridge and straight from gene_resolutions (without the PR's SQL).
    out["bridge_pairs_no_gene_and_a_gene"] = one(
        "select count(*) from (select protein_accession, target_species from po group by 1, 2 "
        "having bool_or(status = 'no_gene') and bool_or(status <> 'no_gene'))")[0]
    con.execute("""create temp table held as select g.* from gene_resolutions g
        join orthology_species s on s.gene_set_sha256 = g.gene_set_sha256
        where exists (select 1 from protein_genes pg where pg.artefact_id = g.artefact_id and pg.protein_accession = g.accession)""")
    out["held_accessions_no_gene_row_and_gene_row"] = one(
        "select count(*) from (select accession from held group by 1 "
        "having bool_or(gene_id is null) and bool_or(gene_id is not null))")[0]
    out["their_gene_rows_by_source"] = dict(con.execute("""
        select source, count(distinct accession) from held where gene_id is not null and accession in
          (select accession from held group by 1 having bool_or(gene_id is null) and bool_or(gene_id is not null))
        group by 1""").fetchall())
    out["their_outcomes"] = dict(con.execute("""
        select outcome, count(distinct accession) from held where accession in
          (select accession from held group by 1 having bool_or(gene_id is null) and bool_or(gene_id is not null))
        group by 1 order by 1""").fetchall())
    out["examples"] = [list(r) for r in con.execute("""
        select accession, outcome, gene_id, source from held where accession in
          (select accession from held group by 1 having bool_or(gene_id is null) and bool_or(gene_id is not null))
        group by all order by 1, 3 nulls first limit 6""").fetchall()]
    # The PR's column docs: a no-gene outcome has status no_gene, and a partner's outcome is resolved or multi_gene.
    out["no_gene_outcomes_by_status"] = {f"{o}|{s}": n for o, s, n in con.execute(
        "select resolution_outcome, status, count(*) from po where resolution_outcome in ('not_in_source', "
        "'off_primary_only', 'unrecognized_accession') group by all order by 1, 2").fetchall()}
    out["partner_rows_by_outcome"] = dict(con.execute(
        "select partner_resolution_outcome, count(*) from po where partner_accession is not null group by 1 order by 1").fetchall())
    cols = {r[0] for r in con.execute("describe gene_resolutions").fetchall()}
    out["gene_resolutions_has_ensembl_xref_agreement"] = "ensembl_xref_agreement" in cols
    out["definition_ids"] = dict(con.execute(
        "select definition_id, count(distinct artefact_id) from gene_resolutions group by 1").fetchall())

    # Partners: the PR offers accessions some search held; what would every searched database's add?
    out["ortholog_rows_no_partner_accession"] = one(
        "select count(*) from po where partner_gene is not null and partner_accession is null")[0]
    r = one("""select count(*), count(distinct partner_gene) from po
               where partner_gene is not null and partner_accession is null
                 and partner_gene in (select gene_id from gene_resolutions where gene_id is not null)""")
    out["of_which_a_searched_database_holds_an_accession"] = {"rows": r[0], "partner_genes": r[1]}
    out["not_in_gene_set_rows"] = out["status"].get("not_in_gene_set", {"rows": 0})["rows"]
    out["genes_in_every_direction"] = out["tables"]["gene_ortholog_status"] == (len(species) - 1) * out["tables"]["orthology_genes"]
    return out


def render(r: dict) -> str:
    b = r["bridge"]
    st = "\n".join(f"| {k} | {v['rows']:,} | {v['accessions']:,} |" for k, v in b["status"].items())
    ex = "\n".join(f"| {a} | {o} | {g or ''} | {s} |" for a, o, g, s in b["examples"])
    nb = b["of_which_a_searched_database_holds_an_accession"]
    return f"""# {r['pr']} re-run on catalog {r['catalog_id']}

The PR's `protein_orthologs` SQL at `{r['pr_head'][:9]}`, word for word, on catalog `{r['catalog_id']}` (read-only), with the
four snapshot tables rebuilt from snapshot artefact `{r['snapshot']['artefact_id']}`'s own macros. Gene resolutions:
{', '.join(f'`{k}` ({v} artefacts)' for k, v in b['definition_ids'].items())}. Built in {b['bridge_seconds']} s.

- {b['rows']:,} rows over {b['accessions']:,} accessions; one row per key: {b['rows_equal_distinct_keys']}
  (`protein_index` has {b['protein_index_duplicate_accessions']} duplicate accessions).
- GFAP P14136: {'; '.join(f"{t[0]} {t[5]} ({t[2]}, high confidence {t[3]})" for t in b['gfap'])}.
- `not_in_gene_set`: {b['not_in_gene_set_rows']} rows. Every gene is in `gene_ortholog_status` in every direction:
  {b['genes_in_every_direction']}.

| status | rows | accessions |
|---|---:|---:|
{st}

## Answered both `no_gene` and with a gene

{b['held_accessions_no_gene_row_and_gene_row']:,} held accessions have a no-gene row and a gene row (counted straight from
`gene_resolutions`). Their gene rows by source: {b['their_gene_rows_by_source']}; their outcomes: {b['their_outcomes']}.
The bridge answers {b['bridge_pairs_no_gene_and_a_gene']:,} (accession, target species) pairs both ways.

- Rows whose outcome links no gene, by status: {b['no_gene_outcomes_by_status']}.
- Partner rows by the partner's outcome: {b['partner_rows_by_outcome']}.

| accession | outcome | gene_id | source |
|---|---|---|---|
{ex}

## Partners

{b['ortholog_rows_no_partner_accession']:,} ortholog rows have no partner accession. For {nb['rows']} of them
({nb['partner_genes']} partner genes), some searched database holds an accession of the gene that no search held.
"""


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("catalog", type=Path)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)
    con, snap = connect(a.catalog)
    catalog_id = a.catalog.stem.removeprefix("catalog-")
    r = {"pr": PR, "pr_head": PR_HEAD, "catalog": a.catalog.as_posix(), "catalog_id": catalog_id,
         "snapshot": {k: snap[k] for k in ("artefact_id", "release", "manifest_matches_registration")},
         "bridge": review(con, snap["root"])}
    stem = a.out or project_root() / "results" / f"catalog_bridge_review_{catalog_id}"
    stem.parent.mkdir(parents=True, exist_ok=True)
    stem.with_name(stem.name + ".json").write_text(json.dumps(r, indent=1, default=str) + "\n", encoding="utf-8")
    stem.with_name(stem.name + ".md").write_text(render(r), encoding="utf-8")
    print(render(r))


if __name__ == "__main__":
    main()
