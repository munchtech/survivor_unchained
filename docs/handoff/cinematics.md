# Cinematics: handoff

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
