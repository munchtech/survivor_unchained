"""The hero (the man the player can be), made anew from MakeHuman's CC0 man:
one mesh from his crown to his soles, his own head with no graft, on the
game's skeleton. (Judge j0, 12 October 2026: the TRELLIS sculpt read as a
stage bodybuilder with a grafted, older face; rebuilt as an athletic
heavyweight, the sculpt kept only as a donor of surface detail.)

    blender -b --python tools/assets/hero_male.py -- <donor.glb> <ual.glb> <out.blend> <art dir>

  1. The man: MakeHuman's (MPFB, system assets only, CC0) at the build
     BUILD names, his face FACE, his neck NECK; scaled to HEIGHT.
  2. Stood in a T (his arms out, palms down), as the heroine and the game's
     skeleton stand, by his own rig's weights.
  3. The donor (the old hero.glb, the TRELLIS sculpt on AccuRIG's rig, in
     the same T): half its volume where it helps (VOLUME: chest, shoulders,
     arms, thighs, calves; its misplacement taken out, only its girth kept),
     and its fine detail (its relief, against a smoothed copy of itself)
     baked onto his own UVs where DETAIL says (his stomach, flanks, arms,
     the front and outside of his thighs, his calves).
  4. Smoothed once (Catmull-Clark) for a hero's silhouette.
  5. The game's skeleton (UAL) laid on his joints and his weights folded
     onto it, as build_heroine.py does.

HM_STOP=body writes his body alone (MakeHuman's skin, his relief) to
<art dir>/hero.glb for a first look in lookdev.
"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
import scipy.sparse as sp
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from scipy.spatial import ConvexHull, cKDTree

sys.stdout.reconfigure(line_buffering=True)
ARGS = sys.argv[sys.argv.index("--") + 1:]
DONOR, UAL, OUT_BLEND, ART = [os.path.abspath(a) for a in ARGS[:4]]
STOP = os.environ.get("HM_STOP", "")
TEXDIR = os.path.join(os.path.dirname(OUT_BLEND), "hero_tex")
os.makedirs(TEXDIR, exist_ok=True)
HEIGHT = 1.98          # crown to sole (she is 1.87)
TEX = 4096

from bl_ext.user_default.mpfb.services.humanservice import HumanService  # noqa: E402
from bl_ext.user_default.mpfb.services.targetservice import TargetService  # noqa: E402

USER = os.path.join(bpy.utils.user_resource("EXTENSIONS"), ".user", "user_default", "mpfb", "data")
TDIR = os.path.join(bpy.utils.user_resource("EXTENSIONS"), "user_default", "mpfb", "data", "targets")

# An athletic heavyweight about thirty: a rugby forward's or a decathlete's
# build at 8-10% fat, not a stage bodybuilder's (j0).
MACROS = {"gender": 1.0, "age": 0.5625, "muscle": float(os.environ.get("HM_MUSCLE", 0.95)),
          "weight": float(os.environ.get("HM_WEIGHT", 0.58)), "proportions": 1.0, "height": 0.75,
          "cupsize": 0.5, "firmness": 0.5, "race": {"african": 0.0, "asian": 0.0, "caucasian": 1.0}}
# Past the sliders: a clear V from broad shoulders to a narrow waist, a full
# chest, strong arms and forearms, a hard stomach, thick thighs and calves,
# firm square glutes. (Each "X-" is both sides.)
BUILD = {"torso-vshape-incr": 0.8, "torso-muscle-pectoral-incr": 0.75, "torso-muscle-dorsi-incr": 0.35,
         "measure-shoulder-dist-incr": 0.5, "measure-waist-circ-decr": 0.1, "stomach-tone-incr": 1.0,
         "X-upperarm-muscle-incr": 1.0, "measure-upperarm-circ-incr": 0.5, "X-upperarm-shoulder-muscle-incr": 0.6,
         "X-lowerarm-muscle-incr": 0.8, "measure-upperarm-length-decr": 0.3, "measure-lowerarm-length-decr": 0.3,
         "X-upperleg-muscle-incr": 0.9, "measure-thigh-circ-incr": 0.5, "X-lowerleg-muscle-incr": 0.6,
         "buttocks-volume-incr": 0.15, "X-hand-scale-incr": 0.25, "pelvis-tone-incr": 0.6}
# A wrestler's neck, near as wide as his jaw, so his head never reads small.
NECK = {"measure-neck-circ-incr": 0.7, "neck-scale-horiz-incr": 0.45, "measure-neck-height-decr": 0.35}
# His face (j0: thirty to thirty-five, handsome and rugged; a wider, squarer
# jaw with a clear angle, a strong chin, cheeks half as hollow as before, a
# straight heavy brow, fuller lips).
FACE = {"head-square": 0.2, "head-oval": 0.2, "head-scale-vert-decr": 0.15, "forehead-scale-vert-decr": 0.25, "head-fat-decr": 0.2,
        "head-back-scale-depth-incr": 0.2,
        "chin-width-incr": 0.55, "chin-bones-incr": 1.0, "chin-prominent-incr": 0.35, "chin-height-incr": 0.05, "chin-cleft-incr": 0.2,
        "X-cheek-bones-incr": 0.55, "X-cheek-volume-decr": 0.25, "forehead-nubian-incr": 0.35,
        "eyebrows-trans-down": 0.3, "eyebrows-trans-forward": 0.45, "eyebrows-angle-down": 0.1,
        "X-eye-height2-decr": 0.1, "X-eye-push1-in": 0.2,
        "nose-hump-incr": 0.1, "nose-width1-incr": 0.2, "nose-scale-depth-incr": 0.1,
        "mouth-scale-horiz-incr": 0.15, "mouth-lowerlip-volume-incr": 0.4, "mouth-upperlip-volume-incr": 0.2}
SKIN = os.path.join(USER, "skins", "young_caucasian_male", "young_lightskinned_male_diffuse.png")


def active(o):
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o


def smooth01(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def sides(names):
    out = []
    for n in names:
        out += [n.replace("X-", "l-", 1), n.replace("X-", "r-", 1)] if n.startswith("X-") else [n]
    return out


def adjacency(n, faces):
    e = []
    for f in faces:
        for a, b in zip(f, f[1:] + f[:1]):
            e.append((a, b))
    e = np.array(e)
    A = sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)).tocsr()
    A = ((A + A.T) > 0).astype(float)
    return sp.diags(1 / np.maximum(np.asarray(A.sum(1)).ravel(), 1)) @ A


def vnormals(V, faces):
    N = np.zeros_like(V)
    for f in faces:
        p = V[f]
        n = np.cross(p[1] - p[0], p[-1] - p[0])
        N[f] += n
    return N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)


# ------------------------------------------------------------ the man --
TARGET = {}
for _root, _, _files in os.walk(TDIR):
    for _f in _files:
        if _f.endswith(".target.gz") and "expression" not in _root:
            TARGET.setdefault(_f[:-10], os.path.join(_root, _f))
hm = HumanService.create_human(mask_helpers=True, detailed_helpers=True, extra_vertex_groups=True, feet_on_ground=True,
                               scale=0.1, macro_detail_dict=MACROS)
for _set in (BUILD, NECK, FACE):
    for _t, _v in _set.items():
        for _n in sides([_t]):
            TargetService.load_target(hm, TARGET[_n], weight=_v)
HumanService.add_builtin_rig(hm, "game_engine")
mh_arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
eyes_px = HumanService.add_mhclo_asset(os.path.join(USER, "eyes", "high-poly", "high-poly.mhclo"), hm, asset_type="eyes",
                                       subdiv_levels=0, material_type="NONE", set_up_rigging=False, interpolate_weights=False,
                                       import_subrig=False, import_weights=False)
for mo in hm.modifiers:
    mo.show_viewport = False
bpy.context.view_layer.update()


def grab(o):
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
_bg = hm.vertex_groups["body"].index
_inbody = np.array([any(g.group == _bg for g in v.groups) for v in hm.data.vertices])
keep_f = [i for i, f in enumerate(MF) if _inbody[f].all()]
used = np.unique(np.concatenate([MF[i] for i in keep_f]))
remap = -np.ones(len(MV), int)
remap[used] = np.arange(len(used))
V = MV[used].copy()
F = [list(remap[MF[i]]) for i in keep_f]
U = [MU[i] for i in keep_f]
# His weights, by his rig's bones (MakeHuman's game_engine: the game's names).
BONES = [b.name for b in mh_arm.data.bones]
BI = {n: i for i, n in enumerate(BONES)}
W = np.zeros((len(V), len(BONES)))
_gname = {g.index: g.name for g in hm.vertex_groups}
for v in hm.data.vertices:
    if remap[v.index] < 0:
        continue
    for g in v.groups:
        n = _gname[g.group]
        if n in BI:
            W[remap[v.index], BI[n]] = g.weight
W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
EV = grab(eyes_px)[0]
# Joints, in the world.
_mw = mh_arm.matrix_world
JH = {b.name: np.array((_mw @ b.head_local)[:]) for b in mh_arm.data.bones}
JT = {b.name: np.array((_mw @ b.tail_local)[:]) for b in mh_arm.data.bones}
PARENT = {b.name: (b.parent.name if b.parent else None) for b in mh_arm.data.bones}

# His height: crown to sole, his feet on the ground, his middle on the axis.
k = HEIGHT / np.ptp(V[:, 2])
o_ = np.array([-(V[:, 0].max() + V[:, 0].min()) / 2, 0, -V[:, 2].min()])


def fit(P):
    return (P + o_) * k


V, EV = fit(V), fit(EV)
JH = {n: fit(p[None])[0] for n, p in JH.items()}
JT = {n: fit(p[None])[0] for n, p in JT.items()}
print("MAN", len(V), "points,", len(F), "faces, %.3f m" % np.ptp(V[:, 2]))

# ------------------------------------------------------------- in a T --
# Each arm turned out level, its forearm and hand straight along it (palms
# down), by linear blend skinning on his own weights; his head untouched.
POSE = {}            # bone -> (3x3 world turn, pivot), parents first
LIN = {n: np.eye(3) for n in BONES}
OFF = {n: np.zeros(3) for n in BONES}


def depth(n):
    d = 0
    while PARENT[n]:
        n, d = PARENT[n], d + 1
    return d


def rot_between(a, b):
    a, b = a / np.linalg.norm(a), b / np.linalg.norm(b)
    v, c = np.cross(a, b), float(a @ b)
    if np.linalg.norm(v) < 1e-9:
        return np.eye(3)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx * (1 / (1 + c))


AIM = {}
for s, x in (("l", 1.0), ("r", -1.0)):
    # (MakeHuman's "l" is the figure's left, on +x.)
    if JH[f"upperarm_{s}"][0] * x < 0:
        x = -x
    AIM[f"upperarm_{s}"] = (f"lowerarm_{s}", np.array([x, 0, 0]))
    AIM[f"lowerarm_{s}"] = (f"hand_{s}", np.array([x, 0, 0]))
    AIM[f"hand_{s}"] = (f"middle_01_{s}", np.array([x, 0, 0]))
for n in sorted(BONES, key=depth):
    p = PARENT[n]
    L, O = (LIN[p], OFF[p]) if p else (np.eye(3), np.zeros(3))
    if n in AIM:
        child, tgt = AIM[n]
        cur = L @ (JH[child] - JH[n])
        R = rot_between(cur, tgt)
        h = L @ JH[n] + O
        # x -> R (L x + O - h) + h
        LIN[n], OFF[n] = R @ L, R @ (O - h) + h
    else:
        LIN[n], OFF[n] = L, O
V0 = V.copy()
V = np.zeros_like(V0)
for b in range(len(BONES)):
    w = W[:, b]
    m = w > 0
    if m.any():
        V[m] += w[m, None] * (V0[m] @ LIN[BONES[b]].T + OFF[BONES[b]])
JH2 = {n: (LIN[PARENT[n]] @ JH[n] + OFF[PARENT[n]]) if PARENT[n] else JH[n] for n in BONES}
JT2 = {n: LIN[n] @ JT[n] + OFF[n] for n in BONES}
JH, JT = JH2, JT2
print("T-POSE: hands at %s" % np.round([JH["hand_l"], JH["hand_r"]], 3).tolist())

# ------------------------------------------------------------ the donor --
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=DONOR)
_new = [o for o in bpy.data.objects if o not in before]
donor = next(o for o in _new if o.type == "MESH" and o.name == "Hero")
for o in _new:
    o.name = "donor_" + o.name
DV = np.array([(donor.matrix_world @ v.co)[:] for v in donor.data.vertices])
DF = [list(p.vertices) for p in donor.data.polygons]
# Laid onto his bones: each of the donor's bones carried onto his (its
# head onto his, turned along his, stretched along its length only, so its
# girth is kept), its skin following by its own weights. Its arms are
# shorter than his and its legs set wider; its muscles land on his.
darm = next(o for o in _new if o.type == "ARMATURE")
_dmw = darm.matrix_world
DJH = {b.name: np.array((_dmw @ b.head_local)[:]) for b in darm.data.bones}
DJT = {b.name: np.array((_dmw @ b.tail_local)[:]) for b in darm.data.bones}
DPAR = {b.name: (b.parent.name if b.parent else None) for b in darm.data.bones}
_PREF = ("lowerarm", "hand", "calf", "foot", "ball", "spine", "neck", "Head", "middle_01", "upperarm")


def seg_end(name, heads, tails, kids):
    for pref in _PREF:
        c = next((k for k in kids.get(name, []) if k.startswith(pref) and k in heads), None)
        if c:
            return heads[c]
    return tails[name]


_U = lambda n: "Head" if n == "head" else n
_dkids, _mk = {}, {}
for n, pnt in DPAR.items():
    _dkids.setdefault(pnt, []).append(n)
for n, pnt in PARENT.items():
    _mk.setdefault(_U(pnt) if pnt else None, []).append(_U(n))
_MJH = {_U(n): p for n, p in JH.items()}
_MJT = {_U(n): p for n, p in JT.items()}
XF = {}
for n in DJH:
    if n not in _MJH:
        continue
    hd, cd = DJH[n], seg_end(n, DJH, DJT, _dkids)
    hm_, cm = _MJH[n], seg_end(n, _MJH, _MJT, _mk)
    a_, b_ = cd - hd, cm - hm_
    sc_ = np.linalg.norm(b_) / max(np.linalg.norm(a_), 1e-6)
    u = a_ / max(np.linalg.norm(a_), 1e-6)
    M = rot_between(a_, b_) @ (np.eye(3) + (sc_ - 1) * np.outer(u, u))
    XF[n] = (M, hm_ - M @ hd)


def xf_of(n):
    while n and n not in XF:
        n = DPAR.get(n)
    return XF.get(n, (np.eye(3), np.zeros(3)))


_dn = {g.index: g.name for g in donor.vertex_groups}
_DW = {}
for v in donor.data.vertices:
    for g in v.groups:
        if g.weight > 0:
            _DW.setdefault(_dn[g.group], []).append((v.index, g.weight))
_acc = np.zeros_like(DV)
_wsum = np.zeros(len(DV))
for n, lst in _DW.items():
    idx = np.array([i for i, _ in lst])
    w = np.array([x for _, x in lst])
    M, t = xf_of(n)
    _acc[idx] += w[:, None] * (DV[idx] @ M.T + t)
    _wsum[idx] += w
DV = np.where(_wsum[:, None] > 1e-6, _acc / np.maximum(_wsum[:, None], 1e-6), DV)
print("DONOR laid on his bones: %d bones" % len(XF))
print("DONOR", len(DV), "points, %.3f m; arms' reach %.3f (his %.3f)" % (np.ptp(DV[:, 2]), np.ptp(DV[:, 0]), np.ptp(V[:, 0])))
dbvh = BVHTree.FromPolygons([tuple(p) for p in DV], DF)

# Where his body takes the donor's volume (half of it) and its detail.
N = vnormals(V, F)
A = adjacency(len(V), F)


def wsum(*names):
    return sum(W[:, BI[n]] for n in names if n in BI)


z = V[:, 2]
front = smooth01((-N[:, 1] - 0.05) / 0.4)
arms = wsum("upperarm_l", "upperarm_r", "lowerarm_l", "lowerarm_r")
delts = wsum("clavicle_l", "clavicle_r") * smooth01((np.abs(V[:, 0]) - 0.12) / 0.06)
chest = wsum("spine_03", "clavicle_l", "clavicle_r") * front * smooth01((z - (JH["spine_03"][2] - 0.08)) / 0.05)
thighs = wsum("thigh_l", "thigh_r") * (1 - smooth01((N[:, 1] - 0.2) / 0.4) * smooth01((z - (JH["thigh_l"][2] - 0.25)) / 0.08))
calves = wsum("calf_l", "calf_r")
VOLUME = np.clip(arms + delts + chest + thighs + calves, 0, 1)
abdomen = wsum("spine_01", "spine_02", "pelvis", "spine_03") * smooth01((-N[:, 1] + 0.35) / 0.5) \
    * smooth01((z - (JH["pelvis"][2] - 0.12)) / 0.06)
DETAIL = np.clip(VOLUME + abdomen, 0, 1)
for _ in range(4):
    VOLUME, DETAIL = A @ VOLUME, A @ DETAIL
for _hold in ("head", "neck_01", "hand_l", "hand_r", "foot_l", "foot_r", "ball_l", "ball_r"):
    VOLUME *= 1 - np.clip(W[:, BI[_hold]] * 2, 0, 1)
    DETAIL *= 1 - np.clip(W[:, BI[_hold]] * 2, 0, 1)

d = np.zeros_like(V)
ok = np.zeros(len(V), bool)
for i in np.nonzero(VOLUME > 1e-3)[0]:
    hit = dbvh.find_nearest(Vector(V[i]), 0.06)
    if hit[0] is not None:
        d[i] = np.array(hit[0][:]) - V[i]
        ok[i] = True
# Only the girth: the donor's misplacement (its arms a little higher, its
# chest a little forward) is what is common to all of a bone's skin, its
# mean there (all round a limb, so its girth cancels out of it); what is
# left, along his normals, is volume.
_okf = ok.astype(float)
shift = W @ ((W.T @ (d * _okf[:, None])) / np.maximum(W.T @ _okf, 1e-6)[:, None])
s = ((d - shift) * N).sum(1) * ok
if os.environ.get("HM_DEBUG"):
    for _b in ("thigh_l", "calf_l", "upperarm_l", "lowerarm_l", "spine_03", "spine_02"):
        _m = W[:, BI[_b]] > 0.7
        print("DBG %s n=%d ok=%.2f mean d %s, d.N %.1f mm, shift %s, s %.1f mm, N.outward %.2f" % (
            _b, _m.sum(), ok[_m].mean(), np.round(1000 * d[_m & ok].mean(0), 1), 1000 * (d * N).sum(1)[_m & ok].mean(),
            np.round(1000 * shift[_m].mean(0), 1), 1000 * s[_m & ok].mean(),
            ((V[_m] - V[_m].mean(0)) * N[_m]).sum(1).mean() * 100))
for _ in range(6):
    s = A @ s
GAIN = float(os.environ.get("HM_GAIN", 0.0))
V = V + N * (s * VOLUME * GAIN)[:, None]
print("VOLUME from the donor: mean %.1f mm, max %.1f mm, min %.1f mm over %d points" % (
    1000 * (s * VOLUME * GAIN)[VOLUME > 0.5].mean(), 1000 * (s * VOLUME * GAIN).max(), 1000 * (s * VOLUME * GAIN).min(),
    (VOLUME > 0.5).sum()))


# --------------------------------------------------------- his measures --
_E = np.unique(np.sort(np.array([(f[i], f[(i + 1) % len(f)]) for f in F for i in range(len(f))]), 1), axis=0)


def section(axis, c, keep=None):
    """Where his surface crosses the plane (axis = c): the edges' crossings."""
    a, b = V[_E[:, 0]], V[_E[:, 1]]
    da, db = a[:, axis] - c, b[:, axis] - c
    m = (da * db) < 0
    t = da[m] / (da[m] - db[m])
    P = a[m] + (b[m] - a[m]) * t[:, None]
    return P[keep(P)] if keep is not None else P


