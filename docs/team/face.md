# Heroine face, hair and creation's Look: status

Agent a43570e07edbe40b2 (handing off at v11), branch `worktree-agent-a43570e07edbe40b2`.
The handoff for v12 is `docs/handoff/face.md`.

## Current state (2026-10-06)
- **v11** (this branch, through 93f66173; no geometry or blend paint changed, **no refit needed**). Merged with the integration branch's v10b refit (19dca97e); creation's portraits rerun on it (a3369938).
- Against the bar (`face_sheets/v11_face.jpg`, `v11_presets.jpg`, `v11_play_zoom.png`):
  - **Tones** under the white rig: every face within 3.3% per channel of its portrait (`tone_fit.py v11e`).
  - **Irises**: every face within 5% per channel of its portrait (were a third to a fiftieth as light; `iris_fit.py`).
  - **Grain** at the Look: face s0.8 / s1.6 / s3.2 = 0.65 / 0.82 / 0.89 of the photo's. Not 0.9 yet (the finest is TAA's).
  - **Neck grain**: neck over face 0.36 / 0.29 / 0.25 at the Look (was 0.26 / 0.22 / 0.23; the portrait's 0.46 / 0.45 / 0.39).
  - **Brows** (hers): dark third over skin L 0.74, hair 0.27 (portrait 0.76, 0.28; were 0.35, 0.41).
  - **Play zoom**: eyes and a mouth read at the game's camera, day, night and arena (were a blank); brows read at 12.5 m, merged with the eyes at 23 m.
  - **Book by day**: her lamp at half while the book frames her; still flat (the sun is frontal).
- **Tells left at the close-up**: skin a touch smooth and even; lips thinner and paler than her portrait's; the hair (a helmet, a pale strip at the temples; the hair pass); the other faces' brows 1.3 to 1.8 times too light against their portraits.

## Key decisions (why)
- **Eye swatches are the iris's own colour** (`iris_light` 1): the sky's cornea reflection that lit them at 0.3 was dimmed in v10. Fey, Vixen, Doe and Moonlit have swatches of their own (Dove, Lichen, Chestnut, Umber): shared, two faces were 20 to 50% apart.
- **Each face's paint has its own tone** (`face_tone`, laid by the features' blue on the face alone), the swatch fit for the body.
- **Only her own face's brows are dyed** to her hair: her brow mask on another face dyed its lid crease. Each hair keeps its painted darkness, in the dye's hue.
- **Play zoom**: the features' marks read at a capped mip and grown to the pixel; her head carried 8 degrees up in play (`HerCarriage.HeadLevel`; play only, the animation lead to sign off).
- **Her neck's grain is her face paint's own** (`heroine_grain.py`, a tile): the pores' tile read as sandpaper.
- **Freckles**: lower defaults (hers 0.18, Hard-won 0.12, Wildling 0.1, Fey 0.06), softer at low amounts; a face shaped by hand starts with none.

## Next
See the handoff: the other faces' brows, the face's finest grain, the lips, the book's light, the chest flake (not found at the Look on the refit), then the paints and sliders pass.

## Notes for other areas
- **Male hero:** the eye shader's `iris_light` is 1 now; his flint is refitted (`People.HisEyes`). His irises were as dark as hers.
- **Animation:** `HerCarriage.HeadLevel` lifts her head 8 degrees above level in play (`--head-level`, `--head-ease`). Please judge it in motion.
- **Arena art / experience:** at the Verge's arrival the canopy hides her entirely from play's camera.
- **Shots:** `--book-lamp`, `--grain`, `--brows soften,sat`, `--head-level`, `--head-ease` try values.
