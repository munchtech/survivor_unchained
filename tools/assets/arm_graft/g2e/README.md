# Body 1 stage 2e: the arm patch's UVs re-laid, her paint re-baked (armor 18 g2e, 22 Oct 2026)

Runs inside `g2c/run.sh` after `g2b/w_write.py` (skip with `SKIP_G2E=1`). Needs the graft's work dir (her.npz,
graft_data.npz, graft_geom.npz). Writes `survivorsunchained_inputs/armor_src/armroot_tex/heroine_body_paint.png` and
`heroine_graft.png` (copies; the originals stay packed in heroine_built.blend) and packs them into heroine_built_armroot.blend
under the old datablock names.

1. `plan.py`: patch faces = the new faces. Material carried (nearest old face), majority-smoothed (MAT_IT 6), per side the
   largest skin_graft piece touching the torso ring kept: the shoulder cap. Seams: the cap's edge, and one cut through the
   arm from the pit's underside (top quarter of ring points by under-score) to the wrist loop, Dijkstra on
   length x (1 + CUT_K (1 - n.under)^2), under = down + CUT_BACK x back, off the cap and its first ring of faces.
2. `b_img.py` (the original blend's two skin images as .npy), `b_unwrap.py` (SLIM, minimum stretch, UV_IT 60).
3. `bake.py`: islands scaled to the kept skin's area-weighted density along the torso ring, per material; packed by FFT
   search (rotations DROT 5 deg, corner strategies) into texels no kept face uses (KEEP_PAD 3, islands 2 PAD apart);
   density stepped down 3% at a time when a material's islands do not fit (F0_1 starts the graft's at 0.72, the known fit
   is 0.677). Bake: 3x3 samples per texel, patch point (before the shape field) -> closest point on her old arm/ring ->
   old UV -> old image of that face's material; PAD/2 padding; every other texel unchanged.
4. `b_apply.py`: materials, UVs and the two images into the armroot blend (in place; refuses the original).
5. `check.py`: colour delta E across the torso ring, the patch's seams and plain torso edges (noise floor); ring normals.
   `rp_dump.py` + `rp_render.py`: the export checked (images equal the copies) and rendered lit and textured at the town
   close-up camera (diagnosis only).
Freckles (`heroine_freckles.py`, laid on her surface) must be re-run on the armroot blend when the source switches (G3).
