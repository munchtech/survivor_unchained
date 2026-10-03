"""The interface's painted art, from prompt to the file the game loads
(docs/UI_ART_BRIEF.md). Every asset is listed in ui_assets.json with where it
goes, the size of its file and how it is cut; this paints candidates on the
local ComfyUI (Krea 2 turbo with the darkbrush LoRA, graphs/krea_t2i.json),
cuts them out (BiRefNet) and fits the one chosen to its exact size, straight
into godot/art/ui/ where the game picks it up (godot/src/Ui/UiArt.cs).

    python tools/comfy/ui_art.py list                      # every asset, and which are in place
    python tools/comfy/ui_art.py paint ID [--seeds 4] [--prompt "..."]
    python tools/comfy/ui_art.py fit ID CANDIDATE.png      # cut and fit one into place
    python tools/comfy/ui_art.py icon SET KEY "what it shows" [--seeds 4]
    python tools/comfy/ui_art.py fit-icon SET KEY CANDIDATE.png

Candidates land in tools/comfy/out/ui/ID/ (ignored by git). Fitting by kind:
a frame keeps its corners and border thickness and stretches only between
its nine-slice margins (so a square painting becomes a wide button without
fat edges); a strip is cropped and made seamless left to right; a cut piece
(a medallion, a ring, the logo) is cut from its background and centred in
its box. Assets painted on black whose middle must stay open (the focus
ring, dividers) are keyed by their light instead of cut.

Needs Pillow and numpy. The server is http://127.0.0.1:8188 (COMFY_URL).
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
UI = os.path.join(ROOT, "godot", "art", "ui")
OUT = os.path.join(HERE, "out", "ui")
sys.path.insert(0, HERE)
import comfy  # noqa: E402

SPEC = json.load(open(os.path.join(HERE, "ui_assets.json"), encoding="utf-8"))
ASSETS = {a["id"]: a for a in SPEC["assets"]}
# Painted on black and keyed by their light: what must stay see-through in the middle.
LIGHT_KEYED = {"focus", "rule", "flourish"}
# Rings: cut out, then the hole in the middle opened (radius as a share of the half size).
HOLES = {"minimap_frame": 0.835, "ring_art": 0.74}


def paint(prompt, aspect, out_dir, seeds=4, first=4200):
    """Candidates from Krea 2 turbo: the project's graph, its prompt enhancer off."""
    os.makedirs(out_dir, exist_ok=True)
    graph = json.load(open(os.path.join(HERE, "graphs", "krea_t2i.json"), encoding="utf-8"))
    made = []
    for k in range(seeds):
        api = json.loads(json.dumps(graph))
        api["30:24"]["inputs"]["value"] = False
        api["30:3"]["inputs"]["seed"] = first + k
        api["30:19"]["inputs"]["value"] = prompt
        api["49"]["inputs"]["aspect_ratio"] = aspect
        for f in comfy.run(api, out_dir):
            dst = os.path.join(out_dir, f"cand_{first + k}.png")
            os.replace(f, dst)
            made.append(dst)
            print(dst, flush=True)
    return made


def birefnet(path):
    """The thing cut from its background (BiRefNet on the local server): RGBA."""
    name = comfy.upload(path)
    # RemoveBackground gives a mask (the thing white): saved as an image, then made the alpha.
    api = {
        "1": {"class_type": "LoadImage", "inputs": {"image": name}},
        "2": {"class_type": "LoadBackgroundRemovalModel", "inputs": {"bg_removal_name": "birefnet.safetensors"}},
        "3": {"class_type": "RemoveBackground", "inputs": {"bg_removal_model": ["2", 0], "image": ["1", 0]}},
        "4": {"class_type": "MaskToImage", "inputs": {"mask": ["3", 0]}},
        "5": {"class_type": "SaveImage", "inputs": {"images": ["4", 0], "filename_prefix": "ui_cut"}},
    }
    out = comfy.run(api, os.path.join(OUT, "_cut"))
    mask = Image.open(out[0]).convert("L")
    img = Image.open(path).convert("RGB")
    if mask.size != img.size:
        mask = mask.resize(img.size, Image.LANCZOS)
    rgba = img.copy()
    rgba.putalpha(mask)
    os.remove(out[0])
    return rgba


def light_key(img):
    """On black: alpha from how bright it is, colour un-darkened to match (for glows and gold lines)."""
    a = np.asarray(img.convert("RGB"), dtype=np.float32) / 255
    alpha = np.clip(a.max(axis=2) * 1.6, 0, 1)
    rgb = np.where(alpha[..., None] > 0.01, np.clip(a / np.maximum(alpha[..., None], 1e-3), 0, 1), 0)
    return Image.fromarray((np.dstack([rgb, alpha]) * 255).astype(np.uint8), "RGBA")


def bbox_crop(img, pad=0):
    box = img.getchannel("A").point(lambda v: 255 if v > 24 else 0).getbbox()
    if not box:
        return img
    l, t, r, b = box
    return img.crop((max(0, l - pad), max(0, t - pad), min(img.width, r + pad), min(img.height, b + pad)))


