"""Wrap a survivor's rigged body onto a 3D model of a reference figure (made
from the reference pictures by Pixal3D on the local ComfyUI), keeping her
rig, UVs and sliders: the result is a shape key, `figure_ref`.

    blender -b <hero.blend> --python tools/assets/wrap_to_scan.py -- <scan.glb> <out.blend> [--strength 1.0] [--bust 1.0]

How:
  1. The scan is scaled to the body's height, its soles on the ground, and
     centred.
  2. The body's skeleton is posed to the scan's T-pose: upper arms raised to
     the horizontal, thighs turned in or out until the ankles stand as far
     apart as the scan's.
  3. In that pose, every vertex of the torso and legs (not the head, hands
     or feet, which are the face's and the rig's business) is pulled to the
     nearest point of the scan's surface; the pull is smoothed over the
     surface so the skin stays even, and limited to a few centimetres.
  4. The pull is carried back to the rest pose through each vertex's own
     skinning (the inverse of its blend of bone matrices) and stored as a
     shape key, so it moves with the rig like any other.
"""
import math
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ARGS = sys.argv[sys.argv.index("--") + 1:]
SCAN, OUT = ARGS[0], ARGS[1]
STRENGTH = float(ARGS[ARGS.index("--strength") + 1]) if "--strength" in ARGS else 1.0
BUST = float(ARGS[ARGS.index("--bust") + 1]) if "--bust" in ARGS else 1.0
MAX_PULL = 0.13

body = next(o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("hero_") and "." not in o.name)
rig = next(o for o in bpy.data.objects if o.type == "ARMATURE")
me = body.data
names = [g.name for g in body.vertex_groups]


def gw(v, pred):
    return sum(g.weight for g in v.groups if pred(names[g.group]))


# ------------------------------------------------------------- the scan --
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=SCAN)
scan_objs = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
pts, tris = [], []
for o in scan_objs:
    m = o.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
    base = len(pts)
    pts += [o.matrix_world @ v.co for v in m.vertices]
    m.calc_loop_triangles()
    tris += [tuple(base + i for i in t.vertices) for t in m.loop_triangles]
P = np.array([p[:] for p in pts])
# Its up: the longest of y and z (glTF is y-up; Blender's importer turns it).
lo, hi = P.min(0), P.max(0)
up = 2 if hi[2] - lo[2] >= hi[1] - lo[1] else 1
if up == 1:
    P = P[:, [0, 2, 1]] * np.array([1, -1, 1])
lo, hi = P.min(0), P.max(0)

# The body's rest height, and the scan scaled to it.
rest = np.array([v.co[:] for v in me.vertices])
helpers = {body.vertex_groups[n].index for n in ("HelperGeometry", "JointCubes") if n in body.vertex_groups}
real = np.array([not any(g.group in helpers and g.weight > 0.5 for g in v.groups) for v in me.vertices])
bz0, bz1 = rest[real, 2].min(), rest[real, 2].max()
s = (bz1 - bz0) / (hi[2] - lo[2])
P = (P - np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]])) * s + np.array([0, 0, bz0])
# Facing: the scan's front is -y if its bust is there.
chest = P[(P[:, 2] > bz0 + (bz1 - bz0) * 0.68) & (P[:, 2] < bz0 + (bz1 - bz0) * 0.75)]
if chest[:, 1].mean() > np.median(P[:, 1]):
    P[:, 1] *= -1
    P[:, 0] *= -1
for o in scan_objs:
    bpy.data.objects.remove(o)
bvh = BVHTree.FromPolygons([Vector(p) for p in P], tris)
print("SCAN", len(P), "verts, scale", round(s, 3))

# ------------------------------------------------------------- the pose --
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="POSE")
for pb in rig.pose.bones:
    pb.rotation_mode = "XYZ"
    pb.rotation_euler = (0, 0, 0)


def raise_arm(side):
    """Turn the upper arm until it points straight out to the side."""
    pb = rig.pose.bones[f"upperarm_{side}"]
    bpy.context.view_layer.update()
    head = rig.matrix_world @ pb.head
    tail = rig.matrix_world @ pb.tail
    cur = (tail - head).normalized()
    want = Vector((1 if side == "l" else -1, 0, 0))
    if cur.x * want.x < 0:
        want = -want
    q = cur.rotation_difference(want)
    # Into the bone's own space.
    m = (rig.matrix_world @ pb.bone.matrix_local).to_3x3()
    local = m.inverted() @ q.to_matrix() @ m
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = local.to_quaternion() @ pb.rotation_quaternion


