"""The skills' own sprites (the bodies of what they throw and cast), painted
with Krea 2 on the local ComfyUI on black, and laid into the effects' sprite
array (godot/art/fx/sprites.png, its groups in sprites.json).

    python tools/comfy/fx_sprites.py make [name ...]       # candidates, two seeds each
    python tools/comfy/fx_sprites.py cut NAME=PICK.png ...  # into the array

A candidate lands in tools/comfy/out/fx_sprites/NAME_SEED_0.png. Cutting
takes light from black (alpha from the brightest channel), centres it on its
light, fits it round inside its cell with a soft edge, and refuses any that
would still show light at its border (the same rule as flipbook.py).
"""
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools", "uiforge"))
OUT = os.path.join(ROOT, "tools", "comfy", "out", "fx_sprites")
ART = os.path.join(ROOT, "godot", "art", "fx")

STYLE = ("game visual effect texture, glowing light, centred, isolated on a pure black background, seen from directly "
         "above, symmetrical, crisp, high contrast, nothing else in the image, no text, no frame, no border")

SPRITES = {
    "sun_disc": "a spinning disc of radiant golden holy light, a circular blade of sunlight with sharp rays round its rim "
                "like a sunburst, a white-gold blazing centre",
    "ward_disc": "a round ward of pale silver-blue light, a glowing circle of fine runes round a bright centre, like a "
                 "shield made of moonlight",
    "crescent": "a thin crescent moon of cold silver and lavender light, glowing softly, a little stardust round it",
    "umbral": "an orb of black shadow wreathed in a corona of violet flame tendrils, glowing purple rim round a dark core",
    "wisp": "a tiny will-o'-the-wisp, a bright violet-white spark of magic light in a soft magenta glow with three "
            "tiny orbiting sparkles",
    "rune_ring": "a circle of glowing violet arcane runes and fine geometric lines, a magic sigil, thin bright lines",
    "dawn_sigil": "a golden sigil of the dawn, a circular emblem of a rising sun with long thin rays, thin glowing gold lines",
    "frost_star": "a six-pointed star of pale blue ice crystal, sharp glassy spikes, glittering, a snowflake of light",
    "ember_coal": "a burning ember coal, glowing orange and yellow, small flames licking off it, sparks",
    "blood_drop": "a splash of glowing crimson blood light, a dark red droplet bursting into fine spatter",
}


def make(names):
    from krea import t2i_many
    jobs = []
    for n in names:
        for seed in (1, 2):
            jobs.append((f"{n}_{seed}", f"{SPRITES[n]}, {STYLE}", seed))
    res = t2i_many(jobs, size=(768, 768), lora=0.0, out=OUT, tag="fx", steps=8)
    for k, v in res.items():
        print(k, v)


def cut(pairs):
    meta_path = os.path.join(ART, "sprites.json")
    meta = json.load(open(meta_path))
    size = meta["size"]
    arr = np.asarray(Image.open(os.path.join(ART, "sprites.png")).convert("RGBA"))
    layers = [arr[i * size:(i + 1) * size] for i in range(arr.shape[0] // size)]
    g = (np.arange(size) + 0.5) / size * 2 - 1
    r = np.sqrt(g[None] ** 2 + g[:, None] ** 2)
    edge = np.clip((0.97 - r) / 0.12, 0, 1)
    edge = edge * edge * (3 - 2 * edge)
    for pair in pairs:
        name, path = pair.split("=", 1)
        im = np.asarray(Image.open(path).convert("RGB")).astype(np.float32) / 255
        light = np.clip((im.max(axis=2) - 0.03) / 0.97, 0, 1)
        # Centre on the light, and take a square round it a little wider than it.
        ys, xs = np.nonzero(light > 0.08)
        if ys.size == 0:
            raise SystemExit(f"{name}: nothing brighter than black")
        w = light ** 2
        cy, cx = (w.sum(axis=1) @ np.arange(w.shape[0])) / w.sum(), (w.sum(axis=0) @ np.arange(w.shape[1])) / w.sum()
        half = max(abs(ys - cy).max(), abs(xs - cx).max()) * 1.12
        box = (int(cx - half), int(cy - half), int(cx + half), int(cy + half))
        rgb = Image.fromarray((im * 255).astype(np.uint8)).crop(box).resize((size, size), Image.LANCZOS)
        c = np.asarray(rgb).astype(np.float32) / 255
        a = np.clip((c.max(axis=2) - 0.03) / 0.97, 0, 1) * edge
        # Straight colour, as the pack's sprites are: brightness in red (the shader reads r * a).
        lum = c.max(axis=2) / np.maximum(1e-3, c.max(axis=2).max())
        layer = np.dstack([lum, lum, lum, a])
        border = max(layer[:3, :, 3].max(), layer[-3:, :, 3].max(), layer[:, :3, 3].max(), layer[:, -3:, 3].max())
        if border > 1.5 / 255:
            raise SystemExit(f"{name}: light at its border ({border * 255:.0f}/255)")
        layer = (np.clip(layer, 0, 1) * 255 + 0.5).astype(np.uint8)
        if name in meta["groups"]:
            first, count = meta["groups"][name]
            layers[first] = layer
        else:
            meta["groups"][name] = [len(layers), 1]
            layers.append(layer)
        print(f"{name}: layer {meta['groups'][name][0]}")
    meta["layers"] = len(layers)
    Image.fromarray(np.concatenate(layers, axis=0), "RGBA").save(os.path.join(ART, "sprites.png"))
    json.dump(meta, open(meta_path, "w"), indent=1)
    # The importer must cut the strip into as many layers.
    imp = os.path.join(ART, "sprites.png.import")
    text = open(imp).read()
    import re
    text = re.sub(r"slices/vertical=\d+", f"slices/vertical={len(layers)}", text)
    open(imp, "w").write(text)


if __name__ == "__main__":
    if sys.argv[1] == "make":
        make(sys.argv[2:] or list(SPRITES))
    else:
        cut(sys.argv[2:])
