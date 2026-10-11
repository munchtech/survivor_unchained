# Handoff: the heroine's face, hair and creation's Look

Read `docs/team/README.md` ("Working lean", "Safety"), `RESUME.md`, `OWNER_NOTES.md` (the face's order and bar; "Neck length"), this page, then `docs/team/face.md`. Read by section (grep, then line ranges). Hand off at about 300k.

## Start here (11 Oct, midday; face successor 6 handing off at about 250k; branch `worktree-agent-a2d632df7c7f21ec0`)
Brief (coordinator): the nod check; decide BodyK; re-lay the ears; shoot r5 incl. the neck-length sheet; one max judge; send the judged neck sheet to the main session for the owner (today's length a full option, no helmet model yet, say so). Then: Vixen's and Fey's jaws (about 0.1 too light under any rig: their paint or shape), Sunborn's and Saffron's ears, lids/brows/lashes/catchlights (values below), the chain_haul tuft. Helpers must SendMessage you their results (or run judges in the foreground).
Scratch G = `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18`. Scripts in `tools/scratch/face17` (copies run from G): `look.ps1`, `r5.ps1` (the full batch, 33 shots, ~35 min), `meas.py`, `trims.py` + `apply_trims.py TRIMS.txt` (refit: shoot all ten, trims, apply, rebuild), `sheet3.py TAG OUT`, `jawcrop.py`, `neck_sheet.py TAG OUT`, `notch.py`, `neckprof.py` (L down the neck's middle), `nodcheck.py GLB`, `tuft.sh TAG` (motion-check frames in this worktree; env CLIP, STYLE, VIEWSET, NF, IMPORT=1). Python with mediapipe: `%LOCALAPPDATA%\facefit\.venv\Scripts\python.exe`.
- **Judge j5 (G\j5, verdict in this page):** hair PASS; skin PASS WITH FIXES (a), cheeks PASS (b), lit neck FAIL (c), ears PASS WITH FIXES (d), no new tells (e), neck sheet PASS WITH FIXES (f): not yet sent to the owner.
- **Done (all unjudged until j5):**
  - Nod check: head/graft seam points 0 mm apart at +-30 deg on neck_01/Head/spine_03, every axis (before the weld up to 10 mm). Animation and outfits told.
  - 3068f8c6 BodyK 1; the skin shader's shade tint gated by each lamp's sheen (`shade_by_soft`; the Look's fill 0.1 and bounce 0 are the soft lamps): their light shows her paint's own colour, the key's carries her body tone. Tried and rejected: ndl gate held to down-facing (shade stayed grey, own jaw C .015), each lamp's irradiance (warm, but an orange band along the jaw's edge). `--shade-tint off|ndl|light|soft`, `--shade-gate`, `--shade-down on`, `--body-k`. Trims refitted (r6b). Ears re-laid from `f17\heads_orig` (heroine_ears.py reads BodyK now).
  - 3d059b29 the tuft: her hair's chain weights (second UV's v) reached the shader upside down (Blender's glTF export flips v). The tail never swung; on all fours it ran through her. `uv2flip.py` fixed the five shipped .bin files (they need a reimport); heroine_hair.py writes 1 - weight. HairSway: neck/back balls push the chain out behind her only. The short styles' sway now runs (bob) for the first time.
- **Next, in order:**
  1. **(c) Lit neck too dark on all ten** (own L .73 vs portrait .83; Saffron .64/.73, Doe .67/.75, Hardwon .67/.74, others -.02 to -.06). `neckprof.py`: near the chin ours matches; from 0.5 pupil-chin down the portraits reach .79-.84, ours plateau at .72-.75 (≈25-30% linear). Judge: raise the lit neck's L per face in the key term only (the shade mustn't brighten), chroma untouched; accept neck L / cheek L within .02 of the portrait's ratio. Idea: give HerBodyTone a lightness gain and make the soft-lamp shade tint undo all of b (drop the luminance-keeping normalisation in `light()`), face tone divided to keep the cheek. Mind play (b is on her everywhere: check a play shot). A solver if one try fails.
  2. **(a) Under-jaw shade still grey on fair faces** (chroma/L vs portrait: Moonlit -55%, Vixen -53%, Fey -49%, own -37%, Doe -23%, Wildling -19%; Vixen, Moonlit, Fey also too light, L .49-.52 vs .37-.44); hue 5-7 deg too yellow on own, Doe, Saffron, Wildling, Hardwon; Sunborn +34% (terracotta). Lever: the under-jaw paint (soft lamps show the paint). Targets L/C at h≈51: Vixen .37/.050, Moonlit .44/.059, Fey .38/.046; own C .05. Accept chroma/L within 10%, hue within 3 deg. And a thin orange-pink rim along the jaw's lower edge (Doe, Sunborn, Saffron, Hardwon; was there before): one render with the wrap/SSS tint off; baked → desaturate a 1 cm band; else widen the tint's falloff.
  3. Optional: face chroma -5% on own, Vixen, Moonlit, Fey. A faint light band across the upper neck (Hardwon, Fey, own): feather if it's the paint blend. Orange hairline edge on fair faces.
  4. **(d) Ears:** reshoot t40 with the whole ear and the cheek in front in frame (sheet3.py's crop 80 px further left); Sunborn's ear reads lighter than her cheek, Saffron's slightly.
  5. **(f) Neck sheet**, after 1-2, re-render (r5's neck runs) and fix the sheet: in-play row is from behind (all four alike): one strip saying so plus a play frame facing the camera; a guide line at today's collarbone height (or a portrait column at the same eye-chin size); maybe drop one of -1.5/-2; caption both sides: "by a rough measure today's neck is about a third longer than the ten portraits'; 3 cm shorter matches them". Judge's read: -3 most natural, -2 the compromise, today elegant from the front but stretched in profile; even at -3 a gorget wouldn't take the bust view. Then a judge, then the main session.
  6. Hair watch: vault back_03, the tail horizontal for one frame (snap? add damping). Animation's successor reports tail clipping on get_up/get_up_back/death.
  7. Then the queue: Vixen's and Fey's jaw shade (part of 2), lids/brows/lashes/catchlights (values below).
- **Outfits** (handed off @ 9ab04261) has the pauldron note: polished metal roughness 0.18 blows 5.7% of the Look's lower frame; raise it. The key's sheen stays 0.3.
- Gotchas: `sed -i` strips CRLF from People.cs (BOM + CRLF): edit with the Edit tool or Python bytes. Don't `dotnet build` while a batch runs. The motion check's `MARKS`/`LEGALBARE` frames show her bare: scratch only.

## Earlier start-heres
In this page's history: successor 5 (214249ec: rig, nape weld, trims at 0.5), successor 4 (6fc6b368), n1/n2 (4aa76ffe, 5794c4e3), f6 (a411e6c81f22f5c18's, in 6fc6b368).

## The owner's words
- "we are striving for perfection". The bar: at the Look close-up beside each face's reference, no "this is a render" tell; grain at least 0.9 of the photo's; tones and irises within a few per cent; no seams, bands or blobs; it holds at play distance.
- Order: the face, then the paints and sliders, then hair over many rounds ("way more than 2-3").


## Eyes round-2 judge's values (most applied in 19a239bd and after: check `People.HerEyes`/looks.json before redoing; lashes and catchlight still open)
- iris_r 0.117 (per face if possible: Sunborn 0.108, Moonlit 0.109, Saffron 0.114, Wildling 0.121).
- pupil_dark 0.010, applied after `tint` in the shader (or 0.019 for her painted iris). pupil: own 0.22, Highborn 0.23, Doe 0.25, Sunborn 0.225, Vixen 0.225, Moonlit 0.255, Saffron 0.255, Wildling 0.215, Hard-won 0.23, Fey 0.29.
- Resting lids (with iris_r 0.117): own 0.03, Doe 0.035, Highborn 0.06, Sunborn 0.08; Vixen, Saffron, Wildling, Hard-won -0.05; Moonlit, Fey -0.07 to -0.08 (or the `eyes_open` slider). Lower lid over 0.05 of the iris after that: a sculpt fix for the refit.
- whites: own 1.25, Highborn 0.9, Doe 0.8, Sunborn 0.65, Vixen 0.8, Moonlit 0.85, Saffron 0.85, Wildling 0.75, Hard-won 0.8, Fey 1.0. Add the portraits' gradient (white 1.15-1.3x brighter half a radius below centre, 0.6x at +0.2 R).
- lid shadow: place it at the visible margin (-0.42 to -0.52 R on the defaults), not -0.85. Wet line: at 0.95 once the lower lid is down, plus a 10-15% albedo lift over 0.05 R.
- catchlight: catch_at (-0.15, -0.33), catchlight 0.9; in the shader `ALBEDO *= 1.0 - 0.8 * glint`, emission (0.9, 0.95, 1.08).
- Lashes REDO: the cards are unlit (paint (26,19,15) renders about 0). Light them like lid skin (normals to camera/up, or wrap) or lift the paint to about (60,42,32); target (45,30,24) at the Look; alpha capped 0.85; fan the outer lashes (alpha <= 0.6) instead of the winged wedge. Then write `head_tex/heroine_lashes.png` (the script's default output) and retire `heroine_eyes.lashes()`.


## Gotchas
- The worktree guard refuses computed paths, variables, heredocs and compound commands in Bash: write scripts and call them with literal paths.
- Godot's import rewrites hundreds of `.import` sidecars and adds `.uid`s: never commit them (stage files by name). `godot/assets` is a junction with `--skip-worktree`.
- A fresh worktree needs main's `godot/.godot` (robocopy), `f12\sidecars.py`, and a first `-import` (about 8 minutes).