def hull(P, dims):
    return ConvexHull(P[:, dims]).area if len(P) > 3 else 0.0


def girth_z(z0, xsign=0, xmin=0.0):
    return hull(section(2, z0, (lambda P: P[:, 0] * xsign > xmin) if xsign else None), [0, 1])


def girth_x(x0):
    return hull(section(0, x0), [1, 2])


def measures():
    sh, el, wr = JH["upperarm_l"], JH["lowerarm_l"], JH["hand_l"]
    knee, ank, hip = JH["calf_l"], JH["foot_l"], JH["thigh_l"]
    side = np.sign(sh[0])
    arm = max(girth_x(sh[0] + t * (el[0] - sh[0])) for t in np.linspace(0.35, 0.75, 9))
    fore = max(girth_x(el[0] + t * (wr[0] - el[0])) for t in np.linspace(0.1, 0.4, 7))
    neck = min(girth_z(JH["neck_01"][2] + t * (JH["head"][2] - JH["neck_01"][2])) for t in np.linspace(0.2, 0.8, 7))
    calf = max(girth_z(knee[2] + t * (ank[2] - knee[2]), side) for t in np.linspace(0.2, 0.5, 7))
    thigh = max(girth_z(hip[2] + t * (knee[2] - hip[2]), side, 0.02) for t in np.linspace(0.15, 0.35, 5))
    kneeg = min(girth_z(knee[2] + t * (hip[2] - knee[2]), side) for t in np.linspace(0.02, 0.15, 5))
    waist = min(girth_z(z0) for z0 in np.linspace(JH["spine_01"][2] - 0.02, JH["spine_02"][2], 9))
    _cx = abs(sh[0]) - 0.02
    chest = max(hull(section(2, z0, lambda P: np.abs(P[:, 0]) < _cx), [0, 1]) for z0 in np.linspace(JH["spine_03"][2], sh[2] - 0.06, 7))
    print("JOINTS z: " + ", ".join("%s %.3f" % (n, JH[n][2]) for n in ("pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "head",
                                                                         "upperarm_l", "thigh_l", "calf_l", "foot_l")))
    _sh = V[(np.abs(V[:, 2] - (sh[2] - 0.03)) < 0.02)]
    width = np.ptp(_sh[np.abs(_sh[:, 0]) < abs(sh[0]) + 0.08][:, 0])
    print("MEASURES cm: upper arm %.1f, forearm %.1f, neck %.1f, calf %.1f, thigh %.1f, knee %.1f, waist %.1f, chest(armpits) %.1f,"
          " shoulder width %.1f; arm/neck %.2f, calf/neck %.2f, thigh/knee %.2f, shoulder width/waist width %.2f" % tuple(
              (100 * np.array([arm, fore, neck, calf, thigh, kneeg, waist, chest, width])).tolist() + [
                  arm / max(neck, 1e-6), calf / max(neck, 1e-6), thigh / max(kneeg, 1e-6), width / max(waist / math.pi, 1e-6)]))


