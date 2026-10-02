"""Bind a finished character model (any pose near A or T, one mesh, textured)
to the game's own skeleton without webbing, taking its weights from a body
already rigged to that skeleton.

    blender -b --python tools/assets/bind_model.py -- <model.glb> <rigged.glb> <out.glb> [--faces 120000] [--smooth 2] [--check <prefix>]

  1. The rigged body's arms and thighs are posed until its hands and ankles
     stand where the model's do.
  2. The model is scaled to the rigged body's height and aligned to its
     torso by nearest points.
  3. Each of the model's vertices takes its weights from the rigged body's
     nearest vertices that are on the same side of the body (for limbs) and
     whose surface faces the same way. That is what stops webbing: the inside
     of an arm cannot take the hip's weights, which face the other way, and
     an inner thigh cannot take the other leg's.
  4. The model is carried back to the skeleton's rest (its T-pose) through
     the inverse of its own skinning, so it stands in the pose every clip
     expects, and in the pose it was made in looks exactly as it was made.
--check renders it at rest and in two poses, to judge the deformation.
"""
import math
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

ARGS = sys.argv[sys.argv.index("--") + 1:]
MODEL, RIGGED, OUT = ARGS[0], ARGS[1], ARGS[2]
opt = lambda k, d: type(d)(ARGS[ARGS.index(k) + 1]) if k in ARGS else d
FACES = opt("--faces", 120000)
SMOOTH = opt("--smooth", 5)
CHECK = opt("--check", "")

bpy.ops.wm.read_factory_settings(use_empty=True)


def active(o):
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o


# ------------------------------------------------- the rigged body --
bpy.ops.import_scene.gltf(filepath=RIGGED)
rig = next(o for o in bpy.data.objects if o.type == "ARMATURE")
ref = max((o for o in bpy.data.objects if o.type == "MESH" and o.find_armature() == rig), key=lambda o: len(o.data.vertices))
for o in [o for o in bpy.data.objects if o.type == "MESH" and o != ref]:
    bpy.data.objects.remove(o)
bones = [b.name for b in rig.data.bones]
bi = {b: i for i, b in enumerate(bones)}
rnames = [g.name for g in ref.vertex_groups]
RW = np.zeros((len(ref.data.vertices), len(bones)))
for i, v in enumerate(ref.data.vertices):
    for g in v.groups:
        nm = rnames[g.group]
        if nm in bi:
            RW[i, bi[nm]] = g.weight
RW /= np.maximum(RW.sum(1, keepdims=True), 1e-9)


def ref_posed():
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ref.evaluated_get(dg)
    m = ev.to_mesh()
    co = np.array([(ev.matrix_world @ v.co)[:] for v in m.vertices])
    nr = np.array([(ev.matrix_world.to_3x3() @ v.normal).normalized()[:] for v in m.vertices])
    ev.to_mesh_clear()
    return co, nr


# ------------------------------------------------------- the model --
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=MODEL)
parts = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
active(parts[0])
for o in parts:
    o.select_set(True)
if len(parts) > 1:
    bpy.ops.object.join()
model = bpy.context.view_layer.objects.active
model.name = "Woman"
bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
for o in [o for o in bpy.data.objects if o not in before and o != model]:
    bpy.data.objects.remove(o)
if len(model.data.polygons) > FACES:
    dec = model.modifiers.new("dec", "DECIMATE")
    dec.ratio = FACES / len(model.data.polygons)
    bpy.ops.object.modifier_apply(modifier="dec")
print("MODEL", len(model.data.polygons), "faces")

