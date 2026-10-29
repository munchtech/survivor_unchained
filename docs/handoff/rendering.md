# Handoff: rendering (global light, exposure, tonemap, grade, her light vs the scene's)

## Now (Rendering 1, 28 Oct): fixed list DONE (3 rounds, final max judge: merge YES, no regressions); MR READY
- **Worktree** `.claude/worktrees/rend-1`, branch `rend-1` (from integration 7b94438d; `godot\assets` is a junction to its OWN `public\assets`, assume-unchanged; the unstaged `.import` edits are reimport noise, not ours). Scratch (the coordinator's pad): `...\scratchpad\rend1\`: shoot.sh (list format `NAME|WxH|ENV|ARGS|SECONDS|COUNT|EVERY`, `EXTRA=` for switches), r0.txt (the 30-frame worst-case set: Low Ford night play, camp, lantern, a night fight, the close-up at camp fair and deep, the town by night, day and dawn at play and close-up, the Look by night, day and deep), measure.py, sheet.py, `r2d\face3.py` and `e\e_face.py` (face box: face:bg, key:fill, cheek L/C/hue; reads `--camlog`), `work_c\poolc.py` (pool areas), briefs and verdicts j0-j3, frames r0-r3. Backed up to `survivorsunchained_inputs\scratch_rend1\`.
- **What changed:**
  - **LowFordNight (Atmospheres.cs, d351ad4e):** moon 1.7, exposure 1.3, fill #34507e at 1.6, env 0.6, the shade blue (not violet), ember 3.5.
  - **Camp:** lantern 0.42, range 3.2 (props_own.json `lamps.glow-1-0`, 480df369); the fire light 80/18 (zone.json lights[0]).
  - **The town:** NightTown ember 3 plus a lift; WaystationDay PaintShadowK 1.6 (cool slate shade).
  - **Her ember, split (PlayerView.cs, 105cdcaa):** a ground-only 2500K pool, plus a `FolkLight` 4.5 m up for her and the people near her; her gear on the people layer while it's on. Flare burst gain capped at 2.2. Near a lamp (3 m) the folk light halves and the pool is cut.
  - **Close-up rig (GameCloseUp.cs, 745d3847, 64f35775, f806d91e, 2bacf782, 71c9d88e):**
    - The key comes from the nearest fire or lamp (or the moon), 3000K, held within 100 deg of where she faces, 65-75 deg off the camera at Low Ford and 50-60 in town.
    - A cool fill at 0.25 plus extra on dark skin.
    - A warm ground spot lights the world around her (not in town).
    - Her shield and sword are on her gear layer at the night close view, with their metal halved.
    - Town lamps are 1 stop down at the night close view (a camera multiplier; the town's data is untouched).
    - Her folk light is off and her pool at 0.25 in the town's night close view.
  - **Skin guard (Atmosphere.cs GradeLut, ae09adb5):** up to 25% chroma off strong red-orange skin, close view and Look only.
  - **The Look by night (GameFront.cs, 6167d17f; People.HerSkinGain, 05450777):** a fire-side key, a cool fill, and deep skin +0.5 stop on the skin only.
  - All the knobs are `--close-*`, `--look-night-*`, `--ember-*` and `--skin-guard-*` switches.
- **Closed:**
  - Not visible at 1:1: night crushing her and the dead; the AgX lantern blowout (no own tonemap needed); the BattleFx discs.
  - Passed: Low Ford's dark wash, the camp lantern, her ember at the play camera, deep skin at the close-up, the town's day shade, the Look by night, tcloseN, tdawn_01, tnight_01.
- **Closed as known (round cap, j3):**
  1. **tnight_02, the town night close-up at the stall:** flat front light, pale and waxy. It's a dialogue spot: RESTAGE first in the next rendering pass, keying her from the stall-lamp side with tcloseN_00's rule.
  2. **The night close-up in near-profile (lfclose_00):** flat pale cream. The three-quarter view (lfclose_01) is modeled. Suspect the extra dark-skin fill. Restage any staged shot at this angle.
  3. **The deep preset's copper hair reads paler than on fair skin:** the crown pixels match, so pick the same strands first; if they match, it's Face/hair (a per-skin swatch).
  4. **Deep shoulders and chest redder than the face at the Look:** body vs face albedo (Face/body).
  5. **The wood road's side thirds near-black (Environment's judge):** the fill and env barely move them (+1-2 luma at hemi 2.8, env 1.0); only the moon or exposure would, which would undo the passed darkness.
  - Marks: the town by day close-up face is a little flat and the haze milky; shaded wood reads navy by day; a hot yellow sheen on the forehead at lfclose_01.
- **Routed:** the cobble patches are Environment's mud decals (unchanged with SSAO and key shadow off); the forehead seam at the hairline is Face/hair; the moon glints were fixed by Environment (#d8e0ea).
- **Owner sheet (half size, judge-passed frames):** `survivorsunchained_inputs\rend1\rendering_before_after.jpg` (the night close-up, Low Ford at night, the camp, the town at night at play and close-up).
- **Cost:** judges 150k + 157k + 158k + 149k; solvers A 157k, B 201k, C 156k, D 182k, E 200k; lead ~250k. About 1.8M in all.
