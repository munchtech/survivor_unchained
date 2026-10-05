"""The lamp-iron in the interface: one, hung by a short chain from a page's head band, a live
coal in its cage ("Lamps are lit. Stay where they reach."), its light falling on the page
below it, brightening when a level is gained. Modelled in Blender (blender_lamp.py).

    python tools/uiforge/lamp.py           # into tools/comfy/out/uiforge/lamp/, then kit.py --apply

  lamp/lamp.png       the lamp at rest, 120x200 shown, its chain running up off its top edge's middle
                      (draw it under the head band, so the chain goes up behind the rail)
  lamp/lamp_lit.png   the same, its coal blown bright (cross-fade to it on a level gained)
  lamp/light.png      the light it throws on the page, 600x600 shown, its source at the middle:
                      laid under everything on the page, additively, scaled by how lit it is
"""
from __future__ import annotations

import json
import os
import subprocess
import time

import cv2
import numpy as np
from PIL import Image

import forge as F

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BLENDER = os.environ.get("BLENDER", r"C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe")
OUT = os.path.join(ROOT, "tools", "comfy", "out", "uiforge", "lamp")
SPEC = {"cell": [240, 400], "ss": 3, "samples": 128,
        "material": {"iron": "#262122", "rust": "#3a2012", "worn": "#e2dce6", "worn_rough": 0.14},
        "cage": {"y": 270, "h": 130, "r": 40, "bars": 6, "bar": 3.4},
        "chain": {"links": 8, "length": 38, "width": 23, "wire": 3.8}, "heat": [10, 28]}


def render():
    raw = os.path.join(OUT, "raw")
    os.makedirs(raw, exist_ok=True)
    for f in os.listdir(raw):
        if f.endswith(".png"):
            os.remove(os.path.join(raw, f))
    sp = os.path.join(raw, "spec.json")
    json.dump(SPEC, open(sp, "w"), indent=1)
    t0 = time.time()
    r = subprocess.run([BLENDER, "-b", "-P", os.path.join(HERE, "blender_lamp.py"), "--", sp, raw],
                       capture_output=True, text=True, timeout=3600)
    made = {}
    for nm in ("lamp", "lamp_lit"):
        p = os.path.join(raw, nm + ".png")
        if not os.path.exists(p) or os.path.getmtime(p) < t0:
            raise RuntimeError(f"{nm} not rendered:\n" + (r.stdout + r.stderr)[-3000:])
        img = np.asarray(Image.open(p).convert("RGBA"), np.float32) / 255
        img = F.downsample(img, tuple(SPEC["cell"]))
        import chain
        img = soften_shadow(img)
        img = chain.deepen_shadow(img, k=1.0, edge=12)
        made[f"lamp/{nm}.png"] = chain.ember_glow(img, 1.3 if nm == "lamp" else 2.0, edge=12)
    return made


def soften_shadow(img, sigma=10.0, k=0.55):
    """The cage stands off the page, so the house light throws its shadow far and hard; on a
    page that reads as a black block. Keep the shadow, but spread and fainter, as lamplight
    from the coal itself would wash it out."""
    rgb, a = img[..., :3], img[..., 3]
    lum = rgb @ np.array([0.3, 0.59, 0.11], np.float32)
    shade = ((lum < 0.03) & (a < 0.98)).astype(np.float32)
    sh = cv2.GaussianBlur(a * shade, (0, 0), sigma) * k
    body = a * (1 - shade)
    out_a = body + sh * (1 - body)
    out_rgb = (rgb * body[..., None] + np.zeros(3, np.float32) * (sh * (1 - body))[..., None]) / np.maximum(out_a[..., None], 1e-4)
    return np.dstack([out_rgb, out_a]).astype(np.float32)


def light(W=600, H=600, sx=300, sy=300):
    """lamp/light.png: the lamp's warmth on the page, strongest just under it and falling away
    as light does (inverse square, softened), a little uneven where the cage's bars cut it."""
    w, h = W, H                                       # made at shown size: nothing sharp in it
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dx, dy = xx - sx, (yy - sy) * 1.15
    d = np.hypot(dx, dy)
    fall = 1 / (1 + (d / 70.0) ** 2)
    edge = np.clip(1 - d / (min(W, H) * 0.49), 0, 1) ** 1.5
    ang = np.arctan2(dy, dx)
    bars = 0.88 + 0.12 * np.cos(ang * 6)              # the cage's six bars, barely
    a = np.clip(fall * edge * bars * 0.55, 0, 1)
    rgb = np.broadcast_to(np.array([1.0, 0.56, 0.22], np.float32), (h, w, 3))
    img = np.dstack([rgb, a]).astype(np.float32)
    return cv2.resize(img, (W * 2, H * 2), interpolation=cv2.INTER_CUBIC).clip(0, 1)


def build():
    made = render()
    made["lamp/light.png"] = light()
    for rel, img in made.items():
        p = os.path.join(OUT, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        F.save(F.to_pil(np.clip(img, 0, 1)), p)
        print("lamp", rel, flush=True)


if __name__ == "__main__":
    build()
