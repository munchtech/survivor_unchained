# Handoff: the coordinator (main session)

## Start here (startup reading, nothing else)
1. This page.
2. `docs/team/RESUME.md`, its top section only (the current state, the restart order, the owner's pending decisions).
3. Restart each lead it lists with `docs/handoff/lead_brief.md` (the shared brief: paste it, then add the area's worktree, where the predecessor stopped, and its steps).
4. Check for live agents from older sessions before you spawn: `find ~/.claude/projects/C--Users-munch-Desktop-survivorsunchained/*/subagents -name '*.jsonl' -mmin -15` (outside your own session). For any you find, ask that session to TaskStop it (`mcp__ccd_session_mgmt__send_message`; match the session by its lastActivityAt) unless its work is still wanted, and release any stale turns in `tools/turn.py show`.
Open README, OWNER_NOTES or a handoff only when a step needs them, by `grep -n` and the exact lines. The rules are in memory and README "Working lean"; you don't need to re-read them to start.

From the coordinator session that ran 3 to 6 October 2026. Read this after `docs/team/README.md`, `RESUME.md` and `OWNER_NOTES.md`. Your memory (MEMORY.md) holds the owner's standing direction.

## What the coordinator does
- **Runs the team:** 3 to 5 leads at once, spawned as fresh successors from `docs/handoff/<area>.md`, typed by model and effort: long-running leads on `su-lead-high` (pass `effort: "high"` on the spawn, so it holds even if the type files haven't reloaded), max effort only in short-lived `su-lead-max` judges and solvers, and the story writer and editor on `su-lead-max`; also `su-lead-sonnet`, with `su-worker` and `su-runner` for leads to delegate to; README "Working lean", memory `effort-policy`). Leads are restarted in RESUME's order.
- **Merges every lead's push** into the integration branch `claude/vigilant-galileo-l6jqyx` in the main checkout (`C:\Users\munch\Desktop\survivorsunchained`, always on that branch), tests, and pushes.
- **Judges before the owner sees:** looks at every sheet at full size, sends notes back, and only then sends the owner the good ones (`SendUserFile`, with a one-line caption). Honest verdicts, never "done" early.
- **Relays the owner's words** to the right lead, verbatim where it matters, and records decisions in `docs/team/OWNER_NOTES.md` and in memory.
- **Does the mechanical refit** after face changes (docs/handoff/outfits.md, "Refits"). The outfits themselves are now a lead's (`su-lead-high`, judged by `su-lead-max`).


Older blocks: history/coordinator.md (grep by keyword, never read whole).
