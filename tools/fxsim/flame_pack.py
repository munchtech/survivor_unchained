"""Loop, pack and add motion vectors to flame_sim.py's side views, for the flame kit (FlameKit.cs,
shaders/flame_mv.gdshader).

    python tools/fxsim/flame_pack.py preview SIM_DIR OUT.png [--start 60] [--n 24]
    python tools/fxsim/flame_pack.py pack SIM_DIR OUT_PREFIX [--start 60] [--len 64] [--fade 24] [--cw 128] [--ch 256]

pack writes OUT_PREFIX.png (8x8 atlas, grey heat in L, a soft coverage in A, sRGB-encoded), OUT_PREFIX_mv.png
(optical flow from each frame to the next, the last to the first included, as a fraction of the cell: RG around
0.5, times mv_scale in the sidecar) and OUT_PREFIX.json. The loop: frames start..start+len, the `fade` frames after
it cross-faded into its head, so its last frame leads into its first like any two neighbours.
"""
import json
import sys

import cv2
import numpy as np
from PIL import Image


def opts(a, **d):
    i = 0
    while i < len(a):
        k = a[i].lstrip("-")
        d[k] = type(d[k])(a[i + 1])
        i += 2
    return d


def load(sim):
    f = np.load(sim + "/flame.npz")["frames"].astype(np.float32)
    return f[:, ::-1, :]  # top row = the top


def heat(p, k):
    """Projected flame (m of flame through the depth) to 0..1 heat: soft-saturating, so the core rounds off."""
    return 1.0 - np.exp(-p * k)


def main():
    mode, sim, out = sys.argv[1:4]
    o = opts(sys.argv[4:], start=60, n=24, len=64, fade=24, cw=128, ch=256, k=0.0, kk=1.2, vfall=0.55, grid=8, fps=24.0)
    F = load(sim)
    k = o["k"] or o["kk"] / max(np.percentile(F[o["start"]:].max(axis=(1, 2)), 50), 1e-6)
    if mode == "preview":
        sel = F[o["start"]:o["start"] + o["n"]]
        strip = np.concatenate([heat(f, k) for f in sel], axis=1)
        Image.fromarray((np.clip(strip, 0, 1) ** (1 / 2.2) * 255).astype(np.uint8)).save(out)
        print("frames", F.shape, "k", k)
        return
    s, L, K = o["start"], o["len"], o["fade"]
    src = F[s:s + L + K]
    loop = src[:L].copy()
    for i in range(K):
        w = i / K
        loop[i] = (1 - w) * src[L + i] + w * src[i]
    H = heat(loop, k)
    # Fire cools as it climbs: the heat falls off up the flame (from its base, the lowest lit row), so the
    # core is a hot heart low in the tongue and the tip is orange, not white.
    rows = np.nonzero(H.max(axis=(0, 2)) > 0.01)[0]
    base, tip = rows.max(), rows.min()
    up = np.clip((base - np.arange(H.shape[1])) / max(base - tip, 1), 0, 1)
    H *= (1 - o["vfall"] * up ** 1.3)[None, :, None]
    # The crop: the union of every frame's flame, centred on the emitter (the domain's middle), cell's aspect.
    m = H.max(axis=0) > 0.04
    ys, xs = np.nonzero(m)
    cx = H.shape[2] / 2
    half_w = max(cx - xs.min(), xs.max() + 1 - cx) * 1.12
    top, bot = ys.min(), ys.max() + 1
    hgt = (bot - top) * 1.06
    # The cell is stretched to the flame's own width: the card's width over its height is `aspect` (sidecar).
    aspect = 2 * half_w / hgt
    y1 = bot + 2
    y0 = y1 - hgt
    print("crop: %.0f wide x %.0f tall cells of the sim" % (2 * half_w, hgt))
    cells = []
    for f in H:
        M = np.float32([[2 * half_w / o["cw"], 0, cx - half_w], [0, hgt / o["ch"], y0]])
        c = cv2.warpAffine(f, M, (o["cw"], o["ch"]), flags=cv2.INTER_CUBIC | cv2.WARP_INVERSE_MAP,
                           borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        # A soft vignette at the cell's sides and top: nothing reaches its border.
        cells.append(np.clip(c, 0, 1))
    cells = np.stack(cells)
    yy, xx = np.mgrid[0:o["ch"], 0:o["cw"]]
    edge = np.clip(np.minimum.reduce([xx, o["cw"] - 1 - xx, yy]) / 6.0, 0, 1)
    cells *= edge
    enc = (cells ** (1 / 2.2) * 255 + 0.5).astype(np.uint8)
    seam = np.abs(enc[-1].astype(float) - enc[0].astype(float)).mean()
    nb = np.mean([np.abs(enc[i + 1].astype(float) - enc[i].astype(float)).mean() for i in range(L - 1)])
    print("seam (last vs first) %.2f/255; neighbours mean %.2f/255" % (seam, nb))
    G = o["grid"]
    atlas = np.zeros((G * o["ch"], G * o["cw"], 2), np.uint8)
    mv = np.zeros((G * o["ch"], G * o["cw"], 3), np.uint8)
    flows = []
    for i in range(L):
        a, b = enc[i], enc[(i + 1) % L]
        fl = cv2.calcOpticalFlowFarneback(a, b, None, 0.5, 4, 15, 5, 7, 1.5, 0)
        fl[..., 0] /= o["cw"]
        fl[..., 1] /= o["ch"]
        flows.append(fl)
    flows = np.stack(flows)
    sc = float(np.percentile(np.abs(flows), 99.9)) * 1.1
    for i in range(L):
        r, c = divmod(i, G)
        sl = (slice(r * o["ch"], (r + 1) * o["ch"]), slice(c * o["cw"], (c + 1) * o["cw"]))
        atlas[sl + (0,)] = enc[i]
        atlas[sl + (1,)] = (np.clip(cells[i] * 3.0, 0, 1) ** (1 / 2.2) * 255 + 0.5).astype(np.uint8)
        e = np.clip(flows[i] / sc * 0.5 + 0.5, 0, 1)
        mv[sl + (0,)] = (e[..., 0] * 255 + 0.5).astype(np.uint8)
        mv[sl + (1,)] = (e[..., 1] * 255 + 0.5).astype(np.uint8)
    Image.fromarray(atlas, "LA").save(out + ".png", optimize=True)
    Image.fromarray(mv, "RGB").save(out + "_mv.png", optimize=True)
    json.dump({"grid": G, "frames": L, "fps": o["fps"], "cell": [o["cw"], o["ch"]], "aspect": round(float(aspect), 4), "mv_scale": sc,
               "mv": "flow from frame i to i+1 (last to first included) in cell UV, RG = 0.5 + flow / mv_scale / 2;"
                     " +y is down the cell",
               "source": "tools/fxsim/flame_sim.py (Blender Mantaflow, our own) + flame_pack.py",
               "seam_255": round(seam, 2), "neighbour_255": round(nb, 2), "sim": o},
              open(out + ".json", "w"), indent=1)
    print("mv_scale", sc, "wrote", out)


main()
