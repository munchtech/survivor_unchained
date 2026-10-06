# Handoff: the heroine's face, hair and creation's Look (for v12)

From agent a43570e07edbe40b2 (took over from a7905c3e498df9528 at v10b).
Read `docs/team/README.md`, `docs/team/RESUME.md`, `docs/team/OWNER_NOTES.md` (the face's order and bar), then this page, then `docs/team/face.md`.

## The owner's words
- "we are striving for perfection". The bar: at the Look close-up beside each face's reference, no "this is a render" tell; grain at least 0.9 of the photo's; tones and irises within a few per cent under a white rig; no seams, bands or blobs; it holds at play distance.
- The order: the face first, then paints and sliders, then hair over many rounds.
- "not seeing any face at long distance is tragic": at play zoom she always has SOME face.
- Freckles: "none is probably the preferred for most people but they are a fun rarity too".
- "prioritize finishing this face pass".

## Where v11 stands (worktree-agent-a43570e07edbe40b2, through 93f66173; no refit needed)
Numbers and the open tells are on `docs/team/face.md`; pictures in `docs/team/face_sheets/v11_*`.
- Done: portraits on the v10b refit; tones round 2 plus each face's own tone; irises refitted (all within 5%); her brows; her neck's grain (part of the way); freckle defaults; the book's lamp by day; her face at play zoom.

## Next, worst first
1. **The other faces' brows** read 1.3 to 1.8 times too light against their portraits (`brow_fit.py TAG`). They need masks of their own to deepen and dye. Finding them on the rest head's sheet (`heroine_paint.py`) was noisy: the presets' brows and lid creases sit elsewhere on it. Try the sheet built from each face's own shaped head, or MediaPipe's brows on a UV render.
2. **The finest grain** (s0.8 0.65, s1.6 0.82): TAA's. Try a sharper TAA or a little sharpening at the Look only; ask the rendering lead.
3. **Her neck's grain** is at 0.29 of her face's where the portrait's is 0.45. `--grain` above 3 adds more of her own skin's mottle; check it at 1:1 for blotches.
4. **The lips** read thinner and paler than her portrait's.
5. **The book by day** is still flat (a frontal sun). A soft key only on her (a light cull layer) would model her face.
6. **The chest flake**: on the refitted body, at the Look front and turned 40 degrees, no flake reads at 1:1. Find the predecessor's view of it before changing her sculpt (a sculpt change needs the main session's refit).
7. **The base head paint's spots** at her jaw's edge (her right) read as a blotch cluster: the MakeHuman base under the face paint's edge.
8. Then the paints and sliders pass: the freckle control (CreateLook's draft has no field yet), the paints laid per face (they use her sheet's features on every face).

## Decisions and failures (why)
- Eye swatches are the iris's own colour (`iris_light` 1): v10 dimmed the sky's cornea reflection and every iris went dark. Fitted by `iris_cal.py` (greys under the white rig), then `iris_fit.py` and `eye_refit.py` twice (damped for the dark ones).
- `face_tone` per face (People.HerFaceTone) on the face alone, the features' blue its mask (`heroine_features.py` writes it; `features_blue.py` laid it without Blender).
- Brows: only her own are dyed. Each hair keeps its painted darkness in the dye's hue (`soften` 0.07).
- Play zoom: the features' marks at a capped mip, grown to the pixel, from the book's view outward (`far_from` 4.5, `far_to` 6.5, `far_bold` 3); her head 8 degrees up in play. The hair does not hide her eyes; the steep camera foreshortens her face.
- Failed: mottle from the pores' tile (pale dots like sandpaper; blurred, nothing); per-face brow masks on the rest sheet (they caught lid creases and forehead pores).

## Gotchas
- The worktree guard refuses compound shell commands and computed paths: use literal paths, one command per call, and Write for scripts.
- **Build before every batch** (`dotnet build` in `godot/`): the shots use the last build, and a build during a batch splits it. `looks.json` and shaders are read at each shot's start.
- After a new or changed texture, run `--headless --import`. The first shot after an import sometimes dies with a GPU device-lost in the sky pass; rerun it.
- The import touches many `.import` files and adds `.uid` files: never commit that churn; add files by name.
- `godot/assets` is a junction to this worktree's `public/assets` (made by hand; `--skip-worktree` set).

## Scripts (scratchpad `face8/`; measures with `%LOCALAPPDATA%\facefit\.venv\Scripts\python.exe`)
- Batches: `batch_final.ps1 -tag T` (everything), `batch_faces.ps1` (white rig and Look for all ten), `batch_look.ps1`, `batch_pz.ps1`, `shots_white.ps1`, `portraits.ps1`, `shot.ps1`, `shotr.ps1` (resolution).
- Measures: `tone_fit.py`, `iris_fit.py`, `iris_cal.py`, `eye_refit.py`, `brow_fit.py`, `brow_one.py`, `fair_grain.py`, `neck_grain.py`.
- Views: `sheets.py`, `eyes_sheet.py`, `cheeks_sheet.py`, `zoom.py` (pixels as blocks), `grid4.py`, `crops.py`.
- Repoint to a new worktree: copy to `face9`, edit and run `repoint.py`.

## Collaborators
- The main session: reviews, refits and merges.
- Animation: sign-off on the head carriage in play.
- Male hero (paused): his eyes follow the new calibration.

## Files to read first
`godot/src/Actors/People.cs` (HerToneFit, HerFaceTone, EyeColour, HerPaint, HerBrows, HerGrain, HerFreckles), `godot/shaders/heroine_skin.gdshader`, `heroine_eye.gdshader`, `heroine_paint.gdshader`, `godot/src/Actors/HerCarriage.cs`, `godot/data/content/looks.json` (eyes, faces).

HANDOFF READY: docs/handoff/face.md on worktree-agent-a43570e07edbe40b2@HEAD
