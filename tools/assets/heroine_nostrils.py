"""Her nostrils' insides brought to the dark of each nostril's painted ring, in each face's paint.

Each face's lay painted her from flat views of her head, level, from in front and three-quarters either side: no view
saw up into her nostrils, so their insides kept a flat pale fill (the lay's pad), inside the dark ring the painting drew
at each nostril's mouth. Seen level the ring hid it; at the Look her chin is lifted 12 degrees (HerPose.ChinUp), we see
into her nostrils, and the pale fill read as a lump in each, on all nine preset faces (the owner, 12 October 2026: "see
the like lump in the nose"; a flat paint showed clean dark nostrils, so it was the paint).

This finds each nostril's inside on her head's mesh (heroine.glb's skin_head, under each face's own shape key, face_ID):
the points whose walls face across the cavity, by the share of a cone of rays about each point's normal (CONE degrees
wide, out to REACH) that meet her again. A nostril is a connected patch of points at least CORE blocked (the two
biggest, either side of her nose's middle), eased out to EDGE; laid in the paint by her UVs and feathered by FEATHER
texels. The paint there is brought to the ring's dark, measured per nostril and per face in the paint as it is: the
median of the darkest third of the texels on the ring (the band where the patch eases out, and 2 texels past it).
Everything else in the paint is left as it was (the jpg is written again at the chain's 95, 4:4:4, as heroine_ears.py
and heroine_jaw_cut.py write it): her nostrils' rims and wings as painted, the creases about her nose's wings untouched.

    python tools/assets/heroine_nostrils.py [face ...]           (no faces: every paint in godot/art/people/head_tex)
    python tools/assets/heroine_nostrils.py --measure [face ...]  (per nostril: its inside's colour and its ring's dark)

The chain: heroine_face.py's lay, heroine_jaw_cut.py, heroine_ears.py, heroine_lips.py, then this (it touches only the
insides of her nostrils, which none of them do). Idempotent: a nostril whose inside is no lighter than its ring's dark
(within TOL) is left as it is.
"""
import os
import re
import sys

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_seam as hs  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEX = os.path.join(ROOT, "godot", "art", "people", "head_tex")
GLB = os.path.join(ROOT, "godot", "art", "people", "heroine.glb")
CONE = 50.0          # (degrees: the cone of rays about each point's normal)
REACH = 0.012        # (metres: a ray meeting her within this is blocked)
RAYS = 64
CORE = 0.20          # (a point at least this blocked is inside a nostril)
FADE = 3.0           # (texels: the inside eased out past its edge, over its ring)
FEATHER = 1.0        # (texels: the mask softened)
RING_IN = 6.0        # (texels: the painted ring lies on the inside's edge, from this far in)
TOL = 4.0            # (8-bit luma: an inside this little lighter than its ring's dark is left)
# Her nose's base, where her nostrils are (her own shape, glTF metres: x across from her nose's tip, y up, z forward)
BOX = dict(x=0.020, y=(1.698, 1.718), z=0.088)
UVBOX = (0.38, 0.38, 0.52, 0.52)


def mesh():
    """Her head's points, UVs, triangles and the faces' shape keys (face_ID: the moves, not the shaped points)."""
    js, binc = hs._load(GLB)
    mats = [m.get("name") for m in js["materials"]]
    me = next(m for m in js["meshes"] if any(mats[p["material"]] == "skin_head" for p in m["primitives"]))
    prim = next(p for p in me["primitives"] if mats[p["material"]] == "skin_head")
    P = hs._read(js, binc, prim["attributes"]["POSITION"])
    UV = hs._read(js, binc, prim["attributes"]["TEXCOORD_0"])
    T = hs._read(js, binc, prim["indices"]).astype(np.int64).reshape(-1, 3)
    keys = {}
    for k, name in enumerate(me.get("extras", {}).get("targetNames", [])):
        mm = re.fullmatch(r"face_([a-z]+)", name)
        if mm:
            keys[mm.group(1)] = hs._read(js, binc, prim["targets"][k]["POSITION"])
    return P, UV, T, keys


def paints():
    out = {"own": "heroine_head.jpg"}
    for f in os.listdir(TEX):
        mm = re.fullmatch(r"heroine_head_(\w+)\.jpg", f)
        if mm:
            out[mm.group(1)] = f
    return out


