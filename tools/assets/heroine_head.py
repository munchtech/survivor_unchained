"""Her head, made anew. The sculpt's (tools/assets/build_heroine.py) had her
hair fused into it and its eyes painted on, so nothing about it could be
changed. In its place a MakeHuman head (CC0, made by MPFB), bald, with eyes,
brows, lashes, teeth and tongue of its own, fitted to her face. Her
hairstyles are made on it after (tools/assets/heroine_hair.py), a file each,
for the game to swap and dye.

    blender -b tools/comfy/out/heroes/heroine_body.blend --python tools/assets/heroine_head.py -- \
        tools/comfy/out/heroes/heroine_built.blend godot/art/people

The scene is what build_heroine.py saved (her body, sculpted head and all);
the scene saved is the one the outfits are built on (heroine_outfits.py).

The sculpt's hair hung over her neck, shoulders and upper back, and there
was no skin under it. That region, above the surface CUT, is the MakeHuman
woman's too: fitted to her own skin wherever she has any, so her shape is
kept and only what was missing is MakeHuman's. It is joined to her body
along CUT, and her head, a mesh of its own for its shape keys, to it along
SPLIT, where the two share their points.

With HEAD_CHECK=<folder> in the environment, renders of each step are
written there.
"""
import math
import os
import shutil
import sys

import bmesh
import bpy
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from scipy.spatial import cKDTree

sys.stdout.reconfigure(line_buffering=True)
ARGS = sys.argv[sys.argv.index("--") + 1:]
OUT_BLEND, ART = os.path.abspath(ARGS[0]), os.path.abspath(ARGS[1])
CHECK = os.environ.get("HEAD_CHECK")
TEXDIR = os.path.join(ART, "head_tex")
os.makedirs(TEXDIR, exist_ok=True)

from bl_ext.user_default.mpfb.services.humanservice import HumanService  # noqa: E402

DATA = os.path.join(bpy.utils.user_resource("EXTENSIONS"), ".user", "user_default", "mpfb", "data")

# MakeHuman's woman: young, slim, ideal proportions; her face is fitted to
# the heroine's after.
MACROS = {"gender": 0.0, "age": 0.5, "muscle": 0.75, "weight": 0.5, "proportions": 1.0, "height": 0.5, "cupsize": 0.5,
          "firmness": 0.5, "race": {"african": 0.0, "asian": 0.0, "caucasian": 1.0}}
# Her parts, MakeHuman's own (all CC0): kind, asset.
# (Her brows are made for heroine_face.py to paint over, and are in her
# face's paint once it has: then not written for the game.)
PARTS = [("eyes", "high-poly"), ("eyebrows", "eyebrow010"), ("eyelashes", "eyelashes03"), ("teeth", "teeth_base"),
         ("tongue", "tongue01")]
EYES = "green"
SKIN = ("skins", "toigo_light_skin_female_ginger")
# (Her hairstyles are tools/assets/heroine_hair.py's, made on this head.)

# Her face: MakeHuman's woman shaped by its targets (each with its weight;
# "X-" is both sides). Every slider moves her from here.
FACE = {"head-age-decr": 0.35, "head-fat-decr": 0.2, "X-eye-scale-incr": 0.35, "X-eye-corner2-up": 0.35, "eyebrows-angle-up": 0.3,
        "nose-scale-horiz-decr": 0.65, "nose-point-up": 0.3, "nose-point-width-decr": 0.3, "nose-hump-decr": 0.45, "nose-scale-vert-decr": 0.3,
        "mouth-upperlip-volume-incr": 0.75, "mouth-lowerlip-volume-incr": 0.8, "mouth-cupidsbow-incr": 0.5, "mouth-angles-up": 0.2,
        "X-cheek-bones-incr": 0.15, "X-cheek-volume-incr": 0.5, "chin-bones-incr": 0.1, "chin-width-incr": 0.3, "chin-height-decr": 0.25,
        "chin-triangle": 0.2, "chin-prominent-incr": 0.15}
# Her sliders, for the game to shape her face with: each a shape key one
# way (name+) and the other (name-), from MakeHuman's targets.
SLIDERS = {
    "eyes_size": ("X-eye-scale-incr", "X-eye-scale-decr"), "eyes_spacing": ("X-eye-trans-out", "X-eye-trans-in"),
    "eyes_height": ("X-eye-trans-up", "X-eye-trans-down"), "eyes_tilt": ("X-eye-corner2-up", "X-eye-corner2-down"),
    "eyes_open": ("X-eye-height2-incr", "X-eye-height2-decr"), "brows_height": ("eyebrows-trans-up", "eyebrows-trans-down"),
    "brows_arch": ("eyebrows-angle-up", "eyebrows-angle-down"), "nose_width": ("nose-scale-horiz-incr", "nose-scale-horiz-decr"),
    "nose_length": ("nose-scale-vert-incr", "nose-scale-vert-decr"), "nose_tip": ("nose-point-up", "nose-point-down"),
    "nose_bridge": ("nose-hump-incr", "nose-hump-decr"), "nostrils": ("nose-flaring-incr", "nose-flaring-decr"),
    "lips_upper": ("mouth-upperlip-volume-incr", "mouth-upperlip-volume-decr"),
    "lips_lower": ("mouth-lowerlip-volume-incr", "mouth-lowerlip-volume-decr"),
    "mouth_width": ("mouth-scale-horiz-incr", "mouth-scale-horiz-decr"), "mouth_corners": ("mouth-angles-up", "mouth-angles-down"),
    "cupids_bow": ("mouth-cupidsbow-incr", "mouth-cupidsbow-decr"), "cheekbones": ("X-cheek-bones-incr", "X-cheek-bones-decr"),
    "cheeks": ("X-cheek-volume-incr", "X-cheek-volume-decr"), "jaw": ("chin-bones-incr", "chin-bones-decr"),
    "chin_width": ("chin-width-incr", "chin-width-decr"), "chin_length": ("chin-height-incr", "chin-height-decr"),
    "chin_forward": ("chin-prominent-incr", "chin-prominent-decr"), "ears_size": ("X-ear-scale-incr", "X-ear-scale-decr"),
    "ears_pointed": ("X-ear-shape-pointed", None),
}
# Her expressions (MakeHuman's expression units), for blinking, speaking and
# her scenes: each a shape key from nothing to full.
EXPRESSIONS = {
    "blink_l": ["eye-left-closure"], "blink_r": ["eye-right-closure"], "eyes_wide": ["eye-left-opened-up", "eye-right-opened-up"],
    "squint": ["eye-left-slit", "eye-right-slit"], "brows_up": ["eyebrows-left-up", "eyebrows-right-up"],
    "brows_sad": ["eyebrows-left-inner-up", "eyebrows-right-inner-up"], "brows_angry": ["eyebrows-left-down", "eyebrows-right-down"],
    "smile": ["mouth-corner-puller"], "mouth_open": ["mouth-open"], "pucker": ["mouth-pursing"], "snarl": ["mouth-upward-retraction"],
    "frown": ["mouth-depression"], "nose_wrinkle": ["nose-compression"],
}


def cut_z(P):
    """Height of CUT under a point: low on her chest in front, lower down her
    back, rising over the tops of her shoulders (gently, and out past where
    the tips of her hair lay), so all that the sculpt's hair lay on is above
    it and her arms are not."""
    x, y = P[:, 0], P[:, 1]
    side = np.logaddexp(0, (np.abs(x) - 0.17) / 0.015) * 0.015
    return 1.47 - 0.35 * (y + 0.10) + 2.0 * side


def g_cut(P):
    return P[:, 2] - cut_z(P)


def s_split(P):
    """Above SPLIT is her head: under her chin in front, under her skull behind."""
    return P[:, 2] - (1.625 + 0.27 * (P[:, 1] + 0.02))


def smooth01(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def bary(p, a, b, c):
    v0, v1, v2 = b - a, c - a, p - a
    d00, d01, d11 = (v0 * v0).sum(1), (v0 * v1).sum(1), (v1 * v1).sum(1)
    d20, d21 = (v2 * v0).sum(1), (v2 * v1).sum(1)
    den = d00 * d11 - d01 * d01
    den[np.abs(den) < 1e-18] = 1e-18
    v = (d11 * d20 - d01 * d21) / den
    w = (d00 * d21 - d01 * d20) / den
    return np.clip(np.stack([1 - v - w, v, w], 1), 0, 1)


def sample(img, uv):
    """Bilinear lookup in an image (rows from the bottom, as Blender has them)."""
    h, w = img.shape[:2]
    x = np.clip(uv[:, 0] * w - 0.5, 0, w - 1.001)
    y = np.clip(uv[:, 1] * h - 0.5, 0, h - 1.001)
    x0, y0 = x.astype(int), y.astype(int)
    fx, fy = (x - x0)[:, None], (y - y0)[:, None]
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy)
            + img[y0 + 1, x0] * (1 - fx) * fy + img[y0 + 1, x0 + 1] * fx * fy)


def load_png(path):
    im = bpy.data.images.load(path, check_existing=True)
    w, h = im.size
    return np.array(im.pixels[:], np.float32).reshape(h, w, 4)