R0, _ = ref_posed()
z0, z1 = R0[:, 2].min(), R0[:, 2].max()
S = np.array([v.co[:] for v in model.data.vertices])
lo, hi = S.min(0), S.max(0)
S = (S - np.array([(lo[0] + hi[0]) / 2, np.median(S[:, 1]), lo[2]])) * ((z1 - z0) / (hi[2] - lo[2])) + np.array([0, np.median(R0[:, 1]), z0])
band = lambda A: A[(A[:, 2] > z0 + (z1 - z0) * 0.66) & (A[:, 2] < z0 + (z1 - z0) * 0.74) & (np.abs(A[:, 0]) < 0.15)]
if np.sign(band(S)[:, 1].mean() - np.median(S[:, 1])) != np.sign(band(R0)[:, 1].mean() - np.median(R0[:, 1])):
    S[:, 1] = 2 * np.median(S[:, 1]) - S[:, 1]
    S[:, 0] *= -1
    print("TURNED")

# ------------------------------------------- the pose of the model --
# Its hands: the furthest points out to each side; its ankles: the lowest
# points of each leg above the sole.
hand_l = S[np.argmax(S[:, 0])]
hand_r = S[np.argmin(S[:, 0])]
ank = S[(S[:, 2] > z0 + 0.06) & (S[:, 2] < z0 + 0.1)]
gap = ank[:, 0].max() - ank[:, 0].min() if len(ank) else None

active(rig)
bpy.ops.object.mode_set(mode="POSE")
for pb in rig.pose.bones:
    pb.rotation_mode = "XYZ"
    pb.rotation_euler = (0, 0, 0)


def tip(name):
    bpy.context.view_layer.update()
    return np.array((rig.matrix_world @ rig.pose.bones[name].tail)[:])


def fit_arm(side, target):
    """Lower the upper arm (about the body's front axis, in the bone's own
    space) until the hand's tip is as low as the model's."""
    pb = rig.pose.bones[f"upperarm_{side}"]
    best = None
    for deg in np.linspace(-80, 80, 161):
        pb.rotation_euler = (0, 0, 0)
        # Rotate in world about Y (front axis), expressed in the bone's space.
        m = (rig.matrix_world @ pb.bone.matrix_local).to_3x3()
        rot = Matrix.Rotation(math.radians(deg), 3, "Y")
        local = m.inverted() @ rot @ m
        pb.rotation_euler = local.to_euler("XYZ")
        e = abs(tip(f"hand_{side}")[2] - target[2]) + 0.3 * abs(tip(f"hand_{side}")[0] - target[0])
        if best is None or e < best[0]:
            best = (e, pb.rotation_euler.copy())
    pb.rotation_euler = best[1]
    print("ARM", side, "error %.3f" % best[0])


fit_arm("l", hand_l)
fit_arm("r", hand_r)
if gap:
    best = None
    for deg in np.linspace(-12, 12, 49):
        for side, sign in (("l", 1), ("r", -1)):
            rig.pose.bones[f"thigh_{side}"].rotation_euler = (0, 0, math.radians(deg) * sign)
        g = abs(tip("calf_l")[0] - tip("calf_r")[0])
        if best is None or abs(g - gap) < best[0]:
            best = (abs(g - gap), deg)
    for side, sign in (("l", 1), ("r", -1)):
        rig.pose.bones[f"thigh_{side}"].rotation_euler = (0, 0, math.radians(best[1]) * sign)
    print("LEGS", round(best[1], 1), "deg")
bpy.ops.object.mode_set(mode="OBJECT")
R, RN = ref_posed()

# Aligned to the torso by nearest points (shift and a little scale).
core = R[(R[:, 2] > z0 + (z1 - z0) * 0.35) & (R[:, 2] < z0 + (z1 - z0) * 0.75) & (np.abs(R[:, 0]) < 0.17)][::3]
mf = [list(p.vertices) for p in model.data.polygons]
for it in range(10):
    t = BVHTree.FromPolygons([Vector(p) for p in S], mf)
    src, dst = [], []
    for p in core:
        co, _, _, d = t.find_nearest(Vector(p), 0.12)
        if co is not None:
            src.append(co[:]); dst.append(p)
    src, dst = np.array(src), np.array(dst)
    cs, cd = src.mean(0), dst.mean(0)
    k = float(np.clip(np.sqrt(((dst - cd) ** 2).sum() / ((src - cs) ** 2).sum()), 0.95, 1.05))
    S = (S - cs) * k + cd
