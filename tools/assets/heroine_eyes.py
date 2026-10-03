"""Her eyes' paint, made anew at twice the size: MakeHuman's whites (their
veins and shading), with irises painted by Krea 2 (local, through ComfyUI)
over a drawing of an iris (so it is round, centred and as big as hers).

    python tools/assets/heroine_eyes.py [seed]      (IRIS_KEEP=1: the iris painted before)

Writes godot/art/people/head_tex/heroine_eye.png, her eyes' whites, laid
out as MakeHuman's green_eye.png (the irises painted out, the clear
cornea's patch kept clear), and heroine_iris.png, the iris alone, for
shaders/heroine_eye.gdshader, which lays it wherever she looks. Its iris is
green with a ring of amber round the pupil; the game can tint it. And
heroine_lashes.png, her lashes with the lower ones made finer.
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "comfy"))
import comfy  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "godot", "art", "people", "head_tex", "green_eye.png")
DST = os.path.join(ROOT, "godot", "art", "people", "head_tex", "heroine_eye.png")
IRIS = os.path.join(ROOT, "godot", "art", "people", "head_tex", "heroine_iris.png")
LASH_SRC = os.path.join(ROOT, "godot", "art", "people", "head_tex", "eyelashes03.png")
LASHES = os.path.join(ROOT, "godot", "art", "people", "head_tex", "heroine_lashes.png")
OUT = os.path.join(ROOT, "tools", "comfy", "out", "heroes", "eyes")
SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 21
SIZE = 2048
# Where each iris is in MakeHuman's paint (its UVs, from the top), and how
# big (measured from the paint: the pupils' middles, the green's reach).
IRISES = [(0.7064, 0.2959), (0.2933, 0.7015)]
IRIS_R = 0.12
PUPIL = 0.28                                   # (of the iris's radius)

PROMPT = ("extreme macro photograph of a single human iris seen straight on, perfectly round and centred, "
          "a vivid deep green iris with a warm golden amber ring around the pupil, intricate radial fibres, crypts "
          "and furrows, a dark green limbal ring at its edge, a round black pupil, razor sharp detail, even soft "
          "light, no reflections, no highlights, no eyelids, no eyelashes")


def guide(n=1024):
    """An iris drawn plainly for Krea to paint over: its pupil, fibres from
    amber to green, a dark ring at its edge, white beyond."""
    img = Image.new("RGB", (n, n), (226, 220, 212))
    d = ImageDraw.Draw(img)
    c, R = n / 2, n * 0.42
    rng = np.random.default_rng(SEED)
    d.ellipse([c - R, c - R, c + R, c + R], fill=(52, 96, 52))
    for _ in range(1600):
        a = rng.uniform(0, 2 * math.pi)
        r0, r1 = R * PUPIL * rng.uniform(1.0, 1.2), R * rng.uniform(0.6, 0.98)
        t = rng.uniform(0, 1)
        col = (int(60 + 120 * (1 - t)), int(110 + 50 * t), int(40 + 20 * t))
        d.line([(c + r0 * math.cos(a), c + r0 * math.sin(a)), (c + r1 * math.cos(a), c + r1 * math.sin(a))], fill=col, width=2)
    d.ellipse([c - R * 0.5, c - R * 0.5, c + R * 0.5, c + R * 0.5], outline=(170, 130, 50), width=int(R * 0.12))
    d.ellipse([c - R, c - R, c + R, c + R], outline=(20, 45, 25), width=int(R * 0.07))
    p = R * PUPIL
    d.ellipse([c - p, c - p, c + p, c + p], fill=(6, 6, 6))
    return img.filter(ImageFilter.GaussianBlur(1.5))


def paint(img):
    """The drawing painted over by Krea 2 (turbo, local)."""
    os.makedirs(OUT, exist_ok=True)
    src = os.path.join(OUT, "iris_drawn.png")
    img.save(src)
    up = comfy.upload(src)
    g = {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "krea2_turbo_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_4b_fp8_scaled.safetensors", "type": "krea2", "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": PROMPT, "clip": ["2", 0]}},
        "5": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["4", 0]}},
        "6": {"class_type": "LoadImage", "inputs": {"image": up}},
        "7": {"class_type": "VAEEncode", "inputs": {"pixels": ["6", 0], "vae": ["3", 0]}},
        "8": {"class_type": "KSampler", "inputs": {"model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["7", 0],
                                                    "seed": SEED, "steps": 8, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple",
                                                    "denoise": 0.62}},
        "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["3", 0]}},
        "10": {"class_type": "SaveImage", "inputs": {"images": ["9", 0], "filename_prefix": "heroine_iris"}},
    }
    got = comfy.run(g, OUT)
    dst = os.path.join(OUT, "iris_painted.png")
    os.replace(got[0], dst)
    return Image.open(dst).convert("RGB")


def compose(iris):
    """Her eyes' whites: MakeHuman's paint at twice the size, each iris
    painted out (the white carried in from round it, at its own angle), its
    alpha (the cornea's clear patch) as it was; and the iris apart, square,
    for the shader to lay wherever she looks."""
    from scipy import ndimage
    src = Image.open(SRC).convert("RGBA").resize((SIZE, SIZE), Image.LANCZOS)
    out = np.asarray(src, np.float32).copy()
    for cx, cy in IRISES:
        r = IRIS_R * SIZE
        x0, y0 = int(cx * SIZE - r * 1.3), int(cy * SIZE - r * 1.3)
        w = int(r * 2.6)
        ys, xs = np.mgrid[y0:y0 + w, x0:x0 + w]
        dx, dy = (xs + 0.5 - cx * SIZE) / r, (ys + 0.5 - cy * SIZE) / r
        rr = np.hypot(dx, dy)
        # (each point inside taken from the white just outside, along its own angle)
        k = 1.12 / np.maximum(rr, 1e-3)
        sx = np.clip(cx * SIZE + dx * r * k, 0, SIZE - 1).astype(int)
        sy = np.clip(cy * SIZE + dy * r * k, 0, SIZE - 1).astype(int)
        white = out[sy, sx, :3]
        white = np.stack([ndimage.gaussian_filter(white[..., c], 3) for c in range(3)], -1)
        m = np.clip((1.1 - rr) / 0.06, 0, 1)[..., None]
        tile = out[y0:y0 + w, x0:x0 + w, :3]
        out[y0:y0 + w, x0:x0 + w, :3] = tile * (1 - m) + white * m
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(DST)
    # The iris: its edge at 0.412 of the square (as the shader reads it); past
    # its edge, its own darkest green (no white to bleed in as it is filtered).
    ir = np.asarray(iris, np.float32).copy()
    n = ir.shape[0]
    yy, xx = np.mgrid[0:n, 0:n]
    rr = np.hypot(xx + 0.5 - n / 2, yy + 0.5 - n / 2) / (n * 0.412)
    edge = ir[(rr > 0.95) & (rr < 1.0)].mean(0)
    ir[rr > 1.0] = edge
    Image.fromarray(np.clip(ir, 0, 255).astype(np.uint8)).save(IRIS)
    print("WRITTEN", DST, "and", IRIS)


def lashes():
    """Her lashes' paint: MakeHuman's (its upper lashes, the top half, as
    they are), its lower lashes (the bottom half) a good deal finer and
    fainter, as lower lashes are, not a dark band under her eyes."""
    from scipy import ndimage
    im = np.asarray(Image.open(LASH_SRC).convert("RGBA"), np.float32)
    h = im.shape[0]
    a = im[..., 3]
    low = np.zeros_like(a, bool)
    low[int(h * 0.54):] = True
    thin = ndimage.grey_erosion(a, size=(1, 2))                  # (each lash narrower)
    a = np.where(low, thin * 0.55, a)
    im[..., 3] = a
    Image.fromarray(np.clip(im, 0, 255).astype(np.uint8)).save(LASHES)
    print("WRITTEN", LASHES)


if __name__ == "__main__":
    lashes()
    # (with IRIS_KEEP set, the iris painted before is laid in again, unpainted)
    kept = os.path.join(OUT, "iris_painted.png")
    compose(Image.open(kept).convert("RGB") if os.environ.get("IRIS_KEEP") and os.path.exists(kept) else paint(guide()))
