# Heroine face, hair and creation's Look: status

Agent abfa9bb430ec2391e, branch `worktree-agent-abfa9bb430ec2391e`.
Research: `docs/FACE_RESEARCH.md`.

## The owner's asks (2026-10-04)
- "weird hair strands in her neck", and a ragged hairline;
- "all of the pre made faces are kinda ugly"; generate beautiful ones with the local AI;
- forehead and other features not editable; the chin can't get narrower;
- "the customizations don't do enough"; look up beauty science.

## Current state
- **Research written** (`docs/FACE_RESEARCH.md`): averageness, symmetry and feminine cues; the 36% and 46% ratios; thirds, fifths and the golden ratio (myth); five AAA creators compared.
- **Reference faces:** `tools/assets/face_refs.py` paints reference faces with local Krea 2. Each is a beauty portrait, front and three-quarter side by side, at four seeds per face. The heroine's references look stunning (scratch `face/refs/`).
- **Face fitting works.** It has three parts:
  - `tools/assets/face_shapes.py` holds her face data: MACROS, FACE, BUILD, and 122 fit targets.
  - `tools/assets/face_lab.py` (Blender) renders MakeHuman's woman with any weights. It also anchors MediaPipe landmarks on her mesh, with every target's move.
  - `tools/assets/face_fit.py` (its own venv with MediaPipe, `%LOCALAPPDATA%/facefit`) reads the landmarks and fits the weights. The fit is bounded least squares; each view has its own pose and is matched to anchors rendered at a similar turn.
  - Results: a self-test recovers her own face to 0.1 to 0.35 mm. The heroine references fit to about 1 mm (front) and 1.3 to 1.5 mm (three-quarter).
- **Candidate default face:** `tools/assets/heroine_face/fit_heroine_candidate.json`, fitted with the depth targets held (see `face_sheets/candidate_face.jpg`).
- **47 sliders drafted** in `face_shapes.SLIDERS`, in 8 groups. Each side's reach is calibrated from ±1 and ±2 renders (`face_sheets/cal_*.jpg`).
- **Narrow chin done:** `sculpt-chin-narrow` is a smooth V with no crease (`face_sheets/chin_sculpt.jpg`).
- **Not yet in her head:** heroine_head.py still has the old FACE and 25 sliders, and the game is unchanged.
- **Handoff written:** `docs/handoff/face.md`, at about 440k tokens.

## Key decisions
- **Presets come from AI references fitted by landmarks,** not hand-guessed numbers. This is the owner's ask, and the BG3 and Dragon's Dogma lesson.
- **Her face data lives in one plain module** (`face_shapes.py`), shared by the head build, the lab and the fit.
- **The fit uses picture x and y only.** MediaPipe's depth is on another scale. The three-quarter view is matched to anchors seen from near its own turn, because the cheek outline's landmarks slide with the view.

## Next (in order)
1. Fit the new default face to the chosen heroine reference. Judge it beside the reference and hand-tune what the landmarks miss: profile, brow ridge, ears.
2. **New sliders** in `face_shapes.py`, built by heroine_head.py:
   - forehead height and slope, temples, brow ridge;
   - cheekbone height, width and prominence, cheek fullness;
   - jaw width and angle; chin width, length and projection;
   - nose bridge, width, tip and length; lips separately; mouth width;
   - eyes (size, spacing, tilt, depth); ear shape; neck length and width.

   Each key is baked at a tasteful extreme, so the slider's ±1 spans the useful range. Sculpts go in `SCULPTS` where MakeHuman has no target.
3. **Hair:** shape keys on the hair cards following the head (forehead and temples). Fix the neck strands and soften the hairline. Rebuild all five styles.
4. **Rebuild the head:**
   - repaint the face (heroine_face.py);
   - fix the face paint (heroine_face_fixes.py), then rerun heroine_paint.py;
   - outfits `--body` gives heroine.glb (tell the main session).
5. **8 to 10 presets:** a reference per ethnicity and bone structure, fitted, and mapped to sliders in `looks.json`.
6. **Game side:**
   - `People.HerSliders`, the slider groups in `CreateLook`, neck length on `HerPose`;
   - FaceSheet sheets of every slider at both ends and the middle;
   - creation checked at 1920x1080.

## Notes for other areas
- **Main session:** her neck will get slimmer and the head will be rebuilt. Outfits must be rebuilt on the new `heroine_built.blend`; the arcanist's collar and choker sit on her neck. I'll message you when it's ready.
- **Male hero (ae2de192cce8298ca):** the slider set is growing. Field names will follow when they settle.
- **Scratch:** `scratchpad/face/` holds `refs/`, `lab/` and the `anchor.ps1`, `sheet.py`, `compare.py` and `combine.py` helpers.
