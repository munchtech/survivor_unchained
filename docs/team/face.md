# Heroine face, hair and creation's Look: status

Agent a833b7942e978d994, branch `worktree-agent-a833b7942e978d994` (took over from a6784044c82f101d9).
Read first: `docs/handoff/face.md` (the last handoff) and `docs/FACE_RESEARCH.md` (the science).

## Current state (2026-10-05, early)
- **Her face is a TRELLIS 2 head's**, made from her front reference (`her_23`). `tools/assets/face_wrap.py` lays her MakeHuman head on it and writes our own target, `portrait-heroine`, in `face_shapes.FACE`.
  - Topology, rig, UVs, sliders and expressions are kept.
  - Her lips' outline is the photo's (`--photo`); everything else is TRELLIS's volumes.
- **Her face is painted with the reference itself** (`heroine_face.py` with `FACE_REF`):
  - the photo is warped onto her head by landmarks read off her head in clay;
  - its light is partly taken out by her normals;
  - its fine grain is added back from a light Krea pass (`FACE_DETAIL`);
  - the sides are Krea's.
- **v5 was judged in the game** (side-by-side `godot/.shots/sbs_default_v5.jpg`). The main session called it a clear step. Its fixes:
  - hair no longer grows from the roof of her mouth;
  - a softer catchlight;
  - a lighter skin tone;
  - a lower hairline from TRELLIS's;
  - no face paint under her jaw.
- **v6 is building:** freckles and grain from Krea, the photo's lips, every hair card fading in from its root, an uneven parting, and loose tendrils for Tail.
- **Presets:** front references are chosen (`scratchpad/face4/refs_front/picks.jpg`), and TRELLIS heads are queued. Each becomes a `face_<id>` key and its own paint.
- **The art is on disk, not committed.** My worktree's `heroine.glb` and outfits are refitted locally (`heroine_outfits.py --body`) for shots only.

## Key decisions
- **TRELLIS 2 over MoGe-2** for the shape: MoGe sees only the front and reads it flat. (Both MIT, local.)
- **Landmarks read alike on both heads:** clay renders, lit the same, MediaPipe on both. Not the photo's eyes: off a photo, MediaPipe draws the eye's rim at the lash line, a fifth taller than off clay.
- **The whole head is wrapped**, with her skull 5 mm under TRELLIS's hair. MakeHuman's skull was a tall egg.
- **Her head is sized by its shape before the portrait.** Otherwise the portrait grew her head 12%.
- **The eyes:** each eye's opening is an affine map at 0.92 height (her eyes stared at full height). The eyeball moves whole.
- **Made symmetrical.**
- **Hair grows only from her outside:** inside her head's outline is never scalp.
- **Her scalp is darkened to her hair's colour** (`heroine_shadow.png`, `People.HerScalp`), not covered by a long hashed fade.
- **Presets:** each has its own whole face as a key, `face_<id>`, set by `People.HerFaceKey`. Their slider shapes are emptied, and the sliders work on top.

## Next
1. v6 in the game, then send the main session the side-by-side in the same four columns.
2. The presets: TRELLIS heads, then the wraps, the unpainted head with all the keys, the paints (`presets_paint.ps1`), and `face_looks.py`. Then a sheet of all ten.
3. Play-zoom readability (`--auto toward` walks her to the camera), and the `far_*` tuning.
4. When it's final: commit the art, then message the main session for the outfits.

## Notes for other areas
- **Main session:** her head changes `heroine_built.blend`: the whole skull, not the neck or nape, which the wrap holds. I'll message before pushing the art.
- **UI design:** rerun the creation portraits once the head lands. New shot flag: `--turn DEGREES`.
- **Male hero:** the eye shader's catchlight and limbal ring changed (it's shared). `face_shapes.FACE` gained `portrait-heroine` (hers only), and `target_paths()` includes `heroine_face/targets/`.
- **Experience / combat:** new shot flag `--auto toward`, which walks the survivor down the screen to the camera.
