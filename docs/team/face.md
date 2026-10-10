# Heroine face, hair and creation's Look: status

Agent afb7deb41dbb5d904 (took over from a6e8e6d0f539943bb), branch `worktree-agent-afb7deb41dbb5d904`, handing off. The handoff is `docs/handoff/face.md`.

## 10 October 2026: round 2 judged, the fix pass next
- **Hair:** the new strand atlas ships (soft ragged roots, unclipped sides, straight shade; hard lock blocks gone), blended drawing the direction. Round 2 (baby hairs, ragged cap hairline, card tone, strand contrast, skin rim behind only) built and with a judge.
- **Eyes:** the shader takes every judged control (iris contrast, collarette, pupil darkness, whites, lid shadow, wet line, catchlight); round 2's judge reversed round 1's iris size and lids (MediaPipe mismeasures renders) and gave exact per-face values: not yet applied, so nothing merged.
- **Brows:** the pin smoothed and split; Doe's setting chosen (1.0, lower 0.65); three `brow_zone` fixes and a tint fix before the GPU re-lay.
- **Lashes:** the new paint has the ink now, but the cards are unlit: redo.

## Earlier state (2026-10-07)
- **v12 continued (ca7efb10; nothing shipped changes yet):** the brow pin runs and no longer folds the warp (`heroine_face.py` `brow_zone`, `FACE_BROW_PIN` a fraction); a face's paint can be laid on its head without a build (`heroine_face_relay.py`); her lashes painted hair by hair (`heroine_lashes.py`, a trial paint); a resting lid per face (looks.json faces "lid", none set yet). Doe's brows re-laid flat (no Krea) are dark and full like her portrait's. **Not yet seen in the game.**
- **v12, her skin (committed):**
  - **No speckle over her breasts** (the owner's note, 6 October). The face-grain tile (93f66173) was laid at 3x over her whole body; it is now only up her neck (the freckle maps' blue), its dark outliers eased; the graft's freckles stop at her collarbones in front. Her bust at the Look: 0.26 specks per 1000 px to 0.06, the floor (`face_sheets/v12_breast_speckle.jpg`).
  - **Her paint no longer smeared at the close-up:** her skin's scattering 0.38 to 0.1. Godot's screen-space SSS spreads the lit colour with her paint in it. Grain at the Look (s0.8 / 1.6 / 3.2 of her portrait's) 0.62 / 0.79 / 0.91 to 0.74 / 0.92 / 0.99; Doe's brows' darkness 0.30 to 0.20 (portrait 0.18).
  - Mipmaps on the textures loaded from code (the presets' head paints, freckles, grain, AO, scalp).
- **Short of the bar, found this round (worst first):**
  1. **Every face's brows sit 22 to 37% too near its eyes** (in eye widths): the warp squashed each portrait's eye region onto the clay's narrower eyes. Fix in `heroine_face.py`, tried on Doe and Sunborn without Krea: the brows and the landmarks round them pinned toward the portrait's place over each eye (a fraction: the clays' brow ridge may sit low, so 1.0 or about 0.6 is decided in the game next), a linear tint, the front's features laid from it alone. Then all ten paints re-laid with Krea and relayed onto the head paints.
  2. **The eyes stare and read as a render:** the iris fully uncovered (a resting lid per face: Highborn about 0.18), irises 4 to 8% small and too contrasty, the lashes MakeHuman's black spiky band (and a faded rectangle in their paint). Ready to try: `--rest-lid X`, `--lashes PATH` (the new paint).
  3. **Upper lips 13 to 37% thinner than the portraits'** on most faces, in the sculpt itself (the clays). Sliders don't fill (lips_upper pouts). A sculpt per face: **a refit**, gathered with anything else of the head's.
  4. AgX (the world's tone curve) pales her lips and lifts her darks unshaded; under the white rig her lips are close. Secondary.
  5. Her neck's grain is half her portrait's neck's (0.0049 at s0.8 against 0.0094); the tile is clean now, so it can rise without speckle. The book by day; the jaw-edge spots.

## Key decisions (why)
- **Scatter 0.1, hers only** (`People.HerScatter`): 0.2 smears as 0.38 does; at 0.1 the detail stays and the light's edge is still soft (the shader's own terminator). The hero shares the shader; his lead may want the same.
- **Grain up her neck only, by the freckle maps' blue** (`heroine_freckles.py`): no new texture, no mesh change, no seam (the blue carried past the UV islands).
- **No freckles on the front of her chest:** sun freckles thin down the chest; over her breasts they read as specks.
- **Brow position by the paint, not the brows_height slider:** at 1.0 the slider moves the gap 0.52 to 0.60 (portrait 0.77) and looks surprised.
- **Brows pinned with their neighbours:** pinned alone, MediaPipe's guessed forehead points held while the brows moved, and the warp stretched a band 12 to 25 times (streaks). With the landmarks round them it stretches 0.55 to 1.24.
- **Her own head paint stays heroine.glb's** until reading `head_tex/heroine_head.jpg` (the same paint) is seen in a shot.
- Dev switches for pictures: `--zoom Z` (the Look's framing), `--lids X` (0 at rest), `--rest-lid X`, `--head-paint PATH`, `--lashes PATH`, `--tonemap linear|agx|...`, `--grade off`.

## Next
The brows' A/B in the game (pin fraction); the rendering lead's hair sheets (cycle 1); the eyes (lashes, resting lids, irises); then one sculpt (upper lips, maybe the brow ridge), one GPU re-lay of the ten paints, one build and **one refit**; then the handoff's list; then the paints and sliders pass (freckle control); then hair.

## Notes for other areas
- **Outfits:** her body takes no grain tile now (smooth below her collarbones, around and under garments too); her skin is sharper (scatter 0.1). No mesh or vertex-colour change.
- **Male hero:** the same shader's scatter 0.38 smears his paint at close-ups too.
- **Rendering:** her face's grain numbers are cleanest with `--skinparam scatter=0.1` (now her default). The new lash paint is soft at the tips for the blended card path (cover = its alpha as painted).
- **Main:** no refit yet. The upper lips' sculpt (and maybe the brow ridge) will need one, gathered with the ten paints' re-lay.
- **Shots:** an ember from the camp fire can drift in front of her at the Look (a soft orange disc); it's not her skin.
