"""The heroine from AccuRIG's rig of her sculpt, on the game's own skeleton.

    blender -b --python tools/assets/build_heroine.py -- <accurig.fbx> <ual.glb> <texture source.glb> <out.glb> [<scene.blend>]

The scene is saved too when asked, for heroine_outfits.py: her clothes are
exported from the very skeleton she was, so they bind to hers exactly.

AccuRIG (Reallusion, free) rigs a sculpt in its own pose with a full
Character Creator skeleton: twist bones, corrective share bones, weights
that hold the groin, shoulders and fingers together. The game's clips are
made for the Quaternius skeleton of the Universal Animation Library, so:

  1. The library's own skeleton (UAL) is turned, bone by bone, by the
     smallest rotation that lays each bone along her A-pose, then given her
     joints (each head where AccuRIG put it). Its bones keep the library's
     own frames, only turned, so a clip's rotations land on her exactly as
     they land on the bodies the clips were made for.
  2. Her mesh does not move: her A-pose is the bind pose. (Carrying a mesh
     to another rest through its own skinning leaves ripples.)
  3. AccuRIG's weights are folded onto the library's bones: twist and share
     bones onto the bone they belong to.
Her paint is the sculpt's (AccuRIG does not carry the texture), on the same
UVs.
"""
import sys

import bpy
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:]
CC_FBX, UAL, TEXSRC, OUT = ARGS[:4]
BLEND = ARGS[4] if len(ARGS) > 4 else None

bpy.ops.wm.read_factory_settings(use_empty=True)


def active(o):
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o


# ------------------------------------------------------------- AccuRIG --
bpy.ops.import_scene.fbx(filepath=CC_FBX)
cc = next(o for o in bpy.data.objects if o.type == "ARMATURE")
body = next(o for o in bpy.data.objects if o.type == "MESH")
active(body)
body.select_set(True)
cc.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
for o in (body, cc):
    o.animation_data_clear()
bpy.context.view_layer.update()
CCJ = {b.name: (cc.matrix_world @ b.head_local, cc.matrix_world @ b.tail_local) for b in cc.data.bones}

# Each library bone: the AccuRIG bone whose head is its joint, and the one
# whose head it points at.
L, R = "L", "R"


def side(q, c):
    return {f"{q}_l": c.replace("{S}", "L"), f"{q}_r": c.replace("{S}", "R")}


JOINT = {"pelvis": "CC_Base_Pelvis", "spine_01": "CC_Base_Waist", "spine_02": "CC_Base_Spine01", "spine_03": "CC_Base_Spine02",
         "neck_01": "CC_Base_NeckTwist01", "Head": "CC_Base_Head"}
for q, c in (("clavicle", "CC_Base_{S}_Clavicle"), ("upperarm", "CC_Base_{S}_Upperarm"), ("lowerarm", "CC_Base_{S}_Forearm"),
             ("hand", "CC_Base_{S}_Hand"), ("thigh", "CC_Base_{S}_Thigh"), ("calf", "CC_Base_{S}_Calf"), ("foot", "CC_Base_{S}_Foot"),
             ("ball", "CC_Base_{S}_ToeBase")):
    JOINT.update(side(q, c))
for f, cf in (("index", "Index"), ("middle", "Mid"), ("ring", "Ring"), ("pinky", "Pinky"), ("thumb", "Thumb")):
    for k in (1, 2, 3):
        JOINT.update(side(f"{f}_0{k}", f"CC_Base_{{S}}_{cf}{k}"))

# AccuRIG's weights onto the library's bones.
FOLD = {"CC_Base_Hip": "pelvis", "CC_Base_Pelvis": "pelvis", "CC_Base_Waist": "spine_01", "CC_Base_Spine01": "spine_02",
        "CC_Base_Spine02": "spine_03", "CC_Base_NeckTwist01": "neck_01", "CC_Base_NeckTwist02": "neck_01"}
