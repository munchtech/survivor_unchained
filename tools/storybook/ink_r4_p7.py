"""Storybook 3 ink round 4 (sequence judge r1): p7 as one tall drawing the camera tilts through, p7u patches.

    python tools/storybook/ink_r4_p7.py gen          # GPU: ink_jobs/r4_p7.json (p7t, 8 seeds) -> out/ink_r4_p7/
    python tools/storybook/ink_r4_p7.py sheet        # CPU: out/ink_r4_p7/p7t_sheet.jpg (all seeds, small)
    python tools/storybook/ink_r4_p7.py sam <seed>   # GPU: SAM 3 masks on the pick -> _work/p7t_s<seed>_<what>.png
    python tools/storybook/ink_r4_p7.py p7u          # GPU: p7u inpaints (the cage in the bright patch, clean bubble clumps)
    python tools/storybook/ink_r4_p7.py p7u_apply <cage seed> <bubble seed>   # CPU: out/ink_r4_p7/p7u_r4.png
Then `ink_layers.py masks p7 p7u`, `fills p7 p7u` (GPU), `build p7 p7u`.
"""
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ink_layers as L  # noqa: E402

OUT = os.path.join(HERE, "out", "ink_r4_p7")
SAMS = {"person": ("hooded person", 0.3), "flask": ("flask", 0.3), "hand": ("hand holding the flask", 0.3),
        "cage": ("small iron cage with blue fire", 0.3), "holder": ("arm and hand reaching down from above", 0.25),
        "stones": ("wet stones", 0.3)}

# p7u (gen px of ink_r3/p7u_s47): the bright surface patch's middle (the cage goes in) and the two clumps that read
# as melted skulls (plus the one cut by the bottom edge)
P7U_CAGE_BOX = (760, 0, 1160, 352)
P7U_CLUMPS = [(1080, 610, 1380, 820), (650, 850, 900, 1050), (960, 990, 1210, 1088)]
P7U_CAGE = ("Underwater at night, looking straight up from below at the rippling bright underside of a black river's surface. "
            "Seen through the bright water, just above the surface, the dark warped silhouette of a small crude cage of a "
            "few black iron bars, bent and broken by the ripples, and inside it a small cold pale blue fire, a bright "
            "blue-white core. Carved woodcut lines, black and deep green-black ink, cold pale blue light.")
P7U_BUBBLES = ("Underwater at night, black-green murky water: a loose cluster of round air bubbles rising, each bubble a "
               "clean simple carved pale ring or small round dot, different sizes, black water between them, nothing "
               "else. Carved woodcut lines, black and deep green-black ink, cold pale blue-white bubbles.")


def gen():
    subprocess.check_call([sys.executable, os.path.join(HERE, "ink_gen.py"), os.path.join(HERE, "ink_jobs", "r4_p7.json"), OUT])


