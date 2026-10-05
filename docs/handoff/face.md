# Handoff: the heroine's face, hair and creation's Look

From agent a6784044c82f101d9 (who took over from ade92e8285938438f), at about 500k tokens, to a fresh successor.
Read `docs/team/README.md` first, then this page, then `docs/team/face.md` (status) and `docs/FACE_RESEARCH.md` (the science).
Branch `worktree-agent-a6784044c82f101d9`. The integration branch is merged in at 75f6d431.

## The owner's words
- "all of the pre made faces are kinda ugly"; "for premade faces generate beautiful ones with our local ai hookup".
- "the customizations don't do enough to change"; "chin can't get any narrower"; "some things not editable like forehead etc."
- "look up beauty science and proportions and fix that stuff".
- "weird hair strands in her neck"; a harsh, ragged hairline.
- "some sort of semblance of a face should exist at anything other than completely max zoom": the game's own camera range. His screenshot showed her face as a red-orange blur.
- The bar: AAA, "never settle", sex appeal "tho not at the cost of looking bad".

## The brief (from the main session)
The main session's critique of the presets:
- the lips are thin and flat;
- the eyes are small, with no lid crease or lash line;
- the skull is long and the lower face heavy;
- the brows are plain;
- every preset is nearly the same face.

The default face isn't beautiful yet. In order:
1. Build FACE v3 and paint it.
2. Judge it at the Look close-up, with hair on, in the game's light.
3. Send the main session a side-by-side: the default, vixen and sunborn, each against its reference. Do this before painting the rest.
4. Review the play-zoom readability shots.
5. The neck strands.

Rules for the head:
- When her head or neck changes `heroine_built.blend`, message the main session before pushing. The main session re-runs `heroine_outfits.py --body`, then tells UI design to re-run the portraits.
- Don't edit `heroine_outfits.py`.

Rules for work:
- Free ComfyUI after each batch (`POST /free`); never kill it.
- Run `dotnet test` before every commit.
- Commit and push your own branch at milestones. Open no PRs.
- Use British spelling.

## What I did
1. **FACE v3 is built and painted** with `chain_face.ps1 -seeds 11,7 -prefix paintD`, then `finish.ps1 -paint paintD_s11` (seed 11 is the prettier).
   - Head, features, all 5 hairstyles and Godot's import are done in this worktree. **The art is on disk, not committed.**
2. **Judged at the Look close-up** (`scratchpad/face3/lookD.jpg`).
   - **Better than v2:** the mouth no longer bulges forward.
   - **Still not beautiful:**
     - the face is long and gaunt in the cheeks, and the jaw is heavy;
     - a pale fleck sits at the mouth's corner;
     - the eyes are plain;
     - the fire paints an orange smear down her shadow side, and the portrait key light is weak;
     - her hair starts far back on her head, so she reads bald-browed, with a ragged edge.
3. **Vixen and sunborn are repainted** on the v3 head (`paint_presets.py`), and the head is rebuilt to lay them.
   - Sunborn's old paint, on v3's shape, showed a pale band down her forehead.
   - The side-by-side is below ("The side-by-side").
4. **Play-zoom shots reviewed** (`scratchpad/face2/arenaF.jpg`).
   - At 22 to 31 m and a 64° pitch, her face is foreshortened and mostly hidden under the crown of her hair.
   - In three of the four shots she faces away (an idle auto run), so the `far_*` tuning can't be judged from them.
   - Retake them with her facing the camera: walk her toward the bottom of the screen, or turn her.
5. **Neck strands:** not re-checked beyond the Look close-ups, where none show. The predecessor's fix (hair kept 1.6 cm off her neck) is in the built hair. Check it turning, with `long` hair, at the Look's Hair part (`--step 1 --part 0`).
6. **A new direction, MoGe-2: tried, not yet good enough.**
   - **What it is:** MoGe-2 (MIT, in our ComfyUI, `moge_2_vitl_normal_fp16`) reads a portrait's surface: a 3D point per pixel, plus normals.
   - **Its normals are excellent:** lid folds, the lips' volume, nose, cheekbones and chin all come out clean (`scratchpad/face3/ref_h11/moge/moge_normal_00001_.png`).
   - **The tools:**
     - `tools/assets/face_moge.py` runs MoGe on a picture.
     - `tools/assets/face_warp.py` lays her MakeHuman face on the result and writes a MakeHuman target. Its docstring says what fails.
   - **Results** (on `heroine_11`, check sheets `scratchpad/face3/ref_h11/chk*.jpg`):
     - **across** (landmarks), the warp works but leaves a ridge along her jaw, because the skin under the jaw doesn't follow;
     - **in depth**, MoGe's points are flatter than its normals, and laid on her they made a flat mask.
   - **Why bother:** a landmark warp alone moves her only 1 to 3 mm, because the predecessor's fit already matched her outline. What's wrong is the volumes, which only the surface carries.
7. **New front references for her default face** are in `scratchpad/face3/refs_her/her_{11,23,37,41}.png`:
   - 1024×1536, face large in the frame, made by `scratchpad/face3/refs_front.py` (fuller lips, defined lid crease, lash line);
   - **`her_23` is the best.**

