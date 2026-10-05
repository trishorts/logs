<!-- Auto-loaded when cwd is inside this project folder. Managed by the /project skill. -->

# Project: logs

This folder is a `/project`-managed research project. **You are de facto working on it.**

- **Phase:** BUILD
- **Goal:** A generic, versioned, gene-centric cross-species orthology layer that lets any
  multi-organism proteomics project join protein identifications across species without collapsing
  one-to-many orthology.
- **Pick up at:** run the thread inbox. Then re-check the two open mzLib PRs:
  `gh pr view 1381 --repo smith-chem-wisc/mzLib --json state,reviewDecision` (the orthology store) and
  the same for **1382** (`VariantApplication.ParseAccession`, the LOGS-D2 rule; ready for review again 2026-09-30). On a merge:
  - move its board #19 card to Shipped;
  - for 1381, drop the pre-release flag (`gh release edit orthology-compara-116-b63a3331 --repo trishorts/logs --prerelease=false`);
  - for 1382, run `/bridge-oracle pyMzLib` to project it, then tell dataRepo (022 promised this).

  #1381 was made ready again on 2026-10-05 (master merged, writer folded into
  `UsefulProteomicsDatabases`, ZstdSharp 0.8.8, reply posted to nbollis); it now waits on re-review.
  **LOGS-D4 is closed** (read in place; 030 sent the file contract in `design/DEFINITIONS.md`).
  **The residue schema is proposed, not built** (`DEF-RESIDUE-CORRESPONDENCE v1`, sent as ptmQtl 007).
  Wait for LOGS-P5 (target databases) and LOGS-P6 (keep `substituted` rows) before building. Then
  fetch and pin `Compara.116.protein_default.aa.fasta.gz` and check that its proteins are the store's
  `protein_a/b`. Run `/oracle mzLib` before any aligner code.

  Step 6 is BUILT (2026-09-27/28) and released: public repo, pre-release
  `orthology-compara-116-b63a3331`, MIT for code and CC-BY-4.0 for data. See `RESUME.md`.

## Things that will bite you here

1. **Ensembl's genome-specific Compara dumps partition rather than overlap, and each species pair
   lives entirely in ONE file — not the obvious one.** Every human↔mouse orthology is in the
   **mouse** dump; the human dump has none. Downloading the file named after your species yields a
   complete-looking result missing 100% of human↔mouse. Read a provider's README before its data.
2. **A denominator is a claim — enumerate the set before dividing by it.** Two were wrong in one
   afternoon: `protein_coding` is not the eligible set (Compara also trees IG/TR gene segments),
   and counting raw gene ids from the xref dumps includes ALT haplotypes, which inflated the
   multi-gene rate twentyfold and invented a human-vs-rodent difference that does not exist.
3. **Never name an entity from memory in a deliverable.** `Q5JQC4` was written up as KIR2DL5A from
   recall; it is CT47A1. Resolve identifiers against the data, every time.
4. **When a result is surprising, suspect the measurement first.** "Human is dramatically worse
   than mouse" was surprising and wrong. The surprise was the signal.
5. **`Protein.NcbiTaxonomyId`'s projection does not transfer to gene ids.** UniProt writes one
   `dbReference` per *transcript* with the ENSG in a `<property>`, so `FirstOrDefault(...)?.Id` is
   a category error — it needs `SelectMany(Properties)` and a `Distinct()`.
6. **A number sent to a partner is a contract.** `tests/test_reported_claims.py` pins every one. If
   a re-run moves it, fix the code or send a correction — never edit the expected value.
7. **#1338 and #1337 are MERGED (mzLib 1.0.592).** The `code/` worktrees are historical pins; their
   origin branches carry later master merges. Start new mzLib work from `smith/master`, and never
   force-push anyone else's branch.
8. **`LoadProteinXML` applies sequence variants by default.** The human reviewed proteome loads as
   52,359 proteins from 20,416 entries (`P12345_S70N`). Say whether a count is of entries or
   proteoforms.
9. **"Multi-gene" depends on the source.** UniProt's XML links readthrough genes, novel genes and
   paralogs, giving 350 multi-gene entries; Ensembl's xref gives 69. Both are reported;
   `ensembl_xref_agrees` separates them.
10. **Long heredocs and backslashes in the Bash tool can break a script.** Write a message body with
    the Write tool, then post it, and use forward-slash Windows paths.
