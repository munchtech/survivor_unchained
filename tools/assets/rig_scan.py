"""Rig a 3D model of a reference figure (TRELLIS 2 from a picture) with the
survivors' skeleton, so the figure in the picture is the figure in the game.

    blender -b <hero.blend> --python tools/assets/rig_scan.py -- <scan.glb> <out.blend> [--faces 60000]

  1. The hero's skeleton is posed to a T-pose (arms out, thighs as the
     scan's stance) and that pose made its rest.
  2. The scan is brought down to a game's weight (its UVs and texture
     kept), scaled to the hero's height, and aligned to the hero's posed
     body by nearest points on the torso and legs.
  3. Each of the scan's vertices takes its bone weights from the nearest
     point of the posed body's surface, and the scan is bound to the
     skeleton.
"""
import math
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ARGS = sys.argv[sys.argv.index("--") + 1:]
SCAN, OUT = ARGS[0], ARGS[1]
FACES = int(ARGS[ARGS.index("--faces") + 1]) if "--faces" in ARGS else 60000

body = next(o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("hero_") and "." not in o.name)
rig = next(o for o in bpy.data.objects if o.type == "ARMATURE")


def set_active(o):
    bpy.ops.object.mode_set(mode="OBJECT") if bpy.context.object and bpy.context.object.mode != "OBJECT" else None
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o


# ---------------------------------------------------------- the scan --
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=SCAN)
parts = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
set_active(parts[0])
for o in parts:
    o.select_set(True)
if len(parts) > 1:
    bpy.ops.object.join()
scan = bpy.context.view_layer.objects.active
scan.name = "hero_scan"
bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
for o in [o for o in bpy.data.objects if o not in before and o != scan]:
    bpy.data.objects.remove(o)
print("SCAN", len(scan.data.polygons), "faces")
dec = scan.modifiers.new("dec", "DECIMATE")
dec.ratio = min(1.0, FACES / max(1, len(scan.data.polygons)))
bpy.ops.object.modifier_apply(modifier="dec")
print("DECIMATED", len(scan.data.polygons), "faces")

# ------------------------------------------- the skeleton in T-pose --
set_active(rig)
bpy.ops.object.mode_set(mode="POSE")
for pb in rig.pose.bones:
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = (1, 0, 0, 0)
for side in ("l", "r"):
    pb = rig.pose.bones[f"upperarm_{side}"]
    bpy.context.view_layer.update()
    head, tail = rig.matrix_world @ pb.head, rig.matrix_world @ pb.tail
    cur = (tail - head).normalized()
    want = Vector((1 if cur.x > 0 else -1, 0, 0))
    q = cur.rotation_difference(want)
    m = (rig.matrix_world @ pb.bone.matrix_local).to_3x3()
    pb.rotation_quaternion = (m.inverted() @ q.to_matrix() @ m).to_quaternion()
bpy.context.view_layer.update()
bpy.ops.object.mode_set(mode="OBJECT")

# The body as it stands in that pose (shape keys mixed, rig applied).
for mod in body.modifiers:
    mod.show_viewport = mod.type == "ARMATURE"
dg = bpy.context.evaluated_depsgraph_get()
ev = body.evaluated_get(dg)
bm = ev.to_mesh()
posed_co = [ev.matrix_world @ v.co for v in bm.vertices]
posed_faces = [list(p.vertices) for p in bm.polygons]
ev.to_mesh_clear()
names = [g.name for g in body.vertex_groups]
helpers = {body.vertex_groups[n].index for n in ("HelperGeometry", "JointCubes") if n in body.vertex_groups}
real = [not any(g.group in helpers and g.weight > 0.5 for g in v.groups) for v in body.data.vertices]
posed_faces = [f for f in posed_faces if all(real[i] for i in f)]
body_tree = BVHTree.FromPolygons(posed_co, posed_faces)
PB = np.array([c[:] for c in posed_co])

