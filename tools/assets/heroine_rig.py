"""Her helper bones built into a body (hers or the hero's), and every mesh
bound to the skeleton split onto them, in Blender. What the helpers are, and
why, is tools/anim/helpers.py; the game drives them (HerJoints.cs).

    import heroine_rig
    heroine_rig.apply(armature, meshes)     # bones added once; weights split

Called by heroine_outfits.py just before it exports: her body and every
piece she wears take the same split, so cloth and skin move as one. The
split only moves weight her upper arms, forearms, collarbones, thighs and
calves already had onto the helpers that lie along them; a body without the
driver moves as it did.
"""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "anim"))
import helpers as hp  # noqa: E402

# Her front in Blender's space (the game's +Z).
FRONT = (0.0, -1.0, 0.0)


def _active(o):
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o


def add_bones(arm):
    """The helper bones, if the armature lacks them: twist bones along their
    parents in their parents' frames; share bones at their joints in the
    lower bone's frame turned about its line onto the joint's hinge."""
    have = {b.name for b in arm.data.bones}
    want = [(h, n) for h in hp.SPEC["helpers"] for n in hp.each(h["name"])]
    if all(n in have for _, n in want):
        return 0
    _active(arm)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm.data.edit_bones
    made = 0
    for h, n in want:
        if n in eb:
            continue
        s = n[-1]
        parent = eb[h["parent"].replace("{s}", s)]
        if h["kind"] in ("share", "point"):
            low = eb[h["bone"].replace("{s}", s)]
            above = low.parent
            g = low.matrix.to_quaternion()
            turn = hp.hinge_turn((g.x, g.y, g.z, g.w), tuple(above.head), tuple(low.head), h["way"], FRONT)
            m = low.matrix @ Matrix.Rotation(math.radians(turn), 4, "Y")
            length = low.length * 0.5
        else:
            main = eb[hp.MAIN_CHILD[parent.name.split("_")[0]] + "_" + s]
            m = parent.matrix.copy()
            m.translation = parent.head + (main.head - parent.head) * h["at"]
            length = 0.04
        b = eb.new(n)
        # (a new bone has no length, and a bone with none takes no frame)
        b.head = (0.0, 0.0, 0.0)
        b.tail = (0.0, length, 0.0)
        b.matrix = m
        b.length = length
        b.parent = parent
        b.use_connect = False
        b.use_deform = True
        made += 1
    bpy.ops.object.mode_set(mode="OBJECT")
    return made


def split_mesh(arm, obj, skin=None, body=None):
    """The mesh's weights onto the helpers (helpers.split), its other vertex
    groups left as they are. With `skin` (a point to the nearest point of her
    skin, in world space), a piece she wears is split where the skin under it
    lies, not where it lies itself: the crease cut and the twist bones'
    reach are read along her skin, so cloth takes the split of the skin it
    covers (split at its own offset, cloth behind a knee was cut deeper into
    the crease than the skin under it, and the skin came through). Points
    far off her (a cape's hem) ease back to their own place."""
    bones = [b.name for b in arm.data.bones]
    index = {n: i for i, n in enumerate(bones)}
    heads = {b.name: np.array((arm.matrix_world @ b.head_local)[:]) for b in arm.data.bones}
    gname = {g.index: g.name for g in obj.vertex_groups}
    # Only points the split can touch: those with weight on a bone a helper
    # helps (collarbone, upper arm, forearm, thigh, calf).
    src = set()
    for pair in hp.SPEC["weights"]["pairs"]:
        for t in pair[:2]:
            src.update(hp.each(t))
    me = obj.data
    rows, pts = [], []
    for v in me.vertices:
        gs = [(gname.get(g.group), g.weight) for g in v.groups]
        if not any(n in src and w > 0 for n, w in gs):
            continue
        rows.append((v.index, gs))
        pts.append((obj.matrix_world @ v.co)[:])
    if not rows:
        return 0
    if skin is not None:
        own = np.array(pts)
        near = np.array([skin(p) for p in pts])
        d = np.linalg.norm(own - near, axis=1)
        t = np.clip((d - SKIN_NEAR) / SKIN_NEAR, 0.0, 1.0)
        t = t * t * (3 - 2 * t)
        pts = near + (own - near) * t[:, None]
    W = np.zeros((len(rows), len(bones)))
    for r, (_, gs) in enumerate(rows):
        for n, w in gs:
            if n in index:
                W[r, index[n]] += w
    W2 = hp.split(W, np.array(pts), index, heads, front=(0.0, -1.0, 0.0))
    if skin is not None and body is not None:
        # Split where the skin lies is not enough: the split reads the
        # piece's own blend between the bones above and below a joint, and a
        # sleeve weighted 60/40 over skin weighted 80/20 still took another
        # share (judge 6: the mismatch's p95 stayed at 0.09, and skin came
        # through behind the knee and at the elbow). So near her, the limb's
        # weight is shared out as the skin's under it is: the piece keeps how
        # much it rides the limb, the skin says on which of its bones.
        W2 = _as_skin(W2, near, t, body, index, src)
    groups = {g.name: g for g in obj.vertex_groups}
    for n in bones:
        if n not in groups and W2[:, index[n]].any():
            groups[n] = obj.vertex_groups.new(name=n)
    bone_set = set(bones)
    for r, (vi, gs) in enumerate(rows):
        for n, _ in gs:
            if n in bone_set:
                groups[n].remove([vi])
        for j in np.nonzero(W2[r] > 1e-4)[0]:
            groups[bones[j]].add([vi], float(W2[r, j]), "REPLACE")
    return len(rows)


