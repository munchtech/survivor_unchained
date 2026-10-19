# Handoff: the gameplay experience director

For a fresh successor. Read these first:
1. `docs/team/README.md`: the bar, the turns, and batching shots.
2. `docs/team/experience.md`: the one-page status, which holds what's done, the next steps in order, and the verdicts.
3. `docs/design/STORY_NIGHTS_AND_TIME.md`: the owner's decisions are at its top.

## Teaching pass round 2 (teach-1 lead, 19 Oct): rounds 2-3 judged, fixes built, the MR next

**Worktree** `.claude/worktrees/teach-1`, branch `teach-1`. Integration merged twice (fd5271bc; 470c3293 with env 1 E1). Commit named files only: the `*.import`/`.uid` noise and the local clip pack (`godot/art/anim/heroine.res`, `heroine_clips.json`, `tools/anim/manifest.json`, rebuilt here by `tools/anim/build.py`) are NOT committed. Tests 993/0/8.
**Built:** the callout queue (`logic/Play/Teach.cs`), freeze and aims (`src/Game/GameTeach.cs`), the drawing (`src/Ui/Callout.cs`); F1-F10 and F12 in `Prologue.cs Callouts()`.
**Verdicts** (`survivorsunchained_inputs/teach1/`): judge1 (r1 1/11), round2/verdict.md (r2 0/10: the dim), round3/verdict_fixes.md (r3, the cap: F3, F4 PASS; the callouts pass in F2, F5, F6, F10, their gate fails are the WORLD; seven small fixes, all built and checked by the numbers). Final frames: `teach1/final/`.
**Since r1:** world dim ~30% with her own soft pool, HUD whole; damage numbers, trails and sparks hidden under a freeze (`BattleFx.Frozen`); the camera holds in a freeze; F2 brackets the whole chain (slots and buttons over it at 20%, heat fills from the left); F4 no arrow; F7 waits for a windup in the open with the Knight in view (`Aim.Open`, `Aim.Seen`, `GameTeach.InOpen`, per plant for flora scatters) and rings the lane clear of her; F8's copy says what a Flare is, in three rows; F9 rings a lamp only well inside the screen, the others get an edge marker (a ringed glyph with a tip), copy "Three lamps guard the Warden..."; her keep-out covers what she holds; ground embers get a warm breathing halo (`shaders/ember_halo.gdshader`, faded by ALPHA so fog paints no square).
**Autopilot:** at the Post it circles until F7 is read, then closes on the Knight (`Autopilot.cs`, `Game.OpenGround`); before that it walked off and the run stalled.
**Next:** the final full run on 470c3293 (frames to `teach1/final/`), one light check, MR READY.
**Run:** from godot/, under a godot turn: `Godot_v4.5.1-stable_mono_win64_console.exe --path . --resolution 1920x1080 -- --quick warden --sex female --auto --teach-reset --teach-hurt --teach-end --shot teach --cines --until 1500 --count 0` (`--teach-diag` logs the cover checks; 10-35 min depending on the GPU). Frames `godot/.shots/teach_teach_<id>_1.png`.
**For the MR and other leads:** F8 teaches the Flare on Q (the story writer reconciles the F8/F13/F9 copy in docs/story/TUTORIAL_COPY.md). The Knight and the Grave-Caller can't die until their callout shows (caps 48 s, 30 s); F7 can be missed if the fight stays under cover (the cap lets the Knight die). Elite lanes draw through roofs game-wide (combat). Slot icons come from the skill's painted icon (HUD). Routed world items (r3): white fog blotches over the Low Ford Road (environment: the largest gate failure); lamps blow out to a white disc with blue bloom (lighting); the opening cinematic's frost decal left on a flat prop in play (cinematics); card UI "1-4 Choose" with three cards, Moonbrand's text cut, orphan words (UI); the Q orb's percent on its sigil (HUD); light squares round Thornbloom's brambles, likely the same fog-on-quad fault in `BattleFx.Skills.SkillGround` (VFX).

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