print("ALIGNED", np.round(cd - cs, 4), round(k, 4))
for i, v in enumerate(model.data.vertices):
    v.co = Vector(S[i])
model.data.update()
SN = np.array([v.normal[:] for v in model.data.vertices])

# --------------------------------------------------- the weights --
# Limbs and sides: which side of the body a reference vertex belongs to,
# from its bones (left, right, or the middle).
side_of = np.zeros(len(R))
for i in range(len(R)):
    l = sum(RW[i, bi[b]] for b in bones if b.endswith("_l"))
    r = sum(RW[i, bi[b]] for b in bones if b.endswith("_r"))
    side_of[i] = 1 if l > 0.5 else -1 if r > 0.5 else 0
# The crotch: the lowest point the pelvis still carries. Below it the legs
# are two, and nothing may belong to both.
# (The reference's lowest point on the midline, between its own legs.)
# Measured on the model itself: its own lowest midline point.
mid = S[(np.abs(S[:, 0]) < 0.008) & (S[:, 2] > z0 + (z1 - z0) * 0.3) & (S[:, 2] < z0 + (z1 - z0) * 0.6)]
CROTCH = mid[:, 2].min() - 0.005
print("CROTCH %.3f" % CROTCH)
# Faces bridging the legs below the crotch (a sculpt with touching thighs
# joins them) are cut: stretched when the legs part, they are the webbing.
import bmesh
bm = bmesh.new()
bm.from_mesh(model.data)
bm.verts.ensure_lookup_table()
cut = [f for f in bm.faces if all(v.co.z < CROTCH - 0.005 for v in f.verts)
       and min(v.co.x for v in f.verts) < -0.001 and max(v.co.x for v in f.verts) > 0.001]
bmesh.ops.delete(bm, geom=cut, context="FACES")
loose = [v for v in bm.verts if not v.link_faces]
bmesh.ops.delete(bm, geom=loose, context="VERTS")
# Slivers: where the thighs touched, the generator left thin sheets with
# nothing behind them. A real surface has the body behind it; a face whose
# own back is within a few millimetres is a sheet, and goes.
bm.faces.ensure_lookup_table()
tree = BVHTree.FromBMesh(bm)
thin = []
for f in bm.faces:
    c = f.calc_center_median()
    if c.z > CROTCH + 0.06 or abs(c.x) > 0.09:
        continue
    n = f.normal
    hit = tree.ray_cast(c - n * 0.0004, -n, 0.008)
    if hit[0] is not None:
        thin.append(f)
bmesh.ops.delete(bm, geom=thin, context="FACES")
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
bm.to_mesh(model.data)
bm.free()
model.data.update()
print("BRIDGE", len(cut), "faces cut;", len(thin), "sliver faces cut")
S = np.array([v.co[:] for v in model.data.vertices])
SN = np.array([v.normal[:] for v in model.data.vertices])
leg_l = np.array([sum(RW[i, bi[b]] for b in bones if b.endswith("_l") and any(k in b for k in ("thigh", "calf", "foot", "ball"))) for i in range(len(R))])
leg_r = np.array([sum(RW[i, bi[b]] for b in bones if b.endswith("_r") and any(k in b for k in ("thigh", "calf", "foot", "ball"))) for i in range(len(R))])

# Which leg each vertex below the crotch is joined to, by the mesh itself:
# where the thighs pressed together, an inner thigh crosses the midline,
# and judged by position it would be given to the other leg.
nS = len(S)
parent = list(range(nS))
def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a
low = S[:, 2] < CROTCH - 0.005
for f in model.data.polygons:
    vs = [v for v in f.vertices if low[v]]
    for a_, b_ in zip(vs, vs[1:]):
        ra, rb = find(a_), find(b_)
        if ra != rb:
            parent[ra] = rb
