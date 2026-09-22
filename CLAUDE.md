<!-- Auto-loaded when cwd is inside this project folder. Managed by the /project skill. -->

# Project: logs

This folder is a `/project`-managed research project. **You are de facto working on it.**

- **Phase:** INCEPTION
- **Goal:** A generic, versioned, gene-centric cross-species orthology layer that lets any
  multi-organism proteomics project join protein identifications across species without collapsing
  one-to-many orthology.
- **Pick up at:** `/grill-me` on `design/problem-statement.md` - settle the implementation home
  (mzLib vs standalone vs dataRepo), the orthology source of record, and the dataRepo accession seam.

**The name:** `logs` = homologs, orthologs, paralogs, and any other -logs. Not log files.

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
