"""The den's boulders (dungeon lead 6, the den under Wolf Hollow): built and painted in one command.

    python tools/look/den_rocks.py [--no-mesh] [--preview]

(1) tools/assets/env_rocks.py mesh --form den in Blender (the blender turn taken and given back) writes
godot/art/world/flora/den/den_rock_a-d.gltf (one rock per file, one node, material Stone_OwnDenrock on den_rock_atlas.png)
and the painter's dump godot/art/world/painted/_forms/den_rocks/mesh.npz (git-ignored);
(2) this paints den_rock_atlas.png from that dump, in 3D (every texel's own point, normal and planes, so no seam shows):
FROM den_room.png's four boulders: a warm grey-brown stone painted in short value strokes (ochre lit dabs, cool grey and
umber ones), each plane's strokes laid its own way; a dark warm-brown ink line, broken, where two planes meet at a real
angle (the bevel's middle: the main breaks only); an olive moss cap on what faces up, its edge broken by the strokes; the
foot grimed. Kit.gdshader's OWN_ROCK draws the map (painted 1, its moss off: the moss is painted); the silhouette's ink is
den_rock_ink.gdshader's hull (DungeonDress.Kit). Deterministic: the same sources give the same files.
--no-mesh repaints only. --preview writes a quick lit preview of the four (scratch, not the game's look) to the dump folder.
Its numbers (the measured albedo of each layer) go to godot/art/world/painted/den_rocks/paint.json.
"""
import json, math, os, subprocess, sys, time

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
BLENDER = r"C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe"
DEN = os.path.join(ROOT, "godot", "art", "world", "flora", "den")
DUMP = os.path.join(ROOT, "godot", "art", "world", "painted", "_forms", "den_rocks")
NUMS = os.path.join(ROOT, "godot", "art", "world", "painted", "den_rocks")
A = 2048

# ---- the look (sRGB albedo; the den's key and fill turn these into den_room.png's lit ~(150,140,120), shade ~(70,62,55))
LOOK = dict(
    stone="#958877",          # the warm grey-brown stone's middle
    warm="#ab9172",           # the ochre dabs (the lit side's)
    cool="#7d7570",           # the cool grey dabs
    umber="#625244",          # the dark dabs
    moss="#565f2c", moss_dark="#424a22", moss_light="#687034",
    ink="#2a1f19",            # the crease line, dark warm brown
    ink_cm=2.4,               # its half width (cm) at a full break
    ink_a=0.8,                # its opacity (a painted dark stroke over the break, not a pen line)
    ink_deg=(26.0, 44.0),     # the angle between two planes' normals from which a break is inked (none under, whole over)
    dab_cm=(9.0, 26.0),       # a dab's short and long side (cm)
    fine_cm=(4.5, 11.0),
    moss_up=(0.75, 0.92),     # the normal's up share where the cap begins and is whole
    big_m=0.8, big_k=0.34,   # the broad value patches: a plane lit unevenly, as a broad brush leaves it (den_room.png: a lit band)
    moss_dabs=0.25,
    moss_patch=(0.6, 0.72),   # the low-frequency gate: the cap is mossed only in a patch or two (den_room.png's are sparse)
    cool_shade="#808478", shade_cool=0.8, value=0.62,
    side=(-0.75, 0.5, 0.43), lit_k=(0.75, 0.3), lit_pivot=0.38, warm_lit="#c29a6e", lit_warm=0.45,   # the painted side light (den_room.png's median ~69 of 255, its lit band ~120): up, down   # (value: the whole stone, before the moss)   # the planes turned from the key pulled this far toward a cool grey            # the share of its dabs that are moss at the cap's edge (more toward the crown)
    foot_m=0.3, foot_dark=0.7,
)


def turn(*a): subprocess.run([sys.executable, os.path.join(ROOT, "tools", "turn.py"), *a], check=True, cwd=ROOT)


def blender(args, job):
    turn("take", "blender", f"den rocks: {job}", "--wait", "90", "--stale-ok")   # (the rocks read no art of hers)
    try:
        r = subprocess.run([BLENDER, "-b", "--factory-startup", "-P", *args], cwd=ROOT, capture_output=True, text=True)
    finally:
        turn("give", "blender")
    if r.returncode != 0 or "Traceback (most recent call last)" in (r.stdout + r.stderr):
        sys.stderr.write(r.stdout[-4000:] + r.stderr[-3000:]); raise SystemExit(f"blender failed: {job}")
    return r.stdout


