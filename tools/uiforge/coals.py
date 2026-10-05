"""Self's attribute points as live coals in a small iron dish (the owner: the boxes are "still
ai boxes"): a coal for each point to spend, which UI design moves onto an attribute as it is
spent, its glow the "pending" state. Modelled in Blender (blender_coals.py) under the house
light; the soft ember glow behind a numeral is drawn here.

    python tools/uiforge/coals.py          # into tools/comfy/out/uiforge/coal/, then kit.py --apply

  coal/coal_0..3.png   18x14 shown: a rough dark crust, the fire in its cracks (UI design adds
                       the halo and the breathing)
  coal/dish.png        84x36 shown: the dish seen from above and a little in front
  coal/dish_rim.png    its near rim alone, laid over the coals' feet
  coal/numeral_glow.png  60x60 shown: the warmth behind a numeral a coal has gone into
"""
from __future__ import annotations

import json
import os
import subprocess
import time

import numpy as np
from PIL import Image

import forge as F

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BLENDER = os.environ.get("BLENDER", r"C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe")
OUT = os.path.join(ROOT, "tools", "comfy", "out", "uiforge", "coal")
SPEC = {"ss": 3, "samples": 96, "tilt": 52,
        "coal": {"cell": [36, 28], "size": 22, "variants": 4},
        "dish": {"cell": [168, 72], "rx": 74, "ry": 34, "depth": 24, "wall": 3.0},
        "material": {"iron": "#2e2829", "rust": "#4a2814", "worn": "#e2dce6", "worn_rough": 0.14}}


def render():
    """The coals and the dish, from Blender. A run that fails must not hand back old pictures."""
    raw = os.path.join(OUT, "raw")
    os.makedirs(raw, exist_ok=True)
    for f in os.listdir(raw):
        if f.endswith(".png"):
            os.remove(os.path.join(raw, f))
    sp = os.path.join(raw, "spec.json")
    json.dump(SPEC, open(sp, "w"), indent=1)
    t0 = time.time()
    r = subprocess.run([BLENDER, "-b", "-P", os.path.join(HERE, "blender_coals.py"), "--", sp, raw],
                       capture_output=True, text=True, timeout=3600)
    made = {}
    names = [f"coal_{k}" for k in range(SPEC["coal"]["variants"])] + ["dish", "dish_rim"]
    for nm in names:
        p = os.path.join(raw, nm + ".png")
        if not os.path.exists(p) or os.path.getmtime(p) < t0:
            raise RuntimeError(f"{nm} not rendered:\n" + (r.stdout + r.stderr)[-3000:])
        img = np.asarray(Image.open(p).convert("RGBA"), np.float32) / 255
        cell = SPEC["coal"]["cell"] if nm.startswith("coal") else SPEC["dish"]["cell"]
        # (the shadow faded out before the cell's sides, so no edge of it shows)
        import chain
        made[f"coal/{nm}.png"] = chain.deepen_shadow(F.downsample(img, tuple(cell)), k=1.0, edge=14)
    return made


def numeral_glow(S=60):
    """coal/numeral_glow.png, S shown px square: the warmth a coal leaves behind a numeral, a
    soft orange glow, uneven as embers are, falling to nothing well inside its square."""
    n = S * 2
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    u, v = (xx + 0.5) / n - 0.5, (yy + 0.5) / n - 0.5
    r = np.hypot(u * 1.05, v * 1.2)
    lump = F.fbm(n, n, scale=18, octaves=3, seed=71) * 0.5 + 0.5
    a = np.clip(1 - r / 0.46, 0, 1) ** 2.2 * (0.75 + 0.5 * lump) * 0.55
    core = np.clip(1 - r / 0.22, 0, 1) ** 2
    rgb = (np.array([0.95, 0.38, 0.1], np.float32) * (1 - core[..., None]) + np.array([1.0, 0.7, 0.35], np.float32) * core[..., None])
    return np.dstack([rgb, np.clip(a, 0, 1)]).astype(np.float32)


def build():
    os.makedirs(OUT, exist_ok=True)
    made = render()
    made["coal/numeral_glow.png"] = numeral_glow()
    for rel, img in made.items():
        p = os.path.join(OUT, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        F.save(F.to_pil(np.clip(img, 0, 1)), p)
        print("coal", rel, flush=True)


if __name__ == "__main__":
    build()