11. **Pin a number the moment it is sent, and never send a prototype's number.** 007's "20,412" was
    unpinned and moved silently; "563 KB" came from an awk extract, and the real file is 523 KB.
12. **UniProt's rat XML links four Ensembl gene-id series.** Only `ENSRNOG00000…` is GRCr8. The
    resolver is correct to hold them to the gene set, and the `source = ensembl_xref` rows recover
    Ensembl's answer (rat: 725 entries). Filter on `source` for the XML's view, and on
    `ensembl_xref_agrees` for Ensembl's.
13. **mzLib PRs:** open against smith-chem-wisc, start the body with the `<!-- project-of-origin -->`
    "Project of origin: `logs`" line, and use `type(scope): summary` commits (`commit-style.md`).
    **Every logs PR goes on GitHub Project #19** (https://github.com/orgs/smith-chem-wisc/projects/19):
    `gh project item-add 19 --owner smith-chem-wisc --url <pr>`, Status In review; Shipped on merge.
14. **`*.tsv.gz` is gitignored globally** (only `results/gene_sets/` and the delivered
    `results/search_db_human_e116.tsv.gz` are excepted). Run `git check-ignore -v <path>` before a
    message calls a file "tracked"; 015 said so before checking.
15. **The table's gene column is `gene_id`**, not `gene_stable_id` (011's error, corrected in 015).
    Read a column name from `GeneResolutionTsv.Schema`, never from a prose description.
16. **pyMzLib's `resolve_genes` resolves ENTRIES, and `xref=` is optional.** It wrote 20,899 rows
    where our tool wrote 53,239 proteoform rows. It does not apply variants, and every row it writes
    is identical to a reference row. Without `xref=`, `ensembl_xref_agrees` is None everywhere, and
    aging's default view is empty. The v1 definition requires the xref input.
17. **A row's `gene_set_sha256` is the GTF's sha256, not the gene-set table's.** Check rows against
    the manifest's `row_values`.
18. **Question ids must match `threads.py`'s `QID_RE`**, so `LOGS-D1` rather than `LOGS-DR1`. An id
    that does not match is silently left out of the ledger. Check the charter before promising a
    seam: S4 moved to per-engine namespaces while 015 and 016 still promised QuantProject.
19. **Count a gene view by the view, not by `outcome`.** `outcome` is the XML's links; the
    `ensembl_xref_agrees` view adds xref-only rows. Rat: 51.4% by `outcome`, 59.6% by agrees (022).

20. **Anything of substance is C# in mzLib, not Python** (user, 2026-09-27). The Python in `src/` is
    measurement and test oracle: `cardinality.py` checked #1381, and `normalize()` checked #1382. Run
    `/oracle mzLib` before writing C#.
21. **mzLib tooling traps.**
    - `dotnet sln add` rewrites `mzLib.sln` wholesale (365 lines, adds x86 configs). Add the Project
      entry and its 12 configuration lines by hand, copying an existing project's.
    - A new project also needs its DLL/XML and any NuGet dependency in `mzLib.nuspec`, in both
      target groups.
    - `Check-TestNameHygiene.ps1 -NoBuild` expects a Debug build; run it without `-NoBuild`.
    - mzLib ships as ONE nupkg, so a separate csproj keeps a NuGet dependency away from no consumer.
      Before adding a package, compare its transitive pins with the nuspec's: Parquet.Net needed
      ZstdSharp 0.8.8 against a 0.8.7 pin, and only the MetaMorpheus `integration` job saw it (NU1605).
22. **The repo is PUBLIC** (2026-09-28). Everything committed is published, including the partner
    thread copies. A snapshot's `views.sql` is mzLib's LGPL-3.0, not CC-BY (`LICENSING.md`).
23. **Pushing a mirror pushes the partner's unpushed commits too.** Run `git -C ../<peer> status -sb`
    before pushing their repo. 2026-09-28 pushed pride's `5f70f17` unchecked.
24. **Pin a snapshot by its manifest, not its folder.** `snapshots/` is gitignored.
    `test_first_orthology_snapshot_as_sent_in_026` checks every file and the release tar's sha256 when
    they are present locally. Rebuild with `tools/BuildOrthologySnapshot` (the tar is reproducible:
    `tar --sort=name --mtime=@0 --owner=0 --group=0 --numeric-owner --format=gnu`).
