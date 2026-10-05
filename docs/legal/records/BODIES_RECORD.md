# Record: how the heroes' base bodies were made

Kept by the legal lead (aab20546fe06daa89) on 4 October 2026, as evidence for brief issue 5(b). ComfyUI keeps only three rotations of its log, so the lines below are copied here before they are overwritten. Nothing here is game content.

## The owner's account (4 Oct 2026, through the main session)

- "we made images in krea 2 turbo for the IMAGE but we did not use hunyuan 3d. we used trellis for the 3d."
- "we made it in comfyui": the picture and the 3D were both made in our local ComfyUI. No web tool was used.

## What the machine shows

**Installed models** (`%LOCALAPPDATA%\Comfy-Desktop\ComfyUI-Shared\models`):
- TRELLIS 2, installed 30 Sep 2026 04:15–04:17:
  - `diffusion_models/trellis_2_int8_convrot.safetensors`
  - `vae/trellis_2_shape_vae_bf16.safetensors`
  - `vae/trellis_2_texture_vae_bf16.safetensors`

  It is run by ComfyUI's own `comfy_extras/nodes_trellis2.py`. No other TRELLIS, no Hunyuan3D model, and no `nvdiffrast` are installed there.
- `diffusion_models/krea2_turbo_fp8_scaled.safetensors` (SHA-256 `eb4dd8c6…502f1`), the Krea 2 Turbo weights from `Comfy-Org/Krea-2`.
- LoRAs:
  - `krea2_darkbrush.safetensors` (official Krea, 264 target layers; SHA-256 `f47c4316…db7c6`), installed 30 Sep 13:09;
  - `MysticXXX_KREA2_v1.safetensors` (256 target layers; SHA-256 `32bfa436…87580`), installed 3 Oct 20:35.

**The hero's body** (`Desktop\ComfyUI_00008.glb`, 4 Oct 00:38, 46 MB, SHA-256 `924e5128e3588e23aa080f38cf4485afd45995edf911aad882d6567d96344535`). Its glTF `asset.generator` is "ComfyUI", and it has three PNG textures. `comfyui.log` of that night:

```
[2026-10-04 00:17:59] got prompt
[2026-10-04 00:18:00] ... diffusion_models\krea2_turbo_fp8_scaled.safetensors
[2026-10-04 00:18:06] Model Krea2 prepared for dynamic VRAM loading. 12530MB Staged. 256 patches attached.
[2026-10-04 00:18:37] Prompt executed in 37.99 seconds
  (four more Krea 2 Turbo prompts, 00:20 to 00:26, each with 256 patches attached)
[2026-10-04 00:28:32] got prompt
[2026-10-04 00:28:32] ... vae\trellis_2_shape_vae_bf16.safetensors
[2026-10-04 00:28:33] ... vae\trellis_2_texture_vae_bf16.safetensors
[2026-10-04 00:28:34] ... background_removal\birefnet.safetensors
[2026-10-04 00:28:35] ... clip_vision\dino_v3_L_naf_fp32.safetensors
[2026-10-04 00:28:36] ... diffusion_models\trellis_2_int8_convrot.safetensors
[2026-10-04 00:28:36] Requested to load Trellis2
```

**Which LoRA:**
- "256 patches attached" equals the MysticXXX LoRA's 256 target layers.
- The official darkbrush LoRA attaches 263 of its 264, as in `comfyui_8189.prev2.log`. All the repo's tools use darkbrush (`tools/uiforge/krea.py`, `tools/comfy/graphs/krea_t2i.json`).
- So the hero's picture was **most likely made with MysticXXX**. This is an inference; the owner should confirm.

**The heroine's body** (`234.glb`, in the repo by 1 Oct 23:08, commit da12945):
- It predates the MysticXXX install (3 Oct 20:35), so it can't have used that LoRA.
- TRELLIS 2 was the only TRELLIS installed then. The logs of 1 Oct don't name models.
- Its texture was JPEG, unlike ComfyUI's PNG saves. That suggests a re-export after TRELLIS. It doesn't affect the licence.

## The MysticXXX LoRA, identified

- Civitai's by-hash API, read 4 Oct 2026: https://civitai.com/api/v1/model-versions/by-hash/32BFA4362BCD9294E9B3515CC9F5F7013AC40463B1A9762625CCFB6F3A387580
  - Model 2728644, "[KREA 2] Mystic XXX", version 3067313 "v1.0", published 25 Jun 2026, base model Krea 2.
  - Creator `alcaitiff`; AIR `urn:air:krea2:lora:civitai:2728644@3067313`.
- The creator's permissions (https://civitai.com/api/v1/models/2728644):
  - `allowCommercialUse`: Image, RentCivit, Rent, Sell, SellMerge;
  - `allowNoCredit`: true;
  - `allowDerivatives`: true;
  - `allowDifferentLicense`: true.
- Flags: `nsfw` true (an explicit adult concept LoRA); `poi` false (not a real person); `minor` false.
- Its training data is not published.

## Still to add (owner)

A signed and dated paragraph for each body. It should give:
- the date;
- that the picture was text-to-image from his own words in local ComfyUI, with Krea 2 Turbo and the LoRA used (darkbrush, MysticXXX or none);
- that no real person was named and no photo or anyone else's art was uploaded as input;
- that TRELLIS 2 made the mesh locally.

If a picture was image-to-image, name the input and its origin.
