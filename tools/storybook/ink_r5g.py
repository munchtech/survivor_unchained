"""Storybook 4 round 5g, G2 (paste): the ChatGPT drowned (C1) cut, posted and stood in the ditch water of a Krea plate.

    python tools/storybook/ink_r5g.py gpu      # SAM the plate's own figures, Krea inpaint empty ditches, BiRefNet C1 (gpu turn)
    python tools/storybook/ink_r5g.py cut      # C1 -> one posted RGBA per figure (out/ink_r5g/fig_*.png)
    python tools/storybook/ink_r5g.py place    # stand them in the ditches -> out/ink_r5g/g2_<seed>.png (+ posted) + seams
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
G = os.path.join(HERE, "out", "ink_r5g")
R5 = os.path.join(HERE, "out", "ink_r5")
PLATE = "p5r5bw_s11"            # the base Krea plate (r5b: varied cages, wagon on its side, carved ground)
EMPTY_SEEDS = (7, 23)
CLUMPS = [(20, 573, 330, 830), (520, 720, 850, 1060), (1610, 485, 2030, 745)]   # gen px: the plate's own figure clumps
EMPTY = ("Along both sides of the road run ditches of black water, empty: black water carved in short horizontal strokes, "
         "frosted reeds at their edges, carved snow banks, nobody, no figures, no people.")


def gpu():
    import ink_comfy as C
    import ink_layers as IL
    src = os.path.join(R5, PLATE + ".png")
    m = os.path.join(G, "_sam_people.png")
    if not os.path.exists(m):
        C.sam(src, "person", m, threshold=0.3)
    mk = np.asarray(Image.open(m).convert("L")) > 127      # SAM finds ~0.5% here: add the dark shapes in the figure clumps
    im = np.asarray(Image.open(src).convert("RGB")).astype(np.float32).mean(-1) / 255
    for x0, y0, x1, y1 in CLUMPS:
        sub = np.zeros_like(mk)
        sub[y0:y1, x0:x1] = im[y0:y1, x0:x1] < 0.28
        mk |= sub
    mk = nd.binary_closing(mk, iterations=4)
    mk = nd.binary_dilation(mk, iterations=12)
    mp = os.path.join(G, "_mask_people.png")
    Image.fromarray((mk * 255).astype(np.uint8)).save(mp)
    spec = json.load(open(os.path.join(HERE, "ink_jobs", "r5b_p5.json"), encoding="utf-8"))
    p = spec["jobs"][0]["prompt"]
    a = p.index("Along both sides of the road run ditches")
    b = p.index("The snow and the ground are carved")
    prompt = (spec["prefix"] + " " + p[:a] + EMPTY + " " + p[b:].split(" The whole scene sits")[0] + " " + spec["style"]).strip()
    for s in EMPTY_SEEDS:
        dst = os.path.join(G, f"empty_s{s}.png")
        if not os.path.exists(dst):
            raw = os.path.join(G, f"_raw_empty_s{s}.png")
            C.krea(prompt, 2048, 1088, s, raw, init=src, denoise=1.0, mask=mp)
            IL.composite_back(src, raw, mp).save(dst)
            print(dst, flush=True)
    c1 = os.path.join(G, "_C1_matte.png")
    if not os.path.exists(c1):
        C.birefnet(os.path.join(G, "_C1.png"), c1)
    print("gpu done")


S = 3600 / 2048                     # gen px -> posted px
# Ditch centrelines in gen px (read off empty_s7), (x, y) top (by the ford) -> bottom; width grows with nearness.
DITCH = {"L": [(625, 537), (410, 778), (246, 1024)], "R": [(1260, 537), (1638, 778), (1966, 1024)]}
DW = (51, 184)                      # ditch width at the top / bottom (gen px)


def figures():
    """C1's ten figures: (rgb float, alpha float) crops, each with its stray hair/weed bits."""
    im = np.asarray(Image.open(os.path.join(G, "_C1.png")).convert("RGB")).astype(np.float32) / 255
    a = np.asarray(Image.open(os.path.join(G, "_C1_matte.png")).convert("L")).astype(np.float32) / 255
    lab, n = nd.label(a > 0.5)
    objs = nd.find_objects(lab)
    big = [o for o in objs if o[0].stop - o[0].start > 300]
    out = []
    for o in sorted(big, key=lambda o: o[1].start):
        y0, y1, x0, x1 = max(0, o[0].start - 15), o[0].stop + 2, max(0, o[1].start - 15), o[1].stop + 15
        al = a[y0:y1, x0:x1].copy()
        al = np.clip((al - 0.25) / 0.5, 0, 1)          # full opacity inside, a 1-2 px edge
        out.append((im[y0:y1, x0:x1], al))
    return out


