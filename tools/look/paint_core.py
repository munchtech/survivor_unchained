"""B3's painter core (L1 texture authoring; docs/design/look/TEXTURE_AUTHORING.md): painted-block maps from an asset's
form maps (tools/look/bake_forms.py). The one core both sides call (the game's world build, Marionette's paint stage).

    python tools/look/paint_core.py FORMS_DIR OUT_DIR [--arm A|B|C] [--ai AI.png] [--albedo-src albedo|lit]

Inputs, and what each part is FROM (PIPELINE.md rule 4):
  forms.npz / forms.json   the asset's own forms (blocks, classes, world position and normal, AO, cavity, convexity)
  materials.json           each class's color (paint.albedo once B2 round 2 writes it, else paint.measured: the
                           boards' lit color, MB2-MB4) and its brush (brush_cm, spread_L, edge, cavity)
  the bible's rule 9       per-block value spread within +-0.06 Oklab L; the brush at one world scale; no detail
                           under about 3 cm; light painted in (a top-lit gradient, a lit bevel stroke, a cool cavity);
                           normal maps carry big forms only; rule 6 (matte classes have no highlight: roughness 1)
Arms: A procedural (the brush: flat dabs of a 3D anisotropic cell field at brush_cm, per block along its long axis);
B the brush taken from an AI paint (AI.png in the same UV space), re-quantized: its in-block value only, held to the
brush's share of the spread; C the AI's own in-block light kept too (its value and a little of its hue), clamped to
the spread. Every arm's block colors, bevel, cavity and normal are the same (from the forms), so the arms differ only
where the brush comes from.
Outputs: albedo.png (sRGB, light painted in), normal.png (tangent space, OpenGL +Y), rough.png, paint.json (numbers).
"""
import json, os, sys, time, zlib

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LIB = os.path.join(ROOT, "godot", "data", "look", "materials.json")
VERSION = 1  # (bumped on any change to the painting: outputs carry it, and the check refuses a stale one)
TOP_SHARE, BRUSH_SHARE = 0.4, 0.6  # (the spread's split: the top-lit gradient and the brush, inside +-spread_L)


# ---- Oklab -------------------------------------------------------------------------------------------------------
def srgb_to_lin(c): return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def lin_to_srgb(c): c = np.clip(c, 0, 1); return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def lin_to_oklab(c):
    M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566], [0.0883024619, 0.2817188376, 0.6299787005]])
    M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099], [0.0259040371, 0.7827717662, -0.8086757660]])
    return np.cbrt(np.maximum(c @ M1.T, 0)) @ M2.T


def oklab_to_lin(o):
    M2i = np.array([[1, 0.3963377774, 0.2158037573], [1, -0.1055613458, -0.0638541728], [1, -0.0894841775, -1.2914855480]])
    M1i = np.array([[4.0767416621, -3.3077115913, 0.2309699292], [-1.2684380046, 2.6097574011, -0.3413193965], [-0.0041960863, -0.7034186147, 1.7076147010]])
    return ((o @ M2i.T) ** 3) @ M1i.T


def hex_oklab(h): return lin_to_oklab(srgb_to_lin(np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)])))


def hsh(*k):  # deterministic hash in [0, 1)
    return (zlib.crc32(repr(k).encode()) & 0xffffff) / float(1 << 24)


# ---- the class's color --------------------------------------------------------------------------------------------
def class_color(cls, src):
    """(L lo/mid/hi, C lo/mid/hi, h mean and deviation lo/hi) of a class; src 'albedo' when B2 round 2 has written
    paint.albedo (same shape as paint.measured), else the boards' lit color."""
    p = cls["paint"]
    if src == "albedo" and "albedo" in p: return p["albedo"], "albedo"
    return p["measured"], "lit"


def block_lab(m, b, salt):
    """One block's color, varied inside the class's range: L across its middle 60 % (the painted light needs the rest),
    C and hue across half of theirs."""
    u = [hsh(salt, b, k) * 2 - 1 for k in range(3)]
    L = m["L"][1] + u[0] * 0.3 * (m["L"][2] - m["L"][0])
    C = max(0.0, m["C"][1] + u[1] * 0.25 * (m["C"][2] - m["C"][0]))
    h = np.radians(m["h"][0] + (m["h"][1] if u[2] < 0 else m["h"][2]) * abs(u[2]) * 0.25)
    return np.array([L, C * np.cos(h), C * np.sin(h)])


