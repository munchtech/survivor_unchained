"""The Drowned Girl HUD, piece 2 (UI 17): her hair runs out as the river, and the river is the bar.

    python tools/uiforge/dg_river_cut.py [--check out.png]

Source: the owner's picked concept's own bar (UI 16 d1v, Krea 2 turbo seed 5071, its BiRefNet cut; provenance
tools/comfy/ui_assets.json "hud_direction_drowned_girl_d1v"), the part right of the concept's girl, at the
concept's scale (0.615 source px -> 1080 px), shifted DX right of the concept's place (the in-game figure is
wider than the concept's). The six seats' hair-bound rings are d1b seeds 5040-5042 (mirrored as the concept did).
Copies of the sources: survivorsunchained_inputs/ui17_dg_src/.

The join: the river is drawn UNDER her figure (art/ui/lamp_life/drowned/lamp_cold.png, read here, never written).
Where her figure is solid it hides the river; right of her back hair's contour the river shows, so the strands
come out of her hair and run on as the river. Above the JOIN line (near her) the river fades out, so no second mass of
hair stands behind her head. Re-run this if her figure's contour changes.

The Flare's eddy: its painted glass is cut out (a hole, r FLARE_R at 1080) for the live glass under it (piece 4:
a coal). The crest (where piece 3's gold XP thread runs) is the river's top contour between XP_X, smoothed.

Writes godot/art/ui/dg_river/: river.png (2x), ring_0..5.png and well_0..5.png (2x), river_geo.json (1080 px).
"""
import json
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dg_figure_cut import STRAND_GAIN, bronze_pass, strand_pass  # noqa: E402

WT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = r"C:\Users\munch\Desktop\survivorsunchained_inputs\ui17_dg_src"
OUT = os.path.join(WT, "godot", "art", "ui", "dg_river")
FIG = os.path.join(WT, "godot", "art", "ui", "lamp_life", "drowned")