def ditch_point(side, t):
    p = np.array(DITCH[side], np.float32)
    seg = np.clip(t * 2, 0, 1.999)
    i = int(seg)
    f = seg - i
    return p[i] * (1 - f) + p[i + 1] * f


def h_gen(t):
    return 80 + 380 * t ** 1.2                       # full figure height at this distance (gen px)


def slots(seed):
    """Clumps and gaps along both ditches: (side, t, across, flip, lean, fig index). Members of a clump stand a body
    width apart along the ditch (never merged into one blob); clumps are 1-4, the gaps between them uneven."""
    rng = np.random.default_rng(seed)
    out = []
    for side in "LR":
        t = 0.04 + rng.uniform(0, 0.04)
        while t < 0.72:
            k = rng.choice([1, 2, 2, 3, 3, 4])
            tt = t
            for j in range(k):
                if tt > 0.74:
                    break
                out.append((side, tt, (1 if j % 2 else -1) * rng.uniform(0.1, 0.32), bool(rng.integers(2)),
                            float(rng.choice([0, 0, 0, 0, -6, 5])), int(rng.integers(10))))
                tt += 0.36 * h_gen(tt) / 650 * rng.uniform(0.35, 0.7)
            t = tt + rng.uniform(0.02, 0.07) * (1 + 0.6 * t)
    return sorted(out, key=lambda s: s[1])


