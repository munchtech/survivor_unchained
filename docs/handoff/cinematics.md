# Cinematics: handoff

## Start here (cinematics 3 successor, agent ac7e54435a82fff12, 18 Oct)
Scope: items 1-4 only, then the MR and STOP. (1) Loot is hidden in cinematics (888bf952). (2) A darker grade with real-source light and mist. (3) The owner's o1-o3: C01 s3, s6 and s10, plus s11. (4) Side keys on the close-ups, to the look bible's rule (docs/art/look_bible/02_skin.md item 5). Items 5-6 (blocking against the notes, the missing moments) are the backlog for after the new art, with the list in the k10 verdicts.
- k10 (staging solver a5f61d98, a0f421e7/6c8e0756): the `atmosphere` cue's tuning, a `mist` cue (FogVolume), and HeadTurn keeping a lying head's roll. Two max gate judges passed 1/33 (`tools/scratch/cin6/judge/k10A_verdict.md`, `k10B_verdict.md`). The C01 and C04 A hand-overs pass.
- k11: two max staging solvers (briefs `judge/s5a_brief.md` for C01 and `s5b_brief.md` for C02-C04 A, shared `s5_common.md`), shots `k11a*`/`k11b*`. Then one judge round (reuse `k10_brief.md`), the tests, the MR.
- Touch-up 2's finding on C01 s3: the face/neck split is the moon, shadowed by her armor (evidence `judge/tu_tone_evidence.jpg`).

## Start here (cinematics 3, PAUSED 18 Oct, clean point)
Worktree `agent-a59432fe3bfc6eb92`, branch `cinematics-1` (merged with integration incl. the neck seam fix 7b9cd519). `godot/assets` is a JUNCTION: never `git reset --hard`, `git checkout .` or bare `git stash`. Full suite 942/0/8 at 888bf952. No turns held. Nothing is merged to main yet.

**The owner's bar changed (18 Oct):** the gate is now "would this frame ship in a AAA game as it stands?" at 1:1 on the whole picture (docs/handoff/lead_brief.md); a NO fails regardless of the checklist; calibration frames `godot/.shots/o1_lying_neck_adams_apple.webp`, `o2_hunched_at_log.webp`, `o3_spin_profile.webp` (C01 s3, end of s6, s10). Art direction: "more realistic - but stylized enough to make sense on saving graphics lag", our own assets; the tutorial (Prologue, so these cinematics) launch-ready first.

**The gate audit** (`tools/scratch/cin6/judge/gateA_verdict.md` C01-C02, `gateB_verdict.md` C03-C04 B; one real-play still per shot, `godot/.shots/playc2_<cine>_s<id>_1.png`): 1 of 54 YES (the black card). Every NO also fails on other areas, so staging alone reaches no YES. The per-area lists in those files are the BACKLOG for the environment (low-poly pines, tiled water, town haze, grass rows, fog sprites), NPC/creature art (drowned, warden, risen, Grimtunnel, villagers), her armour metal (chrome hot spots), her skin shader (waxy: no SSS, no pore break-up), story props (heart, lamps), and animation (face-down wake, R1 emerge, warden rise, ready guards, slack mouth, sa5/sa7 faces).

**Items 1-4 (agreed with the coordinator) - BUILT, UNJUDGED:**
1. Loot hidden during cinematics: `BattleFx.HideLoot` (888bf952). Light shafts and the way-out band still draw.
2. Darker night grade + low mist: `atmosphere` cue takes adjustments (key, hemi, env, exposure, fog, rim, azimuth, elevation, keyColor, fogColor; `"from": "now"`), new `mist` cue (a0f421e7, 6c8e0756). C01 and C02 have their own darker night; mist on C02's river and past C01's firelight.
3. The owner's shots: C01 s3 head tipped to the coals, camera on her face's side (`HeadTurn.cs` no longer rolls a lying head upright); s6 head to bedroll then bowed to her hands, warm light on her nape, lower 32 mm (no flask: props take weapon pieces only); s10 1.0 s, cut on the lift (kneel_to_stand_snap from 0.3 s, no spin); s11 the body `look` dropped, the clip's own turn carries her, side-on at chest height.
4. Side/three-quarter keys: C01 s8, s8b, s10; C02 s4, s8; C03 s3b; C04 A sa5-sa7 (sun on her right = frame left; the note says frame right, a cheat if wanted).
Frames: `godot/.shots/k10c01_*`, `k10c02_*`, `k10c03_c03_s3b_*`, `k10c04a_c04a_sa5..7_*` (3 stills a shot). Edit scripts `tools/scratch/cin6/ed_k10_*.py`.

**Next, in order:**
- **C01 s3 face-vs-throat tone is OURS** (touch-up solver fcde25f0, evidence `survivorsunchained_inputs\scratch_touchup1\tu\tone\evidence.jpg`): the breastplate shades the moon off her throat, so the throat is fire-orange and the face moon-pale, split at the jaw. Fix: moon off for s3, or move it so the cups don't shade her throat, or the armour's moon shadow off in close-ups; also check the moon's colour (it turns skin pink-white). Likely the same in s10. `CINEDBG lamps=0,glow=0` doesn't reach C01's fire. Known misses from the solver: s3 too orange (ember 0.45 -> ~0.25, lens 100, camera 0.15 m toward her face), C02 s8 still pale. Check the mist for blockiness and s12's bright start.
- Then ONE max judge with the AAA gate first on the k10 frames + round-3 items (brief `judge/j1r3_brief.md` and `j2r3_brief.md`, written for k9: point them at k10 where reshot). Round-3 k9 frames for C01 s10-s12 and C03/C04 A are in `godot/.shots/k9c0*`; C03 s9-s11 were restaged for the sunk Grimtunnel (cameras at his eye line, hug pose, VAT v14) and are unjudged.
- Then the MR (tests: `dotnet test` in godot/tests; drop untracked `.uid`/`.import` noise; never commit the tracked `.import` changes).
- **Items 5-6, after the art lands** (restage list): blocking/framing against the notes (C01 s2, 5, 11, 12; C02 s1, 3, 7, 9, 11, 12 incl. the warden lying on and actors standing on the water, her running at the hand-off; C03 s1, 2, 8, 11, 12; C04 A sa3, sa8; C04 B sb2, 3, 5), and the promised moments (sa2 gold treetops, sa4 ember drain, sa5 breath, C03 s4 steam, s6 water off the heart, sb4a smoke): build or cut.
- Real play: `tools/scratch/cin6/playc.py NAME COUNT` runs the Prologue with every cinematic (`--cines`); playc2 played c01, c02, c03 -> c04a on the cut, c04b with no errors. The Gestures Slerp throw is fixed.

Done this session (commits f8e0d473..6c8e0756): k8 judged (j1r2/j2r2 verdicts), round-2 fixes (pacing trims c01 s6 6.4, s11 1.8; c02 s2 2.4; c03 3b 1.9; c04a A2 2.2; c04b B4a/B4b 1.7; C02 s8 lamp side fixed: place offsets are WORLD metres), the s3 solver (take_from_log for her pick-up, the crane aims from where it is, Grimtunnel sunk and hugging), `--cines`, the gate audit.

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
