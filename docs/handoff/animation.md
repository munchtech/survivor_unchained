# Handoff: animation (the heroine, the hero, the crowd, the townsfolk, the cinematics)

For the next animation lead in Survivor Unchained. Read `docs/team/README.md`
first, then this page, then `docs/team/animation.md` (the one-page status).
Written by agent a03acf30b3e9bdd70, branch `worktree-agent-a03acf30b3e9bdd70`,
which took over from a435f4dd0ac80df75 (before it a1e3002b800ee55ac and
aa4f5fc266b043035).

## 1. The owner's bar (quotes)

- "AAA standard", "strive for excellent, above and beyond - not just good
  enough". "Not polish, perfection." Never settle: remake rather than polish.
- "we are striving for perfection." Improved is not enough: before you show
  anything, ask whether it is the best version of this in any game, ground the
  design in how the best games solve it, then make it ours (the main session,
  passing on the owner).
- "Do we have soul?" The aim is "one game in a million, not one soulless game of
  many". For motion: "movement with personality, specific to her and to each
  calling: a signature idle, the way she draws a weapon or catches her
  breath, small human details. Stock-library motion fails, however clean."
- Motion should be "weighty, characterful, readable at the game's camera".
- Sex appeal and the male gaze drive the heroine, "tho not at the cost of
  looking bad". The tone is 18+ (mature, not explicit).
- Context: "accurate, efficient, on track, manage and engineer context.
  deliberate. clean over chaos".

## 2. The brief

You own character animation in `godot/` (Godot 4.5.1 .NET), with the tools in
`tools/anim/`:
- her clips (`her/`, `heroine.res`) and the male hero's (`him/`, `hero.res`);
- the townsfolk's clips and the crowd's own motion (`folk/`, `folk.res`; `crowd.py`);
- the beasts' composed motion (`Beasts.cs`);
- the cinematics' clips and gestures, including the Ford-Warden's (`clips/warden.py`, in `folk.res`).

How to work:
- Judge everything at full resolution as the player sees it: on sheets, in the running game at the default camera (1920x1080), and cinematic clips in their cinematic at its own cameras.
- Reject takes that don't fit the game's action; don't bend them to fit.
- In `godot/src/Actors/` change only animation mapping and playback. Hair, face, skin, outfits and the sim belong to others.
- Keep `cd godot/tests && dotnet test` green (661 pass).
- Commit and push at milestones; the main session merges. Open no PRs. British spelling. Short comments that say why. Don't stop to ask.
- **Take a turn before any Godot run for pictures or clips** (packs too): `python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take godot "animation: <job>" --wait 10`, and `give godot "<same name>"` the moment it ends. Two heavy jobs at once have crashed the machine.

## 3. Done this session (all pushed; newest last)

ffab4040, 926efa47, 3818c0e0 (status), 75cff887, 869a1d81.

- **The slam** (`crowd.slam`, `slam_armed`; ffab4040). The predecessor's keyed draft read as a stretch from the game's camera, so it was remade:
  - the lead foot planted in a gather; the fists locked (armed: the axe raised high, its head up and back where the camera above sees it); the back arched; a hang;
  - the jack-knife with the body leading, the blow on frame 30 (1.0 s, a frame the 15 fps bake samples); held down glaring; up and settled 0.67 s after.
  - Its own role `"slam"` (`Visuals.Clips.Slam`) on kerchief_brute (Barn-Door) and skeleton_minion (the Heap). `CrowdView` plays the windup so the blow lands with the sim's (`SlamImpact` = 1.0), then plays the rest of the clip after the cast.
  - Judged on sheets (side, front, 64 degrees) and in the game.