measures()
if STOP == "shape":
    # (The donor measured the same way, at his joints, for comparison.)
    _keepV, _keepE = V, _E
    V = DV
    _E = np.unique(np.sort(np.array([(f[i], f[(i + 1) % len(f)]) for f in DF for i in range(len(f))]), 1), axis=0)
    print("DONOR:")
    measures()
    V, _E = _keepV, _keepE
print("VOLUME: the donor found within 6 cm of %d of %d points" % (ok.sum(), (VOLUME > 1e-3).sum()))
if STOP == "shape":
    raise SystemExit

# ------------------------------------------------------------- smoothed --
def mesh_object(name, P, faces, uvs=None, mats=()):
    me = bpy.data.meshes.new(name)
    me.from_pydata(P.tolist(), [], [list(map(int, f)) for f in faces])
    if uvs is not None:
        uv = me.uv_layers.new(name="UVMap")
        uv.data.foreach_set("uv", np.concatenate(uvs).ravel())
    for m in mats:
        me.materials.append(m)
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    return o


body = mesh_object("Hero", V, F, U)
for b in range(len(BONES)):
    m = np.nonzero(W[:, b] > 1e-4)[0]
    if len(m):
        g = body.vertex_groups.new(name=BONES[b])
        for i in m:
            g.add([int(i)], float(W[i, b]), "REPLACE")