def vertex_normals(V, faces):
    n = np.zeros_like(V)
    for f in faces:
        f = list(f)
        for i in range(1, len(f) - 1):
            a, b, c = V[f[0]], V[f[i]], V[f[i + 1]]
            fn = np.cross(b - a, c - a)
            for k in (f[0], f[i], f[i + 1]):
                n[k] += fn
    return n / (np.linalg.norm(n, axis=1)[:, None] + 1e-12)


# ------------------------------------------------------------------ her --
her = bpy.data.objects["Heroine"]
arm = bpy.data.objects["Armature"]
BONES = [b.name for b in arm.data.bones]
BI = {n: i for i, n in enumerate(BONES)}
hme = her.data
assert her.matrix_world == arm.matrix_world and her.matrix_world.is_identity
IMG = next(n.image for n in hme.materials[0].node_tree.nodes if n.type == "TEX_IMAGE" and n.image)
TEX = np.array(IMG.pixels[:], np.float32).reshape(IMG.size[1], IMG.size[0], 4)
HV = np.array([v.co[:] for v in hme.vertices])
hme.calc_loop_triangles()
HT = np.array([t.vertices[:] for t in hme.loop_triangles])
HTL = np.array([t.loops[:] for t in hme.loop_triangles])
HTP = np.array([t.polygon_index for t in hme.loop_triangles])
HUV = np.array([d.uv[:] for d in hme.uv_layers.active.data])
HW = np.zeros((len(HV), len(BONES)))
gname = {g.index: g.name for g in her.vertex_groups}
for v in hme.vertices:
    for g in v.groups:
        if gname.get(g.group) in BI:
            HW[v.index, BI[gname[g.group]]] = g.weight
# Her hair, by its paint: red, above her breasts (below, red is her nipples).
_puv = np.zeros((len(hme.polygons), 2))
np.add.at(_puv, HTP, HUV[HTL].mean(1))
_puv /= np.bincount(HTP, minlength=len(hme.polygons))[:, None]
_pc = sample(TEX, _puv)[:, :3]
_pz = np.zeros(len(hme.polygons))
np.maximum.at(_pz, HTP, HV[HT][:, :, 2].max(1))
_py = np.zeros(len(hme.polygons))
np.minimum.at(_py, HTP, HV[HT][:, :, 1].min(1))
_pcen = np.zeros((len(hme.polygons), 3))
np.add.at(_pcen, HTP, HV[HT].mean(1))
_pcen /= np.bincount(HTP, minlength=len(hme.polygons))[:, None]
# Her areolae, by their own muted pink, on the fronts of her breasts:
# nothing within 2.5 cm of their middles is taken for hair.
AREOLA = []
for sd in (1, -1):
    m = (_pcen[:, 0] * sd > 0.06) & (_pcen[:, 1] < -0.14) & (_pcen[:, 2] > 1.38) & (_pcen[:, 2] < 1.46) & (
        _pc[:, 0] > 1.4 * _pc[:, 1]) & (_pc[:, 0] < 2.2 * _pc[:, 1])
    AREOLA.append(_pcen[m].mean(0))
    print("AREOLA", "lr"[sd < 0], np.round(AREOLA[-1], 3), m.sum(), "faces")
_off_areola = np.min([np.linalg.norm(_pcen - a, axis=1) for a in AREOLA], 0) > 0.025
# Her hair: red above her breasts, and its deep red (the tips of it lay
# on her) anywhere on her upper body.
RED = (((_pc[:, 0] > 0.25) & (_pc[:, 0] > _pc[:, 1] * 1.7) & (_pc[:, 0] > _pc[:, 2] * 1.7) & (_pz > 1.40))
       | ((_pc[:, 0] > _pc[:, 1] * 2.4) & (_pc[:, 0] > _pc[:, 2] * 2.4) & (_pz > 1.33))) & _off_areola
# Her skin as it is: what everything new is fitted to, weighted from and
# painted from. Not her hair, and not her face (the new one is MakeHuman's).
_tc = HV[HT].mean(1)
SKIN_T = np.where(~RED[HTP] & (s_split(_tc) < -0.004))[0]
SKIN_BVH = BVHTree.FromPolygons([tuple(p) for p in HV], HT[SKIN_T].tolist())
# What the graft is fitted to is surer still: none of it near her hair (the
# lighter streaks of it are not red, and stand off her skin: one such patch,
# taken for skin, pulled her neck into a ridge).
# (3 cm on her neck and upper back, where her hair lay thick; on her
# shoulders, where only its tips lay, 1.2 cm, or the graft there fits
# nothing of hers and meets her skin at an angle.)
_near_hair = cKDTree(_tc[RED[HTP]]).query(_tc[SKIN_T])[0] < np.where(_tc[SKIN_T, 2] > 1.52, 0.03, 0.012)
FIT_T = SKIN_T[~_near_hair]
FIT_BVH = BVHTree.FromPolygons([tuple(p) for p in HV], HT[FIT_T].tolist())
# (Her build is fitted to more of her, clear of her hair by 1.2 cm: a
# handful of targets cannot be pulled into a ridge by a stray patch.)
NEAR_T = SKIN_T[cKDTree(_tc[RED[HTP]]).query(_tc[SKIN_T])[0] > 0.012]
NEAR_BVH = BVHTree.FromPolygons([tuple(p) for p in HV], HT[NEAR_T].tolist())
print("HER", len(HV), "points,", int(RED.sum()), "faces of hair")


def on_skin(pts, maxd=0.3, sure=False, near=False):
    """For each point the nearest of her skin (with `sure`, of the skin
    well clear of her hair): where, its normal, its distance, and the
    weights and paint there."""
    n = len(pts)
    loc, nor, dist = np.zeros((n, 3)), np.zeros((n, 3)), np.full(n, np.inf)
    tri = np.zeros(n, int)
    bvh, tris = (FIT_BVH, FIT_T) if sure else ((NEAR_BVH, NEAR_T) if near else (SKIN_BVH, SKIN_T))
    for i, p in enumerate(pts):
        r = bvh.find_nearest(Vector(p), maxd)
        if r[0] is not None:
            loc[i], nor[i], tri[i], dist[i] = r[0][:], r[1][:], r[2], r[3]
    t = tris[tri]
    b = bary(loc, HV[HT[t, 0]], HV[HT[t, 1]], HV[HT[t, 2]])
    w = (HW[HT[t]] * b[:, :, None]).sum(1)
    uv = (HUV[HTL[t]] * b[:, :, None]).sum(1)
    return loc, nor, dist, w, uv


def her_face_landmarks():
    """Her nose tip and the bottom of her chin, from her face's profile."""
    m = ~RED[HTP] & (_tc[:, 2] > 1.55) & (_tc[:, 2] < 1.77) & (_tc[:, 1] < 0.0)
    return nose_chin(_tc[m])


def nose_chin(pts):
    mid = pts[np.abs(pts[:, 0]) < 0.012]
    nose = mid[np.argmin(mid[:, 1])]
    prof = []
    for z in np.arange(nose[2] - 0.03, nose[2] - 0.15, -0.004):
        m = np.abs(mid[:, 2] - z) < 0.004
        if m.any():
            prof.append((z, mid[m, 1].min()))
    for (z0, y0), (z1, y1) in zip(prof, prof[1:]):
        if y1 - y0 > 0.02:
            return nose, np.array([0.0, y0, z0])
    raise SystemExit("no chin found")


# ------------------------------------------------------------ MakeHuman --
hm = HumanService.create_human(mask_helpers=True, detailed_helpers=True, extra_vertex_groups=True, feet_on_ground=True,
                               scale=0.1, macro_detail_dict=MACROS)
from bl_ext.user_default.mpfb.services.targetservice import TargetService  # noqa: E402
from bl_ext.user_default.mpfb.entities.clothes.mhclo import Mhclo  # noqa: E402

_TDIR = os.path.join(bpy.utils.user_resource("EXTENSIONS"), "user_default", "mpfb", "data", "targets")
TARGET = {}
for _root, _, _files in os.walk(_TDIR):
    for _f in _files:
        if _f.endswith(".target.gz") and "expression" not in _root:
            TARGET.setdefault(_f[:-10], os.path.join(_root, _f))
for _f in os.listdir(os.path.join(_TDIR, "expression", "units", "caucasian")):
    TARGET["x:" + _f[:-10]] = os.path.join(_TDIR, "expression", "units", "caucasian", _f)


def sides(names):
    """Target names, "X-" ones as both sides."""
    out = []
    for n in names:
        out += [n.replace("X-", "l-", 1), n.replace("X-", "r-", 1)] if n.startswith("X-") else [n]
    return out


for _t, _v in FACE.items():
    for _n in sides([_t]):
        TargetService.load_target(hm, TARGET[_n], weight=_v)
# Every slider's and expression's targets too, at nothing (so they change
# nothing yet), for what each does to her to be read off later.
SHAPES = {}
for _k, (_up, _down) in SLIDERS.items():
    SHAPES[_k + "+"] = sides([_up])
    if _down:
        SHAPES[_k + "-"] = sides([_down])