# Copies of a vertex split along UV seams are one point.
_k = np.round(S / 1e-5).astype(np.int64)
_, _tw = np.unique(_k, axis=0, return_inverse=True)
_first = {}
for i, t in enumerate(_tw.ravel()):
    if low[i]:
        if t in _first:
            ra, rb = find(i), find(_first[t])
            if ra != rb:
                parent[ra] = rb
        else:
            _first[t] = i
roots = np.array([find(i) for i in range(nS)])
leg_side = np.zeros(nS)
comp = {}
for i in np.nonzero(low)[0]:
    comp.setdefault(roots[i], []).append(i)
big = sorted(comp.values(), key=len, reverse=True)
for members in big[:2]:
    side = 1 if S[members, 0].mean() > 0 else -1
    leg_side[members] = side
for members in big[2:]:
    leg_side[members] = 1 if S[members, 0].mean() > 0 else -1
print("LEGS", [len(m) for m in big[:2]], "verts;", len(big) - 2, "small pieces; below", int(low.sum()), "of", nS, "z", np.round(np.percentile(S[:, 2], [0, 25, 50, 75, 100]), 3), "crotch", round(CROTCH, 3))

kd = KDTree(len(R))
for i, p in enumerate(R):
    kd.insert(p, i)
kd.balance()
W = np.zeros((len(S), len(bones)))
fallback = 0
for i in range(len(S)):
    # The inner thigh up to a little above the crotch is leg, not torso:
    # weighted to the pelvis it stays behind as a fin when the leg swings.
    below = S[i, 2] < CROTCH or (S[i, 2] < CROTCH + 0.05 and abs(S[i, 0]) > 0.025)
    if leg_side[i] != 0:
        me_side = int(leg_side[i])
    else:
        me_side = (1 if S[i, 0] >= 0 else -1) if below else (1 if S[i, 0] > 0.02 else -1 if S[i, 0] < -0.02 else 0)
    got = []
    for co, j, d in kd.find_n(S[i], 32):
        if np.dot(RN[j], SN[i]) < 0.25:
            continue
        if side_of[j] != 0 and me_side != 0 and side_of[j] != me_side:
            continue
        # Below the crotch: only the vertex's own leg.
        if below and (leg_l[j] if me_side > 0 else leg_r[j]) < 0.5:
            continue
        got.append((j, d))
        if len(got) >= 4:
            break
    if not got:
        fallback += 1
        got = [(j, d) for co, j, d in kd.find_n(S[i], 4)]
    w = np.array([1 / max(1e-5, d) for _, d in got])
    w /= w.sum()
    for (j, _), ww in zip(got, w):
        W[i] += RW[j] * ww
print("WEIGHTS", len(S), "verts,", fallback, "by fallback")
# Copies of one point: glTF splits a vertex along every UV seam, and copies
# weighted even slightly differently tear the seam open when she moves.
key = np.round(S / 1e-5).astype(np.int64)
_, twin = np.unique(key, axis=0, return_inverse=True)
twin = twin.ravel()
adj = [[] for _ in range(len(S))]
for e in model.data.edges:
    a, b = e.vertices
    adj[a].append(b)
    adj[b].append(a)
# Neighbours across a seam are neighbours too.
groups = {}
for i, g in enumerate(twin):
    groups.setdefault(g, []).append(i)
for members in groups.values():
    if len(members) > 1:
        nb = set()
        for m in members:
            nb.update(adj[m])
        for m in members:
            adj[m] = list(nb - {m})


def weld(W):
    sums = np.zeros((twin.max() + 1, W.shape[1]))
    np.add.at(sums, twin, W)
    cnt = np.bincount(twin)[:, None]
    return (sums / cnt)[twin]


W = weld(W)
for _ in range(SMOOTH):
    N = W.copy()
    for i in range(len(S)):
        if adj[i]:
            N[i] = 0.6 * W[i] + 0.4 * W[adj[i]].mean(0)
    W = N