- **Kneel-to-shoot** (`crowd.kneel_aim`, `kneel_shot`; 926efa47): on the knee by 0.33 s, on the eye by 0.53 s, held; then the kick, a beat, the rise, standing by 0.63 s. Roles `"aim"` and `"shot"` (`Visuals.Kneels`) on skeleton_rogue and a new visual, **kerchief_crossbow** (the pillager's red hood with a crossbow). `CrowdView` plays the shot only after an aim (`Gait.Aimed`/`ShotT`), so a melee strike stays the library's. Judged in the game with levy_crossbow pointed at it locally.
- **Vat v13.**
- **`--on casts`** (Game.cs): fifteen frames a second through every marked cast, for judging casts in the game.
- **The Ford-Warden's cinematic clips** (`tools/anim/clips/warden.py`, packed by `folk.py` as `m_<name>`, played as `folk/m_<name>`):
  - C02: `rise_stiff` (Kimodo take 1, retimed, grounded, settled on its mark; the lamp keyed up out of the water) and `bend_lift` (take 1's bend cut and slowed into the stop; the lamp keyed out to her face with one bad tremble at 2.0 s; the head tilts as he looks).
  - C03: `kneel_lamp`, `lamp_down`, `fold_forward`, all keyed (the takes were rejected).
  - Each was judged in its cinematic by swapping the cues in locally (never committed). The exact cues are with the cinematics lead (§8).
  - `People.Clip` passes `folk/...` names through, so any kit-built person can play the kit's own clips by name.
  - `keyed.py` fingers take `"oppose"` (0..1): the thumb swung across the palm before it bends, so a fist closes over the thumb. The Warden's fists use it. Existing presets are unchanged.

## 4. Next, in order

1. **C04's `flask_drink`** (her), then C01's `letter`, `kneel_to_stand_snap`, `take_from_log` and `cup_hands`, then C04's rest (`wade_out`, `walk_uphill`, `unfold_arms`).
   - Takes are in `C:/Users/munch/Tools/mocap/kimodo/<name>_<n>.bvh`, three of each.
   - Judge whole takes first. The quickest triage is `stick.py take:<prompt>_<n> f` (scratch, §7). Then sheet the likely take, then judge it in the cinematic with a local cue swap.
   - Her story clips belong in `clips/story.py` (`ALL`; `JUDGED` once judged), built by `build.py` into `heroine.res`. Kimodo-based ones go through `generated.make` (warp, place). Key over a take with `build(..., base=clip)` where its hands must hold something.
   - Read the shooting script (`docs/cinematics/shoot/cNN.md`) and the written script (`docs/cinematics/cNN_*.md`) for each shot's beats. Use `--cinebones` (in `cine.py`) to measure where things are.
2. **The Warden's remaining two:** `lie_arm_up` (C02 shots 3 and 4, lying under the river with the lamp up) and `wade_drag` (C02 shot 6, the wade with the greatsword dragging). `rise_stiff` starts from his left forearm held up off the elbow, so `lie_arm_up` should end in that pose.
3. **Grimtunnel's** `burst_hug`, `sniff`, `laugh` and `dive` (C03), composed on the lampling rig in `Beasts.cs`. The lampling's slam (Grimtunnel, the Gaffer, the Ganger, the Sapper-Foreman) would be a `Beasts.cs` composition too.
4. **Polish:** `chain_strike`'s low landing crouch reads as a kneel; and a heavier flinch while running (a `Gestures` gesture fired with the hit would layer over the run).
5. **The male hero's library rebuild** once his body lands, with the male hero lead (ab82cbe99e2937ddd): re-dump `hero_skeleton.json` with `anim_skeleton.gd`, then `build.py --body hero`.

## 5. Waiting on others

- **Combat's successor** (queued as the first item of `docs/handoff/combat.md` §4.3, on worktree-agent-a708da2c97bf85c95@df6556e2):
  - plant the slammer 0.65 s after its blow, and the shooter 0.7 s after an aimed shot. Until then the Heap strikes again over its get-up, and the crossbows skate as they rise.
  - point levy_crossbow and mb_levy_sergeant at `kerchief_crossbow`, and add it to `EncounterTests`' rigs list.
- **Cinematics** (a79b6d8c81e14dc63) blocks the Warden's clips into C02 and C03 once merged:
  - moves C03's heart (he now falls toward her, his chest at about w plus (0, 0, +2));
  - reframes C03's shot-4 insert;
  - fixed the floating lamp in WardenView (a bail from `handslot.l`, plumb under the fist).

## 6. Decisions and why

- **The slam and the kneel are roles of their own, not `cast` or `attack`.** A rally's cast loops and a slam's must not. A shot after an aim must not replace the crossbow's melee strike.
- **A blow lands on a frame the bake samples** (15 fps), so it is never smeared between two.
- **Wind-ups raise the weapon high.** From the game's camera a weapon hung behind the back is hidden by the body.
- **The kneel is side-on to its mark.** The bolt's line reads from above.
- **Cinematic clips are judged in the cinematic, at its cameras and with its staging.** A clip that looked right on a sheet (`bend_lift`'s first pass) folded him through her in C02. Measure the staging with `--cinebones`.
- **Take what a take does well, key what it can't.** Kimodo's bodies have weight, but its hands hold nothing. Key the hands over the take (`build(..., base=...)`), and reset a take's fingers first (`_bare_hands`).
- **The Warden's clips live in folk.res** (he is the kit man at 2.5 times), not in a library of his own.
- Earlier: corpses lie three ways with weapons laid flat; his clips come from her code with a man's numbers; gestures are additive; Kimodo's slam was rejected.

## 7. Failures and why

- **The first `bend_lift` folded him through her.** The take's bend is for a man looking at the ground; at 2.5 times, an arm's length from her, that put his head at her shoulder. It was cut at the right depth instead.
- **The cinematic played Idle in place of `folk/...` clips.** `People.Resolve` maps any name the library lacks to Idle. Fixed in `People.Clip`.
- **The Warden's lamp hand thumbed a lift.** The keyed fist bent the thumb but never brought it across. Fixed with `"oppose"`.
- **`rise_stiff` lay through the ground and stood 0.7 m off his mark.** Retargeting doesn't ground a lying body, and the take travels as it rises. Fixed with `_grounded` and `_settled`.
- **The disk filled briefly** (0 bytes free on C:, about 20:35 on 4 October; not ours). Every worktree's `godot/.godot` is about 1.8 GB.

## 8. Gotchas

- **Fresh worktree:**
  - `godot/assets` checks out as a text file. Replace it with a junction to `public/assets`, then run `git update-index --assume-unchanged godot/assets`.
  - Copy `public/assets` `*.import`/`*.uid`, `godot/.godot` and `tools/anim/out/{clips,folk,hero}` from a worktree that has them (robocopy).
  - Run `--import` in the background. It segfaulted once part-way; running it again finished it.
  - Restore `.import` churn with `git checkout -- "*.import"` before committing. Never commit `.uid` or `.import` files.
- **This sandbox refuses** `cd ... && git` chains with heredocs or runtime-built programs, `sed` in loops, and `python -c` that touches git paths. Write patch scripts to the scratchpad and run them plainly.
- **The scratchpad is shared by every agent.** Keep yours in a subfolder (mine: `scratchpad/anim3`).
- **`folk.py <names>`** filters on the bare name ("slam", not "m_slam"). A name matching nothing packs nothing. Every pack takes every JSON in `out/folk`: move try-takes (`*_k_*`) out first (`repack.py` does it).
- **The VAT cache `user://vat` is shared by every worktree.** Bump `Vat.Version` when a bake changes.
- **In-game captures:** pass `--fixed-fps 30` (engine side, before `--`) so frames land on time. Use `--lab --give +vitality` so the creature isn't flashing white from blows. Spawn far enough away (`--dist 7`) that it doesn't overlap the survivor.
- **Fingers in keys:** a preset name and a dict don't blend. Use dicts with the same keys throughout one clip.
- **Combat's sim** sets `e.Anim` to Move or Idle on the tick after a cast, and only an Attack resets `e.AnimT`. Play post-cast tails on `AnimT` with view-side state (`CrowdView.Gait`), never on `e.Anim`.
- **Scratch tools** (in `scratchpad/anim3`, each short to rewrite):
  - `stick.py <keyed|take:prompt_n|warden:name> [m|f] [step]`: stick figures (side and front), the lowest joint per frame.
  - `joints.py name sex frames...`: joint positions.
  - `csheet.py`: CrowdSheet rows. `hsheet.py`: anim_review rows (`model=male`, `@crossbow`).
  - `game.py name <args>`: the game at 1920x1080 with `--fixed-fps 30`. `tile.py`: crops of game frames tiled.
  - `cine.py CINE NAME UNTIL [--stills N]`: a cinematic's stills with `--cinebones`. `board.py`: stills tiled.
  - `cine_try.py` / `cine_try3.py on|off`: the local C02/C03 cue swaps.
  - `try_takes.py`: whole Kimodo takes as `k_` clips. `repack.py`: moves `k_` JSONs aside and repacks under a turn.

## 9. Collaborators

- Main session: `main`.
- Combat: a708da2c97bf85c95 handed off; their successor has the plants and the repoint (§5).
- Cinematics: a79b6d8c81e14dc63 (new lead). The timelines are theirs; send clip names and cues.
- Male hero: ab82cbe99e2937ddd (§4.5).
- Experience director, performance: see the roster in `docs/team/README.md`.

## 10. Read first

1. `docs/team/animation.md`, then this page.
2. `tools/anim/crowd.py` (the slam, the kneel, the fallen) and `tools/anim/clips/warden.py`.
3. `godot/src/Actors/CrowdView.cs` (the Casting case and the tails in `default`), `Vat.cs` (`BakePerson`), `FolkClips.cs`, `Visuals.cs`.
4. `tools/anim/keyed.py` (controls, `build(base=, post=)`, fingers), `clips/generated.py` (`make`, `warp`), `clips/story.py`, `folk.py`.
5. For the next clips: `docs/cinematics/shoot/c01.md` and `c04a.md`, and `godot/data/cinematics/c01.json` and `c04a.json`.
