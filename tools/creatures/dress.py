"""What a beast's sculpt can't carry, made in Blender (inside bpy): tusks
modelled as curved, tapering horns of ivory, and bristle cards for a crest,
a fringe or a tail's tuft, cut from the drawn atlas (bristles.py).
"""
import math
import random

import bmesh
import bpy
from mathutils import Vector


def bezier(p0, p1, p2, p3, t):
    u = 1 - t
    return p0 * u * u * u + p1 * 3 * u * u * t + p2 * 3 * u * t * t + p3 * t * t * t


def horn(name, path, r0, r1=0.0, rings=12, sides=8, flat=0.75, twist=0.0, keel=None):
    """A tapering horn along a path of points: rings of `sides` vertices,
    from radius r0 at the root to r1 at the tip (closed to a point), its
    section pressed flat across (flat < 1) like a tusk's, the flat side
    facing `keel` (a direction, or none). UVs: u round it, v along it."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    pts = [Vector(p) for p in path]
    n = len(pts)
    rings_v = []
    up = Vector((0, 0, 1))
    for i, p in enumerate(pts):
        t = i / (n - 1)
        tan = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        side = (keel if keel is not None else up).cross(tan)
        if side.length < 1e-5:
            side = Vector((1, 0, 0)).cross(tan)
        side.normalize()
        nrm = tan.cross(side).normalized()
        # A tusk thins slowly then sharpens: the radius falls off faster near the tip.
        r = r1 + (r0 - r1) * (1 - t ** 1.6)
        ring = []
        if i == n - 1:
            ring = [bm.verts.new(p)]
        else:
            for k in range(sides):
                a = 2 * math.pi * k / sides + twist * t
                off = side * math.cos(a) * r * flat + nrm * math.sin(a) * r
                ring.append(bm.verts.new(p + off))
        rings_v.append(ring)
    for i in range(n - 1):
        a, b = rings_v[i], rings_v[i + 1]
        for k in range(sides):
            k2 = (k + 1) % sides
            if len(b) == 1:
                f = bm.faces.new((a[k], a[k2], b[0]))
                coords = [(k / sides, i / (n - 1)), ((k + 1) / sides, i / (n - 1)), ((k + 0.5) / sides, 1.0)]
            else:
                f = bm.faces.new((a[k], a[k2], b[k2], b[k]))
                coords = [(k / sides, i / (n - 1)), ((k + 1) / sides, i / (n - 1)), ((k + 1) / sides, (i + 1) / (n - 1)), (k / sides, (i + 1) / (n - 1))]
            for loop, c in zip(f.loops, coords):
                loop[uv].uv = c
    # The root capped (it sits inside the jaw, but a crowd sees through nothing).
    cap = bm.faces.new(list(reversed(rings_v[0])))
    for loop in cap.loops:
        loop[uv].uv = (0.5, 0.0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    for p in me.polygons:
        p.use_smooth = True
    return obj


def tusk(name, root, out, up, fwd, length, r0, sweep=(0.35, 0.75, -0.2), curl=0.25, rings=12, sides=8):
    """A tusk from its root: out of the jaw `out`-wards (the beast's side),
    up, and curling back over itself at the tip. `sweep`: where the tip
    ends, as (out, up, forward) shares of its length."""
    root = Vector(root)
    o, u, f = Vector(out).normalized(), Vector(up).normalized(), Vector(fwd).normalized()
    tip = root + (o * sweep[0] + u * sweep[1] + f * sweep[2]) * length
    p1 = root + (o * 0.25 + u * 0.15 + f * 0.25) * length
    p2 = root + (o * (sweep[0] + 0.1) + u * (sweep[1] * 0.75) + f * (sweep[2] + curl)) * length
    path = [bezier(root, p1, p2, tip, i / rings) for i in range(rings + 1)]
    return horn(name, path, r0, 0.0, rings=rings, sides=sides, flat=0.7, keel=o)


def cards(name, roots, uvcols, columns, rng_seed=5):
    """Bristle cards: each a strip rooted at a point and running along a
    direction, bending as it goes, cut from one column of the atlas.

    roots: [(root, direction, bend_axis, length, width, bend, column_kind)]
    uvcols: {kind: [column indices]}; columns: how many in the atlas."""
    rng = random.Random(rng_seed)
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    for root, d, axis, length, width, bend, kind in roots:
        col = rng.choice(uvcols[kind])
        u0, u1 = col / columns, (col + 1) / columns
        root, d, axis = Vector(root), Vector(d).normalized(), Vector(axis).normalized()
        across = d.cross(axis).normalized()  # the card's width runs across its bend
        segs = 3
        rows = []
        for i in range(segs + 1):
            t = i / segs
            # The strand bends about the axis as it goes (stiff at the root).
            ang = bend * t * t
            q = d.copy()
            q.rotate(__import__("mathutils").Quaternion(axis, ang))
            p = root + q * length * t
            w = width * (1 - 0.35 * t)
            rows.append((bm.verts.new(p - across * w / 2), bm.verts.new(p + across * w / 2), t))
        for i in range(segs):
            a0, a1, ta = rows[i]
            b0, b1, tb = rows[i + 1]
            f = bm.faces.new((a0, a1, b1, b0))
            # v: 0 at the root (the atlas's top) to 1 at the tip.
            for loop, c in zip(f.loops, [(u0, 1 - ta), (u1, 1 - ta), (u1, 1 - tb), (u0, 1 - tb)]):
                loop[uv].uv = c
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    return obj
