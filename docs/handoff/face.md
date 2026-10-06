# Handoff: the heroine's face, hair and creation's Look (for v11)

From agent a7905c3e498df9528 (took over from a2f7b0f1283f6144a at v9b).
Read `docs/team/README.md`, `docs/team/RESUME.md`, `docs/team/OWNER_NOTES.md` (the face's order and bar), then this page, then `docs/team/face.md`.

## The owner's words
- "we are striving for perfection". The bar for "perfect" (OWNER_NOTES, 5 October): at the Look close-up beside each face's reference, no "this is a render" tell; grain at least 0.9 of the photo's; tones and irises within a few per cent; no seams, bands or blobs; it holds at play distance.
- The order: the face first (v10, v11...), then paints and sliders, then hair over many rounds.
- "not seeing any face at long distance is tragic". The book frames her face. At play zoom she always has SOME face.
- Freckles: "none is probably the preferred for most people but they are a fun rarity too"; "some of the presets can have freckles if they go with the reference".

## The brief
- Keep versioning her face until it clears the bar. Report honestly with numbers.
- Any change to her head or body geometry, normals or body paint needs the main session's refit: it runs `heroine_outfits.py --body` on this worktree's `tools/comfy/out/heroes/heroine_built.blend`.
- Paint in `head_tex`, shaders and C# need no refit.
- After a refit, rerun creation's portraits (`portraits.ps1`) and the Look shots on your branch.
- Rules:
  - Krea 2, TRELLIS 2 and MoGe-2 only.
  - Don't edit `heroine_outfits.py`.
  - Never commit `heroine.glb` or the outfits.
  - Don't commit the hair `.bin`/`.gltf` a rebuild re-exports unchanged (churn).
  - Take turns with `tools/turn.py`.
  - Batch your shots.
  - Use British spelling.
  - Run `dotnet test` before every commit.

## Done since v10 (on `worktree-agent-a7905c3e498df9528`)
- **v10** (ba0797b4, refitted and merged at 6e1b272e):
  - the v10 grain laid on all ten faces;
  - her body takes her surface's own smooth normals, not the sculpt's faceted ones (the chest's shards);
  - the graft smoothed down her middle (a crease and a fold under her throat);
  - a skin light() with a soft, warm terminator;
  - the cornea's sky reflection dimmed (`sky_wet`; it made the pupil-sized blob);
  - creation's campfire taken off her face at the close-up (`ZoneView.LightNear`).
- **The book** (4315e41c): Pack, Self and Arts frame her (`Overlay.BookFrame`, 28 deg, 3.9 m, 1.05 m; `--book-frame`). She turns to the camera and lifts her head (HeadTurn). Her face is about 80 px tall at 1080.
- **v10b** (2eb5ff28, merged with the integration branch at bc8d2a38; **needs a refit for the body paint**):
  - skin tones fitted per swatch (`People.HerToneFit`, linear factors, hers only);
  - her hair copper `#7a4824` (`--hair-colour` tries others);
  - her own brows dyed her hair's copper;
  - no sandpaper grain laid into the body and graft paint (`heroine_head.py fill_in`);
  - freckles as a layer: `heroine_freckles.py` writes the maps, the skin shader has `freckle_amount`, `Look.Freckles` sets it, and looks.json `faces[].freckles` holds each face's default (her own 0.3, Hard-won 0.25, Wildling 0.15, Fey 0.1, the rest 0);
  - the portrait key 20 deg toward the camera (`Portraits.cs`, the main session's call).
  - Before and after: `docs/team/face_sheets/v10b_face.jpg` and `v10b_neck_1to1.jpg`.

## Open (worst first)
1. **The v10b refit**, then the creation portraits and Look shots on your branch for the main session (`portraits.ps1`, then `shots_v8.ps1 -tag v11 -nocal` and `shots_white.ps1`). Tell the main session the blend is ready. After merging, a local `build_v9.ps1 -rest` restores your own glb (I discarded my local build to merge).
2. **Tones:** round 2 of `HerToneFit` is applied but not re-measured. Run `shots_white.ps1 -tag X`, then `tone_fit.py X`, and multiply the factors in. Fair faces spread about ±5% (Fey's G 1.08, Vixen's L 0.95). Consider a per-face residual.
3. **Brows:** the copper dye reads better but may be a touch dark and dense beside her_23 (`v10b_face.jpg`). Judge at 1:1 against the portrait; the paint shader's `dye` mix is in `People.HerPaint`.
4. **Neck grain:** the speckle is gone, but her neck now reads smoother than her face (pores only). Match her face's v10 grain so the head/body seam can't be seen: `fair_grain.py` on a neck crop against a face crop.
5. **Freckles:**
   - verify each default against its portrait at 1:1, and at play zoom (do the mips darken her cheeks?);
   - the Look's control is the paints and sliders pass;
   - a face the player builds should start at none (CreateLook's draft has no freckles field yet).
6. **The book by day:** her face reads washed out and pale. Is it the day's exposure on her, or her lamp? Maybe come a little nearer (upper body), or a soft key for the book.
7. **The play-zoom face:** not started.
   - Judge at the game's own camera, day and night: `shots_play.ps1` (the Waystation by day and night, an arena).
   - The Verge's arrival is under trees, and arenas are at night.
   - Levers: `heroine_features.py`, the skin shader's `far_*`, the eye shader's `far_*`.
8. **Hair:** blood-red is fixed. Clumping and contrast are left: the portrait's hair has p90/p10 luminance 6.3, the game's 2.5 (`hair_fit.py`). A small flake on her left upper chest (a sculpt fold) remains.
9. The Look's own light (GameFront.PortraitLight) is unchanged. Ask the main session before changing it.

## Findings that save time
- **The throat "band"** is the portrait key's terminator, not normals: the NormalBuffer is smooth there. Wider Godot SSS (`subsurface_scattering_scale` 0.15 to 0.4) blurred away her grain and barely softened the line.
- **The iris blob** stayed with every light put out: it was the sky's radiance on the cornea. The emission glint (`catchlight`) is the small window.
- **The fire stand-in** never worked before: ZoneView's `lit[]` is false for lights never lit, though they shine.
- **The hair colour's response is non-linear** (about colour^1.4 per channel): fit by trying colours under `--rig-white`, not by one factor.
- **freckle_score.py** counts pores too: every portrait scores about 0.7 per 1000 px, Hard-won 1.3. Judge freckles by eye at 2x.

## Scripts (scratchpad `face7/`; the measures run with `%LOCALAPPDATA%\facefit\.venv\Scripts\python.exe`)
- **Build:**
  - `build_v9.ps1 -rest -tag T`: head, features, hair, teeth, outfits (local), import. About 15 min.
  - `lay_all.ps1`: lays all ten paints again, no GPU.
  - `head_try.ps1 -tag T`: builds the head into the scratchpad, then clay and the crease probe.
  - `freckles.ps1`: the freckle maps.
- **Shots:**
  - `shot.ps1`, `shots_v8.ps1`, `shots_white.ps1`, `shots_book.ps1`, `shots_play.ps1`;
  - `verify_v10b.ps1` (one batch of Look checks);
  - `eye_try*.ps1`, `tone_try.ps1`.
  - `pk.ps1` runs Portraits.cs jobs with LIGHTS, SKIN, DEBUGDRAW and KEYSHADOW. `gclay.ps1` is the game's clay. `band_probe.ps1`, `sss_probe.ps1`, `term_probe.ps1`.
- **Blender clay:** `side2.py` (modes asis, dev, joined, flat, lap, mat; SIDE_VIEW chest, torso, back, under) through `clay_set.ps1`. `crease_probe.py`, `normals_probe.py`, `pairs_probe.py`.
- **Measures:** `fair_grain.py`, `tone_fit.py TAG`, `hair_fit.py`, `freckle_score.py`, `rows.py`, `nbgrad.py`, `crops.py`, `grid6.py`.
- **Repointing** to your own worktree: copy `face7` to `face8`, edit and run `repoint.py`.

## Gotchas
- **The worktree guard:**
  - It refuses compound or complex shell commands and `python -c` with variables.
  - Write a script file, use literal paths, keep one git command per call.
  - Python heredocs sometimes pass.
- **PowerShell:**
  - Variable names ignore case: `$t` overwrote `$T` (the turn.py path) and left a turn held.
  - A single-item `if` result splats as characters: use `[string[]]`.
- **A play shot can hang** (`--cam 12.5` in an arena once). Watch for it and stop that Godot process.
- **`godot/assets`** is a junction to this worktree's `public/assets`, with `--skip-worktree` set.
- **The main session copies the blend to refit.** Your rebuild can overwrite yours afterwards.

## Collaborators
- The main session: reviews, refits and merges.
- The male hero (paused): his skin uses the same shader (`terminator`, the freckle layer at 0) and the eye shader (`sky_wet`).

## Files to read first
- `docs/team/face.md`.
- `godot/src/Actors/People.cs`: `HerTone`, `HerFreckles`, `HerPaint`, `Skin`.
- `godot/shaders/heroine_skin.gdshader`: light(), freckles, `far_*`.
- `godot/shaders/heroine_eye.gdshader`.
- `tools/assets/heroine_head.py`: normals, the middle smoothing, `fill_in`.
- `tools/assets/heroine_freckles.py`.

HANDOFF READY: docs/handoff/face.md on worktree-agent-a7905c3e498df9528@HEAD
