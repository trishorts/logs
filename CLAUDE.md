<!-- Auto-loaded when cwd is inside this project folder. Managed by the /project skill. -->

# Project: logs

This folder is a `/project`-managed research project. **You are de facto working on it.**

- **Phase:** BUILD
- **Goal:** A generic, versioned, gene-centric cross-species orthology layer that lets any
  multi-organism proteomics project join protein identifications across species without collapsing
  one-to-many orthology.
- **Pick up at:** **human accession→gene resolution in `logs`** (`design/PLAN.md` step 5). Plan
  reordered 2026-09-22 after `aging` 002 (reply 003-logs): compare not pool, rodents months away so
  the store is deferred, and they want resolution more than orthology. First decision: search-XML
  `dbReference`s vs the on-disk Ensembl 116 xref (ideally both, cross-checked). See `RESUME.md`.

**The name:** `logs` = homologs, orthologs, paralogs, and any other -logs. Not log files.

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
7. **Don't start mzLib-side code until PR #1336 merges.** It establishes the
   typed-view-over-`DatabaseReferences` idiom; a second mechanism written independently is the
   duplication `/oracle` exists to prevent.

## Running things

```powershell
$env:PYTHONPATH = "E:\CodeReview\logs\src"
python -m logs_orthology.fetch          # re-fetch/verify the pinned Ensembl 116 inputs
python -m logs_orthology.cardinality    # -> results/cardinality.{md,json}
python -m logs_orthology.xrefs          # -> results/accession_resolution.{md,json}
python -m logs_orthology.resolve --reference          # -> results/resolution_human_e116.{tsv.gz,json}
python -m logs_orthology.resolve --accessions ids.tsv # accession[<TAB>contaminant] per line
python tests/test_contracts.py         # 10 contract tests
python tests/test_resolve.py           # 16 resolver contracts (last one reconciles on real data)
python tests/test_reported_claims.py   # 15 numbers already sent to a partner
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
