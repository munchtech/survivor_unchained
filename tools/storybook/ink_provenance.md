# Ink storybook (SB00, Storybook 3): provenance

## The four picks (Krea 2 turbo, local ComfyUI; sidecar JSON beside each PNG holds model files, prompt, seed, settings, sha256)

| Plate | File (tools/storybook/out/) | Sidecar | sha256 (first 16) | Jobs file |
|---|---|---|---|---|
| p5 The Low Ford; the drowned | ink_r3/p5_s707.png | ink_r3/p5_s707.json | 3b032305db7357c9 | ink_jobs/r3.json |
| p6 The traveler | ink_r2/p6_s47.png | ink_r2/p6_s47.json | 227f50786578c317 | ink_jobs/r2.json |
| p7 The water | ink_r2/p7_s11.png | ink_r2/p7_s11.json | 80cee76fb19649aa | ink_jobs/r2.json |
| p7u Underwater | ink_r3/p7u_s47.png | ink_r3/p7u_s47.json | fca646abe93bc661 | ink_jobs/r3.json |

Fills behind cuts and the drawn states are Krea 2 turbo inpaints of these (same model, prompts in `ink_layers.py`,
seeds 7 for fills and 11/23/47/202 for states); masks from MoGe-2 depth and SAM 3.1 (local models).

## Paper

- **ambientCG Paper005** (4K JPG, Color map only), https://ambientcg.com/view?id=Paper005,
  downloaded 2026-10-29 from https://ambientcg.com/get?file=Paper005_4K-JPG.zip
  (zip sha256 c20d1e04707988ce3c80449130ac01beca7a14decba3a7241c99c21bae2508ab).
