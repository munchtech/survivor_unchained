"""A face's whole shape taken from a picture of it: her MakeHuman head (as
heroine_head.py makes it: face_shapes's MACROS, FACE and BUILD) moved,
every point of her face, onto the face in the picture, and written as a
MakeHuman target of our own (heroine_head.py loads it as it loads
MakeHuman's own).

    blender -b --python tools/assets/face_warp.py -- <picture.png> <moge.glb> <marks.json> <anchors.npz> <out.target> [--check <dir>]

picture.png: the woman, from in front (face_refs.py's left half, say).
moge.glb: MoGe-2's surface of it (the local ComfyUI's MoGePointMapToMesh,
every pixel a point, its UV the pixel: tools/assets/face_moge.py).
marks.json: MediaPipe's landmarks on it (face_fit.py `marks`).
anchors.npz: face_lab.py's `anchor` of her own face seen from in front
(each landmark's point on her).

Why: MakeHuman's targets are broad strokes. Fitted to a reference by its
landmarks they can't make full lips, almond eyes with a lid's fold, high
cheekbones and a small chin all at once: every preset came out the same
face, thin of lip and small of eye. MoGe reads the picture's whole surface
(its lids, its lips' volume, its cheeks), and her own points can be laid
on it.

How:
  1. The picture's surface placed on her: turned, scaled and moved so its
     landmarks on her eyes, nose and mouth lie on hers, its depth scaled
     on its own. (Landmarks on the rims of her openings, and on her face's
     outline, are first moved to her surface: face_lab.py's rays went on
     through them, into her eye sockets and mouth, or past her jaw.)
  2a. Across (x and z, as the camera sees her): every landmark where the
     picture has it, her surface bent as little as can be; her ears, her
     head behind them and her neck held.
  2b. In depth: her skin brought to the picture's surface straight before
     or behind it, from brow to chin where both face the camera, not round
     her eyes nor in her mouth; as deep as hers at her face's edge.
  3. Her eyes moved, each eyeball whole, with the skin round it; her lids
     and sockets laid back on them as they lay; her lashes, teeth and
     tongue moved with what they sit in.

EXPERIMENTAL, not yet good enough to build her with (2026-10-04, against
heroine_11): across alone narrows her face to the picture's, but leaves a
ridge along her jaw (the skin under it doesn't follow); in depth, MoGe's
surface is flatter than its own normals say, and laid on her it made her
face a flat mask, stepped at its edge. WARP_NORMALS=<moge_normal png>
remakes the surface's depth from MoGe's normals (integrated; its broad
shape from its depths): clean, no stripes, but its relief came out a
quarter of MoGe's depths' (check the normals' decoding, sRGB or sign,
against the point map's own slopes, before trusting it). Next: that check;
the depth data faded softly to nothing toward her face's edge (it is cut
off there now, and the face steps); her jaw's underside moved with her jaw.
Debugging: WARP_NO_ACROSS=1 or WARP_NO_DEPTH=1 skip a stage, WARP_DUMP=<npz>
writes the landmarks as read on each.
"""
import gzip
import math
import os
import sys

import bpy
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from scipy.spatial import cKDTree

sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import face_shapes as fs  # noqa: E402

from bl_ext.user_default.mpfb.services.humanservice import HumanService  # noqa: E402
from bl_ext.user_default.mpfb.services.targetservice import TargetService  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:]
PIC, MOGE, MARKS, ANCH, OUT = (os.path.abspath(a) for a in ARGS[:5])
CHECK = os.path.abspath(ARGS[ARGS.index("--check") + 1]) if "--check" in ARGS else None

# MediaPipe's landmarks by what they mark (face_fit.py's).
OVAL = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136,
        172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]
LIPS = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 185, 40, 39, 37, 0, 267, 269, 270, 409, 78, 95, 88, 178, 87, 14, 317,
        402, 318, 324, 308, 191, 80, 81, 82, 13, 312, 311, 310, 415]
INNER_LIPS = [78, 191, 80, 81, 82, 13, 312, 311, 310, 415, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95]
EYE_A = [33, 246, 161, 160, 159, 158, 157, 173, 133, 155, 154, 153, 145, 144, 163, 7]
EYE_B = [263, 466, 388, 387, 386, 385, 384, 398, 362, 382, 381, 380, 374, 373, 390, 249]
BROWS = [70, 63, 105, 66, 107, 55, 65, 52, 53, 46, 300, 293, 334, 296, 336, 285, 295, 282, 283, 276]
NOSE = [1, 2, 98, 327, 4, 5, 195, 197, 6, 168, 48, 278, 64, 294, 129, 358, 49, 279, 115, 344, 220, 440]
IRIS = list(range(468, 478))
CORE = EYE_A + EYE_B + NOSE + LIPS


