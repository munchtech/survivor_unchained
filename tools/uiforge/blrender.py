"""Run blender_frames.py on a spec (a dict or a JSON file) and return the render as
float RGBA (0..1, straight alpha), at the spec's file size (area-filtered down
from the supersampled render).
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile

import numpy as np
from PIL import Image

import forge as F

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BLENDER = os.environ.get("BLENDER", r"C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe")
CACHE = os.path.join(ROOT, "tools", "comfy", "out", "uiforge", "blender")


def render(spec, name):
    os.makedirs(CACHE, exist_ok=True)
    sp = os.path.join(CACHE, name + ".json")
    out = os.path.join(CACHE, name + ".png")
    json.dump(spec, open(sp, "w", encoding="utf-8"), indent=1)
    r = subprocess.run([BLENDER, "-b", "-P", os.path.join(HERE, "blender_frames.py"), "--", sp, out],
                       capture_output=True, text=True, timeout=1200)
    if not os.path.exists(out) or "Traceback" in r.stdout + r.stderr:
        raise RuntimeError((r.stdout + r.stderr)[-3000:])
    img = np.asarray(Image.open(out).convert("RGBA"), np.float32) / 255
    W, H = spec["size"]
    if img.shape[1] != W:
        img = F.downsample(img, (W, H))
    return img, out