S = 0.615                     # source px -> 1080 px (the concept's)
DX = 40                       # right of the concept's place
OX, OY = 356 - 42 * S + DX, 815 - 34 * S   # the source's (0, 0) on the 1080 screen (the concept: piece (356, 815), bbox (42, 34))
X_FROM = 300                  # source columns left of this are the concept's girl (the rest of her is hidden under the in-game figure)
# (1080 px) near her, the river shows only under this line. ui17 A (the owner circled the swept-back lock over the XP's
# left end, "can probably just go"): the line drops to the bar's top, so her back hair falls straight into the bar
JOIN = [(600, 946), (636, 952), (660, 962), (700, 971), (760, 977), (820, 980), (880, 983)]
# ui17 A ("a little tighter"): the bar sinks BAR_SINK px from her hair to the flat run before the eddy, tapering to
# nothing over SINK_TAPER (1080 x) so the eddy (the Flare's glass) and the seats' centres stay where they are
BAR_SINK = 6.0
SINK_TAPER = (1372, 1432)
GOLD = (1837.6, 312.6, 93.3)  # the eddy's painted glass in the source (cx, cy, r)
SEAT_PITCH, SEAT_D, SEAT_Y = 82, 78, 1031
SEAT_MID = 958 + DX
RINGS = [(5040, False), (5042, False), (5041, True), (5040, True), (5042, True), (5041, False)]
XP_X = (668 + DX, 1392 + DX)
DRAUGHT = (675 + DX + 4, 1024)
DASH = (SEAT_MID + SEAT_PITCH * 2.5 + 76, 1024)
GRADE = dict(value=0.80, sat=0.86, gamma=1.06)
# ui17 A: painted patches over the cut (Krea 2 turbo masked inpaints of this cut + her figure, BiRefNet alpha; the
# scripts and seeds in survivorsunchained_inputs/ui17_dg_src/patches/README.txt): (name, box at 1080 px). Each is
# river_patch_NAME.png (RGBA, 2x: the river there) and river_patch_NAME_w.png (its blend weight).
#   j: her hair's fall into the bar, a clean sculpted top where the circled lock was cut
#   c: 2-3 crests on the flat run from the dash to the eddy (the judge: "reads as a ladle handle")
PATCHES = [("j", (584, 904, 944, 1044)), ("c", (1256, 924, 1456, 1024))]
# UI 18 (round 3's fixes: the crest left of the centre "flat and ruler-straight ... reads as a machined edge", cut there
# for the old XP line): two low swells rolling right, painted here by lifting the river's own crest band column by
# column (its highlight and grooves follow the new curve; the lift fades to nothing 18 px below the crest). (cx, h, w),
# 1080 px: a long rounded back over w, a rounded front over 0.45 w. Krea inpaints were tried (ui18 r3, 12 candidates
# at 0.40-0.64): they made domed clumps, not its neighbours' long swells. Stays inside SWELL_BOX.
SWELLS = [(912, 10.0, 40.0), (984, 8.0, 38.0)]
SWELL_BASE = 987.0
SWELL_BOX = (850, 924, 1030, 1024)


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def swells(L):
    """SWELLS on the 2x screen layer L (premultiplied RGBA), in place."""
    x0, y0, x1, y1 = SWELL_BOX
    sl = np.s_[y0 * 2:y1 * 2, x0 * 2:x1 * 2]
    C = L[sl].astype(np.float32)
    H, W = C.shape[:2]
    Y, X = np.mgrid[:H, :W].astype(np.float32)
    xs = x0 + (np.arange(W) + 0.5) / 2
    lift = np.zeros(W, np.float32)
    for cx, h, w in SWELLS:
        t = (xs - cx) / w
        back = np.sin(np.pi / 2 * np.clip(1 + t, 0, 1)) ** 1.5
        front = np.sqrt(np.clip(1 - (t / 0.45) ** 2, 0, 1))
        lift = np.maximum(lift, h * np.where(t < 0, back, front) * (t > -1) * (t < 0.45))
    lift = cv2.GaussianBlur(lift.reshape(1, -1), (0, 0), 3).ravel()
    fall = np.clip(1 - (y0 + (Y + 0.5) / 2 - (SWELL_BASE - 2)) / 18.0, 0, 1)
    dy = (lift[None, :] * fall * 2).astype(np.float32)
    L[sl] = np.clip(cv2.remap(C, X, Y + dy, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE), 0, 1)


def grade(rgb):
    """The figure's grade (dg_figure_cut.py): warm bronze, highlights toward old gold, the verdigris deepened."""
    R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    lum = (0.3 * R + 0.59 * G + 0.11 * B)[..., None]
    g = lum + (rgb - lum) * GRADE["sat"]
    g = np.clip(g, 0, 1) ** GRADE["gamma"] * GRADE["value"]
    gl = (0.3 * g[..., 0] + 0.59 * g[..., 1] + 0.11 * g[..., 2])[..., None]
    hi = np.clip((gl - 0.30) / 0.35, 0, 1)
    g = g * (1 + hi * np.array([0.16, 0.04, -0.14]))
    green = np.clip((G - R) * 6.0 + 0.2, 0, 1)[..., None] * (1 - hi)
    g = g * (1 - green) + g * np.array([0.62, 0.86, 0.84]) * green
    return np.clip(g, 0, 1)


def load(name):
    rgb = np.asarray(Image.open(os.path.join(SRC, f"{name}_cand_{SEED_OF[name]}.png")).convert("RGB")).astype(np.float32) / 255
    a = np.asarray(Image.open(os.path.join(SRC, f"{name}_cut_{SEED_OF[name]}.png")).convert("RGBA"))[..., 3].astype(np.float32) / 255
    return rgb, a


SEED_OF = {"d1v": 5071}


def figure_alpha_2x():
    """Her figure's alpha on the 2x screen (its quad's top left and size from lamp_geo.json)."""
    geo = json.load(open(os.path.join(FIG, "lamp_geo.json")))
    fa = np.asarray(Image.open(os.path.join(FIG, "lamp_cold.png")).convert("RGBA"))[..., 3].astype(np.float32) / 255
    at = geo["at"]
    F = np.zeros((2160, 3840), np.float32)
    x0, y0 = int(round(at[0] * 2)), int(round(at[1] * 2))
    h, w = fa.shape
    F[y0:y0 + h, x0:x0 + w] = fa[:2160 - y0, :3840 - x0]
    return F


