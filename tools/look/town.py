"""The town kit's one command (L1 W2 town, C4/R8: LOOK_BIBLE rules 5, 6, 8, 9, 10; MB3 SETTS, PLASTER & BEAMS, STONE, ROOF).

    python tools/look/town.py setts|houses|roofs|all [--no-mesh]

setts   tools/look/ground_paint.py build setts + check (ground.json's "setts" surface and set: coursed chunky setts).
houses  (1) tools/assets/env_house.py (the wall pieces; thicker timbers: its BEAM_K) unless --no-mesh; (2) the walls'
        trim sheet painted here from nothing (house_albedo.jpg, house_normal.png, house_aux.png; house_atlas.json's
        regions kept, so env_house.py's UVs and P9's sets still fit); (3) godot/data/house_look.json's tints and
        weathering from godot/data/look/town.json's "house_look" (the photo-era grime, mottle, lost plaster off: rule 9).
roofs   (1) tools/assets/env_roof.py unless --no-mesh; (2) the roof trim sheet (roof_albedo.jpg, roof_normal.png,
        roof_aux.png; roof_atlas.json kept); (3) house_look.json's roof tints and weathering (town.json).
The sheets tile per region (a trim sheet is a tile, as the setts are, not a prop's own UV layout, so the painter is
ground_paint.py's family: chunky planes, a lit bevel to the light, a cool darker bevel and joint; one color per block
varied +-spread_L; nothing under 3 cm). Every color is a class's paint.albedo.mid in godot/data/look/materials.json
(hand-set, the arithmetic in its "w2" line) times a region's hand gain in town.json (its FROM there). Deterministic.
"""
import json, os, subprocess, sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
from paint_core import srgb_to_lin, lin_to_srgb, lin_to_oklab, oklab_to_lin  # noqa: E402

DATA = os.path.join(ROOT, "godot", "data", "look", "town.json")
LIB = os.path.join(ROOT, "godot", "data", "look", "materials.json")
HOUSE = os.path.join(ROOT, "godot", "art", "world", "house")
LOOK = os.path.join(ROOT, "godot", "data", "house_look.json")
LIGHT = np.array([-0.45, -0.89]) / np.hypot(0.45, 0.89)  # (ground.json's painted-in light: from the top, a little left)
SPREAD = 0.05


def hexlab(h): return lin_to_oklab(srgb_to_lin(np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)])))


def pnoise(H, W, cells, rng):
    """A periodic smooth noise, about `cells` blobs across the longer side (FFT low-pass), -1..1."""
    f = np.fft.fft2(rng.standard_normal((H, W)))
    k = np.hypot(np.fft.fftfreq(H)[:, None] * H, np.fft.fftfreq(W)[None, :] * W) * max(H, W) / max(H, W)
    x = np.fft.ifft2(f * np.exp(-(k / max(cells, 0.5)) ** 2)).real
    return x / (np.abs(x).max() + 1e-9)


def blocks(H, W, ppm, c, rng):
    """Courses of rounded-rectangle blocks (setts, rubble, brick, tiles, boards), periodic both ways: the block id per
    pixel, the signed distance to its edge (px, < 0 inside), its local x, y and half extents, the count."""
    nr = max(int(round(H / ppm * 100 / c["row_cm"])), 1)
    rh = rng.uniform(1 - c.get("row_jit", 0), 1 + c.get("row_jit", 0), nr); rb = np.concatenate([[0], np.cumsum(rh / rh.sum() * H)])
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)
    row = np.clip(np.searchsorted(rb, yy, side="right") - 1, 0, nr - 1)
    nst = max(int(round(W / ppm * 100 / c["len_cm"])), 1)
    sid = np.zeros((H, W), np.int64); px = np.zeros((H, W)); hx = np.zeros((H, W))
    for r in range(nr):
        ln = rng.uniform(1 - c.get("len_jit", 0), 1 + c.get("len_jit", 0), nst); cb = np.concatenate([[0], np.cumsum(ln / ln.sum() * W)])
        off = (c.get("bond", 0.5) * (r % 2) + rng.uniform(-1, 1) * c.get("off_jit", 0.2)) * W / nst
        k = row == r
        lx = (xx[k] - off) % W
        j = np.clip(np.searchsorted(cb, lx, side="right") - 1, 0, nst - 1)
        sid[k] = r * nst + j; px[k] = lx - (cb[j] + cb[j + 1]) * 0.5; hx[k] = (cb[j + 1] - cb[j]) * 0.5
    py = yy - (rb[row] + rb[row + 1]) * 0.5; hy = (rb[row + 1] - rb[row]) * 0.5
    jh, rad = c["joint_cm"] / 100 * ppm * 0.5, c["corner_cm"] / 100 * ppm
    wob = pnoise(H, W, max(W, H) / ppm * 100 / c["len_cm"] * 1.5, rng) * c.get("wobble_cm", 0) / 100 * ppm * 0.5
    qx, qy = np.abs(px) - (hx - jh - rad), np.abs(py) - (hy - jh - rad)
    d = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - rad + wob
    return sid, d, px, py, hx, hy, nr * nst


