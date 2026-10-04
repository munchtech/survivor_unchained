# Handoff: the heroine's face, hair and character creation's Look

From agent abfa9bb430ec2391e, at about 440k tokens, to a fresh successor. Read `docs/team/README.md` first, then this page, then `docs/team/face.md` (status) and `docs/FACE_RESEARCH.md` (the science).

## The owner's words (2026-10-04, after trying the Look step)
- "weird hair strands in her neck"
- "all of the pre made faces are kinda ugly"
- "some things not editable like forehead etc."
- "i managed to get one kind of pretty but chin can't get any narrower etc"
- "look up beauty science and proportions and fix that stuff"
- "the customizations don't do enough to change"
- Their screenshot shows a harsh, ragged hairline across her forehead.
- Added later: "for premade faces generate beautiful ones with our local ai hookup if possible".

The coordinator's notes on the AI faces:
- Generate front and three-quarter references with the local ComfyUI.
- Fit her shape keys to each, by eye or by landmarks.
- Paint each preset's skin from the same image, as her face paint was made.
- Keep them tasteful and varied across ethnicities, and judge at full resolution.
- Free ComfyUI's models after each batch.

## The full brief
1. **Research** facial attractiveness and write `docs/FACE_RESEARCH.md` with sources. **Done.**
2. **Controls that do enough and cover everything:**
   - forehead height and slope, temples, brow ridge;
   - cheekbone height, width and prominence, cheek fullness;
   - jaw width and angle; chin width, length and projection (much narrower possible);
   - nose bridge, width, tip and length; lips separately; mouth width;
   - eye size, spacing, tilt and depth; ear shape; neck length and width.

   Use MakeHuman targets where they exist and procedural Blender sculpts where they don't. Each range should be wide enough to matter but tasteful, capped only where she truly breaks. Check both ends and the middle in renders.
3. **8 to 10 presets,** each genuinely beautiful and distinct (ethnicities, bone structures), judged at full resolution. She must look stunning by default.
4. **Hair:**
   - fix the stray strands at her neck in every style;
   - a soft, natural hairline (density and alpha falloff, baby hairs, no ragged cut).
5. **In the game:** check creation at 1920x1080. Tell the owner to run a fresh build to see new C#: open the project in the Godot editor and press Play, or `dotnet build godot/SurvivorUnchained.csproj`.

**Coordination:**
- **UI design** owns creation's layout. Its lead is retired, so you may adjust Front.cs and CreateLook.cs's Look step for new controls, keeping its design.
- **The main session** owns `heroine_outfits.py`; don't change it. Tell the main session when head or neck changes affect outfits (the arcanist's collar and choker).
- **The male hero lead** (ae2de192cce8298ca) reuses her slider set; tell it what you add.

**Rules:**
- The GPU is shared: wait for an empty ComfyUI queue and free its models after.
- The drive is tight: write nothing large and clean scratch.
- Keep tests green, use British spelling, commit and push at milestones with render sheets.

## Done (branch `worktree-agent-abfa9bb430ec2391e`, pushed)
- **`docs/FACE_RESEARCH.md`** covers:
  - averageness, symmetry and feminine cues (Cunningham 1986);
  - the 36% and 46% ratios (Pallett 2010);
  - lips 1:1.6 to 1:2;
  - canthal tilt;
  - thirds and fifths, and the golden-ratio myth (Holland 2008);
  - BG3, Cyberpunk 2077, Black Desert, Elden Ring and Dragon's Dogma 2 compared;
  - the preset method.
- **`tools/assets/face_shapes.py`:** her face as plain data.
  - MACROS, PARTS, FACE and BUILD, copied from heroine_head.py, which does not read them yet.
  - `FIT_TARGETS`: 122 MakeHuman targets.
  - **`SLIDERS`:** 47 sliders in 8 groups (Head, Eyes, Nose, Cheeks, Mouth, Jaw, Ears, Neck), each with a "+" and "-" target set.
  - **`REACH`:** how far each key goes, calibrated from renders at ±1 and ±2 (`docs/team/face_sheets/cal_*.jpg`). Ears and neck are not yet checked.
  - `SCULPT_WANTED`: where MakeHuman falls short.
  - `SCULPTS["sculpt-chin-narrow"]`: a smooth field that narrows the chin to a soft V with no crease. It is good at 1.5 (`face_sheets/chin_sculpt.jpg`) and is used by the `chin_width` slider's "-" side. This answers the chin complaint.
  - `anatomy(P)` finds the nose tip, chin point and mouth height from the points.
- **`tools/assets/face_refs.py`:** local Krea 2 turbo paints reference portraits, front and three-quarter side by side, beauty-campaign framing, four seeds. It frees the GPU after. Only `FACES["heroine"]` exists; its four seeds are all stunning (`face_sheets/refs_heroine.jpg`).
- **`tools/assets/face_lab.py`** (Blender) builds MakeHuman's woman with any target weights (and sculpts). It has two modes:
  - `render` writes views at any angles plus a `_cams.json`;
  - `anchor` ray-casts MediaPipe landmarks from a render onto her mesh, storing each landmark's surface point and every target's move of it.
