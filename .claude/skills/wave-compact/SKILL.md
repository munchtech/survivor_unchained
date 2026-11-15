---
name: wave-compact
description: Close a wave and compact the coordinator (or a lead) at the boundary instead of handing off. Use when a wave's results are in and merged, before the next wave starts in the same job. Not for a cold session (start fresh from the state file instead).
---

# Wave compact

Measured 10-13 November: a compaction cost $0.34-0.93, a handoff $1.75-3.54, with no quality loss. A compaction of a cold session pays a full rewrite first, so check the cache.

## 1. Is it warm?
If the last request was more than an hour ago (5 minutes for a helper) and context is above about 150k, do NOT compact or resume: start a fresh session from the state file (`ctx_budget.py` says "Cache has lapsed" when that happens). A new job also gets a new session.

## 2. Close the wave
- Merges done; each merged worktree removed in the same turn (`powershell -NoProfile -ExecutionPolicy Bypass -File tools/scratch/coordinator/wt_remove.ps1 <path>`).
- Agents: every one of the wave reported or stopped; note any still running (id, area, what it waits on).
- Commit by path what you changed (never `.import` / `.uid` churn).

## 3. Update the state file first
The TOP block of your handoff or state file (RESUME top block for the coordinator): state, branch@sha, done this wave (with commits), next in order, open owner decisions, cost so far. The summary keeps its path, so the next context starts there.

## 4. Compact with a focus
Run `/compact` with a focus line, for example:

```
/compact Keep: the owner's quotes word for word with dates; branch@sha per branch; agent ids and worktree paths still live; the fixed list with each item's state; decisions with their why; failed attempts; the state file path <path>. Drop: tool output, file dumps, merged waves' detail.
```

The repo `CLAUDE.md` "Compact instructions" apply on top of the focus.

## 5. After
Read the state file's top block (by section), then start the next wave with the `wave-start` skill.
