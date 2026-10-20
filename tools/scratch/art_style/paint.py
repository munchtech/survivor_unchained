"""Style-frame paint-overs on the local ComfyUI (Z-Image Turbo + its Fun ControlNet Union). Local nodes only:
no Comfy account key is ever sent, so nothing can spend API credits.

    python paint.py JOBS.json OUTDIR     # runs every job in one GPU turn, gives the turn back at the end

JOBS.json: {"defaults": {...}, "jobs": [{...}, ...]}; each job (defaults filled in):
  kind     "paint" (img2img + control) or "mask" (SAM 3: every instance of `text`, one PNG each)
  src      the frame (PNG, any size; it is worked at 1920x1088 and returned at its own size)
  name     the output file's stem
  prompt   (paint) the positive prompt; cfg is 1, so there is no negative
  seed, denoise (0.55), steps (8), shift (3.0), sampler ("res_multistep"), scheduler ("simple")
  control  "depth" (MoGe), "canny", or "none"; cstrength (0.7), cend (1.0); canny_lo/hi (0.15/0.4)
  keep     optional grey PNG, white where the frame must NOT be repainted (her): it becomes
           DifferentialDiffusion's soft mask (repaint strength = 1 - keep)
  text     (mask) what SAM 3 looks for, e.g. "woman"; threshold (0.4)
"""
import json, os, shutil, sys, time, urllib.parse, urllib.request, uuid
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "comfy"))
import comfy  # noqa: E402  (upload, get, post: the shared client; its run() is not used, it sends a key)
from PIL import Image, ImageOps  # noqa: E402

TP = r"C:\Users\munch\Desktop\survivorsunchained\tools\turn.py"
TURN = "art-style: paint-overs"
WW, HH = 1920, 1088
D = {"denoise": 0.55, "steps": 8, "shift": 3.0, "sampler": "res_multistep", "scheduler": "simple", "control": "depth",
     "cstrength": 0.7, "cend": 1.0, "canny_lo": 0.15, "canny_hi": 0.4, "threshold": 0.4, "seed": 1}


def paint_graph(j, src, keep):
    g = {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "z_image_turbo_bf16.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "lumina2"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
        "4": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["1", 0], "shift": j["shift"]}},
        "6": {"class_type": "LoadImage", "inputs": {"image": src}},
        "7": {"class_type": "ImageScale", "inputs": {"image": ["6", 0], "upscale_method": "lanczos", "width": WW, "height": HH, "crop": "disabled"}},
        "13": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": j["prompt"]}},
        "14": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["13", 0]}},
        "15": {"class_type": "VAEEncode", "inputs": {"pixels": ["7", 0], "vae": ["3", 0]}},
    }
    model, latent = ["4", 0], ["15", 0]
    if j["control"] != "none":
        if j["control"] == "depth":
            g["8"] = {"class_type": "LoadMoGeModel", "inputs": {"model_name": "moge_2_vitl_normal_fp16.safetensors"}}
            g["9"] = {"class_type": "MoGeInference", "inputs": {"moge_model": ["8", 0], "image": ["7", 0], "resolution_level": 9, "batch_size": 1}}
            g["10"] = {"class_type": "MoGeRender", "inputs": {"moge_geometry": ["9", 0], "output": "depth"}}
            ctrl = ["10", 0]
        else:
            g["10"] = {"class_type": "Canny", "inputs": {"image": ["7", 0], "low_threshold": j["canny_lo"], "high_threshold": j["canny_hi"]}}
            ctrl = ["10", 0]
        g["5"] = {"class_type": "ModelPatchLoader", "inputs": {"name": "Z-Image-Turbo-Fun-Controlnet-Union-2.1-2602-8steps.safetensors"}}
        g["11"] = {"class_type": "ZImageFunControlnet", "inputs": {"model": model, "model_patch": ["5", 0], "vae": ["3", 0], "strength": j["cstrength"],
                                                                   "image": ctrl, "start_percent": 0.0, "end_percent": j["cend"]}}
        model = ["11", 0]
        if j.get("save_control"):
            g["30"] = {"class_type": "SaveImage", "inputs": {"images": ctrl, "filename_prefix": "artstyle/" + j["name"] + "_ctrl"}}
    if keep:
        g["16"] = {"class_type": "LoadImage", "inputs": {"image": keep}}
        g["16b"] = {"class_type": "ImageScale", "inputs": {"image": ["16", 0], "upscale_method": "bilinear", "width": WW, "height": HH, "crop": "disabled"}}
        g["16c"] = {"class_type": "ImageToMask", "inputs": {"image": ["16b", 0], "channel": "red"}}
        g["16d"] = {"class_type": "InvertMask", "inputs": {"mask": ["16c", 0]}}
        g["12"] = {"class_type": "DifferentialDiffusion", "inputs": {"model": model}}
        g["17"] = {"class_type": "SetLatentNoiseMask", "inputs": {"samples": latent, "mask": ["16d", 0]}}
        model, latent = ["12", 0], ["17", 0]
    g["18"] = {"class_type": "KSampler", "inputs": {"model": model, "seed": j["seed"], "steps": j["steps"], "cfg": 1.0, "sampler_name": j["sampler"],
                                                    "scheduler": j["scheduler"], "positive": ["13", 0], "negative": ["14", 0], "latent_image": latent, "denoise": j["denoise"]}}
    g["19"] = {"class_type": "VAEDecode", "inputs": {"samples": ["18", 0], "vae": ["3", 0]}}
    g["21"] = {"class_type": "SaveImage", "inputs": {"images": ["19", 0], "filename_prefix": "artstyle/" + j["name"]}}
    return g


