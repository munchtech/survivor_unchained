"""Her neck shortened in the scene heroine_outfits.py builds from (the owner, 18 October 2026: "our neck is
just too long ... freakishly long"; slightly long is fine, for helmets and gorgets).

    import heroine_neck; heroine_neck.shorten(arm, delta)        (delta in metres; 0 does nothing)

Her Head joint and every bone under it are moved down her neck's own line by `delta` (the line from
neck_01's head to Head's), and every mesh on her skeleton follows by its weights: each vertex moved by
-delta along that line times its weight on those bones (shape keys alike). That is exactly the pose the
game's `--neck-cm -X` draws (HerPose: the Head bone's position moved along neck_01's length, her skin
skinned to it), baked into her rest, so what the owner picked from those pictures is what is built. Her
head, face and hair keep their shapes; only the skin weighted between neck_01 and Head is drawn shorter.
"""
import bpy
import numpy as np


def subtree(arm, root="Head"):
    out, todo = set(), [arm.data.bones[root]]
    while todo:
        b = todo.pop()
        out.add(b.name)
        todo.extend(b.children)
    return out


def shorten(arm, delta):
    if not delta:
        return
    bones = arm.data.bones
    a = np.array((arm.matrix_world @ bones["neck_01"].head_local)[:])
    h = np.array((arm.matrix_world @ bones["Head"].head_local)[:])
    axis = (h - a) / np.linalg.norm(h - a)
    under = subtree(arm)
    shift_w = -delta * axis                     # world space
    moved, objs = 0, []
    for o in bpy.data.objects:
        if o.type != "MESH" or not any(m.type == "ARMATURE" and m.object == arm for m in o.modifiers):
            continue
        gi = {g.index for g in o.vertex_groups if g.name in under}
        deform = {g.index for g in o.vertex_groups if g.name in bones}
        if not gi:
            continue
        me = o.data
        n = len(me.vertices)
        w = np.zeros(n)
        tot = np.zeros(n)
        for v in me.vertices:
            for g in v.groups:
                if g.group in deform:
                    tot[v.index] += g.weight
                    if g.group in gi:
                        w[v.index] += g.weight
        w = np.where(tot > 0, w / np.maximum(tot, 1e-12), 0.0)
        if not (w > 0).any():
            continue
        # the shift in the mesh's own space (a direction: the matrix's linear part only)
        inv = np.array(o.matrix_world.inverted().to_3x3())
        s = inv @ shift_w
        off = w[:, None] * s[None, :]
        co = np.empty(n * 3)
        me.vertices.foreach_get("co", co)
        me.vertices.foreach_set("co", (co.reshape(-1, 3) + off).ravel())
        if me.shape_keys:
            for kb in me.shape_keys.key_blocks:
                k = np.empty(n * 3)
                kb.data.foreach_get("co", k)
                kb.data.foreach_set("co", (k.reshape(-1, 3) + off).ravel())
        me.update()
        moved += int((w > 0).sum())
        objs.append("%s %d" % (o.name, int((w > 0).sum())))
    # the bones: Head and all under it moved down the line; neck_01's tail meets Head's new head
    prev = bpy.context.view_layer.objects.active
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm.data.edit_bones
    sa = np.array(arm.matrix_world.inverted().to_3x3()) @ shift_w
    from mathutils import Vector
    sv = Vector(sa.tolist())
    for nm in under:
        b = eb[nm]
        roll = b.roll
        b.head = b.head + sv
        b.tail = b.tail + sv
        b.roll = roll
    nk = eb["neck_01"]
    roll = nk.roll
    nk.tail = eb["Head"].head.copy()
    nk.roll = roll
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.view_layer.objects.active = prev
    print("NECK shortened %.1f mm along (%.3f %.3f %.3f): %d bones, %d vertices (%s)"
          % (delta * 1000, *axis, len(under), moved, ", ".join(objs)))