for _k, _ts in EXPRESSIONS.items():
    SHAPES[_k] = ["x:" + t for t in _ts]
# MakeHuman's woman is longer and slimmer of neck and lower of shoulder than
# she is, and where her hair hid her skin there is nothing of hers to fit
# to: her build set by these (her face is placed on hers, so a shorter neck
# lifts the muscles of her shoulders toward her head).
BUILD = {"measure-neck-height-decr": 0.9, "measure-neck-circ-incr": 0.5, "neck-back-scale-depth-incr": 0.3}
for _t, _v in BUILD.items():
    TargetService.load_target(hm, TARGET[_t], weight=_v)
SK = {}
for _t in sorted({t for ts in SHAPES.values() for t in ts}):
    SK[_t] = TargetService.load_target(hm, TARGET[_t], weight=0.0, name="sk_" + _t.replace(":", "_")).name
proxies = {}
for kind, name in PARTS:
    proxies[name] = HumanService.add_mhclo_asset(os.path.join(DATA, kind, name, name + ".mhclo"), hm, asset_type=kind,
                                                 subdiv_levels=0, material_type="NONE", set_up_rigging=False,
                                                 interpolate_weights=False, import_subrig=False, import_weights=False)
for mo in hm.modifiers:
    mo.show_viewport = False
bpy.context.view_layer.update()


def grab(o):
    """An object as it stands (shape keys and all), in the world: points,
    faces, and each face's corners' UVs."""
    e = o.evaluated_get(bpy.context.evaluated_depsgraph_get())
    m = e.to_mesh()
    mw = np.array(o.matrix_world)
    V = np.array([v.co[:] for v in m.vertices]) @ mw[:3, :3].T + mw[:3, 3]
    F = [list(p.vertices) for p in m.polygons]
    uvd = m.uv_layers.active.data
    U = [np.array([uvd[li].uv[:] for li in p.loop_indices]) for p in m.polygons]
    e.to_mesh_clear()
    return V, F, U


MV, MF, MU = grab(hm)
_body = hm.vertex_groups["body"].index
_inbody = np.array([any(g.group == _body for g in v.groups) for v in hm.data.vertices])
keep = [i for i, f in enumerate(MF) if _inbody[f].all()]
MF = [MF[i] for i in keep]
MU = [MU[i] for i in keep]
print("MAKEHUMAN", len(MV), "points,", len(MF), "faces of skin")

# ---- her face's place: scale from nose to chin, then turned and moved
# till its surface lies on hers (an ICP at that scale).
_top = MV[_inbody, 2].max()
mn, mc = nose_chin(MV[_inbody & (MV[:, 2] > _top - 0.28)])
hn, hc = her_face_landmarks()
S = np.linalg.norm(hn - hc) / np.linalg.norm(mn - mc)
R = np.eye(3)
T = hn - S * mn
_hf = np.where(~RED[HTP] & (_tc[:, 2] > hc[2] - 0.003) & (_tc[:, 2] < 1.80) & (_tc[:, 1] < 0) & (np.abs(_tc[:, 0]) < 0.075))[0]
_fbvh = BVHTree.FromPolygons([tuple(p) for p in HV], HT[_hf].tolist())
_cand = MV[np.where(_inbody & (MV[:, 2] > mc[2] - 0.003) & (MV[:, 2] < mn[2] + 0.07) & (MV[:, 1] < mn[1] + 0.06)
                    & (np.abs(MV[:, 0]) < 0.06))[0]]
for _ in range(30):
    p = (S * (R @ _cand.T)).T + T
    q, k = [], []
    for i, x in enumerate(p):
        r = _fbvh.find_nearest(Vector(x), 0.02)
        if r[0] is not None:
            q.append(r[0][:])
            k.append(i)
    q, src = np.array(q), _cand[k]
    ms, mq = src.mean(0), q.mean(0)
    U_, D_, Vt = np.linalg.svd((q - mq).T @ (S * (src - ms)) / len(q))
    sg = np.diag([1, 1, np.sign(np.linalg.det(U_ @ Vt))])
    R = U_ @ sg @ Vt
    T = mq - S * R @ ms
res = np.linalg.norm((S * (R @ src.T)).T + T - q, axis=1)
print("FACE scale %.3f, turned %.1f deg, %.1f mm from hers" % (S, math.degrees(math.acos(min(1, (np.trace(R) - 1) / 2))),
                                                            1000 * np.sqrt((res ** 2).mean())))


def place(V):
    return (S * (R @ V.T)).T + T


MV = place(MV)





# ---- the region made anew (her head, and her body above CUT), each face
# quartered (linearly, so the surface keeps its shape and the eyes, brows
# and lashes, fitted to it, still sit right) for the detail of her skin.
def subdivide(V, F, U):
    used = sorted({i for f in F for i in f})
    idx = {o: n for n, o in enumerate(used)}
    rows, cols, vals = list(range(len(used))), used[:], [1.0] * len(used)
    emid = {}
    nF, nU = [], []
    n = len(used)
    for f, uv in zip(F, U):
        k = len(f)
        c = n
        n += 1
        for i in f:
            rows.append(c), cols.append(i), vals.append(1.0 / k)
        mids = []
        for i in range(k):
            a, b = f[i], f[(i + 1) % k]
            key = (min(a, b), max(a, b))
            if key not in emid:
                emid[key] = n
                rows += [n, n]
                cols += [a, b]
                vals += [0.5, 0.5]
                n += 1
            mids.append(emid[key])
        cuv = uv.mean(0)
        for i in range(k):
            nF.append([idx[f[i]], mids[i], c, mids[i - 1]])
            nU.append(np.array([uv[i], (uv[i] + uv[(i + 1) % k]) / 2, cuv, (uv[i - 1] + uv[i]) / 2]))
    Sub = sp.csr_matrix((vals, (rows, cols)), shape=(n, len(V)))
    return Sub, nF, nU


_fc = np.array([MV[f].mean(0) for f in MF])
_region = [i for i, f in enumerate(MF) if (g_cut(MV[f]) > -0.10).any()]
SUB, RF, RU = subdivide(MV, [MF[i] for i in _region], [MU[i] for i in _region])
RV0 = SUB @ MV
print("REGION", len(RV0), "points,", len(RF), "faces")


# ---- fitted to her skin: as near hers as it can be where she has skin,
# its own shape kept (its Laplacian) where she has none; her head as
# MakeHuman's, untouched.
def fit(V0, F):
    n = len(V0)
    e = np.array([(f[i], f[(i + 1) % len(f)]) for f in F for i in range(len(f))])
    A = sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)).tocsr()
    A = ((A + A.T) > 0).astype(float)
    deg = np.asarray(A.sum(1)).ravel()
    L = sp.identity(n) - sp.diags(1 / np.maximum(deg, 1)) @ A
    LtL = (L.T @ L).tocsc()
    delta0 = L @ V0
    delta = delta0
    ei, ej = sp.triu(A).nonzero()

    def turned(V):
        """Each point's own turning (the rotation that best takes the edges
        round it as they were to as they are), and its shape turned with
        it: so a part of her swung as a whole (MakeHuman's arms hang
        otherwise than hers) costs nothing, and only bending it does."""
        e0, e1 = V0[ej] - V0[ei], V[ej] - V[ei]
        C = np.einsum("ni,nj->nij", e0, e1)
        Cv = np.zeros((n, 3, 3))
        np.add.at(Cv, ei, C)
        np.add.at(Cv, ej, C)
        U_, _, Vt_ = np.linalg.svd(Cv)
        Rv = np.einsum("nji,nkj->nik", Vt_, U_)
        bad = np.linalg.det(Rv) < 0
        Vt_[bad, 2] *= -1
        Rv[bad] = np.einsum("nji,nkj->nik", Vt_[bad], U_[bad])
        return np.einsum("nij,nj->ni", Rv, delta0)
    s = s_split(V0)
    # Her face held as MakeHuman's; her neck free to follow hers, her skin's
    # pull easing to nothing over the 5 cm below SPLIT (else, her neck being
    # thicker behind than MakeHuman's, the surface stepped out there and folded).
    fixed = np.where(s > 0.05, 1e3, 0.0)
    data = np.where((s < -0.004) & (g_cut(V0) > -0.10))[0]
    pull = smooth01((-s[data] - 0.005) / 0.05)
    V = V0.copy()
    for it_, (lam, dmax) in enumerate(((20, 0.06), (8, 0.05), (4, 0.035), (2, 0.025), (1, 0.02), (0.5, 0.015), (0.3, 0.012), (0.3, 0.01),
                                       (0.3, 0.01), (0.3, 0.01))):
        nor = vertex_normals(V, F)
        loc, hn_, dist, _, _ = on_skin(V[data], dmax, sure=True)
        d = V[data] - loc
        along = (d * hn_).sum(1)
        side = np.linalg.norm(d - along[:, None] * hn_, axis=1)
        ok = np.isfinite(dist) & ((nor[data] * hn_).sum(1) > 0.7) & (side < 0.3 * np.abs(along) + 0.002)
        w = np.zeros(n)
        w[data[ok]] = pull[ok]
        tgt = np.zeros((n, 3))
        tgt[data[ok]] = loc[ok]
        M = (sp.diags(w + fixed) + lam * LtL).tocsc()
        solve = spl.factorized(M)
        rhs = w[:, None] * tgt + fixed[:, None] * V0 + lam * (L.T @ delta)
        delta = turned(V) if it_ > 0 else delta0
        V = np.stack([solve(rhs[:, k]) for k in range(3)], 1)
        r = np.linalg.norm(V[data[ok]] - loc[ok], axis=1)
        print("  fit: %d of %d points on her skin, %.1f mm off (stiffness %g)" % (ok.sum(), len(data), 1000 * r.mean(), lam))
    return V


