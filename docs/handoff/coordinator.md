# Handoff: the coordinator (main session)

From the coordinator session that ran 3 to 6 October 2026. Read this after `docs/team/README.md`, `RESUME.md` and `OWNER_NOTES.md`. Your memory (MEMORY.md) holds the owner's standing direction.

## What the coordinator does
- **Runs the team:** 3 to 5 leads at once, spawned as fresh successors from `docs/handoff/<area>.md`, typed by model and effort: long-running leads on `su-lead-high` (pass `effort: "high"` on the spawn, so it holds even if the type files haven't reloaded), max effort only in short-lived `su-lead-max` judges and solvers, and the story writer and editor on `su-lead-max`; also `su-lead-sonnet`, with `su-worker` and `su-runner` for leads to delegate to; README "Working lean", memory `effort-policy`). Leads are restarted in RESUME's order.
- **Merges every lead's push** into the integration branch `claude/vigilant-galileo-l6jqyx` in the main checkout (`C:\Users\munch\Desktop\survivorsunchained`, always on that branch), tests, and pushes.
- **Judges before the owner sees:** looks at every sheet at full size, sends notes back, and only then sends the owner the good ones (`SendUserFile`, with a one-line caption). Honest verdicts, never "done" early.
- **Relays the owner's words** to the right lead, verbatim where it matters, and records decisions in `docs/team/OWNER_NOTES.md` and in memory.
- **Does the mechanical refit** after face changes (docs/handoff/outfits.md, "Refits"). The outfits themselves are now a lead's (`su-lead-high`, judged by `su-lead-max`).

## Procedures
- **Merging a lead:** `bash tools/scratch/coordinator/merge_lead.sh <agent-id>`. It sets aside untracked `.uid` and `.import` files that would block the merge, merges, and stops on a conflict.
  - Resolve conflicts by keeping both sides' intent: Game.cs's `Tour` flags are a common clash; combine the bool lists.
  - Then `dotnet test` in `godot/tests` before every push.
- **After any Godot import in the main checkout:** revert `godot/project.godot` (the editor drops `screen_space_aa=0`) and the regenerated `.import` files: `git status --short | grep '^ M' | grep '\.import$' | cut -c4- > imp.txt; git checkout --pathspec-from-file=imp.txt --`.
- **Context checks:** on every report from a lead, `python tools/scratch/coordinator/ctx.py <agent-id>`. Past about 300k, ask for the handoff. Before resuming a lead after a usage stop, check first. The task `.output` files are empty after a session restart; the script reads the transcripts under `~/.claude/projects/<project>/<session>/subagents/`.
- **Turns** (`tools/turn.py`): `gpu` (ComfyUI, TRELLIS, MoGe; one), `blender` (two), `godot` (three), with a fair queue. The coordinator takes turns too for builds and shots.
- **Big inputs the handoffs mention** (the face leads' reference portraits, TRELLIS heads and builds in face4 to face8, and the creatures lead's boar work, about 8.7 GB) are copied out of the old session's scratchpad to `C:\Users\munch\Desktop\survivorsunchained_inputs\<folder>\`, outside the repo. Point the face and creatures leads there.
- **Scratch scripts the handoffs mention** (face4 to face8, perf, combat6, cin, anim, vfx, legal3 and so on) are mirrored in `tools/scratch/<folder>/`, because the old session's scratchpad may be cleaned. Repoint paths when you use them.

- **Weekly usage audit:** `python tools/scratch/coordinator/usage_week.py` (and `usage_more.py`) reads the last eight days of transcripts: cost at list price, cache rewrites after waits, contexts over 300k, image re-reads. Run it at the start of each week and act on what it shows.
- **Settings that save tokens** live in `.claude/settings.json`: a one-hour cache for subagents and a 400k auto-compact backstop.

## The owner
- Pronouns: they/them unless the owner says otherwise. Some leads wrote "he"; don't repeat it.
- British spelling. Short, plain updates: what changed, what's next, and any decision that's theirs. Pictures over descriptions.
- They play the build and send crops; take every note seriously, sort it by area into OWNER_NOTES, and route it.
- The bar: "we are striving for perfection"; soul over generic; no AI-looking UI; sex appeal "tho not at the cost of looking bad"; coverage pixel-perfect.
- Safety:
  - never print or commit tokens;
  - never enter passwords;
  - downloads are consented, from reputable sources, with checksums logged;
  - never delete permanently (the Recycle Bin, for the owner to empty), and never move long-path folders there;
  - never bare `git stash`.
- Usage: tokens are precious. Save everywhere it doesn't cost quality, and raise effort freely where it does.

## Starting fresh
**Near a restart, don't start successors (the owner, 7 October).** Within about 50k of your 250k, or once a wrap-up is planned, a lead that hands off cleanly waits for the next coordinator: list it first in RESUME's restart order. A new coordinator can't reliably reach your agents, and a successor's ~50k onboarding would be wasted on a short stretch.
The owner starts each new coordinator with the prompt in `docs/handoff/START.md`. Tell the owner in one line when it's time: at about 250k of your own context, at a new wave, or after a usage reset. Keep this page and RESUME current, so that a fresh start costs nothing extra.

## Wrapping up before a fresh start (always, before telling the owner it's time)
A new coordinator can't reliably reach the old session's agents, so never switch mid-task:
1. Bring every running lead to a clean point: finished piece committed and pushed, its handoff or status page current, any turns released. Use a full handoff for those past about 300k, and a "paused here; next:" line for the rest.
2. Merge every branch, revert any import churn, run `dotnet test`, and push. Leave nothing uncommitted in the main checkout except files the owner is handling.
3. Update RESUME.md: each area's exact state, what's half-built and on which branch, and the restart order. Update OWNER_NOTES with anything the owner said, marking what's done. Record the owner's pending decisions in both.
4. Update memory with any new standing direction.
5. Then tell the owner in one line, pointing at START.md. Give the line only when steps 1 to 4 are done.

## Tokens and quality, always
The owner, 7 October: the cheapest route (lower effort, smaller model, any saving technique) that ends at the same quality, always, without asking; raise at once when quality is at risk. Measure each wave's tokens per finished piece against wave 1 (7 October: max-effort leads filled 48k to 300k in about 30 minutes; the hour cache works, 0 five-minute writes) and report the real saving.

## State at handoff
From the coordinator of 6 and 7 October. Everything is merged and green (775); no lead is running. RESUME.md has the restart order. The new workflow (README "Working lean", 7 October) is in place: agent types by model, an hour's cache for subagents, handoff at 300k, and the weekly audit. The owner deleted docs/voice/samples on purpose: the final voices will be made with ElevenLabs.
