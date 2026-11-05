"""B3 arm B/C's AI paint (L1 texture authoring): Z-Image Turbo (Apache-2.0) with its Fun ControlNet Union 2.1
(Apache-2.0) in the local ComfyUI, in the asset's own UV space: the control is the asset's block joints and convex
edges (from its form maps), the start is arm A's albedo (the class colors and the painted light), the prompt names
the boards' kind (MB3/MB4: hand-painted color blocks with the brush inside). paint_core.py --arm B|C then
re-quantizes it to the blocks. The caller holds the gpu turn (tools/turn.py take gpu ...).

    python tools/look/ai_paint.py FORMS_DIR A_ALBEDO.png OUT.png [--seed 11] [--denoise 0.6] [--strength 0.75]
"""
import io, json, os, sys, time, urllib.request, uuid

import numpy as np
from PIL import Image
from scipy import ndimage

HOST = "http://127.0.0.1:8188"
PROMPTS = {
    "setts": "hand-painted stylized game texture, top-down orthographic view of chunky cobblestone setts, each stone one flat color block with soft painterly brush strokes inside, warm lit tops, cool dark joints, Arcane and Overwatch hand-painted texture style, clean, no photo detail, no noise",
    "rock": "hand-painted stylized game texture of a boulder's surface, a few big flat rock planes, each plane one muted grey color block with broad painterly brush strokes inside, Arcane and Overwatch hand-painted style, clean, no photo detail, no small cracks",
    "plank": "hand-painted stylized game texture of wooden barrel staves and iron hoops, each stave one color block with a few long painterly brush strokes along the grain, Arcane and Overwatch hand-painted style, clean, no photo detail",
}


def post(path, data=None, files=None):
    if files:
        b = uuid.uuid4().hex; body = io.BytesIO()
        for k, (fn, content) in files.items():
            body.write(f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"; filename=\"{fn}\"\r\nContent-Type: image/png\r\n\r\n".encode()); body.write(content); body.write(b"\r\n")
        body.write(f"--{b}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n--{b}--\r\n".encode())
        req = urllib.request.Request(HOST + path, body.getvalue(), {"Content-Type": f"multipart/form-data; boundary={b}"})
    else:
        req = urllib.request.Request(HOST + path, json.dumps(data).encode(), {"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=600).read() or b"{}")


def upload(im, name):
    buf = io.BytesIO(); im.save(buf, "PNG")
    return post("/upload/image", files={"image": (name, buf.getvalue())})["name"]


def control(forms_dir, size):
    F = np.load(os.path.join(forms_dir, "forms.npz")); blk, mask = F["blk"], F["mask"]
    e = np.zeros_like(mask)
    for sh in ((0, 1), (1, 0)):
        e |= np.roll(blk, sh, (0, 1)) != blk
    e = ndimage.binary_dilation(e, iterations=max(1, blk.shape[0] // 512))
    cvx = F["convex"].astype(np.float32)
    img = np.maximum(e * 1.0, np.clip((cvx - 0.2) * 2.5, 0, 1) * 0.6)
    return Image.fromarray((img * 255).astype(np.uint8)).convert("RGB").resize((size, size), Image.BILINEAR)


def run(forms_dir, a_albedo, out, seed=11, denoise=0.6, strength=0.75):
    meta = json.load(open(os.path.join(forms_dir, "forms.json")))
    cls = meta["classes"][0]
    size = 1024
    ci = upload(control(forms_dir, size), f"b3_ctl_{meta['asset']}.png")
    ii = upload(Image.open(a_albedo).convert("RGB").resize((size, size), Image.LANCZOS), f"b3_init_{meta['asset']}.png")
    g = {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "z_image_turbo_bf16.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "lumina2"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
        "4": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["1", 0], "shift": 3.0}},
        "5": {"class_type": "ModelPatchLoader", "inputs": {"name": "Z-Image-Turbo-Fun-Controlnet-Union-2.1-2602-8steps.safetensors"}},
        "6": {"class_type": "LoadImage", "inputs": {"image": ci}},
        "7": {"class_type": "ZImageFunControlnet", "inputs": {"model": ["4", 0], "model_patch": ["5", 0], "vae": ["3", 0], "strength": strength, "image": ["6", 0]}},
        "8": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": PROMPTS.get(cls, PROMPTS["setts"])}},
        "9": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["8", 0]}},
        "10": {"class_type": "LoadImage", "inputs": {"image": ii}},
        "11": {"class_type": "VAEEncode", "inputs": {"pixels": ["10", 0], "vae": ["3", 0]}},
        "12": {"class_type": "KSampler", "inputs": {"model": ["7", 0], "positive": ["8", 0], "negative": ["9", 0], "latent_image": ["11", 0],
                                                     "seed": seed, "steps": 8, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": denoise}},
        "13": {"class_type": "VAEDecode", "inputs": {"samples": ["12", 0], "vae": ["3", 0]}},
        "14": {"class_type": "SaveImage", "inputs": {"images": ["13", 0], "filename_prefix": f"b3_{meta['asset']}"}},
    }
    t0 = time.time()
    pid = post("/prompt", {"prompt": g})["prompt_id"]
    while True:
        h = json.loads(urllib.request.urlopen(f"{HOST}/history/{pid}").read())
        if pid in h and h[pid].get("outputs"):
            im = h[pid]["outputs"]["14"]["images"][0]; break
        if pid in h and h[pid].get("status", {}).get("status_str") == "error": sys.exit(json.dumps(h[pid]["status"])[:2000])
        time.sleep(1.0)
    data = urllib.request.urlopen(f"{HOST}/view?filename={im['filename']}&subfolder={im['subfolder']}&type={im['type']}").read()
    W = meta["size"]
    Image.open(io.BytesIO(data)).convert("RGB").resize((W, W), Image.LANCZOS).save(out)
    print(json.dumps(dict(asset=meta["asset"], out=out, seconds=round(time.time() - t0, 1), seed=seed, denoise=denoise, strength=strength,
                          model="z_image_turbo_bf16 + Z-Image-Turbo-Fun-Controlnet-Union-2.1")))


if __name__ == "__main__":
    a = sys.argv[1:]
    def opt(n, d, c=float):
        if n in a: i = a.index(n); v = a[i + 1]; del a[i:i + 2]; return c(v)
        return d
    seed, dn, st = opt("--seed", 11, int), opt("--denoise", 0.6), opt("--strength", 0.75)
    run(a[0], a[1], a[2], seed, dn, st)
