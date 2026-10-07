# Heroine face, hair and creation's Look: status

Agent aed215ba3ca60cc29 (v12; took over from a43570e07edbe40b2 at v11), branch `worktree-agent-aed215ba3ca60cc29`.
The handoff it started from is `docs/handoff/face.md`.

## Current state (2026-10-06)
- **v12, her skin (committed):**
  - **No speckle over her breasts** (the owner's note, 6 October). The face-grain tile (93f66173) was laid at 3x over her whole body; it is now only up her neck (the freckle maps' blue), its dark outliers eased; the graft's freckles stop at her collarbones in front. Her bust at the Look: 0.26 specks per 1000 px to 0.06, the floor (`face_sheets/v12_breast_speckle.jpg`).
  - **Her paint no longer smeared at the close-up:** her skin's scattering 0.38 to 0.1. Godot's screen-space SSS spreads the lit colour with her paint in it. Grain at the Look (s0.8 / 1.6 / 3.2 of her portrait's) 0.62 / 0.79 / 0.91 to 0.74 / 0.92 / 0.99; Doe's brows' darkness 0.30 to 0.20 (portrait 0.18).
  - Mipmaps on the textures loaded from code (the presets' head paints, freckles, grain, AO, scalp).
- **Short of the bar, found this round (worst first):**
  1. **Every face's brows sit 22 to 37% too near its eyes** (in eye widths): the warp squashed each portrait's eye region onto the clay's narrower eyes. Fix written in `heroine_face.py` (brows pinned to the portrait's place over each eye; the laying's colour match made a linear tint; the front's features laid from it alone: brows +20% darker). Needs all ten paints re-laid (Krea detail pass) and laid onto the head paints without a rebuild.
  2. **The eyes stare and read as a render:** the iris fully uncovered (a resting lid per face: Highborn about 0.18), irises 4 to 8% small and too contrasty, the lashes MakeHuman's black spiky band (and a faded rectangle in their paint).
  3. **Upper lips 13 to 37% thinner than the portraits'** on most faces, in the sculpt itself (the clays). Sliders don't fill (lips_upper pouts). A sculpt per face: **a refit**, gathered with anything else of the head's.
  4. AgX (the world's tone curve) pales her lips and lifts her darks unshaded; under the white rig her lips are close. Secondary.
  5. Her neck's grain is half her portrait's neck's (0.0049 at s0.8 against 0.0094); the tile is clean now, so it can rise without speckle. The book by day; the jaw-edge spots.

## Key decisions (why)
- **Scatter 0.1, hers only** (`People.HerScatter`): 0.2 smears as 0.38 does; at 0.1 the detail stays and the light's edge is still soft (the shader's own terminator). The hero shares the shader; his lead may want the same.
- **Grain up her neck only, by the freckle maps' blue** (`heroine_freckles.py`): no new texture, no mesh change, no seam (the blue carried past the UV islands).
- **No freckles on the front of her chest:** sun freckles thin down the chest; over her breasts they read as specks.
- **Brow position by the paint, not the brows_height slider:** at 1.0 the slider moves the gap 0.52 to 0.60 (portrait 0.77) and looks surprised.
- Dev switches for pictures: `--zoom Z` (the Look's framing), `--lids X`, `--tonemap linear|agx|...`, `--grade off`.

## Next
Re-lay the ten paints (brows) and lay them on the head paints; the eyes (resting lids, irises, lashes); the lips' sculpt (refit); then the handoff's list; then the paints and sliders pass (freckle control); then hair.

## Notes for other areas
- **Outfits:** her body takes no grain tile now (smooth below her collarbones, around and under garments too); her skin is sharper (scatter 0.1). No mesh or vertex-colour change.
- **Male hero:** the same shader's scatter 0.38 smears his paint at close-ups too.
- **Rendering:** her face's grain numbers are cleanest with `--skinparam scatter=0.1` (now her default).
- **Shots:** an ember from the camp fire can drift in front of her at the Look (a soft orange disc); it's not her skin.
