"""The Ford-Warden's long full grey beard as hair cards (godot/art/npc/ford_warden/beard.glb), a beard style on
our hair-card tooling.

    python tools/assets/warden_beard.py PKG_DIR [--work DIR] [--seed N]

No Blender: heroine_hair.py's own guide-strand and card functions (resample, drape, onto, cards) are lifted out of it
unchanged (reuse(): their source taken from the file, run with this package's collider in their globals), and
warden_head.py's Glb reads and writes the package. Their frame is Blender's (Z up, front -Y): the beard is built in it
and written back in glTF's.

  1. roots on the Face Forge head (body.glb, material warden_face): under a line just below the cheekbones, rising at
     the sides to meet the hood's side edge (and running under it), down the jaw and under the chin to the hood's
     opening; none on the lips. Thinned toward that line (no hard edge), with short fine cards lying on the skin there;
  2. the mustache: guides from the upper lip combed down and out over the mouth's corners;
  3. the beard: three layers of guides (wide dense cards close to the skin, a middle layer, an outer layer of wet locks
     gathered to points), let fall by heroine_hair.drape with this package's collider (the face) and a front surface
     (the body, tabard and capelet seen from the front: nothing goes behind it), combed in to a tapering lane, down to
     the belt; the middle and outer layers' tips gathered into wet clumps;
  4. cards by heroine_hair.cards on the strand atlas godot/art/people/head_tex/hair_strands.png (grey root to tip, the
     game dyes it: People.Hair, the manifest's hair colour); vertex colour as hers (r depth, g card number, a cover);
  5. skinned: Head at the roots, easing into the body's own spine chain weights where it lies on him (neck_01,
     spine_03, spine_02 by where it lies), a share of Head left to the tip (it swings a little with the head);
  6. beard.glb on body.glb's skeleton: meshes beard (material "hair"), beard.lod1 (~2k) and beard.shadow (opaque, its
     own material "beard_shadow"); the manifest's "hair": {"file": "beard.glb", "colour"}. NpcPackage lays it.
Previews (front and side splats) and the numbers in --work.
"""
import argparse
import ast
import json
import os
import struct
import sys
import time
import types

import numpy as np
import trimesh
from PIL import Image, ImageDraw
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ATLAS = os.path.join(ROOT, "godot", "art", "people", "head_tex", "hair_strands.png")
ATLAS_URI = "../../people/head_tex/hair_strands.png"   # (from godot/art/npc/ford_warden/beard.glb)


def log(*a):
    print("[warden_beard]", *a, flush=True)


# ================= reuse =================
def reuse(path, names, ns):
    """The named top-level functions, classes and assignments of a script, run into `ns` (their globals): reused as
    written, without running the script (heroine_hair.py builds her styles from her blend when run)."""
    src = open(path, encoding="utf-8").read()
    got = set()
    for node in ast.parse(src).body:
        nm = getattr(node, "name", None)
        if isinstance(node, ast.Assign):
            nm = next((t.id for t in node.targets if isinstance(t, ast.Name) and t.id in names), None)
        if nm in names:
            exec(compile(ast.Module([node], []), path, "exec"), ns)
            got.add(nm)
    missing = set(names) - got
    assert not missing, f"not in {path}: {missing}"
    return ns


class _Quat:
    def __init__(self, wxyz):
        self.q = wxyz

    def to_matrix(self):
        w, x, y, z = self.q
        return Rotation.from_quat([x, y, z, w]).as_matrix()


GLB = reuse(os.path.join(HERE, "warden_head.py"), {"CT", "NC", "Glb"},
            dict(np=np, json=json, struct=struct, mathutils=types.SimpleNamespace(Quaternion=_Quat)))
Glb = GLB["Glb"]
HH = reuse(os.path.join(HERE, "heroine_hair.py"), {"KINDS", "COLUMNS", "resample", "drape", "onto", "cards"}, dict(np=np))
# (the atlas's columns: dense 0-5, loose 6-10, locks 11-13 (gathered to a point at the tip), wisps 14-15)
DENSE, LOOSE, LOCK, WISP = (list(range(0, 6)), list(range(6, 11)), list(range(11, 14)), list(range(14, 16)))


def g2b(a):  # glTF (Y up, front +Z) -> Blender (Z up, front -Y)
    a = np.asarray(a, float)
    return np.stack([a[..., 0], -a[..., 2], a[..., 1]], -1)


def b2g(a):
    a = np.asarray(a, float)
    return np.stack([a[..., 0], a[..., 2], -a[..., 1]], -1)


# ================= the shape (package frame, glTF: Y up, metres, front +Z) =================
X0 = 0.0204                       # the face's centre line (between the irises)
CENTRE_G = np.array([X0, 1.625, 0.0])   # the skull's middle, near enough (for the cards' normals over the face)
# the beard's top line on the face: (|x - X0|, y); under the nose, beside its wings, under the cheekbones, rising at
# the sides to the hood's side edge (OPENING in warden_hood.py: x 0.064-0.067 from the centre at these heights) and
# on under it
TOP = [(0.000, 1.6075), (0.012, 1.6085), (0.018, 1.6115), (0.024, 1.6160), (0.032, 1.6210), (0.045, 1.6270),
       (0.056, 1.6330), (0.064, 1.6440), (0.072, 1.6560), (0.090, 1.6650)]
