"""His head, made anew: heroine_head.py's way, for the hero. The sculpt's
head (tools/assets/hero_male_body.py) has its eyes and lips moulded shut into
it and painted on, so nothing about it could move. In its place a MakeHuman
man's head (CC0, made by MPFB), bald, with eyes, brows, lashes, teeth and
tongue of its own, shaped as his own (FACE) and placed on his face. His
hair and beards are made on it after (tools/assets/hero_male_hair.py).

    blender -b tools/comfy/out/heroes/hero_male_body.blend --python tools/assets/hero_male_head.py -- \
        tools/comfy/out/heroes/hero_male_built.blend godot/art/people

The scene is what hero_male_body.py saved; the scene saved is the one his
outfits are built on (hero_male_outfits.py).

He is bald and his sculpt's skin is whole, so only his head is new: above
SPLIT (under his jaw in front, under his skull behind) MakeHuman's, held to
its own shape; between SPLIT and CUT (across the middle of his neck) its
neck, fitted to his own skin, so his thick neck is his; below CUT his body
as the sculpt made it. The neck's ring is sewn to his body along CUT, and
his head, a mesh of its own for its shape keys, meets it along SPLIT, where
the two share their points.

His skin is made one with it on the way: his body's paint and relief are
cleaned of what the sculpt's lighting and long hair left on them
(tools/assets/hero_male_skin.py), his neck and shoulders smoothed where that
hair lay, and his neck, graft and head brought to one tone after his face's
fixes. His brows are marked in hero_shadow.png's blue for the game to dye.

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

# MakeHuman's man: thirty or so, hard-muscled, lean in the face; his face
# shaped after (FACE).
MACROS = {"gender": 1.0, "age": 0.56, "muscle": 0.95, "weight": 0.55, "proportions": 1.0, "height": 0.6, "cupsize": 0.5,
          "firmness": 0.5, "race": {"african": 0.0, "asian": 0.0, "caucasian": 1.0}}
# His parts, MakeHuman's own (all CC0): kind, asset. (His brows are painted
# into his face by hero_male_face.py, and then not written for the game.)
PARTS = [("eyes", "high-poly"), ("eyebrows", "eyebrow001"), ("eyelashes", "eyelashes01"), ("teeth", "teeth_base"),
         ("tongue", "tongue01")]
EYES = "brown"
SKIN = ("skins", "young_caucasian_male")
# (His hair and beards are tools/assets/hero_male_hair.py's, made on this head.)

# His face: a soldier's, handsome and hard used. A square jaw, wide at its
# angles, a strong chin with a faint cleft; high cheekbones over lean cheeks;
# a heavy brow, low over deep-set, narrowed eyes; a straight nose with a
# break in its bridge; a wide mouth, the lower lip the fuller.
# (His skull rounded, not boxed: head-square flattens its crown, so less of
# it, and head-oval lifts the crown back; his jaw keeps its width from
# chin-bones.)
FACE = {"head-square": 0.2, "head-oval": 0.2, "head-scale-vert-decr": 0.2, "forehead-scale-vert-decr": 0.3, "head-fat-decr": 0.4,
        "head-back-scale-depth-incr": 0.2,
        "chin-width-incr": 0.45, "chin-bones-incr": 0.9, "chin-prominent-incr": 0.35, "chin-height-incr": 0.05, "chin-cleft-incr": 0.25,
        "X-cheek-bones-incr": 0.65, "X-cheek-volume-decr": 0.6, "forehead-nubian-incr": 0.3,
        "eyebrows-trans-down": 0.35, "eyebrows-trans-forward": 0.5, "eyebrows-angle-down": 0.15,
        "X-eye-height2-decr": 0.15, "X-eye-push1-in": 0.25,
        "nose-hump-incr": 0.2, "nose-width1-incr": 0.25, "nose-point-width-decr": 0.1, "nose-scale-depth-incr": 0.1,
        "mouth-scale-horiz-incr": 0.18, "mouth-lowerlip-volume-incr": 0.3, "mouth-upperlip-volume-incr": 0.05}
# His sliders, for the game to shape his face with: each a shape key one
# way (name+) and the other (name-), from MakeHuman's targets. (The
# heroine's, with a beard's jaw in place of her pointed ears.)
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
    "chin_forward": ("chin-prominent-incr", "chin-prominent-decr"), "chin_cleft": ("chin-cleft-incr", "chin-cleft-decr"),
    "brow_ridge": ("forehead-nubian-incr", "forehead-nubian-decr"), "ears_size": ("X-ear-scale-incr", "X-ear-scale-decr"),
}
# His expressions (MakeHuman's expression units), for blinking, speaking and
# his scenes: each a shape key from nothing to full. (Hers, and a jaw set
# hard for a fight.)
EXPRESSIONS = {
    "blink_l": ["eye-left-closure"], "blink_r": ["eye-right-closure"], "eyes_wide": ["eye-left-opened-up", "eye-right-opened-up"],
    "squint": ["eye-left-slit", "eye-right-slit"], "brows_up": ["eyebrows-left-up", "eyebrows-right-up"],
    "brows_sad": ["eyebrows-left-inner-up", "eyebrows-right-inner-up"], "brows_angry": ["eyebrows-left-down", "eyebrows-right-down"],
    "smile": ["mouth-corner-puller"], "mouth_open": ["mouth-open"], "pucker": ["mouth-pursing"], "snarl": ["mouth-upward-retraction"],
    "frown": ["mouth-depression"], "nose_wrinkle": ["nose-compression"],
}

# His SPLIT and CUT, from his own profile (hero_male_body.py: 1.98 m): the
# corner under his jaw at 1.70 m, the hollow of his nape at 1.76 m. Both
# lean as his neck does (rising behind, 0.54 m a metre).
SPLIT_Z, CUT_Z, LEAN = 1.696, 1.662, 0.54
HEAD_SCALE = 1.06


def cut_z(P):
    """Height of CUT under a point: across the middle of his neck, a few
    centimetres under SPLIT and parallel to it."""
    return CUT_Z + LEAN * P[:, 1]


def g_cut(P):
    return P[:, 2] - cut_z(P)


def s_split(P):
    """Above SPLIT is his head: under his jaw in front, under his skull behind."""
    return P[:, 2] - (SPLIT_Z + LEAN * P[:, 1])


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


# ------------------------------------------------------------------ him --
him = bpy.data.objects["Hero"]
arm = bpy.data.objects["Armature"]
BONES = [b.name for b in arm.data.bones]
BI = {n: i for i, n in enumerate(BONES)}
hme = him.data
assert him.matrix_world == arm.matrix_world and him.matrix_world.is_identity
IMG = next(n.image for n in hme.materials[0].node_tree.nodes if n.type == "TEX_IMAGE" and n.image and n.image.colorspace_settings.name == "sRGB")
TEX = np.array(IMG.pixels[:], np.float32).reshape(IMG.size[1], IMG.size[0], 4)
HV = np.array([v.co[:] for v in hme.vertices])


def hair_lay(P):
    """Where the sculpt's long hair lay on him: his neck, the tops of his
    shoulders and his upper chest and back, above his nipples and inside his
    deltoids (his arms, out level in his rest pose, are not in it)."""
    return smooth01((P[:, 2] - 1.45) / 0.04) * (1 - smooth01((np.abs(P[:, 0]) - 0.24) / 0.05))


# ---- his neck and shoulders smoothed where the sculpt's hair lay: its
# strands were moulded into him there as ridges, and his collarbones' edges
# came out as sharp folds, so a light from behind drew hard white lines on
# them. Taubin's smoothing (which keeps his size), his muscles left as they
# are, being far broader than a strand.
_E = np.array([e.vertices[:] for e in hme.edges])
_Ah = sp.coo_matrix((np.ones(len(_E)), (_E[:, 0], _E[:, 1])), shape=(len(HV), len(HV))).tocsr()
_Ah = ((_Ah + _Ah.T) > 0).astype(float)
_Ah = sp.diags(1 / np.maximum(np.asarray(_Ah.sum(1)).ravel(), 1)) @ _Ah
_wh = hair_lay(HV)[:, None]
_HV0 = HV.copy()
for _ in range(30):
    HV = HV + 0.5 * _wh * (_Ah @ HV - HV)
    HV = HV - 0.53 * _wh * (_Ah @ HV - HV)
hme.vertices.foreach_set("co", HV.ravel())
hme.update()
print("NECK smoothed where his hair lay: %d points, %.1f mm at most" % ((_wh > 0.5).sum(), 1000 * np.linalg.norm(HV - _HV0, axis=1).max()))
del _Ah, _wh, _HV0, _E
hme.calc_loop_triangles()
HT = np.array([t.vertices[:] for t in hme.loop_triangles])
HTL = np.array([t.loops[:] for t in hme.loop_triangles])
HTP = np.array([t.polygon_index for t in hme.loop_triangles])
HUV = np.array([d.uv[:] for d in hme.uv_layers.active.data])
HW = np.zeros((len(HV), len(BONES)))
gname = {g.index: g.name for g in him.vertex_groups}
for v in hme.vertices:
    for g in v.groups:
        if gname.get(g.group) in BI:
            HW[v.index, BI[gname[g.group]]] = g.weight
# (He has no hair lying on him, and nothing to keep it off: the heroine's
# masks of both, empty.)
RED = np.zeros(len(hme.polygons), bool)
AREOLA = []
# His skin as it is: what everything new is fitted to, weighted from and
# painted from. Not his face (the new one is MakeHuman's).
_tc = HV[HT].mean(1)
SKIN_T = np.where(s_split(_tc) < -0.004)[0]
SKIN_BVH = BVHTree.FromPolygons([tuple(p) for p in HV], HT[SKIN_T].tolist())
FIT_T, FIT_BVH = SKIN_T, SKIN_BVH
NEAR_T, NEAR_BVH = SKIN_T, SKIN_BVH
print("HIM", len(HV), "points")


def on_skin(pts, maxd=0.3, sure=False, near=False):
    """For each point the nearest of his skin (with `sure`, of the skin
    well clear of his hair): where, its normal, its distance, and the
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
    """His nose tip and the bottom of his chin, from his face's profile."""
    m = (_tc[:, 2] > 1.62) & (_tc[:, 2] < 1.92) & (_tc[:, 1] < 0.0)
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
# nothing yet), for what each does to him to be read off later.
SHAPES = {}
for _k, (_up, _down) in SLIDERS.items():
    SHAPES[_k + "+"] = sides([_up])
    if _down:
        SHAPES[_k + "-"] = sides([_down])
