# Heroine face, hair and creation's Look: status

Agent a6007bf07fd45ab0d, branch `worktree-agent-a6007bf07fd45ab0d` (took over from a833b7942e978d994 at v7).
The handoff is `docs/handoff/face.md`.

## Current state (2026-10-05)
- **v8e** (committed art; sheets `godot/.shots/sbs_default_v8e.jpg`, `presets_v8e.jpg`, uncommitted) answers the main session's v7 list: every preset's eyes open (0.89 to 1.05 of hers through the pupil, Blender; 0.88 to 1.08 by MediaPipe in the shots), no smudge on Saffron, no seam on Sunborn and her skin a brown of her portrait's lightness, irises within 3% of their portraits' lightness against the skin (frost blue-grey, not white; both of Moonlit's eyes alike), the neck band gone (AO under her jaw, skin matched), the hairline blended, the presets' lips clean.
- **Open, worst first:**
  1. Her own (default) face shows the tips of her upper teeth between her closed lips at the close-up: a v8 regression (v7's lips met). Fix: put back v7's `portrait-heroine.target` (from commit 1970f5c3; v7's own wrap had none of her inside on her skin), or find why her lips part (`teeth_probe.py`); then `build_v8.ps1` and shots.
  2. Sloe and peat eyes a little darker than their portraits (the dark range is not linear: v8d 3x too light, v8e 2x too dark; try the geometric mean of the two dyes).
  3. A faint pale wedge under her jaw on her left.
  4. Her skin pinker and smoother than her portrait under the Look's warm light (fine grain 0.02 against the portrait's 0.045).
  5. Hair cards read as broad strokes at the close-up (hashed alpha; lock tints).
  6. Pale patches on her upper chest (her body's paint, not the face's).
- **heroine.glb and the outfits are not committed.** The main session rebuilds them with `heroine_outfits.py --body` from this worktree's `tools/comfy/out/heroes/heroine_built.blend`, and merges the art and the refit together.

## Key decisions (why)
- **The wrap keeps her inside inside** (`face_wrap.py`): points no ray leaves (her mouth's walls, nostrils) are carried along, not laid on TRELLIS's skin, and set back 1.5 mm behind her outside. v7's presets had their mouth's walls laid on their cheeks: Saffron's "smudges", holes in every preset's paint, Sunborn's jaw seam and a ridge along every preset's jaw.
- **Eyes at least 0.89 of hers by the lids' ring** (was 0.86): measured through the pupil, Fey's came out 0.84 at 0.86.
- **Her head's skin matched to her face and her body** (`heroine_head.py` `matched_base`): a harmonic colour field over her head's points. MakeHuman's paler, greyer skin was the band across her neck.
- **Preset skins from their portraits** (each portrait's skin against hers, as a tone on her paint): Vixen and Moonlit fair; Doe, Wildling and Hard-won rose; Saffron warm; Sunborn brown, with Brown lightened to `#ba7f5e` (Sunborn on Deep was four to six times darker than her portrait).
- **Her hairline blended, not hashed** (`heroine_hair_soft.gdshader`): her scalp's cap and the fine hairs at her hairline. Hashed alpha does not move, so the TAA kept its dots: a speckled band with a hard edge. Her scalp's shade is even (no stubs) and starts 4 mm under her hairline.
- **Shots hold her eyes open** (`--open-eyes`): v7's shut eyes were blinks caught.
- **The moon off her face at the Look's close-up** (`GameFront.PortraitLight`, from p > 0.5; back on in `EndCreate`): it was a fourth light, cold and flat, and its reflection a pupil-sized white blob on each iris.
- **Her head's AO baked** (`heroine_ao.png`, `ao_light` 0.55): the neck under her jaw was lit like her cheeks.
- **Paint edges eased, her jaw's underside left to her head's own skin** (`heroine_face.py`): triangle-at-a-time visibility drew a pale stair under her jaw.
- **Where her lips meet held hard to where TRELLIS's meet** (`face_wrap.py`, inner-lip landmarks at weight 5; the log's `LIPS MEET`): with her lips' linings carried, not laid on its skin, her lips parted a hair and the tips of her teeth showed.

## Next
1. The main session's review of v8; then its refit and merge. It runs the portrait steps itself (`heroine_paint.py brows`, `creation_portraits.py`, the Look shots: UI design is paused), which also fill creation's missing Sunborn, Moonlit and Saffron portraits. Message the main session, not UI design.

## Notes for other areas
- **Everyone taking pictures of her:** `--open-eyes` (lids up, eyes ahead), `--unshaded` (paint without light), `--debugdraw Lighting` (any of Godot's views), `--eyeparam name=v,...` (her eye shader's numbers), `--eyecycle paint,#rrggbb,...` (her irises dyed in turn).
- **Male hero:** the eye shader (shared) has `iris_light` (0.3: irises showed two and a half times too light against the skin) and `wet`/`wet_rough` (the cornea's sheen). The eye colours in looks.json are dyed for it, and his own `HisEyes` is the new flint.
- **UI design (when back):** the eye colour beads are darker now (looks.json `eyes`), as the irises render; the Brown skin is lighter.
- **Main session:** her body's paint is padded between its islands now (no red bleeding into her seams as it shrinks).