- Licence: **CC0 1.0** (ambientCG, https://docs.ambientcg.com/license/). No credit required.
- Local copy: `tools/storybook/out/paper_Paper005.jpg` (git-ignored; sha256 63e73d68a5e1ddce...).
  `ink_post.py` uses its luminance only (fibre + blotch), sampled at each layer's place in the plate.

## p5 drowned and refills, rounds 2-3 (Krea 2 turbo, local ComfyUI; a JSON sidecar beside each PNG: model files, prompt, seed, settings, sha256)

All under `tools/storybook/out/ink_layers/` (git-ignored). Round 2's sidecars were written in round 3 from `ink_r2.py`'s calls.
Round 3's init (`_work/p5/r3_init.png`) is the clean plate plus round 2's frieze figures (above), darkened, re-haired and
placed by `ink_r3.py init`; the shipped candidate's whole is `_work/p5/S_drowned_r3_<tag>.png`, baked into `p5/road.png`.

| Round | File | What | sha256 (first 16) |
|---|---|---|---|
| ink round 2 | `_work/p5/frieze_s11.png` | frieze of drowned figures, txt2img 1920x1088, seed 11 (prompt `ink_layers.P5_FRIEZE`); BiRefNet matte `frieze_s11_sam.png` | cd980880d5e8a7d4 |
| ink round 2 | `_work/p5/frieze_s23.png` | frieze of drowned figures, txt2img 1920x1088, seed 23 (prompt `ink_layers.P5_FRIEZE`); BiRefNet matte `frieze_s23_sam.png` | 743b3f971014ad48 |
| ink round 2 | `_work/p5/frieze_s47.png` | frieze of drowned figures, txt2img 1920x1088, seed 47 (prompt `ink_layers.P5_FRIEZE`); BiRefNet matte `frieze_s47_sam.png` | c789ccbd392ab349 |
| ink round 2 | `_work/p5/frieze_s202.png` | frieze of drowned figures, txt2img 1920x1088, seed 202 (prompt `ink_layers.P5_FRIEZE`); BiRefNet matte `frieze_s202_sam.png` | c367c8a0d318f70f |
| ink round 2 | `_work/p5/frieze_s303.png` | frieze of drowned figures, txt2img 1920x1088, seed 303 (prompt `ink_layers.P5_FRIEZE`); BiRefNet matte `frieze_s303_sam.png` | 89b5694eeed504c4 |
| ink round 2 | `_work/p5/frieze_s505.png` | frieze of drowned figures, txt2img 1920x1088, seed 505 (prompt `ink_layers.P5_FRIEZE`); BiRefNet matte `frieze_s505_sam.png` | abbd096b5d20cdc6 |
| ink round 2 | `_work/p5/raw2_ghost_s31.png` | the right ditch ghost refill, inpaint denoise 1.0, seed 31 (prompt `P5_CLEAN_LOCAL`); applied into `S_clean.png` | f36f908515694640 |
| ink round 3 | `_work/p5/r3_raw_left_d50_s11.png` | broad-ditch img2img, denoise 0.5, seed 11, init `r3_in_left.png` (prompt `ink_r3.PROMPT`) | adcc5a971f25f178 |
| ink round 3 | `_work/p5/r3_raw_left_d50_s23.png` | broad-ditch img2img, denoise 0.5, seed 23, init `r3_in_left.png` (prompt `ink_r3.PROMPT`) | 86c0af09a10d6f90 |
| ink round 3 | `_work/p5/r3_raw_left_d50_s47.png` | broad-ditch img2img, denoise 0.5, seed 47, init `r3_in_left.png` (prompt `ink_r3.PROMPT`) | 7016c813039b7c3e |
| ink round 3 | `_work/p5/r3_raw_left_d60_s11.png` | broad-ditch img2img, denoise 0.6, seed 11, init `r3_in_left.png` (prompt `ink_r3.PROMPT`) | 1966d5c7b8054bf0 |
| ink round 3 | `_work/p5/r3_raw_left_d60_s23.png` | broad-ditch img2img, denoise 0.6, seed 23, init `r3_in_left.png` (prompt `ink_r3.PROMPT`) | 7588e127b847ac5a |
| ink round 3 | `_work/p5/r3_raw_left_d60_s47.png` | broad-ditch img2img, denoise 0.6, seed 47, init `r3_in_left.png` (prompt `ink_r3.PROMPT`) | d29033f100adc4fc |
| ink round 3 | `_work/p5/r3_raw_left_d70_s11.png` | broad-ditch img2img, denoise 0.7, seed 11, init `r3_in_left.png` (prompt `ink_r3.PROMPT`) | 75cd323be43c212e |
| ink round 3 | `_work/p5/r3_raw_left_d70_s23.png` | broad-ditch img2img, denoise 0.7, seed 23, init `r3_in_left.png` (prompt `ink_r3.PROMPT`) | e0916fd713ea3a21 |
| ink round 3 | `_work/p5/r3_raw_left_d70_s47.png` | broad-ditch img2img, denoise 0.7, seed 47, init `r3_in_left.png` (prompt `ink_r3.PROMPT`) | da1d586127fe24a8 |
| ink round 3 | `_work/p5/r3_raw_right_d50_s11.png` | broad-ditch img2img, denoise 0.5, seed 11, init `r3_in_right.png` (prompt `ink_r3.PROMPT`) | 3fbea3e3fe16de85 |
| ink round 3 | `_work/p5/r3_raw_right_d50_s23.png` | broad-ditch img2img, denoise 0.5, seed 23, init `r3_in_right.png` (prompt `ink_r3.PROMPT`) | 6c1b8166027fdc2f |
| ink round 3 | `_work/p5/r3_raw_right_d50_s47.png` | broad-ditch img2img, denoise 0.5, seed 47, init `r3_in_right.png` (prompt `ink_r3.PROMPT`) | a293b2580c959d36 |
| ink round 3 | `_work/p5/r3_raw_right_d60_s11.png` | broad-ditch img2img, denoise 0.6, seed 11, init `r3_in_right.png` (prompt `ink_r3.PROMPT`) | 78c1a8591caf80de |
| ink round 3 | `_work/p5/r3_raw_right_d60_s23.png` | broad-ditch img2img, denoise 0.6, seed 23, init `r3_in_right.png` (prompt `ink_r3.PROMPT`) | 55fa4bd51de13ad7 |
| ink round 3 | `_work/p5/r3_raw_right_d60_s47.png` | broad-ditch img2img, denoise 0.6, seed 47, init `r3_in_right.png` (prompt `ink_r3.PROMPT`) | 0d2607f85b7602db |
| ink round 3 | `_work/p5/r3_raw_right_d70_s11.png` | broad-ditch img2img, denoise 0.7, seed 11, init `r3_in_right.png` (prompt `ink_r3.PROMPT`) | 2c664332cd93a891 |
| ink round 3 | `_work/p5/r3_raw_right_d70_s23.png` | broad-ditch img2img, denoise 0.7, seed 23, init `r3_in_right.png` (prompt `ink_r3.PROMPT`) | 9f35f2ba70cb036d |
| ink round 3 | `_work/p5/r3_raw_right_d70_s47.png` | broad-ditch img2img, denoise 0.7, seed 47, init `r3_in_right.png` (prompt `ink_r3.PROMPT`) | 5866542461dd831f |
