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
LANE = ([0.95, 1.15, 1.35, 1.47, 1.55], [0.48, 0.52, 0.67, 0.86, 1.0])   # the beard's width (of its roots') by height (r5: 0.52-0.9 at r4, the mass 10-15% smaller)
LAYERS = [
    # name, root spacing, held off, card width, columns, narrowing, shade (depth), points, clump pull, tip jitter
    dict(name="inner", spacing=0.019, off=0.0045, width=(0.036, 0.046), cols=DENSE, narrow=0.45, shade=(0.40, 0.55), K=13, clump=0.15, jit=0.03),
    dict(name="mid", spacing=0.021, off=0.0125, width=(0.030, 0.038), cols=DENSE + LOOSE, narrow=0.62, shade=(0.62, 0.80), K=13, clump=0.45, jit=0.06),
    dict(name="outer", spacing=0.022, off=0.0205, width=(0.016, 0.024), cols=LOCK + LOOSE[:2], narrow=0.88, shade=(0.85, 1.0), K=13, clump=0.65, jit=0.09),
]
MOUSTACHE = dict(spacing=0.0040, off=0.0030, width=(0.010, 0.016), cols=LOCK + DENSE[:3], narrow=0.80, shade=(0.62, 0.95), K=9,
                 length=(0.060, 0.095))
FINE = dict(off=0.0012, width=(0.005, 0.009), cols=WISP + LOOSE, narrow=0.7, shade=(0.45, 0.65), K=5, length=(0.014, 0.030),
            alpha=(0.45, 0.8))
LOD1 = dict(every={"inner": 3, "mid": 2, "outer": 2}, K=8, wide=1.7)   # beard.lod1: a share of each layer's guides, wider, fewer points
SHADOW = dict(every=2, K=6, wide=2.0)        # beard.shadow: every second inner-layer guide
COLOUR = "#4f4c47"                # (r4: #7a7871 read white under the moon on the solid mass) the dye: old river-wet grey (concept A: neutral grey, a touch warm; darker wet roots by the shader)
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
            # (r5: the whole hood, its wool, inner face and fringe: the collar's rim and the capelet's tatters are not wool)
            hv = [v for (m, mat), v in hp.items() if "lod1" not in m and "shadow" not in m]
            if hv:
                o_ = np.cumsum([0] + [len(v["P"]) for v in hv])
                self.hood = dict(P=np.concatenate([v["P"] for v in hv]), F=np.concatenate([v["F"] + o for v, o in zip(hv, o_[:-1])]))
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
        self.hood_grid = self.grid_front(self.hood["P"], self.hood["F"]) if self.hood is not None else None
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

    def grid_front(self, V, F, step=0.003):
        """The frontmost z of a mesh seen from the front, by (x, y) cell (nan where it is not), over the beard's reach."""
        P, _, _ = sample_surface(V, F, step / 3.0, np.random.default_rng(6))
        xs, ys = X0 - 0.27, 0.95
        ix = np.floor((P[:, 0] - xs) / step).astype(int)
        iy = np.floor((P[:, 1] - ys) / step).astype(int)
        nx, ny = int(0.54 / step) + 1, int(0.75 / step) + 1
        ok = (ix >= 0) & (ix < nx) & (iy >= 0) & (iy < ny)
        Z = np.full((ny, nx), -np.inf)
        np.maximum.at(Z, (iy[ok], ix[ok]), P[ok, 2])
        return dict(x0=xs, y0=ys, step=step, Z=Z)

    def hood_cover(self, Q):
        """How far (m) the hood's front stands in front of each point (glTF) at its (x, y); -inf where no hood."""
        g = self.hood_grid
        ix = np.clip(np.floor((Q[:, 0] - g["x0"]) / g["step"]).astype(int), 0, g["Z"].shape[1] - 1)
        iy = np.clip(np.floor((Q[:, 1] - g["y0"]) / g["step"]).astype(int), 0, g["Z"].shape[0] - 1)
        return g["Z"][iy, ix] - Q[:, 2]

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
    # (r5: none where the hood's collar is in front of the skin, seen from the front (under the chin, the jaw's
    # underside): their locks came out through the collar from behind; the sides under the hood's side walls kept)
    if pk.hood is not None and region != "edge":
        cov = pk.hood_cover(pts)
        ok &= ~((cov > -0.004) & (adx < 0.066) & (pts[:, 1] < 1.565))
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


