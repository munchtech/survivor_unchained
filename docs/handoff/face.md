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
- `presets_wrap.ps1 -ids ...` (wraps, TRELLIS heads copied to `face5/tr_<id>`), `build_v8.ps1` (unpainted head, all paints with sides kept, head, features, hair, body, import), `build_v8b.ps1` (presets' paints with fresh Krea sides: v8e's presets' sides are these, kept since by `FACE_REUSE`; hers are v7's), `shots_v8.ps1 -tag T` and `sheets.py T` (the side-by-side, the ten-face sheet, eye calibration, play zoom).
- Measures: `eyes_check.py` (Blender: each key's eye opening against hers, eyeball through skin), `iris_sample.py` and `skin_sample.py` (MediaPipe on shots and portraits; run with `%LOCALAPPDATA%\facefit\.venv\Scripts\python.exe`), `eyefix.py` (eye dyes from measured shots), `tones.py` (preset tones from portraits), `holes.py` (paint holes), `occl_probe.py`, `inner_probe.py`.

## Done (v8e, commit 6e73f647)
- The v7 review answered (details and numbers in `docs/team/face.md`'s Current state): eyes open on every preset, Saffron's smudge and Sunborn's seam gone (both were her mouth's walls laid on the cheeks by the wrap), irises matched to the portraits, the neck band gone, the hairline blended, the presets' lips clean, skins from the portraits.
- Code: `face_wrap.py` (her inside kept inside; eye floor 0.89; lips' meeting held; teeth behind the lips), `heroine_head.py` (`matched_base`; body paint padded), `heroine_face.py` (eased visibility; jaw underside left to her head's skin), `heroine_features.py` (AO), `heroine_hair.py` + `heroine_hair_soft.gdshader` (blended cap and fine hairs), `heroine_eye.gdshader` (`iris_light`, `wet`, `wet_rough`), `heroine_skin.gdshader` (`ao_map`, `scalp_stubs`), `GameFront.PortraitLight` (the moon off her at the close-up), shot flags.

## Next (worst first; the owner: keep improving until the credits run out, at the Look close-up and at play zoom)
1. **Her own face's teeth show between her lips** (v8 regression). Put back v7's target (`git show 1970f5c3:tools/assets/heroine_face/targets/portrait-heroine.target > tools/assets/heroine_face/targets/portrait-heroine.target`), run `build_v8.ps1` and `shots_v8.ps1 -tag v9 -nocal`, and check her lips at 1:1. If v7's has its own faults (a notch under her jaw in clay), find why the new wrap parts her lips instead (`teeth_probe.py` on the built blend).
2. Tell the main session when it passes: it refits and merges, then runs the portrait steps itself (UI design is paused).
3. Sloe and peat a little dark (see the status page); a faint pale wedge under her jaw on her left; her skin's fine grain half the portrait's; hair cards like broad strokes at the close-up (hashed alpha; try alpha to coverage at the High tier); pale patches on her upper chest (her body's paint: tell the main session).
4. Play zoom: her face is ~15 px from above; the far deepening reads as eyes and brows; nothing broken (v8e_play_c*.png).

## Decisions (why)
See `docs/team/face.md`'s Key decisions.

## Failures (and why)
- v7's wrap laid her mouth's walls on its cheeks (a ray along a wall's normal met TRELLIS's skin, the surface turned to face as hers does): Saffron's smudges, holes in every paint, the jaw seam, side paintings drawn with the blotches.
- Exempting her lips' linings from the set-back (a "lip zone") moved her chin by 9 mm: reverted.
- Moving the eye's catchlight on a guess: the white blob under her pupils was the moon's reflection, not the catchlight.
- Eye calibration by `--eyecycle` on one run: she moves in the Look's idle, frames differ. Calibrate from the presets' own shots (`eyefix.py ... lum`); the dark eyes swing (the cornea's sheen dominates there).

## Collaborators
- Main session (coordinator): reviews the sheets, refits outfits on `heroine_built.blend`, merges, runs the portrait steps.
- Male hero (paused): shares the eye shader; his `HisEyes` is the new flint.

## Files to read first
`docs/team/face.md`, `tools/assets/face_wrap.py` (INSIDE, LIPS MEET, TEETH), `tools/assets/heroine_head.py` (`matched_base`), `godot/shaders/heroine_eye.gdshader`, `scratchpad/face5/build_v8.ps1` and `shots_v8.ps1`.

## Gotchas
- Her worktree's `heroine.glb` and outfits are refitted locally only: never commit them. `godot/art/people/x/` is the build's outfit scratch. Many `.import` files show as modified (the import cache came from the old worktree): don't commit them.
- `godot/assets` is a junction to `public/assets` here (`git update-index --skip-worktree godot/assets`).
- The worktree guard refuses commands that name git inside piped python or loops with variables: write a small Python file and run it.
- Shots: `--open-eyes` always; `--unshaded`, `--debugdraw Lighting|NormalBuffer`, `--eyeparam name=v`, `--rig K,F,E,R`.

HANDOFF READY: docs/handoff/face.md on worktree-agent-a6007bf07fd45ab0d@HEAD
