# Handoff: the coordinator (main session)

From the coordinator session that ran 3 to 6 October 2026. Read this after `docs/team/README.md`, `RESUME.md` and `OWNER_NOTES.md`. Your memory (MEMORY.md) holds the owner's standing direction.

## What the coordinator does
- **Runs the team:** 3 to 5 leads at once, spawned as fresh successors from `docs/handoff/<area>.md`, typed by model and effort (`su-lead-max`, `su-lead-high`, `su-lead-sonnet`, with `su-worker` and `su-runner` for leads to delegate to; README "Working lean", memory `effort-policy`). Leads are restarted in RESUME's order.
- **Merges every lead's push** into the integration branch `claude/vigilant-galileo-l6jqyx` in the main checkout (`C:\Users\munch\Desktop\survivorsunchained`, always on that branch), tests, and pushes.
- **Judges before the owner sees:** looks at every sheet at full size, sends notes back, and only then sends the owner the good ones (`SendUserFile`, with a one-line caption). Honest verdicts, never "done" early.
- **Relays the owner's words** to the right lead, verbatim where it matters, and records decisions in `docs/team/OWNER_NOTES.md` and in memory.
- **Does the mechanical refit** after face changes (docs/handoff/outfits.md, "Refits"). The outfits themselves are now a lead's (`su-lead-max`).

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

## State at handoff
See RESUME.md. Everything is merged and green (774). No lead is running.
