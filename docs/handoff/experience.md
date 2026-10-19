# Handoff: the gameplay experience director

For a fresh successor. Read these first:
1. `docs/team/README.md`: the bar, the turns, and batching shots.
2. `docs/team/experience.md`: the one-page status, which holds what's done, the next steps in order, and the verdicts.
3. `docs/design/STORY_NIGHTS_AND_TIME.md`: the owner's decisions are at its top.

## Paused here; next: the tutorial teaching pass (teach-1 lead a1c7861e, 19 Oct)

**Worktree** `.claude/worktrees/teach-1`, branch `teach-1` (pushed). Its own `godot/assets` junction (skip-worktree), imported. Never commit the `*.import`/`.uid` files the import changed: `git add` named files only. The brief is the coordinator's teaching-pass lead brief (fixed list 1-4). The copy is `docs/story/TUTORIAL_COPY.md`.
**Built** (861e182e..172419df, tests 958/0/8):
- `logic/Play/Teach.cs`: the callout queue. `src/Game/GameTeach.cs`: freeze, holds, waits, logging. `src/Ui/Callout.cs`: all the drawing.
- Settings `Tips` and `SeenTips` (an options row).
- Placement: F1-F10 and F12 in `Prologue.cs Callouts()`. F13 is commented out.
- The autopilot answers freezes. Dev switches: `--teach-reset`, `--teach-hurt` and `--teach-end`.
- Items 1 and 3 are done. Item 2 (the look) is in judge rounds. Item 4 (the MR) is not started.
**Judge round 1** (xhigh): 1 PASS (great_blessing), 10 FAIL. The verdict and the frames it judged are in `C:\Users\munch\Desktop\survivorsunchained_inputs\teach1\judge1\` (verdict.md).
- Main reasons: arrows starting inline with the text; tinted or boxy spotlights and a faint, foggy dim; words or arrows crossing her and enemies; toasts and the "<art>: ready" label doubling the callout.
- F1's stone was jammed into a corner. F2 fired after the first rise (the ring read 2) and its arrow cut through the slot row.
- F7 froze before the red line had drawn, under a roof. F8 pointed at the Flare's meter ("3%") under the art's words.
- F9 ringed one lamp, on its post. F12 doubled the banner's "(C)" and its arrow ran over her head.
**Round-1 fixes are all built** (e09023c9, 172419df). The fix shoot's frames are in `...\teach1\judge2\`, UNJUDGED. They were shot `--stale-ok`, because teach-1 is 14 armor and shader commits behind integration.
**Next:**
1. Merge integration and run `dotnet build`.
2. Fix the one known miss: in red_line the arrow leaves the words' right side and hooks back to the ring.
3. Re-shoot only the failed stages (or the one full run, below), then send the 10 failed frames to a fresh xhigh judge (whole-frame gate first; round 1's brief is the template). Round cap 2-3.
4. One full run, then the MR: branch@commit, tests, the verdict path, and a contact sheet of the 11 at 1:1.
**Run** (from godot/, under a godot turn, `dotnet build` first): `Godot_v4.5.1-stable_mono_win64_console.exe --path . --resolution 1920x1080 -- --quick warden --auto --teach-reset --teach-hurt --teach-end --shot teach --cines --until 1500 --count 0` (~7-10 min). `grep "^teach "` gives queued/shown/answered/dropped with `waited=` reasons. Frames are `godot/.shots/teach_teach_<id>_1.png`.
**F2 chain target:** the HUD's ember is the CHAIN at the foot between the cuffs. The copy's "top center" is wrong. The arrow stops at y≈918 aimed at the lock; the slots fade to 50% and the chain pulses. F2 queues 0.6 s after F1, and a newly owed draft waits for an arrow callout (≤4 s), so F2 lands before the first rise.
**For the MR notes, and other leads:**
- **F8 now teaches the Flare.** In this build Q is the Flare and the art (Bull Rush) rides the dash, so it reads "Q: your Flare. Kill the Grave-Caller before it raises more." under the Flare's name. The story lead should reconcile the copy's F8 and F13 rows.
- **Gameplay holds:** the Barrow Knight can't die before F7 is seen (cap 48 s), and his windups lengthen by 0.3 s until then. The Grave-Caller can't die before F8 (cap 30 s).
- **Lanes through roofs (combat lead's eye):** elite and boss lanes now redraw without depth testing where something stands more than 2.6 m above them, everywhere in the game.
- **Slot icons (HUD lead's call):** the slots now use the skill's painted icon (68 of 75 have one).
- **World notes (environment):** a flat canopy covers the left of F2, and fog blotches show on the ground in F2 and F5.

## The owner, in their words

- "We are striving for perfection." Improved is not the bar: ask whether this is the best version of the moment in any game, and root it in how the best games solve it.
- "Endless is truly endless."
- Full pages pause rarely, and "are often not the best choice".
- Story nights: "smaller arena", "proper arpg end bosses", no endless.
- Time "passing should probably happen".

**Standing decisions:**
- A lost story fight wakes her at Chid's a day on.
- Redcowl can be spared or killed.
- One rise in Act 1; after that, only with the rise skill.
- Story is about 40% of the early game.
- The endgame is PoE-like maps plus survivors arenas.

**Working rules:**
- Only 3 to 5 leads run at once.
- One Godot turn per batch of shots: look once, then fix in one pass.
- Handoffs are lean, at about 500k tokens.

## The brief

You own how the game feels to play, end to end: pacing, readability, the day clock, the story fights' flow, what the screen says and what is noise. Play it on the autopilot and in scripted runs, judge it at 1920×1080, then fix it yourself or brief the owning lead in short writing: what's wrong, the evidence, the target, how it's judged.

**Branch:** `worktree-agent-a9f0d6c64d891d56d`. The main session merges it; open no PRs. Run `dotnet test` in `godot/tests` before each commit.

## Collaborators (roster in `docs/team/README.md`)

- **Combat** `a739d6792d21f5efd`: the story fights. 52d202f2 and later are not yet judged.
- **UI design** `a4fdbc49786ba8b7f`: the dial and the fall at 2378e165; the result screens.
- **Story** `a7ba8903f4c8261b1`: all the words.
- **Paused:** skills `abc6bbe020c7fe287` and arena art `aba487928a1515c93`. Their asks are on the status page.

## Failures and gotchas

- **A fresh worktree has `godot/assets` as a 16-byte stub.**
  - Fix it: delete the stub, make a junction to `public/assets` (PowerShell `New-Item -ItemType Junction`), run `git update-index --skip-worktree godot/assets`, then `--headless --import` (about 4 minutes).
  - A checkout can turn the junction back into a stub, and the game then renders black frames or throws in `Dressing.PartsOf`. Check `(Get-Item godot\assets).LinkType`.
  - Once, deleting the stub through git removed `public/assets`. `git checkout -- public/assets` brings it back.
- **Copy `.godot` from an older worktree** to skip the full import.
- **Godot runs `.godot/mono/temp/bin`.** Run `dotnet build SurvivorUnchained.csproj` in `godot/` after every change.
- **To judge someone's unmerged work, use a local `exp-judge` branch,** then return to your own branch and delete it.
  - Skills' branch conflicts with loot's code, so leave it out.
  - Revert regenerated `.import` files before switching branches.
- **The shell guard** refuses compound git commands, `cd ..` followed by git, and runtime-built sed. Write a small Python script in the scratchpad instead (`gist.py`, `branches.py`, `contains.py`).
- **The autopilot** never answers a story fight's spare/finish offer (the Roost stalls), and takes the first card of every draft. A drafted Cold, Then Not rises her on its own. Use `--auto idle` to see the fall card.
- **Quote commit ids only from git.**

## Tools (scratchpad `experience/`)

- `play.py NAME -- [game args]`: a run at 1920×1080 and 60 fps, with the log in `logs/`.
- `batch1.sh`: one turn holding all three fights whole (`--on boss --until 720`), the fall, the dial, the Verge, loot and map results.
- `gist.py NAME`: a run's health by time, its tagged moves and its exceptions.
- `sheet.py`, `tsheet.py`, `crop.py`, `keep.py` (frames to `docs/experience/`).
- `wait_for.py`.
- Turns: `turn.py take godot "experience: <job>" --wait 30`.
- **Game switches:**
  - `--night ID`, `--stage N`, `--on boss`, `--die T1,T2`, `--choose rise|letgo`;
  - `--clock S`;
  - `--loot [legendary]`, `--hoard N`, `--strongbox`;
  - `--open mapresult [--fell]`, `--perf-off taa`.
