# Heroine face, hair and creation's Look: status

Agent ade92e8285938438f, branch `worktree-agent-ade92e8285938438f` (took over from abfa9bb430ec2391e).
Read first: `docs/handoff/face.md` (the predecessor's handoff) and `docs/FACE_RESEARCH.md` (the science).

## Paused (2026-10-04, the owner needed the machine)
All my Blender and Godot jobs are stopped and ComfyUI is freed. Code, tools and data are pushed.
**Art is not committed** (it is mid-iteration): head textures, hair, `heroine_features.png`, the preset paints and `face_paint.png` stay on disk in this worktree. Rebuild them, don't trust them. `heroine.glb` is restored to git's.

## The owner's asks
- "weird hair strands in her neck"; a ragged hairline;
- "all of the pre made faces are kinda ugly"; "generate beautiful ones with our local ai hookup";
- forehead not editable; "chin can't get any narrower"; "the customizations don't do enough";
- (new) "some sort of semblance of a face should exist at anything other than completely max zoom".

## The coordinator's critique (cmp_k16a.jpg), and where it stands
The critique: the presets came out nearly the same face, with:
- thin, flat lips;
- small plain eyes with no lid crease or lash line;
- an egg-shaped skull and a heavy lower face;
- no brow shape.

A 0.2 slider difference drawn out 1.6 times wasn't enough. The asks, in order:
1. Make the default face clearly beautiful.
2. Judge with hair on, in the game's light, at the Look close-up and at the play zooms.
3. Make each preset its own face.
4. Show the default and two presets, each beside its reference in game, before going wide.

Where each stands:
1. **Default face: in progress, not yet beautiful.**
   - FACE v2 was built and looked at in game. The jaw is now tapered, the cheekbones higher, and the eyes upturned and less staring.
   - Still wrong at the close-up:
     - the mouth bulges (MakeHuman's lip volume pushes the lips forward);
     - a pale rim shows above the upper lip, where the paint and the geometry disagree;
     - the cheeks look hollow;
     - the nose looks long.
   - Measured against the reference (`scratchpad/face2/measure.py`, MediaPipe ratios): most ratios are within 5%. The brows sit 20% too close to the eyes, the lower lip is 29% too full against the upper, and eye-to-mouth is 8% long.
   - **FACE v3 is in `face_shapes.py` but not built.** It raises the brows and the mouth, fills the upper lip, thins the lower, softens the cheeks, and makes the jaw a little less tapered.
   - The head is now smoothed (Catmull-Clark through the SUB operator, but not round the eyes). MakeHuman's facets had lit as lumps and creases.
2. **Judging:** the Look close-up is shot with `--new --sex female --step 3 --part 2 [--face s=v,...] [--preset ID] [--hair ID]`.
3. **Presets are now art-directed** (`tools/assets/heroine_face/presets.json`). Each has:
   - large, distinct slider settings: eye shape, nose, lips, face shape;
   - its own skin and eyes;
   - its own face painting (`heroine_face.py` with FACE_SHAPE and FACE_WHO, painted from its reference's description on her head shaped as it).
   - Vixen and sunborn are painted (`face_paint_<id>.png`, then `heroine_head_<id>.jpg`). The game swaps her head's paint by the chosen face: `CharacterData.FaceShape` → `PersonSpec.FaceShape` → `People.HerHeadPaint`. They are not yet seen in game.
   - Vixen's shape was softened after her painting (she read gaunt and older): repaint her.
4. **Side-by-side: not yet made.**

## Readability at play zoom: in progress
- The camera sits 22 to 31 m away, with a 34° field of view, looking down at 64°. Her head is about 10 px across.
- Built so far:
  - `tools/assets/heroine_features.py` draws her eyes, lash line, brows and lips bold and soft in her head's UVs (`head_tex/heroine_features.png`);
  - `heroine_skin.gdshader` darkens and reddens by that mask the smaller she is on screen (how many paint texels a pixel covers);
  - `heroine_eye.gdshader` turns the white of her eye dark when far.
- Not yet judged. Arena shots at `--cam 12.5/22/27/31` were taken (`godot/.shots/arenaF_c*.png`) but not reviewed.

## Next (exact)
1. `scratchpad/face2/chain_face.ps1 -seeds 11,7 -prefix paintD`: FACE v3, unpainted head, two paintings. Pick the best front.
2. `scratchpad/face2/finish.ps1 -paint paintD_s11` (or s7): head, features, hair, Godot import.
3. Shoot the Look close-up and the measure sheet (`fs.ps1 variants.json`, then `measure.py`). Iterate FACE by sliders (the `--face` flag) until it is clearly beautiful. Fix the lip bulge, perhaps with `mouth-scale-depth-decr` or `lips_forward`.
4. Repaint vixen (`paint_presets.py vixen`) and paint the rest of the presets. Rebuild the head, which lays every `face_paint_<id>.png`. Shoot `--preset vixen --skin rose --eyes flint` and `--preset sunborn --skin deep --eyes sloe`.
5. Send the coordinator the side-by-side (default, vixen, sunborn), each beside its reference in game.
6. Readability: review `arenaF_c*.png`, tune `far_from`, `far_to` and `far_dark`, and check that hair doesn't swallow her face.
7. Then:
   - commit art;
   - message the main session to rerun `heroine_outfits.py --body` on my `tools/comfy/out/heroes/heroine_built.blend`;
   - tell UI design to rerun `heroine_paint.py` and `creation_portraits.py`;
   - tell the male hero lead the final sliders.

## Key decisions
- **Presets carry their own painting**, chosen by `FaceShape`. Slider differences alone can't make them distinct.
- **Neck by bones** (`HerPose.NeckWidth`/`NeckLength`), so collars follow.
- **One hairline** (`face_shapes.HAIRLINE`) for hair and paint. The temples were bald because hair stopped at the old curve and an ear test cut the side of her head.
- **Faces judged in game** (the Look close-up), not in lab renders.
- **The temple band** in FaceSheet is FaceSheet's back light, not a crease; her face is now matte (rough 0.6).

## Done and pushed
- 47 sliders in 8 groups (as UI design asked). Hair carries the head's slider keys.
- A real hairline: round her temples and ears, roots thinning toward it, baby hairs.
- Neck clearance of 1.6 cm; nothing lies on her face.
- The lips fix no longer paints her nostrils red.
- Tools:
  - face_presets.py (fit and presets);
  - face_looks.py (writes looks.json);
  - FaceSheet's REST, PLAIN, HIDE and LIGHTS switches.

## Notes for other areas
- **UI design (a69858664f1d3dd29):**
  - `Front.cs`: `Choice()` passes FaceShape, and LookKey includes it.
  - `GameFront.NewJourney` reads `--face`, `--preset`, `--hair`, `--skin` and `--eyes` for shots.
  - Presets in looks.json carry "skin" and "eyes".
- **Main session:** don't take my art yet. I'll message you when the head is final.
- **Scratch:** `scratchpad/face2/`. The scripts are `chain_face.ps1`, `finish.ps1`, `rebuild.ps1`, `paint_seeds.ps1`, `paint_presets.py`, `fs.ps1`, `shot.ps1`, `measure.py`, `overlay.py`, `face_plus.py`, `hair_dbg.py` and `montage.py`. The data is in `refs/` (the AI references) and `an_her/` (anchors).
