"""Krea 2 turbo jobs for the ink/woodcut storybook (Storybook 2).

    python tools/storybook/ink_gen.py <jobs.json> <outdir>

jobs.json: {"style": "<shared hand text, appended to every prompt>",
            "jobs": [{"name": "p5a", "prompt": "...", "w": 2048, "h": 1088, "seeds": [11, 23]}]}
Writes <outdir>/<name>_s<seed>.png and a provenance sidecar <name>_s<seed>.json
(model files, prompt, seed, settings). Skips images that exist. Needs the gpu turn.
"""
import json, os, sys, hashlib, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "comfy"))
import comfy  # noqa: E402

MODEL = {"unet": "krea2_turbo_fp8_scaled.safetensors", "clip": "qwen3vl_4b_fp8_scaled.safetensors",
         "clip_type": "krea2", "vae": "qwen_image_vae.safetensors"}
SETTINGS = {"steps": 8, "cfg": 1, "sampler": "euler", "scheduler": "simple"}


def graph(prompt, w, h, seed, init=None, denoise=1.0, mask=None):
    g = {
        "u": {"class_type": "UNETLoader", "inputs": {"unet_name": MODEL["unet"], "weight_dtype": "default"}},
        "c": {"class_type": "CLIPLoader", "inputs": {"clip_name": MODEL["clip"], "type": MODEL["clip_type"], "device": "default"}},
        "v": {"class_type": "VAELoader", "inputs": {"vae_name": MODEL["vae"]}},
        "p": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["c", 0], "text": prompt}},
        "n": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["p", 0]}},
    }
    if init:
        g["li"] = {"class_type": "LoadImage", "inputs": {"image": comfy.upload(init)}}
        g["le"] = {"class_type": "VAEEncode", "inputs": {"pixels": ["li", 0], "vae": ["v", 0]}}
        lat = ["le", 0]
        if mask:
            g["mi"] = {"class_type": "LoadImage", "inputs": {"image": comfy.upload(mask)}}
            g["mc"] = {"class_type": "ImageToMask", "inputs": {"image": ["mi", 0], "channel": "red"}}
            g["lm"] = {"class_type": "SetLatentNoiseMask", "inputs": {"samples": lat, "mask": ["mc", 0]}}
            lat = ["lm", 0]
    else:
        g["l"] = {"class_type": "EmptyLatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}}
        lat = ["l", 0]
    g["s"] = {"class_type": "KSampler", "inputs": {"model": ["u", 0], "positive": ["p", 0], "negative": ["n", 0],
              "latent_image": lat, "seed": seed, "steps": SETTINGS["steps"], "cfg": SETTINGS["cfg"],
              "sampler_name": SETTINGS["sampler"], "scheduler": SETTINGS["scheduler"], "denoise": denoise}}
    g["d"] = {"class_type": "VAEDecode", "inputs": {"samples": ["s", 0], "vae": ["v", 0]}}
    g["o"] = {"class_type": "SaveImage", "inputs": {"images": ["d", 0], "filename_prefix": "sb2ink"}}
    return g


def main():
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    out = sys.argv[2]
    os.makedirs(os.path.join(out, "_tmp"), exist_ok=True)
    style = spec.get("style", "")
    for j in spec["jobs"]:
        prompt = (j.get("prefix", spec.get("prefix", "")) + " " + j["prompt"] + " " + j.get("style", style)).strip()
        for seed in j["seeds"]:
            dst = os.path.join(out, f"{j['name']}_s{seed}.png")
            if os.path.exists(dst):
                continue
            t0 = time.time()
            saved = comfy.run(graph(prompt, j.get("w", 1600), j.get("h", 896), seed, j.get("init"),
                                    j.get("denoise", 1.0), j.get("mask")), os.path.join(out, "_tmp"))
            os.replace([x for x in saved if x.endswith(".png")][0], dst)
            side = {"generator": "Krea 2 turbo (local ComfyUI)", "model": MODEL, "settings": SETTINGS,
                    "prompt": prompt, "seed": seed, "size": [j.get("w", 1600), j.get("h", 896)],
                    "init": j.get("init"), "mask": j.get("mask"), "denoise": j.get("denoise", 1.0),
                    "made": time.strftime("%Y-%m-%d %H:%M"), "sha256": hashlib.sha256(open(dst, "rb").read()).hexdigest()}
            json.dump(side, open(dst[:-4] + ".json", "w", encoding="utf-8"), indent=1)
            print(f"{dst} {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