def weights(n):
    """How surely each landmark is taken where the picture has it: her
    features' outlines most; her face's outline less (MediaPipe reads it off
    a soft edge, and the surface holds it anyway); the irises not at all
    (they are her eyeballs', not her skin's)."""
    w = np.full(n, 0.4)
    for group, v in ((OVAL, 0.5), (LIPS, 1.6), (EYE_A, 1.6), (EYE_B, 1.6), (BROWS, 0.8), (NOSE, 1.3)):
        w[group] = v
    w[[i for i in IRIS if i < n]] = 0.0
    return w


def smooth01(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def umeyama(src, dst, wt):
    """The scale, turn and shift taking src to dst, weighted (least squares)."""
    W = wt / wt.sum()
    ms, md = (W[:, None] * src).sum(0), (W[:, None] * dst).sum(0)
    a, b = src - ms, dst - md
    C = (W[:, None] * b).T @ a
    U, S, Vt = np.linalg.svd(C)
    D = np.diag([1, 1, np.sign(np.linalg.det(U @ Vt))])
    R = U @ D @ Vt
    s = (S * np.diag(D)).sum() / (W * (a * a).sum(1)).sum()
    return s, R, md - s * R @ ms


def inside(poly, pts):
    """Which 2D points lie inside a polygon (even-odd)."""
    x, y = pts[:, 0], pts[:, 1]
    res = np.zeros(len(pts), bool)
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        cross = ((yi > y) != (yj > y)) & (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi)
        res ^= cross
        j = i
    return res


# ---------------------------------------------------------------- her --
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
hm = HumanService.create_human(mask_helpers=True, detailed_helpers=True, extra_vertex_groups=True, feet_on_ground=True,
                               scale=0.1, macro_detail_dict=fs.MACROS)
TARGET = fs.target_paths()
for t, v in {**fs.FACE, **fs.BUILD}.items():
    if t in fs.SCULPTS or t.startswith("portrait-"):
        continue
    for n in fs.sides([t]):
        TargetService.load_target(hm, TARGET[n], weight=v, name="face_" + n)
for mo in hm.modifiers:
    mo.show_viewport = mo.show_render = False
bpy.context.view_layer.update()
MW = np.array(hm.matrix_world)


def positions():
    dg = bpy.context.evaluated_depsgraph_get()
    e = hm.evaluated_get(dg)
    m = e.to_mesh()
    V = np.array([v.co[:] for v in m.vertices])
    e.to_mesh_clear()
    assert len(V) == len(hm.data.vertices)
    return V @ MW[:3, :3].T + MW[:3, 3]


P = positions()
for t, v in fs.FACE.items():                     # (her face's own sculpts, as face_lab.py and heroine_head.py lay them)
    if t in fs.SCULPTS:
        P = P + v * fs.SCULPTS[t](P, fs.anatomy(P))
NV = len(P)
groups = {g.name: g.index for g in hm.vertex_groups}
member = {name: np.zeros(NV, bool) for name in groups}
_gi = {i: n for n, i in groups.items()}
for v in hm.data.vertices:
    for g in v.groups:
        if g.weight > 0.5:
            member[_gi[g.group]][v.index] = True
BODY = member["body"]

an = np.load(ANCH)
tri, bary, hit = an["tri"].copy(), an["bary"].copy(), an["hit"].copy()
L0 = (P[tri] * bary[:, :, None]).sum(1)
if np.abs(L0[hit] - an["P0"][hit]).max() > 1e-4:
    print("WARNING: the anchors were read off another face (%.1f mm off)" % (1000 * np.abs(L0[hit] - an["P0"][hit]).max()))
hit[IRIS] = False
# A landmark on the edge of an opening (her lids' rims, where her lips
# meet) or of her face's outline was anchored where the camera's ray went
# on through it (into her eye's socket, her mouth, past her cheek): such
# an anchor is moved to the nearest of her points the camera sees.
_me = hm.data
_me.calc_loop_triangles()
_F = np.array([t.vertices[:] for t in _me.loop_triangles])
_F = _F[BODY[_F].all(1)]
_bvh = BVHTree.FromPolygons([tuple(p) for p in P], _F.tolist())
_head = np.where(BODY & (P[:, 2] > L0[152, 2] - 0.02) & (P[:, 1] < L0[hit, 1].max() + 0.02))[0]
_seen = np.array([_bvh.ray_cast(Vector(P[i]) + Vector((0, -0.0003, 0)), Vector((0, -1, 0)), 1.0)[0] is None for i in _head])
VIS = _head[_seen]
_vt = cKDTree(P[VIS][:, [0, 2]])
_front = np.array([P[VIS[_vt.query_ball_point(L0[i, [0, 2]], 0.003) or [_vt.query(L0[i, [0, 2]])[1]]], 1].min() for i in range(len(L0))])
_deep = hit & (L0[:, 1] > _front + 0.002)
# (her face's outline below her brows is where her surface turns away from
# the camera: her cheeks' and jaw's edges, the underside of her chin; the
# nearest of those, not the nearest point the camera sees, which can be her
# neck under her jaw)
_fn = np.zeros((NV, 3))
_fa = np.cross(P[_F[:, 1]] - P[_F[:, 0]], P[_F[:, 2]] - P[_F[:, 0]])
for _k in range(3):
    np.add.at(_fn, _F[:, _k], _fa)
_fn /= np.linalg.norm(_fn, axis=1)[:, None] + 1e-12
if (_fn[VIS][:, 1] < 0).mean() < 0.5:
    _fn = -_fn
_ear = np.abs(L0[[234, 454], 0]).max()
_edge = VIS[(np.abs(_fn[VIS, 1]) < 0.35) & (P[VIS, 2] > L0[152, 2] - 0.012) & (np.abs(P[VIS, 0]) < _ear + 0.002)]
_et = cKDTree(P[_edge][:, [0, 2]])
for i in np.where(_deep)[0]:
    if i in OVAL and L0[i, 2] < L0[168, 2]:
        v = _edge[_et.query(L0[i, [0, 2]])[1]]
    else:
        v = VIS[_vt.query(L0[i, [0, 2]])[1]]
    tri[i], bary[i] = [v, v, v], [1.0, 0.0, 0.0]
L0 = (P[tri] * bary[:, :, None]).sum(1)
print("ANCHORS: %d moved to her surface from behind it (%s)" % (_deep.sum(), ", ".join(
    "%s %d" % (nm, _deep[g].sum()) for nm, g in (("oval", OVAL), ("lips", LIPS), ("eyes", EYE_A + EYE_B), ("brows", BROWS),
                                                ("nose", NOSE)))))

# ------------------------------------------------- the picture's surface --
import json  # noqa: E402

from PIL import Image  # noqa: E402

pic = Image.open(PIC)
PW, PH = pic.size
marks = json.load(open(MARKS, encoding="utf-8-sig"))
Lp = np.array(marks["points"])[:, :2]
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=MOGE)
mo_ = next(o for o in bpy.data.objects if o not in before and o.type == "MESH")
mme = mo_.data
MV = np.array([v.co[:] for v in mme.vertices]) @ np.array(mo_.matrix_world)[:3, :3].T + np.array(mo_.matrix_world)[:3, 3]
_uvd = np.array([d.uv[:] for d in mme.uv_layers[0].data])
_li = np.zeros(len(mme.loops), int)
mme.loops.foreach_get("vertex_index", _li)
MUV = np.zeros((len(MV), 2))
MUV[_li] = _uvd
MPX = np.c_[MUV[:, 0] * PW, (1 - MUV[:, 1]) * PH]          # (each point's pixel)
mme.calc_loop_triangles()
MT = np.array([t.vertices[:] for t in mme.loop_triangles])
_ptree = cKDTree(MPX)