for side in ("l", "r"):
    raise_arm(side)
bpy.context.view_layer.update()

# Ankles as far apart as the scan's.
scan_ank = P[(P[:, 2] > bz0 + 0.05) & (P[:, 2] < bz0 + 0.09)]
scan_gap = np.abs(scan_ank[:, 0]).mean() * 2 if len(scan_ank) else None


def ankle_gap():
    bpy.context.view_layer.update()
    l = rig.matrix_world @ rig.pose.bones["foot_l"].head
    r = rig.matrix_world @ rig.pose.bones["foot_r"].head
    return abs(l.x - r.x)


if scan_gap:
    for side, sign in (("l", 1), ("r", -1)):
        pb = rig.pose.bones[f"thigh_{side}"]
        pb.rotation_mode = "XYZ"
    best = None
    for deg in np.linspace(-10, 10, 41):
        for side, sign in (("l", 1), ("r", -1)):
            rig.pose.bones[f"thigh_{side}"].rotation_euler = (0, 0, math.radians(deg) * sign)
        g = ankle_gap()
        if best is None or abs(g - scan_gap) < best[0]:
            best = (abs(g - scan_gap), deg)
    for side, sign in (("l", 1), ("r", -1)):
        rig.pose.bones[f"thigh_{side}"].rotation_euler = (0, 0, math.radians(best[1]) * sign)
    print("THIGHS", round(best[1], 2), "deg, ankle gap", round(ankle_gap(), 3), "scan", round(scan_gap, 3))
bpy.ops.object.mode_set(mode="OBJECT")
bpy.context.view_layer.update()

# ----------------------------------------------- skinning, both directions --
bone_names = [b.name for b in rig.data.bones]
skin_m = {}
for b in rig.data.bones:
    pb = rig.pose.bones[b.name]
    skin_m[b.name] = np.array(rig.matrix_world @ pb.matrix @ b.matrix_local.inverted() @ rig.matrix_world.inverted())

# The body as it stands now (its shape keys mixed), in the rest pose.
for mod in body.modifiers:
    mod.show_viewport = False
dg = bpy.context.evaluated_depsgraph_get()
ev = body.evaluated_get(dg).to_mesh()
shaped = np.array([v.co[:] for v in ev.vertices])
body.evaluated_get(dg).to_mesh_clear()

n = len(me.vertices)
M = np.zeros((n, 4, 4))
for i, v in enumerate(me.vertices):
    tot = 0
    for g in v.groups:
        nm = names[g.group]
        if nm in skin_m and g.weight > 0:
            M[i] += skin_m[nm] * g.weight
            tot += g.weight
    M[i] = M[i] / tot if tot > 0 else np.eye(4)
homo = np.hstack([shaped, np.ones((n, 1))])
posed = np.einsum("nij,nj->ni", M, homo)[:, :3]

# ------------------------------------------------------- the pull --
# Matched as scan-fitting tools match: a point on the scan counts only if it
# is on the same side of the body and faces the same way as the vertex;
# the body moves a part of the way, is smoothed, and is matched again.
HEAD = lambda nm: nm in ("head", "neck_01") or any(k in nm for k in ("eye", "jaw", "lip", "tongue", "teeth"))
HAND = lambda nm: any(k in nm for k in ("hand", "index", "middle", "ring", "pinky", "thumb", "lowerarm"))
ARMU = lambda nm: nm.startswith("upperarm")
FOOT = lambda nm: any(k in nm for k in ("foot", "ball", "toe"))
BREAST = lambda nm: nm.startswith("breast")
free = np.zeros(n)
bust = np.zeros(n)
for i, v in enumerate(me.vertices):
    if not real[i]:
        continue
    excl = gw(v, HEAD) + gw(v, HAND) + gw(v, FOOT) + gw(v, ARMU) * 0.7
    free[i] = max(0.0, 1.0 - excl * 1.5)
    bust[i] = min(1.0, gw(v, BREAST) * 2)

adj = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices
    adj[a].append(b)
    adj[b].append(a)
faces = [list(p.vertices) for p in me.polygons]


def normals(co):
    nr = np.zeros((n, 3))
    for f in faces:
        a, b, c = co[f[0]], co[f[1]], co[f[2]]
        fn = np.cross(b - a, c - a)
        for j in f:
            nr[j] += fn
    l = np.linalg.norm(nr, axis=1, keepdims=True)
    return nr / np.maximum(l, 1e-9)


