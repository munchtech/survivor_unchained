"""The storybook's paintings, made on the local ComfyUI with Z-Image-Turbo
(Apache-2.0, cleared in docs/legal/LEGAL_BRIEF.md; never Krea), and each one
logged: a sidecar JSON beside every picture holds the prompt, the seed, the
settings and the hashes of the weights that made it (docs/storybook/README.md,
"Provenance").

    python tools/storybook/gen.py <jobs.json> [--out DIR] [--only NAME,...]

A jobs file is a list (or {"defaults": {...}, "jobs": [...]}) of:
    {"name": "p1_a", "prompt": "...", "seed": 7 | [7, 8, 9], "w": 1792, "h": 1024,
     "steps": 9, "shift": 3.0,
     "init": "path.png", "denoise": 0.55,               # paint over a picture
     "control": "edges.png", "strength": 0.7,             # hold a layout (canny/depth/pose/hed)
     "inpaint": "path.png", "mask": "mask.png"}           # repaint the white of the mask
Take the GPU turn first (tools/turn.py take gpu "storybook: ...").
"""
import argparse
import hashlib
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "comfy"))
import comfy  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = r"C:\Users\munch\AppData\Local\Comfy-Desktop\ComfyUI-Shared\models"
UNET = "z_image_turbo_bf16.safetensors"
CLIP = "qwen_3_4b.safetensors"
VAE = "ae.safetensors"
PATCH = "Z-Image-Turbo-Fun-Controlnet-Union-2.1-2602-8steps.safetensors"
WEIGHTS = {UNET: "diffusion_models", CLIP: "text_encoders", VAE: "vae", PATCH: "model_patches"}
HASHES = os.path.join(HERE, "model_hashes.json")


def sha(name):
    """A weight's sha256, worked out once and kept in model_hashes.json."""
    known = json.load(open(HASHES)) if os.path.exists(HASHES) else {}
    if name not in known:
        h = hashlib.sha256()
        with open(os.path.join(MODELS, WEIGHTS[name], name), "rb") as f:
            for block in iter(lambda: f.read(1 << 24), b""):
                h.update(block)
        known[name] = h.hexdigest()
        json.dump(known, open(HASHES, "w"), indent=1, sort_keys=True)
    return known[name]


def graph(job, seed, prefix):
    w, h = int(job.get("w", 1792)), int(job.get("h", 1024))
    g = {
        "unet": {"class_type": "UNETLoader", "inputs": {"unet_name": UNET, "weight_dtype": "default"}},
        "clip": {"class_type": "CLIPLoader", "inputs": {"clip_name": CLIP, "type": "lumina2", "device": "default"}},
        "vae": {"class_type": "VAELoader", "inputs": {"vae_name": VAE}},
        "shift": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["unet", 0], "shift": float(job.get("shift", 3.0))}},
        "pos": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["clip", 0], "text": job["prompt"]}},
        "neg": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["pos", 0]}},
    }
    model = ["shift", 0]
    denoise = 1.0
    if job.get("init"):
        g["init"] = {"class_type": "LoadImage", "inputs": {"image": comfy.upload(job["init"])}}
        g["init_s"] = {"class_type": "ImageScale", "inputs": {"image": ["init", 0], "upscale_method": "lanczos", "width": w, "height": h, "crop": "disabled"}}
        g["latent"] = {"class_type": "VAEEncode", "inputs": {"pixels": ["init_s", 0], "vae": ["vae", 0]}}
        denoise = float(job.get("denoise", 0.55))
    else:
        g["latent"] = {"class_type": "EmptySD3LatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}}
    if job.get("control") or job.get("inpaint"):
        g["patch"] = {"class_type": "ModelPatchLoader", "inputs": {"name": PATCH}}
        cn = {"model": model, "model_patch": ["patch", 0], "vae": ["vae", 0], "strength": float(job.get("strength", 1.0))}
        if job.get("control"):
            g["ctl"] = {"class_type": "LoadImage", "inputs": {"image": comfy.upload(job["control"])}}
            g["ctl_s"] = {"class_type": "ImageScale", "inputs": {"image": ["ctl", 0], "upscale_method": "lanczos", "width": w, "height": h, "crop": "disabled"}}
            cn["image"] = ["ctl_s", 0]
        if job.get("inpaint"):
            g["inp"] = {"class_type": "LoadImage", "inputs": {"image": comfy.upload(job["inpaint"])}}
            g["inp_s"] = {"class_type": "ImageScale", "inputs": {"image": ["inp", 0], "upscale_method": "lanczos", "width": w, "height": h, "crop": "disabled"}}
            g["msk"] = {"class_type": "LoadImageMask", "inputs": {"image": comfy.upload(job["mask"]), "channel": "red"}}
            cn["inpaint_image"] = ["inp_s", 0]
            cn["mask"] = ["msk", 0]
        if "end" in job:
            cn["end_percent"] = float(job["end"])
        g["cn"] = {"class_type": "ZImageFunControlnet", "inputs": cn}
        model = ["cn", 0]
    g["sample"] = {"class_type": "KSampler", "inputs": {
        "model": model, "positive": ["pos", 0], "negative": ["neg", 0], "latent_image": ["latent", 0],
        "seed": int(seed), "steps": int(job.get("steps", 9)), "cfg": float(job.get("cfg", 1.0)),
        "sampler_name": job.get("sampler", "res_multistep"), "scheduler": job.get("scheduler", "simple"), "denoise": denoise}}
    g["decode"] = {"class_type": "VAEDecode", "inputs": {"samples": ["sample", 0], "vae": ["vae", 0]}}
    g["save"] = {"class_type": "SaveImage", "inputs": {"images": ["decode", 0], "filename_prefix": prefix}}
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jobs")
    ap.add_argument("--out", default=None)
    ap.add_argument("--only", default=None)
    a = ap.parse_args()
    spec = json.load(open(a.jobs, encoding="utf-8"))
    defaults, jobs = ({}, spec) if isinstance(spec, list) else (spec.get("defaults", {}), spec["jobs"])
    out = a.out or os.path.join(HERE, "out", os.path.splitext(os.path.basename(a.jobs))[0])
    os.makedirs(out, exist_ok=True)
    only = set(a.only.split(",")) if a.only else None
    weights = {n: sha(n) for n in (UNET, CLIP, VAE)}
    for raw in jobs:
        job = {**defaults, **raw}
        if only and job["name"] not in only:
            continue
        if "prompt" not in job and "style" in job:
            pass
        seeds = job.get("seed", 1)
        for seed in seeds if isinstance(seeds, list) else [seeds]:
            name = f"{job['name']}_s{seed}"
            dst = os.path.join(out, name + ".png")
            if os.path.exists(dst):
                continue
            t0 = time.time()
            tmp = os.path.join(out, "_tmp")
            saved = comfy.run(graph(job, seed, "sb_" + name), tmp)
            src = [p for p in saved if p.endswith(".png")][0]
            os.replace(src, dst)
            used = dict(weights)
            if job.get("control") or job.get("inpaint"):
                used[PATCH] = sha(PATCH)
            side = {k: v for k, v in job.items() if k != "seed"}
            side.update({"seed": seed, "file": os.path.basename(dst), "weights_sha256": used,
                         "made": time.strftime("%Y-%m-%d %H:%M:%S"), "tool": "tools/storybook/gen.py", "seconds": round(time.time() - t0, 1)})
            json.dump(side, open(dst[:-4] + ".json", "w", encoding="utf-8"), indent=1)
            print(f"{name}: {side['seconds']} s", flush=True)


if __name__ == "__main__":
    main()
