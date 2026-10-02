"""Bind a 3D model of a reference figure (TRELLIS 2 from a picture) to the
game's own skeleton (the Quaternius one the Universal Animation Libraries
play on), taking her bone weights from a body already rigged to it, so
every clip the game has plays on her as it is.

    blender -b --python tools/assets/bind_scan.py -- <scan.glb> <rigged.glb> <out.glb> [--faces 60000] [--smooth 3]

Both stand in a T-pose facing -Y. The scan is brought to a game's weight
(UVs and texture kept), scaled to the rigged body's height, aligned to its
torso and legs by nearest points, and each of its vertices takes the
weights of the nearest point of the rigged body's surface; the weights are
then smoothed a little over the scan, so a stride does not crease it.
"""
import sys

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ARGS = sys.argv[sys.argv.index("--") + 1:]
SCAN, RIGGED, OUT = ARGS[0], ARGS[1], ARGS[2]
FACES = int(ARGS[ARGS.index("--faces") + 1]) if "--faces" in ARGS else 60000
SMOOTH = int(ARGS[ARGS.index("--smooth") + 1]) if "--smooth" in ARGS else 3

bpy.ops.wm.read_factory_settings(use_empty=True)


def active(o):
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o


# The rigged body and its skeleton.
bpy.ops.import_scene.gltf(filepath=RIGGED)
rig = next(o for o in bpy.data.objects if o.type == "ARMATURE")
ref = max((o for o in bpy.data.objects if o.type == "MESH" and o.find_armature() == rig), key=lambda o: len(o.data.vertices))
for o in [o for o in bpy.data.objects if o.type == "MESH" and o != ref]:
    bpy.data.objects.remove(o)
dg = bpy.context.evaluated_depsgraph_get()
evr = ref.evaluated_get(dg)
rm = evr.to_mesh()
R_co = [evr.matrix_world @ v.co for v in rm.vertices]
R_f = [list(p.vertices) for p in rm.polygons]
evr.to_mesh_clear()
R = np.array([c[:] for c in R_co])
tree_r = BVHTree.FromPolygons(R_co, R_f)
rnames = [g.name for g in ref.vertex_groups]
rw = [{rnames[g.group]: g.weight for g in v.groups if rnames[g.group] in rig.data.bones and g.weight > 0} for v in ref.data.vertices]

# The scan.
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=SCAN)
parts = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
active(parts[0])
for o in parts:
    o.select_set(True)
if len(parts) > 1:
    bpy.ops.object.join()
scan = bpy.context.view_layer.objects.active
scan.name = "Woman"
bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
for o in [o for o in bpy.data.objects if o not in before and o != scan]:
    bpy.data.objects.remove(o)
if len(scan.data.polygons) > FACES:
    dec = scan.modifiers.new("dec", "DECIMATE")
    dec.ratio = FACES / len(scan.data.polygons)
    bpy.ops.object.modifier_apply(modifier="dec")
print("SCAN", len(scan.data.polygons), "faces")

S = np.array([v.co[:] for v in scan.data.vertices])
lo, hi = S.min(0), S.max(0)
z0, z1 = R[:, 2].min(), R[:, 2].max()
S = (S - np.array([(lo[0] + hi[0]) / 2, np.median(S[:, 1]), lo[2]])) * ((z1 - z0) / (hi[2] - lo[2])) + np.array([0, np.median(R[:, 1]), z0])
band = lambda A: A[(A[:, 2] > z0 + (z1 - z0) * 0.68) & (A[:, 2] < z0 + (z1 - z0) * 0.75) & (np.abs(A[:, 0]) < 0.2)]
if np.sign(band(S)[:, 1].mean() - np.median(S[:, 1])) != np.sign(band(R)[:, 1].mean() - np.median(R[:, 1])):
    S[:, 1] = 2 * np.median(S[:, 1]) - S[:, 1]
    S[:, 0] *= -1
    print("TURNED")
core = R[(R[:, 2] > z0 + (z1 - z0) * 0.3) & (R[:, 2] < z0 + (z1 - z0) * 0.78) & (np.abs(R[:, 0]) < 0.2)][::3]
faces = [list(p.vertices) for p in scan.data.polygons]
for it in range(10):
    t = BVHTree.FromPolygons([Vector(p) for p in S], faces)
    src, dst = [], []
    for p in core:
        co, _, _, d = t.find_nearest(Vector(p), 0.15)
        if co is not None:
            src.append(co[:]); dst.append(p)
    src, dst = np.array(src), np.array(dst)
    cs, cd = src.mean(0), dst.mean(0)
    k = float(np.clip(np.sqrt(((dst - cd) ** 2).sum() / ((src - cs) ** 2).sum()), 0.92, 1.08))
    S = (S - cs) * k + cd
print("ALIGNED", np.round(cd - cs, 4), round(k, 4))
for i, v in enumerate(scan.data.vertices):
    v.co = Vector(S[i])
scan.data.update()

# Weights from the nearest point of the rigged body.
bones = [b.name for b in rig.data.bones]
W = np.zeros((len(S), len(bones)))
bi = {b: i for i, b in enumerate(bones)}
for i in range(len(S)):
    co, _, fi, _ = tree_r.find_nearest(Vector(S[i]))
    f = R_f[fi]
    inv = np.array([1 / max(1e-6, (R_co[j] - co).length) for j in f])
    inv /= inv.sum()
    for j, w in zip(f, inv):
        for nm, wt in rw[j].items():
            W[i, bi[nm]] += wt * w
# Smoothed over the scan's own surface.
adj = [[] for _ in range(len(S))]
for e in scan.data.edges:
    a, b = e.vertices
    adj[a].append(b)
    adj[b].append(a)
for _ in range(SMOOTH):
    N = W.copy()
    for i in range(len(S)):
        if adj[i]:
            N[i] = 0.5 * W[i] + 0.5 * W[adj[i]].mean(0)
    W = N
W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
for b in bones:
    scan.vertex_groups.new(name=b)
for i in range(len(S)):
    top = np.argsort(-W[i])[:4]
    tot = W[i, top].sum()
    for j in top:
        if W[i, j] > 0.01:
            scan.vertex_groups[bones[j]].add([i], float(W[i, j] / tot), "REPLACE")

bpy.data.objects.remove(ref)
scan.parent = rig
mod = scan.modifiers.new("Armature", "ARMATURE")
mod.object = rig
active(rig)
scan.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True, export_skins=True, export_animations=False,
                          export_yup=True, export_apply=False)
print("BOUND", OUT)