- **`tools/assets/face_fit.py`** runs in its own venv, `%LOCALAPPDATA%\facefit\.venv` (Python 3.11, mediapipe 0.10+, scipy, pillow); the model is at `%LOCALAPPDATA%\facefit\models\face_landmarker.task`.
  - `marks` reads landmarks.
  - `fit` takes anchor sets by commas: the front set first, then sets at other turns, which the three-quarter view is matched to. It fits bounded least squares, in picture x and y only, with each view's pose solved.
  - `--hold depth,forward,backward,prognathism,prominent,push` keeps the depth targets at zero. The two views can't judge depth, and unheld they gave her a Pinocchio nose in profile.
  - Self-test error: 0.1 to 0.35 mm. Against the heroine references: about 1 mm front and 1.4 mm at three-quarter.
- **`tools/assets/heroine_face/fit_heroine_candidate.json`:** the candidate new default face. It is the average of the four held fits plus research tweaks (fuller lips with the lower fuller, a finer tip, a slight eye lift, a slimmer lower face). It applies over MakeHuman's bare woman, *replacing* FACE. See `face_sheets/candidate_face.jpg`: oval, slimmer, better proportioned than the old face. The profile chin is still a little soft.
- **Sheets:** `docs/team/face_sheets/` (refs, fit against refs, candidate, chin sculpt, calibration).

## Not done (in order)
1. **The default face.**
   - Judge the candidate against the reference; nudge the chin projection and jaw-to-neck line in profile by hand.
   - Better: add a profile view to `face_refs.py`'s frame (three panels: front, three-quarter, profile) and anchor a set at 90° so the fit sees depth.
   - Then put it into `face_shapes.FACE`. Mind that the fit is over the *bare* woman, with `"-": true` in lab files.
   - Make heroine_head.py import face_shapes (MACROS, FACE, BUILD, PARTS, SLIDERS) instead of its own copies.
2. **Remaining sculpts** (`SCULPT_WANTED`):
   - brow ridge: MakeHuman's moves the brows off her face;
   - eye depth: push1 barely shows;
   - eyes following `head-scale-horiz`: add it to heroine_head.py's EYE_FOLLOW.

   Check ears and neck renders and set their REACH.
3. **heroine_head.py with the new sliders.**
   - Build each key from `slider_keys(name)`.
   - Sculpts: compute the delta on MakeHuman's points in its own world (the lab's frame), then through `_to_world` and `SUB` as targets go.
   - **Neck keys** belong on her body, below SPLIT. The head's `_hold` zeroes them at SPLIT. Make neck width a shared smooth field over head and body (shared points get the same move). Make neck length a Head-bone offset in `HerPose` (a SkeletonModifier3D), which avoids skew.
   - Then the rebuild chain, in order:
     1. `heroine_head.py`, which writes `heroine_built.blend`. That file lives in the main checkout's `tools/comfy/out/heroes/`, a shared path outside git; back it up first.
     2. `heroine_face.py` (Krea repaint of her face, which must match the new shape). Consider a better prompt: the refs' beauty framing.
     3. heroine_face_fixes (run inside the head build).
     4. `heroine_hair.py` (all 5 styles).
     5. `heroine_paint.py`.
     6. **The main session** runs `heroine_outfits.py --body godot/art/people/heroine.glb`. That run is what writes heroine.glb; tell them. Her neck is slimmer, so the collar and choker need refitting.
4. **Hair follows the head:** the hair cards need the same shape keys as the head where it moves her scalp (forehead, temples, face width). Use the nearest scalp point's delta per card point, in heroine_hair.py. `People.HerFace` already sets keys on every mesh that has them.
5. **Neck strands:** in Blender at rest no strand passes through her neck (all 5 styles; scratch `face/hair/_s.jpg`). So it is likely at run time:
   - `heroine_hair.py rig()` eases weights from Head to her body over 6 cm below her jaw, so as her head turns the strands near her neck stretch through it;
   - or the HairSway or chain swings them in.

   Reproduce it in Godot with FaceSheet: `CAM=head`, `YAW=90/180`, `CLIP` at several seek times, and the Hair section's turn of -0.95 rad. Then fix it, for example by keeping cards rooted on the head Head-weighted to their tips, or by pushing strands out of a neck capsule in the shader.
6. **Hairline:** the owner saw a ragged, harsh line. Today: `hairline_z` is a fixed curve; `hairline_hairs` are short cards, alpha-tested; `cap()` fades over 1.6 cm. Make it:
   - an irregular, natural hairline, with a widow's-peak option and soft temples;
   - a density falloff, with fine baby-hair cards at 30 to 50% opacity (the shader uses alpha hash);
   - the cap's fade longer and noisier.

   Check every style at full resolution.