# ---------------------------------------------- the scan, aligned --
S = np.array([(scan.matrix_world @ v.co)[:] for v in scan.data.vertices])
lo, hi = S.min(0), S.max(0)
if hi[1] - lo[1] > hi[2] - lo[2]:          # y-up: turn to z-up
    S = S[:, [0, 2, 1]] * np.array([1, -1, 1])
    lo, hi = S.min(0), S.max(0)
reals = PB[np.array(real)]
bz0, bz1 = reals[:, 2].min(), reals[:, 2].max()
S = (S - np.array([(lo[0] + hi[0]) / 2, 0, lo[2]])) * ((bz1 - bz0) / (hi[2] - lo[2])) + np.array([0, 0, bz0])
S[:, 1] -= np.median(S[:, 1]) - np.median(reals[:, 1])
# Facing the same way: the bust is the front.
band = lambda A: A[(A[:, 2] > bz0 + (bz1 - bz0) * 0.68) & (A[:, 2] < bz0 + (bz1 - bz0) * 0.75)]
if np.sign(band(S)[:, 1].mean() - np.median(S[:, 1])) != np.sign(band(reals)[:, 1].mean() - np.median(reals[:, 1])):
    S[:, 1] = 2 * np.median(S[:, 1]) - S[:, 1]
    S[:, 0] *= -1
torso = (reals[:, 2] > bz0 + (bz1 - bz0) * 0.3) & (reals[:, 2] < bz0 + (bz1 - bz0) * 0.78) & (np.abs(reals[:, 0]) < 0.2)
core = reals[torso][::4]
for it in range(10):
    tree = BVHTree.FromPolygons([Vector(p) for p in S], [list(p.vertices) for p in scan.data.polygons])
    src, dst = [], []
    for p in core:
        co, _, _, d = tree.find_nearest(Vector(p), 0.15)
        if co is not None:
            src.append(co[:]); dst.append(p)
    src, dst = np.array(src), np.array(dst)
    cs, cd = src.mean(0), dst.mean(0)
    k = float(np.clip(np.sqrt(((dst - cd) ** 2).sum() / ((src - cs) ** 2).sum()), 0.92, 1.08))
    S = (S - cs) * k + cd
print("ALIGNED", np.round(cd - cs, 4), round(k, 4))
for i, v in enumerate(scan.data.vertices):
    v.co = Vector(S[i])
scan.matrix_world = rig.matrix_world.copy() if False else scan.matrix_world
scan.data.update()

# --------------------------------------------------- the weights --
for g in body.vertex_groups:
    scan.vertex_groups.new(name=g.name)
bw = [{names[g.group]: g.weight for g in v.groups if names[g.group] in rig.data.bones} for v in body.data.vertices]
for i, v in enumerate(scan.data.vertices):
    co, _, fi, _ = body_tree.find_nearest(v.co)
    f = posed_faces[fi]
    # Barycentric-ish: weights of the face's corners by inverse distance.
    ds = [max(1e-6, (posed_co[j] - co).length) for j in f]
    inv = [1 / d for d in ds]
    tot = sum(inv)
    acc = {}
    for j, w in zip(f, inv):
        for nm, wt in bw[j].items():
            acc[nm] = acc.get(nm, 0) + wt * w / tot
    s = sum(acc.values()) or 1
    for nm, wt in acc.items():
        if wt / s > 0.01:
            scan.vertex_groups[nm].add([i], wt / s, "REPLACE")
for g in list(scan.vertex_groups):
    if g.name not in rig.data.bones:
        scan.vertex_groups.remove(g)

# --------------------------------------------- the T-pose as rest --
set_active(rig)
bpy.ops.object.mode_set(mode="POSE")
bpy.ops.pose.armature_apply(selected=False)
bpy.ops.object.mode_set(mode="OBJECT")
mod = scan.modifiers.new("rig", "ARMATURE")
mod.object = rig
scan.parent = rig
# The old body stays in the file, hidden, for reference.
body.hide_set(True)
body.hide_render = True
for o in bpy.data.objects:
    if o.type == "MESH" and o.name.startswith(body.name + "."):
        o.hide_set(True)
        o.hide_render = True
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("RIGGED", OUT)
