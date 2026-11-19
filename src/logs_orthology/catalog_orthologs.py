"""Every ortholog of one accession, on a dataRepo catalog, through the orthology snapshot it registers (PXR-O13).

A dataRepo catalog cites at most one ``logs.register_orthology`` artefact. It copies no orthology rows: the
snapshot sits in the artefact's ``snapshot/`` directory and is read through its own ``views.sql`` (DuckDB table
macros). So the catalog is attached read-only to an in-memory connection, and the macros are created there.

Two measurements:

* **one accession**: accession -> gene (``gene_resolutions``) -> orthologs in each other species (``orthologs()``,
  one-to-many kept, ``pair_status()`` when there is none) -> the partner genes' accessions in every searched
  database. Each step is timed (indicative only: timings are not pinned).
* **symbol against orthology**, the stand-in PXReprise 019 used: for every human accession in ``protein_index``
  that has a gene name, is seen at 1% in at least one dataset, and resolves to exactly one gene, compare two
  sets of partner accessions in species b, both drawn from b's ``protein_index``:
  ``S``, the accessions with the same gene name (case-insensitive), and ``O``, the accessions whose resolved
  gene Compara calls an ortholog of X's gene. Every symbol partner outside ``O`` is then given its reason.

Run:
    python -m logs_orthology.catalog_orthologs F:/aging_data/repo/catalogs/catalog-4e486c3dcf0aa01c.duckdb
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import time
from pathlib import Path

import duckdb

from .fetch import project_root

TAXON = {"homo_sapiens": "NCBITaxon:9606", "mus_musculus": "NCBITaxon:10090", "rattus_norvegicus": "NCBITaxon:10116"}
GENE_PREFIX = (("ENSMUSG", "mus_musculus"), ("ENSRNOG", "rattus_norvegicus"), ("ENSG", "homo_sapiens"))

CLASSES = """
  case when len(s) = 0 and len(o) = 0 then 'neither'
       when s = o then 'same'
       when len(s) = 0 then 'only_orthology'
       when len(o) = 0 then 'only_symbol'
       when list_has_all(o, s) then 'symbol_subset_of_orthologs'
       when list_has_all(s, o) then 'symbol_adds_non_orthologs'
       when len(list_intersect(s, o)) = 0 then 'disjoint'
       else 'overlapping_different' end"""

WHY_OUTSIDE = """
  case when pouts is null then 'partner_not_in_gene_resolutions'
       when pg is null then 'partner_has_no_gene:' || array_to_string(pouts, '+')
       when len(list_intersect(pg, og)) > 0 then 'is_ortholog'
       when status is null then 'human_gene_not_in_snapshot'
       when status <> 'has_ortholog' then 'human_gene_has_no_ortholog:' || status
       else 'partner_gene_not_an_ortholog' end"""


def _species(gene_id: str) -> str:
    return next(sp for prefix, sp in GENE_PREFIX if gene_id.startswith(prefix))


def connect(catalog: Path) -> tuple[duckdb.DuckDBPyConnection, dict]:
    con = duckdb.connect()
    con.execute(f"ATTACH '{catalog.as_posix()}' AS cat (READ_ONLY)")
    rows = con.execute("""select artefact_id, definition_id, path, release, inputs from cat.catalog_engine_artefacts
                          where engine = 'logs.register_orthology'""").fetchall()
    if len(rows) != 1:
        raise SystemExit(f"{catalog}: {len(rows)} registered orthology snapshots; a catalog cites exactly one")
    artefact_id, definition_id, path, release, inputs = rows[0]
    root = Path(path) / "snapshot"
    manifest = (root / "manifest.json").read_bytes()
    snap = {
        "artefact_id": artefact_id, "definition_id": definition_id, "root": root.as_posix(),
        "release": json.loads(release), "inputs": json.loads(inputs),
        "manifest_sha256": hashlib.sha256(manifest).hexdigest(),
        "snapshot_id": json.loads(manifest)["snapshot_id"],
    }
    snap["manifest_matches_registration"] = snap["manifest_sha256"] == snap["inputs"]["snapshot_manifest"]
    con.execute((root / "views.sql").read_text(encoding="utf-8"))
    return con, snap


def _timed(con, sql: str, params: list) -> tuple[list, float]:
    t = time.perf_counter()
    rows = con.execute(sql, params).fetchall()
    return rows, round(1000 * (time.perf_counter() - t), 1)


def one_accession(con, root: str, accession: str) -> dict:
    out: dict = {"accession": accession, "steps": []}
    genes, ms = _timed(con, """select distinct gene_id, gene_symbol, outcome, source, ensembl_xref_agrees
        from cat.gene_resolutions where (accession = ? or entry_accession = ?) and gene_id is not null order by 1""",
                       [accession, accession])
    out["steps"].append({"step": "accession -> gene", "ms": ms, "rows": [list(r) for r in genes]})
    src = sorted({g[0] for g in genes})
    if not src:
        out["refusal"] = "the accession resolves to no gene"
        return out
    a = _species(src[0])
    ph = ",".join("?" * len(src))
    partners: set[str] = set()
    for b in [s for s in TAXON if s != a]:
        orth, ms = _timed(con, f"""select gene, partner_gene, relationship_type, is_high_confidence
            from orthologs(?, ?, ?) where gene in ({ph}) order by 2""", [root, a, b] + src)
        status, ms2 = _timed(con, f"select gene_id, status from pair_status(?, ?, ?) where gene_id in ({ph})",
                             [root, a, b] + src)
        out["steps"].append({"step": f"gene -> orthologs in {b}", "ms": ms, "rows": [list(r) for r in orth],
                             "pair_status": [list(r) for r in status], "pair_status_ms": ms2})
        partners |= {r[1] for r in orth}
    if partners:
        ph = ",".join("?" * len(partners))
        accs, ms = _timed(con, f"""select gene_id, accession, outcome, ensembl_xref_agrees,
            count(distinct search_database_sha256) as n_databases
            from cat.gene_resolutions where gene_id in ({ph}) group by all order by 1, 2""", sorted(partners))
        out["steps"].append({"step": "partner genes -> accessions", "ms": ms, "rows": [list(r) for r in accs]})
    return out


def symbol_vs_orthology(con, root: str) -> dict:
    con.execute("create or replace temp table acc_gene as select distinct accession, gene_id "
                "from cat.gene_resolutions where gene_id is not null")
    con.execute("create or replace temp table acc_out as select accession, list(distinct outcome order by outcome) outs "
                "from cat.gene_resolutions group by 1")
    con.execute(f"""create or replace temp table hx as
        select p.protein_accession acc, p.gene sym, any_value(g.gene_id) gene_id
        from cat.protein_index p join acc_gene g on g.accession = p.protein_accession
        where p.organism = '{TAXON['homo_sapiens']}' and p.gene is not null and p.n_datasets_1pct > 0
        group by 1, 2 having count(distinct g.gene_id) = 1""")
    n, n_genes = con.execute("select count(*), count(distinct gene_id) from hx").fetchone()
    out: dict = {"denominator": {"human_accessions": n, "human_genes": n_genes,
                                 "rule": "protein_index, organism human, gene name present, n_datasets_1pct > 0, "
                                         "exactly one gene in gene_resolutions"}, "species": {}}
    for b in ("mus_musculus", "rattus_norvegicus"):
        con.execute(f"""create or replace temp table cmp as
          with pb as (select protein_accession acc, upper(gene) sym from cat.protein_index where organism = '{TAXON[b]}'),
               s as (select hx.acc, list(distinct pb.acc order by pb.acc) s from hx join pb on pb.sym = upper(hx.sym) group by 1),
               o as (select hx.acc, list(distinct pb.acc order by pb.acc) o, list(distinct ot.relationship_type) rt
                     from hx join orthologs('{root}', 'homo_sapiens', '{b}') ot on ot.gene = hx.gene_id
                     join acc_gene ag on ag.gene_id = ot.partner_gene join pb on pb.acc = ag.accession group by 1)
          select hx.acc, hx.sym, coalesce(s.s, []) s, coalesce(o.o, []) o, coalesce(o.rt, []) rt
          from hx left join s using (acc) left join o using (acc)""")
        classes = dict(con.execute(f"select {CLASSES} cls, count(*) from cmp group by 1 order by 1").fetchall())
        examples = {c: [list(r) for r in con.execute(
            f"select acc, sym, s, o, rt from cmp where {CLASSES} = ? order by acc limit 3", [c]).fetchall()]
            for c in classes if c not in ("same", "neither")}
        con.execute(f"""create or replace temp table pairs as
          with pb as (select protein_accession pacc, upper(gene) sym from cat.protein_index where organism = '{TAXON[b]}'),
               ps as (select gene_id, status from pair_status('{root}', 'homo_sapiens', '{b}')),
               og as (select gene, list(distinct partner_gene) og from orthologs('{root}', 'homo_sapiens', '{b}') group by 1)
          select hx.acc, hx.sym, hx.gene_id hg, pb.pacc, ps.status, coalesce(og.og, []) og,
                 (select list(distinct gene_id) from acc_gene a where a.accession = pb.pacc) pg,
                 (select any_value(outs) from acc_out o where o.accession = pb.pacc) pouts
          from hx join pb on pb.sym = upper(hx.sym)
          left join ps on ps.gene_id = hx.gene_id left join og on og.gene = hx.gene_id""")
        why = {r[0]: {"pairs": r[1], "human_accessions": r[2]} for r in con.execute(
            f"select {WHY_OUTSIDE} why, count(*), count(distinct acc) from pairs group by 1 order by 1").fetchall()}
        not_one2one, with_orth = con.execute(
            "select count(*) filter (where len(o) > 0 and not list_contains(rt, 'ortholog_one2one')), "
            "count(*) filter (where len(o) > 0) from cmp").fetchone()
        out["species"][b] = {"classes": classes, "symbol_partners_by_reason": why,
                             "with_orthologs": with_orth, "with_orthologs_not_one2one": not_one2one,
                             "examples": examples}
    return out


def _md(r: dict) -> str:
    d = r["symbol_vs_orthology"]["denominator"]
    lines = [f"# Orthologs of an accession on catalog `{r['catalog_id']}`", "",
             f"Snapshot: artefact `{r['snapshot']['artefact_id']}` ({r['snapshot']['release']}), "
             f"manifest matches its registration: {r['snapshot']['manifest_matches_registration']}.", "",
             f"## One accession: {r['one_accession']['accession']}", "", "| step | rows | ms |", "|---|---:|---:|"]
    lines += [f"| {s['step']} | {len(s['rows'])} | {s['ms']} |" for s in r["one_accession"]["steps"]]
    lines += ["", "## A gene symbol against Compara orthology", "",
              f"{d['human_accessions']:,} human accessions ({d['human_genes']:,} genes): {d['rule']}.", ""]
    for b, sp in r["symbol_vs_orthology"]["species"].items():
        tot = sum(sp["classes"].values())
        lines += [f"### human -> {b}", "", "| class | accessions | % |", "|---|---:|---:|"]
        lines += [f"| {c} | {k:,} | {100 * k / tot:.1f} |" for c, k in sp["classes"].items()]
        lines += ["", "Symbol partners outside the orthology set, by reason:", "", "| reason | pairs | human accessions |",
                  "|---|---:|---:|"]
        lines += [f"| {w} | {v['pairs']:,} | {v['human_accessions']:,} |" for w, v in sp["symbol_partners_by_reason"].items()]
        lines.append("")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("catalog", type=Path)
    ap.add_argument("--accession", default="P14136")
    ap.add_argument("--out", type=Path, help="output stem (default results/catalog_orthologs_<catalog id>)")
    a = ap.parse_args(argv)
    con, snap = connect(a.catalog)
    catalog_id, schema_version, builder_version, n_datasets = con.execute(
        "select catalog_id, schema_version, builder_version, n_datasets from cat.catalog_meta").fetchone()
    r = {"catalog": a.catalog.as_posix(), "catalog_id": catalog_id, "catalog_schema_version": schema_version,
         "datarepo": builder_version, "n_datasets": n_datasets, "snapshot": snap,
         "engine_artefacts": dict(con.execute(
             "select engine, count(*) from cat.catalog_engine_artefacts group by 1 order by 1").fetchall()),
         "measured_utc": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
         "duckdb": duckdb.__version__,
         "one_accession": one_accession(con, snap["root"], a.accession),
         "symbol_vs_orthology": symbol_vs_orthology(con, snap["root"])}
    stem = a.out or project_root() / "results" / f"catalog_orthologs_{catalog_id}"
    stem.with_name(stem.name + ".json").write_text(json.dumps(r, indent=1, default=str) + "\n", encoding="utf-8")
    stem.with_name(stem.name + ".md").write_text(_md(r), encoding="utf-8")
    print(_md(r))


if __name__ == "__main__":
    main()
