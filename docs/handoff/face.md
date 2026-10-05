# Handoff: the heroine's face, hair and creation's Look

From agent a833b7942e978d994 (who took over from a6784044c82f101d9).
Read `docs/team/README.md`, then this page, then `docs/team/face.md`.

## The owner's words
- "all of the pre made faces are kinda ugly"; "for premade faces generate beautiful ones with our local ai hookup".
- "the customizations don't do enough to change".
- The face must read at every in-game zoom except the farthest.
- Latest: "face is doing a great job, keep up the work".

## The brief, in order
1. The default face clearly beautiful, judged against `her_23` at the Look close-up under UI design's portrait light.
2. The hairline: lower, with a natural full frame of hair.
3. Each preset genuinely its own face.
4. Readability at play zoom.

Rules:
- Legal: Krea 2 is allowed (it counts toward the US$1M cap); TRELLIS 2 and MoGe-2 are MIT. Never Hunyuan3D, web tools, or pictures of real people or others' art.
- Don't edit `heroine_outfits.py`. Message the main session before pushing art that changes `heroine_built.blend`.
- Take turns with `tools/turn.py`:
  - `gpu` only for ComfyUI, TRELLIS and MoGe;
  - `blender` for builds and renders;
  - `godot` for shots.
- Batch shots, and look once.

## How her face is made now (the pipeline)
1. `face_refs.py --front` (Krea) makes a front portrait.
2. `face_trellis.py` (TRELLIS 2) makes a head of it.
3. `face_wrap.py --photo <ref>` lays her MakeHuman head on that head, and writes `tools/assets/heroine_face/targets/portrait-<id>.target`.
   - Hers is `portrait-heroine`, in `face_shapes.FACE`.
   - Each preset's becomes the key `face_<id>` (`heroine_head.py`), set by `People.HerFaceKey`.
4. `heroine_face.py` with `FACE_REF` (and `FACE_SHAPE` and `FACE_WHO` for a preset) paints the face:
   - the front from the portrait itself, warped by landmarks read off her head in clay, partly delit by her normals;
   - fine grain from a light Krea pass;
   - Krea for the sides.
5. Then `heroine_head.py`, `heroine_features.py` (also `heroine_shadow.png`, the scalp mask), `heroine_hair.py`, a local `heroine_outfits.py --body`, and the Godot import.

The scratch scripts in `scratchpad/face4/` drive all of it, and point at my worktree:
- `build_v7.ps1`: the whole build, with turns;
- `presets_wrap.ps1` and `portrait.ps1`: the wraps;
- `shots_v7.ps1`: the side-by-side, the ten-face sheet and the play-zoom shots;
- `refs_front/`: the presets' references (`picks.jpg`).

## Decisions (why)
- **TRELLIS over MoGe:** MoGe sees only the front and reads it flat.
- **Both heads read alike:** landmarks come off clay renders of each, lit the same.
- **Landmarks hold across her face, hardly in depth:** ray depths crumpled her lips.
- **The photo sets only her mouth's width**, never where her lips meet; taller, it folded or parted her lips.
- **Eyes:** an affine map of TRELLIS's opening, at 0.92 of its height and never under 0.86 of hers. TRELLIS shuts some eyes to slits.
- **The head is sized by its shape before the portrait,** or it grows 12%.
- **Hair grows only from her outside:** before, it grew from the roof of her mouth and hung under her jaw.
- **The scalp is darkened to her hair's colour** under the cards, from a centimetre under the hairline.
- **Every card fades in from its root over 8 mm.**

## Done
- **v7:** her face and nine presets' faces as above. Art is committed; heroine.glb and the outfits are left to the main session's refit.
- **Fixes:**
  - No hair grows from inside her mouth.
  - The eyes have a smaller catchlight and a darker limbal ring.
  - The skin tone and darker tones are truer.
  - Her scalp is darkened under the hair.
  - Tail has tendrils.
  - The far-zoom deepening is stronger.

## Failures (and why)
- **MoGe depth:** a flat mask.
- **The photo's lip landmarks taken whole:** they parted and folded the lips.
- **Preset nose and lip fixes on the shaped head:** they made dark blotches (the mouth's inside lies near the lips), so presets now get lid cleaning only.
- **TRELLIS seed 56:** faceted on Sunborn and masculine on Highborn; both were re-rolled at seed 61.

## Next
1. The main session refits the outfits on this worktree's `tools/comfy/out/heroes/heroine_built.blend`. Then UI design reruns `brows.png` and the creation portraits.
2. Tail's hairline edge is still hard: try a ring of very fine, short, low-alpha cards over it, or a hair-strand texture in the scalp mask.
3. Saffron has a pale smudge under each eye: check `paint_saffron/painted_left.png` and the right one, and the sides' colour match.
4. Some presets' lip lines are a little crumpled: try more lip smoothing in `face_wrap.py`.
5. Play-zoom review.

For the current state, see `docs/team/face.md`.

## Gotchas
- Her worktree's `heroine.glb` and outfits are refitted locally only. Restore them with `git checkout` before merging integration, and never commit them.
- Generated `.uid` files can block a merge; delete those that git names.
- The hair dumps (`HAIR_DUMP`) and `scratchpad/face4/stray.py` find stray strands.
- Shots: `--step 1 --part 1` is the Look's Face; `--turn DEG`; `--preset ID --skin --eyes`; `--auto toward` at play zoom.