25. **Say plainly what a PR keeps, not only what it joins.** #1382's first description led with
    "join a variant proteoform to its entry" and never said the variants are returned too; the user
    read it as stripping them and drafted it (2026-09-30). Variants are applied only on request and in
    many combinations, so the accession is the only record of them: never discard the suffix.

## Running things

```powershell
$env:PYTHONPATH = "E:\CodeReview\logs\src"
python -m logs_orthology.fetch          # re-fetch/verify the pinned Ensembl 116 inputs
python -m logs_orthology.cardinality    # -> results/cardinality.{md,json}
python -m logs_orthology.xrefs          # -> results/accession_resolution.{md,json}
python -m logs_orthology.resolve --reference          # -> results/resolution_human_e116.{tsv.gz,json}
python -m logs_orthology.resolve --accessions ids.tsv # accession[<TAB>contaminant] per line
python tests/test_contracts.py         # 10 contract tests
python tests/test_resolve.py           # 21 resolver contracts (last one reconciles on real data)
python tests/test_reported_claims.py   # 25 claims already sent to a partner
python -m logs_orthology.manifest       # -> results/resolver_inputs_e116.{json,md}
dotnet run --project tools/BuildGeneSet -c Release -- <gtf.gz> results/gene_sets/<Species>.116.genes.tsv.gz
dotnet run --project tools/BuildOrthologySnapshot -c Release -- 116 data/compara results/gene_sets snapshots/compara-116 homo_sapiens mus_musculus rattus_norvegicus   # out dir "-" = check only
dotnet run --project tools/ResolveSearchDb -c Release -- <xml> <gtf.gz | genes.tsv.gz> <uniprot.tsv.gz> <out.tsv>
python -m logs_orthology.search_db <out.tsv> [--species mus_musculus --out results/search_db_resolution_mouse]
```

Inputs live in `data/compara/` (gitignored, 673 MB, recorded in `data/PROVENANCE.md`).

**Scope discipline:** this is **generic engineering infrastructure**. `aging` is the first consumer,
not the design driver; `dataRepo` is a generic neighbour. Any requirement arriving from a consuming
project must be generalized before it lands in the design.

**At the start of a session (your first response in this folder), render the standard `/project brief`
once** - the fixed "where I sit" briefing (phase + progress bar, goal, pick-up, recent wins, current
gate checks, health: uncommitted/stale figures/stale docx/unsynced, open gaps). Format + derivation:
the `project` skill's `references/session-brief.md`. Compute it like `status` (read `.project/state.yaml`
+ infer from folder/git). Do it once per session, not every turn. State lives in `.project/state.yaml`;
the human-readable live doc is `RESUME.md` (rendered fresh by `/project`). Do not hand-edit the
generated block in `RESUME.md`.

**How we work with peers — ask, answer, and state our own needs.** Communication is the
highest-value activity here, not overhead around it. Measured on our first day: four messages with
`dataRepo` produced ten substantive results, and only **two** were reachable by thinking harder. Two
schema contracts were stopped before being built, and a real defect in their store was found only
because we stated a *wrong* hypothesis out loud and they checked it.

So: ask the owner directly, never through a proxy. Answer quickly, including "I don't know" and "I
was wrong" — record a disproved hypothesis in the thread rather than quietly dropping it, so the
thread shows which side supplied which idea. And **state our own needs unprompted** — that is the one
that gets skipped. Are we a blocker or an improvement? Does a partner want half the deliverable
early? Is a claim in our charter currently unfalsified? Say it before someone has to ask.

Never open an empty channel: every message carries a concrete finding or ask.

**Threads come first.** Run the inbox check as step 0 of the session, before anything else:

```
python "$env:USERPROFILE/.claude/skills/project/assets/threads.py" inbox
```

Another project may be blocked on a reply from us. Read any unread messages, then re-run with
`--mark-read`. Post replies with `threads.py new --to <peer>` (it writes both mirrored copies and
allocates the number); never edit a posted message - send a correction as a new one. Ownership of
capabilities is `design/threads/OWNERSHIP.md`; the protocol is the `project` skill's
`references/threads.md`. Our question-ID prefix is `LOGS-`.

**Before writing any C# code**, run `/oracle mzLib` - mzLib is the lab's large shared library and the
candidate implementation home. Do not re-implement something it already has under another name.

Layout: `design/` `lit/` `code/` (worktrees, gitignored) `data/` (+PROVENANCE) `results/`
`manuscript/` `submission/`. Conventions and dispatch live in the `project` skill.
