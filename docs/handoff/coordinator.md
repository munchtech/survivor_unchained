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
  - **When the lead's work is finished and merged, remove its worktree in the same turn** (`powershell -NoProfile -ExecutionPolicy Bypass -File tools/scratch/coordinator/wt_remove.ps1 <path>`; links first, long paths handled). Disk rules: `CLAUDE.md` (the owner, 10 October). End of day: `python tools/scratch/coordinator/wt_audit.py`, remove the merged and clean ones, and report any older than 48 h that are unmerged or dirty.
  - Resolve conflicts by keeping both sides' intent: Game.cs's `Tour` flags are a common clash; combine the bool lists.
  - Then `dotnet test` in `godot/tests` before every push.
- **After any Godot import in the main checkout:** revert `godot/project.godot` (the editor drops `screen_space_aa=0`) and the regenerated `.import` files: `git status --short | grep '^ M' | grep '\.import$' | cut -c4- > imp.txt; git checkout --pathspec-from-file=imp.txt --`.
- **Context checks:** on every report from a lead, `python tools/scratch/coordinator/ctx.py <agent-id>`. Past about 300k, ask for the handoff. Before resuming a lead after a usage stop, check first. The task `.output` files are empty after a session restart; the script reads the transcripts under `~/.claude/projects/<project>/<session>/subagents/`.
- **Turns** (`tools/turn.py`): `gpu` (ComfyUI, TRELLIS, MoGe; one), `blender` (three), `godot` (four), with RAM and VRAM guards, with a fair queue. The coordinator takes turns too for builds and shots.
- **Big inputs the handoffs mention** (the face leads' reference portraits, TRELLIS heads and builds in face4 to face8, and the creatures lead's boar work, about 8.7 GB) are copied out of the old session's scratchpad to `C:\Users\munch\Desktop\survivorsunchained_inputs\<folder>\`, outside the repo. Point the face and creatures leads there.
- **Scratch scripts the handoffs mention** (face4 to face8, perf, combat6, cin, anim, vfx, legal3 and so on) are mirrored in `tools/scratch/<folder>/`, because the old session's scratchpad may be cleaned. Repoint paths when you use them.

- **Background runners' and judges' reports reach you, not the lead (10 October).** A lead that ends its turn "waiting" on one stops and won't wake. Relay each result with SendMessage (condensed), and save a judge's full verdict next to its sheets: `python <scratchpad>/lastmsg.py <agent-id> <dir>/verdict.md` (reads the last text of `~/.claude/projects/<project>/<session>/subagents/agent-<id>.jsonl`; a copy is in tools/scratch/coordinator/lastmsg.py). Leads are now told to run a runner or judge in the foreground when their next step depends on it.
- **Weekly usage audit:** `python tools/scratch/coordinator/usage_week.py` (and `usage_more.py`) reads the last eight days of transcripts: cost at list price, cache rewrites after waits, contexts over 300k, image re-reads. Run it at the start of each week and act on what it shows.
- **Lean agent types (10 October):** every type now lists only the tools it uses (`tools:` in `.claude/agents/*.md`; `su-worker-medium` is in `~/.claude/agents`). Without that list an agent loaded every tool (the browser, computer use, artifacts, docs): about 40k of its 48-53k starting context. A runner with 5 tools starts at 12.8k. Types load at session start, so **on your first spawn, check the start**: spawn `su-lead-max` (effort low) with "reply ok and list your tool names; Context budget: 60k" and confirm it starts near 15k, not 51k. If a lead needs another tool (the browser for downloads), spawn it with `subagent_type: claude` for that job. **Check the type listing too:** a description with an unquoted `: ` fails to parse and the old user-level type in `~/.claude/agents` loads instead, silently (su-lead-max did, until 10 October). Quote descriptions.
- **`isolation: "worktree"` branches from `main`, which is a stub (the initial commit only).** A worker spawned that way must first `git reset --hard <integration commit>` in its new worktree: say so in its brief.
- **Settings that save tokens** live in `.claude/settings.json`: a one-hour cache for subagents and a 400k auto-compact backstop.

## The owner
- Pronouns: they/them unless the owner says otherwise. Some leads wrote "he"; don't repeat it.
- Short, plain updates: what changed, what's next, and any decision that's theirs. Pictures over descriptions.
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
**Near a restart, don't start successors (the owner, 7 October).** Within about 50k of your 250k, or once a wrap-up is planned, a lead that hands off cleanly waits for the next coordinator: list it first in RESUME's restart order. A new coordinator can't reliably reach your agents, and a successor's ~50k onboarding would be wasted on a short stretch. If the owner can't restart soon, start the successor anyway: progress is worth more than one onboarding.
The owner starts each new coordinator with the prompt in `docs/handoff/START.md`. Tell the owner in one line when it's time: at about 250k of your own context, at a new wave, or after a usage reset. Keep this page and RESUME current, so that a fresh start costs nothing extra.