W = weld(W)
# Smoothing runs over the mesh, and through the groin it carries each leg's
# weights onto the other: near and below the crotch, a vertex keeps nothing
# of the other leg, and on the leg proper little of the pelvis.
LEGB = {s_: [bi[b] for b in bones if b.endswith("_" + s_) and any(k in b for k in ("thigh", "calf", "foot", "ball"))] for s_ in ("l", "r")}
pel_i = bi.get("pelvis")
cleaned = 0
for i in range(len(S)):
    if S[i, 2] > CROTCH + 0.1 or (leg_side[i] == 0 and abs(S[i, 0]) < 0.004):
        continue
    sd = leg_side[i] if leg_side[i] != 0 else (1 if S[i, 0] > 0 else -1)
    own, other = ("l", "r") if sd > 0 else ("r", "l")
    if W[i, LEGB[other]].sum() > 1e-4:
        cleaned += 1
    W[i, LEGB[other]] = 0
    if S[i, 2] < CROTCH - 0.02 and pel_i is not None:
        W[i, pel_i] *= 0.3
W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
print("CLEANED", cleaned, "verts of the other leg's weight")
# No vertex is carried by both legs: at the midline above the crotch the
# two legs' weights meet, and skin carried by both is torn between them as
# soon as one leg moves (the flap). The lesser leg's share goes to the pelvis.
if pel_i is not None:
    both = 0
    Lb, Rb = LEGB["l"], LEGB["r"]
    for i in range(len(S)):
        wl, wr = W[i, Lb].sum(), W[i, Rb].sum()
        if min(wl, wr) < 0.01:
            continue
        both += 1
        lesser, greater = (Lb, Rb) if wl < wr else (Rb, Lb)
        # Below the crotch it is all the leg's own; above, the pelvis's.
        if S[i, 2] < CROTCH + 0.01:
            own_ = LEGB["l"] if (leg_side[i] or np.sign(S[i, 0]) or 1) > 0 else LEGB["r"]
            oth_ = LEGB["r"] if own_ is LEGB["l"] else LEGB["l"]
            tot = W[i, oth_].sum()
            W[i, oth_] = 0
            k = own_[0] if W[i, own_].sum() == 0 else own_[int(np.argmax(W[i, own_]))]
            W[i, k] += tot
        else:
            W[i, pel_i] += W[i, lesser].sum()
            W[i, lesser] = 0
    W = weld(W)
    # Welding can mix the two again across a seam: once more, after.
    for i in range(len(S)):
        wl, wr = W[i, Lb].sum(), W[i, Rb].sum()
        if min(wl, wr) >= 0.01:
            lesser = Lb if wl < wr else Rb
            if S[i, 2] < CROTCH + 0.01:
                own_ = LEGB["l"] if (leg_side[i] or np.sign(S[i, 0]) or 1) > 0 else LEGB["r"]
                oth_ = LEGB["r"] if own_ is LEGB["l"] else LEGB["l"]
                tot = W[i, oth_].sum(); W[i, oth_] = 0
                W[i, own_[int(np.argmax(W[i, own_]))]] += tot
            else:
                W[i, pel_i] += W[i, lesser].sum()
                W[i, lesser] = 0
    print("BOTH LEGS", both, "verts given to the pelvis")

# Four bones a vertex, as the game skins.
top = np.argsort(-W, axis=1)[:, :4]
W4 = np.zeros_like(W)
rows = np.arange(len(S))[:, None]
W4[rows, top] = W[rows, top]
W4 /= np.maximum(W4.sum(1, keepdims=True), 1e-9)
_sum = W4.sum(1)
print("WEIGHTLESS", int((_sum < 0.5).sum()), "verts; one bone", int(((W4 > 0.005).sum(1) == 1).sum()))

# -------------------------------------------- back to the T-pose rest --
mats = np.array([np.array(rig.matrix_world @ rig.pose.bones[b].matrix @ rig.data.bones[b].matrix_local.inverted() @ rig.matrix_world.inverted()) for b in bones])
M = np.einsum("nb,bij->nij", W4, mats)
rest = np.einsum("nij,nj->ni", np.linalg.inv(M), np.hstack([S, np.ones((len(S), 1))]))[:, :3]
for i, v in enumerate(model.data.vertices):
    v.co = Vector(rest[i])
