---
name: usage-audit
description: Weekly usage audit of Survivor Unchained sessions: spend by model, compactions vs handoffs, shell-output dollars, fixed overhead, cold rewrites, this week vs last. Use when asked for the week's usage, at the end of a week, or before changing a usage rule.
---

# Usage audit

One script reads every transcript under `~/.claude/projects/*survivorsunchained*` and `*Marionette*` and prices it at list price (cache writes at their own 5-minute or 1-hour price).

## Run it (about 3-4 minutes; in the background)

```bash
mkdir -p .quiet && python tools/scratch/coordinator/usage_cmp.py --days 7 > .quiet/usage_audit.log 2>&1
```

- `--end` is the last day of the week (default today, Pacific); `--days` the length (default 7). The previous period of the same length is "last week".
- `--roots survivorsunchained,Marionette` picks the project folders.
- Run it with `run_in_background`; read the log when it finishes (it is about 60 lines).

## What it prints, per period
- **Spend by model** (fable, opus, sonnet, haiku) and by part: input, cache writes, cache reads, output.
- **Compactions vs handoffs**: how many of each and what the compactions' rewrites cost. More compactions and fewer handoffs is the aim.
- **Shell output**: tokens and dollars carried from Bash/PowerShell results until the next compaction. Reads through the shell (`sed`, `grep`, `cat`) were two thirds of it on 10-13 November.
- **Fixed overhead**: each session's first request minus its brief (system prompt, tools, CLAUDE.md, MEMORY.md, skill and agent listings).
- **Cold rewrites**: cache writes after a lapse (more than 5 minutes, or an hour for 1-hour leads).
- **Per agent type** table, then one line: THIS WEEK vs LAST.

## Report
Lead with the total and the change from last week, then the two biggest movers and what drove them (by type and by part). Name a rule to change only with its measured cost. Never propose lowering a model, an effort level or a judge (the owner: quality first).