def sheet():
    fs = sorted(f for f in os.listdir(OUT) if f.startswith("p7t_s") and f.endswith(".png"))
    tw = 288
    th = round(tw * 1536 / 1152)
    S = Image.new("RGB", (tw * 4 + 12, (th + 4) * ((len(fs) + 3) // 4)), (20, 20, 20))
    for i, f in enumerate(fs):
        im = Image.open(os.path.join(OUT, f)).convert("RGB").resize((tw, th), Image.LANCZOS)
        ImageDraw.Draw(im).text((4, 4), f[4:-4], fill=(255, 230, 120))
        S.paste(im, ((i % 4) * (tw + 4), (i // 4) * (th + 4)))
    S.save(os.path.join(OUT, "p7t_sheet.jpg"), quality=85)


def sam(seed):
    import ink_comfy as C
    src = os.path.join(OUT, f"p7t_s{seed}.png")
    for k, (text, th) in SAMS.items():
        C.sam(src, text, os.path.join(L.WORK, f"p7t_s{seed}_{k}.png"), th)
        print(k, flush=True)


def _crop_inpaint(base, box, mask, prompt, seed, tag, denoise, scale=2):
    import ink_comfy as C
    x0, y0, x1, y1 = box
    w, h = (x1 - x0) * scale, (y1 - y0) * scale
    w, h = w - w % 16, h - h % 16
    ip, mp = L.wd("p7u", f"_in_{tag}.png"), L.wd("p7u", f"_mk_{tag}.png")
    Image.fromarray(base[y0:y1, x0:x1]).resize((w, h), Image.LANCZOS).save(ip)
    Image.fromarray((mask[y0:y1, x0:x1] * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR).save(mp)
    raw = L.wd("p7u", f"raw_{tag}_s{seed}.png")
    C.krea(prompt, w, h, seed, raw, init=ip, denoise=denoise, mask=None)     # whole-crop img2img, kept inside the mask
    L.composite_back(ip, raw, mp).resize((x1 - x0, y1 - y0), Image.LANCZOS).save(L.wd("p7u", f"x_{tag}_s{seed}.png"))


def p7u_masks():
    base = np.asarray(Image.open(os.path.join(HERE, "out", "ink_r3", "p7u_s47.png")).convert("RGB"))
    H, W = base.shape[:2]
    Y, X = np.mgrid[0:H, 0:W]
    x0, y0, x1, y1 = P7U_CAGE_BOX
    cx, cy = (x0 + x1) / 2, 150
    cage = (((X - cx) / 150) ** 2 + ((Y - cy) / 150) ** 2) <= 1
    clumps = np.zeros((H, W), bool)
    lum = base.astype(np.float32).mean(-1) / 255
    for a, b, c, d in P7U_CLUMPS:
        box = np.zeros((H, W), bool)
        box[b:d, a:c] = True
        clumps |= nd.binary_dilation(box & (lum > 0.3), iterations=14) & box
    clumps = nd.binary_closing(clumps, iterations=8)
    return base, cage.astype(np.float32), nd.gaussian_filter(clumps.astype(np.float32), 3) * nd.binary_dilation(clumps, iterations=4)


def p7u(seeds=(11, 23, 47, 202)):
    base, cage, clumps = p7u_masks()
    for s in seeds:
        _crop_inpaint(base, P7U_CAGE_BOX, nd.gaussian_filter(cage, 4), P7U_CAGE, s, "cage", 0.78)
        for j, box in enumerate(P7U_CLUMPS):
            _crop_inpaint(base, box, clumps, P7U_BUBBLES, s, f"clump{j}", 0.9)
        print("p7u", s, flush=True)
    # a small sheet: per seed the cage crop and the clumps
    rows = []
    for s in seeds:
        cells = [Image.open(L.wd("p7u", f"x_cage_s{s}.png"))] + [Image.open(L.wd("p7u", f"x_clump{j}_s{s}.png"))
                                                                  for j in range(len(P7U_CLUMPS))]
        hh = 200
        cells = [c.convert("RGB").resize((round(c.width * hh / c.height), hh)) for c in cells]
        r = Image.new("RGB", (sum(c.width + 4 for c in cells), hh), (20, 20, 20))
        x = 0
        for c in cells:
            r.paste(c, (x, 0))
            x += c.width + 4
        ImageDraw.Draw(r).text((4, 4), f"s{s}", fill=(255, 230, 120))
        rows.append(r)
    S = Image.new("RGB", (max(r.width for r in rows), sum(r.height + 4 for r in rows)), (20, 20, 20))
    y = 0
    for r in rows:
        S.paste(r, (0, y))
        y += r.height + 4
    S.save(L.wd("p7u", "r4_patches.jpg"), quality=85)


def p7u_apply(cage_seed, bubble_seed):
    base, cage, clumps = p7u_masks()
    out = base.astype(np.float32)
    x0, y0, x1, y1 = P7U_CAGE_BOX
    patch = np.asarray(Image.open(L.wd("p7u", f"x_cage_s{cage_seed}.png")).convert("RGB")).astype(np.float32)
    m = nd.gaussian_filter(cage, 4)[y0:y1, x0:x1, None]
    out[y0:y1, x0:x1] = out[y0:y1, x0:x1] * (1 - m) + patch * m
    for j, (a, b, c, d) in enumerate(P7U_CLUMPS):
        patch = np.asarray(Image.open(L.wd("p7u", f"x_clump{j}_s{bubble_seed}.png")).convert("RGB")).astype(np.float32)
        m = clumps[b:d, a:c, None]
        out[b:d, a:c] = out[b:d, a:c] * (1 - m) + patch * m
    Image.fromarray((out + 0.5).astype(np.uint8)).save(os.path.join(OUT, "p7u_r4.png"))


def load_layers(plate):
    """layers.json -> ink_build.render's layer dicts (target px)."""
    import json
    meta = json.load(open(os.path.join(L.OUT, plate, "layers.json"), encoding="utf-8"))
    up = meta["units_per_px"]
    out = []
    for e in meta["layers"]:
        a = np.asarray(Image.open(os.path.join(L.OUT, plate, e["file"])).convert("RGBA")).astype(np.float32) / 255
        out.append(dict(name=e["name"], file=e["file"], z=e["z"], blend=e["blend"], state=e["state"], rgba=a,
                        x0=round(e["pos"][0] / up), y0=round(e["pos"][1] / up)))
    return meta, out


def straight_edges(meta, layers):
    """A layer whose alpha is still up on its own crop's border (not the plate's edge) shows a straight cut."""
    W, H = meta["image_px"]
    bad = []
    for d in layers[1:]:
        a = d["rgba"][..., 3]
        h, w = a.shape
        sides = {"top": (a[0], d["y0"] > 0), "bottom": (a[-1], d["y0"] + h < H),
                 "left": (a[:, 0], d["x0"] > 0), "right": (a[:, -1], d["x0"] + w < W)}
        for k, (row, inside) in sides.items():
            if inside and row.max() > 0.05:
                bad.append(f"{d['file']}:{k} {row.max():.2f}")
    return bad


def keys_sheet(frames, path, extra=None):
    """frames: [(label, cam, {layer file: opacity})] -> one half-size sheet with the 2.39 bars drawn."""
    import ink_build as B
    meta, layers = load_layers("p7")
    P = B.Plate("p7")
    cells = []
    for lab, cam, ops in frames:
        ls = []
        for d in layers:
            k = ops.get(d["file"], 1.0)
            if k <= 0:
                continue
            ls.append(dict(d, rgba=np.dstack([d["rgba"][..., :3], d["rgba"][..., 3] * k])))
        ls[0]["valid"] = np.ones(ls[0]["rgba"].shape[:2], bool)
        rgb, bad = B.render(P, sorted(ls, key=lambda d: -d["z"]), cam, 640, 360)
        band = np.abs((np.arange(360) + 0.5 - 180) / 180) <= L.BAND
        rgb[~band] = 0
        im = B.to_im(rgb)
        B.label(im, f"{lab} unfilled {int((bad[band] > 0.5).sum())}px")
        cells.append(im)
    cols = 2
    S = Image.new("RGB", (cols * 644, ((len(cells) + 1) // cols) * 364 + (extra.height + 4 if extra else 0)), (20, 20, 20))
    for i, c in enumerate(cells):
        S.paste(c, ((i % cols) * 644, (i // cols) * 364))
    if extra:
        S.paste(extra, (0, ((len(cells) + 1) // cols) * 364))
    S.save(path, quality=85)
    return straight_edges(meta, layers)


if __name__ == "__main__":
    a = sys.argv[1]
    if a == "gen":
        gen()
    elif a == "sheet":
        sheet()
    elif a == "sam":
        sam(int(sys.argv[2]))
    elif a == "p7u":
        p7u()
    elif a == "p7u_apply":
        p7u_apply(int(sys.argv[2]), int(sys.argv[3]))