for _k, _ts in EXPRESSIONS.items():
    SHAPES[_k] = ["x:" + t for t in _ts]
# MakeHuman's man is longer and slimmer of neck than he is (a wrestler's
# neck, near as wide as his jaw): his build set by these, so the neck fitted
# to his between CUT and SPLIT need not swell to reach it.
BUILD = {"measure-neck-height-decr": 0.5, "measure-neck-circ-incr": 1.0, "neck-scale-horiz-incr": 0.5}
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
# (His ears, as MakeHuman marks them.)
_earg = hm.vertex_groups["ears"].index
EARS_MH = np.array([max([g.weight for g in v.groups if g.group == _earg], default=0.0) for v in hm.data.vertices])
keep = [i for i, f in enumerate(MF) if _inbody[f].all()]
MF = [MF[i] for i in keep]
MU = [MU[i] for i in keep]
print("MAKEHUMAN", len(MV), "points,", len(MF), "faces of skin")

# ---- his face's place: scale from nose to chin, then turned and moved
# till its surface lies on hers (an ICP at that scale).
_top = MV[_inbody, 2].max()
mn, mc = nose_chin(MV[_inbody & (MV[:, 2] > _top - 0.28)])
hn, hc = her_face_landmarks()
# (A size larger than his sculpt's face: on his shoulders and his neck, a
# wrestler's, the sculpt's own head looked small.)
S = HEAD_SCALE * np.linalg.norm(hn - hc) / np.linalg.norm(mn - mc)
R = np.eye(3)
T = hn - S * mn
_hf = np.where(~RED[HTP] & (_tc[:, 2] > hc[2] - 0.003) & (_tc[:, 2] < 1.88) & (_tc[:, 1] < 0) & (np.abs(_tc[:, 0]) < 0.08))[0]
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