def at_pixels(px):
    """The surface's points at pixels (the nearest four, by nearness)."""
    dd, kk = _ptree.query(px, k=4)
    ww = 1 / (dd + 0.25)
    return (MV[kk] * ww[:, :, None]).sum(1) / ww.sum(1)[:, None]




def from_normals(path):
    """The surface's depths remade from MoGe's own normals (its picture,
    normal_opengl), which carry the face's relief far better than its depths:
    the normals' slopes integrated over the face (least squares, so it holds
    together), its broadest shape left to MoGe's depths."""
    from scipy import ndimage
    nimg = np.asarray(Image.open(path).convert("RGB"), np.float64) / 255 * 2 - 1
    H, W = nimg.shape[:2]
    # (each point's pixel, rounded, and the face's box with a margin)
    col = np.clip(np.round(MPX[:, 0] - 0.5).astype(int), 0, W - 1)
    row = np.clip(np.round(MPX[:, 1] - 0.5).astype(int), 0, H - 1)
    x0, y0 = np.maximum(Lp.min(0).astype(int) - 40, 0)
    x1, y1 = np.minimum(Lp.max(0).astype(int) + 40, [W - 1, H - 1])
    depth = np.full((H, W), np.nan)
    depth[row, col] = MV[:, 1]
    sub = depth[y0:y1, x0:x1]
    nz = np.clip(nimg[y0:y1, x0:x1, 2], 0.2, None)
    gx = -nimg[y0:y1, x0:x1, 0] / nz                       # (height toward the camera, per pixel right)
    gy = nimg[y0:y1, x0:x1, 1] / nz                        # (per pixel down: its normals' y is up)
    ok = np.isfinite(sub)
    h, w = sub.shape
    ids = -np.ones((h, w), int)
    ids[ok] = np.arange(ok.sum())
    rr, cc, vv, bb = [], [], [], []
    k = 0
    for dy_, dx_, g in ((0, 1, gx), (1, 0, gy)):
        a = ids[:h - dy_, :w - dx_]
        b = ids[dy_:, dx_:]
        m = (a >= 0) & (b >= 0)
        gg = 0.5 * (g[:h - dy_, :w - dx_] + g[dy_:, dx_:])[m]
        n_ = m.sum()
        rr += [np.arange(k, k + n_)] * 2
        cc += [b[m], a[m]]
        vv += [np.ones(n_), -np.ones(n_)]
        bb.append(gg)
        k += n_
    A = sp.coo_matrix((np.concatenate(vv), (np.concatenate(rr), np.concatenate(cc))), shape=(k, ok.sum())).tocsr()
    # (solved directly: an iterative solve leaves the broad slopes unsettled, flat)
    hpx = spl.spsolve((A.T @ A + 1e-6 * sp.eye(ok.sum())).tocsc(), A.T @ np.concatenate(bb))
    # (pixels to the surface's own units: how far apart neighbouring points lie across)
    xmap = np.full((H, W), np.nan)
    xmap[row, col] = MV[:, 0]
    px = np.nanmedian(np.abs(np.diff(xmap[y0:y1, x0:x1], axis=1)))
    hy = np.full((h, w), np.nan)
    hy[ok] = -hpx * px                                     # (depth: away from the camera)
    # Its broad shape from MoGe's depths: both blurred wide, the difference added back.
    def blur(img, s):
        m_ = np.isfinite(img)
        num = ndimage.gaussian_filter(np.where(m_, img, 0), s)
        den = ndimage.gaussian_filter(m_.astype(float), s)
        return num / np.maximum(den, 1e-6)
    s_ = max(h, w) / 8
    fused = hy - blur(hy, s_) + blur(sub, s_)
    rel = np.nanstd(hy - blur(hy, s_)) / max(np.nanstd(sub - blur(sub, s_)), 1e-9)
    print("NORMALS: relief from the normals %.2f times MoGe's own" % rel)
    inbox = (col >= x0) & (col < x1) & (row >= y0) & (row < y1)
    fz = np.full(len(MV), np.nan)
    fz[inbox] = fused[row[inbox] - y0, col[inbox] - x0]
    good = np.isfinite(fz)
    # (each point moved along its own ray from the camera, to its new depth)
    MV[good] = MV[good] * (fz[good] / MV[good, 1])[:, None]


