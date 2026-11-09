# coordinator.md history

Moved 9 Nov 2026 from docs/handoff/coordinator.md, nothing edited.

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
- **Settings that save tokens:** a 400k auto-compact backstop in `.claude/settings.json`; the cache TTL is per agent type (26 Oct): `experimental: cacheTtl: 1h` in the su-lead-high and su-lead-sonnet agent files, the 5m default for the rest.

- **A `su-lead-max` LEAD needs "Spawning: allowed" as its brief's first line (29 Oct).** The spawn guard reads only the first brief, so without that line it can't start helpers, and a later message can't unlock it (Storybook 2 stopped on this). Judges and solvers don't need it.

- **Lessons from b9e8a09f (2 Nov):** (1) Quiet relays really matter: relaying every lead update filled 250k in one evening; tell the owner only decisions and milestones. (2) Run `ctx.py` on every lead report; don't rely on self-reported cost. (3) Near 200k, don't start successors (VFX 8 wasted ~44k). (4) Before merging any lead branch, check `git ls-tree <branch> godot/assets` is a 120000 symlink: classes-15 had committed the junction's contents as 861 files and the merge aborted; fix on the branch with `git rm -r --cached godot/assets` + `git update-index --add --cacheinfo 120000,<blob>,godot/assets`. (5) `dotnet test` on the .sln runs nothing: use `godot/tests/Tests.csproj`.

- **Lessons from 29291afc (3 Nov):** (1) The demo reset worked: four Phase 0 MRs + a whole-loop gate + two gate leads, all merged in one session (~3.1M), and the gate came out at six items, none art. Keep the gate as the only backlog until the demo is tagged (`docs/team/DEMO_PLAN.md`). (2) Never chain `git push` after a grep of the suite log: `grep | tail` succeeds on "Failed!" too; I pushed one red commit that way. Push only after reading the Passed!/Failed! line. (3) `merge_lead.sh` runs for minutes on the .uid/.import set-aside loop: run it in the background with the suite in the same command. (4) `git worktree remove` leaves an empty locked folder when the shell's cwd is inside it: `cd` out, then `cmd /c rmdir`.

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
5. **Stop every agent (19 October: a "paused" lead from two coordinators back was still alive and kept relaunching checks in its successor's worktree).** A lead that writes "Paused here" keeps running: TaskStop every lead, runner, solver and judge this session started. Then confirm that nothing is live: no `subagents/*.jsonl` of this session changed in the last 10 min, and `tools/turn.py show` lists no turn of yours.
6. Then tell the owner in one line, pointing at START.md. Give the line only when steps 1 to 5 are done. The owner can restart as soon as you say so; it's on you that nothing is left running.

## Tokens and quality, always

- **A lead's workers report to you, not to the lead (11 October).** A background worker or judge spawned by a lead sends its completion notice to the main session; the lead waits forever. Relay each one (SendMessage to the lead) and tell leads to have their workers SendMessage them before finishing. A notice whose task id isn't on the roster is almost always one of these.
- **The budget hook reads the brief only (11 October fix).** It used to match README's example "Context budget: 120k". Write `Context budget: 300k` in every brief.
The owner, 7 October: the cheapest route (lower effort, smaller model, any saving technique) that ends at the same quality, always, without asking; raise at once when quality is at risk. Measure each wave's tokens per finished piece against wave 1 (7 October: max-effort leads filled 48k to 300k in about 30 minutes; the hour cache works, 0 five-minute writes) and report the real saving.

## Lessons that still apply (from coordinator_history.md)
- Fetch before every merge: other sessions commit to integration. Check a handed-off lead's branch head before spawning from it (it often wakes once more).
- Never merge on a picture the judge hasn't ruled on. Ask for the before-the-owner-plays checks before merging live gameplay.
- Rebuild a lead's art on the latest integration before merging binaries. After any body build, refit every grip and gate it on its correctives (grep the GLB for `elbow_point` against integration's).
- When the art moves on, TaskStop the predecessor's runners (grep `subagents/*.jsonl` for the job); a leftover runner overwrote newer art once.
- Helpers' reports land on you, not the lead: relay each one condensed, and copy sheets out of `.shots` before removing a worktree.
- Leads fill about 240k in 1-2 hours: plan a successor per lead per stretch. You reach 250k in one long evening of relays.
- Diagnose before fixing; two tools disagreeing means a ground-truth measurement in Godot, not a third model.