def ss(x):
    t = np.clip((x - 0.2) / 0.6, 0, 1); return t * t * (3 - 2 * t)


def paint_region(H, W, ppm, reg, base, rng):
    """One region: flat (a color in two or three big flat masses) or blocks (each one color, a tilted top, lit and cool
    bevels, joints), plus optional long strokes along x (wood grain as a few strokes). Returns rgb, height, rough, id."""
    labs = [lin_to_oklab(np.clip(oklab_to_lin(base) * np.array(g), 0, 1)) for g in reg.get("gains", [[1, 1, 1]])]
    o = np.zeros((H, W, 3)); hgt = np.full((H, W), 0.6); tid = np.full((H, W), 0.5)
    if "blocks" in reg:
        c = reg["blocks"]
        sid, d, px, py, hx, hy, n = blocks(H, W, ppm, c, rng)
        pick = rng.integers(0, len(labs), n); dl = rng.uniform(-1, 1, n) * SPREAD * c.get("vary", 0.9)
        tilt = rng.uniform(-1, 1, (n, 2))
        o[:] = np.array(labs)[pick][sid]
        o[..., 0] += dl[sid] + (tilt[sid, 0] * px / np.maximum(hx, 1) + tilt[sid, 1] * py / np.maximum(hy, 1)) * SPREAD * c.get("tilt", 0.5)
        stone = d < 0; e = -d; bev = c["bevel_cm"] / 100 * ppm
        gy, gx = np.gradient(d); gl = np.maximum(np.hypot(gx, gy), 1e-6)
        facing = -(gx / gl * LIGHT[0] + gy / gl * LIGHT[1])
        w = np.sqrt(1 - np.clip(e / bev, 0, 1)) * (stone & (e < bev))
        lit = c.get("lit", 0.06)
        o[..., 0] += lit * ss(facing) * w - lit * 0.8 * ss(-facing) * w
        o[..., 2] -= 0.012 * ss(-facing) * w
        if c.get("under", 0):  # (a course's lap: the course above throws a cool band over the top of the one below)
            rowpos = (py + hy) / np.maximum(2 * hy, 1)
            o[..., 0] -= c["under"] * (1 - np.clip(rowpos / c.get("under_w", 0.25), 0, 1)) * stone
        jl = lin_to_oklab(np.clip(oklab_to_lin(base) * np.array(c["joint"]), 0, 1))
        o = np.where(stone[..., None], o, jl)
        hgt = np.where(stone, 0.55 + 0.45 * (1 - np.clip(1 - e / bev, 0, 1) ** 2), 0.1)
        tid = np.where(stone, (sid % 32 + 0.5) / 32, 0.0)
    else:
        o[:] = labs[0]
        m = pnoise(H, W, reg.get("mass_cells", 3), rng)
        o[..., 0] += np.round(m * 1.5) / 1.5 * SPREAD * reg.get("mass", 0.4)  # (two or three flat masses, not a gradient)
    yy, xx = np.mgrid[0:H, 0:W]
    for st in reg.get("strokes", []):  # (long strokes along x: a beam's few lines of grain, MB3 PLASTER & BEAMS, WOOD)
        for _ in range(st["n"]):
            y = rng.uniform(0, H); wpx = max(st["w_cm"] / 100 * ppm, 3 / 100 * ppm); L = rng.uniform(*st["len_m"]) * ppm; x0 = rng.uniform(0, W)
            dx = (xx - x0) % W
            band = (np.abs(((yy - y + H / 2) % H) - H / 2) < wpx / 2) & (dx < L)
            o[..., 0] += np.where(band, st["dL"], 0.0)
    rgb = lin_to_srgb(oklab_to_lin(o.reshape(-1, 3))).reshape(H, W, 3)
    return rgb, hgt, np.full((H, W), reg.get("rough", 1.0)), tid