# ---- colour
def srgb_to_lin(c): return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def lin_to_srgb(c): c = np.clip(c, 0, 1); return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)
def hexc(h): return srgb_to_lin(np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]))
def smoothstep(a, b, x): t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)


# ---- noise (deterministic, numpy)
def _hash(ix, iy, iz, salt):
    h = (ix * 73856093) ^ (iy * 19349663) ^ (iz * 83492791) ^ (salt * 2654435761)
    h = (h ^ (h >> 13)) * 1274126177 & 0x7fffffff
    return h ^ (h >> 16)


def vnoise(p, scale, salt):
    """Smooth value noise in [0, 1] at 'scale' m."""
    q = p / scale
    b = np.floor(q).astype(np.int64); f = q - b
    f = f * f * (3 - 2 * f)
    out = 0.0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                v = (_hash(b[:, 0] + dx, b[:, 1] + dy, b[:, 2] + dz, salt) & 1023) / 1023.0
                w = (f[:, 0] if dx else 1 - f[:, 0]) * (f[:, 1] if dy else 1 - f[:, 1]) * (f[:, 2] if dz else 1 - f[:, 2])
                out = out + v * w
    return out


def dabs(p, axes, short, long, salt):
    """Flat painted dabs: the nearest feature point of a jittered lattice in each point's frame (long along axes[:, 0]),
    each dab two random numbers (its value, its hue) and its distance-ratio to the next (its edge, for broken borders).
    p, axes[:, k] per point (N, 3)."""
    q = np.stack([(p * axes[:, 0]).sum(1) / long, (p * axes[:, 1]).sum(1) / short, (p * axes[:, 2]).sum(1) / short], 1)
    base = np.floor(q).astype(np.int64)
    best = np.full(len(q), 1e9); second = np.full(len(q), 1e9); hv = np.zeros(len(q), np.int64)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                c = base + (dx, dy, dz)
                h = _hash(c[:, 0], c[:, 1], c[:, 2], salt)
                j = np.stack([(h & 1023) / 1023.0, ((h >> 10) & 1023) / 1023.0, ((h >> 20) & 1023) / 1023.0], 1)
                d = ((q - (c + 0.15 + 0.7 * j)) ** 2).sum(1)
                k = d < best
                second = np.where(k, best, np.minimum(second, d)); best = np.where(k, d, best); hv = np.where(k, h, hv)
    v1 = ((hv >> 3) & 1023) / 1023.0
    v2 = ((hv >> 13) & 1023) / 1023.0
    return v1, v2, np.sqrt(best) / np.maximum(np.sqrt(second), 1e-6)


# ---- the planes (env_rocks.sculpt_planes' shape, read back per texel)
def surfaces(p, c, ax, Np, d):
    """Each texel's signed distance to the ellipsoid (column 0, about) and to each plane (1..), and their normals."""
    P = p - c
    r = np.maximum(np.linalg.norm(P, axis=1, keepdims=True), 1e-9)
    D = P / r
    re = 1.0 / np.sqrt(((D / ax) ** 2).sum(1, keepdims=True))
    ne = D * re / ax ** 2
    ne /= np.linalg.norm(ne, axis=1, keepdims=True)
    e0 = (r - re)[:, 0] * (D * ne).sum(1)
    E = np.concatenate([e0[:, None], P @ Np.T - d[None, :]], 1)
    Nall = np.concatenate([ne[:, None, :], np.broadcast_to(Np[None], (len(p),) + Np.shape)], 1)
    return E, Nall


def frames(n, along):
    """Per point: a stroke direction in its tangent plane (along, projected), the other tangent, the normal."""
    a0 = along - (along * n).sum(1, keepdims=True) * n
    bad = np.linalg.norm(a0, axis=1) < 0.2
    a0[bad] = np.cross(n[bad], np.array([0.0, 0.0, 1.0])) + 1e-3
    a0 /= np.linalg.norm(a0, axis=1, keepdims=True)
    a1 = np.cross(n, a0)
    return np.stack([a0, a1, n], 2)