RV = fit(RV0, RF)


def face_normals(V, F):
    n = np.array([np.cross(V[f[1]] - V[f[0]], V[f[-1]] - V[f[0]]) for f in F])
    return n / (np.linalg.norm(n, axis=1)[:, None] + 1e-12)


# Where the fit folded the surface over (pulled on by what was left of her
# hair), its move eased into its neighbours' till no face of it is turned.
_e = np.array([(f[i], f[(i + 1) % len(f)]) for f in RF for i in range(len(f))])
_A = sp.coo_matrix((np.ones(len(_e)), (_e[:, 0], _e[:, 1])), shape=(len(RV), len(RV))).tocsr()
_A = ((_A + _A.T) > 0).astype(float)
_A = sp.diags(1 / np.maximum(np.asarray(_A.sum(1)).ravel(), 1)) @ _A
_fixed = s_split(RV0) > 0.05
_fv = sp.coo_matrix((np.ones(sum(len(f) for f in RF)), ([i for i, f in enumerate(RF) for _ in f], [v for f in RF for v in f])),
                    shape=(len(RF), len(RV))).tocsr()
for _r in range(60):
    # (turned: facing against the faces round it)
    fn_ = face_normals(RV, RF)
    vn_ = _fv.T @ fn_
    around_ = _fv @ vn_
    around_ /= np.linalg.norm(around_, axis=1)[:, None] + 1e-12
    turned = np.where((fn_ * around_).sum(1) < 0.2)[0]
    if not len(turned):
        break
    near = np.zeros(len(RV), bool)
    near[[i for f in turned for i in RF[f]]] = True
    for _ in range(2):
        near |= (_A @ near.astype(float)) > 0
    near &= ~_fixed
    D = RV - RV0
    D[near] = (_A @ D)[near]
    RV = RV0 + D
print("FOLDS eased in %d rounds (%d turned faces left)" % (_r, len(turned)))
# Near CUT the graft lies on her skin exactly (some of it was fitted to
# none, near her hair), so the two meet flush: wholly at CUT, less and
# less to 3 cm above it.
# (Near it as the crow flies: where CUT climbs over her shoulders its height
# above a point says little of how near the point is.)
_seam = cKDTree(HV[np.abs(g_cut(HV)) < 0.003])
_sd = _seam.query(RV)[0] * np.sign(g_cut(RV))
_near = np.where((s_split(RV) < 0) & (_sd > -0.01) & (_sd < 0.03))[0]
loc, hn_, dist, _, _ = on_skin(RV[_near], 0.02)
_nn = vertex_normals(RV, RF)[_near]
ok = np.isfinite(dist) & ((_nn * hn_).sum(1) > 0.6)
w = (1 - smooth01(_sd[_near] / 0.03))[:, None] * ok[:, None]
RV[_near] += (loc - RV[_near]) * w
print("FLUSH: %d graft points near CUT laid on her skin (%.1f mm at most)" % (ok.sum(), 1000 * (dist[ok] * w[ok, 0]).max()))
# Laid on her scan's faint facets the graft creased: smoothed there (its own
# even mesh only, hers untouched), its lowest row and the rest held.
_e = np.array([(f[i], f[(i + 1) % len(f)]) for f in RF for i in range(len(f))])
_A = sp.coo_matrix((np.ones(len(_e)), (_e[:, 0], _e[:, 1])), shape=(len(RV), len(RV))).tocsr()
_A = ((_A + _A.T) > 0).astype(float)
_A = sp.diags(1 / np.maximum(np.asarray(_A.sum(1)).ravel(), 1)) @ _A
_g = g_cut(RV)
_sm = ((s_split(RV) < -0.01) & (_g > 0.01) & (_g < 0.045)).astype(float)[:, None] * 0.5
for _ in range(6):
    RV = RV + (_A @ RV - RV) * _sm
MOVE = RV - RV0
_rc = np.array([RV[f].mean(0) for f in RF])
HEAD_F = [i for i in range(len(RF)) if s_split(_rc[i:i + 1])[0] > 0]
# (Its lowest row at least 6 mm above CUT, so the strip sewing it to her
# is of faces with some breadth.)
GRAFT_F = [i for i in range(len(RF)) if s_split(_rc[i:i + 1])[0] <= 0 and (g_cut(RV[RF[i]]) > 0.006).all()]
print("HEAD", len(HEAD_F), "faces; GRAFT", len(GRAFT_F), "faces")

if os.environ.get("HEAD_STOP") == "fit":
    if os.environ.get("HEAD_AT"):
        q = np.array([float(c) for c in os.environ["HEAD_AT"].split(",")])
        near = np.linalg.norm(RV - q, axis=1) < 0.03
        mv = np.linalg.norm(MOVE[near], axis=1)
        print("AT", q, "%d points: moved by the fit mean %.1f mm, most %.1f mm" % (near.sum(), mv.mean() * 1000, mv.max() * 1000))
        loc, hn_, dist, _, _ = on_skin(RV0[near], 0.06, sure=True)
        print("   her sure skin from MakeHuman's points there: mean %.1f mm" % (np.nanmean(np.where(np.isfinite(dist), dist, np.nan)) * 1000))
    raise SystemExit


def loops_of(edges):
    """Closed loops of boundary edges (pairs of keys), each in order."""
    adj = {}
    for a, b in edges:
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    seen, out = set(), []
    for s0 in adj:
        if s0 in seen:
            continue
        loop, prev, cur = [s0], None, s0
        seen.add(s0)
        while True:
            nxt = [x for x in adj[cur] if x != prev and x not in seen]
            if not nxt:
                break
            prev, cur = cur, nxt[0]
            seen.add(cur)
            loop.append(cur)
        out.append(loop)
    return out


def around(P, loop):
    """A loop turned to run one way round her neck (anticlockwise seen from
    above), from its point most to her front."""
    q = P[loop]
    a = np.arctan2(q[:, 0], -(q[:, 1] - 0.03))
    area = np.sum(q[:, 0] * np.roll(q[:, 1], -1) - np.roll(q[:, 0], -1) * q[:, 1])
    if area < 0:
        loop = loop[::-1]
        a = a[::-1]
    k = int(np.argmin(np.abs(a)))
    return loop[k:] + loop[:k]


# ------------------------------------------------------------ her body --
bm = bmesh.new()
bm.from_mesh(hme)
bm.faces.ensure_lookup_table()
# What is hers is marked (her own normals kept on her corners, her hair on
# her faces), as cutting renumbers everything.
NL = [bm.loops.layers.float.new(f"n{k}") for k in range(3)]
RL = bm.faces.layers.int.new("hair_paint")
NEW = bm.faces.layers.int.new("new")
# The graft's points marked (heroine_outfits.py keeps its search for her
# nipples off it). Every layer is made here, before any point is held:
# adding one moves them all.
GL = bm.verts.layers.int.new("graft")
DL = bm.verts.layers.deform.verify()
_cn = np.array([n.vector[:] for n in hme.corner_normals])
for fi, f in enumerate(bm.faces):
    f[RL] = int(RED[fi])
    for j, lp in enumerate(f.loops):
        for k in range(3):
            lp[NL[k]] = _cn[hme.polygons[fi].loop_start + j, k]
# Her points split along the paint's seams, joined (only up here, where
# she is cut and sewn).
bmesh.ops.remove_doubles(bm, verts=[v for v in bm.verts if v.co.z > 1.2], dist=1e-5)
# Cut along CUT: the field made her height for a moment, the plane cut at
# nought, and her points put back (the new ones where the field is nought).
OX = [bm.verts.layers.float.new(k) for k in ("ox", "oy", "oz")]
for v in bm.verts:
    g = float(g_cut(np.array([v.co[:]]))[0])
    # (A point within 2 mm of CUT moved to 2 mm off it, down or up, so the
    # cut leaves no sliver of a face beside it nor a huddle of new points.)
    if -0.002 < g < 0.002:
        d = (-0.002 if g < 0 else 0.002) - g
        v.co.z += d
        g += d
    for k in range(3):
        v[OX[k]] = v.co[k]
    v.co.z = g
bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-7, plane_co=(0, 0, 0), plane_no=(0, 0, 1),
                       clear_outer=True)
for v in bm.verts:
    v.co = (v[OX[0]], v[OX[1]], v[OX[2]])
