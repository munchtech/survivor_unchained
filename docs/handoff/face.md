# Handoff: the heroine's face, hair and creation's Look

From agent ade92e8285938438f, well past 500k tokens, to a fresh successor.
Read `docs/team/README.md` first, then this page, then `docs/team/face.md` (status) and `docs/FACE_RESEARCH.md` (the science).
Branch `worktree-agent-ade92e8285938438f`. The integration branch is merged in at 45b60cbc.

## The owner's words
- "weird hair strands in her neck"; a harsh, ragged hairline.
- "all of the pre made faces are kinda ugly"; "for premade faces generate beautiful ones with our local ai hookup if possible".
- "some things not editable like forehead etc."; "chin can't get any narrower"; "the customizations don't do enough to change".
- "look up beauty science and proportions and fix that stuff".
- Later: "some sort of semblance of a face should exist at anything other than completely max zoom", meaning the game's own camera range. His screenshot showed her face as a red-orange blur.
- The bar: AAA, "never settle", sex appeal "tho not at the cost of looking bad".

## The brief
1. Wire the sliders into the head build.
2. Fix the neck strands.
3. Make a soft hairline.
4. Make the pre-made faces, each fitted to its own beautiful AI reference.
5. The game side: `looks.json`, `People.HerSliders` and the Look step.
6. Check creation at 1920x1080.

The coordinator added:
- the default face must be clearly beautiful first;
- judge faces in game, with hair, at the Look close-up and at the play zooms;
- every preset its own face;
- a side-by-side before going wide;
- her face must read at play zoom.

## The coordinator's critique of the presets, and where it stands
- **The critique** (on `scratchpad/face2/cmp_k16a.jpg`): all presets came out almost the same face:
  - thin, flat lips;
  - small plain eyes with no lid crease or lash line;
  - a long egg skull and a heavy lower face;
  - no brow shape.

  The fit's 0.2 slider differences drawn out 1.6 times weren't enough, and a two-view landmark fit can't see those features.
- **Where it stands:**
  - The default face is still not clearly beautiful (FACE v3 below).
  - The presets have been changed from fits to art-directed settings: `tools/assets/heroine_face/presets.json`. Each has large distinct sliders, its own skin and eyes, and its own face painting.
  - Two presets are painted (vixen and sunborn). None has been seen in game yet.
  - The side-by-side for the coordinator is **not yet made**.

## The FACE v3 plan (the next step; hold it until the coordinator says the GPU is free)
FACE v3 is in `tools/assets/face_shapes.py` FACE, committed but **not built**.

Its changes from v2 came from a measurement against her reference (`scratchpad/face2/measure.py`, MediaPipe ratios, FACE_RESEARCH.md):
- the brows were 20% too close to the eyes;
- the lower lip was 29% too full against the upper (she should be 1:1.6);
- eye-to-mouth was 8% long.

So v3:
- raises the brows (`eyebrows-trans-up` 1.15) and the mouth;
- fills the upper lip and thins the lower;
- makes the cheeks less hollow;
- tapers the jaw a little less and lengthens the chin;
- trims the eyes slightly.

The head is also smoothed now (Catmull-Clark through `subdivide(..., smooth=)`, but not round the eyes), because MakeHuman's facets lit as lumps and creases.

Steps:
1. `scratchpad/face2/chain_face.ps1 -seeds 11,7 -prefix paintD`. This builds her head unpainted (`HEAD_UNPAINTED=1`), then Krea paints it at two seeds (`paint_seeds.ps1`). Pick the front you like (`painted_front.png`).
2. `scratchpad/face2/finish.ps1 -paint paintD_s11` (or s7). This copies the paint and runs `heroine_head.py`, `heroine_features.py`, `heroine_hair.py` (all 5 styles, saved into the blend) and Godot's `--import`.
3. Judge her at the Look close-up:
   - `scratchpad/face2/shot.ps1 NAME 8 --new --sex female --step 3 --part 2 [--hair ponytail] [--face s=v,...]`, which writes `godot/.shots/NAME.png`;
   - FaceSheet: `fs.ps1 variants.json OUT face 0 1920x1080` with `REST=1`;
   - `measure.py ref.png:left imgs...`.
4. Iterate by sliders with `--face` (no rebuild needed). When it's right, fold it into FACE with `face_plus.py` and rebuild (steps 1 and 2).
5. Still wrong at v2, to fix:
   - the mouth bulges forward: try `lips_forward` -, or `mouth-scale-depth-decr`;
   - a pale rim shows above the upper lip, where paint and geometry disagree after the shape change; v3's repaint should cure it;
   - the nose reads long.
