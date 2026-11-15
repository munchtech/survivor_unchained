"""The den floor's meso layer (den round 9, floor lane): the things you can name at the play camera, painted from nothing.

    python tools/look/den_floor_paint.py build   -> godot/art/dungeon/den/meso_albedo.png (2 layers, RGBA: an object's colour,
                                                    its coverage with its cast shadow), meso_aux.png (4 layers, linear),
                                                    meso_preview.jpg, meso.json (version, inputs hash)
    python tools/look/den_floor_paint.py check   -> refuses a stale or hand-touched output

FROM den_room.png and den_boss.png (the owner, 15 Nov: "Yes, build"): their floor is a material at three scales; this paints
the middle one (0.05-1.5 m), at the size it reads in our frame (about 73 px a metre):
  albedo 0  stones: flat stones and pebbles (a shade plane, a lit top toward the light, a small cast shadow), earth clods
  albedo 1  litter: dry leaves in clusters (a lit half, a thin shadow), twigs (lit edge, shadow), root fragments
  aux 0, 1  r: each object's rank (0..1, one value over the object and its shadow): the floor shader shows an object where
            its rank is under the place's density (a macro mask), so density follows the floor's masses and nothing is cut
  aux 2     packed-earth plates: r the value multiplier / 2 (a lit edge on the light's side, a dark crevice beyond the far
            side, each plate its own step of value), g the plate's height, b its cool shift (the crevices), a its rank
  aux 3     cracks in dry packed earth: r value / 2 (a dark groove, its far lip lit; the cells a step apart), b cool, a rank
            (a slow noise: a cracked patch grows from its middle as the density rises)
The light is painted in from ground.json's "light" (the screen's top, a little left); the shader reads these unrotated.
Data: godot/data/look/den_floor.json. Deterministic (seeded by layer name and VERSION). Helpers from ground_paint.py.
"""
import hashlib, json, math, os, sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
from ground_paint import pnoise, blur, shift, ribbon, seed_of  # noqa: E402

DATA = os.path.join(ROOT, "godot", "data", "look", "den_floor.json")
OUT = os.path.join(ROOT, "godot", "art", "dungeon", "den")
VERSION = 1
S = 2


class Sheet:
    """One tileable layer drawn at S x: colour, coverage, shadow, rank (objects) or value, height, cool, rank (plates)."""

    def __init__(self, d, n):
        self.W = n * S
        self.ppm = self.W / d["metres"]
        L = np.array(d["light"], float)
        self.L = L / np.linalg.norm(L)
        self.ims = {}
        self.dr = {}

    def chan(self, k, mode, fill):
        if k not in self.ims:
            self.ims[k] = Image.new(mode, (self.W, self.W), fill)
            self.dr[k] = ImageDraw.Draw(self.ims[k])
        return self.dr[k]

    def px(self, cm): return cm / 100.0 * self.ppm

    def poly(self, k, pts, fill):
        P = np.asarray(pts, float)
        lo, hi, W = P.min(0), P.max(0), self.W
        for ox in (-W, 0, W):
            for oy in (-W, 0, W):
                if hi[0] + ox < 0 or lo[0] + ox > W or hi[1] + oy < 0 or lo[1] + oy > W:
                    continue
                self.dr[k].polygon([tuple(p) for p in P + (ox, oy)], fill=fill)

    def arr(self, k): return np.asarray(self.ims[k], np.float32)


def blob(rng, r, aspect, k=12, j=(0.82, 1.15)):
    a = np.linspace(0, 2 * math.pi, k, endpoint=False)
    jit = rng.uniform(*j, k)
    jit = (jit + np.roll(jit, 1) + np.roll(jit, -1)) / 3
    return np.stack([np.cos(a) * jit * r, np.sin(a) * jit * r * aspect], 1)


def rot(p, a, c):
    ca, sa = math.cos(a), math.sin(a)
    return np.stack([p[:, 0] * ca - p[:, 1] * sa, p[:, 0] * sa + p[:, 1] * ca], 1) + c