if os.environ.get("WARP_NORMALS"):
    from_normals(os.environ["WARP_NORMALS"])
Lr = at_pixels(Lp)
if os.environ.get("WARP_DUMP"):
    np.savez(os.environ["WARP_DUMP"], Lr=Lr, L0=L0, hit=hit, Lp=Lp)
# 1. Placed on her by her eyes, nose and mouth: a turn, a scale and a
# shift, and its depth scaled on its own (MoGe reads a face's depth from
# the picture's look; how deep, against how wide, it guesses with the
# lens, and a long lens's portrait it reads deeper or shallower than it
# is): the depth's scale fitted between turns, so her face's relief, nose
# tip to cheek to ear, is hers and its shape the picture's.
wc = np.zeros(len(L0))
wc[CORE] = 1.0
wc *= hit
k_ = 1.0
for _ in range(6):
    Ls = Lr * [1.0, k_, 1.0]
    s_, R_, t_ = umeyama(Ls, L0, wc)
    # (then the depth scale that best lays the picture's landmarks on hers, so placed)
    Lc = Lr - (wc[:, None] * Lr).sum(0) / wc.sum()
    u = s_ * (Lc * [1.0, 0.0, 1.0]) @ R_.T
    v = s_ * (Lc * [0.0, 1.0, 0.0]) @ R_.T
    L0c = L0 - (wc[:, None] * L0).sum(0) / wc.sum()
    k_ = float(np.clip((wc * (v * (L0c - u)).sum(1)).sum() / (wc * (v * v).sum(1)).sum(), 0.3, 3.0))