# ---- the atlas's texels
def rasterize(M, names):
    """Per texel: mask, variant, object point (z up), smooth normal, baked colour (edge, cavity, occlusion)."""
    vid = -np.ones((A, A), np.int16)
    pos = np.zeros((A, A, 3)); nrm = np.zeros((A, A, 3)); bk = np.zeros((A, A, 3))
    for vi, nm in enumerate(names):
        V, F, UV, N, col = (M[f"{nm}_{k}"] for k in ("V", "F", "UV", "N", "col"))
        for fi, tri in enumerate(F):
            xs, ys = UV[fi, :, 0] * A, (1 - UV[fi, :, 1]) * A
            i0, i1 = max(int(math.floor(xs.min())) - 1, 0), min(int(math.ceil(xs.max())) + 1, A)
            j0, j1 = max(int(math.floor(ys.min())) - 1, 0), min(int(math.ceil(ys.max())) + 1, A)
            den = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
            if i1 <= i0 or j1 <= j0 or abs(den) < 1e-12:
                continue
            gx, gy = np.meshgrid(np.arange(i0, i1) + 0.5, np.arange(j0, j1) + 0.5)
            w0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / den
            w1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / den
            w2 = 1 - w0 - w1
            m = (w0 >= -0.02) & (w1 >= -0.02) & (w2 >= -0.02)
            if not m.any():
                continue
            W = np.stack([w0[m], w1[m], w2[m]], 1)
            jj, ii = gy[m].astype(int), gx[m].astype(int)
            vid[jj, ii] = vi
            pos[jj, ii] = W @ V[tri]
            nrm[jj, ii] = W @ N[tri]
            bk[jj, ii] = W @ col[tri]
    nrm /= np.maximum(np.linalg.norm(nrm, axis=2, keepdims=True), 1e-9)
    return vid, pos, nrm, bk


def dilate(img, mask, n=10):
    """Each empty texel takes its nearest painted one's colour (n px out: the islands' mip-safe margin)."""
    d, (iy, ix) = ndimage.distance_transform_edt(~mask, return_indices=True)
    out = img[iy, ix]
    out[d > n] = img[~mask].mean(0) if img.ndim == 3 else 0
    return out