def colour(rng, cols, spread):
    return cols[rng.integers(len(cols))], rng.uniform(-1, 1) * spread


def objects(sh, d, lay, rng):
    """Every object of the layer: pass 1 its cast shadow (and rank), pass 2 its body (colour, coverage, rank)."""
    for k, m, f in (("rgb", "RGB", (0, 0, 0)), ("cov", "L", 0), ("shd", "L", 0), ("rank", "L", 255)):
        sh.chan(k, m, f)
    L, T = sh.L, d["metres"]
    perp = np.array([-L[1], L[0]])
    jobs = []
    for st in lay["stamps"]:
        n = int(round(st["per_m2"] * T * T))
        for _ in range(n):
            c = rng.uniform(0, sh.W, 2)
            if st.get("cluster"):
                lo, hi, rad = st["cluster"]
                cs = [c + rng.normal(0, sh.px(rad) * 0.5, 2) for _ in range(int(rng.integers(lo, hi + 1)))]
            else:
                cs = [c]
            rank = int(rng.integers(0, 254))
            for ci in cs:
                jobs.append((st, ci, rank, int(rng.integers(1 << 30))))
    shapes = []
    for st, c, rank, sd in jobs:
        g = np.random.default_rng(sd)
        size = sh.px(g.uniform(*st["size_cm"]))
        a = g.uniform(0, 2 * math.pi)
        hx, dL = colour(g, st["colors"], d["spread_L"])
        body = []  # (points, colour)
        sk = st["shape"]
        if sk in ("stone", "clod"):
            r = size * 0.5
            b = rot(blob(g, r, g.uniform(*st.get("aspect", (0.65, 0.95)))), a, c)
            body.append((b, shift(hx, dL - st.get("shade_dL", 0.04), -0.04)))
            top = rot(blob(g, r * 0.7, 0.85), a, np.zeros(2)) * 1.0 + c + L * r * 0.22
            body.append((top, shift(hx, dL + st.get("lit_dL", 0.05))))
            if r > sh.px(5.0) and st.get("glint"):
                body.append((rot(blob(g, r * 0.28, 0.8), a, c + L * r * 0.42), shift(hx, dL + st["glint"])))
            shadow = rot(blob(g, r * 1.04, 0.95), a, np.zeros(2)) + c - L * r * st.get("shadow_k", 0.32)
        elif sk == "leaf":
            ln, wd = size, size * g.uniform(0.38, 0.55)
            t = np.linspace(0, 1, 10)
            up = np.stack([(t - 0.5) * ln, 0.5 * wd * np.sin(math.pi * t ** 0.8) ** 0.8], 1)
            outline = np.concatenate([up, (up * (1, -1))[::-1][1:-1]])
            body.append((rot(outline, a, c), shift(hx, dL)))
            nrm = np.array([-math.sin(a), math.cos(a)])
            half = up if float(nrm @ L) > 0 else up * (1, -1)
            mid = np.stack([(t[::-1] - 0.5) * ln, np.zeros_like(t)], 1)
            body.append((rot(np.concatenate([half, mid[1:-1]]), a, c), shift(hx, dL + st.get("lit_dL", 0.04))))
            shadow = rot(outline * 1.02, a, c) - L * sh.px(st.get("shadow_cm", 1.4))
        elif sk == "stroke":
            ln = sh.px(g.uniform(*st["length_cm"]))
            p = c.copy(); pts = [p.copy()]
            stp = max(sh.px(6.0), size)
            for _ in range(max(int(ln / stp), 2)):
                a += g.uniform(-st.get("wander", 0.2), st.get("wander", 0.2))
                p = p + stp * np.array([math.cos(a), math.sin(a)])
                pts.append(p.copy())
            runs = [(pts, size, st.get("taper", 0.15), st.get("taper_tip", 0.4))]
            for _ in range(int(g.integers(*st.get("forks", (0, 1))))):
                i = int(g.integers(1, len(pts)))
                fa = a + g.choice([-1, 1]) * g.uniform(0.4, 0.8)
                q = np.asarray(pts[i - 1]) + 0.0; fp = [q.copy()]
                for _ in range(max(int(ln * g.uniform(0.25, 0.5) / stp), 1)):
                    fa += g.uniform(-0.2, 0.2)
                    q = q + stp * np.array([math.cos(fa), math.sin(fa)]); fp.append(q.copy())
                runs.append((fp, max(size * 0.6, sh.px(3.0)), 0.05, 0.7))
            shadow = None
            for q, w, t0, t1 in runs:
                body.append((ribbon(q, w, t0, t1, sh.px(2.0)), shift(hx, dL)))
                lw = max(w * 0.4, sh.px(1.5))
                body.append((ribbon(np.asarray(q) + L * (w - lw) * 0.5, lw, t0, t1, sh.px(2.0)), shift(hx, dL + st.get("lit_dL", 0.08))))
                sp = ribbon(np.asarray(q) - L * sh.px(st.get("shadow_cm", 1.6)), w * 1.1, t0, t1, sh.px(2.0))
                shadow = sp if shadow is None else shadow
                shapes.append(("shd", sp, rank))
        else:
            raise ValueError(sk)
        if shadow is not None and sk != "stroke":
            shapes.append(("shd", shadow, rank))
        shapes.append(("body", body, rank))
    for kind, s_, rank in shapes:  # pass 1: shadows
        if kind == "shd":
            sh.poly("shd", s_, 255); sh.poly("rank", s_, rank)
    for kind, s_, rank in shapes:  # pass 2: bodies
        if kind == "body":
            for pts, col in s_:
                sh.poly("rgb", pts, col); sh.poly("cov", pts, 255); sh.poly("rank", pts, rank)