MV = s_ * (MV * [1.0, k_, 1.0]) @ R_.T + t_
Lr = s_ * (Lr * [1.0, k_, 1.0]) @ R_.T + t_
_turn = math.degrees(math.acos(min(1, (np.trace(R_) - 1) / 2)))
print("PLACED: scaled %.3f, its depth %.2f times more, turned %.1f deg; her landmarks %.1f mm from the picture's (rms)"
      % (s_, k_, _turn, 1000 * np.sqrt((wc * ((Lr - L0) ** 2).sum(1)).sum() / wc.sum())))
# (only the surface round her face: within the picture's face, a margin round it)
lo_, hi_ = Lr[OVAL].min(0) - 0.03, Lr[OVAL].max(0) + 0.03
keepv = ((MV[:, 0] > lo_[0]) & (MV[:, 0] < hi_[0]) & (MV[:, 2] > lo_[2]) & (MV[:, 2] < hi_[2])
         & (MV[:, 1] > Lr[:, 1].min() - 0.05) & (MV[:, 1] < Lr[:, 1].max() + 0.06))
MTk = MT[keepv[MT].all(1)]
# (its pixel-fine roughness smoothed away: a few rounds of averaging each
# point with its neighbours along the surface, across the picture only)
_n = len(MV)
_e = np.vstack([MTk[:, [0, 1]], MTk[:, [1, 2]], MTk[:, [2, 0]]])
_A = sp.coo_matrix((np.ones(len(_e)), (_e[:, 0], _e[:, 1])), shape=(_n, _n)).tocsr()
_A = ((_A + _A.T) > 0).astype(float)
_deg = np.asarray(_A.sum(1)).ravel()
_Av = sp.diags(1 / np.maximum(_deg, 1)) @ _A
for _ in range(20):
    sm = _Av @ MV
    MV = np.where((_deg > 0)[:, None], 0.5 * MV + 0.5 * sm, MV)
SURF = BVHTree.FromPolygons([tuple(p) for p in MV], MTk.tolist())
for nm, g in (("oval", OVAL), ("lips", LIPS), ("eyes", EYE_A + EYE_B), ("brows", BROWS), ("nose", NOSE)):
    dd = (Lr - L0)[g][hit[g]]
    print("MOVES %-6s %.1f mm (rms), across %.1f, in depth %.1f" % (nm, 1000 * np.sqrt((dd ** 2).sum(1).mean()),
                                                                  1000 * np.sqrt((dd[:, [0, 2]] ** 2).sum(1).mean()),
                                                                  1000 * np.sqrt((dd[:, 1] ** 2).mean())))

# ------------------------------------------------------- 2. laid on it --
me = hm.data
me.calc_loop_triangles()
F = np.array([t.vertices[:] for t in me.loop_triangles])
F = F[BODY[F].all(1)]
chin_z = L0[152, 2]
region = BODY & (P[:, 2] > chin_z - 0.09)
idx = np.where(region)[0]
loc = -np.ones(NV, int)
loc[idx] = np.arange(len(idx))
Fr = F[region[F].all(1)]
e = loc[np.vstack([Fr[:, [0, 1]], Fr[:, [1, 2]], Fr[:, [2, 0]]])]
n = len(idx)
Adj = sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)).tocsr()
Adj = ((Adj + Adj.T) > 0).astype(float)
deg = np.asarray(Adj.sum(1)).ravel()
Lap = sp.eye(n) - sp.diags(1 / np.maximum(deg, 1)) @ Adj
# Her normals as she is (out from her).
Nv = np.zeros((NV, 3))
fn = np.cross(P[F[:, 1]] - P[F[:, 0]], P[F[:, 2]] - P[F[:, 0]])
for k in range(3):
    np.add.at(Nv, F[:, k], fn)
Nv /= np.linalg.norm(Nv, axis=1)[:, None] + 1e-12
if (Nv[BODY & (P[:, 2] > chin_z)][:, 1] < 0).mean() < 0.3:
    Nv = -Nv
# What is held still: her ears, her head behind them, her neck below her
# jaw, and all of her past 9 cm from any landmark. A narrower face narrows
# her jaw back to its angles, and her temples (held close round her face,
# a narrower face stood out of a wide head like a mask).
dl = cKDTree(L0[hit]).query(P[idx])[0]
ear_x = np.abs(L0[[234, 454], 0]).max()
ear_y = L0[[234, 454], 1].mean()
ears = ((np.abs(P[idx, 0]) > ear_x + 0.004) & (P[idx, 1] > ear_y - 0.004) & (P[idx, 2] > L0[2, 2] - 0.012)
        & (P[idx, 2] < L0[105, 2] + 0.008))