def place(seed=3, base="empty_s7"):
    import ink_post as IP
    import ink_r5 as R
    R.R5 = G
    R.post_night([base])
    plate = np.asarray(Image.open(os.path.join(G, "posted", base + "_nc.png")).convert("RGB")).astype(np.float32) / 255
    out = plate.copy()
    H, W = out.shape[:2]
    figs = figures()
    used = [0] * len(figs)
    rings = Image.new("L", (W, H), 0)
    dr = ImageDraw.Draw(rings)
    rng = np.random.default_rng(seed + 100)
    sl = slots(seed)
    figs_out = []
    for side, t, across, flip, lean, fi in sl:
        # spread the ten figures evenly
        fi = int(np.argmin([u + (0.5 if i != fi else 0) for i, u in enumerate(used)]))
        used[fi] += 1
        rgb, al = figs[fi]
        cx, wy = ditch_point(side, t)
        cx += across * (DW[0] + (DW[1] - DW[0]) * t)
        hg = h_gen(t)
        cut = rng.uniform(0.80, 0.86)                      # the waterline: shins and feet under
        fh = rgb.shape[0]
        top = rgb[:int(fh * cut)]
        ta = al[:int(fh * cut)]
        sc = hg * S / fh
        tw, th = max(2, round(top.shape[1] * sc)), max(2, round(top.shape[0] * sc))
        ti = Image.fromarray((top * 255).astype(np.uint8)).resize((tw, th), Image.LANCZOS)
        ai = Image.fromarray((ta * 255).astype(np.uint8)).resize((tw, th), Image.LANCZOS)
        if flip:
            ti, ai = ti.transpose(Image.FLIP_LEFT_RIGHT), ai.transpose(Image.FLIP_LEFT_RIGHT)
        if lean:
            ti = ti.rotate(lean, resample=Image.BICUBIC, expand=True, center=(tw / 2, th))
            ai = ai.rotate(lean, resample=Image.BICUBIC, expand=True, center=(tw / 2, th))
        tw2, th2 = ti.size
        x0, y0 = round(cx * S - tw2 / 2), round(wy * S - th2)
        if x0 < 0 or y0 < 0 or x0 + tw2 > W or y0 + th2 > H:
            continue
        # a solid black silhouette (C1's scratch detail averages to grey at plate size): the black ink, posted
        # two-tone: C1's own light gaps (between arm and body, strands of hair) kept as navy, the rest the black ink
        lum = np.asarray(ti.convert("L")).astype(np.float32) / 255
        gap = nd.binary_opening(nd.gaussian_filter(lum, 0.8) > 0.6, iterations=1)
        base_ = np.where(gap[..., None], IP.PAL[list(IP.INKS).index("navy")], IP.PAL[0])
        f = IP.post(base_.astype(np.float32), offset=(x0, y0), light="cold")
        a2 = np.asarray(ai).astype(np.float32) / 255
        # a sliver of cold rim on the edges that face up toward the fires (hair, shoulders), carved hard, never a glow
        gy = nd.sobel(a2, axis=0)
        edge = np.clip(a2 - nd.grey_erosion(a2, size=(3, 3)), 0, 1)
        rim = np.clip(0.35 + gy / (np.abs(gy).max() + 1e-6) * 3, 0, 1) * edge
        rim = (rim > 0.35).astype(np.float32) * a2
        f = f * (1 - rim[..., None] * 0.7) + IP.PAL[list(IP.INKS).index("cage")] * 0.8 * rim[..., None] * 0.7
        figs_out.append((y0, x0, th2, tw2, f, a2[..., None]))
        # the ripple ring at the waterline: two broken carved ellipses
        rw = tw * 0.62
        wyp = wy * S
        for k, (gro, wid) in enumerate(((1.0, 3), (1.45, 2))):
            ex, ey = rw * gro, rw * gro * 0.16
            for a0 in range(0, 360, 40):
                if rng.random() < 0.3:
                    continue
                dr.arc((cx * S - ex, wyp - ey, cx * S + ex, wyp + ey), a0, a0 + rng.uniform(18, 32),
                       fill=int(235 - 70 * k), width=max(2, round(wid * (0.6 + t))))
    ring = np.asarray(rings).astype(np.float32)[..., None] / 255
    ink = IP.PAL[list(IP.INKS).index("snow")] * 1.15
    out = out * (1 - ring) + ink * ring          # the rings first: each figure covers its ring's back half
    for y0, x0, th2, tw2, f, a in figs_out:
        out[y0:y0 + th2, x0:x0 + tw2] = out[y0:y0 + th2, x0:x0 + tw2] * (1 - a) + f * a
    dst = os.path.join(G, f"g2_{base}_k{seed}.png")
    IP.save(out, dst)
    print(dst, len(sl), "figures")
    return dst, plate, out


def seams(dst_out, plate, out):
    """ink_r3's straight-edge scan on the composite vs its empty plate, framed at the 4 camera-path keys."""
    import ink_r3 as R3
    import ink_r5 as R
    name = os.path.basename(dst_out)[:-4]
    for t, x, y, z, _ in R.p5_keys(name):
        w, h = 3200 / z, 1800 / z
        box = tuple(round(v) for v in (x - w / 2, y - h / 2, x + w / 2, y + h / 2))
        bar = round(1080 * (1 - R.BAND) / 2)
        fr = [np.asarray(Image.fromarray((q * 255 + 0.5).astype(np.uint8)).crop(box).resize((1920, 1080), Image.LANCZOS))
              .astype(np.float32)[bar + 2:1080 - bar - 2, 2:-2] / 255 for q in (out, plate)]
        n, best, runs = R3.seam_runs(fr[0] - fr[1], matte=True)
        print(f"seams {name} t={t} zoom {z}: straight edges >= 40 px: {n}, longest {best}", runs[:3])


if __name__ == "__main__":
    a = sys.argv[1]
    if a == "gpu":
        gpu()
    elif a == "place":
        d, p, o = place(int(sys.argv[2]) if len(sys.argv) > 2 else 3)
        seams(d, p, o)