for c in ("Head", "FacialBone", "JawRoot", "Tongue01", "Tongue02", "Tongue03", "Teeth01", "Teeth02", "UpperJaw", "L_Eye", "R_Eye"):
    FOLD[f"CC_Base_{c}"] = "Head"
for S, s in (("L", "l"), ("R", "r")):
    FOLD.update({f"CC_Base_{S}_Clavicle": f"clavicle_{s}", f"CC_Base_{S}_Upperarm": f"upperarm_{s}",
                 f"CC_Base_{S}_UpperarmTwist01": f"upperarm_{s}", f"CC_Base_{S}_UpperarmTwist02": f"upperarm_{s}",
                 f"CC_Base_{S}_Forearm": f"lowerarm_{s}", f"CC_Base_{S}_ForearmTwist01": f"lowerarm_{s}",
                 f"CC_Base_{S}_ForearmTwist02": f"lowerarm_{s}", f"CC_Base_{S}_ElbowShareBone": f"lowerarm_{s}",
                 f"CC_Base_{S}_Hand": f"hand_{s}", f"CC_Base_{S}_Thigh": f"thigh_{s}", f"CC_Base_{S}_ThighTwist01": f"thigh_{s}",
                 f"CC_Base_{S}_ThighTwist02": f"thigh_{s}", f"CC_Base_{S}_Calf": f"calf_{s}", f"CC_Base_{S}_CalfTwist01": f"calf_{s}",
                 f"CC_Base_{S}_CalfTwist02": f"calf_{s}", f"CC_Base_{S}_KneeShareBone": f"calf_{s}", f"CC_Base_{S}_Foot": f"foot_{s}",
                 f"CC_Base_{S}_ToeBase": f"ball_{s}", f"CC_Base_{S}_ToeBaseShareBone": f"ball_{s}"})
    for t in ("BigToe1", "IndexToe1", "MidToe1", "RingToe1", "PinkyToe1"):
        FOLD[f"CC_Base_{S}_{t}"] = f"ball_{s}"
    for f, cf in (("index", "Index"), ("middle", "Mid"), ("ring", "Ring"), ("pinky", "Pinky"), ("thumb", "Thumb")):
        for k in (1, 2, 3):
            FOLD[f"CC_Base_{S}_{cf}{k}"] = f"{f}_0{k}_{s}"

# ------------------------------------------------- the library's skeleton --
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=UAL)
q = next(o for o in bpy.data.objects if o not in before and o.type == "ARMATURE")
for o in [o for o in bpy.data.objects if o not in before and o != q]:
    bpy.data.objects.remove(o)
q.animation_data_clear()
active(q)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# 1. Turned bone by bone, parents first, onto her directions.
bpy.ops.object.mode_set(mode="POSE")
for pb in q.pose.bones:
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = (1, 0, 0, 0)


def depth(b):
    d = 0
    while b.parent:
        b, d = b.parent, d + 1
    return d


CHILD = {}
for b in q.data.bones:
    if b.name in JOINT:
        kids = [c for c in b.children if c.name in JOINT]
        # The bone's own line runs to its main child (for a hand, the middle finger).
        pick = None
        for pref in ("lowerarm", "hand", "calf", "foot", "ball", "spine", "neck", "Head", "middle_01", "upperarm"):
            pick = next((k for k in kids if k.name.startswith(pref)), None)
            if pick:
                break
        if pick is None and kids:
            pick = kids[0]
        CHILD[b.name] = pick.name if pick else None