# ---- the region made anew (his head, and his body above CUT), each face
# quartered (linearly, so the surface keeps its shape and the eyes, brows
# and lashes, fitted to it, still sit right) for the detail of his skin.
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


# ---- his skull rounded: quartered linearly, MakeHuman's coarse crown kept
# its facets, and bald, they showed against the sky as flat runs and
# corners. Smoothed (Taubin's way, which keeps its size) over his cranium
# only: above his brow and behind his ears, never his face, his ears, or
# the neck that is fitted to his own after.
def find_ears(V):
    """His ears' middles: each side's outermost point near his eyes' height,
    a little in from its rim."""
    eye_z = float(place(grab(proxies["high-poly"])[0])[:, 2].mean())
    side = (np.abs(V[:, 0]) > 0.05) & (np.abs(V[:, 2] - (eye_z - 0.02)) < 0.04)
    ears = []
    for sg in (-1, 1):
        m = side & (np.sign(V[:, 0]) == sg)
        ears.append(V[m][np.argmax(np.abs(V[m, 0]))] - [sg * 0.012, 0, 0])
    return eye_z, ears


EYE_Z, EARS = find_ears(RV0)


# How much each point of the region is ear (MakeHuman's own marking, eased
# a ring or two past its edge, so what is done round them fades).
def _ring_avg(F, n):
    e = np.array([(f[i], f[(i + 1) % len(f)]) for f in F for i in range(len(f))])
    A = sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)).tocsr()
    A = ((A + A.T) > 0).astype(float)
    return sp.diags(1 / np.maximum(np.asarray(A.sum(1)).ravel(), 1)) @ A


EAR_RV = SUB @ EARS_MH
_A_ears = _ring_avg(RF, len(RV0))
for _ in range(3):
    EAR_RV = np.maximum(EAR_RV, _A_ears @ EAR_RV)
EAR_RV = np.clip(EAR_RV, 0, 1)


def cranium_smoothed(V, F):
    eye_z, ears = EYE_Z, EARS
    ear_y = float(np.mean([e[1] for e in ears]))
    up = smooth01((V[:, 2] - (eye_z + 0.045)) / 0.03)
    back = smooth01((V[:, 1] - (ear_y + 0.025)) / 0.02)
    w = np.maximum(up, back) * smooth01(s_split(V) / 0.05 - 0.6)
    w *= 1 - EAR_RV
    e = np.array([(f[i], f[(i + 1) % len(f)]) for f in F for i in range(len(f))])
    A = sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(len(V), len(V))).tocsr()
    A = ((A + A.T) > 0).astype(float)
    A = sp.diags(1 / np.maximum(np.asarray(A.sum(1)).ravel(), 1)) @ A
    w = w[:, None]
    V = V.copy()
    V0 = V.copy()
    for _ in range(60):
        V = V + 0.5 * w * (A @ V - V)
        V = V - 0.53 * w * (A @ V - V)
    print("CRANIUM smoothed over %d points, moved %.1f mm at most" % ((w > 0.5).sum(), 1000 * np.linalg.norm(V - V0, axis=1).max()))
    return V


RV0 = cranium_smoothed(RV0, RF)