# Loose scraps of hair below CUT. (Hair lying on her skin there is her
# skin, painted red: repainted, further on, not cut out.)
bm.faces.ensure_lookup_table()
comp = {}
for f in bm.faces:
    if f in comp:
        continue
    c = len(set(comp.values()))
    stack = [f]
    comp[f] = c
    while stack:
        x = stack.pop()
        for e in x.edges:
            for y in e.link_faces:
                if y not in comp:
                    comp[y] = c
                    stack.append(y)
sizes = np.bincount(list(comp.values()))
main = int(np.argmax(sizes))
# (Only up here: lower down her paint's seams still part her into islands.)
low = {c for f, c in comp.items() if f.calc_center_median().z < 1.25}
scraps = [f for f, c in comp.items() if c != main and c not in low]
bmesh.ops.delete(bm, geom=scraps, context="FACES")
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
print("BODY cut: %d scraps of hair gone (%d faces)" % (len({comp[f] for f in scraps}), len(scraps)))
# Below CUT, where the tips of her hair lay on her shoulders, the sculpt
# left her skin rough: smoothed within 1.5 cm of them, all round held.
_tips = cKDTree(_tc[RED[HTP]])
rough = [v for v in bm.verts if v.link_faces and _tips.query(v.co[:])[0] < 0.015 and float(g_cut(np.array([v.co[:]]))[0]) < -0.004
         and not v.is_boundary and min(np.linalg.norm(np.array(v.co[:]) - a) for a in AREOLA) > 0.03]
# (Each point moved only along her surface's normal there, toward its
# neighbours' middle: drawn sideways too, her uneven faces folded over.)
for _ in range(20):
    bm.normal_update()
    moved = {}
    for v in rough:
        d = sum((e.other_vert(v).co for e in v.link_edges), Vector()) / len(v.link_edges) - v.co
        moved[v] = v.co + v.normal * (d.dot(v.normal) * 0.5)
    for v, q in moved.items():
        v.co = q
print("SMOOTHED %d points of her skin where her hair's tips lay" % len(rough))
# Her open edge along CUT.
BP = np.array([v.co[:] for v in bm.verts])
bl = loops_of([(e.verts[0].index, e.verts[1].index) for e in bm.edges if e.is_boundary])
cut_loop = max(bl, key=lambda L: (np.abs(g_cut(BP[L])) < 1e-4).sum())
for L in bl:
    if L is not cut_loop and BP[L, 2].min() > 1.25:
        print("  (an open edge of %d points at %s)" % (len(L), np.round(BP[L].mean(0), 3)))
bm.verts.ensure_lookup_table()
cut_loop = around(BP, cut_loop)
A = [bm.verts[i] for i in cut_loop]
bm.normal_update()
_out = {v: np.array(v.normal[:]) for v in A}
print("CUT", len(cut_loop), "points round her, %.3f to %.3f m high" % (BP[cut_loop, 2].min(), BP[cut_loop, 2].max()))

# ---- the graft: its points and faces into her body, sewn to her along
# CUT by a strip zipped between her edge and its own.
gv = sorted({i for fi in GRAFT_F for i in RF[fi]})
head_v = {i for fi in HEAD_F for i in RF[fi]}
ecount = {}
for fi in GRAFT_F:
    f = RF[fi]
    for i in range(len(f)):
        k = (min(f[i], f[(i + 1) % len(f)]), max(f[i], f[(i + 1) % len(f)]))
        ecount[k] = ecount.get(k, 0) + 1
lower = [k for k, c in ecount.items() if c == 1 and not (k[0] in head_v and k[1] in head_v)]
gl = loops_of(lower)
print("GRAFT edge loops below:", [len(L) for L in gl])
# (One, all the way round her: CUT crossing her arms would part it.)
assert len(gl) == 1, "CUT parts the graft's edge in %d: it must pass over her arms" % len(gl)
graft_loop = around(RV, max(gl, key=len))
# Every point made anew takes her weights from the skin nearest it, easing
# to her head's alone over 3 cm above SPLIT (the same for the graft and her
# head, so the points they share move as one).
_, _, _, RW, _ = on_skin(RV)
RW /= RW.sum(1, keepdims=True) + 1e-12
_t = smooth01(s_split(RV) / 0.03)[:, None]
RW = RW * (1 - _t)
RW[:, BI["Head"]] += _t[:, 0]
gmap = {}
for i in gv:
    v = bm.verts.new(RV[i])
    v[GL] = 1
    for b in np.nonzero(RW[i] > 1e-3)[0]:
        v[DL][int(b)] = float(RW[i, b])
    gmap[i] = v
for fi in GRAFT_F:
    f = bm.faces.new([gmap[i] for i in RF[fi]])
    f.smooth = True
    f.material_index = 1
    f[NEW] = 1
# The strip: the two edges zipped together the shortest way (of all the
# ways to join them in order, the one whose crossings are shortest in sum,
# by dynamic programming), from the graft's point nearest her edge's start.
B = [gmap[i] for i in graft_loop]
pa, pb = np.array([v.co[:] for v in A]), np.array([v.co[:] for v in B])
n, m = len(A), len(B)
j0 = int(np.argmin(np.linalg.norm(pb - pa[0], axis=1)))
B, pb = B[j0:] + B[:j0], np.roll(pb, -j0, axis=0)
qa, qb = np.r_[pa, pa[:1]], np.r_[pb, pb[:1]]          # each closed: back to its start
dist = np.linalg.norm(qa[:, None] - qb[None], axis=2)
cost = np.full((n + 1, m + 1), np.inf)
step = np.zeros((n + 1, m + 1), int)
cost[0, 0] = 0
for i in range(n + 1):
    for j in range(m + 1):
        if i and cost[i - 1, j] + dist[i, j] < cost[i, j]:
            cost[i, j], step[i, j] = cost[i - 1, j] + dist[i, j], 1
        if j and cost[i, j - 1] + dist[i, j] < cost[i, j]:
            cost[i, j], step[i, j] = cost[i, j - 1] + dist[i, j], 2
strip = []
i, j = n, m
while i or j:
    if step[i, j] == 1:
        strip.append((A[(i - 1) % n], A[i % n], B[j % m]))
        i -= 1
    else:
        strip.append((A[i % n], B[j % m], B[(j - 1) % m]))
        j -= 1
strip.reverse()
# The zipped faces all turn the same way; all turned, if need be, to run
# along her edge against her face beside it (so they face out as hers do:
# judged face by face, thin ones came out backwards, and showed her inside).
_e = next(e for e in A[0].link_edges if e.other_vert(A[0]) == A[1])
_her_way = any(lp.vert == A[0] and lp.link_loop_next.vert == A[1] for lp in _e.link_faces[0].loops)
strip_f = []
for t in strip:
    f = bm.faces.new(t[::-1] if _her_way else t)
    f.smooth = True
    f.material_index = 1
    f[NEW] = 1
    strip_f.append(f)
# Any dent or bump the join left on her back and shoulders, within 5 cm
# above it and 2 cm below, eased out: each point drawn halfway to the plane
# of the skin round it (2.5 cm) while it stands more than 3 mm off it. (Not
# in front, where her collarbones are hers; not her breasts.)
bm.normal_update()
_seam_now = cKDTree(np.array([v.co[:] for v in A]))
_band = [v for v in bm.verts if v.link_faces and not v.is_boundary
         and -0.02 < _seam_now.query(v.co[:])[0] * (1 if g_cut(np.array([v.co[:]]))[0] > 0 else -1) < 0.05
         and min(np.linalg.norm(np.array(v.co[:]) - a) for a in AREOLA) > 0.05 and v.co.y > 0.0]
_eased = set()
for _ in range(30):
    _all = np.array([v.co[:] for v in bm.verts])
    _kd = cKDTree(_all)
    moved = {}
    for v in _band:
        q = _all[_kd.query_ball_point(v.co[:], 0.025)]
        if len(q) < 6:
            continue
        c = q.mean(0)
        nrm = np.linalg.svd(q - c)[2][2]
        d = float((np.array(v.co[:]) - c) @ nrm)
        if abs(d) > 0.003:
            moved[v] = v.co - Vector(nrm) * (0.5 * d)
    if not moved:
        break
    for v, q in moved.items():
        v.co = q
        _eased.add(v)
print("EVENED: %d points of the join eased flat" % len(_eased))
if os.environ.get("HEAD_AT"):
    _q = np.array([float(c) for c in os.environ["HEAD_AT"].split(",")])
    _all = np.array([v.co[:] for v in bm.verts])
    _i = int(np.argmin(np.linalg.norm(_all - _q, axis=1)))
    bm.verts.ensure_lookup_table()
    _v = bm.verts[_i]
    print("AT", np.round(_all[_i], 4), "in band:", _v in set(_band), "boundary:", _v.is_boundary, "faces:", len(_v.link_faces),
          "seam dist %.4f" % _seam_now.query(_v.co[:])[0], "g %.4f" % g_cut(np.array([_v.co[:]]))[0])