turned = 0
for b in sorted(q.data.bones, key=depth):
    if b.name not in JOINT or JOINT[b.name] not in CCJ:
        continue
    head = CCJ[JOINT[b.name]][0]
    if CHILD.get(b.name) and JOINT[CHILD[b.name]] in CCJ:
        tgt = CCJ[JOINT[CHILD[b.name]]][0] - head
    else:
        tgt = CCJ[JOINT[b.name]][1] - head
    if tgt.length < 1e-5:
        continue
    bpy.context.view_layer.update()
    pb = q.pose.bones[b.name]
    cur = (q.matrix_world @ pb.tail) - (q.matrix_world @ pb.head)
    rot = cur.normalized().rotation_difference(tgt.normalized())
    m = pb.matrix.to_3x3()
    # World rotation, expressed on the bone's local rotation.
    loc = pb.bone.matrix_local.to_3x3()
    par = pb.parent.matrix.to_3x3() @ pb.parent.bone.matrix_local.to_3x3().inverted() if pb.parent else loc.inverted() @ loc
    world_now = m
    world_new = rot.to_matrix() @ world_now
    if pb.parent:
        pm = pb.parent.matrix.to_3x3()
        rel = pb.parent.bone.matrix_local.to_3x3().inverted() @ pb.bone.matrix_local.to_3x3()
        basis = (pm @ rel).inverted() @ world_new
    else:
        basis = loc.inverted() @ world_new
    pb.rotation_quaternion = basis.to_quaternion()
    turned += 1
bpy.context.view_layer.update()
bpy.ops.pose.armature_apply(selected=False)
print("TURNED", turned, "bones")

# 2. Her joints: each head where AccuRIG put it, the line and roll kept.
bpy.ops.object.mode_set(mode="EDIT")
eb = q.data.edit_bones
for e in eb:
    e.use_connect = False
moved = 0
for e in sorted(eb, key=lambda e: len(e.parent_recursive)):
    if e.name not in JOINT or JOINT[e.name] not in CCJ:
        continue
    head = CCJ[JOINT[e.name]][0]
    d = (e.tail - e.head)
    ln = d.length
    if CHILD.get(e.name) and JOINT[CHILD[e.name]] in CCJ:
        ln = (CCJ[JOINT[CHILD[e.name]]][0] - head).length or ln
    roll = e.roll
    e.head = head
    e.tail = head + d.normalized() * ln
    e.roll = roll
    moved += 1
# Leaves follow their parents' tails.
for e in eb:
    if e.name.endswith("_leaf_l") or e.name.endswith("_leaf_r"):
        p = e.parent
        if p:
            d = e.tail - e.head
            e.head = p.tail
            e.tail = p.tail + d
bpy.ops.object.mode_set(mode="OBJECT")
print("JOINTS", moved, "placed")

# 3. Her weights, folded onto the library's bones.
names = [g.name for g in body.vertex_groups]
acc = {}
for v in body.data.vertices:
    w = {}
    for g in v.groups:
        tgt = FOLD.get(names[g.group])
        if tgt and tgt in q.data.bones:
            w[tgt] = w.get(tgt, 0) + g.weight
    acc[v.index] = w
missing = sorted({n for n in names if n not in FOLD})
print("UNFOLDED", missing)
for g in list(body.vertex_groups):
    body.vertex_groups.remove(g)
for b in q.data.bones:
    body.vertex_groups.new(name=b.name)
for i, w in acc.items():
    tot = sum(w.values()) or 1
    top = sorted(w.items(), key=lambda kv: -kv[1])[:4]
    t4 = sum(x for _, x in top) or 1
    for nm, x in top:
        if x / t4 > 0.005:
            body.vertex_groups[nm].add([i], x / t4, "REPLACE")
for mod in list(body.modifiers):
    body.modifiers.remove(mod)
body.parent = q
mod = body.modifiers.new("Armature", "ARMATURE")
mod.object = q
bpy.data.objects.remove(cc)
# Named only now: AccuRIG's own armature held the name till it went, and
# the clips address "Armature/Skeleton3D".
q.name = "Armature"

