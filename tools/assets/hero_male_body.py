"""The hero (the man the player can be) from AccuRIG's rig of his sculpt, on
the game's own skeleton: build_heroine.py's way, for his body.

    blender -b --python tools/assets/hero_male_body.py -- <accurig.fbx> <ual.glb> <sculpt.glb> <out.blend> [check dir]

His sculpt is TRELLIS 2's (ComfyUI_00008.glb: 700k triangles, 4K paint), and
AccuRIG rigged a reduced copy of it whose UVs no longer fit the paint. So:

  1. AccuRIG's mesh is brought to his height (HEIGHT), his feet on the ground,
     and reduced to a game's budget (FACES), symmetric, its weights carried.
  2. It is unwrapped afresh, and his paint and his relief are baked onto it
     from the full sculpt: the colour, and a normal map that keeps every
     muscle, vein and crease the reduction smoothed away.
  3. The library's skeleton (UAL) is laid along his T-pose and given his
     joints, and AccuRIG's weights are folded onto its bones, exactly as
     build_heroine.py does for her (see there for why).

His head is hero_male_head.py's, made after on the scene saved here.
"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from scipy.spatial import cKDTree

sys.stdout.reconfigure(line_buffering=True)
ARGS = sys.argv[sys.argv.index("--") + 1:]
CC_FBX, UAL, SCULPT, OUT = ARGS[:4]
CHECK = ARGS[4] if len(ARGS) > 4 else None
HEIGHT = 1.98          # metres, crown to sole: a head over the heroine (1.87)
FACES = 110_000        # triangles for his body (hers is 49k; his muscle needs more silhouette)
PAINT = 4096           # his paint and normal map
TEXDIR = os.path.join(os.path.dirname(os.path.abspath(OUT)), "hero_tex")
os.makedirs(TEXDIR, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)


def active(o):
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o


def world_co(o):
    return np.array([(o.matrix_world @ v.co)[:] for v in o.data.vertices])


# ------------------------------------------------------------- AccuRIG --
bpy.ops.import_scene.fbx(filepath=CC_FBX)
cc = next(o for o in bpy.data.objects if o.type == "ARMATURE")
body = next(o for o in bpy.data.objects if o.type == "MESH")
for o in (body, cc):
    o.animation_data_clear()
active(body)
cc.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = world_co(body)
k = HEIGHT / (co[:, 2].max() - co[:, 2].min())
cc.scale = (k, k, k)
bpy.context.view_layer.update()
active(cc)
body.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = world_co(body)
# (His feet on the ground, his middle on the axis.)
shift = Vector((-(co[:, 0].max() + co[:, 0].min()) / 2, 0, -co[:, 2].min()))
cc.location = shift
bpy.context.view_layer.update()
active(cc)
body.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = world_co(body)
print("ACCURIG", len(co), "points, %.3f m tall, %.3f m across" % (co[:, 2].ptp() if hasattr(co[:, 2], "ptp") else np.ptp(co[:, 2]), np.ptp(co[:, 0])))

# ---------------------------------------------------- the sculpt, matched --
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=SCULPT)
hi = next(o for o in bpy.data.objects if o not in before and o.type == "MESH")
for o in [o for o in bpy.data.objects if o not in before and o != hi]:
    bpy.data.objects.remove(o)
active(hi)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
hco = world_co(hi)
hk = HEIGHT / np.ptp(hco[:, 2])
hi.scale = (hk, hk, hk)
bpy.context.view_layer.update()
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
hco = world_co(hi)
# Moved onto AccuRIG's copy: centres matched, then each of AccuRIG's points
# to the sculpt's nearest, the mean of what is left (a translation; the two
# are the same shape at the same size).
off = (co.min(0) + co.max(0)) / 2 - (hco.min(0) + hco.max(0)) / 2
tree = cKDTree(hco[::3])
probe = co[::7]
for _ in range(8):
    d, i = tree.query(probe - off)
    ok = d < np.percentile(d, 80)
    off = off + (probe[ok] - off - hco[::3][i[ok]]).mean(0)
d, _ = tree.query(probe - off)
hi.location = Vector(off)
bpy.context.view_layer.update()
active(hi)
bpy.ops.object.transform_apply(location=True)
print("SCULPT matched: moved", np.round(off, 4), "residual mean %.2f mm, 99th %.2f mm" % (1000 * d.mean(), 1000 * np.percentile(d, 99)))

# --------------------------------------------------------------- reduced --
for mod in list(body.modifiers):
    body.modifiers.remove(mod)
body.parent = None
# AccuRIG's copy comes split along its old seams (a point for every corner
# that differed): welded first, or the reduction keeps every split as an edge.
_bm = bmesh.new()
_bm.from_mesh(body.data)
_n0 = len(_bm.verts)
bmesh.ops.remove_doubles(_bm, verts=_bm.verts, dist=1e-5)
_bm.to_mesh(body.data)
_bm.free()
print("WELDED", _n0, "points to", len(body.data.vertices))
active(body)
dec = body.modifiers.new("Reduce", "DECIMATE")
dec.decimate_type = "COLLAPSE"
dec.ratio = FACES / len(body.data.polygons)
dec.use_symmetry = True
dec.symmetry_axis = "X"
dec.use_collapse_triangulate = True
bpy.ops.object.modifier_apply(modifier="Reduce")
print("REDUCED to", len(body.data.polygons), "faces,", len(body.data.vertices), "points")

# Unwrapped afresh (AccuRIG's copy's UVs fit nothing).
while body.data.uv_layers:
    body.data.uv_layers.remove(body.data.uv_layers[0])
body.data.uv_layers.new(name="UVMap")
active(body)
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.002, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
bpy.ops.uv.pack_islands(rotate=True, margin=0.002)
bpy.ops.object.mode_set(mode="OBJECT")
for p in body.data.polygons:
    p.use_smooth = True

# ---------------------------------------------------------------- baked --
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 1
sc.render.bake.use_selected_to_active = True
sc.render.bake.cage_extrusion = 0.012
sc.render.bake.max_ray_distance = 0.03
sc.render.bake.margin = 16


def bake_image(name, colour):
    img = bpy.data.images.new(name, PAINT, PAINT, alpha=False, float_buffer=False)
    img.colorspace_settings.name = "sRGB" if colour else "Non-Color"
    return img


paint = bake_image("hero_body_paint", True)
normal = bake_image("hero_body_normal", False)
mat = bpy.data.materials.new("hero_skin")
mat.use_nodes = True
nt = mat.node_tree
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = paint
ntex = nt.nodes.new("ShaderNodeTexImage")
ntex.image = normal
nmap = nt.nodes.new("ShaderNodeNormalMap")
bsdf = nt.nodes["Principled BSDF"]
nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
nt.links.new(ntex.outputs["Color"], nmap.inputs["Color"])
nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
body.data.materials.clear()
body.data.materials.append(mat)
active(hi)
body.select_set(True)
bpy.context.view_layer.objects.active = body
# (The sculpt's paint is lit by nothing: its colour alone.)
nt.nodes.active = tex
bpy.ops.object.bake(type="DIFFUSE", pass_filter={"COLOR"})
nt.nodes.active = ntex
bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT")
for img, fn in ((paint, "hero_body_paint.png"), (normal, "hero_body_normal.png")):
    img.filepath_raw = os.path.join(TEXDIR, fn)
    img.file_format = "PNG"
    img.save()
    img.filepath = img.filepath_raw
print("BAKED paint and normals, %d px" % PAINT)
bpy.data.objects.remove(hi)

# ------------------------------------------------- the library's skeleton --
CCJ = {b.name: (cc.matrix_world @ b.head_local, cc.matrix_world @ b.tail_local) for b in cc.data.bones}


def side(q, c):
    return {f"{q}_l": c.replace("{S}", "L"), f"{q}_r": c.replace("{S}", "R")}


JOINT = {"pelvis": "CC_Base_Pelvis", "spine_01": "CC_Base_Waist", "spine_02": "CC_Base_Spine01", "spine_03": "CC_Base_Spine02",
         "neck_01": "CC_Base_NeckTwist01", "Head": "CC_Base_Head"}
for q, c in (("clavicle", "CC_Base_{S}_Clavicle"), ("upperarm", "CC_Base_{S}_Upperarm"), ("lowerarm", "CC_Base_{S}_Forearm"),
             ("hand", "CC_Base_{S}_Hand"), ("thigh", "CC_Base_{S}_Thigh"), ("calf", "CC_Base_{S}_Calf"), ("foot", "CC_Base_{S}_Foot"),
             ("ball", "CC_Base_{S}_ToeBase")):
    JOINT.update(side(q, c))
for f, cf in (("index", "Index"), ("middle", "Mid"), ("ring", "Ring"), ("pinky", "Pinky"), ("thumb", "Thumb")):
    for n in (1, 2, 3):
        JOINT.update(side(f"{f}_0{n}", f"CC_Base_{{S}}_{cf}{n}"))

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
                 f"CC_Base_{S}_ToeBase": f"ball_{s}", f"CC_Base_{S}_ToeBaseShareBone": f"ball_{s}",
                 # (his chest's own bones, which AccuRIG gives every body: his chest)
                 f"CC_Base_{S}_RibsTwist": "spine_03", f"CC_Base_{S}_Breast": "spine_03"})
    for t in ("BigToe1", "IndexToe1", "MidToe1", "RingToe1", "PinkyToe1"):
        FOLD[f"CC_Base_{S}_{t}"] = f"ball_{s}"
    for f, cf in (("index", "Index"), ("middle", "Mid"), ("ring", "Ring"), ("pinky", "Pinky"), ("thumb", "Thumb")):
        for n in (1, 2, 3):
            FOLD[f"CC_Base_{S}_{cf}{n}"] = f"{f}_0{n}_{s}"

before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=UAL)
q = next(o for o in bpy.data.objects if o not in before and o.type == "ARMATURE")
for o in [o for o in bpy.data.objects if o not in before and o != q]:
    bpy.data.objects.remove(o)
q.animation_data_clear()
active(q)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# 1. Turned bone by bone, parents first, onto his directions.
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
        pick = None
        for pref in ("lowerarm", "hand", "calf", "foot", "ball", "spine", "neck", "Head", "middle_01", "upperarm"):
            pick = next((c for c in kids if c.name.startswith(pref)), None)
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
print("TURNED", turned, "bones")

# 2. His joints: each head where AccuRIG put it, the line and roll kept.
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
for e in eb:
    if e.name.endswith("_leaf_l") or e.name.endswith("_leaf_r"):
        p = e.parent
        if p:
            d = e.tail - e.head
            e.head = p.tail
            e.tail = p.tail + d
bpy.ops.object.mode_set(mode="OBJECT")
print("JOINTS", moved, "placed")

# 3. His weights, folded onto the library's bones (four at most, as the game takes).
names = [g.name for g in body.vertex_groups]
acc = {}
for v in body.data.vertices:
    w = {}
    for g in v.groups:
        tgt = FOLD.get(names[g.group])
        if tgt and tgt in q.data.bones:
            w[tgt] = w.get(tgt, 0) + g.weight
    acc[v.index] = w
print("UNFOLDED", sorted({n for n in names if n not in FOLD}))
for g in list(body.vertex_groups):
    body.vertex_groups.remove(g)
for b in q.data.bones:
    body.vertex_groups.new(name=b.name)
bare = 0
for i, w in acc.items():
    top = sorted(w.items(), key=lambda kv: -kv[1])[:4]
    t4 = sum(x for _, x in top)
    if t4 <= 0:
        bare += 1
        continue
    for nm, x in top:
        if x / t4 > 0.005:
            body.vertex_groups[nm].add([i], x / t4, "REPLACE")
print("WEIGHTS folded;", bare, "points had none")
body.parent = q
mod = body.modifiers.new("Armature", "ARMATURE")
mod.object = q
bpy.data.objects.remove(cc)
q.name = "Armature"
body.name = "Hero"

bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(OUT))
print("SAVED", OUT)
