#!/bin/sh
# Z-Image-Turbo (Apache-2.0, Tongyi-MAI), ComfyUI's repackage from Comfy-Org/z_image_turbo.
M=/c/Users/munch/AppData/Local/Comfy-Desktop/ComfyUI-Shared/models
B=https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files
fetch() { # dir file sha
  if [ -f "$M/$1/$2" ]; then echo "have $2"; else
    curl -L -s -S --retry 5 -o "$M/$1/$2.part" "$B/$1/$2" && mv "$M/$1/$2.part" "$M/$1/$2"; fi
  echo "$3  $M/$1/$2" | sha256sum -c -
}
fetch vae ae.safetensors afc8e28272cd15db3919bacdb6918ce9c1ed22e96cb12c4d5ed0fba823529e38
fetch text_encoders qwen_3_4b.safetensors 6c671498573ac2f7a5501502ccce8d2b08ea6ca2f661c458e708f36b36edfc5a
fetch diffusion_models z_image_turbo_bf16.safetensors 2407613050b809ffdff18a4ac99af83ea6b95443ecebdf80e064a79c825574a6
echo done