# 4. Soft tissue: a bone for each breast and each buttock, for the game to
# swing on springs (HerJiggle.cs).
# Placed from her own landmarks: the nipple is the most forward point of
# each side of the chest, the buttock the most rearward of each side of the
# hips; the fold under each is where the surface steps back toward the ribs
# (or the thigh).
import numpy as np
co = np.array([(body.matrix_world @ v.co)[:] for v in body.data.vertices])
z0, z1 = co[:, 2].min(), co[:, 2].max()
H = z1 - z0
SOFT = {}
for s, sd in ((1, "l"), (-1, "r")):
    m = (co[:, 2] > z0 + 0.62 * H) & (co[:, 2] < z0 + 0.8 * H) & (co[:, 0] * s > 0.03) & (co[:, 0] * s < 0.2)
    nip = co[np.where(m)[0][np.argmin(co[m, 1])]]
    m = (co[:, 2] > z0 + 0.4 * H) & (co[:, 2] < z0 + 0.58 * H) & (co[:, 0] * s > 0.02)
    glu = co[np.where(m)[0][np.argmax(co[m, 1])]]
    SOFT[sd] = (nip, glu)
    print("SOFT", sd, "nipple", nip.round(3), "buttock", glu.round(3))


def falloff(p, c, rx, ry, up, down):
    """1 at the centre of a soft mass, easing to 0 at its edge (an egg:
    taller above its centre than below, where the fold is)."""
    d = p - c
    rz = np.where(d[:, 2] > 0, up, down)
    r = np.sqrt((d[:, 0] / rx) ** 2 + (d[:, 1] / ry) ** 2 + (d[:, 2] / rz) ** 2)
    t = np.clip((1.0 - r) / 0.65, 0, 1)
    return t * t * (3 - 2 * t)


def ramp(x, a, b):
    """0 at a, 1 at b, smooth between (a hard cut makes a crease)."""
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


bpy.ops.object.mode_set(mode="OBJECT")
active(q)
bpy.ops.object.mode_set(mode="EDIT")
eb = q.data.edit_bones
for sd, (nip, glu) in SOFT.items():
    b = eb.new(f"breast_{sd}")
    b.head = Vector((nip[0], nip[1] + 0.075, nip[2] + 0.005))     # on the chest wall behind it
    b.tail = Vector((nip[0], nip[1] - 0.01, nip[2]))
    b.parent = eb["spine_03"]
    b = eb.new(f"glute_{sd}")
    b.head = Vector((glu[0], glu[1] - 0.09, glu[2] + 0.02))
    b.tail = Vector((glu[0], glu[1] + 0.01, glu[2] - 0.01))
    b.parent = eb["pelvis"]
bpy.ops.object.mode_set(mode="OBJECT")

# Each mass's weight: the share of its own bone, the rest of the vertex's
# weights scaled down to make room. A breast is all chest, so it may take
# the whole of a vertex; a buttock is also moved by the thigh, so it takes
# at most half, and the leg still pulls it when she strides.
gi = {g.name: g.index for g in body.vertex_groups}
for b in ("breast_l", "breast_r", "glute_l", "glute_r"):
    body.vertex_groups.new(name=b)
    gi[b] = body.vertex_groups[b].index
names = [g.name for g in body.vertex_groups]
share = {}
for sd, (nip, glu) in SOFT.items():
    c = nip + np.array([0, 0.035, -0.005])
    w = falloff(co, c, 0.085, 0.09, 0.105, 0.07) * ramp(-co[:, 1], 0.02, 0.06)
    share[f"breast_{sd}"] = w
    c = glu + np.array([0, -0.04, 0.0])
    w = 0.5 * falloff(co, c, 0.095, 0.11, 0.11, 0.1) * ramp(co[:, 1], 0.0, 0.05)
    share[f"glute_{sd}"] = w
