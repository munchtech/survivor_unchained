"""Krea 2 turbo on the local ComfyUI, as a function: text to image, and image
to image over a guide (a forge render, a Blender render, a drawing), with
the darkbrush LoRA. Raw results land in tools/comfy/out/uiforge/ (ignored).

Candidates are made as one batch per call (the GPU is shared: the model is
loaded once for all of them, not once per candidate). A candidate is named
TAG_SEED_N: the call's seed and its place in the batch, which together
remake it exactly.

    from krea import t2i, i2i
    paths = t2i("prompt", seed=1, n=4, size=(1024, 1024))
    paths = i2i("guide.png", "prompt", denoise=0.45, seed=1, n=2)
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools", "comfy"))
import comfy  # noqa: E402

OUT = os.path.join(ROOT, "tools", "comfy", "out", "uiforge")

STYLE = ("hand-painted dark fantasy game interface art, forged blackened iron, soft light from the upper left, "
         "crisp clean edges, AAA game UI, no text, no letters, no numbers, no watermark")


def qrun(api, out_dir, front=False, timeout=7200):
    """comfy.run, quieter, and able to jump the queue (front=True) for quick jobs such as a
    cut-out, so they do not wait behind a long batch of paintings."""
    import json
    import time
    import urllib.parse
    import urllib.request
    import uuid
    body = {"prompt": api, "client_id": str(uuid.uuid4())}
    if front:
        body["front"] = True
    r = comfy.post("/prompt", body)
    pid = r["prompt_id"]
    t0 = time.time()
    while True:
        h = comfy.get(f"/history/{pid}")
        if pid in h:
            entry = h[pid]
            if entry.get("status", {}).get("status_str") == "error":
                raise SystemExit(json.dumps(entry["status"].get("messages", []))[:3000])
            break
        if time.time() - t0 > timeout:
            raise SystemExit("timed out")
        time.sleep(1.0)
    os.makedirs(out_dir, exist_ok=True)
    saved = []
    for node, out in entry["outputs"].items():
        for f in out.get("images", []):
            q = urllib.parse.urlencode({"filename": f["filename"], "subfolder": f.get("subfolder", ""), "type": f.get("type", "output")})
            dst = os.path.join(out_dir, f["filename"])
            with urllib.request.urlopen(f"{comfy.URL}/view?{q}") as resp, open(dst, "wb") as o:
                o.write(resp.read())
            saved.append(dst)
    return saved


def _graph(prompt, seed, lora=0.8, steps=8, denoise=1.0, prefix="uiforge"):
    return {
        "unet": {"class_type": "UNETLoader", "inputs": {"unet_name": "krea2_turbo_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "lora": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["unet", 0], "lora_name": "krea2_darkbrush.safetensors", "strength_model": lora}},
        "clip": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_4b_fp8_scaled.safetensors", "type": "krea2", "device": "default"}},
        "vae": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "pos": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["clip", 0], "text": prompt}},
        "neg": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["pos", 0]}},
        "ks": {"class_type": "KSampler", "inputs": {"model": ["lora", 0] if lora > 0 else ["unet", 0], "positive": ["pos", 0], "negative": ["neg", 0],
                                                  "latent_image": None, "seed": seed, "steps": steps, "cfg": 1, "sampler_name": "euler",
                                                  "scheduler": "simple", "denoise": denoise}},
        "dec": {"class_type": "VAEDecode", "inputs": {"samples": ["ks", 0], "vae": ["vae", 0]}},
        "save": {"class_type": "SaveImage", "inputs": {"images": ["dec", 0], "filename_prefix": prefix}},
    }


def _done(out, tag, seed):
    """What an earlier run already made for this call (so a cut-off batch resumes)."""
    import glob
    return sorted(glob.glob(os.path.join(out, f"{tag}_{seed}_*.png")))


def _collect(files, out, tag, seed):
    made = []
    for i, f in enumerate(sorted(files)):
        dst = os.path.join(out, f"{tag}_{seed}_{i}.png")
        os.replace(f, dst)
        made.append(dst)
    return made


def t2i(prompt, seed=1, n=4, size=(1024, 1024), lora=0.8, out=None, tag="t2i", steps=8):
    out = out or os.path.join(OUT, tag)
    os.makedirs(out, exist_ok=True)
    if _done(out, tag, seed):
        return _done(out, tag, seed)
    g = _graph(prompt, seed, lora=lora, steps=steps)
    g["lat"] = {"class_type": "EmptyLatentImage", "inputs": {"width": size[0], "height": size[1], "batch_size": n}}
    g["ks"]["inputs"]["latent_image"] = ["lat", 0]
    return _collect(qrun(g, out), out, tag, seed)


def t2i_many(jobs, size=(1024, 1024), lora=0.8, out=None, tag="many", steps=8, n=1):
    """Several prompts in one queued graph (one model load): jobs = [(name, prompt, seed)].
    Returns {name: [paths]}."""
    out = out or os.path.join(OUT, tag)
    os.makedirs(out, exist_ok=True)
    res = {name: _done(out, name, seed) for name, prompt, seed in jobs if _done(out, name, seed)}
    jobs = [j for j in jobs if j[0] not in res]
    if not jobs:
        return res
    import uuid
    tok = uuid.uuid4().hex[:6]
    base = _graph("", 0, lora=lora, steps=steps)
    g = {k: base[k] for k in ("unet", "lora", "clip", "vae")}
    g["lat"] = {"class_type": "EmptyLatentImage", "inputs": {"width": size[0], "height": size[1], "batch_size": n}}
    model = ["lora", 0] if lora > 0 else ["unet", 0]
    for i, (name, prompt, seed) in enumerate(jobs):
        g[f"pos{i}"] = {"class_type": "CLIPTextEncode", "inputs": {"clip": ["clip", 0], "text": prompt}}
        g[f"neg{i}"] = {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": [f"pos{i}", 0]}}
        g[f"ks{i}"] = {"class_type": "KSampler", "inputs": {"model": model, "positive": [f"pos{i}", 0], "negative": [f"neg{i}", 0],
                                                         "latent_image": ["lat", 0], "seed": seed, "steps": steps, "cfg": 1,
                                                         "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0}}
        g[f"dec{i}"] = {"class_type": "VAEDecode", "inputs": {"samples": [f"ks{i}", 0], "vae": ["vae", 0]}}
        g[f"save{i}"] = {"class_type": "SaveImage", "inputs": {"images": [f"dec{i}", 0], "filename_prefix": f"many_{tok}_{i:03d}_"}}
    files = qrun(g, out)
    for i, (name, prompt, seed) in enumerate(jobs):
        mine = sorted(f for f in files if os.path.basename(f).startswith(f"many_{tok}_{i:03d}_"))
        res[name] = []
        for j, f in enumerate(mine):
            dst = os.path.join(out, f"{name}_{seed}_{j}.png")
            os.replace(f, dst)
            res[name].append(dst)
    return res


def i2i(guide, prompt, denoise=0.45, seed=1, n=2, lora=0.8, out=None, tag="i2i", steps=8, front=False):
    out = out or os.path.join(OUT, tag)
    os.makedirs(out, exist_ok=True)
    if _done(out, tag, seed):
        return _done(out, tag, seed)
    name = comfy.upload(guide)
    g = _graph(prompt, seed, lora=lora, steps=steps, denoise=denoise)
    g["img"] = {"class_type": "LoadImage", "inputs": {"image": name}}
    g["enc"] = {"class_type": "VAEEncode", "inputs": {"pixels": ["img", 0], "vae": ["vae", 0]}}
    g["rep"] = {"class_type": "RepeatLatentBatch", "inputs": {"samples": ["enc", 0], "amount": n}}
    g["ks"]["inputs"]["latent_image"] = ["rep", 0]
    return _collect(qrun(g, out, front=front), out, tag, seed)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--size", default="1024x1024")
    ap.add_argument("--lora", type=float, default=0.8)
    ap.add_argument("--tag", default="t2i")
    ap.add_argument("--guide")
    ap.add_argument("--denoise", type=float, default=0.45)
    ap.add_argument("--style", action="store_true", help="append the house style line")
    a = ap.parse_args()
    p = a.prompt + (" " + STYLE if a.style else "")
    if a.guide:
        print("\n".join(i2i(a.guide, p, a.denoise, a.seed, a.n, a.lora, tag=a.tag)))
    else:
        w, h = (int(v) for v in a.size.split("x"))
        print("\n".join(t2i(p, a.seed, a.n, (w, h), a.lora, tag=a.tag)))