6. Presets:
   - repaint vixen with `scratchpad/face2/paint_presets.py vixen` (her shape was softened after she was painted; she read gaunt and older);
   - paint the rest the same way: `paint_presets.py highborn doe moonlit saffron wildling hardwon fey`. Fey needs her new references first (`face_refs.py OUT fey`, already rewritten: young, fair-haired);
   - rebuild the head, which writes every `head_tex/heroine_head_<id>.jpg`;
   - shoot `--preset vixen --skin rose --eyes flint` and `--preset sunborn --skin deep --eyes sloe`.
7. Make the side-by-side: default, vixen and sunborn, each reference beside its in-game Look close-up. Send it to the coordinator before going wide.
8. Then:
   - commit art;
   - message the main session to run `heroine_outfits.py --body` on this worktree's `tools/comfy/out/heroes/heroine_built.blend`;
   - tell UI design to rerun `heroine_paint.py` and `creation_portraits.py face/hair/paint`;
   - tell the male hero lead (ab82cbe99e2937ddd) the final slider set.

## Play-zoom readability (built; the shots are not yet reviewed)
- The camera:
  - `FollowCamera`: Fov 34, pitch 64°;
  - arena distance 22 to 31 m (`ArenaRun.CameraNear` and `CameraFar`), 12.5 m in talks;
  - no player zoom.

  Her head is about 10 px across.
- Built:
  - `tools/assets/heroine_features.py` draws `head_tex/heroine_features.png` (1K): eyes, lash line and brows in red; lips in green; big and soft so they survive mipmaps.
  - `heroine_skin.gdshader` darkens and reddens by that mask, by screen size (`far_from` 3.5, `far_to` 6, `far_dark` 0.78, `far_lips`).
  - `heroine_eye.gdshader` darkens the white when far.
  - `People.Skin` gives the head the mask, hers only.
- **Not yet judged:** `godot/.shots/arenaF_c12.5.png`, `arenaF_c22.png`, `arenaF_c27.png` and `arenaF_c31.png` (an arena run, `--quick warden --sex female --zone arena --auto idle --cam D`), and the crop sheet `scratchpad/face2/arenaF.jpg`.
- Next: review them. Tune `far_from`, `far_to` and `far_dark` (People.Skin can set them). Check that her hair doesn't swallow her face, and that the warden outfit doesn't either.

## Art on disk, not committed
Kept in this worktree, mid-iteration. It will be rebuilt by the steps above. A backup copy is in `scratchpad/face2/wip_art/`.
- `godot/art/people/head_tex/`:
  - `heroine_head.jpg` and `heroine_graft.jpg` (FACE v2, smoothed, paint `paintC_s11`);
  - `heroine_features.png` and its `.import` (BC, mipmaps; that `.import` is committed);
  - `heroine_head_vixen.jpg` and `heroine_head_sunborn.jpg`.