## The side-by-side (sent to the main session)
`scratchpad/face3/sbs_v3.jpg` shows the default, vixen and sunborn, each reference beside its Look close-up in game (ponytail, v3, presets repainted). **None is near its reference.**
- The fire's orange lies in a slab down her shadow side, and the rest of her face falls off into the dark.
- She is seen a little from below, turned. Her hair starts high, over a big bare brow.
- All three are one face shape under three paints: a heavy jaw, gaunt cheeks, small lips. Vixen's eyes stare.
- Sunborn's face paint is lighter at its edges than her "deep" skin round it.

## Next (exact)
1. **Wait for the main session's answer** to the side-by-side (sent). To remake the sheet after any change:
   - shoot each face:
     - `scratchpad/face2/shot.ps1 sbs_default 8 --new --sex female --step 1 --part 1 --hair ponytail`;
     - the same with `--preset vixen --skin rose --eyes flint`;
     - the same with `--preset sunborn --skin deep --eyes sloe`;
   - make the sheet with `scratchpad/face3/sbs.py out.jpg 460 "label=img:x0,y0,x1,y1" ...`. The references are the left halves, `0,0,0.5,0.75`; the game crop is `0.36,0.1,0.7,0.8`.
2. **Fix the Look close-up's light first, with UI design** (`GameFront.UpdateCreate`; it's their file):
   - a soft frontal fill at face zoom;
   - less of the fire on her face.

   Every face judgement depends on it.
3. **Her face from her reference's surface:** make `face_warp.py` good, then build her with it.
   - **Depth from MoGe's normals:** integrate them over the face into a height field (Frankot-Chellappa, or a Poisson solve), with MoGe's depth only for the broad shape. Then use that, not the point map, in stage 2b.
   - **The jaw's underside and the submandibular skin** must follow the jaw line in stage 2a. Today it's held by the neck rule, and leaves a ridge.
   - **Try it on `her_23`** (front, large): `face_moge.py`, then `face_fit.py marks`, then `face_warp.py --check`. Judge in clay at 0, 35 and 80 degrees against MoGe's own surface, which the check renders as `w2_*`.
   - **Into the head:**
     - add `portrait-heroine` to FACE;
     - teach `fs.target_paths()` and `heroine_head.py`'s TARGET about `tools/assets/heroine_face/targets/`;
     - `face_lab.py` and `face_warp.py` already skip `portrait-*`.
   - **Paint her by projecting the reference itself:** its geometry now matches. Delight it with MoGe's normals: fit spherical-harmonic light to its skin, then divide. Fill the sides from the 3/4 view or from Krea as now.
   - **Then the presets:** each from its own front reference, as a shape key of its own (`face_<id>`). `People.HerHeadPaint` sets the key with the paint. Sliders stay on top.