def smooth(field, mask, times):
    for _ in range(times):
        nxt = field.copy()
        for i in range(n):
            if mask[i] > 0 and adj[i]:
                nb = [j for j in adj[i] if mask[j] > 0]
                if nb:
                    nxt[i] = 0.4 * field[i] + 0.6 * field[nb].mean(0)
        field = nxt
    return field


# Rigid alignment first: the scan shifted and scaled (about the body's
# middle) to best fit the torso and legs, by nearest points, several times.
core = free > 0.9
for it in range(8):
    tree = BVHTree.FromPolygons([Vector(p) for p in P], tris)
    src, dst = [], []
    for i in np.nonzero(core)[0][::3]:
        co, _, _, d = tree.find_nearest(Vector(posed[i]), 0.15)
        if co is not None:
            src.append(np.array(co[:])); dst.append(posed[i])
    src, dst = np.array(src), np.array(dst)
    cs, cd = src.mean(0), dst.mean(0)
    k = np.sqrt(((dst - cd) ** 2).sum() / max(1e-9, ((src - cs) ** 2).sum()))
    k = float(np.clip(k, 0.9, 1.1))
    P = (P - cs) * k + cd
    print("ALIGN", it, "shift", np.round(cd - cs, 3), "scale %.3f" % k)
bvh = BVHTree.FromPolygons([Vector(p) for p in P], tris)

cur = posed.copy()
for it in range(10):
    nr = normals(cur)
    step = np.zeros((n, 3))
    for i in range(n):
        if free[i] <= 0:
            continue
        p = Vector(cur[i])
        # Along the vertex's own normal both ways first, then the nearest.
        best = None
        for d in (Vector(nr[i]), -Vector(nr[i])):
            hit, hn, _, dist = bvh.ray_cast(p, d, MAX_PULL)
            if hit is not None and (best is None or dist < best[1]):
                best = (hit, dist, hn)
        if best is None:
            co, hn, _, dist = bvh.find_nearest(p, MAX_PULL)
            if co is None:
                continue
            best = (co, dist, hn)
        co, dist, hn = best
        if np.dot(np.array(hn[:]), nr[i]) < 0.2:
            continue
        if abs(cur[i][0]) > 0.02 and np.sign(co.x) != np.sign(cur[i][0]):
            continue
        step[i] = (np.array(co[:]) - cur[i]) * free[i] * (1 + (BUST - 1) * bust[i])
    step = smooth(step, free, 2)
    cur = cur + step * 0.8
    print("ITER", it, "mean step %.4f" % np.linalg.norm(step, axis=1)[free > 0].mean())

pull = smooth(cur - posed, free, 1) * STRENGTH
weight = free

# ------------------------------------------------- back to the rest pose --
target = posed + pull
inv = np.linalg.inv(M)
back = np.einsum("nij,nj->ni", inv, np.hstack([target, np.ones((n, 1))]))[:, :3]
delta_rest = back - shaped

if not me.shape_keys:
    body.shape_key_add(name="Basis")
key = me.shape_keys.key_blocks.get("figure_ref") or body.shape_key_add(name="figure_ref", from_mix=False)
basis = me.shape_keys.key_blocks["Basis"]
for i in range(n):
    key.data[i].co = basis.data[i].co + Vector(delta_rest[i])
key.value = 1.0
key.slider_max = 1.5
if "--debug" in ARGS:
    import bmesh as _bm
    dm = bpy.data.meshes.new("scan_aligned")
    dm.from_pydata([tuple(p) for p in P], [], [list(t) for t in tris])
    bpy.context.collection.objects.link(bpy.data.objects.new("scan_aligned", dm))
    pm = bpy.data.meshes.new("body_posed")
    pm.from_pydata([tuple(p) for p in posed], [], faces)
    bpy.context.collection.objects.link(bpy.data.objects.new("body_posed", pm))
print("PULL mean %.4f max %.4f m" % (np.linalg.norm(pull, axis=1)[weight > 0].mean(), np.linalg.norm(pull, axis=1).max()))

# Back to the rest pose for saving.
for pb in rig.pose.bones:
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = (1, 0, 0, 0)
    pb.rotation_euler = (0, 0, 0)
for mod in body.modifiers:
    mod.show_viewport = True
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("WRAPPED", OUT)
