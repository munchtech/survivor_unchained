"""The marks a blow leaves on the ground, painted by Krea 2 on the local
ComfyUI (graphs/krea_t2i.json) and keyed into decals for BattleFx: each an
albedo with alpha and an emission map.

    python tools/comfy/marks.py <out dir> [name ...]

A mark is painted alone on flat white (a dark mark: scorch, cracks) or on
black (a mark of light: frost, a sigil), then keyed: alpha from how far a
pixel stands from the ground it was painted on, the colour recovered from
under that, and what burns (embers, glowing runes) lifted into the emission.
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SIZE = 512

FRAME = ("Game decal texture, orthographic top-down view looking straight down, a single mark centred in the "
         "frame with a ragged irregular edge that fades out, nothing else, no shadow, photoreal, highly detailed. ")
ON_WHITE = " Isolated on a pure flat white background."
ON_BLACK = " Isolated on a pure flat black background."

MARKS = {
    # name: (prompt, ground, seed)
    "scorch": ("A round scorch mark burned into dry earth by an explosion, charred black centre, radial soot streaks "
               "thrown outward, cracked ash, a few glowing orange embers in the cracks.", "white", 41),
    "crack": ("A heavy impact crater in hard packed earth: a shallow round dent with deep radial cracks running "
              "outward, broken plates of dirt, loose pebbles and dust.", "white", 42),
    "blight": ("A patch of rotten black-purple corruption seeping into the ground, veins of dark ichor spreading "
               "outward like roots, oily sheen, dead withered grass.", "white", 43),
    "frost": ("A round bloom of frost and ice crystals spreading across the ground, delicate feathery frost fronds "
              "branching outward, glittering pale blue ice, cold mist.", "black", 44),
    "sigil": ("A circle of burning golden holy light seared into the ground: concentric rings of glowing runes and "
              "sacred geometry, radiant, luminous gold lines.", "black", 45),
    "runes": ("A circle of glowing violet arcane runes etched into the ground, intricate magical sigils and rings, "
              "luminous magenta and purple lines.", "black", 46),
    "roots": ("A ring of glowing green spectral roots and vines bursting through the ground, luminous emerald moss "
              "and sprouting leaves of light.", "black", 47),
}


def paint(name, out_dir):
    text, ground, seed = MARKS[name]
    prompt = FRAME + text + (ON_WHITE if ground == "white" else ON_BLACK)
    tmp = os.path.join(out_dir, f"_{name}")
    subprocess.run([sys.executable, os.path.join(HERE, "comfy.py"), "run", os.path.join(HERE, "graphs", "krea_t2i.json"),
                    "--set", "30:24.value=false", "--set", f"30:3.seed={seed}",
                    "--set", f"30:19.value={json.dumps(prompt)}", "--out", tmp], check=True)
    made = [f for f in os.listdir(tmp) if f.endswith(".png")][0]
    src = os.path.join(tmp, made)
    img = Image.open(src).convert("RGB")
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)
    return img, ground


def key(img, ground):
    c = np.asarray(img.resize((SIZE, SIZE), Image.LANCZOS)).astype(np.float32) / 255.0
    if ground == "white":
        # How far from white, in its most departed channel; the colour
        # recovered from under the white it was laid over.
        a = np.clip((1.0 - c.min(axis=2)) * 1.25, 0, 1)
        rgb = np.where(a[..., None] > 1e-3, (c - (1 - a[..., None])) / np.maximum(a[..., None], 1e-3), 0)
    else:
        a = np.clip(c.max(axis=2) * 1.3, 0, 1)
        rgb = np.where(a[..., None] > 1e-3, c / np.maximum(a[..., None], 1e-3), 0)
    rgb = np.clip(rgb, 0, 1)
    # Round: nothing reaches the edge of the square.
    y, x = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)
    r = np.hypot(x - SIZE / 2, y - SIZE / 2) / (SIZE / 2)
    edge = np.clip((1 - r) / 0.25, 0, 1)
    a = a * edge * edge * (3 - 2 * edge)
    # What burns: saturated and bright (embers, runes, glints).
    hi = c.max(axis=2)
    sat = (hi - c.min(axis=2)) / np.maximum(hi, 1e-3)
    if ground == "white":
        burn = np.clip((sat - 0.45) * 3, 0, 1) * np.clip((c[..., 0] - 0.45) * 3, 0, 1)
    else:
        burn = np.clip((hi - 0.25) * 1.6, 0, 1)
    emit = c * burn[..., None] * a[..., None]
    return rgb, a, emit


def main():
    out = sys.argv[1]
    want = sys.argv[2:] or list(MARKS)
    os.makedirs(out, exist_ok=True)
    for name in want:
        img, ground = paint(name, out)
        img.save(os.path.join(out, f"{name}_source.jpg"), quality=92)
        rgb, a, emit = key(img, ground)
        Image.fromarray((np.dstack([rgb, a]) * 255 + 0.5).astype(np.uint8), "RGBA").save(os.path.join(out, f"{name}.png"))
        Image.fromarray((np.clip(emit, 0, 1) * 255 + 0.5).astype(np.uint8), "RGB").save(os.path.join(out, f"{name}_emit.png"))
        print(name, flush=True)


if __name__ == "__main__":
    main()