hold = np.max([smooth01((dl - 0.045) / 0.045), smooth01((P[idx, 1] - ear_y - 0.012) / 0.03),
               smooth01((chin_z - 0.025 - P[idx, 2]) / 0.04), ears * 1.0], 0)
rows = np.arange(len(L0))[hit]
Bm = sp.coo_matrix((bary[rows].ravel(), (np.repeat(np.arange(len(rows)), 3), loc[tri[rows]].ravel())), shape=(len(rows), n)).tocsr()
wa = weights(len(L0))[rows]
K_LM, K_BEND, K_HOLD = 4.0, 0.05, 6.0
# 2a. Across her face (x and z, as the camera sees her): every landmark
# where the picture has it, her surface bent as little as can be.
M = K_LM * Bm.T @ sp.diags(wa) @ Bm + K_BEND * (Lap.T @ Lap) + K_HOLD * sp.diags(hold) + 1e-9 * sp.eye(n)
solve = spl.factorized(M.tocsc())
d = np.zeros((n, 3))
for k in ((0, 2) if not os.environ.get("WARP_NO_ACROSS") else ()):
    d[:, k] = solve(K_LM * Bm.T @ (wa * (Lr - L0)[rows, k]))
got = Bm @ d
print("ACROSS: landmarks within %.2f mm (rms)" % (1000 * np.sqrt((((got - (Lr - L0)[rows])[:, [0, 2]]) ** 2).sum(1).mean())))
# 2b. In depth: each point of her skin brought to the picture's surface
# straight in front of or behind it (the picture's face as a height field
# over hers), from her brows to her chin, ear to ear, where she faces the
# camera; not round her eyes (her eyeballs and lids are moved whole, 3)
# nor in her mouth or nostrils. As deep as hers at her face's edges, where
# it meets her skull (the picture's depth there is least sure).
eye_c = []
for ring in (EYE_A, EYE_B):
    sx = np.sign(L0[ring, 0].mean())
    _ev = (member["helper-l-eye"] | member["helper-r-eye"]) & (np.sign(P[:, 0]) == sx)
    eye_c.append((P[_ev].mean(0), np.linalg.norm(P[_ev] - P[_ev].mean(0), axis=1).mean()))
Pa = P[idx] + d
oval2d = Lr[OVAL][:, [0, 2]]
cen = oval2d.mean(0)
in_face = inside(cen + (oval2d - cen) * 0.93, Pa[:, [0, 2]])
ring_ = in_face & ~inside(cen + (oval2d - cen) * 0.78, Pa[:, [0, 2]])
near_eye = np.min([np.linalg.norm(P[idx] - c, axis=1) - r for c, r in eye_c], 0)
mouth_open = inside(Lr[INNER_LIPS][:, [0, 2]], Pa[:, [0, 2]])
brow_z = Lr[BROWS, 2].max()
facing = np.clip(-Nv[idx, 1], 0, 1)
wb = (in_face & ~mouth_open) * smooth01((facing - 0.3) / 0.3) * smooth01((near_eye - 0.006) / 0.004) \
    * (1 - smooth01((Pa[:, 2] - brow_z - 0.015) / 0.02)) * (1 - hold)
hy = np.full(n, np.nan)
hf = np.zeros(n)
y0 = Lr[:, 1].min() - 0.1
for i in np.where(wb > 0.01)[0]:
    r = SURF.ray_cast(Vector((Pa[i, 0], y0, Pa[i, 2])), Vector((0, 1, 0)), 1.0)
    if r[0] is not None:
        hy[i], hf[i] = r[0][1], abs(r[1][1])
# (where the picture's surface turns away from its camera, at the edges of
# its face, its depth is the least sure)
wb *= smooth01((hf - 0.35) / 0.3)
dy = hy - Pa[:, 1]
ok = np.isfinite(dy) & (np.abs(dy) < 0.015)
off = np.median(dy[ok & ring_]) if (ok & ring_).sum() > 20 else np.median(dy[ok])
dy = np.where(ok, dy - off, 0.0)
wb = wb * ok
Mb = sp.diags(wb) + 0.5 * (Lap.T @ Lap) + K_HOLD * sp.diags(hold) + 1e-9 * sp.eye(n)
d[:, 1] = spl.spsolve(Mb.tocsc(), wb * dy) * (0.0 if os.environ.get("WARP_NO_DEPTH") else 1.0)
res = (d[:, 1] - dy)[wb > 0.5]
print("DEPTH: %d of her points on the picture's surface (its edge %.1f mm off hers); within %.2f mm (rms), %.1f mm the most moved"
      % ((wb > 0.5).sum(), 1000 * off, 1000 * np.sqrt((res ** 2).mean()), 1000 * np.abs(d[:, 1]).max()))