model.data.update()
for b in bones:
    model.vertex_groups.new(name=b)
for i in range(len(S)):
    for j in top[i]:
        if W4[i, j] > 0.005:
            model.vertex_groups[bones[j]].add([i], float(W4[i, j]), "REPLACE")
active(rig)
bpy.ops.object.mode_set(mode="POSE")
for pb in rig.pose.bones:
    pb.rotation_euler = (0, 0, 0)
bpy.ops.object.mode_set(mode="OBJECT")
if "--debug-colors" in ARGS:
    # Each vertex painted by who carries it: red the left leg, blue the
    # right, green the pelvis and spine (for finding mis-weighted skin).
    ca = model.data.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    L = [bi[b] for b in bones if b.endswith("_l") and any(k in b for k in ("thigh", "calf", "foot", "ball"))]
    Rr = [bi[b] for b in bones if b.endswith("_r") and any(k in b for k in ("thigh", "calf", "foot", "ball"))]
    T = [bi[b] for b in ("pelvis", "spine_01", "spine_02", "spine_03") if b in bi]
    for i in range(len(S)):
        ca.data[i].color = (float(W4[i, L].sum()), float(W4[i, T].sum()), float(W4[i, Rr].sum()), 1)
bpy.data.objects.remove(ref)
model.parent = rig
mod = model.modifiers.new("Armature", "ARMATURE")
mod.object = rig
active(rig)
model.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True, export_skins=True, export_animations=False, export_yup=True,
                          **({"export_vertex_color": "ACTIVE", "export_all_vertex_colors": True} if "--debug-colors" in ARGS else {}))
print("BOUND", OUT)

if CHECK:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x, scene.render.resolution_y = 700, 1000
    w = bpy.data.worlds.new("w")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.6, 0.6, 0.63, 1)
    scene.world = w
    for name, loc, e in (("k", (2, -3, 2.5), 500), ("f", (-3, -2, 1.5), 200), ("r", (0, 3, 2.5), 400)):
        l = bpy.data.lights.new(name, "AREA"); l.energy = e; l.size = 2.5
        ob = bpy.data.objects.new(name, l); ob.location = loc; scene.collection.objects.link(ob)
        ob.rotation_euler = (-Vector(loc) + Vector((0, 0, 1))).to_track_quat("-Z", "Y").to_euler()
    cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); scene.collection.objects.link(cam); scene.camera = cam; cam.data.lens = 50
    active(rig)
    bpy.ops.object.mode_set(mode="POSE")

    def pose(d):
        for pb in rig.pose.bones:
            pb.rotation_euler = (0, 0, 0)
        for b, (x, y, z) in d.items():
            rig.pose.bones[b].rotation_euler = (math.radians(x), math.radians(y), math.radians(z))
        bpy.context.view_layer.update()

    poses = {"rest": {}, "stride": {"thigh_l": (-40, 0, 0), "thigh_r": (30, 0, 0), "calf_r": (45, 0, 0), "upperarm_l": (0, 0, -70), "upperarm_r": (0, 0, 70), "lowerarm_r": (0, -30, 0), "spine_02": (0, 15, 0)},
             "crouch": {"thigh_l": (-80, 0, 0), "thigh_r": (-80, 0, 0), "calf_l": (100, 0, 0), "calf_r": (100, 0, 0), "upperarm_l": (40, 0, -40), "upperarm_r": (40, 0, 40)}}
    for tag, d in poses.items():
        pose(d)
        for vt, ang in (("front", 15), ("side", 95)):
            r = math.radians(ang)
            cam.location = (math.sin(r) * 4.8, -math.cos(r) * 4.8, 0.95)
            cam.rotation_euler = (math.radians(90), 0, r)
            scene.render.filepath = f"{CHECK}_{tag}_{vt}.png"
            bpy.ops.render.render(write_still=True)