## Wrapping up before a fresh start (always, before telling the owner it's time)
A new coordinator can't reliably reach the old session's agents, so never switch mid-task:
1. Bring every running lead to a clean point: finished piece committed and pushed, its handoff or status page current, any turns released. Use a full handoff for those past about 300k, and a "paused here; next:" line for the rest.
2. Merge every branch, revert any import churn, run `dotnet test`, and push. Leave nothing uncommitted in the main checkout except files the owner is handling.
3. Update RESUME.md: each area's exact state, what's half-built and on which branch, and the restart order. Update OWNER_NOTES with anything the owner said, marking what's done. Record the owner's pending decisions in both.
4. Update memory with any new standing direction.
5. Then tell the owner in one line, pointing at START.md. Give the line only when steps 1 to 4 are done.

## Tokens and quality, always

- **A lead's workers report to you, not to the lead (11 October).** A background worker or judge spawned by a lead sends its completion notice to the main session; the lead waits forever. Relay each one (SendMessage to the lead) and tell leads to have their workers SendMessage them before finishing. A notice whose task id isn't on the roster is almost always one of these.
- **The budget hook reads the brief only (11 October fix).** It used to match README's example "Context budget: 120k". Write `Context budget: 300k` in every brief.
The owner, 7 October: the cheapest route (lower effort, smaller model, any saving technique) that ends at the same quality, always, without asking; raise at once when quality is at risk. Measure each wave's tokens per finished piece against wave 1 (7 October: max-effort leads filled 48k to 300k in about 30 minutes; the hour cache works, 0 five-minute writes) and report the real saving.

## State at handoff
From the coordinator of 10 October (session 181eef02). Wave 1 restarted, ran about three hours, hit the weekly limit, resumed on usage credit, then was wound down by the owner. Integration is unchanged apart from docs (roster, OWNER_NOTES 10 October: the neck note, nipple show-through, boots). No area passed its judge except rendering's FSR 2 native, which waits to merge alongside face. Every lead stopped with a "Paused here; next:" block on its own branch; RESUME "10 October" has the four branches, the restart order and the scratch backup. Token use, measured with every judge, solver and runner (`tools/scratch/coordinator/wave_cost.py <session>`, usage_week.py's list prices): 7 October (session 0b33992d, 1 h 40 min) about $75, $45 an hour; 10 October (3 h 40 min) about $150, $41 an hour. The leads got about four times cheaper per hour (four max leads $40 in 45 min; five high leads $44 in 3 h 40 min), but judges and solvers took 70% of the spend ($104 over 15 spawns, each filling 180-366k with images and their own measuring). So the saving moved, not landed. Fix adopted in README "Working lean": lean judges.

**Coordinator 91211d34 (10 October, evening):** restarted wave 1 in the old worktrees; the owner's disk cleanup (CLAUDE.md, wt_remove.ps1); the context-budget hook; lean agent types. Wound down at 245k with rendering handed off and ready to merge with face, and the other three asked to pause (RESUME "10 October, late"). If their PAUSED lines didn't arrive, check each branch's handoff block and `ctx.py` before restarting.

**Coordinator ba85aba8 (12 October):** merged Act 1 boss health, classes phase 2, her hair swing (16/18), relaxed turns (blender 3, godot 4, VRAM guard). Ran classes, face, hero, outfits and animation, then wound all five down on the owner's word (RESUME "12 October, evening"). Lessons: leads hit their ~250-300k budget in 1-4 hours, so plan a successor per lead per long stretch; a lead's report can say "merge-ready" while a merged piece later fails a check (Butcher's Hour), so ask for the before-the-owner-plays checks before merging live gameplay; another session may commit to integration in the main checkout (free_ram tools): fetch before every merge. This session's scratchpad holds leads' scratch: keep it.

**Coordinator 1515c1de (12 October, night):** ran classes, face, outfits and animation (hero held: Blender turns). Merged the get_up braid and ponytail, the Butcher's Hour fix and the Flare press-stagger fix with Act 1 retuned (RESUME "12 October, night"). Lessons: every su-lead-high lead filled 250-280k in 1.5-3.5 h, so plan a successor per lead every couple of hours and keep onboarding small; most of their spend was their own measuring and pictures, so brief successors to hand build-and-measure loops to runners and take the build to a judge before chasing every number; give a solver one item and a named route, and make it build before measuring (several solvers ran out measuring); judges rule on what the eye sees (the neck and reach_coals rulings). Run a narrow judge yourself (foreground, Context budget: 100k) when a lead hands off just before one. A lead often wakes once more after its "HANDOFF READY" when its background batch ends: check the branch head before spawning from it. Scratch to keep: this session's scratchpad (classes, face, outfits, anim).
