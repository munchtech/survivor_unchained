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
from mathutils import Matrix

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
        if h["kind"] == "share":
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


def split_mesh(arm, obj):
    """The mesh's weights onto the helpers (helpers.split), its other vertex
    groups left as they are."""
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
    W = np.zeros((len(rows), len(bones)))
    for r, (_, gs) in enumerate(rows):
        for n, w in gs:
            if n in index:
                W[r, index[n]] += w
    W2 = hp.split(W, np.array(pts), index, heads, front=(0.0, -1.0, 0.0))
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


def apply(arm, meshes):
    # Off until a built body has been checked in the game (docs/handoff/animation.md):
    # pass --helpers after the build's "--" to build them in.
    if "--helpers" not in sys.argv:
        print("RIG helpers: off (pass --helpers to build them in)")
        return
    made = add_bones(arm)
    total = 0
    for o in meshes:
        if o.type == "MESH":
            total += split_mesh(arm, o)
    print(f"RIG helpers: {made} bones added; {total} points split onto them")
