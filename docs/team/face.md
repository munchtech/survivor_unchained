# Heroine face, hair and creation's Look: status

Agent a7905c3e498df9528 (handing off at v10b), branch `worktree-agent-a7905c3e498df9528`.
The handoff for v11 is `docs/handoff/face.md`.

## Current state (2026-10-05)
- **v10b** (this branch, 2eb5ff28; **needs a refit for her body's paint**): her tones fitted per swatch to the portraits (round 2 not yet re-measured); copper hair (#7a4824) and copper brows; the sandpaper speckle gone from her neck and upper chest; freckles as a layer (`freckle_amount`, each face's default from its portrait: her own 0.3, Hard-won 0.25, Wildling 0.15, Fey 0.1, the rest none); the portrait key 20 degrees toward the camera. Before and after: `face_sheets/v10b_face.jpg`, `face_sheets/v10b_neck_1to1.jpg`.
- **v10** (refitted and merged, 6e1b272e): her grain laid on all ten faces; her body's normals her own surface's, her middle smoothed; her skin's terminator soft and warm; her eyes' sky blob gone; the book frames her face.
  - Grain at the Look, beside her portrait (`fair_grain.py`, face 380 px): s0.8 0.64-0.73, s1.6 0.81-0.92, s3.2 0.88-0.97 of the photo's (v9: 0.52 / 0.67 / 0.73). The finest is the TAA's limit.
  - Tones under the white rig (`tone_fit.py v10`): renders 8-15% too red in R against every portrait; Sunborn 1.2x too light and 1.6x too blue. Not yet applied.
  - Proofs: `face_sheets/v10_normals_clay.jpg` (Blender clay, side key, before and after), `face_sheets/v10_normals_game.jpg` (the game's own clay, key alone and all lights).
- **The throat band, found:** two things, neither paint.
  - Her chest's shards were the sculpt's own normals (as AccuRIG wrote them), faceted, 46 degrees off her surface at the 99th percentile. `heroine_head.py` now gives her body her surface's own joined smooth normals (the sculpt's kept only where she folds, 294 corners).
  - The graft (MakeHuman's neck and upper chest, fitted to her sculpt) took the sculpt's crease down her middle and a fold under her throat. Smoothed there (Taubin, 4 cm either side).
  - The dark line itself is the portraits' key's terminator: their short key lights her from 90 degrees to her throat's front, so its edge runs down her middle (the NormalBuffer shows no step there). Godot's scattering is a few pixels at a close-up, so the edge was a hard grey line; `heroine_skin.gdshader` now has its own light() with each channel reaching past the edge (red furthest, `terminator`), Godot's own light elsewhere.
- **The catchlight blob** was her sky's radiance on the sharp cornea, not any light (it stayed with every light on her put out). The eye shader's light() keeps the lights' highlights; the sky's reflection is at `sky_wet` 0.04. The small glint remains. Also fixed: creation's campfire was never taken off her face at the close-up (`ZoneView.LightNear` skipped lights never lit).
- **heroine.glb and the outfits are not committed.** The main session rebuilds them with `heroine_outfits.py --body` from this worktree's `tools/comfy/out/heroes/heroine_built.blend`.

## Key decisions (why)
- **Her body's normals her surface's own** (not the sculpt's): the sculpt's were faceted, the source of the chest's shards.
- **A skin terminator of our own** (not wider screen-space scattering): scattering 0.15 to 0.4 softened the edge little and blurred away her grain.
- **The cornea's sky reflection dimmed, its lights' sheen kept**: the radiance map is coarse and bright; the lights give small crisp windows.
- **The book (Pack, Self, Arts) frames her** from 28 degrees and 3.9 m, her whole figure beside the panel, her head lifted to the camera (HeadTurn) and her body turned to it: her face about 80 px tall at 1080 (from play's view it was the top of her head). `--book-frame P,D,H|off` tries others.
- Earlier decisions stand (in git history of this page): the wrap keeps her inside inside; eyes at least 0.89 of hers; preset skins from their portraits; her hairline blended; shots hold her eyes open; the moon off her face at the close-up; her head's AO baked.

## Next
1. The v10b refit (`heroine_built.blend`), then the creation portraits and Look shots on this branch (`portraits.ps1`).
2. The bar, worst first (detail in the handoff): tones re-measured; the brows' copper judged at 1:1; her neck's grain matched to her face's; freckle defaults checked against each portrait and at play zoom; the book's face washed out by day; her face at play zoom (some face always, day and night); hair clumping and contrast.

## Notes for other areas
- **Everyone taking pictures of her:** shots: `--open-eyes`, `--unshaded`, `--debugdraw`, `--eyeparam`, `--eyecycle`, `--skinparam`, `--rig-white`, `--no-taa`, `--mipbias`, `--book-frame`. Portraits.cs: `SKIN=name=v,...`, `DEBUGDRAW=view`, `LIGHTS=k,f,r`, `KEYSHADOW=0`.
- **Male hero:** the skin shader (shared) has its own light() now (`terminator`, his too); the eye shader's `sky_wet`.
- **UI design (when back):** the book screens now frame her close (`Overlay.BookFrame`, `CameraFrame`); a screen that wants play's view leaves `CameraFrame` null.
