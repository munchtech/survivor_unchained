# Handoff: the gameplay experience director

For a fresh successor. Read these first:
1. `docs/team/README.md`: the bar, the turns, and batching shots.
2. `docs/team/experience.md`: the one-page status, which holds what's done, the next steps in order, and the verdicts.
3. `docs/design/STORY_NIGHTS_AND_TIME.md`: the owner's decisions are at its top.

## Experience 2 (play-1 lead, 26 Oct): MR1+MR2 judged twice; round 3 fixes next, then merge

**Worktree/branch** as Experience 1 below (junction to the worktree's OWN `public/assets`; to remove the link use PowerShell `cmd /c rmdir godot\assets` from the worktree, since bash's `cmd //c rmdir` failed). Integration 126b1d9e is merged in. Import cache is fresh. Run tool: `<coordinator scratchpad>\play2\play.py NAME EVERY COUNT --teach-end` (one godot turn, about 9 min to dawn). It logs `teach ...` and now `tip <id> t= keys= text=` lines, and shoots `NAME_teach_<id>_1.png` and `NAME_tip_<id>_1.png` into `godot/.shots/`.
**Done (commits 3145c709, 200aeb30, a2a06a12, plus the copy doc):**
- au1 4: the channel tip had a dead key, because Act.Ability became Act.Flare on 11 Oct and her calling's art now rides the dash (Forms.cs). The tip now names Bull Rush and the Flare. A new F6b `form` callout in the Ambush. The dash ring glows ember when the form is ready (`Round.Form`), and the gray "Bull Rush: ready" note under the Q orb is gone.
- au1 9: the lamps callout says how. Callout rings keep out of the top-right HUD corner (`GameTeach.HudCorner`).
- au1 10: F8 waits for "Your pack" to clear. The Knight doesn't begin its first lunge far from her or under another callout, and holds it once while F7 waits.
- au1 2: the opening is spread. The great blessing gets its own panel 40 s into Rising, and dash comes after it. Timeline in m2: 0:45 / 0:46 / 0:53 / 0:55 / 1:21 / 1:39 / 1:51 road / 2:09 form.
- au1 3: `Battle.FlareGreatsHeld` keeps Flare blessings out until F8.
- au1 13: F12 and its banner now give the counts and tell traits from skills (`Callout.Mark` picks the word marked in ember).
- au1 17: a line rests 300 s per NPC (`NpcActor.LineRest`). au1 20: the lanes log.
- Judge round 1 fixes: the blessing kicker is keyed on holding a great blessing, no summon blessings before a summon, teaching panels hide Reroll/Banish/Skip, keys read 1-N, and lamps2 no longer re-fires every frame.
- Tests 1051/0/8 before round 1.
**Round 2 judge (m3 frames): level SHIP; all round-1 asks landed; 6 FIX.** Fix next, in this order:
1. **Called Shot (a Flare blessing) was still offered at 1:21.** `b.FlareGreatsHeld` is set at Prologue.cs ~1157 and read at LevelUp.cs:293. Find which path still adds FlareGreat: maybe another offer builder for the GreatRoles Answer slot, or setup running on another Battle. Also change the great block's `o.Why.Add("Your calling's own")` to "Suits your calling".
2. **The form glow can't be told apart:** a callout's HUD-target spotlight is ember too (`hud.Spotlight`). Make the callout highlight neutral (pale), and give `Round.Form` ready a look of its own (flame licks or a horn badge). Re-break the form lines: "When your dash glows, it's a charge / that throws the dead aside. / Big ones stop it, but they're stunned, / and their spell breaks."
3. **Channel tip:** show it only once the form or the Flare is ready. Hold the Warden's "RISE..." bark until the tip settles. Use one name: cast bar "Raising the drowned: break it!" (Prologue.cs channel case) and title "Break his spell".
4. **First draft:** hide "Fits your build" and the "Evolves:" lines on teaching panels (Panels.cs, `v.Teaching`). "all the way round" -> "sweeps the whole front of you" (Butcher's Cleaver text).
5. **Pack tip:** an inline [I] chip (hint text has no inline keys today: `TipLine`), with breaks at sentence ends.
6. **Lamps:** the off-screen markers are orange flames but the lamps are cold blue (recolor the markers); drop the card lower-left, off the Warden.
Routed by the judge: Combat card copy (Cold, Then Not tail; "fire" -> "strike"); UI (rarity row floats, dim italic objective, Night icon at dawn, bottom-right counters over bright planks); Env (no visible flame in the lit lamps); Rendering (ferns cover her at the form freeze).
**The m3 run found:** with the Knight's first lunge gated on her distance (8 m), a kiting run never saw F7 and the Post ran 140 s. Gate removed (commit after d9748814). Run m4 checks it (`grep "red_line" play2/logs/m4.log`).
**Tests:** PrologueTests updated (the first rise brings its card alone). Full suite 1050+1 green after that fix. Run the full suite before the merge.
**Still open from judge 1:**
- The red_line ring sits at the lane's far end by the chest. Order `KnightLane()` points away from L("chest").
- The pack tip's "I" chip is dark (`GameHud.HintKeys`, UI).
- "Cold, Then Not" tail copy (Combat).
**Then:**
- MR3: canopy whole-fade per tree instance in kit.gdshader (`see_parts`, OWN_FOLIAGE). Re-check whether E9c's house fade already fixed au1 6 in a hub run.
- MR4: Waystation 6 s freeze. The audit log breakdown: ground+water 1.8 s, props 1.5 s, her outfit built twice (about 0.5 s), 1126 pipelines. Fix with a black-hold pipeline prewarm before the fade-in. Hub p50 13-15 ms against main 4 + render 4.6 + gpu 3.5: diagnose with a medium solver, art causes to main for Env 17.
- MR5: au1 14 and 15.
**Routed (tell main):** night exposure crushes her and the dead at 1:1 and she blows out under the gallows lantern (Rendering); blobby canopies, flat crates, gray boulders and graves (Env); the "blocked" floater collides with the Warden's bark (UI); the zone header reads "Night" at dawn (UI); the Q orb shows the calling's bull icon for the Flare (UI).

## Experience 1 (play-1 lead, 26 Oct): step 1 MR READY, the audit done, step 3 (fixes) next

**Worktree** `.claude/worktrees/play-1`, branch `play-1` (from integration f91a13ca). `godot/assets` is a junction to this worktree's OWN `public/assets` (skip-worktree): never stash, reset --hard or checkout .; before merging integration, `cmd /c rmdir godot\assets`, merge, remake it. Import cache is current. Commit named files only (the .import/.uid noise stays out). Tests 1046/0/8.
**Scope (coordinator brief):** playability of the path from new game to Act 1. Env 16 owns env art, Face 41 and Body 12 own her: route their items to main in one line.
**Step 1, DONE, MR READY play-1@3cf21c2b** (the owner's 25 Oct butt-shot note). C04 A: the old A8 became A8a (a 3/4 front full figure at head height, for the reeds and sun lines, with a soft sinking ember) plus A8 (over her shoulder at shoulder height; she walks off 5 s in; `top` moved to -71). A1s is her front 3/4. The dawn now comes up under the lines (atmosphere preset `playdawn`), and the ford lamps dim with it. Code: `PlayerView.Still` (no idle breaks while a cinematic holds or hides her), nova `plain` -> `BattleFx.Sinking`, GameCinema `playdawn`. Four xhigh judges, all camera SHIP. The doc is `docs/cinematics/shoot/c04a.md` "As it plays now". Frames are in `survivorsunchained_inputs/play1/`. Scan of the other cinematics: no other low rear shots.
**Step 2, DONE:** the audit `survivorsunchained_inputs/play1/audit_au1.md`: 20 ranked items with their owners and sizes, and the fix order at the end. Run tools (backed up): `survivorsunchained_inputs/scratch_a44c2c21/play1/` (`play.py NAME EVERY COUNT [args]` is the full real-play run, one godot turn, ~9 min to the hub; `shoot.py RUNS.json` and `jedit.py c04a ed_X.py` are the cinematics tools; all point at play-1). The autopilot now walks to the Waystation at Dawn (e84d289d).
**Step 3, NEXT (start here):** the fixes in the audit's order, small MRs, each re-run on its stretch. (1) Items 4, 9 and 10: the "[ABILITY]" key name unresolved on the boss banner plus a Bull Rush callout; the lamps callout says how and aims clear of the HUD; YOUR PACK out of the Knight fight; the red line held until its callout shows (`Prologue.cs Callouts()`, `logic/Play/Teach.cs`). (2) Items 2, 3 and 13: spread the opening six lessons; Flare before the Great Blessing; the level copy. (3) Items 5 and 6: the canopy and roof cutaways. (4) Item 7: a loading screen and pipeline pre-warm. Judges: teaching frames at xhigh (whole-frame gate).
**For main / the owner:** SB00 (the storybook lore intro) is OFF (`sb00.json` `"live": false` since 19 Oct, waiting on its painted plates), so a new game opens on black, then C01.

## Teaching pass round 2 (teach-1 lead, 19 Oct): rounds 2-3 judged, fixes built, the MR next

**Worktree** `.claude/worktrees/teach-1`, branch `teach-1`. Integration merged twice (fd5271bc; 470c3293 with env 1 E1). Commit named files only: the `*.import`/`.uid` noise and the local clip pack (`godot/art/anim/heroine.res`, `heroine_clips.json`, `tools/anim/manifest.json`, rebuilt here by `tools/anim/build.py`) are NOT committed. Tests 993/0/8.
**Built:** the callout queue (`logic/Play/Teach.cs`), freeze and aims (`src/Game/GameTeach.cs`), the drawing (`src/Ui/Callout.cs`); F1-F10 and F12 in `Prologue.cs Callouts()`.
**Verdicts** (`survivorsunchained_inputs/teach1/`): judge1 (r1 1/11), round2/verdict.md (r2 0/10: the dim), round3/verdict_fixes.md (r3, the cap: F3, F4 PASS; the callouts pass in F2, F5, F6, F10, their gate fails are the WORLD; seven small fixes, all built and checked by the numbers). Final frames: `teach1/final/`.
**Since r1:** world dim ~30% with her own soft pool, HUD whole; damage numbers, trails and sparks hidden under a freeze (`BattleFx.Frozen`); the camera holds in a freeze; F2 brackets the whole chain (slots and buttons over it at 20%, heat fills from the left); F4 no arrow; F7 waits for a windup in the open with the Knight in view (`Aim.Open`, `Aim.Seen`, `GameTeach.InOpen`, per plant for flora scatters) and rings the lane clear of her; F8's copy says what a Flare is, in three rows; F9 rings a lamp only well inside the screen, the others get an edge marker (a ringed glyph with a tip), copy "Three lamps guard the Warden..."; her keep-out covers what she holds; ground embers get a warm breathing halo (`shaders/ember_halo.gdshader`, faded by ALPHA so fog paints no square).
**Autopilot:** at the Post it circles until F7 is read, then closes on the Knight (`Autopilot.cs`, `Game.OpenGround`); before that it walked off and the run stalled.
**MR READY** (19 Oct): the final xhigh check on HER 11 frames (`teach1/final_her/`, sheet_11.jpg) passed the callouts everywhere; F10 (she hid under a roof slab) fixed with Aim.HerSeen and re-shot. Gate fails left are the world (routed below). Earlier rounds' frames showed the male hero by mistake (no --sex female). Open, not blocking: world barks show dimmed during a freeze (hide them like damage numbers); F1 may ring an ember with a mob over it.
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