def _normals(Q, T):
    n = np.cross(Q[T[:, 1]] - Q[T[:, 0]], Q[T[:, 2]] - Q[T[:, 0]])
    N = np.zeros_like(Q)
    for j in range(3):
        np.add.at(N, T[:, j], n)
    return N / (np.linalg.norm(N, axis=1)[:, None] + 1e-18)


def _blocked(o, dirs, V0, E1, E2, reach):
    """Each ray from o (Moller-Trumbore against every triangle given): does it meet one within reach."""
    pv = np.cross(dirs[:, None, :], E2[None])
    det = (E1[None] * pv).sum(-1)
    ok = np.abs(det) > 1e-14
    inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
    tv = o[None] - V0
    u = (tv[None] * pv).sum(-1) * inv
    qv = np.cross(tv, E1)
    v = (dirs[:, None, :] * qv[None]).sum(-1) * inv
    t = (E2[None] * qv[None]).sum(-1) * inv
    return (ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-6) & (t < reach)).any(1)


def occlusion(Q, T, vi):
    """Per point listed: the share of RAYS rays in a CONE-degree cone about its normal that meet her within REACH."""
    N = _normals(Q, T)
    rng = np.random.default_rng(5)
    cz = rng.uniform(np.cos(np.radians(CONE)), 1.0, RAYS)
    ph = rng.uniform(0.0, 2 * np.pi, RAYS)
    sz = np.sqrt(1 - cz ** 2)
    cone = np.stack([sz * np.cos(ph), sz * np.sin(ph), cz], 1)
    c = Q[T].mean(1)
    occ = np.zeros(len(vi))
    for k, i in enumerate(vi):
        n = N[i]
        a = np.array([1.0, 0, 0]) if abs(n[0]) < 0.9 else np.array([0, 1.0, 0])
        e1 = np.cross(n, a)
        e1 /= np.linalg.norm(e1)
        e2 = np.cross(n, e1)
        dirs = cone[:, :1] * e1 + cone[:, 1:2] * e2 + cone[:, 2:3] * n
        tt = T[np.linalg.norm(c - Q[i], axis=1) < REACH + 0.004]
        V0 = Q[tt[:, 0]]
        occ[k] = _blocked(Q[i] + n * 0.0002, dirs, V0, Q[tt[:, 1]] - V0, Q[tt[:, 2]] - V0, REACH).mean()
    return occ


def nostrils(P, UV, T, Q):
    """Each nostril's inside points (label 1: her right, -x; 2: her left: the two biggest connected patches at least
    CORE blocked) and every point's occlusion (-1 where not measured)."""
    tip = np.argmax(np.where(np.abs(P[:, 0]) < 0.004, P[:, 2], -9.0))
    xt = P[tip, 0]
    cand = ((np.abs(P[:, 0] - xt) < BOX["x"]) & (P[:, 1] > BOX["y"][0]) & (P[:, 1] < BOX["y"][1]) & (P[:, 2] > BOX["z"])
            & (UV[:, 0] > UVBOX[0]) & (UV[:, 1] > UVBOX[1]) & (UV[:, 0] < UVBOX[2]) & (UV[:, 1] < UVBOX[3]))
    vi = np.nonzero(cand)[0]
    occ = np.full(len(P), -1.0)
    occ[vi] = occlusion(Q, T, vi)
    E = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    A = coo_matrix((np.ones(len(E)), (E[:, 0], E[:, 1])), shape=(len(P), len(P))).tocsr()
    A = A + A.T

    def parts(keep):
        sel = np.nonzero(keep)[0]
        n, lab = connected_components(A[sel][:, sel], directed=False)
        out = np.full(len(P), -1)
        out[sel] = lab
        return out, np.bincount(lab, minlength=n)
    core, size = parts(cand & (occ >= CORE))
    label = np.zeros(len(P), int)
    for b in np.argsort(size)[::-1][:2]:
        v = core == b
        label[v] = 1 if P[v, 0].mean() < xt else 2
    assert sorted(np.unique(label[label > 0]).tolist()) == [1, 2], "two nostrils, one either side, not found"
    return label, occ