def paint(M, names):
    L = LOOK
    vid, pos, nrm, bk = rasterize(M, names)
    mask = vid >= 0
    p, n, b, v = pos[mask], nrm[mask], bk[mask], vid[mask]
    N = len(p)
    ink = np.zeros(N); plane = np.zeros(N, np.int64); h01 = np.zeros(N); gap = np.zeros(N)
    along = np.zeros((N, 3)); fn = np.zeros((N, 3))
    for vi, nm in enumerate(names):
        k = v == vi
        c, ax, Np, d = (M[f"{nm}_{q}"] for q in ("center", "ax", "Np", "d"))
        E, Nall = surfaces(p[k], c, ax, Np, d)
        o = np.argsort(-E, 1)
        i1, i2 = o[:, 0], o[:, 1]
        r = np.arange(k.sum())
        n1, n2 = Nall[r, i1], Nall[r, i2]
        dist = (E[r, i1] - E[r, i2]) / np.maximum(np.linalg.norm(n1 - n2, axis=1), 1e-6)   # (to the two's bisecting plane: the crease's line, m)
        ang = np.degrees(np.arccos(np.clip((n1 * n2).sum(1), -1, 1)))
        strength = smoothstep(L["ink_deg"][0], L["ink_deg"][1], ang)
        # (a break the floor cuts, under 12 cm up, is no break: the foot's own)
        strength *= smoothstep(0.0, 0.15, p[k][:, 2])
        hw = L["ink_cm"] / 100.0 * (0.55 + 0.45 * strength) * (0.7 + 0.6 * vnoise(p[k], 0.35, 11 + vi))
        brk = smoothstep(0.32, 0.45, vnoise(p[k], 0.22, 23 + vi))       # (broken: a gap here and there along it)
        ink[k] = strength * brk * (1 - smoothstep(0.25 * hw, hw, dist))
        gap[k] = dist
        plane[k] = i1
        z = p[k][:, 2]
        h01[k] = (z - z.min()) / max(np.ptp(z), 1e-6)
        # each plane its own stroke direction (a broad hand's: across the plane, a little off level), the round one a slant
        rng = np.random.default_rng(int(1000 + vi))
        dirs = []
        for j in range(len(Np) + 1):
            a = rng.uniform(0, 2 * math.pi)
            dirs.append((math.cos(a), math.sin(a), rng.uniform(-0.6, 0.6)))
        dirs = np.array(dirs)
        along[k] = dirs[i1]
        # (the dabs' frame is the plane's own, constant across it, so the lattice is not sheared by a turning normal (a swirl);
        # the round part's a fixed one, z up)
        fn[k] = np.where((i1 > 0)[:, None], Nall[r, i1], np.array([0.0, 0.0, 1.0]))
    ax = frames(fn, along)
    # the stone: a broad value patch, then dabs, then fine dabs, each dab its value and a pull toward warm or cool
    big = vnoise(p * [1, 1, 1] + 7.0 * v[:, None], L["big_m"], 3) - 0.5
    v1, v2, e1 = dabs(p + 13.0 * v[:, None] + 0.37 * plane[:, None], ax, L["dab_cm"][0] / 100, L["dab_cm"][1] / 100, 5)
    f1, f2, _ = dabs(p + 17.0 * v[:, None] + 0.51 * plane[:, None], ax, L["fine_cm"][0] / 100, L["fine_cm"][1] / 100, 9)
    stone, warm, cool, umber = (hexc(L[q]) for q in ("stone", "warm", "cool", "umber"))
    col = np.tile(stone, (N, 1))
    # dab colour: by its hue number a warm, cool or umber pull, by its value number how far (quantised: flat dabs)
    q = np.floor(v1 * 4) / 3.0
    tw = np.where(v2 < 0.45, 1.0, 0.0); tc = np.where((v2 >= 0.45) & (v2 < 0.75), 1.0, 0.0); tu = np.where(v2 >= 0.75, 1.0, 0.0)
    pull = 0.15 + 0.35 * q
    col = col + (pull * tw)[:, None] * (warm - stone) + (pull * tc)[:, None] * (cool - stone) + (pull * tu)[:, None] * (umber - stone)
    col *= (1.0 + L["big_k"] * big)[:, None]
    col *= (1.0 + 0.12 * (np.floor(f1 * 3) / 2.0 - 0.5))[:, None]
    # the painted light: up and toward the key's side lighter, under darker (a broad hand's gradient, under the game's own bands)
    # (side-lit, den_room.png's: a plane turned toward the key bright, a level top mid, so the top-down view still splits)
    key = np.array([-0.45, 0.35, 0.82]); key /= np.linalg.norm(key)
    side = np.array(L["side"]); side /= np.linalg.norm(side)
    # (split about a pivot, so the top's few planes part: the ones turned to the key lit and ochre, the rest a step down)
    t = n @ side
    up = np.clip((t - L["lit_pivot"]) / 0.3, 0, 1); dn = np.clip((L["lit_pivot"] - t) / 0.5, 0, 1)
    col = col * (1 - L["lit_warm"] * up[:, None]) + hexc(L["warm_lit"]) * L["lit_warm"] * up[:, None]
    col *= (1.0 + L["lit_k"][0] * up - L["lit_k"][1] * dn)[:, None]
    lit = t
    # (den_room.png's planes: warm where the key falls, a neutral cool grey turned from it (its shade (41,36,34), the
    # front (73,64,55)), so the turned planes are pulled toward the cool grey, lifted a little, not only darkened)
    away = smoothstep(0.1, -0.45, n @ key)
    col = col * (1 - (L["shade_cool"] * away)[:, None]) + (hexc(L["cool_shade"]) * L["shade_cool"] * away[:, None])
    col *= L["value"]
    # the bake: cavity and broad occlusion darker, the worn rims a touch lighter
    col *= ((1 - 0.25 * b[:, 1]) * (1 - 0.3 * b[:, 2]) * (1 + 0.12 * b[:, 0]))[:, None]
    # the foot: grimed up to foot_m, its line broken by the dabs
    foot = 1 - smoothstep(0.0, L["foot_m"], p[:, 2] + 0.12 * (v1 - 0.5))
    col *= (1 - (1 - L["foot_dark"]) * foot)[:, None]
    # the moss cap: what faces up, its edge broken by the dabs, its own dabs light and dark
    mz = smoothstep(L["moss_up"][0], L["moss_up"][1], n[:, 2] + 0.22 * (v1 - 0.5) + 0.12 * (vnoise(p, 0.3, 31) - 0.5) + 0.08 * h01)
    mz *= smoothstep(0.35, 0.5, h01)
    # (den_room.png's moss is olive dabs over the top, the stone between: a dab is moss by its hue number, more toward the crown)
    mz *= np.where(f2 < L["moss_dabs"] + 0.3 * mz, 1.0, 0.0) * smoothstep(*L["moss_patch"], vnoise(p, 0.6, 37) + 0.15 * mz)
    moss = hexc(L["moss"]) + (np.floor(f2 * 3) / 2.0 - 0.5)[:, None] * (hexc(L["moss_light"]) - hexc(L["moss_dark"]))
    moss *= (1.0 + 0.2 * big)[:, None]
    col = col * (1 - mz[:, None]) + moss * mz[:, None]
    # the ink last, over moss and stone
    inkc = hexc(L["ink"])
    col = col * (1 - L["ink_a"] * ink[:, None]) + inkc * L["ink_a"] * ink[:, None]
    img = np.zeros((A, A, 3)); img[mask] = col
    img = dilate(img, mask)
    srgb = lin_to_srgb(img)
    os.makedirs(DEN, exist_ok=True)
    Image.fromarray((srgb * 255 + 0.5).astype(np.uint8)).save(os.path.join(DEN, "den_rock_atlas.png"))
    nums = dict(texels=int(N), ink_share=round(float((ink > 0.5).mean()), 4), moss_share=round(float((mz > 0.5).mean()), 4),
                stone_srgb=[round(float(x)) for x in np.median(lin_to_srgb(col[(mz < 0.1) & (ink < 0.1)]), 0) * 255],
                moss_srgb=[round(float(x)) for x in np.median(lin_to_srgb(col[mz > 0.9]), 0) * 255] if (mz > 0.9).any() else None,
                look=L)
    os.makedirs(NUMS, exist_ok=True)
    json.dump(nums, open(os.path.join(NUMS, "paint.json"), "w", newline="\n"), indent=1)
    print("den rocks paint:", json.dumps({k: v for k, v in nums.items() if k != "look"}))
    return srgb