# ---- fitted to his skin: as near hers as it can be where she has skin,
# its own shape kept (its Laplacian) where she has none; his head as
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
        it: so a part of him swung as a whole (MakeHuman's arms hang
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
    # Her face held as MakeHuman's; his neck free to follow hers, his skin's
    # pull easing to nothing over the 5 cm below SPLIT (else, his neck being
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
        print("  fit: %d of %d points on his skin, %.1f mm off (stiffness %g)" % (ok.sum(), len(data), 1000 * r.mean(), lam))
    return V


RV = fit(RV0, RF)


def face_normals(V, F):
    n = np.array([np.cross(V[f[1]] - V[f[0]], V[f[-1]] - V[f[0]]) for f in F])
    return n / (np.linalg.norm(n, axis=1)[:, None] + 1e-12)


# Where the fit folded the surface over (pulled on by what was left of his
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
# Near CUT the graft lies on his skin exactly (some of it was fitted to
# none, near his hair), so the two meet flush: wholly at CUT, less and
# less to 3 cm above it.
# (Near it as the crow flies: where CUT climbs over his shoulders its height
# above a point says little of how near the point is.)
_seam = cKDTree(HV[np.abs(g_cut(HV)) < 0.003])
_sd = _seam.query(RV)[0] * np.sign(g_cut(RV))
_near = np.where((s_split(RV) < 0) & (_sd > -0.01) & (_sd < 0.03))[0]
loc, hn_, dist, _, _ = on_skin(RV[_near], 0.02)
_nn = vertex_normals(RV, RF)[_near]
ok = np.isfinite(dist) & ((_nn * hn_).sum(1) > 0.6)
w = (1 - smooth01(_sd[_near] / 0.03))[:, None] * ok[:, None]
RV[_near] += (loc - RV[_near]) * w
print("FLUSH: %d graft points near CUT laid on his skin (%.1f mm at most)" % (ok.sum(), 1000 * (dist[ok] * w[ok, 0]).max()))
# Laid on his scan's faint facets the graft creased: smoothed there (its own
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
# (Its lowest row at least 6 mm above CUT, so the strip sewing it to him
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
        print("   his sure skin from MakeHuman's points there: mean %.1f mm" % (np.nanmean(np.where(np.isfinite(dist), dist, np.nan)) * 1000))
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
    """A loop turned to run one way round his neck (anticlockwise seen from
    above), from its point most to his front."""
    q = P[loop]
    a = np.arctan2(q[:, 0], -(q[:, 1] - 0.03))
    area = np.sum(q[:, 0] * np.roll(q[:, 1], -1) - np.roll(q[:, 0], -1) * q[:, 1])
    if area < 0:
        loop = loop[::-1]
        a = a[::-1]
    k = int(np.argmin(np.abs(a)))
    return loop[k:] + loop[:k]


# ------------------------------------------------------------ his body --
bm = bmesh.new()
bm.from_mesh(hme)
bm.faces.ensure_lookup_table()
# What is his is marked (his own normals kept on his corners, his hair on
# his faces), as cutting renumbers everything.
NL = [bm.loops.layers.float.new(f"n{k}") for k in range(3)]
RL = bm.faces.layers.int.new("hair_paint")
NEW = bm.faces.layers.int.new("new")
# The graft's points marked (the heroine's outfits keep their search for her
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
# Cut along CUT: the field made his height for a moment, the plane cut at
# nought, and his points put back (the new ones where the field is nought).
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
# Loose scraps of hair below CUT. (Hair lying on his skin there is his
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
# (Only up here: lower down his paint's seams still part his into islands.)
low = {c for f, c in comp.items() if f.calc_center_median().z < 1.25}
scraps = [f for f, c in comp.items() if c != main and c not in low]
bmesh.ops.delete(bm, geom=scraps, context="FACES")
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
print("BODY cut: %d scraps gone (%d faces)" % (len({comp[f] for f in scraps}), len(scraps)))
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
print("CUT", len(cut_loop), "points round him, %.3f to %.3f m high" % (BP[cut_loop, 2].min(), BP[cut_loop, 2].max()))

# ---- the graft: its points and faces into his body, sewn to his along
# CUT by a strip zipped between his edge and its own.
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
# (One, all the way round him: CUT crossing his arms would part it.)
assert len(gl) == 1, "CUT parts the graft's edge in %d: it must pass over his arms" % len(gl)
graft_loop = around(RV, max(gl, key=len))
# Every point made anew takes his weights from the skin nearest it, easing
# to his head's alone over 3 cm above SPLIT (the same for the graft and his
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
# by dynamic programming), from the graft's point nearest his edge's start.
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
# along his edge against his face beside it (so they face out as hers do:
# judged face by face, thin ones came out backwards, and showed his inside).
_e = next(e for e in A[0].link_edges if e.other_vert(A[0]) == A[1])
_her_way = any(lp.vert == A[0] and lp.link_loop_next.vert == A[1] for lp in _e.link_faces[0].loops)
strip_f = []
for t in strip:
    f = bm.faces.new(t[::-1] if _her_way else t)
    f.smooth = True
    f.material_index = 1
    f[NEW] = 1
    strip_f.append(f)
# Any dent or bump the join left on his back and shoulders, within 5 cm
# above it and 2 cm below, eased out: each point drawn halfway to the plane
# of the skin round it (2.5 cm) while it stands more than 3 mm off it. (Not
# in front, where his collarbones are hers; not his breasts.)
bm.normal_update()
_seam_now = cKDTree(np.array([v.co[:] for v in A]))
_band = [v for v in bm.verts if v.link_faces and not v.is_boundary
         and -0.02 < _seam_now.query(v.co[:])[0] * (1 if g_cut(np.array([v.co[:]]))[0] > 0 else -1) < 0.05
         ]
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
# from his skin) and the surface keeps its form.
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
print("SEWN: %d strip faces between %d of his points and %d of the graft's" % (len(strip), n, m))

# ------------------------------------------------------------- his head --
hv = sorted(head_v)
hmap = {o: n for n, o in enumerate(hv)}
HEAD_V = RV[hv]
EAR_HEAD = EAR_RV[hv]
HEAD_FACES = [[hmap[i] for i in RF[fi]] for fi in HEAD_F]
HEAD_UV = [RU[fi] for fi in HEAD_F]


def check(name, objs, views=(("front", 0, 0.0), ("side", 90, 0.0), ("back", 180, 0.0), ("q", 35, 0.1)), tgt=(0, 0.03, 1.72), dist=1.1,
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
head = mesh_object("HeroHead", HEAD_V, HEAD_FACES, HEAD_UV, [plain("headcheck", (0.5, 0.6, 0.9))])
for mo in him.modifiers:
    mo.show_render = False
check("sewn", [him, head])
check("sewnback", [him, head], views=(("b", 180, 0.15), ("bl", 140, 0.2), ("fr", -30, 0.05)), tgt=(0, 0.04, 1.66), dist=0.7)
if os.environ.get("HEAD_STOP") == "sewn":
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
    raise SystemExit


# ---------------------------------------------------------------- normals --
def smooth_normals(parts):
    """Normals of the surfaces given as one, joined where their points meet
    (his paint's seams, his head on his neck), so no seam shows in the light."""
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
# (Where his hair lay, smoothed, his old normals are not his shape: eased
# into the smooth ones over the smoothing's own edge.)
_t = hair_lay(BV[_lv])[:, None]
LN = LN * (1 - _t) + bn[_lv] * _t
LN /= np.linalg.norm(LN, axis=1)[:, None] + 1e-12
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
    his skin's own grain over the top."""
    out = img.copy()
    todo = where & ~known
    m = known.astype(np.float32)
    for sg in (2, 4, 8, 16, 32, 64, 128):
        wsum = ndimage.gaussian_filter(m, sg)
        est = np.stack([ndimage.gaussian_filter(img[:, :, k] * m, sg) for k in range(3)], 2) / np.maximum(wsum, 1e-6)[:, :, None]
        ok = todo & (wsum > 0.02)
        out[ok, :3] = est[ok]
        todo &= ~ok
    # (Any too far from skin to paint from: his skin's own colour.)
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


# ---- his body's paint cleaned (tools/assets/hero_male_skin.py): the
# sculpt's baked highlights and its hair's streaks taken out, before
# anything is painted from it. Saved beside the paint baked, and drawn in
# its place.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hero_male_skin  # noqa: E402

_r, _c, _t, _b = raster(HUV[HTL], (IMG.size[0], IMG.size[1]))
_P = (HV[HT[_t]] * _b[:, :, None]).sum(1)
_HAIR = hair_lay(_P)
# (Flecks may be lifted anywhere; dark streaks only where his hair lay; his
# nails, pale by right, kept.)
_n, _most = hero_male_skin.clean(TEX, _P, _r, _c, dark_zone=_HAIR > 0.5, keep=(np.abs(_P[:, 0]) > 0.85) | (_P[:, 2] < 0.05))
print("SKIN cleaned: %d texels eased, %.2f at most" % (_n, _most))
hero_male_skin.even(TEX, _P, _r, _c, _HAIR)
# (His neck's one tone, which his graft and head are brought to as well
# (hero_male_skin.one_tone), and his body's skin within 8 cm of CUT eased
# to it, so where they are sewn no line shows.)
NECK_TONE = np.median(TEX[_r, _c, :3][(_HAIR > 0.9) & (np.abs(g_cut(_P)) < 0.06)], 0)
_wc = (1 - smooth01(np.abs(g_cut(_P)) / 0.08)) * (1 - smooth01((np.abs(_P[:, 0]) - 0.22) / 0.06))
_nc = _wc > 0.01
TEX[_r[_nc], _c[_nc], :3] = (TEX[_r[_nc], _c[_nc], :3] * (1 - _wc[_nc, None])
                             + hero_male_skin.one_tone(TEX[_r[_nc], _c[_nc], :3], _P[_nc], NECK_TONE, np.zeros(_nc.sum())) * _wc[_nc, None])
print("NECK tone %s, his skin within 8 cm of CUT eased to it" % np.round(NECK_TONE, 3))
# His relief, the same way: the bake's stray slopes laid flat.
NIMG = next(n.image for n in hme.materials[0].node_tree.nodes if n.type == "TEX_IMAGE" and n.image
            and n.image.colorspace_settings.name == "Non-Color")
NTEX = np.array(NIMG.pixels[:], np.float32).reshape(NIMG.size[1], NIMG.size[0], 4)
# (Where his hair lay, his relief broad only: its strands were moulded in.)
hero_male_skin.clean_relief(NTEX, _P, _r, _c, keep=np.zeros(len(_P), bool), hair=_HAIR)
del _P, _HAIR
# (Both padded afresh from the faces out: the bake's margins round each
# island carried the flecks and slopes cleaned away inside it.)
_cov = np.zeros(TEX.shape[:2], bool)
_cov[_r, _c] = True
for _img in (TEX, NTEX):
    _img[:] = pad(_img, _cov)
_im_dir = os.path.dirname(bpy.path.abspath(IMG.filepath))
for _bi, _arr, _name in ((IMG, TEX, "hero_body_paint_clean.png"), (NIMG, NTEX, "hero_body_normal_clean.png")):
    save_image(_arr, os.path.join(_im_dir, _name))
    _bi.filepath = os.path.join(_im_dir, _name)
    _bi.reload()
del NTEX, _cov

# Her skin's colour, on his neck and shoulders (well clear of his hair).
_ft = FIT_T[(_tc[FIT_T, 2] > 1.52) & (_tc[FIT_T, 2] < 1.66)]
HER_SKIN = sample(TEX, HUV[HTL[_ft]].mean(1))[:, :3]
HER_MEAN, HER_STD = HER_SKIN.mean(0), HER_SKIN.std(0)
print("HER SKIN", np.round(HER_MEAN, 3), "+-", np.round(HER_STD, 3))

# ---- the graft: unwrapped on its own and painted from his skin where
# she has any, filled in where she had none.
bpy.context.view_layer.objects.active = him
him.select_set(True)
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
# Only paint that is his skin's (his hair's red and its shadows were
# painted onto his skin around it too): the rest filled in.
ok = (dist < 0.006) & ((np.abs(col - HER_MEAN) / HER_STD).max(1) < 3.0)
gimg[r_[ok], c_[ok], :3] = col[ok]
known[r_[ok], c_[ok]] = True
inside = np.zeros((GSIZE, GSIZE), bool)
inside[r_, c_] = True
# (and none within 5 texels of what was not: the soft edges of that paint)
known &= ~ndimage.binary_dilation(inside & ~known, iterations=5)
gimg = pad(fill_in(gimg, known, inside), inside)
# (one skin with his body's and his head's: hero_male_skin.one_tone)
gimg[r_, c_, :3] = hero_male_skin.one_tone(gimg[r_, c_, :3], P_, NECK_TONE, np.zeros(len(P_)))
gimg = pad(gimg, inside)
print("GRAFT paint: %d%% from his skin, the rest filled in" % (100 * known[r_, c_].mean()))
gpath = os.path.join(TEXDIR, "hero_graft.jpg")
save_image(gimg, gpath)
hme.materials[1] = textured("skin_graft", gpath)

# ---- his head: MakeHuman's skin, in his colouring, on a texture of its
# own; at his neck, his own skin, so the two meet unseen.
_mh_skin = os.path.join(DATA, *SKIN)
_mh_png = next(os.path.join(_mh_skin, f) for f in os.listdir(_mh_skin) if f.endswith(".png") and "normal" not in f)
MH_TEX = load_png(_mh_png)
# Her head's own texture, 4K: MakeHuman's islands for it packed to fill
# the square (laid as MakeHuman lays them, his face had a sixth of it).
bpy.ops.object.select_all(action="DESELECT")
head.select_set(True)
bpy.context.view_layer.objects.active = head
# (MakeHuman's own layout kept beside it, as "mh", for the face's paint:
# hero_male_face.py records which packed place each part of it was laid
# in, so a packing made anew, as his head's shape changes, never moves it.)
head.data.uv_layers.new(name="mh", do_init=True)
head.data.uv_layers.active_index = 0
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
EAR_T = (EAR_HEAD[HT2[t_]] * b_).sum(1)
P_ = (HEAD_V[HT2[t_]] * b_[:, :, None]).sum(1)
col = sample(MH_TEX, (HTU1[t_] * b_[:, :, None]).sum(1))[:, :3]
# MakeHuman's colouring made hers: its neck's mean and spread made his neck's.
_neck = s_split(P_) < 0.04
mh_mean, mh_std = col[_neck].mean(0), col[_neck].std(0)
col = HER_MEAN + (col - mh_mean) * np.clip(HER_STD / (mh_std + 1e-6), 0.7, 1.4)
# Every MakeHuman man's skin has a buzz cut painted on his scalp; his scalp
# is bare skin (his shaved shadow and his hair are chosen in the game). Above
# his hairline (a line from his brow's top over his ears to his nape), his
# own neck's skin, its grain kept: MakeHuman's paint there with its broad
# colour taken away, laid on his skin's colour. His ears are left as they are.
_eye_z = float(np.mean([p[2] for p in place(grab(proxies["high-poly"])[0])]))
_front = HEAD_V[:, 1].min()


def scalp(P):
    """How much of a point is scalp: 0 below his hairline, 1 a centimetre
    and a half above it."""
    line = _eye_z + 0.075 - 0.75 * (P[:, 1] - _front - 0.015)
    w = smooth01((P[:, 2] - line) / 0.015)
    return w


# Where his beard grows, the same: MakeHuman's man has a shadow of stubble
# painted on, and he is drawn clean-shaven (his stubble and beards are
# chosen in the game). His beard's ground: his jaw and cheeks below his
# cheekbones, up his sideburns to the front of his ears, his upper lip below
# his nose, and under his jaw, but not his lips.
_nose = HEAD_V[np.argmin(HEAD_V[:, 1])]
_teeth = place(grab(proxies["teeth_base"])[0])
_mouth = np.array([0.0, _teeth[:, 1].min() - 0.008, float(np.median(_teeth[_teeth[:, 1] < _teeth[:, 1].min() + 0.01, 2]))])
_side = np.abs(HEAD_V[:, 0]) > 0.068
_ear_y = HEAD_V[_side & (np.abs(HEAD_V[:, 2] - _eye_z) < 0.03), 1].min()
print("BEARD ground: nose tip %s, mouth %s, ears from y %.3f" % (np.round(_nose, 3), np.round(_mouth, 3), _ear_y))


def beard(P):
    """How much of a point is where his beard grows (0 to 1, soft at its edges)."""
    ax = np.abs(P[:, 0])
    # Its upper edge: under his nose over his lip, at his nose's base across
    # his cheeks, up to his eyes' height at his sideburns.
    top = (_nose[2] - 0.021 + 0.016 * smooth01((ax - 0.02) / 0.014)
           + (_eye_z - _nose[2] + 0.005) * smooth01((ax - 0.052) / 0.012))
    w = smooth01((top - P[:, 2]) / 0.01)
    w *= 1 - smooth01((P[:, 1] - (_ear_y - 0.012)) / 0.01)          # in front of his ears
    lip = ((P[:, 0] / 0.027) ** 2 + ((P[:, 2] - _mouth[2]) / 0.0115) ** 2 + ((P[:, 1] - _mouth[1]) / 0.03) ** 2)
    w *= smooth01((lip - 1.0) / 0.35)                                 # not his lips
    return w


# (his ears left as MakeHuman painted them, softly: a hard edge here showed
# as a flat patch with stepped edges on his ear)
_sw = (scalp(P_) * (1 - EAR_T))[:, None]
_bw = beard(P_)[:, None]
# (Their grain found in the texture itself, as an image: the fine detail of
# what is there, its broad colour taken out, a part of it kept, a shaved
# head's faint grain.)
_tmp = np.zeros((HSIZE, HSIZE, 3), np.float32)
_tmp[r_, c_] = col
_ins = np.zeros((HSIZE, HSIZE), bool)
_ins[r_, c_] = True
_tmp = pad(_tmp, _ins)
_broad = ndimage.gaussian_filter(_tmp, (8, 8, 0))[r_, c_]
_grain = _tmp[r_, c_] - _broad
del _tmp
# (Bare too below his hairline on the sides of his head and behind his
# ears, down his nape to SPLIT, all but his beard's ground and his ears:
# MakeHuman's buzz cut reached lower than his hairline and left pale
# stubble at his temples and nape. His face's paint is laid over after;
# his shaved shadow keeps to his hairline.)
_side = np.maximum(smooth01((np.abs(P_[:, 0]) - 0.05) / 0.012), smooth01((P_[:, 1] - (_ear_y + 0.02)) / 0.03))
_bare = np.maximum(_sw, (_side * (1 - _bw[:, 0]) * (1 - EAR_T))[:, None])
col = col * (1 - _bare) + (HER_MEAN + 0.3 * _grain) * _bare
# (His beard's ground keeps its own broad colour, the warmth of his lips and
# cheeks, only lightened back to his skin's where the stubble darkened it.)
_lift = np.clip(HER_MEAN - _broad, 0, None) * 0.8
col = col * (1 - _bw) + (_broad + _lift + 0.25 * _grain) * _bw
print("SCALP cleared over %d%% of his head; BEARD ground over %d%%" % (100 * (_sw > 0.5).mean(), 100 * (_bw > 0.5).mean()))
# The two grounds as a map for the game (his head's UV): red his beard's,
# green his scalp's, for shaders/heroine_skin.gdshader to lay a shaved
# shadow on (People.HisShadow).
_mask = np.zeros((HSIZE, HSIZE, 4), np.float32)
_mask[..., 3] = 1
_mask[r_, c_, 0] = _bw[:, 0]
_mask[r_, c_, 1] = _sw[:, 0]
# His face as tools/assets/hero_male_face.py painted it (a photograph's skin,
# brows, lashes and lips, by the local ComfyUI), over MakeHuman's by its alpha.
# Its edge softened (where a view stopped seeing him it was cut in steps),
# and kept off his ears, which MakeHuman painted whole.
FACE_PAINT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hero_male_face", "face_paint.png")
if os.path.exists(FACE_PAINT):
    from PIL import Image
    _fp = np.asarray(Image.open(FACE_PAINT).convert("RGBA"), np.float32)[::-1] / 255
    if _fp.shape[0] == HSIZE:
        # (Each texel's place in the paint: by MakeHuman's layout, through
        # the packing it was painted in, face_paint_uv.npz.)
        _fuv = os.path.join(os.path.dirname(FACE_PAINT), "face_paint_uv.npz")
        if os.path.exists(_fuv):
            # (MakeHuman's layout gives his head a small corner of the
            # square, its triangles a few texels across: each texel's own
            # triangle found among those nearest, not by rounding.)
            _z = np.load(_fuv)
            _mh = (HTU1[t_] * b_[:, :, None]).sum(1)
            _tri = _z["mh"]
            _, _cand = cKDTree(_tri.mean(1)).query(_mh, k=12)
            _best = np.full(len(_mh), -np.inf)
            _k = _cand[:, 0].copy()
            _bw2 = np.zeros((len(_mh), 3))
            for _j in range(_cand.shape[1]):
                _tm = _tri[_cand[:, _j]]
                _v0, _v1, _v2 = _tm[:, 1] - _tm[:, 0], _tm[:, 2] - _tm[:, 0], _mh - _tm[:, 0]
                _den = _v0[:, 0] * _v1[:, 1] - _v1[:, 0] * _v0[:, 1]
                _den = np.where(np.abs(_den) < 1e-14, 1e-14, _den)
                _bv = (_v2[:, 0] * _v1[:, 1] - _v1[:, 0] * _v2[:, 1]) / _den
                _bw_ = (_v0[:, 0] * _v2[:, 1] - _v2[:, 0] * _v0[:, 1]) / _den
                _b3 = np.stack([1 - _bv - _bw_, _bv, _bw_], 1)
                _score = _b3.min(1)
                _take = _score > _best
                _best[_take], _k[_take], _bw2[_take] = _score[_take], _cand[_take, _j], _b3[_take]
            _bw2 = np.clip(_bw2, 0, 1)
            _bw2 /= _bw2.sum(1, keepdims=True)
            _at = (_z["packed"][_k] * _bw2[:, :, None]).sum(1)
            print("FACE PAINT: %d%% of his head's texels inside a triangle of it" % (100 * (_best > -1e-3).mean()))
            print("FACE PAINT found through MakeHuman's layout (%d triangles)" % len(_z["mh"]))
        else:
            _at = (HTU2[t_] * b_[:, :, None]).sum(1)
        _fpx = sample(_fp, _at)
        # Its edge softened (where a view stopped seeing him it was cut in
        # steps), and kept off his ears.
        _alpha = np.zeros((HSIZE, HSIZE), np.float32)
        _alpha[r_, c_] = _fpx[:, 3]
        _in = _ins.astype(np.float32)
        _soft = ndimage.gaussian_filter(_alpha, 5) / np.maximum(ndimage.gaussian_filter(_in, 5), 1e-6)
        # (His face only: Krea painted a buzz cut's pale stubble on his
        # temples above his ears and on his scalp, and he is bare there.)
        # (On the sides of his head, wide of his brows' tails, his hairline
        # comes down to the top of his ear; behind his ear it is nape.)
        _temple = (smooth01((np.abs(P_[:, 0]) - 0.058) / 0.008) * smooth01((P_[:, 2] - _eye_z) / 0.012)
                   * smooth01((P_[:, 1] - (_ear_y - 0.03)) / 0.012)
                   + smooth01((P_[:, 1] - (_ear_y + 0.005)) / 0.02) * smooth01((P_[:, 2] - (_eye_z - 0.06)) / 0.02))
        _dom = (1 - _sw[:, 0]) * (1 - np.clip(_temple, 0, 1))
        _a = (np.minimum(_fpx[:, 3], _soft[r_, c_]) * (1 - EAR_T) * _dom)[:, None]
        col = col * (1 - _a) + _fpx[:, :3] * _a
        print("FACE PAINT laid over %d%% of his head" % (100 * (_a > 0.5).mean()))
        del _soft, _alpha
# His brows (painted with his face) marked for the game to dye them his
# hair's colour (People.HisShadow): blue in the map, as much as each texel
# is darker than his brow's bare skin, in the band above his eyes.
_ax = np.abs(P_[:, 0])
# (Where they grow: about MakeHuman's own brows, its cards laid on his
# brow, a centimetre round, for Krea painted them heavier and lower.)
_bcard = cKDTree(place(grab(proxies["eyebrow001"])[0]))
_bz = 1 - smooth01((_bcard.query(P_)[0] - 0.005) / 0.004)
_lum = col @ np.array([0.3, 0.59, 0.11])
_fore = (P_[:, 2] > _eye_z + 0.055) & (P_[:, 2] < _eye_z + 0.08) & (_ax < 0.04) & (P_[:, 1] < _ear_y - 0.01)
# (only what is clearly darker than his brow's skin: a lid's or a brow
# bone's shading, dyed a fair man's colour, showed as a pale patch)
_brow = np.clip((np.median(_lum[_fore]) - _lum - 0.05) / 0.15, 0, 1) * _bz
_mask[r_, c_, 2] = _brow
BROW_T = _brow.copy()
print("BROWS marked over %d texels" % (_brow > 0.5).sum())
save_image(pad(_mask, _ins), os.path.join(TEXDIR, "hero_shadow.png"))
# Over the 3 cm above SPLIT, eased into his own skin's.
near = s_split(P_) < 0.03
_, _, dist, _, huv = on_skin(P_[near], 0.05, sure=True)
hc_ = sample(TEX, huv)[:, :3]
# (His skin there is clean now, hero_male_skin.py: taken wherever it is
# near, the ease smooth, not cut in scallops where his old hair's paint was.)
mix = (1 - smooth01(s_split(P_[near]) / 0.03)) * (1 - smooth01((dist - 0.01) / 0.01))
mix = mix[:, None]
col[near] = col[near] * (1 - mix) + hc_ * mix
# (Brought to one skin with his body's after the face's fixes, which find
# his lips by their own red: see below.)
_face_w = np.maximum(_a[:, 0] if os.path.exists(FACE_PAINT) else 0.0, EAR_T)
himg = np.zeros((HSIZE, HSIZE, 4), np.float32)
himg[..., 3] = 1
himg[r_, c_, :3] = col
inside = np.zeros((HSIZE, HSIZE), bool)
inside[r_, c_] = True
himg = pad(himg, inside)
hpath = os.path.join(TEXDIR, "hero_head.jpg")
save_image(himg, hpath)
HEAD_TEXELS = (r_.copy(), c_.copy(), P_.copy(), _face_w.copy())

head.data.materials[0] = textured("skin_head", hpath)
print("HEAD paint from", os.path.basename(_mh_png))


# (The heroine's sculpt had hair painted on his skin below CUT, repainted
# here; his skin is bare.)
hme.attributes.remove(hme.attributes["hair_paint"])


# ------------------------------------------------------------ his parts --
def rig(o, W):
    """Parented to his skeleton, weighted to its bones."""
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
    o = mesh_object("Hero" + key.capitalize(), place(V), F, U, [textured(key, mhmat_texture(mhmat), alpha, rough)])
    W = np.zeros((len(V), len(BONES)))
    W[:, BI["Head"]] = 1
    rig(o, W)
    parts.append(o)
    print("PART", o.name, len(V), "points")
check("parts", [him, head] + parts, views=(("front", 0, 0.0), ("q", 35, 0.0)), tgt=(0, -0.0, 1.84), dist=0.55, lens=85)
if os.environ.get("HEAD_STOP") == "parts":
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
    raise SystemExit

# ------------------------------------------------------------ his shapes --
# Each slider and expression as a shape key on his head and on whichever of
# its parts it moves (the eyes, brows and lashes follow by the way MakeHuman
# fits them to it), none of it moving his neck at SPLIT.
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
# MakeHuman's targets for the size and place of his eyes move their sockets
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
print("SHAPES: %d on his head, of %d sliders' and expressions' (%s)" % (_made, len(SHAPES), ", ".join(
    "%s %d" % (o.name, len(o.data.shape_keys.key_blocks) - 1) for o in parts)))


# ---- his face's paint put right where it and his head disagree (lashes
# painted on his lids, nostrils painted off his nose): heroine_face_fixes.py,
# from the paint as made here.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_face_fixes  # noqa: E402
# (His raw paint kept apart from hers, and his eyes found by his names.)
heroine_face_fixes.RAW = os.path.join(os.path.dirname(OUT_BLEND), "hero_head_raw.jpg")


def _his_landmarks(h):
    mw = h.matrix_world
    P = np.array([(mw @ v.co)[:] for v in h.data.vertices])
    eyes = bpy.data.objects["HeroEyes"]
    ez = float(np.mean([(eyes.matrix_world @ v.co)[2] for v in eyes.data.vertices]))
    return P, ez, P[:, 1].min()


heroine_face_fixes.landmarks = _his_landmarks
shutil.copy(hpath, heroine_face_fixes.RAW)
heroine_face_fixes.fix(head, hpath)
# (Her nostrils' shading, on his larger nose, also reached a few of the
# faces beside it, and laid its deep red on his cheek and lip in small hard
# diamonds: anything it darkened hard away from his nostrils given back.)
from PIL import Image  # noqa: E402
_fixed = np.asarray(Image.open(hpath).convert("RGB"), np.float32) / 255
_raw = np.asarray(Image.open(heroine_face_fixes.RAW).convert("RGB"), np.float32) / 255
_hr, _hc, _hp, _hfw = HEAD_TEXELS
_hin = np.zeros((HSIZE, HSIZE), bool)
_hin[HSIZE - 1 - _hr, _hc] = True
_hr = HSIZE - 1 - _hr
_drop = (_raw[_hr, _hc] - _fixed[_hr, _hc]) @ np.array([0.3, 0.59, 0.11])
_nost = (((_hp[:, 0]) / 0.024) ** 2 + ((_hp[:, 2] - (_nose[2] - 0.012)) / 0.016) ** 2 + ((_hp[:, 1] - (_nose[1] + 0.022)) / 0.03) ** 2) < 1
_back = (_drop > 0.06) & ~_nost
_fixed[_hr[_back], _hc[_back]] = _raw[_hr[_back], _hc[_back]]
print("NOSE shading kept to his nostrils: %d texels given back" % _back.sum())
# All of it one skin with his body's (hero_male_skin.one_tone): his face and
# ears keep some warmth of their own, and all their features. (Krea painted
# his face olive beside his tan neck, and MakeHuman's paint is pinker.)
_fixed[_hr, _hc] = np.clip(hero_male_skin.no_green(hero_male_skin.one_tone(_fixed[_hr, _hc], _hp, NECK_TONE, _hfw, keep=0.3), _hp), 0, 1)
_fixed = pad(_fixed, _hin)
Image.fromarray((_fixed * 255 + 0.5).astype(np.uint8)).save(hpath, quality=92)
print("HEAD toned to his neck's %s" % np.round(NECK_TONE, 3))
# (His brows' paint as it is now, the colour the game dyes from.)
_bp = np.median(_fixed[_hr, _hc][BROW_T > 0.7], 0)
print("BROWS painted #%02x%02x%02x (People.HisBrowPaint)" % tuple(int(round(255 * v)) for v in np.clip(_bp, 0, 1)))
for _im in bpy.data.images:
    if bpy.path.abspath(_im.filepath) == hpath:
        if _im.packed_file:
            _im.unpack(method="REMOVE")
        _im.reload()


# ---------------------------------------------------------------- written --
for o in [hm] + list(proxies.values()) + [o for o in bpy.data.objects if o.name.startswith("CheckCam")]:
    bpy.data.objects.remove(o, do_unlink=True)
for m in him.modifiers:
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


# (MakeHuman's layout is the face tool's, not the game's.)
head.data.uv_layers.remove(head.data.uv_layers["mh"])
_game_parts = [o for o in parts if not (o.name == "HeroBrows" and os.path.exists(FACE_PAINT))]
# (Its paint as WebP: his three 4K maps as PNG made a 38 MB file.)
# (His tangents written with him, as Blender baked his relief against
# them: Godot's own, made afresh from his split normals and seams, turned
# some of his small islands' relief into hard-edged patches.)
export([him, head] + _game_parts, os.path.join(ART, "hero.glb"), export_format="GLB", export_image_format="WEBP", export_image_quality=92,
       export_tangents=True)
print("WRITTEN", OUT_BLEND, "and", ART)
