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

active(q)
body.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True, export_skins=True, export_animations=False, export_yup=True)
print("BUILT", OUT)
if BLEND:
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    print("SAVED", BLEND)
