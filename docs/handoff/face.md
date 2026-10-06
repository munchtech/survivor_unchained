# Handoff: the heroine's face, hair and creation's Look

From agent a6007bf07fd45ab0d (who took over from a833b7942e978d994 at v7).
Read `docs/team/README.md`, `docs/team/RESUME.md`, then this page, then `docs/team/face.md`.

## The owner's words
- "all of the pre made faces are kinda ugly"; "for premade faces generate beautiful ones with our local ai hookup".
- "the customizations don't do enough to change".
- The face must read at every in-game zoom except the farthest.
- "face is doing a great job, keep up the work". The bar: "we are striving for perfection".

## The brief
1. The default face clearly beautiful, judged against `her_23` at the Look close-up under UI design's portrait light.
2. The hairline: lower, with a natural full frame of hair.
3. Each preset genuinely its own face.
4. Readability at play zoom.
5. The main session's review of v7 (all answered in v8, see Done): shut eyes (prove open at the 0.86 floor), Saffron's smudge, Sunborn's seam and plastic skin, iris colours against the portraits, the neck band, Tail's hairline, crumpled lips, play zoom.
6. The flow after a pass: the main session runs `heroine_outfits.py --body` on this worktree's `tools/comfy/out/heroes/heroine_built.blend`, refits the outfits, and merges this branch with the refit (never without). The main session then runs the portrait steps itself (`heroine_paint.py brows`, `creation_portraits.py`, the Look shots; UI design is paused): message the main session, not UI design.

Rules: Krea 2, TRELLIS 2 and MoGe-2 only (never Hunyuan3D, web tools, real people). Don't edit `heroine_outfits.py`. Turns (`tools/turn.py`): `gpu` for Krea/TRELLIS/MoGe, `blender` for builds, `godot` for shots. Batch shots, look once. British spelling.

## How her face is made (the pipeline)
1. `face_refs.py --front` (Krea) makes a front portrait; `face_trellis.py` (TRELLIS 2) a head of it.
2. `face_wrap.py --photo <ref>` lays her MakeHuman head on that head: `targets/portrait-<id>.target` (hers `portrait-heroine`, in `face_shapes.FACE`; each preset a key `face_<id>`).
3. `heroine_head.py` with `HEAD_UNPAINTED=1` → `heroine_unpainted.blend`.
4. `heroine_face.py` with `FACE_REF` (and `FACE_SHAPE`, `FACE_WHO` for a preset; `FACE_REUSE=1` keeps the side paintings already in the out dir) paints each face.
5. `heroine_head.py` (painted; `matched_base` brings her head's own skin to her face and body), `heroine_features.py` (features, scalp shade, AO), `heroine_hair.py`, a local `heroine_outfits.py --body`, the Godot import.

The scratch scripts in `scratchpad/face5/` drive it (they point at this worktree; inputs stay in `face4/`: `refs_front/`, `from_face3/`):
- `presets_wrap.ps1 -ids ...` (wraps, TRELLIS heads copied to `face5/tr_<id>`), `build_v8.ps1` (unpainted head, all paints with sides kept, head, features, hair, body, import), `build_v8b.ps1` (presets' paints with fresh Krea sides), `shots_v8.ps1 -tag T` and `sheets.py T` (the side-by-side, the ten-face sheet, eye calibration, play zoom).
- Measures: `eyes_check.py` (Blender: each key's eye opening against hers, eyeball through skin), `iris_sample.py` and `skin_sample.py` (MediaPipe on shots and portraits; run with `%LOCALAPPDATA%\facefit\.venv\Scripts\python.exe`), `eyefix.py` (eye dyes from measured shots), `tones.py` (preset tones from portraits), `holes.py` (paint holes), `occl_probe.py`, `inner_probe.py`.

## Decisions (why)
See `docs/team/face.md`'s Key decisions. In short: the wrap keeps her inside inside; the eye floor 0.89 by ring; her head's skin harmonically matched; AO baked; skins from portraits; hair cap and fine hairs blended; eyes calibrated to portraits; the moon off her face at the close-up.

## Failures (and why)
- v7's wrap laid her mouth's walls on its cheeks (a ray along a wall's normal met TRELLIS's skin; the surface was turned to face as hers does). It made Saffron's smudges, holes in every paint, the jaw seam, and side paintings drawn with those blotches (repainted fresh in v8b).
- Flipping the eye's catchlight on a guess: the paint's v runs down the eye as expected; it was the moon's reflection, not the catchlight, under the pupil.
- A calibration run cycling eye colours: she moves in the Look's idle, so frames differ in pose; calibrate from presets shot one per run instead (`eyefix.py`).

## Gotchas
- Her worktree's `heroine.glb` and outfits are refitted locally only: never commit them. `godot/art/people/x/` is the build's outfit scratch.
- `godot/assets` is a junction to `public/assets` here (`git update-index --skip-worktree godot/assets`).
- The worktree guard refuses commands naming other worktrees' git or complex shell loops with variables: write a small Python file and run it.
- Shots: `--open-eyes` always; `--unshaded`, `--debugdraw Lighting|NormalBuffer`, `--eyeparam name=v`, `--rig K,F,E,R`.

HANDOFF READY: (to be completed)
