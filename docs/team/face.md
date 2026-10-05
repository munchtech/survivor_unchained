# Heroine face, hair and creation's Look: status

Agent a833b7942e978d994, branch `worktree-agent-a833b7942e978d994` (took over from a6784044c82f101d9).
Read first: `docs/handoff/face.md` (the last handoff) and `docs/FACE_RESEARCH.md` (the science).

## Current state (2026-10-04, night)
- **Her face is now a TRELLIS 2 head's**, made from her front reference (`her_23`), laid on her MakeHuman head by `tools/assets/face_wrap.py` and written as our own target `portrait-heroine` (in `face_shapes.FACE`).
  - Topology, rig, UVs, sliders and expressions are kept.
  - Judged in the game at the Look close-up under UI design's portrait light: she reads as a pretty young woman, close to her reference. The old heavy jaw, gaunt cheeks and thin lips are gone.
- **Her face is painted with the reference itself** (`heroine_face.py` with `FACE_REF`): the photo warped landmark to landmark onto the front, its own light partly taken out using her normals; the sides are Krea's as before.
- **Hairline:** lowered to 6.8 cm over her eyes (the reference's), hair cards rooted at it, and the hair cap's fade cut to 6 mm. Her scalp under the hair is darkened to her hair's colour (`heroine_shadow.png`, `People.HerScalp`), so there is no pale, bald brow between the cards.
- **The art is on disk, not committed** until it's judged good.

## Key decisions
- **TRELLIS 2 over MoGe-2** for the shape: MoGe sees only the front and reads it flat; TRELLIS gives the whole head, its volumes round to the ears and under the jaw. (MIT, local.)
- **Landmarks read alike on both heads:** clay renders of hers and TRELLIS's, lit the same, MediaPipe on both. The old `face_lab` anchors were read off a textured render and disagreed.
- **The whole head is wrapped**, her cranium too (her skull 5 mm under TRELLIS's hair). MakeHuman's skull was a tall egg.
- **Her head is sized by its shape before the portrait.** By its own nose and chin, the portrait grew her head 12%.
- **Each eye's opening is an affine map** of her lid landmarks onto TRELLIS's. The eyeball moves whole, never stretched, and the lids are laid back on it.
- **Made symmetrical:** TRELLIS's guess is a little lopsided.
- **Presets:** each its own TRELLIS head and its own key, `face_<id>` (from her own face to it), plus its own paint. `People.HerFaceKey` sets the key; sliders work on top. Hair follows the key.

## Next
1. The default face: the skin's colour and detail, and the hair's frame (volume, face-framing locks, the long style's bald parting and a stray lock across her cheek).
2. The presets: front references by Krea (`face_refs.py --front`), then TRELLIS, wrap, paint, and `face_looks.py` with the presets' slider shapes emptied.
3. Play-zoom readability.

## Notes for other areas
- **Main session:** her head changes `heroine_built.blend` (the whole skull, not the neck: the wrap holds her neck and nape). I'll message before pushing the art, for the outfits.
- **UI design:** the portrait light works; faces are judged under it now. The creation portraits want rerunning once the head lands.
- **Male hero:** `face_shapes.FACE` gained `portrait-heroine` (hers only), and `target_paths()` now includes `heroine_face/targets/`. SLIDERS and REACH are unchanged.
