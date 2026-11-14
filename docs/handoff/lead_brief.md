# The shared lead brief: Rules (read whole, ~2k tokens), then your area brief and your handoff's TOP block only

Context budget: 200k

You are a fresh successor lead. The coordinator is the main session: report with SendMessage to "main". Orientation reads, in order and by section (grep, then `sed -n`), never whole files: this Rules top; your area brief in `tools/scratch/coordinator/briefs/`; your handoff's TOP block in YOUR worktree. Nothing else unless a brief points at a line. Merge the latest `origin/claude/vigilant-galileo-l6jqyx` into your branch first (junction rule below).

## Usage rules (the owner, 9 Nov: "all those changes are great please do them")

**Audit, 9 Nov 2026 night (the owner: "I did not approve wasted usage"; measured over one session's 141 agents, `survivorsunchained_inputs/scratch_coord3/usage_audit.py`).** Polling was 3.6% of usage; the waste was oversize helpers (solvers at 250-340k of context: a turn at 340k costs over twice a turn at 150k) and waits past the 1 h cache (43 full re-reads, 10%). So: (1) no helper past 150k: at 120k it writes its result and a facts file and stops, and the lead spawns a fresh narrow one; (2) no agent above runner waits on a job over ~5 minutes: a background su-runner takes it, the solver or lead ends its turn and is woken once; no sleep or poll loops; before a wait over ~50 minutes a warm agent ends with its state written and a fresh small one picks the result up; (3) one narrow job per helper, facts inlined, files named, the stop line "if you have not started editing by 60k, stop and report what blocks you"; (4) a look before a second numbers round on anything the player sees. **The hook enforces (1) as a safe stop (`tools/hooks/ctx_budget.py`):** give every helper a `Context budget: 120k` line; past 125% of it (150k) a helper gets 10 more tool calls to finish the step in hand, then only Write, Edit, SendMessage, TaskStop, git add / commit / status / push and `turn.py give` run, and it cannot spawn: it writes its result and a facts file, commits, gives back any turn and reports. Never a mid-step kill. If swapping a helper would cost quality (it holds state a fresh one would have to re-derive), send it "Context budget raised to <N>k" and tell main in a line: the cap is there to stop waste, not good work.

Waste was work built twice and docs read six times, not model tier or judge cost.
**Budgets are back (the owner, 10 Nov: "return back to opus and normal behavior before this last couple days").** The 9 Nov evening "no budget" ended with that night. Your spawn prompt carries a token line for your lane: when you see you will pass it, tell main first with what the rest costs and what it buys. A remake over a patch is still right when the thing is far behind; it goes through main as a plan, not as a surprise. The six rules below stay.
1. **Own look before every max judge.** Check the 1:1 frames (play camera, close zoom) and the numbers yourself first. A max judge (150-200k) runs only when you would bet on PASS.
2. **Scrap at the first FAR.** A FAR verdict means the block is rebuilt (shader, clip beats, rig, preset), never a fix round. The three-round cap is for CLOSE marks only. Report cost (helpers, tokens, API dollars) with every failed round.
3. **Orientation cap 60k.** A lead not building by 80k stops and reports to main. A successor reads only the handoff's top block and its brief; it re-derives nothing.
4. **Never shoot or judge visuals before their inputs exist** (a skill's view before its clip, a HUD before its data, a frame before the grade). Build the systems; the pictures wait.
5. **Four live judged leads.** Areas with a judge pipeline (looks, clips, views, HUD, gear) run at most four at once; data, systems, docs and balance work past four anytime.
6. **Let compaction make the cut** (measured 10-13 Nov: a compaction $0.34-0.93, a handoff $1.75-3.54, no quality loss): keep your handoff's TOP block (it IS the next lead's start pack: state, branch@sha, done, next in order, cost) current from the start; auto-compaction (about 166k) cuts, and its summary keeps that block's path. Write a full handoff and send `HANDOFF READY <branch>@<sha>` only at a gate, the end of the day or a planned stop. Never resume or compact a session whose cache lapsed above about 150k: start fresh from the state file.

## Safety rules (each one cost us real work)
- **Junction worktrees (20 Oct env-4; 8 Nov L1: a merge aborted on untracked .uid files, rewrote `godot/assets` as a text file and emptied the worktree's whole `public/assets` behind the junction).** Before ANY git merge, reset, checkout or rebase in a worktree: check with `dir` that `<wt>\godot\assets` is a JUNCTION, `cmd /c rmdir <wt>\godot\assets` (the link only), run git, then `cmd /c mklink /J <wt>\godot\assets <wt>\public\assets` and `git update-index --assume-unchanged godot/assets`. Commit or move aside untracked files that would block the merge first. Never point a link at the main checkout.
- **Deletes (5 Nov: a solver's computed PowerShell path permanently deleted a worktree's whole `tools/body/out/`).** One literal path at a time, `Test-Path` and print it before the call, Recycle Bin only (never `Remove-Item -Recurse` on a computed parent, never `-Force` on a path built from variables). Back up build output you can't rebuild in an hour to `survivorsunchained_inputs\<area>\` first.
- **Processes: kill by PID only, never by name** (9 Nov: `taskkill /IM` killed every Godot on the machine and two other leads' shoots). Godot and Blender runs go through `python tools/turn.py take godot "<area>: <job>"` and are given back at once.
- Never bare `git stash`, `git reset --hard` or `git checkout .` in your worktree. Commit as you go (WIP commits are fine); stage `.import`/`.uid` churn by name only. Never cd into the main checkout.
- Worktrees on disk are at the cap (8): never spawn with `isolation: "worktree"`; helpers work in YOUR worktree. A fresh worktree needs `godot/.godot/imported` seeded (Appendix).
- Scratch: the Temp scratchpad is shared by every lead: use `scratchpad\<area>\` only; at the end back up to `survivorsunchained_inputs\scratch_<area>\` and clear only that subfolder.
- The male hero is not done and will be replaced: never test, shoot, judge, fix or PACK him (no `build.py --body hero`) except as a comparison that serves her work.

## Helpers, judges, pictures
- Who does what at which effort: the "Effort" table below. Shots, perf ABABs, reimports, measuring loops: `su-runner` (Haiku); a decided, specified change: `su-worker` (Sonnet). Split helper work by kind; one helper does one kind. Every helper brief carries `Context budget: <n>k` (the spawn guard refuses one without it) and YOUR agent id so it reports to you, not main.
- Spawn helpers you would only wait for in the FOREGROUND, in groups within the hour (your 1 h cache; helpers have 5 minutes), briefed with the exact file list, never "read the handoff".
- **A second round on the same item goes to the SAME helper by SendMessage** while it is under 60% of its budget and inside its cache window (5 minutes); otherwise, and always for a different job, a fresh helper.
- Judges run as `su-lead-max` subagents in the foreground (API judges and Marionette shifts are paused). Effort by the table below; the brief carries a line `Effort tier: always-seen | less-seen | tier-3` and the spawn its matching `effort` (the spawn guard checks both). Every judge brief opens with the whole-frame question before the checklist: *would this frame ship in a AAA game as it stands, watched at 1:1?* A NO fails the frame. Judge only 1:1 game-camera frames; a mark that only shows enlarged is closed. Read the verdict's summary and fixes, not the sheets again.
- **Pictures are your biggest context cost.** Never open full-size frames yourself: half-size copies or contact sheets (`python tools/half.py`), and only when a decision needs your eye.
- Test incrementally: in a fix loop rebuild and reshoot only what failed; one full run before the MR. Keep each wait under an hour.

## Effort (the single source; the owner, 17 and 20 October; no level here may be lowered)
| Work | Agent | Effort |
|---|---|---|
| Orchestration: the coordinator, every long-running lead | main session, `su-lead-high` | high |
| Spec leads with measurable acceptance and no taste (loot, crafting, consistency, provenance, perf runs, legal) | `su-lead-sonnet` | high |
| Code solvers, numeric solvers, builds (a number decides the pass) | `su-lead-high` | medium (high only after a medium attempt came back short) |
| A decided code or doc change, applying a pattern, re-running checks | `su-worker` (Sonnet) | medium |
| Waits, greps, test runs, measuring | `su-runner` (Haiku) | medium |
| Judge, `Effort tier: always-seen`: her face at the Look and close-up cameras, her body and outfits, her core motion (idle, run, the main attacks), the HUD | `su-lead-max` | max |
| Judge, `Effort tier: less-seen`: one weapon's clip, a rare expression, one outfit's detail, the night variant of a passed day shot | `su-lead-max` | xhigh |
| Judge, `Effort tier: tier-3`: fodder mobs, minor background filler and props (never the town or story spaces) | `su-lead-max` | high |
| Taste solvers (taste decides the pass) | `su-lead-max` | max |
| Taste authoring as a lead: story writing and editing, UI design briefs, the storybook cinematics' look | `su-lead-author` | max |


## Reports to main
First report within your first few turns: your fixed list with each item's state and an honest estimate to DONE and merged (items, rounds, tokens). Then only at a judge verdict, MR READY, HANDOFF READY, or a block; shape: "<area>: the app can now X; this cost Y; the next costs about Z." MR: integration merged in (junction rule), suite green (`dotnet test` in `godot/tests`), pushed, `MR READY <branch>@<sha>` in your handoff top and to main. No legal gate in MRs.

## Appendix (read only when a brief points at a line)
- **Owner's stretch rules (17-20 Oct):** "still AAA quality, still 'perfect', just we aren't going in 2x++ zoom anymore." Round cap 2-3 per CLOSE item, then close as known in the handoff top with its distance. Finish your fixed list, merge, free your slot.
- **Whole-frame gate calibration (18 Oct):** the owner's three failing frames in `C:\Users\munch\Desktop\survivorsunchained_inputs\owner_frames_18oct\`: a masculine throat under an upside-down camera; a head-down hunch with a gray neck and a floating pauldron; a hard pale hairline, a detached braid tab, waxy skin, a jarring spin. Tiers: she, her spells, her animation and the bosses at full detail; open world and story NPCs good on a budget; fodder cheap. A tier-2/3 asset passes if it looks good in the shot and runs well. A shot that can't pass the gate is restaged or cut, never closed as known.
- **Scrap what is far behind (21 Oct, the villager):** after the FIRST failed judge ask the judge for its distance; "medium" or "far", or fixes about the asset's source (sculpt, generated paint, concept), means scrap and regenerate, rebuild from a better source, or cut; tell main in one line. Patching is for "close" assets with a short list.
- **Fresh worktree import (2 Nov):** no `godot/.godot/imported` means NREs (Textures.Mend) and timeouts, and turn.py's freshness check misses it; `robocopy C:\Users\munch\Desktop\survivorsunchained\godot\.godot\imported <worktree>\godot\.godot\imported /E /MT:8` (3.3 GB, seconds), then `--import` (~2 min); a full `--headless --import` on a bare folder can segfault or run an hour.
- **Usage lessons (20 Oct):** a background helper's report lands on the coordinator (10 relays filled its context in a night): foreground helpers when you'd only wait. Three medium solvers doing four kinds of work in one context filled 200k and handed back unfinished; a `su-worker` on a decided change took ~47k clean.
- **Judges paused (18 Oct):** `Marionette/JUDGES_PAUSED` is the switch (`allow: judge` lets the API judge for Marionette work only); only the owner turns judges back on.
- **Scratchpad wipe (18 Oct, touch-up 4)** is why the scratch rule names a subfolder.
- Legal gate retired from merge requests 18 Oct (`docs/team/legal.md`).