def raster(UV, T, vals, tris, n):
    """Per-point values (rows) drawn by her UVs over the triangles given, on an n x n map (NaN where none is)."""
    out = np.full((n, n, vals.shape[1]), np.nan)
    for t in tris:
        U = UV[T[t]] * n
        x0, x1 = max(int(np.floor(U[:, 0].min())), 0), min(int(np.ceil(U[:, 0].max())), n - 1)
        y0, y1 = max(int(np.floor(U[:, 1].min())), 0), min(int(np.ceil(U[:, 1].max())), n - 1)
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        a, v0, v1 = U[0], U[1] - U[0], U[2] - U[0]
        den = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(den) < 1e-12:
            continue
        qx, qy = xs + 0.5 - a[0], ys + 0.5 - a[1]
        b1 = (qx * v1[1] - v1[0] * qy) / den
        b2 = (v0[0] * qy - qx * v0[1]) / den
        m = (b1 >= -1e-3) & (b2 >= -1e-3) & (b1 + b2 <= 1 + 1e-3)
        val = vals[T[t]]
        out[ys[m], xs[m]] = (1 - b1 - b2)[m, None] * val[0] + b1[m, None] * val[1] + b2[m, None] * val[2]
    return out


def masks(P, UV, T, Q, n):
    """Per nostril (1, 2): its mask in the paint (1 inside, easing to 0 over FADE texels past its edge, feathered),
    its ring (the texels its dark is measured on: from RING_IN texels inside its edge to FADE + 1 past it) and its
    points' count."""
    core, occ = nostrils(P, UV, T, Q)
    out = {}
    for side in (1, 2):
        own = core == side
        # (its points' triangles and the ring of triangles about them: the inside's edge drawn where the cone is CORE)
        near = np.zeros(len(P), bool)
        near[T[own[T].any(1)].ravel()] = True
        tris = np.nonzero(near[T].any(1) & (occ[T] >= 0).all(1))[0]
        img = raster(UV, T, occ[:, None], tris, n)[..., 0]
        inside = np.nan_to_num(img, nan=-1) >= CORE
        lab, k = ndimage.label(inside)
        seen = {lab[min(n - 1, int(v * n)), min(n - 1, int(u * n))] for u, v in UV[own]} - {0}
        inside = ndimage.binary_fill_holes(np.isin(lab, sorted(seen)))
        # (a texel the inside closes round taken as inside: no light speck left within it)
        d = ndimage.distance_transform_edt(~inside)
        t = np.clip(1 - d / FADE, 0, 1)
        m = ndimage.gaussian_filter(t * t * (3 - 2 * t), FEATHER)
        ring = (d <= FADE + 1) & (ndimage.distance_transform_edt(inside) <= RING_IN)
        out[side] = (m, ring, int(own.sum()))
    return out


def luma(c):
    return c[..., 0] * 0.299 + c[..., 1] * 0.587 + c[..., 2] * 0.114


def dark_of(a, ring):
    px = a[ring]
    k = np.argsort(luma(px))[: max(1, len(px) // 4)]
    return np.median(px[k], 0)


def apply(faces, measure_only=False):
    P, UV, T, keys = mesh()
    pp = paints()
    for face in faces or sorted(pp):
        path = os.path.join(TEX, pp[face])
        a = np.asarray(Image.open(path).convert("RGB"), np.float64)
        Q = P if face == "own" else P + keys[face]
        out = a.copy()
        changed = False
        for side, (mf, ring, nv) in sorted(masks(P, UV, T, Q, a.shape[0]).items()):
            dark = dark_of(a, ring)
            inside = np.median(a[mf > 0.95], 0)
            lift = luma(inside) - luma(dark)
            name = ("right", "left")[side - 1]
            print(f"{face:9s} {name:5s} {nv:4d} points, {int((mf > 0.02).sum()):5d} texels: inside {np.round(inside).astype(int)} "
                  f"(luma {luma(inside):.0f}), ring's dark {np.round(dark).astype(int)} (luma {luma(dark):.0f})"
                  + ("" if measure_only else ("  left as it is" if lift <= TOL else "  brought to it")))
            if measure_only or lift <= TOL:
                continue
            out = out * (1 - mf[..., None]) + dark * mf[..., None]
            changed = True
        if changed:
            Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8)).save(path, quality=95, subsampling=0)
            print(f"{face}: written {path}")


if __name__ == "__main__":
    if sys.argv[1:2] == ["--measure"]:
        apply(sys.argv[2:], measure_only=True)
    else:
        apply(sys.argv[1:])