def plates(sh, d, lay, rng):
    """Packed-earth plates as a value field: per plate a dark crevice beyond its far side, a lit edge toward the light,
    the body a step of value of its own; each plate one rank and one height."""
    for k, f in (("v", 128), ("h", 60), ("cool", 0), ("rank", 255)):
        sh.chan(k, "L", f)
    L, T = sh.L, d["metres"]
    # (patch: neighbouring plates share a value step, so the plates group into 0.5-1.5 m lighter and darker patches)
    pf = pnoise(sh.W // 8, T / 1.5, T / 0.5, rng) * lay.get("patch", 0.0)
    for _ in range(int(round(lay["per_m2"] * T * T))):
        c = rng.uniform(0, sh.W, 2)
        r = sh.px(rng.uniform(*lay["size_cm"])) * 0.5
        b = rot(blob(rng, r, rng.uniform(0.6, 1.0), k=int(rng.integers(6, 10)), j=(0.75, 1.2)), rng.uniform(0, 2 * math.pi), c)
        v = 1.0 + rng.uniform(-1, 1) * lay["spread"] + float(np.clip(pf[int(c[1]) // 8 % pf.shape[0], int(c[0]) // 8 % pf.shape[0]], -2, 2))
        rank, h = int(rng.integers(0, 254)), int(rng.integers(90, 250))
        e, cr = sh.px(lay["lit_cm"]), sh.px(lay["crevice_cm"])
        enc = lambda x: int(np.clip(x * 127.5, 0, 255))
        for pts, val, cool in ((b - L * (e + cr), lay["crevice_v"], 160), (b, v * lay["lit_k"], 0), (b - L * e, v, 0)):
            sh.poly("v", pts, enc(val)); sh.poly("cool", pts, cool); sh.poly("rank", pts, rank); sh.poly("h", pts, h if val != lay["crevice_v"] else 40)


def cracks(sh, d, lay, rng):
    """A periodic jittered Voronoi's edges, wobbled, as grooves: dark, the far lip lit; the cells a step of value apart."""
    W = sh.W
    g = max(int(round(d["metres"] * 100 / lay["cell_cm"])), 2)
    cs = W / g
    jit = rng.uniform(0.15, 0.85, (g, g, 2)); cv = rng.uniform(-1, 1, (g, g)) * lay["spread"]
    yy, xx = np.mgrid[0:W, 0:W].astype(np.float32)
    wob = pnoise(W, g * 0.8, g * 3.0, rng) * cs * 0.12
    xw, yw = xx + wob, yy + np.roll(wob, W // 3, 0)
    gx, gy = (xw // cs).astype(int), (yw // cs).astype(int)
    F1 = np.full((W, W), 1e9, np.float32); F2 = F1.copy(); cell = np.zeros((W, W), np.float32)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            cx, cy = gx + dx, gy + dy
            ix, iy = cx % g, cy % g
            dd = np.hypot(xw - (cx + jit[iy, ix, 0]) * cs, yw - (cy + jit[iy, ix, 1]) * cs)
            closer = dd < F1
            F2 = np.where(closer, F1, np.minimum(F2, dd)); F1 = np.where(closer, dd, F1)
            cell = np.where(closer, cv[iy, ix], cell)
    edge = (F2 - F1) * 0.5
    w = sh.px(lay["width_cm"]) * 0.5
    groove = edge < w
    o = np.round(-sh.L * sh.px(lay["lip_cm"])).astype(int)
    lip = np.roll(np.roll(groove, o[1], 0), o[0], 1) & ~groove
    v = np.where(groove, lay["groove_v"], np.where(lip, lay["lip_k"], 1.0 + cell))
    rk = pnoise(W, 1.0, 2.5, rng)
    rk = (rk - rk.min()) / (rk.max() - rk.min())
    sh.ims["v"] = Image.fromarray(np.clip(v * 127.5, 0, 255).astype(np.uint8))
    sh.ims["h"] = Image.fromarray(np.full((W, W), 128, np.uint8))
    sh.ims["cool"] = Image.fromarray(np.where(groove, 140, 0).astype(np.uint8))
    sh.ims["rank"] = Image.fromarray(np.clip(rk * 253, 0, 253).astype(np.uint8))


def reduce(x, how="mean"):
    n = x.shape[0] // S
    y = x.reshape(n, S, n, S, *x.shape[2:])
    return y.min((1, 3)) if how == "min" else y.mean((1, 3))


def finish_objects(sh, d):
    cov = reduce(sh.arr("cov") / 255); shd = reduce(sh.arr("shd") / 255)
    rgb = reduce(sh.arr("rgb") / 255 * (sh.arr("cov")[..., None] / 255))
    sc = np.array([int(d["shadow_rgb"][i:i + 2], 16) / 255 for i in (1, 3, 5)], np.float32)
    A = cov + (1 - cov) * shd * d["shadow_a"]
    C = rgb + ((1 - cov) * shd * d["shadow_a"])[..., None] * sc
    # (straight alpha: under the empty texels the nearest objects' colour bled out, so the mips draw no dark fringe)
    fill = C / np.maximum(A[..., None], 1e-4)
    have = A > 0.02
    for sg in (2.0, 6.0, 20.0, 60.0):
        bc = np.stack([blur(C[..., i], sg) for i in range(3)], -1); ba = blur(A, sg)
        fill = np.where(have[..., None], fill, bc / np.maximum(ba, 1e-6)[..., None])
        have = have | (ba > 0.01)
    rk = reduce(sh.arr("rank"), "min")
    rk = np.minimum.reduce([np.roll(np.roll(rk, i, 0), j, 1) for i in (-1, 0, 1) for j in (-1, 0, 1)])  # (the rank a texel wider)
    to8 = lambda x: np.clip(x * 255 + 0.5, 0, 255).astype(np.uint8)
    alb = np.concatenate([to8(np.clip(fill, 0, 1)), to8(A)[..., None]], -1)
    aux = np.stack([rk.astype(np.uint8), np.full_like(rk, 128).astype(np.uint8), np.zeros_like(rk).astype(np.uint8), np.full_like(rk, 255).astype(np.uint8)], -1)
    return alb, aux


def finish_mod(sh):
    ch = [reduce(sh.arr(k)) for k in ("v", "h", "cool")] + [reduce(sh.arr("rank"), "min")]
    return np.stack([np.clip(c + 0.5, 0, 255).astype(np.uint8) for c in ch], -1)


def inputs_hash(d):
    return hashlib.sha1((json.dumps([VERSION, d], sort_keys=True) + open(__file__, encoding="utf-8").read()).encode()).hexdigest()[:12]


def build(d):
    n = d["px"]
    albs, auxs = [], []
    for lay in d["objects"]:
        sh = Sheet(d, n)
        objects(sh, d, lay, np.random.default_rng(seed_of("den_meso", lay["name"], VERSION)))
        a, x = finish_objects(sh, d); albs.append(a); auxs.append(x)
    for lay, fn in ((d["plates"], plates), (d["cracks"], cracks)):
        sh = Sheet(d, n)
        fn(sh, d, lay, np.random.default_rng(seed_of("den_meso", lay["name"], VERSION)))
        auxs.append(finish_mod(sh))
    Image.fromarray(np.concatenate(albs, 0), "RGBA").save(os.path.join(OUT, "meso_albedo.png"), optimize=False, compress_level=6)
    Image.fromarray(np.concatenate(auxs, 0), "RGBA").save(os.path.join(OUT, "meso_aux.png"), optimize=False, compress_level=6)
    # the preview: each object layer over a mid earth, the plates and cracks as value, 2 m of each at the play camera's 73 px/m
    earth = np.array([117, 91, 72], np.float32)
    tiles = []
    for a in albs:
        al = a[..., 3:4] / 255.0
        tiles.append((earth * (1 - al) + a[..., :3] * al).astype(np.uint8))
    for x in auxs[2:]:
        tiles.append(np.clip(earth * (x[..., 0:1] / 127.5), 0, 255).astype(np.uint8))
    k = int(n * 2.0 / d["metres"])
    im = Image.fromarray(np.concatenate([t[:k, :k] for t in tiles], 1)).resize((int(73 * 2 * len(tiles)), 146), Image.LANCZOS)
    im.save(os.path.join(OUT, "meso_preview.jpg"), quality=90)
    man = {"by": "tools/look/den_floor_paint.py (den r9 floor: painted from nothing; godot/data/look/den_floor.json)", "painted": VERSION,
           "inputs": inputs_hash(d), "metres": d["metres"], "albedo_layers": [l["name"] for l in d["objects"]],
           "aux_layers": [l["name"] for l in d["objects"]] + [d["plates"]["name"], d["cracks"]["name"]]}
    with open(os.path.join(OUT, "meso.json"), "w", encoding="utf-8") as fh:
        json.dump(man, fh, indent=1)
    print("den meso ->", OUT)


def check(d):
    man = json.load(open(os.path.join(OUT, "meso.json"), encoding="utf-8"))
    ok = man.get("painted") == VERSION and man.get("inputs") == inputs_hash(d)
    a = np.asarray(Image.open(os.path.join(OUT, "meso_albedo.png")))
    n = d["px"]
    for i, l in enumerate(d["objects"]):
        cov = (a[i * n:(i + 1) * n, :, 3] > 128).mean()
        print(f"{l['name']}: coverage {cov:.3f}")
    print("meso:", "PASS" if ok else "STALE (rebuild)")
    return 0 if ok else 1


if __name__ == "__main__":
    d = json.load(open(DATA, encoding="utf-8"))
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    sys.exit(build(d) or 0 if cmd == "build" else check(d))