for i, v in enumerate(body.data.vertices):
    soft = [(b, w[i]) for b, w in share.items() if w[i] > 0.005]
    if not soft:
        continue
    total = sum(x for _, x in soft)
    if total > 1:
        soft = [(b, x / total) for b, x in soft]
        total = 1.0
    old = [(names[g.group], g.weight) for g in v.groups if g.weight > 0]
    ws = {n: x * (1 - total) for n, x in old}
    for b, x in soft:
        ws[b] = ws.get(b, 0) + x
    top = sorted(ws.items(), key=lambda kv: -kv[1])[:4]
    t4 = sum(x for _, x in top) or 1
    for n, _ in old:
        body.vertex_groups[n].remove([i])
    for n, x in top:
        body.vertex_groups[n].add([i], x / t4, "REPLACE")

print("SOFT TISSUE bones 4")

# The inside of her left breast made its right twin's mirror image, shape
# and paint (the sculpt left lumps and a dark smudge there): toward the
# cleavage and below the nipple, fully in the middle of that patch and
# easing to nothing at its edge. The paint is done once her material is on.
from mathutils.bvhtree import BVHTree
import bmesh as _bm
_b = _bm.new()
_b.from_mesh(body.data)
_bm.ops.triangulate(_b, faces=_b.faces)
_b.to_mesh(body.data)
_b.free()
body.data.update()
gl, gr = body.vertex_groups["breast_l"].index, body.vertex_groups["breast_r"].index
wl = np.zeros(len(co))
wr = np.zeros(len(co))
for v in body.data.vertices:
    for g in v.groups:
        if g.group == gl:
            wl[v.index] = g.weight
        elif g.group == gr:
            wr[v.index] = g.weight


