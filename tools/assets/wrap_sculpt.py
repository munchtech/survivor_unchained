"""MakeHuman's base body (built to animate, weighted by hand, rigged) given
the exact shape of a sculpt: the body is aligned to the sculpt in the
sculpt's own pose, shrink-wrapped onto its surface, the wrap's creases
taken out by a corrective smooth that keeps the body's own spacing, and the
result stored as the body's basis. Everything the body was built with
(topology, weights, rig, UVs) is kept.

    blender -b <hero.blend> --python tools/assets/wrap_sculpt.py -- <sculpt.glb> <out.blend> [--check <prefix>]
"""
import math
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ARGS = sys.argv[sys.argv.index("--") + 1:]
SCULPT, OUT = ARGS[0], ARGS[1]
CHECK = ARGS[ARGS.index("--check") + 1] if "--check" in ARGS else ""

body = next(o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("hero_") and "." not in o.name)
rig = next(o for o in bpy.data.objects if o.type == "ARMATURE")
names = [g.name for g in body.vertex_groups]


def active(o):
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o


def evaluated(o, mods=True):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg)
    m = ev.to_mesh()
    co = np.array([(ev.matrix_world @ v.co)[:] for v in m.vertices])
    ev.to_mesh_clear()
    return co


# --------------------------------------------------------- the sculpt --
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=SCULPT)
sculpt = next(o for o in bpy.data.objects if o not in before and o.type == "MESH")
for o in [o for o in bpy.data.objects if o not in before and o != sculpt]:
    bpy.data.objects.remove(o)
active(sculpt)
bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

helpers = {body.vertex_groups[n].index for n in ("HelperGeometry", "JointCubes") if n in body.vertex_groups}
real = np.array([not any(g.group in helpers and g.weight > 0.5 for g in v.groups) for v in body.data.vertices])
for mod in body.modifiers:
    if mod.type == "MASK":
        mod.show_viewport = False
B = evaluated(body)
z0, z1 = B[real, 2].min(), B[real, 2].max()
S = np.array([v.co[:] for v in sculpt.data.vertices])
lo, hi = S.min(0), S.max(0)
S = (S - np.array([(lo[0] + hi[0]) / 2, np.median(S[:, 1]), lo[2]])) * ((z1 - z0) / (hi[2] - lo[2])) + np.array([0, np.median(B[real, 1]), z0])
band = lambda A: A[(A[:, 2] > z0 + (z1 - z0) * 0.66) & (A[:, 2] < z0 + (z1 - z0) * 0.74) & (np.abs(A[:, 0]) < 0.15)]
if np.sign(band(S)[:, 1].mean() - np.median(S[:, 1])) != np.sign(band(B[real])[:, 1].mean() - np.median(B[real, 1])):
    S[:, 1] = 2 * np.median(S[:, 1]) - S[:, 1]
    S[:, 0] *= -1
for i, v in enumerate(sculpt.data.vertices):
    v.co = Vector(S[i])
sculpt.data.update()

# ------------------------------------------- the body in the sculpt's pose --
# Arms lowered (or raised) until the hands are as low as the sculpt's; the
# thighs turned until the ankles stand as far apart.
active(rig)
bpy.ops.object.mode_set(mode="POSE")
for pb in rig.pose.bones:
    pb.rotation_mode = "XYZ"
    pb.rotation_euler = (0, 0, 0)


def tip(name):
    bpy.context.view_layer.update()
    return np.array((rig.matrix_world @ rig.pose.bones[name].tail)[:])


for side, sign in (("l", 1), ("r", -1)):
    target = S[np.argmax(S[:, 0] * sign)]
    pb = rig.pose.bones[f"upperarm_{side}"]
    best = None
    for deg in np.linspace(-60, 60, 121):
        m = (rig.matrix_world @ pb.bone.matrix_local).to_3x3()
        pb.rotation_euler = (m.inverted() @ Matrix.Rotation(math.radians(deg), 3, "Y") @ m).to_euler("XYZ")
        e = abs(tip(f"hand_{side}")[2] - target[2])
        if best is None or e < best[0]:
            best = (e, pb.rotation_euler.copy())
    pb.rotation_euler = best[1]
    print("ARM", side, "error %.3f" % best[0])
ank = S[(S[:, 2] > z0 + 0.06) & (S[:, 2] < z0 + 0.1)]
gap = ank[:, 0].max() - ank[:, 0].min()
best = None
for deg in np.linspace(-12, 12, 49):
    for side, sign in (("l", 1), ("r", -1)):
        rig.pose.bones[f"thigh_{side}"].rotation_euler = (0, 0, math.radians(deg) * sign)
    g = abs(tip("calf_l")[0] - tip("calf_r")[0])
    if best is None or abs(g - gap) < best[0]:
        best = (abs(g - gap), deg)
for side, sign in (("l", 1), ("r", -1)):
    rig.pose.bones[f"thigh_{side}"].rotation_euler = (0, 0, math.radians(best[1]) * sign)
bpy.ops.object.mode_set(mode="OBJECT")