# ---- the brush ----------------------------------------------------------------------------------------------------
def cell_field(p, axes, size, salt):
    """Flat dabs: the nearest feature point of a jittered 3D lattice in the block's frame (long along axes[0]), each
    dab one value in {-1, 0, 1}. p (N, 3) metres; size (cm) is the dab's short side."""
    s = size / 100.0
    q = np.stack([p @ axes[0] / (s * 2.6), p @ axes[1] / s, p @ axes[2] / s], 1)
    base = np.floor(q).astype(np.int64)
    best = np.full(len(q), 1e9); val = np.zeros(len(q))
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                c = base + (dx, dy, dz)
                hcode = (c[:, 0] * 73856093) ^ (c[:, 1] * 19349663) ^ (c[:, 2] * 83492791) ^ (salt * 2654435761)
                hcode = (hcode ^ (hcode >> 13)) * 1274126177 & 0x7fffffff
                j = np.stack([(hcode & 1023) / 1023.0, ((hcode >> 10) & 1023) / 1023.0, ((hcode >> 20) & 1023) / 1023.0], 1)
                d = ((q - (c + 0.15 + 0.7 * j)) ** 2).sum(1)
                k = d < best; best[k] = d[k]; val[k] = ((hcode[k] >> 7) % 3) - 1.0
    return val


def block_axes(pos, nrm):
    """A block's frame: its long axis (the positions' first principal axis, across its mean normal), the second, the normal."""
    n = nrm.mean(0); n /= np.linalg.norm(n) + 1e-9
    c = pos - pos.mean(0)
    c = c - np.outer(c @ n, n)
    w, v = np.linalg.eigh(c.T @ c)
    a0 = v[:, -1]; a1 = np.cross(n, a0); a1 /= np.linalg.norm(a1) + 1e-9
    return np.stack([a0, a1, n])


def smooth(x, sig):
    return ndimage.gaussian_filter(x, sig) if sig > 0 else x


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)