def nine(img, size, margins):
    """A frame remade at a size, its corners and border kept at their painted thickness."""
    W, H = size
    # Margins are in shown pixels; the file is twice that.
    l, t, r, b = (m * 2 for m in margins)
    s = min(img.width / W, img.height / H)
    sl, st, sr, sb = (max(1, round(v * s)) for v in (l, t, r, b))
    xs = [0, sl, img.width - sr, img.width]
    ys = [0, st, img.height - sb, img.height]
    xd = [0, l, W - r, W]
    yd = [0, t, H - b, H]
    out = Image.new("RGBA", (W, H))
    for i in range(3):
        for j in range(3):
            src = img.crop((xs[i], ys[j], xs[i + 1], ys[j + 1]))
            w, h = xd[i + 1] - xd[i], yd[j + 1] - yd[j]
            if w > 0 and h > 0 and src.width > 0 and src.height > 0:
                out.paste(src.resize((w, h), Image.LANCZOS), (xd[i], yd[j]))
    return out


def seamless(img, size):
    """A strip cropped to its proportions, its ends cross-faded so it tiles left to right."""
    W, H = size
    n = W // 4
    # A strip a quarter longer than wanted: its overhang is faded into its start,
    # so the first column follows on from the last.
    k = min(img.width / (W + n), img.height / H)
    cw, ch = int((W + n) * k), int(H * k)
    x0, y0 = (img.width - cw) // 2, (img.height - ch) // 2
    a = np.asarray(img.crop((x0, y0, x0 + cw, y0 + ch)).convert("RGBA").resize((W + n, H), Image.LANCZOS), dtype=np.float32)
    w = np.linspace(0, 1, n)[None, :, None]
    out = a[:, :W].copy()
    out[:, :n] = a[:, W:W + n] * (1 - w) + a[:, :n] * w
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")


def fit_box(img, size):
    """Centred in its box, as large as fits, the rest transparent."""
    W, H = size
    img = bbox_crop(img, 2)
    k = min(W / img.width, H / img.height)
    im = img.resize((max(1, int(img.width * k)), max(1, int(img.height * k))), Image.LANCZOS)
    out = Image.new("RGBA", (W, H))
    out.paste(im, ((W - im.width) // 2, (H - im.height) // 2), im)
    return out


def open_hole(img, share):
    a = np.asarray(img, dtype=np.uint8).copy()
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.hypot(xx - w / 2, yy - h / 2) / (min(w, h) / 2)
    soft = np.clip((r - share + 0.015) / 0.03, 0, 1)
    a[..., 3] = (a[..., 3] * soft).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def fit(asset, cand):
    src = Image.open(cand).convert("RGB")
    size, kind = tuple(asset["size"]), asset["kind"]
    if kind == "strip":
        out = seamless(src, size)
    elif asset["id"] in LIGHT_KEYED:
        cut = bbox_crop(light_key(src), 2)
        out = nine(cut, size, asset["margins"]) if kind == "frame" else fit_box(cut, size)
    else:
        cut = birefnet(cand)
        if asset["id"] in HOLES:
            cut = open_hole(bbox_crop(cut), HOLES[asset["id"]])
        out = nine(bbox_crop(cut), size, asset["margins"]) if kind == "frame" else fit_box(cut, size)
    dst = os.path.join(UI, asset["file"])
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    out.save(dst)
    print(f"{asset['id']}: {dst} ({out.width}x{out.height})")


def main():
    args = sys.argv[1:]
    if not args or args[0] == "list":
        for a in SPEC["assets"]:
            there = os.path.exists(os.path.join(UI, a["file"]))
            print(f"{'[x]' if there else '[ ]'} {a['id']:22} {a['file']:34} {a['size'][0]}x{a['size'][1]}  {a['kind']}")
        for name, s in SPEC["icon_sets"].items():
            d = os.path.join(UI, s["dir"])
            n = len([f for f in os.listdir(d) if f.endswith(".png")]) if os.path.isdir(d) else 0
            print(f"    icons/{name}: {n} painted ({s['size'][0]}x{s['size'][1]}, {s['tint']})")
        return
    seeds = int(args[args.index("--seeds") + 1]) if "--seeds" in args else 4
    custom = args[args.index("--prompt") + 1] if "--prompt" in args else None
    if args[0] == "paint":
        a = ASSETS[args[1]]
        style = "" if a.get("style") is False else SPEC["style"] + " "
        paint(style + (custom or a["prompt"]), a["aspect"], os.path.join(OUT, a["id"]), seeds)
    elif args[0] == "fit":
        fit(ASSETS[args[1]], args[2])
    elif args[0] == "icon":
        s = SPEC["icon_sets"][args[1]]
        paint(s["prompt"].format(name=args[3]), "1:1 (Square)", os.path.join(OUT, f"{args[1]}_{args[2]}"), seeds)
    elif args[0] == "fit-icon":
        s = SPEC["icon_sets"][args[1]]
        src = args[3]
        cut = light_key(Image.open(src)) if args[1] == "glyph" else birefnet(src)
        out = fit_box(cut, tuple(s["size"]))
        if args[1] == "glyph":
            # Value art: the light kept as white, so the code's colour reads true.
            a = np.asarray(out, dtype=np.float32)
            lum = a[..., :3].max(axis=2, keepdims=True)
            a[..., :3] = np.clip(lum * 1.15, 0, 255)
            out = Image.fromarray(a.astype(np.uint8), "RGBA")
        dst = os.path.join(UI, s["dir"], f"{args[2]}.png")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        out.save(dst)
        print(dst)
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