def _ease(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


nip_l = SOFT["l"][0]
T = _ease((wl - 0.005) / 0.25) * _ease((nip_l[0] - co[:, 0]) / 0.03) * _ease((nip_l[2] + 0.03 - co[:, 2]) / 0.03)
CO0 = co.copy()
RIGHT = [p.index for p in body.data.polygons if (wr[list(p.vertices)] > 0.005).any()]
MIR = co * np.array([-1, 1, 1])
RBVH = BVHTree.FromPolygons([tuple(x) for x in MIR], [list(body.data.polygons[k].vertices)[::-1] for k in RIGHT])
moved = 0
for i in np.where(T > 0.001)[0]:
    hit = RBVH.find_nearest(Vector(co[i]))[0]
    if hit is None:
        continue
    body.data.vertices[i].co = Vector(co[i] * (1 - T[i]) + np.array(hit[:]) * T[i])
    moved += 1
co = np.array([(body.matrix_world @ v.co)[:] for v in body.data.vertices])
print("LEFT BREAST inner patch from the right,", moved, "points")

# At the very bottom of her crotch the sculpt left a small crumpled knot of
# skin (folds over itself): ironed flat, only within 2.5 cm of it.
mid = (np.abs(co[:, 0]) < 0.008) & (co[:, 2] > 0.8) & (co[:, 2] < 1.15) & (np.abs(co[:, 1]) < 0.12)
zs_ = np.sort(co[mid, 2])[::-1]
zs_ = zs_[zs_ < 1.07]
gap_ = np.where(np.diff(zs_) < -0.012)[0]
crotch_z = zs_[gap_[0]] if len(gap_) else zs_[-1]
crotch_y = co[mid][np.argmin(np.abs(co[mid, 2] - crotch_z)), 1]
knot = np.array([0.0, crotch_y, crotch_z])
wgt = _ease((0.036 - np.linalg.norm(co - knot, axis=1)) / 0.016)
# (Her skin is split along the paint's seams: points at one place move as one.)
_, grp = np.unique(np.round(co, 6), axis=0, return_inverse=True)
grp = grp.ravel()
G_ = grp.max() + 1
gco = np.zeros((G_, 3))
np.add.at(gco, grp, co)
gco /= np.bincount(grp, minlength=G_)[:, None]
gnb = [set() for _ in range(G_)]
for e in body.data.edges:
    a_, b_ = grp[e.vertices[0]], grp[e.vertices[1]]
    if a_ != b_:
        gnb[a_].add(b_)
        gnb[b_].add(a_)
gw = np.zeros(G_)
np.maximum.at(gw, grp, wgt)
gidx = np.where(gw > 0.001)[0]
gnl = [list(gnb[g]) for g in gidx]
x_ = gco.copy()
for _ in range(300):
    avg = np.array([x_[n].mean(0) if n else x_[g] for g, n in zip(gidx, gnl)])
    x_[gidx] = x_[gidx] + 0.5 * gw[gidx, None] * (avg - x_[gidx])
idx_ = np.where(gw[grp] > 0.001)[0]
for i in idx_:
    body.data.vertices[i].co = Vector(x_[grp[i]])
co = np.array([(body.matrix_world @ v.co)[:] for v in body.data.vertices])
print("CROTCH knot ironed:", len(idx_), "points round", knot.round(3))
# Recorded for the outfit builder (once ironed, the crotch has no step to find).
body["crotch"] = [float(c) for c in knot]


# Below her crotch each side of her moves with its own leg. AccuRIG gave the
# skin of each inner thigh down to 8 cm below the crotch up to a third of
# its weight on the other leg; when her legs part, that skin is dragged into
# the gap between them (two lumps under the crotch). Right under the crotch
# the sharing is kept (that skin does stretch between her legs); below and
# outward it goes to her own thigh.
gi_ = {g.name: g.index for g in body.vertex_groups}
cz, cx = knot[2], 0.0
fixed_ = 0
for v in body.data.vertices:
    p_ = co[v.index]
    if p_[2] > cz + 0.02 or abs(p_[0]) > 0.12:
        continue
    own, oth = ("l", "r") if p_[0] > 0 else ("r", "l")
    w = {body.vertex_groups[g.group].name: g.weight for g in v.groups}
    other = sum(w.get(f"{b}_{oth}", 0.0) for b in ("thigh", "calf", "foot", "ball", "glute"))
    if other < 1e-4:
        continue
    # Shared between her legs only right under the crotch (as skin there is):
    # all of it at the crotch and at her middle, none 3 cm below or 2 cm out.
    keep = (1 - _ease((cz - p_[2]) / 0.03)) * (1 - _ease((abs(p_[0]) - 0.008) / 0.02))
    move = other * (1 - keep)
    if move < 1e-4:
        continue
    w2 = dict(w)
    for b in ("thigh", "calf", "foot", "ball", "glute"):
        if f"{b}_{oth}" in w2:
            w2[f"{b}_{oth}"] *= keep
    w2[f"thigh_{own}"] = w2.get(f"thigh_{own}", 0.0) + move
    for n, x in w2.items():
        if x > 1e-5:
            body.vertex_groups[n].add([v.index], x, "REPLACE")
        else:
            body.vertex_groups[n].remove([v.index])
    fixed_ += 1
print("CROTCH weights: other leg's share moved off", fixed_, "points")

# Triangles joining one of her legs to the other below the crotch (her
# thighs touch at rest, and the sculpt stitched them together there):
# stretched across the gap when her legs part, so cut.
legw = {}
for v in body.data.vertices:
    w = {body.vertex_groups[g.group].name: g.weight for g in v.groups}
    l_ = sum(w.get(f"{b}_l", 0.0) for b in ("thigh", "calf", "glute"))
    r_ = sum(w.get(f"{b}_r", 0.0) for b in ("thigh", "calf", "glute"))
    legw[v.index] = 1 if l_ > r_ + 0.3 else (-1 if r_ > l_ + 0.3 else 0)
import bmesh as _bm2
bm_ = _bm2.new()
bm_.from_mesh(body.data)
bm_.faces.ensure_lookup_table()
cut_ = [f for f in bm_.faces
        if max(co[v.index][2] for v in f.verts) < cz - 0.004
        and {legw[v.index] for v in f.verts} >= {1, -1}]
print("CROTCH web: cut", len(cut_), "triangles joining her legs")
_bm2.ops.delete(bm_, geom=cut_, context="FACES_ONLY")
bm_.to_mesh(body.data)
bm_.free()
body.data.update()
co = np.array([(body.matrix_world @ v.co)[:] for v in body.data.vertices])


# Her paint, from the sculpt.
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=TEXSRC)
src = next(o for o in bpy.data.objects if o not in before and o.type == "MESH")
body.data.materials.clear()
body.data.materials.append(src.data.materials[0])
for o in [o for o in bpy.data.objects if o not in before]:
    bpy.data.objects.remove(o)
