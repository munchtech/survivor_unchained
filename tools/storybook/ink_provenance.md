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