# A piece within this of her skin is split as the skin under it; out to twice
# this it eases to its own place.
SKIN_NEAR = 0.03


def skin_sampler(arm, body):
    """Her skin's weights (helpers included) by point: (BVH of her triangles,
    their corners [T, 3], corner points, weights [V, J] by the armature's bone
    order). A body not yet split is split here, in memory, as split_mesh
    would split it."""
    from mathutils.bvhtree import BVHTree
    bones = [b.name for b in arm.data.bones]
    index = {n: i for i, n in enumerate(bones)}
    me = body.data
    me.calc_loop_triangles()
    mw = body.matrix_world
    P = np.array([(mw @ v.co)[:] for v in me.vertices])
    T = np.array([lt.vertices[:] for lt in me.loop_triangles])
    gname = {g.index: g.name for g in body.vertex_groups}
    W = np.zeros((len(P), len(bones)))
    for v in me.vertices:
        for g in v.groups:
            n = gname.get(g.group)
            if n in index:
                W[v.index, index[n]] += g.weight
    if not any(n in gname.values() for n in hp.names()):
        heads = {b.name: np.array((arm.matrix_world @ b.head_local)[:]) for b in arm.data.bones}
        W = hp.split(W, P, index, heads, front=FRONT)
    return BVHTree.FromPolygons([tuple(p) for p in P], T.tolist()), T, P, W


def _as_skin(W2, near, t, body, index, src):
    """W2's weight on the limb's bones (those the helpers help, and the
    helpers) shared out as her skin's at `near`, eased back to W2's own as t
    goes 0 to 1."""
    bvh, T, P, W = body
    # (the hands too: at the wrist a cuff weighted more to the hand than the
    # skin under it took a different twist share; judge 8, the worst points)
    chain = sorted({index[n] for n in set(src) | set(hp.names()) | {"hand_l", "hand_r"} if n in index})
    tri = np.zeros(len(near), int)
    q = np.zeros((len(near), 3))
    for i, p in enumerate(near):
        hit = bvh.find_nearest(Vector(p))
        q[i], tri[i] = hit[0][:], hit[2]
    a, b, c = P[T[tri, 0]], P[T[tri, 1]], P[T[tri, 2]]
    # Barycentric weights of q in its triangle.
    v0, v1, v2 = b - a, c - a, q - a
    d00, d01, d11 = (v0 * v0).sum(1), (v0 * v1).sum(1), (v1 * v1).sum(1)
    d20, d21 = (v2 * v0).sum(1), (v2 * v1).sum(1)
    den = np.maximum(d00 * d11 - d01 * d01, 1e-18)
    bv = np.clip((d11 * d20 - d01 * d21) / den, 0, 1)
    bw = np.clip((d00 * d21 - d01 * d20) / den, 0, 1)
    bu = np.clip(1 - bv - bw, 0, 1)
    s = bu + bv + bw
    Ws = (W[T[tri, 0]][:, chain] * (bu / s)[:, None] + W[T[tri, 1]][:, chain] * (bv / s)[:, None]
          + W[T[tri, 2]][:, chain] * (bw / s)[:, None])
    ssum, gsum = Ws.sum(1), W2[:, chain].sum(1)
    ok = (ssum > 1e-6) & (gsum > 1e-6) & (t < 1.0)
    out = W2.copy()
    target = Ws[ok] * (gsum[ok] / ssum[ok])[:, None]
    tt = t[ok][:, None]
    out[np.ix_(ok.nonzero()[0], chain)] = tt * W2[ok][:, chain] + (1 - tt) * target
    return out


def apply(arm, meshes, skin=None, body=None):
    # Off until a built body has been checked in the game (docs/handoff/animation.md):
    # pass --helpers after the build's "--" to build them in.
    if "--helpers" not in sys.argv:
        print("RIG helpers: off (pass --helpers to build them in)")
        return
    made = add_bones(arm)
    # (her skin's split, read once, for the pieces she wears to share as it)
    sampler = skin_sampler(arm, body) if (skin is not None and body is not None) else None
    total = 0
    for o in meshes:
        if o.type == "MESH":
            total += split_mesh(arm, o, skin, sampler)
    print(f"RIG helpers: {made} bones added; {total} points split onto them")