D = np.zeros((NV, 3))
D[idx] = d


# ------------------------------------------------------------ 3. eyes --
def sphere(Q):
    c = Q.mean(0)
    return c, np.linalg.norm(Q - c, axis=1).mean()


eyes_all = member["helper-l-eye"] | member["helper-r-eye"]
for ring in (EYE_A, EYE_B):
    sx = np.sign(L0[ring, 0].mean())
    eye = eyes_all & (np.sign(P[:, 0]) == sx)
    c0, r0 = sphere(P[eye])
    rad = np.linalg.norm(P - c0, axis=1)
    # (her eyeball moves as the skin of her lids round it has: across and in depth)
    rim = BODY & (rad < r0 + 0.006) & (rad > r0 - 0.002)
    shift = D[rim].mean(0)
    c1 = c0 + shift
    D[eye] = shift
    for jn in ("joint-l-eye", "joint-r-eye", "joint-l-eye-target", "joint-r-eye-target"):
        j = member.get(jn, np.zeros(NV, bool)) & (np.sign(P[:, 0]) == sx)
        D[j] = shift
    # (and every point of her lids and socket as far off it as it was, the
    # nearer the more so: her lids lie on her eyeball)
    lid = BODY & (rad < r0 + 0.007)
    off0 = rad[lid] - r0
    Q = P[lid] + D[lid]
    u = (Q - c1) / np.linalg.norm(Q - c1, axis=1)[:, None]
    lay = c1 + u * (r0 + off0)[:, None]
    t = 1 - smooth01((off0 - 0.003) / 0.004)
    D[lid] += (lay - Q) * t[:, None]
    print("EYE at x %+.3f: moved %.1f mm (%.1f deeper); %d points of lid and socket laid on it"
          % (sx * 0.03, 1000 * np.linalg.norm(shift), 1000 * shift[1], lid.sum()))
body_pts = np.where(BODY)[0]
tree = cKDTree(P[body_pts])
for gname in ("helper-l-eyelashes-1", "helper-l-eyelashes-2", "helper-r-eyelashes-1", "helper-r-eyelashes-2", "helper-hair",
              "joint-mouth", "joint-jaw", "joint-head", "joint-head-2", "joint-l-upperlid", "joint-l-lowerlid", "joint-r-upperlid",
              "joint-r-lowerlid"):
    g = member.get(gname)
    if g is None or not g.any():
        continue
    _, nn = tree.query(P[g], k=4)
    D[g] = D[body_pts[nn]].mean(1)
_mouth = (D[tri[INNER_LIPS]] * bary[INNER_LIPS][:, :, None]).sum(1).mean(0)
for gname in ("helper-upper-teeth", "helper-lower-teeth", "helper-tongue"):
    D[member[gname]] = _mouth

# ---- written as a MakeHuman target: each moved point in MakeHuman's own
# frame (y up, z toward her front, decimetres).
dl_ = D @ np.linalg.inv(MW[:3, :3]).T / 0.1
moved = np.where(np.linalg.norm(D, axis=1) > 1e-5)[0]
os.makedirs(os.path.dirname(OUT), exist_ok=True)
lines = ["# face_warp.py: her face laid on %s's" % os.path.basename(PIC)]
lines += ["%d %.6f %.6f %.6f" % (i, dl_[i, 0], dl_[i, 2], -dl_[i, 1]) for i in moved]
with (gzip.open(OUT, "wt") if OUT.endswith(".gz") else open(OUT, "w")) as f:
    f.write("\n".join(lines) + "\n")
print("TARGET", OUT, len(moved), "points")