def normals(hgt, ppm, amp=0.02):
    from scipy import ndimage
    hb = ndimage.gaussian_filter(hgt, 0.025 * ppm, mode="wrap")
    du = (np.roll(hb, -1, 1) - np.roll(hb, 1, 1)) * 0.5 * amp * ppm
    dv = (np.roll(hb, -1, 0) - np.roll(hb, 1, 0)) * 0.5 * amp * ppm
    n = np.stack([-du, dv, np.ones_like(du)], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n * 0.5 + 0.5


def sheet(name, T, lib):
    S = T["sheets"][name]
    meta = json.load(open(os.path.join(HOUSE, S["atlas"])))
    N, ppm = meta["size"], meta["ppm"]
    alb = np.zeros((N, N, 3)); nrm = np.full((N, N, 3), 0.5); nrm[..., 2] = 1; aux = np.zeros((N, N, 3)); nums = {}
    for i, (rn, reg) in enumerate(S["regions"].items()):
        u0, v0, u1, v1 = meta["regions"][rn]["uv"]
        x0, y0, x1, y1 = (int(round(t * N)) for t in (u0, v0, u1, v1))
        base = hexlab(lib["classes"][reg["class"]]["paint"]["albedo"]["mid"])
        rgb, hgt, rough, tid = paint_region(y1 - y0, x1 - x0, ppm, reg, base, np.random.default_rng(7100 + 31 * i))
        alb[y0:y1, x0:x1] = rgb; nrm[y0:y1, x0:x1] = normals(hgt, ppm)
        aux[y0:y1, x0:x1, 0] = reg["tint_class"]; aux[y0:y1, x0:x1, 1] = rough; aux[y0:y1, x0:x1, 2] = tid
        lab = lin_to_oklab(srgb_to_lin(rgb.reshape(-1, 3)))
        nums[rn] = {"class": reg["class"], "L50": round(float(np.median(lab[:, 0])), 3), "C50": round(float(np.median(np.hypot(lab[:, 1], lab[:, 2]))), 3)}
    to8 = lambda x: Image.fromarray((np.clip(x, 0, 1) * 255 + 0.5).astype(np.uint8))
    to8(alb).save(os.path.join(HOUSE, S["albedo"]), quality=95, subsampling=0)
    to8(nrm).save(os.path.join(HOUSE, S["normal"])); to8(aux).save(os.path.join(HOUSE, S["aux"]))
    json.dump({"by": "tools/look/town.py (L1 W2 town)", "from": S["from"], "regions": nums}, open(os.path.join(HOUSE, f"{name}_paint.json"), "w", newline="\n"), indent=1)
    print(name, json.dumps(nums))


def house_look(keys, T):
    d = json.load(open(LOOK, encoding="utf-8"))
    for k in keys:
        d[k] = T["house_look"][k]
    d["_w2"] = T["house_look"]["_from"]
    json.dump(d, open(LOOK, "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False)


def run(*a): subprocess.run([sys.executable, *a], check=True, cwd=ROOT)


def build(kind, mesh=True):
    T = json.load(open(DATA, encoding="utf-8")); lib = json.load(open(LIB, encoding="utf-8"))
    if kind == "setts":
        run(os.path.join(HERE, "ground_paint.py"), "build", "setts"); run(os.path.join(HERE, "ground_paint.py"), "check", "setts")
    elif kind == "houses":
        if mesh: run(os.path.join(ROOT, "tools", "assets", "env_house.py"))
        sheet("house", T, lib); house_look(T["house_look"]["walls_keys"], T)
    elif kind == "roofs":
        if mesh: run(os.path.join(ROOT, "tools", "assets", "env_roof.py"))
        sheet("roof", T, lib); house_look(T["house_look"]["roof_keys"], T)


if __name__ == "__main__":
    a = sys.argv[1:]
    which = [x for x in a if not x.startswith("--")] or ["all"]
    for k in (["setts", "houses", "roofs"] if which == ["all"] else which):
        build(k, "--no-mesh" not in a)
