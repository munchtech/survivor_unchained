---
name: wave-start
description: Start a wave of leads or helpers lean (coordinator or a lead). Use before spawning a wave: checks disk and worktrees, then writes each brief with the lines the spawn guard requires (Context budget, model, judge effort tier) and the state-file rule.
---

# Wave start

A wave costs most in what each agent carries for its whole life. Spawn small, by section, with a state file.

## 1. Before any spawn
- Disk: free space on C: (`powershell -NoProfile -Command "(Get-PSDrive C).Free/1GB"`). Under 20 GB: run `python tools/scratch/coordinator/wt_audit.py` and remove merged worktrees first (repo `CLAUDE.md`).
- Worktrees: count `.claude/worktrees`; at 8, remove finished ones before `isolation: "worktree"`.
- Live agents: 4 judged leads at most (memory "Usage rules"); data/systems leads past 4 are fine.

## 2. Each brief carries (the spawn guard refuses it otherwise)
- `Context budget: <n>k` on its own line: judges and solvers 120-180k, workers about 120k, runners 60-100k, leads 200k (a backstop: compaction cuts at about 166k).
- `model` passed on every `general-purpose`, `claude` or `Explore` spawn (haiku for search, sonnet for specified work, opus for taste). Project types (`su-*`) carry their own.
- Judges: a line `Effort tier: always-seen | less-seen | tier-3` and the matching `effort` (max / xhigh / high) from `docs/handoff/lead_brief.md` "Effort". Never lower a level.
- Leads spawning `su-lead-max`: `Item: <name>` (3 rounds per item unless the coordinator raises it).
- A big doc read whole only when it truly must be: `ReadWhole: <path>` (the read guard refuses others over 400 lines or 32 KB).
- The `Spawning: allowed` / `Context budget` lines go in the Agent prompt itself, not only in a brief file it points to.

## 3. What the brief says
- The exact files and sections to read (grep targets), never "read the handoff" or "read README".
- Its state file: the TOP block of `docs/handoff/<area>.md` (state, branch@sha, done, next in order, cost), kept current from the start. Compaction makes the cut; a full handoff only at a gate, end of day or planned stop.
- Noisy runs through the wrapper: `python tools/quiet.py -- <cmd>` or `python tools/turn.py run <kind> "<who>: <job>" -- <cmd>`.
- Who it reports to (your agent id) and the report shape (verdict or result first, numbers, paths).

## 4. Rounds
- A second round on the same item goes to the SAME helper by SendMessage while it is under 60% of its budget and inside its cache window (5 minutes for helpers, an hour for leads). A different job, or a cold or full helper: a fresh spawn with the first round's numbers in its brief.
- Spawn helpers you'd wait for in the foreground, in groups.

## 5. Group spawns
Independent spawns go in one message. Record each agent's id, type, budget and worktree path in your state file as it starts.