def preview(M, names, atlas):
    """A quick look from the play camera's pitch (about 55 degrees down): two cel bands, the atlas at each pixel."""
    sys.path.insert(0, os.path.join(ROOT, "tools", "assets"))
    from env_rocks import raster
    tiles = []
    pitch = math.radians(55)
    for vi, nm in enumerate(names):
        V, F, UV, N = (M[f"{nm}_{k}"] for k in ("V", "F", "UV", "N"))
        yaw = math.radians(30)
        right = np.array([math.cos(yaw), math.sin(yaw), 0.0])
        fwd = np.array([-math.sin(yaw), math.cos(yaw), 0.0])
        eye = -fwd * math.cos(pitch) + np.array([0, 0, 1.0]) * math.sin(pitch)   # (toward the eye)
        up = np.cross(eye, right)
        R = np.stack([right, up, eye])
        ids, (x0, y0), (B0, B1) = raster(V, F, R, 120, pad=6, bary=True)
        H, W = ids.shape
        out = np.full((H, W, 3), 0.12)
        m = ids >= 0
        fi = ids[m]; w0, w1 = B0[m], B1[m]; w2 = 1 - w0 - w1
        uv = UV[fi, 0] * w0[:, None] + UV[fi, 1] * w1[:, None] + UV[fi, 2] * w2[:, None]
        nn = N[F[fi, 0]] * w0[:, None] + N[F[fi, 1]] * w1[:, None] + N[F[fi, 2]] * w2[:, None]
        nn /= np.linalg.norm(nn, axis=1, keepdims=True)
        tx = np.clip((uv[:, 0] * A).astype(int), 0, A - 1); ty = np.clip(((1 - uv[:, 1]) * A).astype(int), 0, A - 1)
        alb = srgb_to_lin(atlas[ty, tx])
        key = np.array([-0.5, 0.3, 0.8]); key /= np.linalg.norm(key)
        band = np.where(nn @ key > 0.15, 1.0, 0.45)
        out[m] = lin_to_srgb(alb * band[:, None] * 0.85)
        tiles.append(out)
    h = max(t.shape[0] for t in tiles)
    row = np.concatenate([np.pad(t, ((0, h - t.shape[0]), (0, 8), (0, 0)), constant_values=0.12) for t in tiles], 1)
    Image.fromarray((np.clip(row, 0, 1) * 255).astype(np.uint8)).save(os.path.join(DUMP, "preview.png"))
    print("preview:", os.path.join(DUMP, "preview.png"))


if __name__ == "__main__":
    a = sys.argv[1:]
    t0 = time.time()
    if "--no-mesh" not in a:
        at = os.path.join(DEN, "den_rock_atlas.png")
        if not os.path.exists(at):   # (the game files name the atlas: a grey stand-in until the first paint)
            os.makedirs(DEN, exist_ok=True)
            Image.new("RGB", (64, 64), (128, 128, 128)).save(at)
        out = blender([os.path.join(ROOT, "tools", "assets", "env_rocks.py"), "--", "mesh", "--form", "den"], "mesh")
        for line in out.splitlines():
            if line.startswith("REPORT") or "tris" in line or "px/m" in line: print(" ", line)
    M = np.load(os.path.join(DUMP, "mesh.npz"))
    names = [str(x) for x in M["names"]]
    atlas = paint(M, names)
    if "--preview" in a:
        preview(M, names, atlas)
    print(f"den rocks: done in {time.time() - t0:.0f} s")