def mask_graph(j, src):
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "sam3.1_multiplex_fp16.safetensors"}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": j["text"]}},
        "3": {"class_type": "LoadImage", "inputs": {"image": src}},
        "4": {"class_type": "SAM3_Detect", "inputs": {"model": ["1", 0], "image": ["3", 0], "threshold": j["threshold"], "refine_iterations": 2,
                                                      "individual_masks": True, "conditioning": ["2", 0]}},
        "5": {"class_type": "MaskToImage", "inputs": {"mask": ["4", 0]}},
        "6": {"class_type": "SaveImage", "inputs": {"images": ["5", 0], "filename_prefix": "artstyle/" + j["name"]}},
    }


def queue(api):
    r = comfy.post("/prompt", {"prompt": api, "client_id": str(uuid.uuid4())})   # no extra_data: no account key
    if r.get("node_errors"): print("NODE ERRORS:", json.dumps(r["node_errors"])[:1500])
    return r["prompt_id"]


def wait(pid, timeout=1800):
    t0 = time.time()
    while True:
        h = comfy.get(f"/history/{pid}")
        if pid in h:
            e = h[pid]
            if e.get("status", {}).get("status_str") == "error":
                print("ERROR:", json.dumps([m for m in e["status"].get("messages", []) if m[0] == "execution_error"])[:2500]); return None
            return e
        if time.time() - t0 > timeout: print("TIMEOUT", pid); return None
        time.sleep(1.0)


def fetch(entry, outdir, stem, size):
    got = []
    for out in entry["outputs"].values():
        for i, f in enumerate(out.get("images", [])):
            q = urllib.parse.urlencode({"filename": f["filename"], "subfolder": f.get("subfolder", ""), "type": f.get("type", "output")})
            suffix = "_ctrl" if "_ctrl" in f["filename"] else ""
            dst = os.path.join(outdir, f"{stem}{suffix}{'_' + str(i) if len(out['images']) > 1 else ''}.png")
            with urllib.request.urlopen(f"{comfy.URL}/view?{q}") as r, open(dst, "wb") as o: o.write(r.read())
            if size and not suffix:
                im = Image.open(dst)
                if im.size != size: im.convert("RGB").resize(size, Image.LANCZOS).save(dst)
            got.append(dst)
    return got


def main():
    spec = json.load(open(sys.argv[1], encoding="utf-8")); outdir = sys.argv[2]; os.makedirs(outdir, exist_ok=True)
    jobs = [dict(D, **spec.get("defaults", {}), **j) for j in spec["jobs"]]
    import subprocess
    if subprocess.run([sys.executable, TP, "take", "gpu", TURN, "--wait", "3600"]).returncode != 0: sys.exit("GPU TURN REFUSED")
    t00 = time.time()
    try:
        uploaded = {}
        def up(p):
            if p not in uploaded: uploaded[p] = comfy.upload(p)
            return uploaded[p]
        pending = []
        for j in jobs:
            src = up(j["src"]); size = Image.open(j["src"]).size
            api = mask_graph(j, src) if j.get("kind") == "mask" else paint_graph(j, src, up(j["keep"]) if j.get("keep") else None)
            pending.append((j, queue(api), size))
        for j, pid, size in pending:
            t0 = time.time(); e = wait(pid)
            if e: print(j["name"], f"{time.time() - t0:.0f}s", fetch(e, outdir, j["name"], size if j.get("kind") != "mask" else None))
    finally:
        try: comfy.post("/free", {"unload_models": True, "free_memory": True})
        except Exception as ex: print("free failed", ex)
        subprocess.run([sys.executable, TP, "give", "gpu", TURN])
    print(f"ALL DONE in {time.time() - t00:.0f}s")


if __name__ == "__main__":
    main()