# The band either side of the join evened out: each point drawn toward the
# middle of its neighbours and laid back on the surface as it was, so the
# faces there are of even shape (thin ones bend the light, and what is cut
# from her skin) and the surface keeps its form.
bm.normal_update()
_ref = BVHTree.FromBMesh(bm)
band = [v for v in bm.verts if abs(float(g_cut(np.array([v.co[:]]))[0])) < 0.015 and not v.is_boundary]
for _ in range(12):
    moved = {}
    for v in band:
        q = v.co.lerp(sum((e.other_vert(v).co for e in v.link_edges), Vector()) / len(v.link_edges), 0.5)
        moved[v] = _ref.find_nearest(q)[0]
    for v, q in moved.items():
        v.co = q
# Slivers of faces along the join (less than 0.7 mm across) dissolved: they
# take a light of their own.
_sc_kd = cKDTree(np.array([v.co[:] for v in A]))
bmesh.ops.dissolve_degenerate(bm, dist=0.0007, edges=[e for e in bm.edges if
                              _sc_kd.query(((e.verts[0].co + e.verts[1].co) / 2)[:])[0] < 0.01])
bm.verts.ensure_lookup_table()
bm.normal_update()
print("SEWN: %d strip faces between %d of her points and %d of the graft's" % (len(strip), n, m))

# ------------------------------------------------------------- her head --
hv = sorted(head_v)
hmap = {o: n for n, o in enumerate(hv)}
HEAD_V = RV[hv]
HEAD_FACES = [[hmap[i] for i in RF[fi]] for fi in HEAD_F]
HEAD_UV = [RU[fi] for fi in HEAD_F]


def check(name, objs, views=(("front", 0, 0.0), ("side", 90, 0.0), ("back", 180, 0.0), ("q", 35, 0.1)), tgt=(0, 0.03, 1.56), dist=1.1,
          lens=60, size=(700, 800)):
    """Grey renders of the given objects (the rest hidden), for a look."""
    if not CHECK:
        return
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "STUDIO"
    sc.display.shading.color_type = "MATERIAL"
    sc.render.resolution_x, sc.render.resolution_y = size
    cam = bpy.data.objects.get("CheckCam") or bpy.data.objects.new("CheckCam", bpy.data.cameras.new("CheckCam"))
    if cam.name not in sc.collection.objects:
        sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.lens = lens
    hide = {o: o.hide_render for o in bpy.data.objects}
    for o in bpy.data.objects:
        o.hide_render = o not in objs and o.type == "MESH"
    t = Vector(tgt)
    for nm, ang, el in views:
        a = math.radians(ang)
        cam.location = t + Vector((math.sin(a) * dist, -math.cos(a) * dist, el))
        cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = os.path.join(CHECK, f"{name}_{nm}.png")
        bpy.ops.render.render(write_still=True)
    for o, h in hide.items():
        o.hide_render = h


def mesh_object(name, V, F, U=None, mats=()):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in V], [], [tuple(f) for f in F])
    if U is not None:
        uvl = me.uv_layers.new(name="UVMap")
        uvl.data.foreach_set("uv", np.concatenate(U).ravel())
    for m in mats:
        me.materials.append(m)
    me.shade_smooth()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return o


def plain(name, rgb):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1)
    return m


bm.to_mesh(hme)
bm.free()
while len(hme.materials) < 2:
    hme.materials.append(plain("graft", (0.5, 0.75, 0.5)))
head = mesh_object("HeroineHead", HEAD_V, HEAD_FACES, HEAD_UV, [plain("headcheck", (0.5, 0.6, 0.9))])
for mo in her.modifiers:
    mo.show_render = False
check("sewn", [her, head])
check("sewnback", [her, head], views=(("b", 180, 0.15), ("bl", 140, 0.2), ("fr", -30, 0.05)), tgt=(0, 0.04, 1.5), dist=0.7)
if os.environ.get("HEAD_STOP") == "sewn":
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
    raise SystemExit


# ---------------------------------------------------------------- normals --
def smooth_normals(parts):
    """Normals of the surfaces given as one, joined where their points meet
    (her paint's seams, her head on her neck), so no seam shows in the light."""
    allp = np.vstack([V for V, _ in parts])
    key = np.unique(np.round(allp / 1e-5).astype(np.int64), axis=0, return_inverse=True)[1].ravel()
    acc = np.zeros((key.max() + 1, 3))
    base = 0
    for V, F in parts:
        for f in F:
            f = list(f)
            for i in range(1, len(f) - 1):
                a, b, c = V[f[0]], V[f[i]], V[f[i + 1]]
                fn = np.cross(b - a, c - a)
                for k in (f[0], f[i], f[i + 1]):
                    acc[key[base + k]] += fn
        base += len(V)
    acc /= np.linalg.norm(acc, axis=1)[:, None] + 1e-12
    out, base = [], 0
    for V, _ in parts:
        out.append(acc[key[base:base + len(V)]])
        base += len(V)
    return out


BV = np.array([v.co[:] for v in hme.vertices])
BF = [list(p.vertices) for p in hme.polygons]
bn, hn = smooth_normals([(BV, BF), (HEAD_V, HEAD_FACES)])
_new = np.zeros(len(hme.polygons), int)
hme.attributes["new"].data.foreach_get("value", _new)
_old = np.stack([np.array([d.value for d in hme.attributes[f"n{k}"].data]) for k in range(3)], 1)
_lv = np.array([lp.vertex_index for lp in hme.loops])
_lp = np.zeros(len(hme.loops), int)
for p in hme.polygons:
    _lp[p.loop_start:p.loop_start + p.loop_total] = p.index
# Her own normals kept, but on what is new and within 2 cm of CUT (where
# she meets the graft), and where hers were lost in the cutting.
_mine = (_new[_lp] == 0) & (g_cut(BV[_lv]) < -0.02) & (np.linalg.norm(_old, axis=1) > 0.5)
_on = _old[_mine] / np.linalg.norm(_old[_mine], axis=1)[:, None]
_ang = np.degrees(np.arccos(np.clip((_on * bn[_lv[_mine]]).sum(1), -1, 1)))
print("NORMALS: hers differ from the joined smooth ones by %.1f deg on average (%.1f at the 99th percentile)"
      % (_ang.mean(), np.percentile(_ang, 99)))
LN = np.where(_mine[:, None], _old, bn[_lv])
hme.normals_split_custom_set([tuple(n) for n in LN])
head.data.normals_split_custom_set_from_vertices([tuple(n) for n in hn])
for k in ("n0", "n1", "n2", "ox", "oy", "oz", "new"):
    if k in hme.attributes:
        hme.attributes.remove(hme.attributes[k])


# ------------------------------------------------------------ the paint --
def raster(uv, size):
    """The texels inside triangles laid out in UV (t x 3 x 2): for each, its
    row, column, triangle and barycentric weights."""
    w_, h_ = size
    out = []
    for k, t in enumerate(uv * [w_, h_]):
        x0, y0 = np.maximum(np.floor(t.min(0)).astype(int), 0)
        x1, y1 = np.minimum(np.ceil(t.max(0)).astype(int), [w_ - 1, h_ - 1])
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        p = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
        a, b, c = t
        v0, v1, v2 = b - a, c - a, p - a
        den = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(den) < 1e-12:
            continue
        v = (v2[:, 0] * v1[1] - v1[0] * v2[:, 1]) / den
        w = (v0[0] * v2[:, 1] - v2[:, 0] * v0[1]) / den
        bb = np.stack([1 - v - w, v, w], 1)
        m = (bb > -1e-3).all(1)
        if m.any():
            out.append((ys.ravel()[m], xs.ravel()[m], np.full(m.sum(), k), bb[m]))
    return tuple(np.concatenate([o[i] for o in out]) for i in range(4))


def triangles(F, U):
    """Faces as triangles, with each corner's UV."""
    T, TU = [], []
    for f, u in zip(F, U):
        for i in range(1, len(f) - 1):
            T.append((f[0], f[i], f[i + 1]))
            TU.append((u[0], u[i], u[i + 1]))
    return np.array(T), np.array(TU)


from scipy import ndimage  # noqa: E402


def pad(img, filled):
    """Every texel outside the faces given the colour of the nearest inside
    (so their edges stay clean when the texture is drawn smaller)."""
    _, (iy, ix) = ndimage.distance_transform_edt(~filled, return_indices=True)
    return img[iy, ix]


def fill_in(img, known, where):
    """Texels not known painted from those around them, ever wider, with
    her skin's own grain over the top."""
    out = img.copy()
    todo = where & ~known
    m = known.astype(np.float32)
    for sg in (2, 4, 8, 16, 32, 64, 128):
        wsum = ndimage.gaussian_filter(m, sg)
        est = np.stack([ndimage.gaussian_filter(img[:, :, k] * m, sg) for k in range(3)], 2) / np.maximum(wsum, 1e-6)[:, :, None]
        ok = todo & (wsum > 0.02)
        out[ok, :3] = est[ok]
        todo &= ~ok
    # (Any too far from skin to paint from: her skin's own colour.)
    out[todo, :3] = img[known, :3].mean(0)
    hp = img[:, :, :3] - np.stack([ndimage.gaussian_filter(img[:, :, k], 3) for k in range(3)], 2)
    grain = np.std(hp[known], 0)
    noise = ndimage.gaussian_filter(np.random.default_rng(1).standard_normal(img.shape[:2]), 0.8)
    noise /= noise.std() + 1e-9
    gen = where & ~known
    out[gen, :3] += noise[gen][:, None] * grain[None] * 0.4
    return out