for p in body.data.polygons:
    p.use_smooth = True
body.name = "Heroine"

# The patch's paint, from the right breast: each texel of it found on her
# skin, reflected, found again on the right breast, and painted with what
# is there, blended as the shape was.
img = next(n.image for n in body.data.materials[0].node_tree.nodes if n.type == "TEX_IMAGE" and n.image)
IW, IH = img.size
px = np.array(img.pixels[:], np.float32).reshape(IH, IW, 4)
src = px.copy()
uvl = body.data.uv_layers.active.data
polys = body.data.polygons


def tri_uv(k):
    return np.array([uvl[li].uv[:] for li in polys[k].loop_indices]), list(polys[k].vertices)


painted = 0
for p in polys:
    vs = list(p.vertices)
    if T[vs].max() < 0.001:
        continue
    uv, _ = tri_uv(p.index)
    pp = uv * [IW, IH]
    x0, y0 = np.floor(pp.min(0)).astype(int)
    x1, y1 = np.ceil(pp.max(0)).astype(int)
    xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
    pts = np.c_[xs.ravel() + 0.5, ys.ravel() + 0.5]
    a, b, c = pp
    m = np.array([[b[0] - a[0], c[0] - a[0]], [b[1] - a[1], c[1] - a[1]]])
    if abs(np.linalg.det(m)) < 1e-9:
        continue
    l = np.linalg.solve(m, (pts - a).T).T
    bc = np.c_[1 - l.sum(1), l]
    inside = (bc >= -1e-4).all(1)
    for (tx, ty), w in zip(pts[inside].astype(int), bc[inside]):
        if not (0 <= tx < IW and 0 <= ty < IH):
            continue
        t = float(w @ T[vs])
        if t < 0.001:
            continue
        p3 = (w @ CO0[vs]) * np.array([-1, 1, 1])
        hit, _, idx, _ = RBVH.find_nearest(Vector(p3 * np.array([-1, 1, 1]) * np.array([-1, 1, 1])))
        if hit is None:
            continue
        k = RIGHT[idx]
        ruv, rvs = tri_uv(k)
        A, B, C = MIR[rvs[::-1]]
        ruv = ruv[::-1]
        v0, v1, v2 = B - A, C - A, np.array(hit[:]) - A
        d00, d01, d11, d20, d21 = v0 @ v0, v0 @ v1, v1 @ v1, v2 @ v0, v2 @ v1
        den = d00 * d11 - d01 * d01
        if abs(den) < 1e-14:
            continue
        bb = (d11 * d20 - d01 * d21) / den
        cc = (d00 * d21 - d01 * d20) / den
        u = (1 - bb - cc) * ruv[0] + bb * ruv[1] + cc * ruv[2]
        sx, sy = int(np.clip(u[0] * IW, 0, IW - 1)), int(np.clip(u[1] * IH, 0, IH - 1))
        px[ty, tx, :3] = src[ty, tx, :3] * (1 - t) + src[sy, sx, :3] * t
        painted += 1
img.pixels[:] = px.ravel()
img.update()
img.pack()
print("LEFT BREAST paint:", painted, "texels from the right")

active(q)
body.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True, export_skins=True, export_animations=False, export_yup=True)
print("BUILT", OUT)
if BLEND:
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    print("SAVED", BLEND)