TOP_JIT = 0.0018                  # the line pushed up and down this much along it (no drawn edge)
SOFT = 0.007                      # the roots thin out over this far below the line
SIDE = 0.088                      # roots to this far from the centre line (under the hood's side)
SIDE_WALL = 0.080                 # no guide point further out than this over the face (inside the hood's side wall)
BACK_Z = -0.030                   # and no further back than this
LIPS = (0.0255, 1.5755, 1.5945)   # no roots on the lips: |dx| under this, between these heights
CHIN_FLOOR = 1.528                # no roots under this at the front (inside the hood's opening's bottom, 1.512-1.528)
MUSTACHE = (0.027, 1.5945)        # the upper lip: |dx| under this, above the lips
TIP_Y = (1.075, 1.20)             # the tips: at the centre (the belt, at about 1.03-1.05), and at the sides
LANE = ([0.95, 1.15, 1.35, 1.47, 1.55], [0.52, 0.56, 0.72, 0.9, 1.0])   # the beard's width (of its roots') by height
LAYERS = [
    # name, root spacing, held off, card width, columns, narrowing, shade (depth), points, clump pull, tip jitter
    dict(name="inner", spacing=0.019, off=0.0045, width=(0.036, 0.046), cols=DENSE, narrow=0.45, shade=(0.40, 0.55), K=13, clump=0.15, jit=0.03),
    dict(name="mid", spacing=0.021, off=0.0125, width=(0.030, 0.038), cols=DENSE + LOOSE, narrow=0.62, shade=(0.62, 0.80), K=13, clump=0.45, jit=0.06),
    dict(name="outer", spacing=0.022, off=0.0205, width=(0.016, 0.024), cols=LOCK + LOOSE[:2], narrow=0.88, shade=(0.85, 1.0), K=13, clump=0.65, jit=0.09),
]
MOUSTACHE = dict(spacing=0.0040, off=0.0030, width=(0.010, 0.016), cols=LOCK + DENSE[:3], narrow=0.80, shade=(0.62, 0.95), K=9,
                 length=(0.060, 0.095))
FINE = dict(off=0.0012, width=(0.005, 0.009), cols=WISP + LOOSE, narrow=0.7, shade=(0.75, 0.95), K=5, length=(0.014, 0.030),
            alpha=(0.45, 0.8))