def save_image(img, path):
    from PIL import Image
    a = (np.clip(img[::-1], 0, 1) * 255 + 0.5).astype(np.uint8)
    if path.endswith(".jpg"):
        Image.fromarray(a[:, :, :3]).save(path, quality=92)
    else:
        Image.fromarray(a).save(path)


def textured(name, path, alpha=False, rough=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(path, check_existing=True)
    nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
    if alpha:
        nt.links.new(t.outputs["Alpha"], bsdf.inputs["Alpha"])
        m.surface_render_method = "DITHERED"
    bsdf.inputs["Roughness"].default_value = rough
    return m


# Her skin's colour, on her neck and shoulders (well clear of her hair).
_ft = FIT_T[(_tc[FIT_T, 2] > 1.45) & (_tc[FIT_T, 2] < 1.62)]
HER_SKIN = sample(TEX, HUV[HTL[_ft]].mean(1))[:, :3]
HER_MEAN, HER_STD = HER_SKIN.mean(0), HER_SKIN.std(0)
print("HER SKIN", np.round(HER_MEAN, 3), "+-", np.round(HER_STD, 3))

# ---- the graft: unwrapped on its own and painted from her skin where
# she has any, filled in where she had none.
bpy.context.view_layer.objects.active = her
her.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
ebm = bmesh.from_edit_mesh(hme)
for f in ebm.faces:
    f.select = f.material_index == 1
bmesh.update_edit_mesh(hme)
bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.004, scale_to_bounds=True)
bpy.ops.object.mode_set(mode="OBJECT")
GSIZE = 1024
_gf = [p for p in hme.polygons if p.material_index == 1]
_uvd = hme.uv_layers.active.data
GT, GTU = triangles([list(p.vertices) for p in _gf], [np.array([_uvd[li].uv[:] for li in p.loop_indices]) for p in _gf])
r_, c_, t_, b_ = raster(GTU, (GSIZE, GSIZE))
P_ = (BV[GT[t_]] * b_[:, :, None]).sum(1)
_, _, dist, _, huv = on_skin(P_, 0.05, sure=True)
gimg = np.zeros((GSIZE, GSIZE, 4), np.float32)
gimg[..., 3] = 1
known = np.zeros((GSIZE, GSIZE), bool)
col = sample(TEX, huv)[:, :3]
# Only paint that is her skin's (her hair's red and its shadows were
# painted onto her skin around it too): the rest filled in.
ok = (dist < 0.006) & ((np.abs(col - HER_MEAN) / HER_STD).max(1) < 3.0)
gimg[r_[ok], c_[ok], :3] = col[ok]
known[r_[ok], c_[ok]] = True
inside = np.zeros((GSIZE, GSIZE), bool)
inside[r_, c_] = True
# (and none within 5 texels of what was not: the soft edges of that paint)
known &= ~ndimage.binary_dilation(inside & ~known, iterations=5)
gimg = pad(fill_in(gimg, known, inside), inside)
print("GRAFT paint: %d%% from her skin, the rest filled in" % (100 * known[r_, c_].mean()))
gpath = os.path.join(TEXDIR, "heroine_graft.jpg")
save_image(gimg, gpath)
hme.materials[1] = textured("skin_graft", gpath)

# ---- her head: MakeHuman's skin, in her colouring, on a texture of its
# own; at her neck, her own skin, so the two meet unseen.
_mh_skin = os.path.join(DATA, *SKIN)
_mh_png = next(os.path.join(_mh_skin, f) for f in os.listdir(_mh_skin) if f.endswith(".png") and "normal" not in f)
MH_TEX = load_png(_mh_png)
# Her head's own texture, 4K: MakeHuman's islands for it packed to fill
# the square (laid as MakeHuman lays them, her face had a sixth of it).
bpy.ops.object.select_all(action="DESELECT")
head.select_set(True)
bpy.context.view_layer.objects.active = head
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.select_all(action="SELECT")
bpy.ops.uv.pack_islands(rotate=True, margin=0.003)
bpy.ops.object.mode_set(mode="OBJECT")
_uvd2 = head.data.uv_layers[0].data
HEAD_UV2 = [np.array([_uvd2[li].uv[:] for li in p.loop_indices]) for p in head.data.polygons]
HSIZE = 4096
HT2, HTU2 = triangles(HEAD_FACES, HEAD_UV2)
_, HTU1 = triangles(HEAD_FACES, HEAD_UV)
r_, c_, t_, b_ = raster(HTU2, (HSIZE, HSIZE))
P_ = (HEAD_V[HT2[t_]] * b_[:, :, None]).sum(1)
col = sample(MH_TEX, (HTU1[t_] * b_[:, :, None]).sum(1))[:, :3]
# MakeHuman's colouring made hers: its neck's mean and spread made her neck's.
_neck = s_split(P_) < 0.04
mh_mean, mh_std = col[_neck].mean(0), col[_neck].std(0)
col = HER_MEAN + (col - mh_mean) * np.clip(HER_STD / (mh_std + 1e-6), 0.7, 1.4)
# Her face as tools/assets/heroine_face.py painted it (a photograph's skin,
# brows, lashes and lips, by the local ComfyUI), over MakeHuman's by its alpha.
FACE_PAINT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "heroine_face", "face_paint.png")
if os.path.exists(FACE_PAINT):
    from PIL import Image
    _fp = np.asarray(Image.open(FACE_PAINT).convert("RGBA"), np.float32)[::-1] / 255
    if _fp.shape[0] == HSIZE:
        _a = _fp[r_, c_, 3:4]
        col = col * (1 - _a) + _fp[r_, c_, :3] * _a
        print("FACE PAINT laid over %d%% of her head" % (100 * (_a > 0.5).mean()))
# Over the 3 cm above SPLIT, eased into her own skin's.
near = s_split(P_) < 0.03
_, _, dist, _, huv = on_skin(P_[near], 0.05, sure=True)
hc_ = sample(TEX, huv)[:, :3]
mix = (1 - smooth01(s_split(P_[near]) / 0.03)) * (dist < 0.01) * ((np.abs(hc_ - HER_MEAN) / HER_STD).max(1) < 4.0)
mix = mix[:, None]
col[near] = col[near] * (1 - mix) + hc_ * mix
himg = np.zeros((HSIZE, HSIZE, 4), np.float32)
himg[..., 3] = 1
himg[r_, c_, :3] = col
inside = np.zeros((HSIZE, HSIZE), bool)
inside[r_, c_] = True
himg = pad(himg, inside)
hpath = os.path.join(TEXDIR, "heroine_head.jpg")
save_image(himg, hpath)

head.data.materials[0] = textured("skin_head", hpath)
print("HEAD paint from", os.path.basename(_mh_png))


# ---- her own paint below CUT, where hair lay on her: her skin's colour
# brought in from around it.
# Each texel of her upper body tested (thin streaks of it cross faces whose
# middles are skin), but for the fronts of her breasts.
_hair_f = np.zeros(len(hme.polygons), int)
if "hair_paint" in hme.attributes:
    hme.attributes["hair_paint"].data.foreach_get("value", _hair_f)
_up = []
for p in hme.polygons:
    c = BV[list(p.vertices)]
    if p.material_index == 0 and c[:, 2].max() > 1.2 and min(np.linalg.norm(c.mean(0) - a) for a in AREOLA) > 0.025:
        _up.append(p)
_hp = [p for p in _up if _hair_f[p.index]]
if _up:
    _, RTU = triangles([list(p.vertices) for p in _up], [np.array([_uvd[li].uv[:] for li in p.loop_indices]) for p in _up])
    r_, c_, _, _ = raster(RTU, (TEX.shape[1], TEX.shape[0]))
    # (and each face's corners and middle, for faces too small to hold a texel)
    _pts = np.vstack([RTU.reshape(-1, 2), RTU.mean(1)])
    r_ = np.r_[r_, np.clip((_pts[:, 1] * TEX.shape[0]).astype(int), 0, TEX.shape[0] - 1)]
    c_ = np.r_[c_, np.clip((_pts[:, 0] * TEX.shape[1]).astype(int), 0, TEX.shape[1] - 1)]
    tc = TEX[r_, c_, :3]
    red_t = (tc[:, 0] > 2.0 * tc[:, 1]) & (tc[:, 0] > 2.2 * tc[:, 2])
    bad = np.zeros(TEX.shape[:2], bool)
    bad[r_[red_t], c_[red_t]] = True
    if _hp:
        _, RTU = triangles([list(p.vertices) for p in _hp], [np.array([_uvd[li].uv[:] for li in p.loop_indices]) for p in _hp])
        r2, c2, _, _ = raster(RTU, (TEX.shape[1], TEX.shape[0]))
        _pts = np.vstack([RTU.reshape(-1, 2), RTU.mean(1)])
        bad[np.clip((_pts[:, 1] * TEX.shape[0]).astype(int), 0, TEX.shape[0] - 1),
            np.clip((_pts[:, 0] * TEX.shape[1]).astype(int), 0, TEX.shape[1] - 1)] = True
        bad[r2, c2] = True
    bad = ndimage.binary_dilation(bad, iterations=3)
    # (Painted from her skin only, not the texture's empty space.)
    _all = [p for p in hme.polygons if p.material_index == 0]
    _, RTU = triangles([list(p.vertices) for p in _all], [np.array([_uvd[li].uv[:] for li in p.loop_indices]) for p in _all])
    r3, c3, _, _ = raster(RTU, (TEX.shape[1], TEX.shape[0]))
    used = np.zeros(TEX.shape[:2], bool)
    used[r3, c3] = True
    TEX2 = fill_in(TEX, used & ~bad, bad)
    # (Written out and loaded back: packing an image already packed keeps
    # the old paint, not the new.)
    _bp = os.path.join(os.path.dirname(OUT_BLEND), "heroine_body_paint.png")
    save_image(TEX2, _bp)
    _new_img = bpy.data.images.load(_bp, check_existing=False)
    _new_img.pack()
    for n in hme.materials[0].node_tree.nodes:
        if n.type == "TEX_IMAGE" and n.image == IMG:
            n.image = _new_img
    print("REPAINTED %d texels where hair lay on her" % bad.sum())