def keep_front(pk, Pb, off, below_y=1.545, lane=None, roots_x=None, comb=0.0, clr=1.0):
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
    # (r4: a soft limit, not a clamp: the clamp folded lifted points flat onto the wall, the zigzag side cards of r3)
    hi = smoothstep(1.47, 1.51, y)
    adx = np.abs(flat[:, 0] - X0)
    a_, b_ = SIDE_WALL - 0.012, SIDE_WALL + 0.012
    soft = np.where(adx > a_, a_ + (b_ - a_) * np.tanh((adx - a_) / (b_ - a_)), adx)
    flat[:, 0] = X0 + np.sign(flat[:, 0] - X0) * (adx + (soft - adx) * hi)
    zf = pk.front_z(flat[:, 0], y) + np.repeat(off if np.ndim(off) else np.full(S, off), K) + clear(y) * clr
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
    # (r4: the fringe's cards lie on the mass (in the collider), held off his front by the mass's depth, "front")
    fo = off if "front" not in cfg else cfg["front"] * (0.9 + 0.2 * rng.random(len(pts)))

    def extra(P, step):
        if region == "beard":
            P[:] = keep_front(pk, P, fo, roots_x=rx, comb=0.04)
        else:
            P[:] = keep_front(pk, P, fo, below_y=-1.0)

    collider(pk, face_only=True)
    P = HH["drape"](starts, db, length, points=K, offset=off, stiff_root=0.02 if region != "beard" else 0.03,
                    steps=140 if region == "beard" else 90, gravity=1.0, extra=extra)
    if region == "beard":
        P = keep_front(pk, P, fo, roots_x=rx, comb=0.0)
    return P, fo


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
    # (r4: a card whose edge points were thrown off its guide (onto() over a fold) folded to its middle: r4c drew one
    # as a 6 cm plane hanging off the beard)
    V4 = c["V"].reshape(S, 3, K, 3)
    span = np.linalg.norm(V4[:, 2] - V4[:, 0], axis=2)
    bad = span.max(1) > 2.0 * width + 0.004
    if bad.any():
        V4[bad, 0] = V4[bad, 1]
        V4[bad, 2] = V4[bad, 1]
        log(f"card_set: {int(bad.sum())} of {S} cards thrown wide, folded flat")
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
    # (r5: Head 0.64 at y 1.45 swung the beard 4-5 cm into his chest when he looked down (44 mm poke): now Head on the
    # face and the chin, the throat between, the chest's own below 1.45)
    h = np.interp(y, HEAD_RAMP[0], HEAD_RAMP[1])
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
    """beard.glb: body.glb's skeleton and skin, its meshes replaced by the beard's (parts: [(node, [(prim dict, mat)])];
    materials 0 "hair" (the strand atlas's cards), 1 "beard_shadow" (opaque), 2 "hair_mass" (the locks, beard_mass.png))."""
    g = Glb(os.path.join(pk.pkg, "body.glb"))
    j = g.j
    drop = [i for i, n in enumerate(j["nodes"]) if n.get("name", "").startswith("ford_warden") and n.get("name") != "ford_warden"]
    g.drop_nodes(drop)
    j["meshes"] = []
    j["images"] = [{"uri": CARDS_TEX, "name": "beard_cards"}, {"uri": MASS_TEX, "name": "beard_mass"}]
    j["samplers"] = [{"magFilter": 9729, "minFilter": 9987, "wrapS": 33071, "wrapT": 33071},
                     {"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 33071}]
    j["textures"] = [{"source": 0, "sampler": 0}, {"source": 1, "sampler": 1}]
    j["materials"] = [
        {"name": "hair", "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}, "metallicFactor": 0.0, "roughnessFactor": 0.6},
         "alphaMode": "MASK", "alphaCutoff": 0.4, "doubleSided": True},
        {"name": "beard_shadow", "pbrMetallicRoughness": {"baseColorFactor": [0.2, 0.2, 0.2, 1.0], "metallicFactor": 0.0, "roughnessFactor": 1.0},
         "doubleSided": True},
        {"name": "hair_mass", "pbrMetallicRoughness": {"baseColorTexture": {"index": 1}, "metallicFactor": 0.0, "roughnessFactor": 0.6},
         "doubleSided": False},
        {"name": "hair_tie", "pbrMetallicRoughness": {"baseColorTexture": {"index": 1}, "metallicFactor": 0.0, "roughnessFactor": 0.8},
         "doubleSided": False},
        {"name": "hair_weed", "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}, "metallicFactor": 0.0, "roughnessFactor": 0.6},
         "alphaMode": "MASK", "alphaCutoff": 0.4, "doubleSided": True},
    ]
    arm = j["scenes"][0]["nodes"][0]
    body_node = next(i for i, n in enumerate(j["nodes"]) if n.get("name") == "ford_warden")
    for k, (node_name, prims_) in enumerate(parts):
        mesh = {"name": node_name, "primitives": []}
        for d, mat in prims_:
            a = {"POSITION": g.add_acc(d["pos"].astype(np.float32), "VEC3", minmax=True), "NORMAL": g.add_acc(d["nrm"].astype(np.float32), "VEC3"),
                 "JOINTS_0": g.add_acc(d["J"], "VEC4"), "WEIGHTS_0": g.add_acc(d["W"], "VEC4")}
            if "uv" in d and mat != 1:
                a["TANGENT"] = g.add_acc(d["tan"].astype(np.float32), "VEC4")
                a["TEXCOORD_0"] = g.add_acc(d["uv"].astype(np.float32), "VEC2")
                a["TEXCOORD_1"] = g.add_acc(np.zeros((len(d["pos"]), 2), np.float32), "VEC2")   # (no chain: it swings by its skin)
                a["COLOR_0"] = g.add_acc(d["col"].astype(np.float32), "VEC4")
            mesh["primitives"].append({"attributes": a, "indices": g.add_acc(d["idx"].astype(np.uint32).ravel(), "SCALAR", target=34963),
                                       "material": mat, "mode": 4})
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


# ================= r4: the sculpted mass (wet locks as tapered tubes) =================
MASS_TEX = "beard_mass.png"         # the mass's strands (beside beard.glb): the atlas's strands packed solid, tileable across
MASS_LAYERS = [
    # roots' spacing, centre held off, width and depth at the root (m), sides, colour depth (r), clump share, tip jitter
    # (r5: widths and depths 0.87 of r4's (the judge: shrink the mass 10-15%); the inner layer darker (the gaps between
    # the outer locks show it: 35-45/255 asked); the outer locks waved)
    dict(name="inner", spacing=0.024, off=0.0085, width=(0.044, 0.059), depth=(0.0096, 0.013), n=5, shade=(0.22, 0.34), clump=0.20, jit=0.035, tip=2.4, wave=0.0015),
    dict(name="outer", spacing=0.027, off=0.0170, width=(0.021, 0.031), depth=(0.0087, 0.012), n=5, shade=(0.62, 0.92), clump=0.50, jit=0.08, tip=1.7, wave=0.0030),
]
MASS_MOUSTACHE = dict(spacing=0.0072, off=0.0048, width=(0.014, 0.020), depth=(0.0065, 0.0085), n=5, shade=(0.70, 0.95),
                      length=(0.055, 0.085))
MASS_UV = 0.10                      # metres of a lock's girth per width of the mass texture
MASS_NORMAL = 0.75                  # the tube's own normal's share (the rest the mass's outward normal: lit as one mass)
# (r5: more, thinner cards, longer than the mass at the bottom (strands hanging past its points) and on its outline (the
# silhouette broken into strands); waved)
FRINGE = dict(spacing=0.021, off=0.0265, width=(0.0055, 0.010), cols=LOCK + WISP + LOOSE[:2], narrow=0.85, shade=(0.72, 1.0), K=9, clump=0.40, jit=0.09,
              past=(0.015, 0.075), wave=0.0035)
OUTLINE = dict(spacing=0.019, off=0.0255, width=(0.0045, 0.008), cols=WISP + LOOSE[:2], narrow=0.75, shade=(0.62, 0.95), K=9, min_dx=0.048, wave=0.004)
STRAYS = dict(n=16, off=0.030, width=(0.003, 0.0055), cols=WISP, narrow=0.6, shade=(0.8, 1.0), K=9)
CARDS_TEX = "beard_cards.png"       # (r5: the strand atlas waved, beside beard.glb: the judge asked a wave in the card textures)
# the mass's clearance off his front (chest, the hood's collar and capelet) by height (r5: the judge, 2-3 cm, for the
# head's nod: on the skin above the chin, 12 mm at the collar's top)
CLEAR = ([1.40, 1.47, 1.53, 1.565], [0.024, 0.022, 0.012, 0.0])
HEAD_RAMP = ([1.40, 1.45, 1.50, 1.535], [0.03, 0.10, 0.40, 1.0])   # Head's share of the skin by height (the rest the chest's)
# the braids (x at the top and the bottom from the centre line, the braid's y from and to, half-width, one twist's length,
# the loose tuft below its last band): two at the beard's outer thirds, a thinner third left of the middle (concept A)
BRAIDS = [dict(x=(0.040, 0.030), y=(1.425, 1.165), R=0.0085, pitch=0.030, tuft=0.050, shade=(0.70, 0.92)),
          dict(x=(-0.046, -0.035), y=(1.415, 1.190), R=0.0085, pitch=0.030, tuft=0.045, shade=(0.66, 0.88)),
          dict(x=(-0.009, -0.014), y=(1.360, 1.210), R=0.0060, pitch=0.022, tuft=0.035, shade=(0.62, 0.86))]
BRAID_SIDES, BRAID_RINGS = 4, 4     # each strand's sides, rings per twist
# river weed caught in it: thin, stringy, dark olive cards (their own material, hair_weed, dyed by the manifest)
WEED = dict(clusters=6, per=(2, 4), off=0.003, width=(0.0030, 0.0060), cols=WISP + LOOSE[3:], narrow=0.45, shade=(0.75, 1.0), K=12,
            length=(0.09, 0.26), wave=0.004)
WEED_COLOUR = [0.15, 0.18, 0.08]
LOD1_MASS = dict(n=4, K=7)
# (the hair shader's uniforms for the beard (NpcPackage.Uniforms): no ash or lift (they cool and lighten a pale grey: blue-
# white under the moon), less light through it (a wet mass, not a backlit halo), darker wet roots)
HAIR_UNIFORMS = {"*": {"ash": 0.0, "lift": 0.0, "through": 0.1, "roots": 0.85}, "hair_mass": {"shine": 0.35},
                 "hair_weed": {"colour": WEED_COLOUR, "shine": 0.3, "variation": 0.5, "roots": 0.0}}
SHADOW_MASS = dict(n=4, K=6)


def mass_texture(path, seed=7, W=1024, H=2048):
    """The mass's strands: the atlas's dense and loose columns layered ten deep over a dark ground, deeper layers
    darker, every layer wrapped across (tileable in u); r the strands' light, g their number, alpha 1 (a solid lock:
    the hair shader's hashed alpha keeps it whole)."""
    rng = np.random.default_rng(seed)
    a = np.asarray(Image.open(ATLAS).convert("RGBA")).astype(np.float32) / 255
    cw = a.shape[1] // 16
    rows = int(a.shape[0] * 0.82)            # (the atlas's tips thin out in its last rows: the strands' length, not their ends)
    cols = []
    for c in DENSE + LOOSE:
        im = Image.fromarray((a[:rows, c * cw:(c + 1) * cw] * 255).astype(np.uint8)).resize((cw, H), Image.LANCZOS)
        cols.append(np.asarray(im).astype(np.float32) / 255)
    r = np.full((H, W), 0.10, np.float32)
    g = np.full((H, W), 0.5, np.float32)
    for L in range(10):
        strip = np.concatenate([cols[i][:, ::(1 if rng.random() < 0.5 else -1)] for i in rng.integers(0, len(cols), W // cw)], 1)
        strip = np.roll(strip, int(rng.integers(0, W)), 1)
        strip = wave_tex(strip, rng, amp=10.0, wrap=True)
        sh = 0.30 + 0.70 * L / 9
        al = strip[..., 3]
        r = r * (1 - al) + strip[..., 0] * sh * al
        g = g * (1 - al) + strip[..., 1] * al
    out = np.dstack([r, g, np.zeros_like(r), np.ones_like(r)])
    Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(path)
    log(f"mass texture {path}: r mean {r.mean():.2f}")


def wave_tex(a, rng, amp=12.0, wrap=False, periods=(4.5, 9.0)):
    """An image's rows shifted sideways by two sines down its height (strands waved), `amp` pixels; wrapped across."""
    from scipy import ndimage
    H, W = a.shape[:2]
    y = np.arange(H)[:, None]
    p1, p2 = rng.uniform(*periods), rng.uniform(periods[1], periods[1] * 2.2)
    sh = amp * (0.75 * np.sin(2 * np.pi * y / H * p1 + rng.uniform(0, 6.28)) + 0.25 * np.sin(2 * np.pi * y / H * p2 + rng.uniform(0, 6.28)))
    xx = (np.arange(W)[None, :] - sh) % W if wrap else np.clip(np.arange(W)[None, :] - sh, 0, W - 1)
    yy = np.broadcast_to(y, xx.shape)
    chans = [ndimage.map_coordinates(a[..., c], [yy, xx], order=1, mode="grid-wrap" if wrap else "nearest") for c in range(a.shape[2])]
    return np.stack(chans, -1).astype(a.dtype)


def card_texture(path, seed=5):
    """The strand atlas waved column by column (each card's strip its own wave: wet hair's slow S, not ruler lines)."""
    rng = np.random.default_rng(seed)
    a = np.asarray(Image.open(ATLAS).convert("RGBA")).astype(np.float32)
    cw = a.shape[1] // 16
    out = a.copy()
    for c in range(16):
        blk = a[:, c * cw:(c + 1) * cw]
        # (the column's edges kept clear: shifted with a clamp, its alpha faded in 6 px at each side)
        w = wave_tex(blk, rng, amp=0.055 * cw)
        e = np.minimum(np.arange(cw), cw - 1 - np.arange(cw)) / 6.0
        w[..., 3] *= np.clip(e, 0, 1)[None]
        out[:, c * cw:(c + 1) * cw] = w
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(path)
    log(f"card texture {path}")


def clear(y):
    return np.interp(y, CLEAR[0], CLEAR[1])


def wave_lines(C, amp, rng, axes=(0, 2), lam=(0.045, 0.08), start=(0.06, 0.30)):
    """Lines (S x K x 3) waved sideways and in depth by a sine along their length (`amp` m, growing from the root)."""
    S, K, _ = C.shape
    arc = np.c_[np.zeros(S), np.cumsum(np.linalg.norm(np.diff(C, axis=1), axis=2), 1)]
    f = arc / np.maximum(arc[:, -1:], 1e-6)
    L = rng.uniform(*lam, S)[:, None]
    ph = rng.uniform(0, 6.28, S)[:, None]
    a = amp * rng.uniform(0.6, 1.3, S)[:, None] * smoothstep(start[0], start[1], f)
    out = C.copy()
    out[:, :, axes[0]] += a * np.sin(2 * np.pi * arc / L + ph)
    out[:, :, axes[1]] += 0.45 * a * np.sin(2 * np.pi * arc / (L * 1.3) + ph * 1.7)
    return out


def smooth_lines(P, it=6, keep_root=2):
    """Each line's points relaxed toward their neighbours' mean (kinks out), the root's first points kept."""
    P = P.copy()
    for _ in range(it):
        P[:, keep_root:-1] = 0.5 * P[:, keep_root:-1] + 0.25 * (P[:, keep_root - 1:-2] + P[:, keep_root + 1:])
    return P


def push_out(pk, C, need, root_keep=0.06):
    """Each lock's centre line (glTF, S x K x 3) moved off him along his surface's normal where it is nearer than
    `need` (S x K: its half-depth and a clearance) to the drape's surfaces (face, body, the hood's capelet), except
    within its first `root_keep` of its length (it grows from the skin there)."""
    tree = cKDTree(pk.drape_pts)
    S, K, _ = C.shape
    f = np.linspace(0, 1, K)[None].repeat(S, 0)
    for _ in range(4):
        flat = C.reshape(-1, 3)
        _, i = tree.query(flat, k=6)
        q = pk.drape_pts[i].mean(1)
        n = pk.drape_nrm[i].mean(1)
        n /= np.linalg.norm(n, axis=1)[:, None] + 1e-12
        sd = ((flat - q) * n).sum(1).reshape(S, K)
        mv = np.maximum(need - sd, 0) * smoothstep(root_keep * 0.5, root_keep, f)
        C = C + (n.reshape(S, K, 3) * mv[:, :, None])
        C[:, 2:] = smooth_lines(C, it=2, keep_root=2)[:, 2:]
    return C


def outward(pk, C):
    """The mass's outward way at each centre-line point (glTF): his surfaces' normals, the head's middle over the face."""
    S, K, _ = C.shape
    flat = C.reshape(-1, 3)
    tree = cKDTree(pk.drape_pts)
    _, i = tree.query(flat, k=10)
    n = pk.drape_nrm[i].mean(1)
    rad = flat - CENTRE_G
    rad /= np.linalg.norm(rad, axis=1)[:, None] + 1e-12
    hd = (pk.drape_face[i] & (pk.drape_pts[i][:, :, 1] > 1.555)).mean(1)[:, None]
    n = n * (1 - hd) + rad * hd
    n = n.reshape(S, K, 3)
    for _ in range(4):
        n[:, 1:-1] = (n[:, :-2] + 2 * n[:, 1:-1] + n[:, 2:]) / 4
    return n / (np.linalg.norm(n, axis=2)[:, :, None] + 1e-12)


def tubes(pk, C, width, depth, n_sides, K, shade, rng, tip_pow=1.7, root_w=0.82):
    """Tapered wet locks round centre lines (glTF, S x K0 x 3, resampled to K): an ellipse `width` across and `depth`
    deep (S each) at the root, lying flat on him, narrowing to a point; u round the lock (the seam behind it), v root
    to tip; vertex colour r depth, g lock number, a 1. Returns a part dict (pos, nrm, uv, col, tan, idx, at, arc)."""
    Cb = HH["resample"](C, K)
    S = len(Cb)
    t = np.zeros_like(Cb)
    t[:, 1:-1] = Cb[:, 2:] - Cb[:, :-2]
    t[:, 0], t[:, -1] = Cb[:, 1] - Cb[:, 0], Cb[:, -1] - Cb[:, -2]
    t /= np.linalg.norm(t, axis=2)[:, :, None] + 1e-12
    out = outward(pk, Cb)
    side = np.cross(t, out)
    side /= np.linalg.norm(side, axis=2)[:, :, None] + 1e-12
    out = np.cross(side, t)
    f = np.linspace(0, 1, K)
    prof = (1 - f ** tip_pow) ** 0.85 * (root_w + (1 - root_w) * smoothstep(0.0, 0.15, f))   # (pointed, narrower at the root)
    dprof = prof * (0.45 + 0.55 * smoothstep(0.0, 0.15, f))                             # (flat on the skin at the root)
    hw = width[:, None] * prof[None] / 2
    hd = depth[:, None] * dprof[None] / 2
    th = -np.pi / 2 + 2 * np.pi * np.arange(n_sides + 1) / n_sides
    ct, st = np.cos(th), np.sin(th)
    V = Cb[:, :, None] + side[:, :, None] * (hw[:, :, None, None] * ct[None, None, :, None]) + out[:, :, None] * (hd[:, :, None, None] * st[None, None, :, None])
    nt = side[:, :, None] * (ct[None, None, :, None] / np.maximum(hw, 1e-4)[:, :, None, None]) + out[:, :, None] * (st[None, None, :, None] / np.maximum(hd, 1e-4)[:, :, None, None])
    nt /= np.linalg.norm(nt, axis=3)[..., None] + 1e-12
    N = MASS_NORMAL * nt + (1 - MASS_NORMAL) * out[:, :, None]
    N /= np.linalg.norm(N, axis=3)[..., None] + 1e-12
    T = -side[:, :, None] * st[None, None, :, None] + out[:, :, None] * ct[None, None, :, None]   # (round the lock)
    T = T - N * (T * N).sum(3)[..., None]
    T /= np.linalg.norm(T, axis=3)[..., None] + 1e-12
    w = np.sign((np.cross(N, T) * t[:, :, None]).sum(3))
    w[w == 0] = 1
    girth = np.pi * (width + depth) / 2
    u0 = rng.random(S)
    U = u0[:, None, None] + (np.arange(n_sides + 1) / n_sides)[None, None, :] * (girth / MASS_UV)[:, None, None]
    U = np.broadcast_to(U, (S, K, n_sides + 1))
    Vv = np.broadcast_to(f[None, :, None], (S, K, n_sides + 1))
    arc = np.c_[np.zeros(S), np.cumsum(np.linalg.norm(np.diff(Cb, axis=1), axis=2), 1)]
    nv = K * (n_sides + 1)
    r = np.repeat(rng.uniform(*shade, S), nv)
    g_ = np.repeat(rng.random(S), nv)
    col = np.c_[r, g_, np.zeros(len(r)), np.ones(len(r))]
    base = (np.arange(S) * nv)[:, None, None]
    k = np.arange(K - 1)[None, :, None]
    j = np.arange(n_sides)[None, None, :]
    a_ = base + k * (n_sides + 1) + j
    b_ = a_ + 1
    c_ = a_ + (n_sides + 1) + 1
    d_ = a_ + (n_sides + 1)
    q = np.stack([a_, b_, c_, d_], -1).reshape(-1, 4)
    tri = np.vstack([q[:, [0, 2, 1]], q[:, [0, 3, 2]]])
    Vf = V.reshape(-1, 3)
    ar = np.linalg.norm(np.cross(Vf[tri[:, 1]] - Vf[tri[:, 0]], Vf[tri[:, 2]] - Vf[tri[:, 0]]), axis=1)
    tri = tri[ar > 1e-12]                       # (the tip's: its last ring is a point)
    fn = np.cross(Vf[tri[:, 1]] - Vf[tri[:, 0]], Vf[tri[:, 2]] - Vf[tri[:, 0]])
    Nf = N.reshape(-1, 3)
    flip = (fn * Nf[tri[:, 0]]).sum(1) < 0      # (wound outward)
    tri[flip] = tri[flip][:, [0, 2, 1]]
    at = np.broadcast_to(Cb[:, :, None], V.shape).reshape(-1, 3)
    return dict(pos=Vf, nrm=Nf, uv=np.c_[U.ravel(), Vv.ravel()], col=col, tan=np.c_[T.reshape(-1, 3), w.ravel()].astype(np.float32),
                idx=tri, at=at, arc=np.broadcast_to(arc[:, :, None], (S, K, n_sides + 1)).ravel().copy(), S=S)


def cat_parts(ps):
    out = {k: np.concatenate([p[k] for p in ps]) for k in ("pos", "nrm", "uv", "col", "tan", "at", "arc")}
    idx, o = [], 0
    for p in ps:
        idx.append(p["idx"] + o)
        o += len(p["pos"])
    out["idx"] = np.concatenate(idx)
    return out


def skin_part(pk, d):
    J, W = weights(pk, d["at"], d["arc"])
    d = dict(d)
    d["J"], d["W"] = J, W
    return d


def cut_lines(pk, C, rise=0.004, ahead=0.080):
    """Each line (glTF) cut where it first climbs `rise` over the lowest it has been (the drape flung a few up and
    forward), or stands more than `ahead` in front of his front below the chin; K points kept along what is left."""
    S, K, _ = C.shape
    arc = np.c_[np.zeros(S), np.cumsum(np.linalg.norm(np.diff(C, axis=1), axis=2), 1)]
    y = C[:, :, 1]
    lo = np.minimum.accumulate(y, axis=1)
    bad = (y > lo + rise)
    fz = pk.front_z(C[:, :, 0].ravel(), y.ravel()).reshape(S, K)
    bad |= (y < 1.50) & (C[:, :, 2] - fz > ahead)
    length = arc[:, -1].copy()
    for s_ in range(S):
        b = np.nonzero(bad[s_])[0]
        if len(b):
            length[s_] = arc[s_, max(b[0] - 1, 1)]
    out = np.zeros_like(C)
    for s_ in range(S):
        t = np.linspace(0, length[s_], K)
        for c in range(3):
            out[s_, :, c] = np.interp(t, arc[s_], C[s_, :, c])
    return out


def lock_lines(pk, region, cfg, rng):
    """A layer's locks' centre lines (glTF): roots, the drape (heroine_hair.drape on the package's collider, held in
    front of him and combed to the lane), cut to their tips' heights, gathered a little in wet clumps, smoothed, and
    held off him by half their depth. Returns lines, widths, depths."""
    bp, bn, below = root_points(pk, rng, cfg["spacing"], region)
    S = len(bp)
    width = rng.uniform(*cfg["width"], S)
    depth = rng.uniform(*cfg["depth"], S)
    adx = np.abs(bp[:, 0] - X0)
    if region == "moustache":
        # (r4: laid, not draped: down and a little out over the upper lip, then falling past the mouth's corners into
        # the beard; the drape threw a corner lock out sideways past his cheek)
        length = rng.uniform(*cfg["length"], S) * (1 + 0.35 * smoothstep(0.0, MOUSTACHE_CORNER, adx))
        sg = np.sign(bp[:, 0] - X0) + (bp[:, 0] == X0)
        K = 12
        s = np.linspace(0, 1, K)[None, :] * length[:, None]
        out_ = 0.004 + 0.010 * smoothstep(0.0, 0.02, s)                       # (off the lip: over it, not on it)
        lat = sg[:, None] * (0.10 + 0.55 * adx / MUSTACHE[0])[:, None] * np.minimum(s, 0.03 + 0.02 * rng.random(S)[:, None])
        C = np.zeros((S, K, 3))
        C[:, :, 0] = bp[:, None, 0] + lat
        C[:, :, 1] = bp[:, None, 1] - s
        C[:, :, 2] = bp[:, None, 2] + out_ - 0.15 * np.maximum(s - 0.03, 0)   # (forward over the lip, then back down the chin)
        C = push_out(pk, C, depth[:, None] * 0.5 + 0.0015, root_keep=0.15)
        C = smooth_lines(C, it=3, keep_root=2)
        return C, width, depth
    else:
        tip = np.interp(adx, [0, 0.03, 0.06, 0.09], [TIP_Y[0], TIP_Y[0] + 0.02, TIP_Y[0] + 0.07, TIP_Y[1]])
        tip = tip + rng.normal(0, cfg["jit"], S) * np.array([0.55, 1.0])[(rng.random(S) < 0.6).astype(int)]
        length = (bp[:, 1] - tip) + 0.10 + 0.08 * smoothstep(0.03, 0.08, adx) + 0.04 * (bp[:, 2] < 0.09)
        Pb, off = grow(pk, bp, bn, "beard", cfg, rng, length.max())
        Pb = trim(Pb, to_height(Pb, tip, length))
        Pb = clump(Pb, cfg["clump"], max(3, S // 2), rng, start=0.45)
        Pb = keep_front(pk, Pb, off * 0.9)
    C = cut_lines(pk, b2g(Pb))
    C = smooth_lines(C, it=8, keep_root=2)
    need = depth[:, None] * 0.5 * np.ones(C.shape[1])[None] + 0.002 + clear(C[:, :, 1])
    if cfg.get("wave"):
        C = wave_lines(C, cfg["wave"], rng)
    C = push_out(pk, C, need)
    return C, width, depth


def strands_collider(pk, parts):
    """The drape's collider with the mass's surface added (the fringe's guides lie on the mass, not inside it)."""
    P = np.concatenate([p["pos"] for p in parts])
    N = np.concatenate([p["nrm"] for p in parts])
    k = np.random.default_rng(3).random(len(P)) < 0.6
    pk.drape_pts = np.vstack([pk.drape_pts, P[k]])
    pk.drape_nrm = np.vstack([pk.drape_nrm, N[k]])
    pk.drape_face = np.r_[pk.drape_face, np.zeros(k.sum(), bool)]


def preview(pk, parts, path, views=("front", "side", "q"), box=(1.0, 1.72), crop=None):
    """A quick look (dense surface points z-buffered, lit by their normals): him grey, the mass and cards in their tints.
    `crop` (x0, x1, y0, y1, glTF metres, front view only) for a close look."""
    L = np.array([0.35, 0.55, 0.75]); L /= np.linalg.norm(L)
    tm = pk.all_tm
    keep = (tm.triangles_center[:, 1] > box[0] - 0.02) & (tm.triangles_center[:, 1] < box[1] + 0.05)
    rng = np.random.default_rng(2)
    H_ = 900
    res = (box[1] - box[0]) / H_
    layers = [(tm.vertices, tm.faces[keep], (0.42, 0.40, 0.38), None)] + [(p["pos"], p["idx"], p["tint"], p["nrm"]) for p in parts]
    samples = []
    for V, F, col, N in layers:
        P, Nf, k = sample_surface(V, F, res * 0.55, rng)
        if N is not None:
            Nf = N[F[k]].mean(1)
            Nf /= np.linalg.norm(Nf, axis=1)[:, None] + 1e-12
        samples.append((P, Nf, np.asarray(col)))
    ims = []
    for view in views:
        ang = {"front": 0.0, "side": -np.pi / 2, "q": -np.pi / 4}[view]
        Rm = np.array([[np.cos(ang), 0, np.sin(ang)], [0, 1, 0], [-np.sin(ang), 0, np.cos(ang)]])
        W_ = 600
        img = np.zeros((H_, W_, 3)) + 0.05
        zb = np.full((H_, W_), -9.0)
        for P, Nf, col in samples:
            X = (P - np.array([X0, 0, 0])) @ Rm.T
            Nr = Nf @ Rm.T
            lit = 0.2 + 0.8 * np.clip(Nr @ L, 0, 1) if True else None
            ix = (X[:, 0] / res + W_ / 2).astype(int)
            iy = (H_ - 1 - (X[:, 1] - box[0]) / res).astype(int)
            ok = (ix >= 0) & (ix < W_) & (iy >= 0) & (iy < H_)
            ix, iy, z, c = ix[ok], iy[ok], X[ok, 2], lit[ok][:, None] * col[None]
            o = np.argsort(z)
            ix, iy, z, c = ix[o], iy[o], z[o], c[o]
            better = z > zb[iy, ix]
            zb[iy[better], ix[better]] = z[better]
            img[iy[better], ix[better]] = c[better]
        ims.append(Image.fromarray((np.clip(img, 0, 1) ** (1 / 1.3) * 255).astype(np.uint8)))
    out = Image.new("RGB", (sum(i.width for i in ims), ims[0].height))
    x = 0
    for i in ims:
        out.paste(i, (x, 0)); x += i.width
    out.save(path)


def card_part(pk, cs):
    p = part(pk, cs)
    p["arc"] = merge(cs)["arc"]
    return p


# ================= r5: braids, cord bands, river weed =================
def surface_grid(P, F, step=0.003, spacing=0.0015):
    """The frontmost z of a mesh (glTF) by (x, y) cell, holes filled from the nearest cell, eased; for laying the braids
    and the weed on the mass."""
    from scipy import ndimage
    Q, _, _ = sample_surface(P, F, spacing, np.random.default_rng(8))
    x0, y0 = X0 - 0.15, 0.95
    nx, ny = int(0.30 / step) + 1, int(0.65 / step) + 1
    ix = np.floor((Q[:, 0] - x0) / step).astype(int)
    iy = np.floor((Q[:, 1] - y0) / step).astype(int)
    ok = (ix >= 0) & (ix < nx) & (iy >= 0) & (iy < ny)
    Z = np.full((ny, nx), -np.inf)
    np.maximum.at(Z, (iy[ok], ix[ok]), Q[ok, 2])
    have = np.isfinite(Z)
    Zf = ndimage.grey_closing(np.where(have, Z, -1.0), size=(3, 3))
    Zf = np.where(have, Z, np.where(Zf > -1.0, Zf, np.nan))
    have = np.isfinite(Zf)
    idx = ndimage.distance_transform_edt(~have, return_distances=False, return_indices=True)
    Zf = ndimage.gaussian_filter(Zf[tuple(idx)], 1.2)
    return dict(x0=x0, y0=y0, step=step, Z=Zf, have=ndimage.binary_dilation(have, iterations=2))


def grid_z(g, x, y):
    ix = np.clip((x - g["x0"]) / g["step"], 0, g["Z"].shape[1] - 1.001)
    iy = np.clip((y - g["y0"]) / g["step"], 0, g["Z"].shape[0] - 1.001)
    a, b = ix.astype(int), iy.astype(int)
    fx, fy = ix - a, iy - b
    Z = g["Z"]
    return Z[b, a] * (1 - fx) * (1 - fy) + Z[b, a + 1] * fx * (1 - fy) + Z[b + 1, a] * (1 - fx) * fy + Z[b + 1, a + 1] * fx * fy


def frames(C):
    """Tangent, side and outward (toward +z, glTF front) along lines (S x K x 3)."""
    t = np.gradient(C, axis=1)
    t /= np.linalg.norm(t, axis=2)[..., None] + 1e-12
    side = np.cross(t, np.array([0.0, 0.0, 1.0]))
    side /= np.linalg.norm(side, axis=2)[..., None] + 1e-12
    out = np.cross(side, t)
    return t, side, out


def braid_lines(pk, grid, b, rng):
    """A braid's centre line on the mass's front (glTF), its three strands round it (S=3 x K x 3), and its bands' arcs.
    The strands weave as a three-strand plait (side to side with the twist, over and under at twice it), drawn in from
    nothing at its top (it grows out of the mass under its first band) and loose below its last band (the tuft)."""
    (xa, xb), (ya, yb), R, pitch, tuft = b["x"], b["y"], b["R"], b["pitch"], b["tuft"]
    yend = yb - tuft
    n = int((ya - yend) * 1.1 / pitch * BRAID_RINGS) + 2
    s = np.linspace(0, 1, n)
    y = ya + (yend - ya) * s
    u = np.clip((ya - y) / (ya - yb), 0, 1)
    x = X0 + xa + (xb - xa) * u + 0.004 * np.sin(u * 3.0 + rng.uniform(0, 6))
    zm = grid_z(grid, x, y)
    zf = pk.front_z(x, y) + clear(y) + R
    from scipy.ndimage import gaussian_filter1d
    z = gaussian_filter1d(np.maximum(zm + 0.55 * R, zf), 2.0, mode="nearest")
    C = np.c_[x, y, z][None]
    t, side, out = frames(C)
    arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(C[0], axis=0), axis=1))]
    L_b = np.interp(yb, y[::-1], arc[::-1])           # the braid's length to its last band
    ph = 2 * np.pi * arc / pitch + rng.uniform(0, 6.28)
    grow_in = smoothstep(0.0, 0.035, arc)              # (from nothing at its top)
    loose = np.clip((arc - L_b) / max(arc[-1] - L_b, 1e-6), 0, 1)
    ph = np.where(arc > L_b, 2 * np.pi * L_b / pitch + ph[0], ph)   # (no more twist in the tuft)
    S = []
    for k in range(3):
        q = ph + 2 * np.pi * k / 3
        a_ = 0.52 * R * np.sin(q) * grow_in * (1 + 1.2 * loose)
        c_ = 0.30 * R * np.sin(2 * q) * grow_in * (1 + 0.5 * loose)
        S.append(C[0] + side[0] * a_[:, None] + out[0] * c_[:, None] + np.array([0.0, 0.0, 0.0]))
    bands = [0.018, 0.018 + (L_b - 0.018) * 0.5, L_b]
    return C[0], np.array(S), bands, arc


def band_mesh(C, arc, at_arc, Rw, Rd, length=0.0075, n=8):
    """A cord band round a braid at arc length `at_arc`: a short swollen ring (glTF), as a tubes() part (material tie)."""
    i = np.searchsorted(arc, at_arc)
    i = int(np.clip(i, 1, len(C) - 2))
    t, side, out = frames(C[None])
    c, t, side, out = C[i], t[0, i], side[0, i], out[0, i]
    hs = np.array([-0.5, -0.17, 0.17, 0.5]) * length
    sc = np.array([0.90, 1.07, 1.07, 0.90])
    th = 2 * np.pi * np.arange(n + 1) / n
    V, N, UV = [], [], []
    for h, k in zip(hs, sc):
        for j, a in enumerate(th):
            d = side * np.cos(a) * Rw * k + out * np.sin(a) * Rd * k
            V.append(c + t * h + d)
            nn = side * np.cos(a) / Rw + out * np.sin(a) / Rd
            N.append(nn / np.linalg.norm(nn))
            UV.append((j / n, (h / length) + 0.5))
    V, N = np.array(V), np.array(N)
    q = []
    for r in range(3):
        for j in range(n):
            a_ = r * (n + 1) + j
            q.append((a_, a_ + 1, a_ + n + 2, a_ + n + 1))
    q = np.array(q)
    tri = np.vstack([q[:, [0, 2, 1]], q[:, [0, 3, 2]]])
    fn = np.cross(V[tri[:, 1]] - V[tri[:, 0]], V[tri[:, 2]] - V[tri[:, 0]])
    flip = (fn * N[tri[:, 0]]).sum(1) < 0
    tri[flip] = tri[flip][:, [0, 2, 1]]
    T = np.cross(N, t)
    T /= np.linalg.norm(T, axis=1)[:, None] + 1e-12
    col = np.c_[np.full(len(V), 0.6), np.full(len(V), 0.5), np.zeros(len(V)), np.ones(len(V))]
    return dict(pos=V, nrm=N, uv=np.array(UV), col=col, tan=np.c_[T, np.ones(len(V))].astype(np.float32), idx=tri,
                at=np.repeat(c[None], len(V), 0), arc=np.zeros(len(V)), S=1)


def braids(pk, grid, rng, lrng):
    """The braids' strands (mass parts), their cord bands (tie part), and each braid as one tube for the LOD and shadow."""
    strands, ties, lod = [], [], []
    for b in BRAIDS:
        C, S3, bands, arc = braid_lines(pk, grid, b, rng)
        R = b["R"]
        K = len(C)
        w = np.full(3, 1.02 * R)
        d = np.full(3, 0.86 * R)
        strands.append(tubes(pk, S3, w, d, BRAID_SIDES, K, b["shade"], rng, tip_pow=7.0))
        for a_ in bands:
            ties.append(band_mesh(C, arc, a_, 1.20 * R, 0.98 * R))
        lod.append(tubes(pk, C[None], np.array([2.1 * R]), np.array([1.6 * R]), 4, 9, b["shade"], lrng, tip_pow=5.0))
    return cat_parts(strands), cat_parts(ties), cat_parts(lod)


def weed_lines(pk, grid, rng):
    """River weed caught in the beard (Blender frame, for cards): clusters of thin strands from the mass's upper front,
    falling over it, wandering and waved."""
    cfg = WEED
    out = []
    K = 24
    for c in range(cfg["clusters"]):
        y0 = rng.uniform(1.36, 1.53)
        half = 0.07 * np.interp(y0, LANE[0], LANE[1])
        x0 = X0 + rng.uniform(-half, half)
        for k in range(int(rng.integers(cfg["per"][0], cfg["per"][1] + 1))):
            L = rng.uniform(*cfg["length"])
            st = np.linspace(0, L, K)
            xs = x0 + rng.normal(0, 0.005) + np.cumsum(rng.normal(0, 0.0012, K)) + rng.normal(0, 0.012) * (st / L) ** 1.5
            ys = y0 + rng.normal(0, 0.006) - st * 0.97
            out.append(np.c_[xs, ys, np.zeros(K)])
    P = np.array(out)
    S = len(P)
    P = wave_lines(P, cfg["wave"], rng, axes=(0, 2), lam=(0.03, 0.06), start=(0.0, 0.15))
    zm = grid_z(grid, P[..., 0].ravel(), P[..., 1].ravel()).reshape(S, K)
    zf = (pk.front_z(P[..., 0].ravel(), P[..., 1].ravel()).reshape(S, K) + clear(P[..., 1]) + 0.004)
    from scipy.ndimage import gaussian_filter1d
    P[..., 2] = gaussian_filter1d(np.maximum(zm, zf) + 0.0065, 1.5, axis=1, mode="nearest") + P[..., 2]
    return g2b(P)


# ================= main =================
def hood_clear(pk, C, w, d, margin=0.003, most=0.035):
    """Locks (glTF centre lines, widths, depths) held in front of the hood's collar: each ring's sides and front checked
    against the hood's front seen from the front; the line moved forward by what is behind it (smoothed), a lock that
    would need more than `most` dropped (rooted too far under the collar). Returns lines and the locks kept."""
    if pk.hood is None:
        return C, np.ones(len(C), bool)
    t, _, _ = frames(C)
    out = outward(pk, C)                         # (as tubes() lays its rings)
    side = np.cross(t, out)
    side /= np.linalg.norm(side, axis=2)[..., None] + 1e-12
    out = np.cross(side, t)
    need = np.zeros(C.shape[:2])
    prof = np.interp(np.linspace(0, 1, C.shape[1]), [0, 0.15], [0.55, 1.0])[None, :, None]   # (tubes()' root_w)
    for sx, so in ((1, 0), (-1, 0), (0.7, 0.7), (-0.7, 0.7), (0, 1), (0.7, -0.7), (-0.7, -0.7), (0, -1)):
        Q = C + side * (sx * w[:, None, None] * prof / 2) + out * (so * d[:, None, None] / 2)
        cov = pk.hood_cover(Q.reshape(-1, 3)).reshape(C.shape[:2])
        need = np.maximum(need, np.where(np.isfinite(cov), cov + margin, 0.0))
    need = np.maximum(need, 0) * (C[:, :, 1] < 1.565)
    from scipy.ndimage import maximum_filter1d, gaussian_filter1d
    need = gaussian_filter1d(maximum_filter1d(need, 5, axis=1), 1.5, axis=1)
    keep = need.max(1) <= most
    C = C.copy()
    C[:, :, 2] += need
    return C, keep


def tubes_by_length(pk, C, w, d, n, shade, rng, Ks=((0.16, 6), (0.30, 9), (9.0, 11)), tip_pow=1.7):
    """tubes() with as many rings as a lock is long (short locks fewer)."""
    L = np.linalg.norm(np.diff(C, axis=1), axis=2).sum(1)
    out, lo = [], 0.0
    for hi, K in Ks:
        m = (L >= lo) & (L < hi)
        if m.any():
            out.append(tubes(pk, C[m], w[m], d[m], n, K, shade, rng, tip_pow, root_w=0.55))
        lo = hi
    return cat_parts(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pkg")
    ap.add_argument("--work", default=None)
    ap.add_argument("--seed", type=int, default=29)
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--no-preview", action="store_true")
    a = ap.parse_args()
    work = a.work or os.path.join(a.pkg, "..", "_beard_work")
    os.makedirs(work, exist_ok=True)
    rng = np.random.default_rng(a.seed)
    lrng = np.random.default_rng(a.seed + 1)   # (the LOD's and shadow's own draws: the full mesh unchanged by them)
    t0 = time.time()
    pk = Package(a.pkg, rng)
    report = {"locks": {}, "cards": {}}
    mass, lod_mass, shadow_mass, cards = [], [], [], []

    # the soft edge first (on the bare skin): short fine cards lying on it at the line
    ep, en, _ = root_points(pk, rng, 0.0078, "edge")
    elen = rng.uniform(*FINE["length"], len(ep))
    Pe, _ = grow(pk, ep, en, "edge", FINE, rng, elen.max())
    Pe = trim(Pe, elen)
    collider(pk, face_only=False)
    cards.append(card_set(Pe, FINE, rng, FINE["K"], alpha=FINE["alpha"], edge=True))
    report["cards"]["edge"] = len(ep)

    # the mass: the moustache's locks, then the beard's inner and outer locks
    Cm, wm, dm = lock_lines(pk, "moustache", MASS_MOUSTACHE, rng)
    Cm, _ = hood_clear(pk, Cm, wm, dm, most=1.0)
    mass.append(tubes(pk, Cm, wm, dm, MASS_MOUSTACHE["n"], 8, MASS_MOUSTACHE["shade"], rng, tip_pow=1.4))
    lod_mass.append(tubes(pk, Cm[::2], wm[::2] * 1.3, dm[::2], LOD1_MASS["n"], 5, MASS_MOUSTACHE["shade"], lrng, tip_pow=1.4))
    report["locks"]["moustache"] = len(Cm)
    for L_ in MASS_LAYERS:
        C, w, d = lock_lines(pk, "beard", L_, rng)
        C, kp = hood_clear(pk, C, w, d)
        report.setdefault("droppedUnderCollar", {})[L_["name"]] = int((~kp).sum())
        C, w, d = C[kp], w[kp], d[kp]
        mass.append(tubes_by_length(pk, C, w, d, L_["n"], L_["shade"], rng, tip_pow=L_["tip"]))
        lod_mass.append(tubes(pk, C[::2], w[::2] * 1.35, d[::2], LOD1_MASS["n"], LOD1_MASS["K"], L_["shade"], lrng))
        sel = slice(None) if L_["name"] == "inner" else slice(None, None, 2)
        shadow_mass.append(tubes(pk, C[sel], w[sel], d[sel], SHADOW_MASS["n"], SHADOW_MASS["K"], L_["shade"], lrng))
        report["locks"][L_["name"]] = len(C)

    # the braids and their cord bands on the mass's front
    mP0 = np.concatenate([p["pos"] for p in mass]); mF0 = np.concatenate([p["idx"] + o for p, o in zip(mass, np.cumsum([0] + [len(p["pos"]) for p in mass])[:-1])])
    grid = surface_grid(mP0, mF0)
    br, ties, br_lod = braids(pk, grid, rng, lrng)
    report["braids"] = len(BRAIDS)
    # the fringe: fewer, finer cards over the mass's outside (the mass in the drape's collider), and a few strays
    strands_collider(pk, mass)
    fp, fn, _ = root_points(pk, rng, FRINGE["spacing"], "beard")
    adx = np.abs(fp[:, 0] - X0)
    tip = np.interp(adx, [0, 0.03, 0.06, 0.09], [TIP_Y[0], TIP_Y[0] + 0.02, TIP_Y[0] + 0.07, TIP_Y[1]])
    tip = tip + rng.normal(0, FRINGE["jit"], len(fp)) - rng.uniform(*FRINGE["past"], len(fp))   # (past the mass's points)
    tip = np.maximum(tip, 1.0)
    length = (fp[:, 1] - tip) + 0.10 + 0.08 * smoothstep(0.03, 0.08, adx)
    fcfg = dict(FRINGE, off=0.0035, front=FRINGE["off"])
    Pf, _ = grow(pk, fp, fn, "beard", fcfg, rng, length.max())
    Pf = trim(Pf, to_height(Pf, tip, length))
    Pf = clump(Pf, FRINGE["clump"], max(3, len(Pf) // 3), rng, start=0.4)
    Pf = wave_lines(Pf, FRINGE["wave"], rng, axes=(0, 1))
    # (the outline: thin cards rooted on the beard's outer sides, its silhouette broken into strands)
    op, on_, _ = root_points(pk, rng, OUTLINE["spacing"], "beard")
    keep = np.abs(op[:, 0] - X0) > OUTLINE["min_dx"]
    op, on_ = op[keep], on_[keep]
    oadx = np.abs(op[:, 0] - X0)
    otip = np.interp(oadx, [0, 0.03, 0.06, 0.09], [TIP_Y[0], TIP_Y[0] + 0.02, TIP_Y[0] + 0.07, TIP_Y[1]]) + rng.normal(0, 0.06, len(op)) - 0.02
    olen = (op[:, 1] - otip) + 0.10 + 0.08 * smoothstep(0.03, 0.08, oadx)
    Po, _ = grow(pk, op, on_, "beard", dict(OUTLINE, off=0.0035, front=OUTLINE["off"]), rng, olen.max())
    Po = trim(Po, to_height(Po, otip, olen))
    Po = wave_lines(Po, OUTLINE["wave"], rng, axes=(0, 1))
    report["cards"]["outline"] = len(op)
    # (the cards' collider the mass itself and the face: their normals the mass's, and onto() holds them to it; on
    # his body's two-sided cloth the normals cancelled and threw 10 of 25 cards' edges wide)
    mP = np.concatenate([p["pos"] for p in mass]); mN = np.concatenate([p["nrm"] for p in mass])
    cP, cN = g2b(np.vstack([mP, pk.face_pts])), g2b(np.vstack([mN, pk.face_nrm]))
    HH.update(COLLIDE_P=cP, COLLIDE_N=cN, COLLIDE=cKDTree(cP), COLLIDE_HEAD=np.r_[np.zeros(len(mP), bool), pk.face_pts[:, 1] > 1.555],
              NECK=np.zeros(len(cP), bool))
    cards.append(card_set(Pf, dict(FRINGE, off=0.003), rng, FRINGE["K"]))
    cards.append(card_set(Po, dict(OUTLINE, off=0.003), rng, OUTLINE["K"]))
    report["cards"]["fringe"] = len(fp)
    # (strays: a few fine strands lifted off the mass, wandering a little)
    si = rng.choice(len(Pf), min(STRAYS["n"], len(Pf)), replace=False)
    Ps = Pf[si].copy()
    S_, K_ = Ps.shape[:2]
    f = np.linspace(0, 1, K_)[None, :, None]
    wob = rng.normal(0, 1, (S_, 1, 3)) * np.array([0.012, 0.006, 0.0])
    Ps = Ps + wob * np.sin(f * np.pi * rng.uniform(1, 2.5, (S_, 1, 1))) * smoothstep(0.1, 0.4, f)
    Ps[:, :, 1] -= 0.006 * smoothstep(0.1, 0.5, f[..., 0])     # (Blender -y: forward, off the mass)
    cards.append(card_set(Ps, dict(STRAYS, off=0.003), rng, STRAYS["K"]))
    report["cards"]["strays"] = len(si)

    # (the weed: over the mass and the cards, its own material)
    weed_p = card_part(pk, [card_set(weed_lines(pk, grid, rng), WEED, rng, WEED["K"])])
    report["weed"] = int(weed_p["pos"].shape[0] // (3 * WEED["K"]))
    mass_p = skin_part(pk, cat_parts(mass + [br]))
    card_p = card_part(pk, cards)
    tie_p = skin_part(pk, ties)
    lod_p = skin_part(pk, cat_parts(lod_mass + [br_lod]))
    sh_p = skin_part(pk, cat_parts(shadow_mass + [br_lod]))
    report.update(massTris=int(len(mass_p["idx"])), cardTris=int(len(card_p["idx"])), tieTris=int(len(tie_p["idx"])), weedTris=int(len(weed_p["idx"])),
                  tris=int(len(mass_p["idx"]) + len(card_p["idx"]) + len(tie_p["idx"]) + len(weed_p["idx"])),
                  lodTris=int(len(lod_p["idx"])), shadowTris=int(len(sh_p["idx"])),
                  restMass=measure(pk, mass_p), restCards=measure(pk, card_p), colour=COLOUR, seconds=round(time.time() - t0, 1))
    log(json.dumps(report))
    json.dump(report, open(os.path.join(work, "beard_report.json"), "w"), indent=1)
    np.savez(os.path.join(work, "beard_mass.npz"), **{k: v for k, v in mass_p.items() if isinstance(v, np.ndarray)})
    if not a.no_preview:
        mass_p["tint"], card_p["tint"] = (0.75, 0.62, 0.45), (0.55, 0.75, 0.95)
        lod_p["tint"] = (0.62, 0.60, 0.55)
        preview(pk, [mass_p, card_p], os.path.join(work, "beard_preview.png"))
        preview(pk, [lod_p], os.path.join(work, "beard_lod1_preview.png"), views=("front", "q"))
        log(f"previews {time.time() - t0:.0f} s")
    if a.no_write:
        return
    mass_texture(os.path.join(a.pkg, MASS_TEX))
    card_texture(os.path.join(a.pkg, CARDS_TEX))
    sh = dict(pos=sh_p["pos"], nrm=sh_p["nrm"], J=sh_p["J"], W=sh_p["W"], idx=sh_p["idx"])
    write(pk, os.path.join(a.pkg, "beard.glb"), [("beard", [(mass_p, 2), (card_p, 0), (tie_p, 3), (weed_p, 4)]), ("beard.lod1", [(lod_p, 2)]), ("beard.shadow", [(sh, 1)])])
    man_path = os.path.join(a.pkg, "manifest.json")
    man = json.load(open(man_path, encoding="utf-8"))
    man["hair"] = {"file": "beard.glb", "colour": COLOUR, "style": "beard", "uniforms": HAIR_UNIFORMS,
                   "source": "tools/assets/warden_beard.py (r5: wet-lock mass on heroine_hair.py's drape, braids with cord bands, river weed, a waved card fringe)",
                   "tris": report["tris"], "massTris": report["massTris"], "cardTris": report["cardTris"], "lodTris": report["lodTris"],
                   "shadowTris": report["shadowTris"], "locks": report["locks"], "cards": report["cards"], "braids": report["braids"], "weed": report["weed"]}
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