for p in body.data.polygons:
    p.use_smooth = True
active(body)
sub = body.modifiers.new("Smooth", "SUBSURF")
sub.levels = sub.render_levels = 1
sub.uv_smooth = "PRESERVE_BOUNDARIES"
bpy.ops.object.modifier_apply(modifier="Smooth")
print("SMOOTHED to", len(body.data.vertices), "points,", sum(len(p.vertices) - 2 for p in body.data.polygons), "triangles")

# ---------------------------------------------------- the donor's detail --
# Baked twice onto his UVs: the donor with its relief, and the donor
# smoothed with none. The turn from the second to the first is the detail
# alone (its muscles' edges, veins, creases), laid on his own surface.
dmat = donor.data.materials[0] if donor.data.materials else None
smooth_d = donor.copy()
smooth_d.data = donor.data.copy()
bpy.context.scene.collection.objects.link(smooth_d)
for mo in list(donor.modifiers) + list(smooth_d.modifiers):
    (donor if mo.id_data == donor else smooth_d).modifiers.remove(mo)
donor.parent = None
smooth_d.parent = None
donor.matrix_world = Matrix.Identity(4)
smooth_d.matrix_world = Matrix.Identity(4)
for o in (donor, smooth_d):
    o.data.vertices.foreach_set("co", DV.ravel())
    o.data.update()
