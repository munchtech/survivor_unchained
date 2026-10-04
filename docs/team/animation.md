# Animation: status

Agent a435f4dd0ac80df75, branch `worktree-agent-a435f4dd0ac80df75` (took over from a1e3002b800ee55ac). The brief, history and gotchas are in `docs/handoff/animation.md`.

## State (paused for the owner, 2026-10-04)

- **Corpse variety: done** (848fab2, 8b2b54f).
  - Every kit body bakes `die`, `die2` and `die3` (`crowd.py`, `FolkClips.Deaths`): onto the back, onto the face, and in a heap on the side.
  - Armed bodies lay the weapon flat (`_armed`, and `_pistol` for crossbows). A shield lies on its forearm. Armed side-falls go onto the left side, so the shield arm is the one on the ground.
  - Wolves, boars and lamplings have three falls each (`Beasts.cs`). The VAT cache is v11.
  - The experience director wired the pick (CrowdView.DeathOf, on their branch). `VatAsset.Death(k)` exists too.
- **The hero's library: done** (72ab9a8). `build.py --body hero` builds 71 clips into `hero.res`, played as `him/`.
  - His carriage: feet wider (`Rig.feet_out`), the runs with square hips (`gait.manly`), and his neck bowed 10° into the mocap takes (`retarget.lean_neck`).
  - `OwnClips` (Her/Him) replaces HerClips' library half; `Person.Own` is hers or his. Seen on sheets and in the game (`--quick warden --sex male --body hero`).
- **Gestures: done** (d7b091e). `her/nod`, `her/exhale` (held) and `her/shiver` are laid over any pose (`Gestures.cs`); a cinematic cue of one is laid over, not swapped in. Judged over `sit_log`. Cinematics placed them in its handoff.
- **Kimodo:** the owner's run is complete (every prompt has 3 takes in `C:/Users/munch/Tools/mocap/kimodo`).
  - `slam` takes: rejected. They don't read as a two-handed overhead slam.
  - `kneel_shoot` take 0: a good drop to one knee and aim. Takes 1 and 2: rejected.
- **In progress:** `slam` / `slam_armed` keyed in `crowd.py`, checked only on stick figures (it is in KEYED, but nothing maps to it yet). Timing: the gather; the fists up overhead by 0.7 s; the hang; the fists into the ground at 0.95 s; held.

## Next (exact)

1. Build and judge the slam: `python tools/anim/folk.py slam`. Map it as the `Cast` for kerchief_brute and skeleton_minion: add `"Slam"` to `FolkClips.Crowd`, and in `Visuals.cs` give those two `cast: "Slam"`. Then judge it on CrowdSheet (`VISUAL=kerchief_brute ROLE=cast`) and in the game with mb_barn_door, and bump `Vat.Version`.
2. Kneel-to-shoot: asked combat (a1d4562f44c7f6feb) for a `RangedSpec.Aim` windup (Windup with `AnimT = 0`, then Shoot). Key `kneel_aim` as the windup, played from `e.AnimT`, and `kneel_shot` as the attack (the release, the kick, the rise). Add a `kerchief_crossbow` visual for levy_crossbow.
3. Cinematics' Kimodo clips, judged with the scratch `try_takes.py` (whole takes as `k_<prompt>_<take>`; delete them and repack after). Start with C02's rise_stiff and bend_lift on the kit man, kneel_fall (C03) and flask_drink (C04).
4. Polish: the chain haul's landing crouch, and a heavier flinch while running (a gesture through `Gestures` would do it).

## Key decisions

- **Corpses lie three ways, and weapons lie flat.** A sword stood on end in a corpse read as a pillar.
- **The hero's clips come from her code with a man's numbers, not from her clips.** Her line-walking hip sway read as feminine on him.
- **Gestures are additive** (each bone's change from frame 0), so one nod serves any pose and any body.
- Takes that don't fit the game's action are rejected, not bent to fit. That rejected Kimodo's slam.

## Gotchas found this session

- Keyed hands that mix `arm()` keys (chest frame) with `pos` keys: give the pos keys `"frame": "char"`. `crowd._in_char` turns a whole clip's hands into character space.
- Bash refuses some multi-line python heredocs and `cd ... && git`. Write patch scripts to the scratchpad and run them plainly.
- A full `--import` dirties hundreds of `.import` files. Restore them with `git checkout -- "*.import"`.

## Notes for other areas

- Experience: wire the pick only to the role names; v11 has die/die2/die3 for every kind.
- Male hero: `him/` clips stand HerPose down (`Native = 1`). Rebuild his library after any rig change (re-dump `hero_skeleton.json`).
- Cinematics: gesture cues use `"do": "anim"` with the clip `her/nod` and so on.