LOD1 = dict(every={"inner": 3, "mid": 2, "outer": 2}, K=8, wide=1.7)   # beard.lod1: a share of each layer's guides, wider, fewer points
SHADOW = dict(every=2, K=6, wide=2.0)        # beard.shadow: every second inner-layer guide
COLOUR = "#7a7871"                # the dye: old river-wet grey (concept A: neutral grey, a touch warm; darker wet roots by the shader)
SPINE = ["pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "Head"]


def top_y(adx):
    t = np.array(TOP)
    return np.interp(adx, t[:, 0], t[:, 1])


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


# ================= the package =================
def prims(path):
    g = Glb(path)
    out = {}
    for m in g.j["meshes"]:
        for p in m["primitives"]:
            mat = g.j["materials"][p["material"]]["name"] if "material" in p else ""
            a = p["attributes"]
            out[(m["name"], mat)] = dict(P=g.acc(a["POSITION"]).astype(float), F=g.acc(p["indices"]).reshape(-1, 3).astype(np.int64),
                                         J=g.acc(a["JOINTS_0"]).astype(np.int64) if "JOINTS_0" in a else None,
                                         W=g.acc(a["WEIGHTS_0"]).astype(float) if "WEIGHTS_0" in a else None)
    return g, out


def sample_surface(P, F, spacing, rng, keep=None):
    """Points over triangles about `spacing` apart (area-weighted, random) and their faces' normals."""
    a, b, c = P[F[:, 0]], P[F[:, 1]], P[F[:, 2]]
    cr = np.cross(b - a, c - a)
    area = 0.5 * np.linalg.norm(cr, axis=1)
    if keep is not None:
        area = area * keep
    n = int(area.sum() / spacing ** 2) + 1
    k = rng.choice(len(F), n, p=area / area.sum())
    u, v = rng.random(n), rng.random(n)
    flip = u + v > 1
    u[flip], v[flip] = 1 - u[flip], 1 - v[flip]
    pts = a[k] + (b[k] - a[k]) * u[:, None] + (c[k] - a[k]) * v[:, None]
    nrm = cr[k] / (np.linalg.norm(cr[k], axis=1)[:, None] + 1e-12)
    return pts, nrm, k


def thin(pts, spacing, rng):
    """Kept unless one kept is nearer than `spacing` (heroine_hair.roots's thinning)."""
    order = rng.permutation(len(pts))
    kept, tree, keep = [], None, []
    for i in order:
        if tree is not None and tree.query(pts[i])[0] < spacing:
            continue
        if kept and tree is None and np.min(np.linalg.norm(np.array(kept) - pts[i], axis=1)) < spacing:
            continue
        kept.append(pts[i])
        keep.append(i)
        if len(keep) % 40 == 0:
            tree = cKDTree(np.array(kept))
    keep = np.array(keep)
    d, _ = cKDTree(pts[keep]).query(pts[keep], k=2)
    return keep[d[:, 1] > spacing * 0.7]


class Package:
    def __init__(self, pkg, rng):
        t0 = time.time()
        self.pkg = pkg
        self.g, self.body = prims(os.path.join(pkg, "body.glb"))
        skin = self.g.j["skins"][0]
        self.names = [self.g.j["nodes"][n]["name"] for n in skin["joints"]]
        self.face = next(v for (m, mat), v in self.body.items() if mat == "warden_face")
        hood_path = os.path.join(pkg, "armor", "hood.glb")
        self.hood = None
        if os.path.exists(hood_path):
            _, hp = prims(hood_path)
            self.hood = next((v for (m, mat), v in hp.items() if mat == "warden_hood_wool" and "lod1" not in m and "shadow" not in m), None)
        # the face's collider for the drape (heroine_hair's COLLIDE): dense points over the head and neck
        fp, fn, _ = sample_surface(self.face["P"], self.face["F"], 0.0016, rng)
        self.face_pts, self.face_nrm = fp, fn
        # every surface (body, face, patch, the hood's wool), for the cards' normals and the measures
        Vs, Fs, o = [], [], 0
        for (m, mat), d in self.body.items():
            Vs.append(d["P"]); Fs.append(d["F"] + o); o += len(d["P"])
        self.body_tm = trimesh.Trimesh(np.concatenate(Vs), np.concatenate(Fs), process=False)
        if self.hood is not None:
            Vs.append(self.hood["P"]); Fs.append(self.hood["F"] + o); o += len(self.hood["P"])
        self.all_tm = trimesh.Trimesh(np.concatenate(Vs), np.concatenate(Fs), process=False)
        keep = (self.all_tm.triangles_center[:, 1] > 0.95) & (self.all_tm.triangles_center[:, 1] < 1.70)
        ap, an, k = sample_surface(self.all_tm.vertices, self.all_tm.faces, 0.004, rng, keep=keep)
        self.all_pts, self.all_nrm = ap, an
        # (the drape's collider: the face and the body, and the hood only below its opening (the capelet's front the
        # beard lies on): over the cheeks a point between the face and the hood's side is inside the hood's outer
        # surface, and was thrown out through it)
        nb = len(self.body_tm.faces)
        face_tri = np.zeros(len(self.all_tm.faces), bool)
        o = 0
        for (m, mat), d in self.body.items():
            if mat == "warden_face":
                face_tri[o:o + len(d["F"])] = True
            o += len(d["F"])
        drop = face_tri[k] | ((k >= nb) & (ap[:, 1] > 1.53))
        self.drape_pts = np.vstack([fp, ap[~drop]])
        self.drape_nrm = np.vstack([fn, an[~drop]])
        self.drape_face = np.r_[np.ones(len(fp), bool), np.zeros((~drop).sum(), bool)]
        self.front = self.front_map()
        # the body's spine-chain weights (the donor where the beard lies on him)
        bp, bj, bw = [], [], []
        for (m, mat), d in self.body.items():
            if d["J"] is None or mat == "warden_face":
                continue
            bp.append(d["P"]); bj.append(d["J"]); bw.append(d["W"])
        self.donor_P, self.donor_J, self.donor_W = np.concatenate(bp), np.concatenate(bj), np.concatenate(bw)
        self.donor_tree = cKDTree(self.donor_P)
        log(f"package read: face {len(self.face['P'])} verts, collider {len(fp)} face points, {len(ap)} surface points, "
            f"hood {'yes' if self.hood is not None else 'no'} ({time.time() - t0:.1f} s)")

    def front_map(self, step=0.003):
        """The front surface seen from the front: for (x, y), the frontmost z of the body, patch and hood (filled where
        a ray missed); nothing of the beard below the chin goes behind it."""
        xs = np.arange(X0 - 0.26, X0 + 0.2601, step)
        ys = np.arange(0.95, 1.5601, step)
        # (a depth buffer of dense surface samples: trimesh's rays without embree took minutes)
        tm = self.all_tm
        c = tm.triangles_center
        keep = (c[:, 1] > 0.93) & (c[:, 1] < 1.58) & (np.abs(c[:, 0] - X0) < 0.28)
        P, _, _ = sample_surface(tm.vertices, tm.faces, step / 3.0, np.random.default_rng(5), keep=keep.astype(float))
        ix = np.round((P[:, 0] - xs[0]) / step).astype(int)
        iy = np.round((P[:, 1] - ys[0]) / step).astype(int)
        ok = (ix >= 0) & (ix < len(xs)) & (iy >= 0) & (iy < len(ys))
        Z = np.full((len(ys), len(xs)), -np.inf)
        np.maximum.at(Z, (iy[ok], ix[ok]), P[ok, 2])
        Z[np.isinf(Z)] = np.nan
        from scipy import ndimage
        bad = np.isnan(Z)
        if bad.any():
            idx = ndimage.distance_transform_edt(bad, return_distances=False, return_indices=True)
            Z = Z[tuple(idx)]
        Z = ndimage.grey_dilation(Z, size=(3, 3))   # (a little past the folds' crests)
        return dict(xs=xs, ys=ys, Z=Z)

    def front_z(self, x, y):
        f = self.front
        ix = np.clip((x - f["xs"][0]) / (f["xs"][1] - f["xs"][0]), 0, len(f["xs"]) - 1.001)
        iy = np.clip((y - f["ys"][0]) / (f["ys"][1] - f["ys"][0]), 0, len(f["ys"]) - 1.001)
        x0, y0 = ix.astype(int), iy.astype(int)
        fx, fy = ix - x0, iy - y0
        Z = f["Z"]
        return (Z[y0, x0] * (1 - fx) * (1 - fy) + Z[y0, x0 + 1] * fx * (1 - fy) + Z[y0 + 1, x0] * (1 - fx) * fy + Z[y0 + 1, x0 + 1] * fx * fy)


# ================= 1. roots =================
def root_points(pk, rng, spacing, region):
    """Roots over the face about `spacing` apart in a region ("beard", "moustache", "edge"), thinned toward the top
    line. Returns glTF points, normals and each one's depth below the (jittered) line."""
    F = pk.face
    pts, nrm, _ = sample_surface(F["P"], F["F"], spacing / 3.0, rng)
    dx = pts[:, 0] - X0
    adx = np.abs(dx)
    # (the line jittered along its length, ~10 mm a wave: no drawn edge)
    ph = rng.random(3) * 6.28
    s = np.arctan2(dx, 0.05) * 0.09
    jit = TOP_JIT * (np.sin(s * 700 + ph[0]) * 0.6 + np.sin(s * 1700 + ph[1]) * 0.4)
    below = top_y(adx) + jit - pts[:, 1]
    ok = (adx < SIDE) & (pts[:, 2] > BACK_Z) & (nrm[:, 2] > -0.45) & (pts[:, 1] > 1.48)
    ok &= ~((adx < LIPS[0]) & (pts[:, 1] > LIPS[1]) & (pts[:, 1] < LIPS[2]))
    ok &= ~((adx < 0.05) & (pts[:, 1] < CHIN_FLOOR))
    # (the under-jaw: not deep under the chin towards the throat inside the hood)
    ok &= ~((pts[:, 1] < 1.545) & (pts[:, 2] < 0.035) & (adx < 0.06))
    mous = (adx < MUSTACHE[0]) & (pts[:, 1] >= MUSTACHE[1])
    if region == "moustache":
        ok &= mous & (below > 0.0015)
    elif region == "edge":
        ok &= (below > -0.001) & (below < SOFT) & ~mous
    else:
        ok &= (below > 0.0025) & ~mous
    pts, nrm, below = pts[ok], nrm[ok], below[ok]
    k = thin(pts, spacing, rng)
    pts, nrm, below = pts[k], nrm[k], below[k]
    if region == "beard":
        # (fewer toward the line: the beard thins out into the skin, as a real one grows)
        p = smoothstep(0.0025, SOFT + 0.006, below)
        k = rng.random(len(pts)) < 0.25 + 0.75 * p
        pts, nrm, below = pts[k], nrm[k], below[k]
    return pts, nrm, below


# ================= 2-3. guides =================
def collider(pk, face_only=True):
    """heroine_hair's collider globals, in Blender's frame: the face's points (the drape) or every surface's (the
    cards' normals and their hold off him)."""
    if face_only:
        P, N, isf = pk.drape_pts, pk.drape_nrm, pk.drape_face
    else:
        P, N = np.vstack([pk.face_pts, pk.all_pts]), np.vstack([pk.face_nrm, pk.all_nrm])
        isf = np.r_[np.ones(len(pk.face_pts), bool), np.zeros(len(pk.all_pts), bool)]
    Pb, Nb = g2b(P), g2b(N)
    HH.update(COLLIDE_P=Pb, COLLIDE_N=Nb, COLLIDE=cKDTree(Pb), NECK=np.zeros(len(Pb), bool), NECK_CLEAR=0.0,
              COLLIDE_HEAD=isf & (P[:, 1] > 1.555),
              CENTRE=g2b(CENTRE_G), rise=lambda q: np.ones(len(q)))


def comb_dirs(pts, nrm, region, rng):
    """Each guide's start: the moustache down and out over the mouth's corners; the beard down, off the skin, the
    sides forward toward the chin (glTF)."""
    dx = pts[:, 0] - X0
    sg = np.sign(dx) + (dx == 0)
    if region == "moustache":
        d = np.c_[sg * (0.55 + 0.25 * rng.random(len(pts))), -np.ones(len(pts)), 0.55 + 0.15 * rng.random(len(pts))]
    else:
        side = smoothstep(0.03, 0.075, np.abs(dx))
        d = np.c_[-sg * 0.25 * side, -np.ones(len(pts)), 0.25 + 0.55 * side + 0.25 * (pts[:, 2] < 0.09)]
        d = d + nrm * (0.35 - 0.25 * side)[:, None]
    return d / np.linalg.norm(d, axis=1)[:, None]


def keep_front(pk, Pb, off, below_y=1.545, lane=None, roots_x=None, comb=0.0):
    """Points (Blender frame) below the chin held `off` in front of the front surface, and combed in to the lane."""
    S, K, _ = Pb.shape
    flat = Pb.reshape(-1, 3)
    y = flat[:, 2]
    low = y < below_y
    if comb > 0 and roots_x is not None:
        rx = np.repeat(roots_x, K)
        want = X0 + (rx - X0) * np.interp(y, LANE[0], LANE[1])
        w = comb * smoothstep(below_y, below_y - 0.06, y)
        flat[:, 0] += (want - flat[:, 0]) * w
    # (over the face, the sides held in under the hood's side wall: a guide rooted there lies on the cheek)
    hi = y > 1.50
    lim = X0 + np.sign(flat[:, 0] - X0) * SIDE_WALL
    over = hi & (np.abs(flat[:, 0] - X0) > SIDE_WALL)
    flat[over, 0] = lim[over]
    zf = pk.front_z(flat[:, 0], y) + np.repeat(off if np.ndim(off) else np.full(S, off), K)
    zg = -flat[:, 1]
    # (eased in over the last 15 mm above the line: no kink at the chin)
    ease = smoothstep(below_y + 0.015, below_y, y)
    push = low | (ease > 0)
    need = np.maximum(zf - zg, 0) * np.where(low, 1.0, ease)
    flat[push, 1] -= need[push]
    return flat.reshape(S, K, 3)


def grow(pk, pts, nrm, region, cfg, rng, length, tip_y=None):
    """Guides from the roots (glTF), let fall by heroine_hair.drape (Blender frame); returns Blender-frame strands."""
    dirs = comb_dirs(pts, nrm, region, rng)
    starts = g2b(pts + nrm * 0.0008)
    db = g2b(dirs)
    off = cfg["off"] * (0.85 + 0.3 * rng.random(len(pts)))
    rx = pts[:, 0]
    K = 24 if region == "beard" else 12

    def extra(P, step):
        if region == "beard":
            P[:] = keep_front(pk, P, off, roots_x=rx, comb=0.04)
        else:
            P[:] = keep_front(pk, P, off, below_y=-1.0)

    collider(pk, face_only=True)
    P = HH["drape"](starts, db, length, points=K, offset=off, stiff_root=0.02 if region != "beard" else 0.03,
                    steps=140 if region == "beard" else 90, gravity=1.0, extra=extra)
    if region == "beard":
        P = keep_front(pk, P, off, roots_x=rx, comb=0.0)
    return P, off


def clump(P, share, n_clumps, rng, start=0.25):
    """Wet clumps: the guides gathered toward their clump's mean path from `start` of the way along, more and more to
    the tip (`share` there): a beard of many wet points, not ropes (many small clumps)."""
    S, K, _ = P.shape
    if share <= 0 or S < 4:
        return P
    feat = np.c_[P[:, K // 2, :] , P[:, -1, :] * 0.5]
    from scipy.cluster.vq import kmeans2
    _, lab = kmeans2(feat, min(n_clumps, S // 2), seed=int(rng.integers(1 << 30)), minit="++")
    out = P.copy()
    f = np.linspace(0, 1, K)
    w = np.clip((f - start) / (1 - start), 0, 1) ** 1.4 * share
    for c in np.unique(lab):
        m = lab == c
        if m.sum() < 2:
            continue
        mean = P[m].mean(0)
        out[m] = P[m] + (mean[None] - P[m]) * w[None, :, None] * (0.75 + 0.25 * rng.random(m.sum()))[:, None, None]
    return out


# ================= 4. cards =================
def card_set(P, cfg, rng, K, wide=1.0, shade=None, alpha=None, edge=False):
    """heroine_hair.cards on Blender-frame guides (resampled to K points): its vertices, normals, UVs, faces, vertex
    colour (r depth, g card number, b 0, a cover) and each vertex's guide point."""
    Q = HH["resample"](P, K)
    S = len(Q)
    width = rng.uniform(*cfg["width"], S) * wide
    HH["RNG"] = rng
    c = HH["cards"](Q, width, cfg["cols"], cfg["off"], root=np.full(S, 0.6 if not edge else 0.9), narrow=cfg["narrow"], floor=0.001, edge_in=False)
    nv = 3 * K
    lo, hi = shade if shade is not None else cfg["shade"]
    r = np.repeat(rng.uniform(lo, hi, S), nv)
    a = np.repeat(rng.uniform(*alpha, S) if alpha is not None else np.ones(S), nv)
    C = np.c_[r, c["card"], np.zeros(len(r)), a]
    return dict(V=c["V"], N=c["N"], UV=c["UV"], F=c["F"], C=C, at=c["at"], along=c["along"], arc=c["arc"], S=S, K=K)


def merge(sets):
    out = {k: [] for k in ("V", "N", "UV", "F", "C", "at", "arc")}
    o = 0
    for s in sets:
        for k in ("V", "N", "UV", "C", "at", "arc"):
            out[k].append(s[k])
        out["F"].append(s["F"] + o)
        o += len(s["V"])
    return {k: np.concatenate(v) for k, v in out.items()}


# ================= 5. skin =================
def weights(pk, at_g, arc):
    """Per vertex (glTF guide points): Head at the roots, the body's own spine-chain weights where it lies on him, a
    share of Head left to the tip."""
    names = pk.names
    bi = {n: i for i, n in enumerate(names)}
    chain = np.array([bi[n] for n in SPINE if n in bi])
    nb = len(names)
    _, idx = pk.donor_tree.query(at_g)
    Wd = np.zeros((len(at_g), nb))
    np.add.at(Wd, (np.repeat(np.arange(len(at_g)), 4), pk.donor_J[idx].ravel()), pk.donor_W[idx].ravel())
    mask = np.zeros(nb, bool)
    mask[chain] = True
    Wd[:, ~mask] = 0
    s = Wd.sum(1)
    Wd[s < 1e-6, bi["spine_03"]] = 1.0
    Wd /= Wd.sum(1)[:, None]
    y = at_g[:, 1]
    # (Head on the face and just under the chin; easing to its tip share down the chest)
    # (r1: 1 to 0.12 over 17 cm read 1.44x stretch p99 and splayed cards in C03 s1's head turn; now a longer ramp
    # through the neck, smoothed, and a smaller share at the tip)
    h = smoothstep(1.33, 1.535, y) * 0.94 + 0.06
    W = Wd * (1 - h)[:, None]
    W[:, bi["Head"]] += h
    order = np.argsort(-W, axis=1)[:, :4]
    J = order
    Wt = np.take_along_axis(W, order, 1)
    Wt[Wt < 0.01] = 0
    Wt /= Wt.sum(1)[:, None]
    return J.astype(np.uint16), Wt.astype(np.float32)


def tangents(V, N, F, at, S_list):
    """Across the card (u: left edge to right) with w so that N x T x w runs root to tip (heroine_hair.gdshaderinc reads
    the strand along BINORMAL)."""
    T = np.zeros_like(V)
    o = 0
    for S, K in S_list:
        n = S * 3 * K
        v = V[o:o + n].reshape(S, 3, K, 3)
        side = v[:, 2] - v[:, 0]
        side /= np.linalg.norm(side, axis=2)[:, :, None] + 1e-12
        T[o:o + n] = np.repeat(side[:, None], 3, 1).reshape(-1, 3)
        o += n
    T -= N * (T * N).sum(1)[:, None]
    T /= np.linalg.norm(T, axis=1)[:, None] + 1e-12
    along = np.zeros_like(V)
    o = 0
    for S, K in S_list:
        n = S * 3 * K
        a = at[o:o + n].reshape(S, 3, K, 3)[:, 1]
        t = np.zeros_like(a)
        t[:, 1:-1] = a[:, 2:] - a[:, :-2]
        t[:, 0], t[:, -1] = a[:, 1] - a[:, 0], a[:, -1] - a[:, -2]
        along[o:o + n] = np.repeat(t[:, None], 3, 1).reshape(-1, 3)
        o += n
    w = np.sign((np.cross(N, T) * along).sum(1))
    w[w == 0] = 1
    return np.c_[T, w].astype(np.float32)


# ================= 6. write =================
def write(pk, path, parts):
    """beard.glb: body.glb's skeleton and skin, its meshes replaced by the beard's (parts: [(node, prim dict, mat)])."""
    g = Glb(os.path.join(pk.pkg, "body.glb"))
    j = g.j
    drop = [i for i, n in enumerate(j["nodes"]) if n.get("name", "").startswith("ford_warden") and n.get("name") != "ford_warden"]
    g.drop_nodes(drop)
    j["materials"], j["textures"], j["images"], j["samplers"] = [], [], [], []
    j["meshes"] = []
    j["images"] = [{"uri": ATLAS_URI, "name": "hair_strands"}]
    j["samplers"] = [{"magFilter": 9729, "minFilter": 9987, "wrapS": 33071, "wrapT": 33071}]
    j["textures"] = [{"source": 0, "sampler": 0}]
    j["materials"] = [
        {"name": "hair", "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}, "metallicFactor": 0.0, "roughnessFactor": 0.6},
         "alphaMode": "MASK", "alphaCutoff": 0.4, "doubleSided": True},
        {"name": "beard_shadow", "pbrMetallicRoughness": {"baseColorFactor": [0.2, 0.2, 0.2, 1.0], "metallicFactor": 0.0, "roughnessFactor": 1.0},
         "doubleSided": True},
    ]
    arm = j["scenes"][0]["nodes"][0]
    body_node = next(i for i, n in enumerate(j["nodes"]) if n.get("name") == "ford_warden")
    for k, (node_name, d, mat) in enumerate(parts):
        a = {"POSITION": g.add_acc(d["pos"].astype(np.float32), "VEC3", minmax=True), "NORMAL": g.add_acc(d["nrm"].astype(np.float32), "VEC3"),
             "JOINTS_0": g.add_acc(d["J"], "VEC4"), "WEIGHTS_0": g.add_acc(d["W"], "VEC4")}
        if "uv" in d:
            a["TANGENT"] = g.add_acc(d["tan"], "VEC4")
            a["TEXCOORD_0"] = g.add_acc(d["uv"].astype(np.float32), "VEC2")
            a["TEXCOORD_1"] = g.add_acc(np.zeros((len(d["pos"]), 2), np.float32), "VEC2")   # (no chain: it swings by its skin)
            a["COLOR_0"] = g.add_acc(d["col"].astype(np.float32), "VEC4")
        mesh = {"name": node_name, "primitives": [{"attributes": a, "indices": g.add_acc(d["idx"].astype(np.uint32).ravel(), "SCALAR", target=34963),
                                                    "material": mat, "mode": 4}]}
        j["meshes"].append(mesh)
        if k == 0:
            j["nodes"][body_node] = {"name": node_name, "mesh": 0, "skin": 0}
        else:
            j["nodes"].append({"name": node_name, "mesh": k, "skin": 0})
            j["nodes"][arm].setdefault("children", []).append(len(j["nodes"]) - 1)
    g.save(path)
    log(f"wrote {path} ({os.path.getsize(path) / 1e6:.2f} MB)")


def tris_of(F):
    return np.vstack([F[:, [0, 1, 2]], F[:, [0, 2, 3]]])


def part(pk, cs):
    m = merge(cs)
    at_g = b2g(m["at"])
    J, W = weights(pk, at_g, m["arc"])
    V, N = b2g(m["V"]), b2g(m["N"])
    T = tris_of(m["F"])
    tan = tangents(V, N, T, at_g, [(c["S"], c["K"]) for c in cs])
    uv = m["UV"].copy()
    uv[:, 1] = 1 - uv[:, 1]   # (heroine_hair writes v = 1 - along for Blender, whose glTF export flips it: here along itself)
    return dict(pos=V, nrm=N, uv=uv, col=m["C"], J=J, W=W, idx=T, tan=tan, at=at_g)


# ================= previews and numbers =================
def splat(pk, mesh, path, view="front", res=0.0009):
    """A quick look without Godot: the face and body (grey shaded) and the cards (the atlas's alpha, shaded by their
    depth), splatted with a depth buffer."""
    atlas = np.asarray(Image.open(ATLAS).convert("RGBA")).astype(float) / 255
    box = (X0 - 0.22, X0 + 0.22, 0.98, 1.72) if view == "front" else (-0.22, 0.26, 0.98, 1.72)
    W_, H_ = int((box[1] - box[0]) / res), int((box[3] - box[2]) / res)
    img = np.zeros((H_, W_, 3))
    zb = np.full((H_, W_), -9.0)
    rng = np.random.default_rng(1)
    L = np.array([0.4, 0.5, 0.75]); L /= np.linalg.norm(L)

    def put(X, col, depth):
        if view == "front":
            u, v = X[:, 0], X[:, 1]
        else:
            u, v = X[:, 2], X[:, 1]
        ix = ((u - box[0]) / res).astype(int)
        iy = (H_ - 1 - (v - box[2]) / res).astype(int)
        ok = (ix >= 0) & (ix < W_) & (iy >= 0) & (iy < H_)
        ix, iy, col, depth = ix[ok], iy[ok], col[ok], depth[ok]
        o = np.argsort(depth)
        ix, iy, col, depth = ix[o], iy[o], col[o], depth[o]
        better = depth > zb[iy, ix]
        zb[iy[better], ix[better]] = depth[better]
        img[iy[better], ix[better]] = col[better]

    tm = pk.all_tm
    keep = tm.triangles_center[:, 1] > 0.95
    for _ in range(3):
        P, Nn, k = sample_surface(tm.vertices, tm.faces[keep], res * 0.6, rng)
        sh = np.clip(Nn @ L, 0.05, 1)[:, None] * np.array([0.45, 0.42, 0.40])
        put(P, sh, P[:, 2] if view == "front" else -P[:, 0])
    V, F, UV, C = mesh["pos"], mesh["idx"], mesh["uv"], mesh["col"]
    for _ in range(6):
        P, Nn, k = sample_surface(V, F, res * 0.5, rng)
        a, b, c = V[F[k, 0]], V[F[k, 1]], V[F[k, 2]]
        # barycentric UV
        v0, v1, v2 = b - a, c - a, P - a
        d00, d01, d11 = (v0 * v0).sum(1), (v0 * v1).sum(1), (v1 * v1).sum(1)
        d20, d21 = (v2 * v0).sum(1), (v2 * v1).sum(1)
        den = d00 * d11 - d01 * d01 + 1e-18
        bv, bw = (d11 * d20 - d01 * d21) / den, (d00 * d21 - d01 * d20) / den
        bu = 1 - bv - bw
        uv = UV[F[k, 0]] * bu[:, None] + UV[F[k, 1]] * bv[:, None] + UV[F[k, 2]] * bw[:, None]
        col = C[F[k, 0]] * bu[:, None] + C[F[k, 1]] * bv[:, None] + C[F[k, 2]] * bw[:, None]
        h, w = atlas.shape[:2]
        t = atlas[np.clip((uv[:, 1] * h).astype(int), 0, h - 1), np.clip((uv[:, 0] * w).astype(int), 0, w - 1)]
        cover = t[:, 3] * col[:, 3] * smoothstep(0, 0.012, uv[:, 1])
        m = cover > 0.45
        nrm = mesh["nrm"][F[k, 0]]
        lit = 0.35 + 0.65 * np.clip(np.abs(nrm @ L), 0, 1)
        shade = (t[:, 0] * col[:, 0] * lit)[:, None] * np.array([0.78, 0.77, 0.74])
        put(P[m], shade[m], (P[:, 2] if view == "front" else -P[:, 0])[m] + 0.0005)
    out = Image.fromarray((np.clip(img, 0, 1) ** (1 / 1.4) * 255).astype(np.uint8))
    dr = ImageDraw.Draw(out)
    for yy in np.arange(1.0, 1.72, 0.05):
        y = int(H_ - 1 - (yy - box[2]) / res)
        dr.line([(0, y), (12, y)], fill=(255, 60, 60))
        dr.text((14, y - 6), f"{yy:.2f}", fill=(255, 90, 90))
    out.save(path)


def measure(pk, mesh):
    """Rest numbers: card points inside the body or hood (signed distance under 0 at the nearest surface point), the
    beard's reach, and the gap between its side and the hood's side edge."""
    V = mesh["pos"]
    tree = cKDTree(pk.all_pts)
    d, i = tree.query(V, k=3)
    q = pk.all_pts[i].mean(1)
    n = pk.all_nrm[i].mean(1)
    n /= np.linalg.norm(n, axis=1)[:, None] + 1e-12
    sd = ((V - q) * n).sum(1)
    low = V[:, 1] < 1.53
    out = {"verts": int(len(V)), "tris": int(len(mesh["idx"])), "insideMm>2": int(((sd < -0.002) & low).sum()),
           "tipY": round(float(V[:, 1].min()), 3), "widthAt1.3": None}
    band = np.abs(V[:, 1] - 1.30) < 0.01
    if band.any():
        out["widthAt1.3"] = round(float(V[band, 0].max() - V[band, 0].min()), 3)
    return out


# ================= main =================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pkg")
    ap.add_argument("--work", default=None)
    ap.add_argument("--seed", type=int, default=29)
    ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args()
    work = a.work or os.path.join(a.pkg, "..", "_beard_work")
    os.makedirs(work, exist_ok=True)
    rng = np.random.default_rng(a.seed)
    lrng = np.random.default_rng(a.seed + 1)   # (the LOD's and shadow's own draws: the full mesh unchanged by them)
    t0 = time.time()
    pk = Package(a.pkg, rng)
    sets, lod_sets, shadow_sets, report = [], [], [], {"layers": {}}

    # the moustache
    mp, mn, _ = root_points(pk, rng, MOUSTACHE["spacing"], "moustache")
    mlen = rng.uniform(*MOUSTACHE["length"], len(mp)) * (1 + 0.25 * smoothstep(0.0, MOUSTACHE_CORNER, np.abs(mp[:, 0] - X0)))
    Pm, _ = grow(pk, mp, mn, "moustache", MOUSTACHE, rng, mlen.max())
    Pm = trim(Pm, mlen)
    collider(pk, face_only=False)
    sets.append(card_set(Pm, MOUSTACHE, rng, MOUSTACHE["K"]))
    lod_sets.append(card_set(Pm[::3], MOUSTACHE, lrng, 5, wide=1.8))
    report["layers"]["moustache"] = len(mp)

    # the beard's layers
    for L_ in LAYERS:
        bp, bn, below = root_points(pk, rng, L_["spacing"], "beard")
        adx = np.abs(bp[:, 0] - X0)
        tip = np.interp(adx, [0, 0.03, 0.06, 0.09], [TIP_Y[0], TIP_Y[0] + 0.02, TIP_Y[0] + 0.07, TIP_Y[1]])
        tip = tip + rng.normal(0, L_["jit"], len(bp)) * np.array([0.55, 1.0])[(rng.random(len(bp)) < 0.6).astype(int)]
        length = (bp[:, 1] - tip) + 0.10 + 0.08 * smoothstep(0.03, 0.08, adx) + 0.04 * (bp[:, 2] < 0.09)
        Pb, off = grow(pk, bp, bn, "beard", L_, rng, length.max())
        Pb = trim(Pb, to_height(Pb, tip, length))
        Pb = clump(Pb, L_["clump"], max(4, len(Pb) // 3), rng)
        Pb = keep_front(pk, Pb, off * 0.9)
        collider(pk, face_only=False)
        sets.append(card_set(Pb, L_, rng, L_["K"]))
        lod_sets.append(card_set(Pb[::LOD1["every"][L_["name"]]], L_, lrng, LOD1["K"], wide=LOD1["wide"]))
        if L_["name"] == "inner":
            shadow_sets.append(card_set(Pb[::SHADOW["every"]], L_, lrng, SHADOW["K"], wide=SHADOW["wide"]))
        report["layers"][L_["name"]] = len(bp)

    # the soft edge: short fine cards lying on the skin at the line
    ep, en, _ = root_points(pk, rng, 0.0068, "edge")
    elen = rng.uniform(*FINE["length"], len(ep))
    Pe, _ = grow(pk, ep, en, "edge", FINE, rng, elen.max())
    Pe = trim(Pe, elen)
    collider(pk, face_only=False)
    sets.append(card_set(Pe, FINE, rng, FINE["K"], alpha=FINE["alpha"], edge=True))
    report["layers"]["edge"] = len(ep)

    full, lod, shadow = part(pk, sets), part(pk, lod_sets), part(pk, shadow_sets)
    report.update(tris=int(len(full["idx"])), lodTris=int(len(lod["idx"])), shadowTris=int(len(shadow["idx"])),
                  rest=measure(pk, full), colour=COLOUR, seconds=round(time.time() - t0, 1))
    log(json.dumps(report))
    splat(pk, full, os.path.join(work, "beard_front.png"), "front")
    splat(pk, full, os.path.join(work, "beard_side.png"), "side")
    splat(pk, lod, os.path.join(work, "beard_lod1_front.png"), "front")
    json.dump(report, open(os.path.join(work, "beard_report.json"), "w"), indent=1)
    np.savez(os.path.join(work, "beard_full.npz"), **{k: v for k, v in full.items()})
    if a.no_write:
        return
    sh = dict(pos=shadow["pos"], nrm=shadow["nrm"], J=shadow["J"], W=shadow["W"], idx=shadow["idx"])
    write(pk, os.path.join(a.pkg, "beard.glb"), [("beard", full, 0), ("beard.lod1", lod, 0), ("beard.shadow", sh, 1)])
    man_path = os.path.join(a.pkg, "manifest.json")
    man = json.load(open(man_path, encoding="utf-8"))
    man["hair"] = {"file": "beard.glb", "colour": COLOUR, "style": "beard", "source": "tools/assets/warden_beard.py (hair cards on heroine_hair.py's drape and cards)",
                   "tris": report["tris"], "lodTris": report["lodTris"], "shadowTris": report["shadowTris"], "guides": report["layers"]}
    with open(man_path, "w", encoding="utf-8") as fh:
        json.dump(man, fh, indent=1)
    log("manifest hair set")


MOUSTACHE_CORNER = 0.025


def to_height(P, tip, most):
    """Each guide's length to where it first comes down to its tip's height (Blender frame: z up), at most `most`."""
    S, K, _ = P.shape
    arc = np.c_[np.zeros(S), np.cumsum(np.linalg.norm(np.diff(P, axis=1), axis=2), 1)]
    out = np.minimum(arc[:, -1], most)
    for s in range(S):
        z = P[s, :, 2]
        i = np.nonzero(z < tip[s])[0]
        if len(i) and i[0] > 0:
            k = i[0]
            f = (z[k - 1] - tip[s]) / max(z[k - 1] - z[k], 1e-9)
            out[s] = min(out[s], arc[s, k - 1] + f * (arc[s, k] - arc[s, k - 1]))
    return out


def trim(P, length):
    """Each guide cut to its own length (the drape ran them all at the longest), K points kept along what is left; and
    cut where it first rises 5 mm over its root (r2: 228 card points flung up over his face and hood, to y 1.92)."""
    S, K, _ = P.shape
    arc = np.c_[np.zeros(S), np.cumsum(np.linalg.norm(np.diff(P, axis=1), axis=2), 1)]
    length = np.array(length, float).copy()
    for s in range(S):
        up = np.nonzero(P[s, 1:, 2] > P[s, 0, 2] + 0.005)[0]
        if len(up):
            length[s] = min(length[s], arc[s, up[0]])
    length = np.maximum(length, 0.008)
    out = np.zeros_like(P)
    for s in range(S):
        t = np.linspace(0, min(length[s], arc[s, -1]), K)
        for c in range(3):
            out[s, :, c] = np.interp(t, arc[s], P[s, :, c])
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    main()