def river():
    rgb, a = load("d1v")
    a = a.copy()
    a[:, :X_FROM] = 0
    g = grade(rgb)
    # the eddy's glass: a hole for the live glass
    cx, cy, r = GOLD
    yy, xx = np.mgrid[:a.shape[0], :a.shape[1]].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    a = a * smooth(r - 2.0, r + 0.5, d)
    # to 2x screen px
    k = 2 * S
    W2, H2 = int(round(a.shape[1] * k)), int(round(a.shape[0] * k))
    pre = np.dstack([g * a[..., None], a])
    big = cv2.resize(pre, (W2, H2), interpolation=cv2.INTER_LANCZOS4)
    big = np.clip(big, 0, 1)
    # (a light unsharp, as the concept's scale_piece)
    blur = cv2.GaussianBlur(big, (0, 0), 1.2)
    big = np.clip(big + (big - blur) * 0.45, 0, 1)
    ox2, oy2 = int(round(OX * 2)), int(round(OY * 2))
    L = np.zeros((2160, 3840, 4), np.float32)
    y1, x1 = min(2160, oy2 + H2), min(3840, ox2 + W2)
    L[oy2:y1, ox2:x1] = big[:y1 - oy2, :x1 - ox2]
    # the bar sinks (a vertical shift by column, tapered off before the eddy)
    Yg, Xg = np.mgrid[:2160, :3840].astype(np.float32)
    dy = 2 * BAR_SINK * (1 - smooth(2 * SINK_TAPER[0], 2 * SINK_TAPER[1], Xg))
    L = cv2.remap(L, Xg, Yg - dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    # the join: hidden left of her back hair's contour (it is under her there), faded out above JOIN_Y near her
    F = figure_alpha_2x()
    cxs = np.zeros(2160, np.float32)
    for y in range(2160):
        c = np.nonzero(F[y] > 0.9)[0]
        cxs[y] = c.max() if len(c) else 0
    Y, X = np.mgrid[:2160, :3840].astype(np.float32)
    side = smooth(cxs[:, None] - 28, cxs[:, None] + 12, X)
    side = np.where(cxs[:, None] > 0, side, 1.0)
    jx, jy = zip(*JOIN)
    line = 2 * np.interp(X[0] / 2, jx, jy)[None, :]
    top = np.maximum(smooth(line - 6, line + 8, Y), smooth(2 * jx[-1] - 20, 2 * jx[-1], X))
    vis = np.where(F > 0.97, 1.0, side * top)
    L[..., 3] *= vis
    L[..., :3] *= vis[..., None]
    for name, (x0, y0, x1, y1) in PATCHES:
        f = os.path.join(SRC, "patches", f"river_patch_{name}.png")
        if not os.path.exists(f):
            print(f"(no patch {name})")
            continue
        P = np.asarray(Image.open(f).convert("RGBA"), np.float32) / 255
        w = np.asarray(Image.open(f.replace(".png", "_w.png")).convert("L"), np.float32)[..., None] / 255
        pre = np.dstack([P[..., :3] * P[..., 3:], P[..., 3:]])
        sl = np.s_[y0 * 2:y1 * 2, x0 * 2:x1 * 2]
        L[sl] = L[sl] * (1 - w) + pre * w
    swells(L)
    # crop to its bbox (even, so the 1x position is whole)
    ys, xs = np.nonzero(L[..., 3] > 1 / 255)
    bx0, by0 = (xs.min() // 2) * 2, (ys.min() // 2) * 2
    bx1, by1 = ((xs.max() + 2) // 2) * 2, 2160
    L = L[by0:by1, bx0:bx1]
    col = np.where(L[..., 3:] > 1e-4, L[..., :3] / np.maximum(L[..., 3:], 1e-4), 0)
    # (ui17 A) the bronze pass, as on her figure (2x screen px: 0.86 of her source's)
    col = bronze_pass(np.clip(col, 0, 1), L[..., 3], scale=0.86)
    col = strand_pass(col, L[..., 3], np.ones(col.shape[:2], np.float32), scale=0.86, gain=STRAND_GAIN)
    img = Image.fromarray((np.dstack([np.clip(col, 0, 1), L[..., 3]]) * 255 + 0.5).astype(np.uint8), "RGBA")
    return img, (int(bx0 // 2), int(by0 // 2))


def ring(seed, mirror, D):
    """A hair-bound bronze ring (d1b), graded as the river, its hole opened, D px across at 1080 (art at 2x)."""
    rgb = np.asarray(Image.open(os.path.join(SRC, f"d1b_cand_{seed}.png")).convert("RGB")).astype(np.float32) / 255
    a = np.asarray(Image.open(os.path.join(SRC, f"d1b_cut_{seed}.png")).convert("RGBA"))[..., 3].astype(np.float32) / 255
    g = grade(rgb)
    ys, xs = np.nonzero(a > 20 / 255)
    g, a = g[ys.min():ys.max() + 1, xs.min():xs.max() + 1], a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = a.shape
    lum = g.max(axis=2)
    cx, cy = w / 2, h / 2
    rs = []
    for t in np.linspace(0, 2 * np.pi, 72, endpoint=False):
        for rr in np.arange(5, min(w, h) / 2, 1.0):
            x, y = int(cx + rr * np.cos(t)), int(cy + rr * np.sin(t))
            if lum[y, x] > 0.12:
                rs.append(rr)
                break
    hole = float(np.median(rs))
    yy, xx = np.mgrid[:h, :w].astype(np.float32)
    a = a * smooth(hole - 1.5, hole + 1.5, np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2))
    if mirror:
        g, a = g[:, ::-1], a[:, ::-1]
    s = 2 * D / max(w, h)
    pre = np.dstack([g * a[..., None], a])
    n = int(round(max(w, h) * s))
    sq = np.zeros((max(w, h), max(w, h), 4), np.float32)
    oy, ox = (max(w, h) - h) // 2, (max(w, h) - w) // 2
    sq[oy:oy + h, ox:ox + w] = pre
    big = np.clip(cv2.resize(sq, (n, n), interpolation=cv2.INTER_AREA), 0, 1)
    blur = cv2.GaussianBlur(big, (0, 0), 1.0)
    big = np.clip(big + (big - blur) * 0.5, 0, 1)
    col = np.where(big[..., 3:] > 1e-4, big[..., :3] / np.maximum(big[..., 3:], 1e-4), 0)
    img = Image.fromarray((np.dstack([np.clip(col, 0, 1), big[..., 3]]) * 255 + 0.5).astype(np.uint8), "RGBA")
    return img, hole * s / 2  # the hole's radius at 1080


def well(hole_r):
    """The seat's well (2x): dark river glass, a soft dome light high on the left, dark at its foot."""
    rr = hole_r + 2
    n = int(np.ceil(rr * 2)) * 2
    yy, xx = np.mgrid[:n, :n].astype(np.float32)
    nx, ny = (xx + 0.5) / n * 2 - 1, (yy + 0.5) / n * 2 - 1
    r = np.sqrt(nx * nx + ny * ny)
    base = np.array([0.035, 0.065, 0.07], np.float32)
    col = base[None, None, :] * (0.55 + 0.6 * (1 - np.clip(r, 0, 1)[..., None]) ** 0.6)
    hl = np.exp(-(((nx + 0.38) / 0.42) ** 2 + ((ny + 0.45) / 0.26) ** 2))
    col += hl[..., None] * np.array([0.10, 0.14, 0.15], np.float32) * 0.6
    a = smooth(1.0, 0.96, r)
    img = Image.fromarray((np.dstack([np.clip(col, 0, 1), a]) * 255 + 0.5).astype(np.uint8), "RGBA")
    return img, n / 2  # its size at 1080


def crest(img, at):
    """The river's top contour between XP_X (1080 px), smoothed: piece 3's gold thread runs on it."""
    al = np.asarray(img.getchannel("A")).astype(np.float32) / 255
    xs = np.arange(XP_X[0], XP_X[1] + 1)
    ys = []
    for x in xs:
        c = al[:, int((x - at[0]) * 2)]
        idx = np.nonzero(c > 0.6)[0]
        idx = idx[idx / 2 + at[1] >= 940]
        ys.append(at[1] + idx.min() / 2 if len(idx) else 1000)
    ys = np.clip(np.array(ys, np.float32), 970, 1000)
    ys = cv2.GaussianBlur(ys.reshape(1, -1), (0, 0), 22).ravel() + 4.0
    pts = [[float(x), round(float(y), 1)] for x, y in zip(xs[::8], ys[::8])]
    if pts[-1][0] != float(xs[-1]):
        pts.append([float(xs[-1]), round(float(ys[-1]), 1)])
    return pts


def build():
    os.makedirs(OUT, exist_ok=True)
    img, at = river()
    img.save(os.path.join(OUT, "river.png"))
    geo = {"at": [at[0], at[1]], "size": [img.width / 2, img.height / 2]}
    seats = []
    for i, (seed, mir) in enumerate(RINGS):
        rimg, hole = ring(seed, mir, SEAT_D)
        rimg.save(os.path.join(OUT, f"ring_{i}.png"))
        wimg, wh = well(hole)
        wimg.save(os.path.join(OUT, f"well_{i}.png"))
        seats.append({"x": SEAT_MID + (i - 2.5) * SEAT_PITCH, "y": SEAT_Y, "ring": rimg.width / 2, "hole": round(float(hole), 2), "well": float(wh)})
    geo["seats"] = seats
    geo["seat_d"] = SEAT_D
    fx, fy = OX + GOLD[0] * S, OY + GOLD[1] * S
    geo["flare"] = [round(fx, 2), round(fy, 2), round(GOLD[2] * S, 2)]
    geo["draught"] = list(DRAUGHT)
    geo["dash"] = list(DASH)
    pts = crest(img, at)
    geo["crest"] = pts
    al = np.asarray(img.getchannel("A")).astype(np.float32) / 255
    rows = np.nonzero(al[:, int((XP_X[0] - at[0]) * 2):int((XP_X[1] - at[0]) * 2)].max(axis=1) > 0.5)[0]
    geo["bar_top"] = round(float(at[1] + rows.min() / 2), 1)
    geo["river_top"] = round(float(at[1] + np.nonzero(al.max(axis=1) > 0.5)[0].min() / 2), 1)
    json.dump(geo, open(os.path.join(OUT, "river_geo.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in geo.items() if k not in ("crest", "seats")}))
    return geo


def check(path, geo):
    """A rough preview over the concept's plate: river, her figure, the rings and wells (no glyphs)."""
    plate = Image.open(os.path.join(SRC, "plate.png")).convert("RGBA").resize((3840, 2160), Image.LANCZOS)
    plate.alpha_composite(Image.open(os.path.join(OUT, "river.png")), (int(geo["at"][0] * 2), int(geo["at"][1] * 2)))
    fg = json.load(open(os.path.join(FIG, "lamp_geo.json")))
    plate.alpha_composite(Image.open(os.path.join(FIG, "lamp_cold.png")), (int(round(fg["at"][0] * 2)), int(round(fg["at"][1] * 2))))
    for i, s in enumerate(geo["seats"]):
        w = Image.open(os.path.join(OUT, f"well_{i}.png"))
        plate.alpha_composite(w, (int(round(2 * s["x"] - w.width / 2)), int(round(2 * s["y"] - w.height / 2))))
        rg = Image.open(os.path.join(OUT, f"ring_{i}.png"))
        plate.alpha_composite(rg, (int(round(2 * s["x"] - rg.width / 2)), int(round(2 * s["y"] - rg.height / 2))))
    plate = plate.resize((1920, 1080), Image.BOX)
    plate.crop((0, 780, 1920, 1080)).save(path)


if __name__ == "__main__":
    g = build()
    if "--check" in sys.argv:
        check(sys.argv[sys.argv.index("--check") + 1], g)