hme.attributes.remove(hme.attributes["hair_paint"])


# ------------------------------------------------------------ her parts --
def rig(o, W):
    """Parented to her skeleton, weighted to its bones."""
    o.parent = arm
    o.matrix_parent_inverse.identity()
    mod = o.modifiers.new("Armature", "ARMATURE")
    mod.object = arm
    for b in np.nonzero(W.max(0) > 1e-3)[0]:
        g = o.vertex_groups.new(name=BONES[b])
        for i in np.nonzero(W[:, b] > 1e-3)[0]:
            g.add([int(i)], float(W[i, b]), "REPLACE")


rig(head, RW[hv])


def mhmat_texture(mhmat):
    """The diffuse texture an asset's material names, copied to hers."""
    tex = next(line.split()[1] for line in open(mhmat, encoding="utf-8") if line.startswith("diffuseTexture"))
    dst = os.path.join(TEXDIR, os.path.basename(tex))
    shutil.copyfile(os.path.join(os.path.dirname(mhmat), tex), dst)
    return dst


def asset_mhmat(kind, name):
    d = os.path.join(DATA, kind, name)
    return next(os.path.join(d, f) for f in os.listdir(d) if f.endswith(".mhmat"))


# Each part: its material's name (the game knows them by it), whether its
# texture's alpha cuts it out (the eyes' clear corneas too), and its roughness.
PART_LOOK = {"eyes": ("eyes", True, 0.1), "eyebrows": ("brows", True, 0.8), "eyelashes": ("lashes", True, 0.8),
             "teeth": ("teeth", False, 0.3), "tongue": ("tongue", False, 0.45)}
parts = []
for kind, name in PARTS:
    V, F, U = grab(proxies[name])
    key, alpha, rough = PART_LOOK[kind]
    mhmat = os.path.join(DATA, "eyes", "materials", EYES + ".mhmat") if kind == "eyes" else asset_mhmat(kind, name)
    o = mesh_object("Heroine" + key.capitalize(), place(V), F, U, [textured(key, mhmat_texture(mhmat), alpha, rough)])
    W = np.zeros((len(V), len(BONES)))
    W[:, BI["Head"]] = 1
    rig(o, W)
    parts.append(o)
    print("PART", o.name, len(V), "points")
check("parts", [her, head] + parts, views=(("front", 0, 0.0), ("q", 35, 0.0)), tgt=(0, -0.0, 1.70), dist=0.55, lens=85)
if os.environ.get("HEAD_STOP") == "parts":
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
    raise SystemExit

# ------------------------------------------------------------ her shapes --
# Each slider and expression as a shape key on her head and on whichever of
# its parts it moves (the eyes, brows and lashes follow by the way MakeHuman
# fits them to it), none of it moving her neck at SPLIT.
_keys = hm.data.shape_keys.key_blocks
_basis = np.array([v.co[:] for v in hm.data.shape_keys.reference_key.data])
_to_world = (S * R) @ np.array(hm.matrix_world)[:3, :3]


def base_delta(targets):
    d = np.zeros_like(_basis)
    for t in targets:
        kd = np.zeros(len(_basis) * 3)
        _keys[SK[t]].data.foreach_get("co", kd)
        d += kd.reshape(-1, 3) - _basis
    return d @ _to_world.T


_hold = smooth01(s_split(HEAD_V) / 0.02)[:, None]
# MakeHuman's targets for the size and place of her eyes move their sockets
# and not the eyes in them: for those each eye is moved and scaled as the
# skin round it is (a best fit of its rim), so it stays in its socket.
EYE_FOLLOW = ("eyes_size", "eyes_spacing", "eyes_height")
_eye_obj = next(o for o, (kind, _) in zip(parts, PARTS) if kind == "eyes")
_ev = np.array([v.co[:] for v in _eye_obj.data.vertices])
_eyes = []
for sd in (1, -1):
    ids = np.where(_ev[:, 0] * sd > 0)[0]
    c = _ev[ids].mean(0)
    r = np.linalg.norm(_ev[ids] - c, axis=1).max()
    rim = np.where(np.linalg.norm(HEAD_V - c, axis=1) < r * 1.6)[0]
    _eyes.append((ids, c, rim))


def eye_follow(dh):
    """The eyes' moves for a change of the head's points: each scaled and
    shifted as best fits the change of the skin round it."""
    de = np.zeros_like(_ev)
    for ids, c, rim in _eyes:
        q = HEAD_V[rim] - c
        q -= q.mean(0)
        d = dh[rim] - dh[rim].mean(0)
        k = 1 + (q * d).sum() / max((q * q).sum(), 1e-12)
        t = dh[rim].mean(0) - (k - 1) * (HEAD_V[rim].mean(0) - c)
        de[ids] = (k - 1) * (_ev[ids] - c) + t
    return de


_maps = {}
for o, (kind, name) in zip(parts, PARTS):
    m = Mhclo()
    m.load(os.path.join(DATA, kind, name, name + ".mhclo"))
    _maps[o] = m
for o in [head] + parts:
    o.shape_key_add(name="Basis", from_mix=False)
_made = 0
for sname, targets in SHAPES.items():
    d = base_delta(targets)
    dh = (SUB @ d)[hv] * _hold
    if np.abs(dh).max() > 1e-5:
        k = head.shape_key_add(name=sname, from_mix=False)
        k.data.foreach_set("co", (HEAD_V + dh).ravel())
        _made += 1
    for o in parts:
        if o == _eye_obj and sname.rstrip("+-") in EYE_FOLLOW:
            dp = eye_follow(dh)
        else:
            mv = _maps[o].verts
            dp = np.zeros((len(o.data.vertices), 3))
            for i in range(len(dp)):
                if i in mv:
                    v3, w3 = mv[i]["verts"], mv[i]["weights"]
                    dp[i] = w3[0] * d[v3[0]] + w3[1] * d[v3[1]] + w3[2] * d[v3[2]]
        if np.abs(dp).max() > 1e-5:
            base = np.zeros(len(dp) * 3)
            o.data.vertices.foreach_get("co", base)
            o.shape_key_add(name=sname, from_mix=False).data.foreach_set("co", (base.reshape(-1, 3) + dp).ravel())
print("SHAPES: %d on her head, of %d sliders' and expressions' (%s)" % (_made, len(SHAPES), ", ".join(
    "%s %d" % (o.name, len(o.data.shape_keys.key_blocks) - 1) for o in parts)))


# ---- her face's paint put right where it and her head disagree (lashes
# painted on her lids, nostrils painted off her nose): heroine_face_fixes.py,
# from the paint as made here.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_face_fixes  # noqa: E402
shutil.copy(hpath, heroine_face_fixes.RAW)
heroine_face_fixes.fix(head, hpath)
for _im in bpy.data.images:
    if bpy.path.abspath(_im.filepath) == hpath:
        if _im.packed_file:
            _im.unpack(method="REMOVE")
        _im.reload()


# ---------------------------------------------------------------- written --
for o in [hm] + list(proxies.values()) + [o for o in bpy.data.objects if o.name.startswith("CheckCam")]:
    bpy.data.objects.remove(o, do_unlink=True)
for m in her.modifiers:
    m.show_render = True
os.makedirs(os.path.dirname(OUT_BLEND), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)


def export(objs, path, **kw):
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.export_scene.gltf(filepath=path, use_selection=True, export_skins=True, export_animations=False, export_yup=True, **kw)


_game_parts = [o for o in parts if not (o.name == "HeroineBrows" and os.path.exists(FACE_PAINT))]
export([her, head] + _game_parts, os.path.join(ART, "heroine.glb"), export_format="GLB")
print("WRITTEN", OUT_BLEND, "and", ART)