# ---- the painter --------------------------------------------------------------------------------------------------
def paint(forms_dir, out_dir, arm="A", ai=None, albedo_src="albedo"):
    t0 = time.time()
    F = np.load(os.path.join(forms_dir, "forms.npz")); meta = json.load(open(os.path.join(forms_dir, "forms.json")))
    lib = json.load(open(LIB, encoding="utf-8"))
    mask, blk, cls = F["mask"], F["blk"], F["cls"]
    pos, nrm = F["pos"].astype(np.float64), F["nrm"].astype(np.float64)
    ao, cav, cvx = [F[k].astype(np.float64) for k in ("ao", "cavity", "convex")]
    H, W = blk.shape; ppm = meta["ppm"]; cm = ppm / 100.0  # px per cm
    names = meta["classes"]
    salt = zlib.crc32(meta["asset"].encode()) & 0xffff
    lab = np.zeros((H, W, 3)); brush = np.zeros((H, W)); top = np.zeros((H, W))
    used = {}
    up = nrm[..., 2]  # (Blender's Z up)
    zlo, zhi = pos[..., 2][mask].min(), pos[..., 2][mask].max()
    h01 = (pos[..., 2] - zlo) / max(zhi - zlo, 1e-6)
    spread = {}
    for b in np.unique(blk[mask]):
        k = blk == b
        cn = names[int(cls[k][0])] if names else "stone"
        C = lib["classes"][cn]; P = C["paint"]
        m, used[cn] = class_color(C, albedo_src)
        s = P["spread_L"]; spread[int(b)] = s
        base = block_lab(m, int(b), salt) if b > 0 or meta["kind"] != "setts" else block_lab(m, 0, salt) * [0.55, 0.6, 0.6]
        lab[k] = base
        # the top-lit gradient: facing up and high on the asset is lit (the key is above: rule 5's painted gradient)
        t = 0.6 * up[k] + 0.4 * (2 * h01[k] - 1)
        top[k] = TOP_SHARE * s * t
        ax = block_axes(pos[k], nrm[k])
        brush[k] = BRUSH_SHARE * s * cell_field(pos[k], ax, P["brush_cm"], salt + int(b))
    # the dabs' edges softened to the 3 cm floor (no detail under about 3 cm: a sigma of 1 cm)
    brush = smooth(brush, 1.2 * cm)
    if arm in ("B", "C") and ai is not None:
        A = np.asarray(Image.open(ai).convert("RGB").resize((W, H), Image.LANCZOS)) / 255.0
        alab = lin_to_oklab(srgb_to_lin(A))
        aL = smooth(alab[..., 0], 1.0 * cm)
        dev = np.zeros((H, W)); dab = np.zeros((H, W, 2))
        for b in np.unique(blk[mask]):
            k = blk == b
            d = aL[k] - np.median(aL[k])
            sc = np.percentile(np.abs(d), 95) + 1e-6
            dev[k] = d / sc  # (-1..1 in the block)
            dab[k] = alab[..., 1:][k] - np.median(alab[..., 1:][k], 0)
        if arm == "B":
            brush = BRUSH_SHARE * np.vectorize(spread.get)(np.where(mask, blk, list(spread)[0])) * np.clip(dev, -1, 1)
        else:  # C: the AI's light too (top + brush), a little of its hue shift
            s_px = np.vectorize(spread.get)(np.where(mask, blk, list(spread)[0]))
            brush = s_px * np.clip(dev, -1, 1); top[:] = 0
            lab[..., 1:] += 0.3 * dab
    lab[..., 0] += top + brush
    # the joints in 3D (blocks are often their own UV islands): each pixel's distance to the nearest pixel of another
    # block, and whether that joint is convex (the other block's centre lies below this block's plane)
    dj, convex_j = joints(blk, mask, pos, nrm)
    # the lit bevel stroke on convex edges (edge.dL, at least edge.width_cm wide) and the cool cavity (cavity.*)
    P0 = {n: lib["classes"][n]["paint"] for n in names}
    e_dL = np.vectorize(lambda c: P0[names[c]]["edge"]["dL"])(cls)
    c_dL = np.vectorize(lambda c: P0[names[c]]["cavity"]["dL"])(cls)
    c_h = np.radians(np.vectorize(lambda c: P0[names[c]]["cavity"]["h"])(cls))
    c_C = np.vectorize(lambda c: P0[names[c]]["cavity"]["C"])(cls)
    wcm = max(P0[n]["edge"]["width_cm"] for n in names)
    w = wcm / 100.0
    edge_j = (1 - smoothstep(0.5 * w, 1.5 * w, dj)) * convex_j
    edge = np.maximum(smooth(smoothstep(0.18, 0.45, cvx), 0.5 * wcm * cm), edge_j) * mask
    edge = np.clip(edge * 1.4, 0, 1)
    cavity = np.clip(np.maximum(smoothstep(0.12, 0.5, cav), 0.8 * smoothstep(0.15, 0.6, 1 - ao)), 0, 1) * mask
    lab[..., 0] += e_dL * edge + c_dL * cavity
    lab[..., 1] += c_C * np.cos(c_h) * cavity
    lab[..., 2] += c_C * np.sin(c_h) * cavity
    rgb = lin_to_srgb(oklab_to_lin(lab))
    # a big-forms-only normal: the stones' own bake on a tile; on a prop, each block's rounded edge (a 4 cm pillow,
    # 1.5 cm high, from the 3D distance to the nearest other block), so the planes turn into their joints
    if "tnrm" in F.files:
        tn = F["tnrm"].astype(np.float64)
        n_out = tn
    else:
        R, A = 0.04, 0.015
        d = np.minimum(dj, R)
        hgt = A * (1 - (1 - d / R) ** 2)
        hgt = dilate(hgt, mask)
        gy, gx = np.gradient(smooth(hgt, 1.5 * cm))
        nx, ny = -gx * ppm, gy * ppm  # (v up: rows run down the image)
        n = np.stack([nx, ny, np.ones_like(nx)], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True)
        n_out = n * 0.5 + 0.5
    rough = np.where(np.vectorize(lambda c: lib["classes"][names[c]]["cel"]["spec"][2] > 0)(cls), 0.45, 1.0)
    os.makedirs(out_dir, exist_ok=True)
    rgbd = np.stack([dilate(rgb[..., i], mask) for i in range(3)], -1)
    Image.fromarray((np.clip(rgbd, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(out_dir, "albedo.png"))
    Image.fromarray((np.clip(np.stack([dilate(n_out[..., i], mask) for i in range(3)], -1), 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(out_dir, "normal.png"))
    Image.fromarray((dilate(rough, mask) * 255 + 0.5).astype(np.uint8)).save(os.path.join(out_dir, "rough.png"))
    nums = measure(lab, blk, mask, cm, edge, cavity)
    nums.update(arm=arm, version=VERSION, albedo_src=sorted(set(used.values())), size=W, ppm=ppm, seconds=round(time.time() - t0, 1),
                brush_cm={n: lib["classes"][n]["paint"]["brush_cm"] for n in names},
                vram_kb=round(W * H * (0.5 + 1.0 + 0.5) * 4 / 3 / 1024))  # (BC1 albedo, BC5 normal, BC4 rough, + mips)
    json.dump(nums, open(os.path.join(out_dir, "paint.json"), "w"), indent=1)
    print("B3 paint:", json.dumps(nums))
    return nums


def joints(blk, mask, pos, nrm, k=24, far=0.06):
    """(distance in m to the nearest pixel of another block, capped at far; 1 where that joint is convex)."""
    H, W = blk.shape
    edge = np.zeros_like(mask)
    for sh in ((0, 1), (1, 0), (0, -1), (-1, 0)):
        edge |= mask & (np.roll(blk, sh, (0, 1)) != blk)
    d = np.full((H, W), far); cv = np.zeros((H, W))
    if not edge.any(): return d, cv
    cen, nm = {}, {}
    for b in np.unique(blk[mask]):
        kk = mask & (blk == b); cen[b] = pos[kk].mean(0); n = nrm[kk].mean(0); nm[b] = n / (np.linalg.norm(n) + 1e-9)
    ep, eb = pos[edge], blk[edge]
    tree = cKDTree(ep)
    q = pos[mask]; qb = blk[mask]
    dd, ii = tree.query(q, k=k, distance_upper_bound=far)
    ok = (ii < len(eb))
    lab = np.where(ok, eb[np.minimum(ii, len(eb) - 1)], -2)
    other = ok & (lab != qb[:, None])
    dd = np.where(other, dd, np.inf)
    j = dd.argmin(1); dmin = dd[np.arange(len(j)), j]
    ob = lab[np.arange(len(j)), j]
    has = np.isfinite(dmin)
    vx = np.zeros(len(j))
    pairs = {}
    for a_, b_ in set(zip(qb[has].tolist(), ob[has].tolist())):
        pairs[(a_, b_)] = 1.0 if (cen[b_] - cen[a_]) @ nm[a_] < 0 else 0.0
    vx[has] = [pairs[(a_, b_)] for a_, b_ in zip(qb[has].tolist(), ob[has].tolist())]
    d[mask] = np.where(has, np.minimum(dmin, far), far); cv[mask] = vx
    return d, cv


def dilate(x, mask, n=12):
    """Pads the islands' color out by n px (so mips and filtering don't pull the background in)."""
    if mask.all(): return x
    idx = ndimage.distance_transform_edt(~mask, return_distances=False, return_indices=True)
    return x[tuple(idx)]


def measure(lab, blk, mask, cm, edge, cavity):
    """Per-block L spread of the block's interior (the bevel and cavity are its border's painted light): the 5th-95th
    percentile half-range, max and median over blocks; the share of interior L variance at scales under 3 cm."""
    L = lab[..., 0]
    inner = mask & (edge < 0.1) & (cavity < 0.1)
    inner &= ndimage.binary_erosion(np.ones_like(mask), iterations=1)
    sp = []
    for b in np.unique(blk[inner]):
        v = L[inner & (blk == b)]
        if v.size > 50: sp.append((np.percentile(v, 95) - np.percentile(v, 5)) / 2)
    med = np.zeros_like(L)
    for b in np.unique(blk[mask]):
        k = blk == b; med[k] = np.median(L[k])
    dv = np.where(inner, L - med, 0.0)
    hi = dv - ndimage.gaussian_filter(dv, 1.5 * cm)
    share = float((hi[inner] ** 2).sum() / max((dv[inner] ** 2).sum(), 1e-12))
    return dict(blocks=len(sp), spread_L_med=round(float(np.median(sp)), 4), spread_L_max=round(float(np.max(sp)), 4),
                detail_under_3cm=round(share, 3), edge_share=round(float((edge > 0.5).mean()), 3), cavity_share=round(float((cavity > 0.5).mean()), 3))


if __name__ == "__main__":
    a = sys.argv[1:]
    def opt(n, d):
        if n in a: i = a.index(n); v = a[i + 1]; del a[i:i + 2]; return v
        return d
    arm, ai, src = opt("--arm", "A"), opt("--ai", None), opt("--albedo-src", "albedo")
    paint(a[0], a[1], arm, ai, src)