# ---- check: her before and after, from in front and three-quarters.
if CHECK:
    bpy.data.objects.remove(mo_)
    os.makedirs(CHECK, exist_ok=True)
    kb = hm.shape_key_add(name="portrait", from_mix=False)
    basek = np.zeros(NV * 3)
    hm.data.shape_keys.reference_key.data.foreach_get("co", basek)
    kb.data.foreach_set("co", (basek + (D @ np.linalg.inv(MW[:3, :3]).T).ravel()).astype(np.float32))
    DATA = os.path.join(bpy.utils.user_resource("EXTENSIONS"), ".user", "user_default", "mpfb", "data")

    def image_material(name, path, alpha=False, rough=0.5):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        nt = m.node_tree
        bsdf = nt.nodes["Principled BSDF"]
        tx = nt.nodes.new("ShaderNodeTexImage")
        tx.image = bpy.data.images.load(path, check_existing=True)
        nt.links.new(tx.outputs["Color"], bsdf.inputs["Base Color"])
        if alpha:
            nt.links.new(tx.outputs["Alpha"], bsdf.inputs["Alpha"])
            m.surface_render_method = "DITHERED"
        bsdf.inputs["Roughness"].default_value = rough
        return m

    def mhmat_texture(mhmat):
        tex = next(line.split()[1] for line in open(mhmat, encoding="utf-8-sig") if line.startswith("diffuseTexture"))
        return os.path.join(os.path.dirname(mhmat), tex)

    def asset_mhmat(kind, name):
        dd = os.path.join(DATA, kind, name)
        return next(os.path.join(dd, f) for f in os.listdir(dd) if f.endswith(".mhmat"))

    hm.data.materials.clear()
    grey = bpy.data.materials.new("clay")
    grey.use_nodes = True
    grey.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.62, 0.52, 0.47, 1)
    grey.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.55
    hm.data.materials.append(grey)
    for mo in hm.modifiers:
        mo.show_viewport = mo.show_render = mo.type == "MASK"
    sc = bpy.context.scene
    proxies = []

    def fit_proxies(value):
        kb.value = value
        for o in proxies:
            bpy.data.objects.remove(o)
        proxies.clear()
        bpy.context.view_layer.update()
        for kind, name in fs.PARTS:
            if kind not in ("eyes", "eyelashes"):
                continue
            o = HumanService.add_mhclo_asset(os.path.join(DATA, kind, name, name + ".mhclo"), hm, asset_type=kind, subdiv_levels=0,
                                             material_type="NONE", set_up_rigging=False, interpolate_weights=False,
                                             import_subrig=False, import_weights=False)
            mhmat = os.path.join(DATA, "eyes", "materials", fs.EYES + ".mhmat") if kind == "eyes" else asset_mhmat(kind, name)
            o.data.materials.clear()
            o.data.materials.append(image_material(kind, mhmat_texture(mhmat), alpha=True, rough=0.1 if kind == "eyes" else 0.8))
            for mo in o.modifiers:
                mo.show_viewport = mo.show_render = False
            proxies.append(o)

    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            sc.render.engine = eng
            break
        except TypeError:
            pass
    sc.render.resolution_x = sc.render.resolution_y = 768
    sc.view_settings.view_transform = "AgX"
    sc.world = bpy.data.worlds.new("w")
    sc.world.use_nodes = True
    sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.32, 0.31, 0.30, 1)
    sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.6
    for rot, energy in (((math.radians(50), 0, math.radians(-30)), 3.0), ((math.radians(70), 0, math.radians(140)), 1.2),
                        ((math.radians(80), 0, math.radians(30)), 1.0)):
        ld = bpy.data.lights.new("sun", "SUN")
        ld.energy = energy
        ld.angle = math.radians(12)
        lo = bpy.data.objects.new("sun", ld)
        lo.rotation_euler = rot
        sc.collection.objects.link(lo)
    camo = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(camo)
    sc.camera = camo
    camo.data.type = "ORTHO"
    camo.data.ortho_scale = 0.26
    centre = Vector((0.0, float(L0[hit, 1].mean()), float(L0[[168, 152], 2].mean() + 0.02)))
    # (the picture's own surface as placed on her, to judge it by)
    _used = np.unique(MTk)
    _map = -np.ones(len(MV), int)
    _map[_used] = np.arange(len(_used))
    sme = bpy.data.meshes.new("picture")
    sme.from_pydata([tuple(p) for p in MV[_used]], [], _map[MTk].tolist())
    sob = bpy.data.objects.new("picture", sme)
    sc.collection.objects.link(sob)
    sme.materials.append(grey)
    for f_ in sme.polygons:
        f_.use_smooth = True
    for value in (0.0, 1.0, 2.0):
        sob.hide_render = value != 2.0
        hm.hide_render = value == 2.0
        fit_proxies(min(value, 1.0))
        for o in proxies:
            o.hide_render = value == 2.0
        for ang in (0.0, 35.0, 80.0):
            a_ = math.radians(ang)
            camo.location = centre + Vector((math.sin(a_), -math.cos(a_), 0)) * 2.0
            camo.rotation_euler = (centre - camo.location).to_track_quat("-Z", "Y").to_euler()
            bpy.context.view_layer.update()
            sc.render.filepath = os.path.join(CHECK, "w%d_%02d.png" % (value, ang))
            bpy.ops.render.render(write_still=True)
    print("CHECK", CHECK)