_SA = adjacency(len(DV), DF)
SV = DV.copy()
for _ in range(80):
    SV = SV + 0.6 * (_SA @ SV - SV)
    SV = SV - 0.62 * (_SA @ SV - SV)
smooth_d.data.vertices.foreach_set("co", SV.ravel())
smooth_d.data.update()
flat = bpy.data.materials.new("flat")
flat.use_nodes = True
smooth_d.data.materials.clear()
smooth_d.data.materials.append(flat)
# (Every other donor object out of the way of the rays.)
for o in _new:
    if o not in (donor,) and o.type == "MESH":
        o.hide_render = True
        o.hide_set(True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 1
bk = sc.render.bake
bk.use_selected_to_active = True
bk.cage_extrusion = 0.04
bk.max_ray_distance = 0.08
bk.margin = 16
bk.normal_space = "TANGENT"


def bake_normals(src, name):
    img = bpy.data.images.new(name, TEX, TEX, float_buffer=True)
    img.colorspace_settings.name = "Non-Color"
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    node = mat.node_tree.nodes.new("ShaderNodeTexImage")
    node.image = img
    mat.node_tree.nodes.active = node
    body.data.materials.clear()
    body.data.materials.append(mat)
    for o in (donor, smooth_d):
        o.hide_render = o is not src
        o.hide_set(o is not src)
    bpy.ops.object.select_all(action="DESELECT")
    src.select_set(True)
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.bake(type="NORMAL")
    a = np.empty(TEX * TEX * 4, np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(TEX, TEX, 4)[..., :3] * 2 - 1


na = bake_normals(donor, "nA")
nb = bake_normals(smooth_d, "nB")
print("BAKED the donor's normals twice")


# The turn taking nb to na, applied to straight up (in his own tangent space).
def turn_up(a, b):
    a = a / np.maximum(np.linalg.norm(a, axis=-1, keepdims=True), 1e-6)
    b = b / np.maximum(np.linalg.norm(b, axis=-1, keepdims=True), 1e-6)
    v = np.cross(b, a)
    c = (a * b).sum(-1, keepdims=True)
    up = np.zeros_like(a)
    up[..., 2] = 1
    # Rodrigues: R up = up c + (v x up) + v (v.up) / (1 + c)
    return up * c + np.cross(v, up) + v * v[..., 2:3] / np.maximum(1 + c, 1e-3)


det = turn_up(na, nb)
# Only where both bakes found the donor (a miss leaves the image black), and
# his surface and the smoothed donor's agree within 50 degrees (elsewhere
# the donor's skin is not his: its cut neck, its fingers, a fold).
_nbn = nb / np.maximum(np.linalg.norm(nb, axis=-1, keepdims=True), 1e-6)
valid = ((na[..., 2] > 0) & (nb[..., 2] > 0) & (_nbn[..., 2] > 0.64)).astype(np.float32)
del _nbn
print("DETAIL found over %d%% of the baked texels" % (100 * valid.sum() / max(((na[..., 2] > -0.99) | (nb[..., 2] > -0.99)).sum(), 1)))
# His DETAIL mask, per texel, from his points through his UVs (the subdivided
# body's points carry it by the nearest original point).
_sv = np.array([v.co[:] for v in body.data.vertices])
_, _near = cKDTree(V).query(_sv)
dmask = DETAIL[_near]
from scipy import ndimage  # noqa: E402


def raster_mask(me, val, size):
    """A per-point value painted into UV space (each triangle flat-filled with
    its corners' mean: enough for a soft mask)."""
    img = np.zeros((size, size), np.float32)
    cnt = np.zeros((size, size), np.float32)
    uvd = me.uv_layers.active.data
    me.calc_loop_triangles()
    for t in me.loop_triangles:
        uv = np.array([uvd[li].uv[:] for li in t.loops]) * (size - 1)
        val3 = float(np.mean([val[vi] for vi in t.vertices]))
        x0, y0 = np.floor(uv.min(0)).astype(int)
        x1, y1 = np.ceil(uv.max(0)).astype(int)
        img[y0:y1 + 1, x0:x1 + 1] += val3
        cnt[y0:y1 + 1, x0:x1 + 1] += 1
    return img / np.maximum(cnt, 1e-6)


m_ = raster_mask(body.data, dmask, 1024)
m_ = ndimage.zoom(ndimage.gaussian_filter(m_, 2), TEX / 1024, order=1)
# (the misses eased out over a few millimetres, not cut)
m_ = (m_ * ndimage.gaussian_filter(ndimage.grey_erosion(valid, size=5), 3))[:, :, None]
del valid
up = np.zeros_like(det)
up[..., 2] = 1
DSTR = float(os.environ.get("HM_DETAIL", 1.0))
nrm = up * (1 - m_ * DSTR) + det * (m_ * DSTR)
nrm /= np.maximum(np.linalg.norm(nrm, axis=-1, keepdims=True), 1e-6)
relief = bpy.data.images.new("hero_relief", TEX, TEX)
relief.colorspace_settings.name = "Non-Color"
relief.pixels.foreach_set(np.concatenate([nrm * 0.5 + 0.5, np.ones((TEX, TEX, 1), np.float32)], -1).astype(np.float32).ravel())
relief.filepath_raw = os.path.join(TEXDIR, "hero_relief.png")
relief.file_format = "PNG"
relief.save()
_pv = relief.copy()
_pv.scale(1024, 1024)
_pv.filepath_raw = os.path.join(TEXDIR, "hero_relief_preview.png")
_pv.save()
print("RELIEF written, detail over %d%% of his texels" % (100 * (m_ > 0.5).mean()))

for o in _new:
    bpy.data.objects.remove(o, do_unlink=True)
bpy.data.objects.remove(smooth_d, do_unlink=True)

# ---------------------------------------------------- the game's skeleton --
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=UAL)
q = next(o for o in bpy.data.objects if o not in before and o.type == "ARMATURE")
for o in [o for o in bpy.data.objects if o not in before and o != q]:
    bpy.data.objects.remove(o)
q.animation_data_clear()
active(q)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
MHN = {"Head": "head"}
CCJ = {u: (Vector(JH[MHN.get(u, u)]), Vector(JT[MHN.get(u, u)])) for u in [b.name for b in q.data.bones] if MHN.get(u, u) in JH}
JOINT = {u: u for u in CCJ}
bpy.ops.object.mode_set(mode="POSE")
for pb in q.pose.bones:
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = (1, 0, 0, 0)


def bdepth(b):
    d = 0
    while b.parent:
        b, d = b.parent, d + 1
    return d


CHILD = {}
for b in q.data.bones:
    if b.name in JOINT:
        kids = [c for c in b.children if c.name in JOINT]
        pick = None
        for pref in ("lowerarm", "hand", "calf", "foot", "ball", "spine", "neck", "Head", "middle_01", "upperarm"):
            pick = next((c for c in kids if c.name.startswith(pref)), None)
            if pick:
                break
        if pick is None and kids:
            pick = kids[0]
        CHILD[b.name] = pick.name if pick else None
turned = 0
for b in sorted(q.data.bones, key=bdepth):
    if b.name not in JOINT or b.name in ("root",):
        continue
    head = CCJ[b.name][0]
    tgt = (CCJ[CHILD[b.name]][0] - head) if CHILD.get(b.name) else (CCJ[b.name][1] - head)
    if tgt.length < 1e-5:
        continue
    bpy.context.view_layer.update()
    pb = q.pose.bones[b.name]
    cur = (q.matrix_world @ pb.tail) - (q.matrix_world @ pb.head)
    rot = cur.normalized().rotation_difference(tgt.normalized())
    world_new = rot.to_matrix() @ pb.matrix.to_3x3()
    if pb.parent:
        rel = pb.parent.bone.matrix_local.to_3x3().inverted() @ pb.bone.matrix_local.to_3x3()
        basis = (pb.parent.matrix.to_3x3() @ rel).inverted() @ world_new
    else:
        basis = pb.bone.matrix_local.to_3x3().inverted() @ world_new
    pb.rotation_quaternion = basis.to_quaternion()
    turned += 1
bpy.context.view_layer.update()
bpy.ops.pose.armature_apply(selected=False)
bpy.ops.object.mode_set(mode="EDIT")
eb = q.data.edit_bones
for e in eb:
    e.use_connect = False
moved = 0
for e in sorted(eb, key=lambda e: len(e.parent_recursive)):
    if e.name not in JOINT or e.name in ("root",):
        continue
    head = CCJ[e.name][0]
    dvec = e.tail - e.head
    ln = dvec.length
    if CHILD.get(e.name):
        ln = (CCJ[CHILD[e.name]][0] - head).length or ln
    roll = e.roll
    e.head = head
    e.tail = head + dvec.normalized() * ln
    e.roll = roll
    moved += 1
for e in eb:
    if (e.name.endswith("_leaf_l") or e.name.endswith("_leaf_r")) and e.parent:
        dvec = e.tail - e.head
        e.head = e.parent.tail
        e.tail = e.parent.tail + dvec
bpy.ops.object.mode_set(mode="OBJECT")
print("SKELETON: %d bones turned, %d joints placed" % (turned, moved))
# His weights onto its bones, four at most.
for g in body.vertex_groups:
    if g.name in MHN.values():
        g.name = next(u for u, m in MHN.items() if m == g.name)
for g in list(body.vertex_groups):
    if g.name not in q.data.bones:
        print("  (unweighted group dropped:", g.name, ")")
        body.vertex_groups.remove(g)
active(body)
bpy.ops.object.vertex_group_limit_total(group_select_mode="ALL", limit=4)
bpy.ops.object.vertex_group_normalize_all(group_select_mode="ALL", lock_active=False)
body.parent = q
body.modifiers.new("Armature", "ARMATURE").object = q
q.name = "Armature"

# -------------------------------------------------------------- his eyes --
_eye_faces = [list(p.vertices) for p in eyes_px.data.polygons]
_euv = eyes_px.data.uv_layers.active.data
_eye_uv = [np.array([_euv[li].uv[:] for li in p.loop_indices]) for p in eyes_px.data.polygons]


def textured(name, path, normal=None, rough=0.55, alpha=False):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(path, check_existing=True)
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    if alpha:
        nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    bsdf.inputs["Roughness"].default_value = rough
    if normal is not None:
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt_ = nt.nodes.new("ShaderNodeTexImage")
        nt_.image = normal
        nt.links.new(nt_.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


eyes = mesh_object("HeroEyes", EV, _eye_faces, _eye_uv,
                   [textured("eyes", os.path.join(ART, "head_tex", "brown_eye.png"), rough=0.1)])
eyes.parent = q
eyes.vertex_groups.new(name="Head").add(list(range(len(EV))), 1.0, "REPLACE")
eyes.modifiers.new("Armature", "ARMATURE").object = q

body.data.materials.clear()
body.data.materials.append(textured("skin", SKIN, relief))
_gone = [o.name for o in bpy.data.objects if o.parent in (hm, mh_arm) and o not in (body, eyes)] + [hm.name, mh_arm.name, eyes_px.name]
for n in _gone:
    if n in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
print("SAVED", OUT_BLEND)

if STOP == "body":
    bpy.ops.object.select_all(action="DESELECT")
    for o in (q, body, eyes):
        o.select_set(True)
    bpy.context.view_layer.objects.active = q
    bpy.ops.export_scene.gltf(filepath=os.path.join(ART, "hero.glb"), use_selection=True, export_skins=True, export_animations=False,
                              export_yup=True, export_format="GLB", export_image_format="WEBP", export_image_quality=92,
                              export_tangents=True)
    print("WRITTEN", os.path.join(ART, "hero.glb"))