4. **Hairline:** bring her hair's front edge down and make it denser. Today she reads as having a receding hairline at the close-up. See `face_shapes.HAIRLINE` (0.080 above her eyes at the front) and `heroine_hair.py`'s `hairline_hairs` and the roots' thinning.
5. **Play zoom:** retake the arena shots with her facing the camera, then tune `far_from`, `far_to` and `far_dark` (`People.Skin`).
6. **When the head is final:**
   - commit the art;
   - message the main session (`heroine_outfits.py --body` on this worktree's `tools/comfy/out/heroes/heroine_built.blend`);
   - tell UI design to rerun `heroine_paint.py` and `creation_portraits.py`;
   - tell the male hero lead the final slider set.

## Decisions (and why)
- **Presets carry their own painting.** Slider differences can't make them distinct; the landmark fit gave near-identical faces.
- **Faces are judged in game,** at the Look close-up with hair, and in clay for shape. Lab renders flatter nothing.
- **Neck by bones** (`HerPose.NeckWidth`/`NeckLength`), so collars follow.
- **One hairline for hair and paint** (`face_shapes.HAIRLINE`).
- **Head smoothing is linear** (through SUB), so every shape key still agrees with it.
- **No art committed until it's beautiful.**

## Failures and why
- **FACE v1 to v3:** MakeHuman's targets move broad regions. They can't give full lips with a defined border, almond eyes with a fold, and soft full cheeks at once.
- **Landmark fit and warp:** the predecessor's fit already matched her outline to within 1 to 3 mm, so moving outlines alone changes little.
- **face_lab's anchors:** a landmark on the rim of an opening (lids, lips), or on the face's outline, was anchored where the camera's ray went on through. That put it inside the eye socket, the mouth or the neck, up to 3 cm deep. `face_warp.py` moves such anchors to her visible surface, and the jaw outline to her surface's edge. `face_fit.py`'s two-view fit still uses the raw anchors, so its depths were wrong.
- **MoGe's depth used as is:** flatter and stripier than its normals. See above.

## Gotchas
- **The Look is creation's step 1 now.** The shot flags are `--step 1 --part N`: 0 Hair, 1 Face, 2 Shape, 3 Paint, 4 Body. The predecessor's `--step 3 --part 2` now gives a full-body shot of another step.
- **The scratch scripts in `scratchpad/face2/`** (`shot.ps1`, `finish.ps1`, `rebuild.ps1`, `chain_face.ps1`, `paint_seeds.ps1`, `paint_presets.py`, `fs.ps1` and others) point at **my** worktree. Repoint them: replace `agent-a6784044c82f101d9`. My own scratch is `scratchpad/face3/`.
- **The Bash sandbox** refuses commands it can't prove aren't git, such as variables in paths or `cd` elsewhere. Use PowerShell, or plain paths.
- **Files written by PowerShell's `WriteAllLines` get CRLF** endings. The Edit tool then fails on multi-line matches made by `.Replace` with `` `n ``.
- **The disk is nearly full at times** (it fell to 7 GB). Keep big files out of scratch, and don't copy `.godot` caches needlessly.
- **MoGe's GLB, once imported into Blender:** x right, y depth (away from the camera), z up. Each vertex's UV is its pixel: u = x/W, v = 1 − y/H. The face sits a couple of "metres" away at a large scale; `face_warp.py` places it.
- **`godot/art/people/heroine.glb`** is git's. The head build writes its own; restore it with `git checkout` before committing.
- **A Godot import rewrites some tracked `.import` files.** Check out those under `paint/` before merging.
- **A test sometimes fails under CPU load** (a timing test). It passes when rerun.
- **The temple's white band in FaceSheet** is its back light (`LIGHTS=b`), not a crease.
- **Krea sometimes paints swept-back hair** on her bald head in side views. That's why paint above the hairline fades out.
- **`heroine_head.py` reuses `r_` and `c_` later.** Keep using `HEAD_R` and `HEAD_C` in `head_paint`.
- **ComfyUI is shared.** Free it with `POST /free` only when the job running is not someone else's.

## Art on disk, not committed (this worktree)
- `godot/art/people/head_tex/`:
  - `heroine_head.jpg`, `heroine_graft.jpg` (FACE v3, paint `paintD_s11`);
  - `heroine_features.png` and its `.import`;
  - `heroine_head_vixen.jpg` and `heroine_head_sunborn.jpg` (repainted on v3);
  - `eyebrow010.png`.
- `godot/art/people/heroine_hair_*` (all 5 styles, built on v3).
- `tools/assets/heroine_face/`: `face_paint.png` (v3), `face_paint_vixen.png` and `face_paint_sunborn.png`.
- `tools/comfy/out/heroes/` (gitignored):
  - `heroine_body.blend` (the head build's input);
  - `heroine_built.blend` (v3, with hair);
  - `heroine_unpainted.blend` (v3);
  - `heroine_built_before.blend` (the old shared one).

  **A successor in a new worktree must copy this folder, never move it.** Also copy the art above, `godot/.godot` (the import cache, 2 GB; robocopy works), and make `godot/assets` a junction to `public/assets` (`git update-index --skip-worktree godot/assets`).

## Done (pushed)
- **This session:** `tools/assets/face_moge.py`, `tools/assets/face_warp.py` (experimental), and these docs.
- **The predecessor's work** (all pushed):
  - sliders wired into the head (47 in 8 groups; `looks.json` by `face_looks.py`);
  - the neck by bones;
  - the face painting (`heroine_face.py`);
  - a real hairline with baby hairs, and neck clearance;
  - the far-zoom feature mask (`heroine_features.py`, `heroine_skin.gdshader`);
  - the art-directed presets (`presets.json`);
  - the creation shot flags (`--face`, `--preset`, `--hair`, `--skin`, `--eyes`).

## Collaborators
- **Main session:** outfits (`heroine_outfits.py --body`), merging.
- **UI design** (a26f87c39952dcd9c on the roster):
  - the Look's parts;
  - preset `skin` and `eyes`;
  - brows dyed from the paint;
  - `creation_portraits.py`;
  - the Look close-up's camera and light (`GameFront.UpdateCreate`).
- **Male hero** (ab82cbe99e2937ddd): imports `face_shapes` (SLIDERS, REACH, slider_keys). Its MACROS and FACE are hers.

## Files to read first
- `tools/assets/face_warp.py` and `tools/assets/face_moge.py` (the new direction)
- `tools/assets/face_shapes.py`, `tools/assets/heroine_face/presets.json`
- `tools/assets/heroine_head.py`: FACE loading, `subdivide`, `head_paint`, the shapes section
- `tools/assets/heroine_face.py` (painting), `tools/assets/face_lab.py` (anchors)
- `godot/src/Actors/People.cs`: `HerFace`, `HerHeadPaint`, `Skin`; `godot/src/Game/GameFront.cs` `UpdateCreate`
- Scratch:
  - `scratchpad/face3/` (mine): `refs_her/`, `ref_h11/` (MoGe and warp checks), `sbs.py`, `refs_front.py`, `lookD.jpg`;
  - `scratchpad/face2/` (the scripts).

HANDOFF READY: docs/handoff/face.md on worktree-agent-a6784044c82f101d9@330c0304 (this line added after)