7. **Presets (8 to 10):**
   - Add to `face_refs.FACES` with distinct ethnicities and bone structures, for example: the heroine (Celtic, freckled); Nordic; Mediterranean; East Asian; South Asian; West African; Afro-Caribbean; Latina; Slavic; fey (high cheekbones, pointed ears).
   - Paint them, pick a seed, anchor, then fit (with `--hold`).
   - **Map the fit to sliders:** a least-squares fit from target weights to `slider_keys` combinations, or fit directly with the slider keys as the "targets" (`face_lab` anchors any target list, including sculpt names).
   - Write them to `godot/data/content/looks.json` `heroes.female.faces`. Its sliders have id, name, group, low, high, min and max. Replace the old 25 with the new set.
   - The coordinator suggests painting each preset's skin from its reference. That needs a per-preset face texture: think about cost. A tone-and-freckles parameter on the skin shader may be enough.
8. **Game side:**
   - `People.HerSliders` (People.cs about line 337) lists slider ids; it must match the head's keys.
   - CreateLook.cs `HeroFace` groups the sliders by `Group`. With 8 groups, make sure the group segments fit: a second row, or a scroll.
   - FaceSheet (`godot/tools_scenes/FaceSheet.cs`, run via `face_sheet.gd` with `SHEET`, `OUT`, `CAM`, `YAW`) renders every slider at its ends and middle.
   - Tests: `dotnet test` in `godot/tests`.
   - Check creation at 1920x1080 (`--new --step 3 --part N`; see `docs/team/ui_design.md`).
   - Tell the male hero lead the final slider ids.

## Decisions (and why)
- **Presets come from AI references fitted by landmarks:** the owner asked for it, and it matches the BG3 and Dragon's Dogma lesson (a curated, real-looking base).
- **One data module** (`face_shapes.py`) is shared by the build, the lab and the fit, so they can't drift.
- **Reach is calibrated per side** (`REACH`). The UI's min/max become plain ±1, so the whole slider is useful and no hand-capped stubs remain.
- **Sculpts replace MakeHuman targets that crease** (`chin-triangle`, and `chin-width-decr` past about 1).

## Failures and why
- **The first fit gave nonsense weights,** for three reasons:
  1. Lab `positions()` evaluated with the helper-mask modifier on, so the vertex numbering was wrong.
  2. The camera matrix was read before `view_layer.update()`, so it was stale.
  3. MediaPipe's depth was mixed in, but it is on a different scale.

  All are fixed. Pose is also solved about the face's centroid.
- **A three-quarter view fitted against front anchors gave about 4 mm error.** The landmarks slide along the cheek outline, so it now uses matched-turn anchor sets.
- **Unheld depth targets** pushed the nose out (`nose-scale-depth` at 0.6), so they are held.

## Gotchas
- **This worktree's Bash** refuses commands that use shell variables, `xargs`, `cd ..` or heredocs feeding Python. Use PowerShell with `$vars`, or plain commands with literal paths.
- **Blender:** `C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe`.
  - MPFB assets: `%APPDATA%\Blender Foundation\Blender\4.5\extensions\.user\user_default\mpfb\data`.
  - Targets: `...\extensions\user_default\mpfb\data\targets`.
- **The lab's eye, brow and lash proxies don't follow targets.** Judge eye sliders by the skin; heroine_head.py's `eye_follow` handles the real eyes.
- **ComfyUI** (127.0.0.1:8188):
  - `/free` answers with an empty body; `comfy.post` chokes on it, so `face_refs.free()` posts directly.
  - The queue was empty when I used it, and I freed it after each batch.
  - Run it with `python tools/assets/face_refs.py <out> [names]`.
- **This worktree has no `godot/.godot` import cache.** The first Godot run imports about 2,900 files (slow, and it uses disk). The retired UI lead's worktree has a cache.
- **heroine.glb** in git comes from the outfits `--body` export, not from heroine_head.py's own export, which lacks the outfit-hiding vertex colours.

## Collaborators
- **Main session:** outfits, the roster, merging.
- **Male hero lead** (ae2de192cce8298ca): reuses the slider set.
- **UI design:** retired; its notes are in `docs/team/ui_design.md` and `docs/handoff/ui_design.md`.
- **UI art** (a72467cac33063d3a): cameo portraits for faces and cuts; tell it when the presets change.

## Files to read first
- `docs/FACE_RESEARCH.md`
- `docs/team/face.md`
- `tools/assets/face_shapes.py`
- `tools/assets/heroine_head.py`, especially:
  - `FACE`/`SLIDERS` (lines 60 to 90);
  - `fit` (about 432);
  - the shapes section (about 1250 to 1330: `base_delta`, `eye_follow`, `_hold`).
- `tools/assets/heroine_hair.py`: `hairline_z`, `roots`, `hairline_hairs`, `cap`, `rig`.
- `godot/src/Actors/People.cs`: `HerFace`, `HerHair`, `HerSliders`.
- `godot/src/Ui/CreateLook.cs`: `HeroFace`, `SliderRow`.
- `godot/data/content/looks.json`
- Scratch, `%TEMP%\claude\...\scratchpad\face\`:
  - `refs/`, `lab/` (renders, anchors `an_bare/a_*.npz`, fits);
  - helpers: `anchor.ps1` (render, landmarks, anchors at several turns), `calib.py` and `calsheet.py` (slider calibration), `sheet.py`, `compare.py`, `combine.py`, `variants.py`, `hairlook.py`.
