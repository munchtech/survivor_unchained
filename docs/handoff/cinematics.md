# Cinematics: handoff

## Start here (cinematics 1, agent a59432fe3bfc6eb92, 18 Oct)
Worktree `agent-a59432fe3bfc6eb92`, branch `cinematics-1` (on integration 7afa833f). `godot/assets` is a JUNCTION to this worktree's own `public/assets` (skip-worktree): never `git reset --hard`, `git checkout .` or bare `git stash` here. The .godot cache is imported and fresh. The worktree guard refuses heredocs and `cd && git` chains: write scripts to files and run them plainly.

**The fixed list** (RESUME 18 Oct item 4; OWNER_NOTES 17-18 Oct). The 17 Oct rules apply: judge 1:1 frames only, 2-3 rounds per item, then close as known.
- **(a) C03 runs on into C04 A: BUILT, unjudged.** The owner: no 3 s of wading between two cinematics. `CineEnd.Next` (c03 `end.next: "c04a"`, shot 13 dropped): the bars stay to the cut (CinePlayer.Bars), and the Chain record in GameCinema hands the bars and the saved camera to the next cinematic. `Prologue.HeartGone` calls `FirstLight(false, onward: true)`. Taken's toast and the Warden's hoard (`Battle.Gather`) come at C04 A's hand-back. Dawnbreak's two narrator lines are skipped. C04 A A1 says the reeds line (`cin_first_light.reeds`, the conversation's new entry; `when !prologue.reeds_said`). `--cine c03` previews the chain. Tested: CinemaTests `A_cinematic_that_runs_on_cuts_into_the_next_in_its_zone`. Seen in batch 1 (`k1c03_ho_*`): the cut from s12's ELS to A1 (her wading out past the Warden's body) reads well. Still to do: a real-play check that kills the Warden (HeartGone path, the hoard gathered, toasts) and one xhigh judge on the cut.
- **(b) C01's slide: BUILT, unshot.** Shot 11 glided her 1.25 m along the log in 0.7 s on her idle, which was the slide. It now cuts onto the pick-up (place at reach, PickUp_Table from 0.15, cues 0.7 s sooner, 2.8 s). Shot 12 was a hip shot with her head out of frame: it now aims at her chest (off y 1.4, camera y 1.5). Shoot s10-s12 plus the hand-over, then judge.
- **(e)/(f) Lighting: first values BUILT, unshot.** The new `rig` cue (GameCinema `PlaceRigs`; a soft spot on the people layer, `from: {lens:[x,y,z]}` or a place, `aim` a place, lasting its shot unless `hold`). Eye light 0.3 at c01 s8/s8b and c04a A5/A7. A warm under-eye fill at c01 s8 (0.25, #ffc890). A crown rim at c01 s7 (0.8, #b9c9ff, from north above). c02 s8: the held lamp 2.0 -> 1.0 at #a8d2ff, and the ECU re-aimed (at off y -0.035 -> +0.01: the top bar was cutting her eyes). Batch 2's baseline (`k2c02_c02_s8_2`) shows a dark band down the left edge, which is likely the "mist wisp": not fixed yet. Find what it is (CINEDBG, `--cinenear`). Shoot each item before and after, then one judge (max for her face in the close shots).
- **(d) Polish found so far:** an ember drifting across the lens made the orange disc on her cheek at c01 s10 (batch 1). Fixed: `Campfire.ClearNear` now runs per frame in cinematics. The frost decal tiles show straight square seams in the top-down play camera after C01 (the `frost` cue's tiles): fade their edges. c03 s8-s12 and c04a A7 hold her FROZEN (0 cm between stills for 22 s and 15 s): add a living hold (idle or breathing) or cut it shorter.
- **(c) Pacing: the tables are made** (`tools/scratch/cin6/pace_k2.txt`, from `pace.py`: each shot's length, its lines, the quiet tail after its last event, and every actor's motion between stills). Candidates: c04a A7 (15.4 s, a 12 s line, then 3 s of silence, with her frozen); c01 s5 (3.9 s tail), s6a (2.7 s tail); c02 s2 (4 s, nothing happens), s3 (3.5 s), s5 (3 s tail), s7 (2 s); c03 s2 (2.6 s tail); c04a A2 (5 s landscape, fine as a beat), A3 (1.9 s); c04b B4a/B5. Trim by the rule: a tail over ~1 s where nothing moves gets cut to 0.6-1.0 s; narrative pauses (notes saying "a beat", "hold") are capped at ~1.5 s. Then one xhigh judge on the tables plus 3-stills sheets.
- **(g) Head 3 cm lower:** bone-aimed cameras follow on their own. The fixed-point aims found so far are c01 s12 and c02 s8 (both done above). Check c01 s8/s8b's top-of-head crop and the rest in batch 3's sheets.

**Tools** (`tools/scratch/cin6`, copy them to your scratchpad): `shoot.py RUNS.json` (one godot turn per batch; runs are name/cine/until/args/env/keep; until must cover the real length: c01 69.5 s, c02 48.5, c03 49.8 + c04a 48.9, c04b 27.5, plus about 12 s of start-up). `sheet.py OUT COLS WIDTH globs`, `pace.py LOG CINE`, `jedit.py CINE edits.py` (keeps the timeline's layout), `ed_*.py` (the edits made). Shots land in `godot/.shots/<name>_<cine>_s<shot>_<k>.png`; hand-overs in `<name>_ho_<cine>_NNN_1.png`.

**Next, in order:** batch 3 = c01 (s7, s8, s8b, s10-s12, hand-over) + c02 s8 + the c03 chain (until 115) + c04a A5/A7, all after this commit. Look at half size, then ONE xhigh judge (face close shots at max) on (a), (b), (e)-(g) at 1:1 (API route, README "Judges on the API credits"). Then the pacing trims and the frozen holds, the mist wisp and the frost seams, one judge, then the MERGE REQUEST. Delete untracked `.uid`/`.import` noise from staging; never commit the tracked `.import` changes.

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