- `godot/art/people/heroine_hair_*.gltf`, `.bin` and `.chain.json` (all 5 styles, with slider keys).
- `tools/assets/heroine_face/`: `face_paint.png` (v2), `face_paint_vixen.png` and `face_paint_sunborn.png`.
- `tools/comfy/out/heroes/` (gitignored, this worktree only):
  - `heroine_body.blend` (copied from the main checkout: it is the head build's input);
  - `heroine_built.blend` (v2, hair saved);
  - `heroine_unpainted.blend`;
  - `heroine_built_before.blend` (the old shared one, as it was).

  **A successor in a new worktree must copy this folder** (copy, never move). Without it, copy `heroine_body.blend` from the main checkout's `tools/comfy/out/heroes/`.
- `godot/art/people/heroine.glb` is git's. The head build writes its own; restore it with `git checkout` before committing. The main session's `--body` run makes the real one.
- In `godot/`: `assets` is a junction to `public/assets`, hidden with `git update-index --skip-worktree godot/assets`. `godot/.godot` is a copied import cache.

## Done (pushed)
- **Head:**
  - `heroine_head.py` reads `face_shapes.py`: FACE (sculpts allowed), 45 slider keys from `slider_keys` with reach, and sculpts through `base_delta`;
  - the eyes follow for size, spacing, height, depth and face width;
  - every `face_paint_<id>.png` is laid as `heroine_head_<id>.jpg`.
- **Neck:** `neck_width` and `neck_length` move bones (`HerPose.NeckWidth`/`NeckLength`), so collars follow.
- **Face paint** (`heroine_face.py`):
  - the references' beauty prompt;
  - MakeHuman's freckles closed out of the drawing;
  - nothing painted above the hairline;
  - `FACE_LAY_ONLY`, `FACE_SHAPE`, `FACE_WHO` and `FACE_SEED`.
- **Hair** (`heroine_hair.py`):
  - the hairline is `face_shapes.HAIRLINE`: round her temples, in front of and round her ears, slightly uneven; the temples were bald before;
  - her ears are found by their own keys;
  - roots thin out toward the hairline; fine hairs, then faint baby hairs (vertex alpha; `heroine_hair.gdshader` multiplies by `COLOR.a`);
  - the cap fade is 2.5 cm and uneven;
  - hair keeps 1.6 cm clear of her neck (this is the neck strands fix: they lay on her neck and drew into it as she turned);
  - gathered hair goes up round her ears, and no strand runs down over her face;
  - the hair carries her head's slider keys (sparse);
  - the blend is saved without the keys.
- **Fixes:** the lips fix no longer paints near her nostrils.
- **Game:**
  - `People.HerSliders` holds the 47 sliders;
  - `looks.json` is written by `tools/assets/face_looks.py` from `face_shapes.py` and `presets.json`: 8 groups of at most 8, as UI design asked;
  - `FaceShape` is carried from the draft into `CharacterData` and `PersonSpec`, and on to `People.HerHeadPaint`;
  - her face is more matte (rough 0.6).
- **Tools:**
  - `face_presets.py` (fit, presets, lab), `face_looks.py`, `heroine_features.py`;
  - the lab's proxies follow its targets;
  - FaceSheet's `REST`, `PLAIN` (1 grey, 2 normals), `HIDE`, `LIGHTS` and `FSDEBUG`;
  - the creation shot flags `--face`, `--preset`, `--hair`, `--skin` and `--eyes`.

## Decisions (and why)
- **Presets are art-directed with their own paintings.** The landmark fit gave near-identical faces.
- **Faces are judged in game, not in the lab.** Bald MakeHuman lab renders hide nothing and flatter nothing.
- **Neck by bones.** The outfits needn't be refitted.
- **One hairline for hair and paint.**
- **Head smoothing is linear (through SUB),** so every shape key still agrees with it.

## Failures and gotchas
- **The temple's white band in FaceSheet is its back light (`LIGHTS=b`), not a crease.** I proved it with `PLAIN=2` normals and the light switches. Don't chase it in the mesh.
- **Krea sometimes paints swept-back hair on her bald head** in the side views. That is why paint above the hairline is faded out.
- **`heroine_head.py` reuses `r_` and `c_` later.** Keep using `HEAD_R` and `HEAD_C` in `head_paint`.
- **The Bash sandbox** refuses shell variables, heredocs feeding Python and `cd` elsewhere. Use PowerShell, or write scripts to scratch.
- **A Godot import rewrites some tracked `.import` files.** Check out those under `paint/` before merging.
- **A test sometimes fails under CPU load** (a timing test). It passes when rerun.
- **ComfyUI is shared.** Free it with `POST /free` only when the job running is not someone else's.
- **Don't run GPU work** (Godot, Blender, ComfyUI) until the coordinator says the owner is done with it.

## Collaborators
- **Main session:** outfits (`heroine_outfits.py --body`), merging.
- **UI design** (a69858664f1d3dd29):
  - the Look parts are Hair, Face, Shape, Paint and Body;
  - preset `skin` and `eyes` fields;
  - brows dyed from the paint;
  - `creation_portraits.py`.
- **Male hero** (ab82cbe99e2937ddd):
  - imports `face_shapes` (SLIDERS, REACH, slider_keys); its MACROS and FACE are hers;
  - his skin layers (relief, shadow) are off by default for her;
  - the head-only settings in `People.Skin` are hers alone (`who == "heroine"`).

## Files to read first
- `tools/assets/face_shapes.py`
- `tools/assets/heroine_face/presets.json`
- `tools/assets/heroine_head.py`: FACE loading, `subdivide`, `head_paint`, the shapes section
- `tools/assets/heroine_face.py`
- `tools/assets/heroine_hair.py`: `hairline_hairs`, `roots`, `drape`, `follow_head`
- `godot/src/Actors/People.cs`: `HerFace`, `HerRestyle`, `HerHeadPaint`, `Skin`
- `godot/shaders/heroine_skin.gdshader`
- `scratchpad/face2/`: the scripts named above, `refs/` (the AI references; `refs_pick/` the chosen ones), `an_her/` (anchors), `wip_art/`

HANDOFF READY: docs/handoff/face.md on worktree-agent-ade92e8285938438f@<this commit>
