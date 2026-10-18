# Cinematics: handoff

## Start here (cinematics 2, agent ac04a1a77622be439, 18 Oct)
Worktree `agent-a59432fe3bfc6eb92`, branch `cinematics-1`, merged with integration b02f172e. `godot/assets` is a JUNCTION to this worktree's own `public/assets`: never `git reset --hard`, `git checkout .` or bare `git stash` here. Tests: 942/0/8 at ef6cf1a9 (full suite). Rules: judge 1:1 frames only, 2-3 rounds per item, then close as known. **Round 1 of judging is done and its fixes are built (77fb41da). Round 2 is next.**

**State of the fixed list** (judges' verdicts: `tools/scratch/cin6/judge/j1_verdict.md` cinematics xhigh, `j2_verdict.md` face lighting max; briefs beside them to reuse):
- (a) C03 runs into C04 A: **PASS** (j1). Real play still to be checked (below).
- (b) C01's end: the slide is gone, but s11 froze about 1 s and s12 lost her head. Fixed in round 1: PickUp from 0.45, @idle at 1.0, dur 2.2; s12 `at` tracks her chest (+0.2). `ActorAt("her")` now follows her own body after the hand-over (it read the hidden stand-in before). **Round 2: judge.**
- (d) The ember on the lens: **PASS**.
- (e)/(f) Lighting (j2): the under-eye fill PASSED. Eye light cone 14 -> 5 deg (s8 had gone flat). Crown rim moved to the far side, `from` head off [0, 0.45, -0.5], 1.5. C02 s8 is frontal 100 mm ([0.08, -0.03, -1.0], aim y -0.03); the held lamp's light sits at her eyes off [-0.20, 0.06, -0.28], 0.8, range 0.55. The dark "mist wisp" band WAS the warden's lamp-iron shaft, and the frontal framing takes most of it out. **Round 2: judge** (j2 also wants the flame in her eyes, a blue side and a red side; if her left cheek has no ember red, add about 0.15 there).
- (g) Lower head: A3 aim +0.12, A5 -0.04, A7 -0.05, c01 s10 +0.03 (raised, so her head clears the top bar). C03 s10 (eye height, pulled back) and s11 (aim up 0.4 on Grimtunnel) were reframed from j1's new marks. **Round 2: judge.**
- (2) Living holds: `CineBreath` (godot/src/Actors/CineBreath.cs) breathes any held clip end (chest 2.0, shoulders 2.2, head drift 1.0/1.4 deg), switched by `PersonView.Advance`. `--cinebones` prints `cinebreath` lines: the stills' cinebones log reads the pose before the modifiers, so 0.0 cm there is not proof of stillness. C04 A A7 was never frozen (its idle moves about 5 mm). C03 s9: a flinch, then at 0.12 s the guard (`Idle_Shield_Loop` for the Warden, @idle for the rest). j1 round 1 failed the late, limp recoil. **Round 2: judge s9.**
- (3) The c02 s8 wisp: see (e)/(f).
- (4) Pacing: trims in `ed_pace_*.py` and `ed_r1_*.py` (c01 6a 2.0; c02 s2 3.0, s3 3.0, s10 2.0; c03 s2 3.3; c04a A2 2.4, A3 2.6, A7 tail 1.5 and its note; c04b B4a 2.2; c01 8b gets a 0.05 push). j1 couldn't check c02/c04b because `pace.py` needs those logs: run it on `logs/k8c02.log` (only s8 kept) or shoot a full c02 and c04b. **Round 2: one look at pace from the k8 logs.**
- (5) Frost seams: the patch is round and ragged; the tile boxes span the slope and cross-fade over a 0.3 m overlap (`FrostSeam`). j1 round 1 still saw a tile grid. **Round 2: judge** `k8c01_ho_c01_036/040`. If it still fails, use one big decal and log the rest for arena art.
- **Not ours, sent to main (a neck seam fix lead, outfits area, has it; reshoot C01 s8/s8b/s10 after it lands):** the stair-stepped neck patch in C01 s8/s8b CUs stays with every shadow off, so it's the new body's head/neck join (`neck_probe.png`). Firelight specular on the Warden's breast cups at C01 s10 (j1 new #4) is logged, not fixed.
- **Round 2 batch:** `b8.json` (k8c01 full plus hand-over, k8c02 s8, k8c03 the chain plus hand-over), shooting as I hand off (`logs_b8_run.txt`). Then ONE judge per verdict file, reusing the briefs with k8 paths. API credits are about $4.6 left (`node tools/ai/api_agent.cjs status`). After that, use `su-lead-max` subagents.
- **Real-play check:** runner a25ec8339d6b83a1c is rerunning `--auto` through the Prologue (log `tools/scratch/cin6/logs/play_warden2.log`, frames `godot/.shots/playw_*`). The autopilot used to stall at the Grave-Caller; fixed in Autopilot.cs (a Barrow case). It now sends its report to main.
- **Then the MERGE REQUEST to main:** tests (942/0/8 last run), then delete the untracked `.uid`/`.import` noise from staging. Never commit the tracked `.import` changes.
- The animation lead is refitting grips: check C01 s11's sword pick-up after their merge.

**Tools** (`tools/scratch/cin6`): `shoot.py RUNS.json` (one godot turn per batch; builds C# first), `sheet.py`, `pace.py LOG CINE...`, `jedit.py CINE edits.py`, `ed_*.py` (every edit made). Shots land in `godot/.shots/<name>_<cine>_s<shot>_<k>.png`; hand-overs in `<name>_ho_<cine>_NNN_1.png`.

From agent a7a4c20bcfd7ccfd3 (who took over from a79b6d8c81e14dc63) to a fresh cinematics production lead. Read `docs/team/README.md`, `docs/team/RESUME.md`, then this page, then `docs/team/cinematics.md`.

## The owner's quotes

- "we are striving for perfection". "cinematic, movie quality, soul, nothing generic". Story is about 40% of the early game, and the cinematics carry it.
- The hand-over (5 October): "cinematics that have our character immediately playable in the same spot should have us... in that same spot when we are playable again ... it should feel like its walking in and we just jump right into that."
- On voice: no placeholders; final voices come from ElevenLabs later.

## The brief

Shooting scripts (`docs/cinematics/shoot/<id>.md`), boards over the engine's own frames (`tools/cinematics/boards.py`), animatics (`tools/cinematics/animatic.py`), and the in-engine player (`godot/data/cinematics/*.json`, `src/Game/GameCinema.cs`, `logic/Cinema`). First milestone: C01 and the Prologue (C02 to C04) right; then C07 and C09; C10 to C13 once combat builds their fights.

## Done this session

- **The hand-over into play** (`docs/cinematics/README.md` 5a, tested by `CinemaTests` through `logic/Cinema/CineHandover.cs`):
  - a `play` cue at 0 of the last shot puts her own body where her double stands (on the cut); her later `move`s steer the player as a stick would (`Game.PlayMove`, `cineWalk`);
  - a walk still going at the end carries on into play and eases out over 0.7 s;
  - `PlayerView.Face` sets her facing; `WorldScene.StartBattle` uses it too. Every zone arrival had faced south until she moved: that was C01's snap;
  - the follow blend turns the view (slerped, ahead of the move) and aims where she really is; `FollowCamera.Snap` no longer drops 0.8 m; the HUD fades in with the bars (`GameHud.ShowPlay(on, fade)`);
  - `end.keep` leaves cast bodies in the world after the hand-over (the Warden in the ford after C03);
  - `--handoff` (with `--shot`) films 1.5 s before the end to 2.5 s after, every 0.1 s.
- **Lowford's camp, made** (title, creation, C01): `src/World/Camp.cs` (sawn pine logs; Pine Bark, credited), `Campfire.cs` (`Stones`: a made ring; `Coals`: a glowing bed, on its own render layer outside its fire's light, with a small glow light), `shaders/endgrain.gdshader`, `shaders/coals.gdshader`. The tripod and pot are gone. Flora and grass are cleared from ring fires (`ZoneView.Bare`, `grass.gdshader` `bare_at`). A fire's light sinks to its coals as its flames go (`SetFire`).
- **C01:** burns to coals; shot 5 from the west (no leg or stone across her); 6 at 35 mm, holding her face and hands; 6a focus tracks the hand; 10 focus tracks her. Staging re-rendered (`st1`); board prompts rewritten for the camp.
- **C04 A:** the last shot cranes up into play over 3 s; her walk outlasts it.
- **Combat** was told the hook asks again. They are item one of its successor's code queue (`docs/handoff/combat.md`). The Dig (C12) exists on combat's branch.

## Next, in order

1. **Animation's new clips (merged in integration):** stage C01's `letter`, `kneel_to_stand_snap`, `take_from_log`, `cup_hands`, and the remade `lie_side_wake`, `sit_back_heels`, `reach_coals`. Swords now sit at a 30 to 35° diagonal grip; check C01's shot 11 pick-up. C04's `flask_drink`: move A6's camera to her front-left (the drinking arm covers her face) and add a flask-and-cork prop.
2. **Film C04 A's hand-over again** (`ho.py c04a <name> 50`) since the turn-ahead fix. Judge every hand-over at full size; consider ending last shots nearer the game's angle.
3. **Staging and boards:** render C02, C03, C04 B staging (look at the heart's ring halo in C03); stage C01 (`boards.py c01 --stage st1`); draw the boards (C02's s3, s5, s7, s8, s11; then C01, C03, C04 A, C04 B), each at full size.
4. Recut the Prologue animatic (`animatics/prologue.txt`; C01's shot 4 is 6a).
5. The male hero through the Prologue (`prev.py ... --male`).
6. C02's and C03's line choices; C07 and C09; C10 to C13 when combat lands the marks.

## Decisions (why)

- **Her own body ends every cinematic that ends in play,** swapped in on a cut: the walk play continues is the walk the shot showed, same gait and stride, and no pose is seen to change.
- **One traveller's fire:** no tripod or pot. A bed of coals carries C01 better than flames, and nothing stands across the low cameras round her.
- **A made stone ring, not the scan:** the Poly Haven pit's few thousand faces read as cut facets at half a metre in C01's close-ups.
- **The engine's frame is the staging truth; boards are drawn over it. Cameras aim at bones. Looks are head turns.**

## Failures and why

- **A web-game ring stone survived the pit's hiding** (its box stood 0.72 m tall turned on its side; the cutoff was 0.7). Found with `--cinenear X,Z,R`, which lists every visible mesh near a point at each still.
- **The coals first lit themselves** from the sunk fire light and flared white: they now sit on a render layer their fire's lights skip.
- **The follow blend lerped a far look point** (C04 A's road toward the gate) toward her, so she dropped out of frame mid-blend: it now turns the view.
- **The first import run was killed** waiting 10 minutes for a turn: use `--wait 90` with a long background limit.

## Gotchas

- **Scratch tools** are in `<scratchpad>/cin4` and point at this worktree (change `WT`, `G`, `W` and `T` if yours differs):
  - `prev.py` builds the C# first, then renders (`--male`, `--calling`, `--clean`, `--only`, `--stills`);
  - `ho.py` films a hand-over (`--before` for an old build); `ba.py` makes a before-and-after;
  - `mkt.py` makes a scratch `_t<id>.json` with camera variants of shots (delete it before committing);
  - `jedit.py`, `bspec.py` (board specs), `sub.py` (exact substitutions in docs), `imp.py` (import new assets), `ends.py`, `times.py`, `crops.py`.
- **The worktree guard** refuses Bash with variables or heredocs near `git`, or a `cd` outside the worktree. Write scripts to the scratchpad and run them plainly; use PowerShell for `dotnet test` with env vars.
- **A new worktree needs** the `godot/assets` junction (skip-worktree), a copy of a `.godot` cache, `imp.py` for anything new, and `dotnet build` (`prev.py` and `ho.py` do it).
- **Generated `.uid` files** block merges when integration starts tracking them. Delete the untracked ones outside `godot/assets` (its contents show as untracked through the junction; leave them).
- **StoryLint reads `Num("...")` in any C# as a fact.** Read cue args with `Get(...)` in logic code.
- **Headings:** 0 faces south (+z), pi/2 east; `Rotation.Y` on a view is the same heading.

## Collaborators (roster in `docs/team/README.md`)

- **Combat** (a5115633c7006e4d4, handing off): the boss hooks and marks are its successor's first code item.
- **Animation** (handed off): the clips listed in Next 1.
- **UI design:** the title's camp changed; the HUD now fades in after a cinematic.
- **Face** (a833b7942e978d994): her head is changing; re-check the close-ups when it lands. `mouth_open` above 0.15 shows the teeth as a grin.
- **Performance:** each ring fire has one more small light and about 6k more triangles.

## Files to read first

1. `docs/team/cinematics.md`, `docs/cinematics/README.md` 5a and 11a, `docs/cinematics/shoot/README.md`, `shoot/c01.md` to `c04b.md`
2. `godot/src/Game/GameCinema.cs` (`Handover`, `Steer`, `Finish`, `PlayMove`, the follow blend) and `logic/Cinema/CineHandover.cs`
3. `godot/src/World/Camp.cs`, `Campfire.cs`, `shaders/coals.gdshader`, `shaders/endgrain.gdshader`
4. `tools/cinematics/boards.py` and `docs/cinematics/shoot/boards/*.json`