# ----------------------------------------------------------- the wrap --
# Done on a copy of the posed body, mesh only, so the wrap is in the
# sculpt's pose; the offsets are then carried back to the rest pose through
# each vertex's own skinning.
P = evaluated(body)            # posed, every vertex
n = len(P)
tmp = bpy.data.meshes.new("wrap")
tmp.from_pydata([tuple(p) for p in P], [], [list(f.vertices) for f in body.data.polygons])
wrap = bpy.data.objects.new("wrap", tmp)
bpy.context.collection.objects.link(wrap)
grp = wrap.vertex_groups.new(name="wrap")
HEAD = lambda nm: nm in ("head", "neck_01") or any(k in nm for k in ("eye", "jaw", "lip", "tongue", "teeth", "ear"))
EXT = lambda nm: any(k in nm for k in ("hand", "index", "middle", "ring", "pinky", "thumb", "foot", "ball", "toe"))
for i, v in enumerate(body.data.vertices):
    if not real[i]:
        continue
    ex = sum(g.weight for g in v.groups if HEAD(names[g.group]) or EXT(names[g.group]))
    w = max(0.0, 1.0 - ex * 1.2)
    if w > 0:
        grp.add([i], w, "REPLACE")
sw = wrap.modifiers.new("sw", "SHRINKWRAP")
sw.target = sculpt
sw.wrap_method = "NEAREST_SURFACEPOINT"
sw.vertex_group = "wrap"
cs = wrap.modifiers.new("cs", "CORRECTIVE_SMOOTH")
cs.iterations = 12
cs.factor = 0.5
cs.smooth_type = "LENGTH_WEIGHTED"
cs.vertex_group = "wrap"
cs.use_only_smooth = False
cs.rest_source = "ORCO"
sw2 = wrap.modifiers.new("sw2", "SHRINKWRAP")
sw2.target = sculpt
sw2.wrap_method = "PROJECT"
sw2.use_negative_direction = True
sw2.use_positive_direction = True
sw2.project_limit = 0.03
sw2.vertex_group = "wrap"
cs2 = wrap.modifiers.new("cs2", "CORRECTIVE_SMOOTH")
cs2.iterations = 4
cs2.factor = 0.4
cs2.rest_source = "ORCO"
cs2.vertex_group = "wrap"
W = evaluated(wrap)
if "--debug" in ARGS:
    dm = bpy.data.meshes.new("body_posed"); dm.from_pydata([tuple(p) for p in P], [], [list(f.vertices) for f in body.data.polygons])
    bpy.context.collection.objects.link(bpy.data.objects.new("body_posed", dm))
    dm2 = bpy.data.meshes.new("scan_aligned"); dm2.from_pydata([tuple(p) for p in S], [], [list(f.vertices) for f in sculpt.data.polygons])
    bpy.context.collection.objects.link(bpy.data.objects.new("scan_aligned", dm2))
    bpy.ops.wm.save_as_mainfile(filepath=OUT.replace(".blend", "_dbg.blend"))
print("WRAP moved mean %.4f max %.4f" % (np.linalg.norm(W - P, axis=1)[real].mean(), np.linalg.norm(W - P, axis=1).max()))

# Back to rest through the body's skinning.
bones = [b.name for b in rig.data.bones]
mats = {b: np.array(rig.matrix_world @ rig.pose.bones[b].matrix @ rig.data.bones[b].matrix_local.inverted() @ rig.matrix_world.inverted()) for b in bones}
for mod in body.modifiers:
    mod.show_viewport = mod.type not in ("ARMATURE", "MASK")
R0 = evaluated(body)           # rest, shape keys mixed
M = np.zeros((n, 4, 4))
for i, v in enumerate(body.data.vertices):
    tot = 0
    for g in v.groups:
        nm = names[g.group]
        if nm in mats and g.weight > 0:
            M[i] += mats[nm] * g.weight
            tot += g.weight
    M[i] = M[i] / tot if tot > 0 else np.eye(4)
rest = np.einsum("nij,nj->ni", np.linalg.inv(M), np.hstack([W, np.ones((n, 1))]))[:, :3]
delta = rest - R0
me = body.data
key = me.shape_keys.key_blocks.get("sculpt") or body.shape_key_add(name="sculpt", from_mix=False)
basis = me.shape_keys.key_blocks["Basis"]
mix = np.array([basis.data[i].co[:] for i in range(n)])
# The new key holds the mix plus the wrap; every other key is zeroed.
for kb in me.shape_keys.key_blocks:
    if kb.name not in ("Basis", "sculpt"):
        kb.value = 0
for i in range(n):
    key.data[i].co = Vector(R0[i] + delta[i] - (rig.matrix_world.translation[:] and 0))
key.value = 1.0
for mod in body.modifiers:
    mod.show_viewport = True
bpy.data.objects.remove(wrap)
active(rig)
bpy.ops.object.mode_set(mode="POSE")
for pb in rig.pose.bones:
    pb.rotation_euler = (0, 0, 0)
bpy.ops.object.mode_set(mode="OBJECT")
sculpt.hide_render = True
sculpt.hide_set(True)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("WRAPPED", OUT)
