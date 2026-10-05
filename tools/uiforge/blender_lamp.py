"""The lamp-iron: Brannoc's forged cage that holds ember, not oil ("no well in it for oil, and
no wick"), hung by a short chain from a page's head band, a live coal in it. Modelled and
rendered in Blender under the house light, lying against the page as the chain does (the
page's up is Blender's +y), its own coal lighting its bars from inside, its shadow caught.

    blender -b -P tools/uiforge/blender_lamp.py -- spec.json OUTDIR

    {"cell": [W, H], "ss": 3, "samples": 128, "material": {...},
     "cage": {"y": 120, "h": 70, "r": 26, "bars": 6, "bar": 2.4},
     "chain": {"links": 3, "length": 30, "width": 18, "wire": 3}, "heat": [5, 16]}

Writes OUTDIR/lamp.png (the coal at rest) and lamp_lit.png (blown bright), file px cells.
"""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import blender_frames as B  # noqa: E402
import blender_chainline as C  # noqa: E402
import blender_coals as K  # noqa: E402

U = B.U


def tube(name, pts, radius, mat):
    """A round bar along a polyline (Blender units)."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = 4
    cu.use_fill_caps = True
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (p[0], p[1], p[2], 1)
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(mat)
    return ob


def ring(name, cy, r, bar, mat, z0):
    """A ring round the lamp's axis (y), at height cy (Blender units)."""
    pts = [(math.cos(a) * r, cy, z0 + math.sin(a) * r) for a in (2 * math.pi * i / 64 for i in range(65))]
    return tube(name, pts, bar, mat)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    spec = json.load(open(argv[0], encoding="utf-8"))
    out = argv[1]
    os.makedirs(out, exist_ok=True)
    C.SPEC.update(spec.get("material", {}))
    sc = B.reset()
    if spec.get("cpu", True):
        sc.cycles.device = "CPU"
    sc.cycles.samples = spec.get("samples", 128)
    B.world()
    B.suns()
    ss = spec.get("ss", 3)
    Wf, Hf = spec["cell"]
    W, H = Wf * ss, Hf * ss
    B.camera(W, H)
    iron = C.iron_chain_material()
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    plane = bpy.context.active_object
    plane.scale = (W * U * 1.5, H * U * 1.5, 1)
    plane.is_shadow_catcher = True

    def P(x, y, z=0.0):
        """File px (y down from the cell's top) to Blender units, the page at z 0."""
        return ((x - Wf / 2) * ss * U, (Hf / 2 - y) * ss * U, z * ss * U)

    cg = spec["cage"]
    r, h, bar = cg["r"], cg["h"], cg["bar"]
    top, foot = cg["y"] - h / 2, cg["y"] + h / 2
    z0 = r + bar                                   # the cage's axis stands off the page by its radius
    # The bars: drawn out round the coal, swelling at the middle.
    for i in range(cg["bars"]):
        a = 2 * math.pi * (i + 0.5) / cg["bars"]
        pts = []
        for j in range(25):
            t = j / 24
            rr = r * (0.55 + 0.45 * math.sin(t * math.pi))
            x, y, z = P(math.cos(a) * rr + Wf / 2, top + t * h, z0 + math.sin(a) * rr)
            pts.append((x, y, z))
        tube(f"bar{i}", pts, bar * ss * U, iron)
    ring("top", P(0, top)[1], r * 0.55 * ss * U, bar * 1.25 * ss * U, iron, z0 * ss * U)
    ring("foot", P(0, foot)[1], r * 0.55 * ss * U, bar * 1.25 * ss * U, iron, z0 * ss * U)
    # Its cap: a low forged cone over the top ring, and the loop it hangs by.
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=r * 0.68 * ss * U, radius2=r * 0.2 * ss * U, depth=h * 0.14 * ss * U)
    cap = bpy.context.active_object
    cap.rotation_euler = (-math.pi / 2, 0, 0)
    cap.location = (0, P(0, top - h * 0.07)[1], z0 * ss * U)
    cap.data.materials.append(iron)
    loop_y = top - h * 0.14 - 6
    tube("loop", [(math.cos(a) * 5 * ss * U, P(0, loop_y)[1] + math.sin(a) * 5 * ss * U, z0 * ss * U) for a in
                  (2 * math.pi * i / 48 for i in range(49))], bar * 1.1 * ss * U, iron)
    # Its foot: a small dish the coal sits in, and a drop finial under it.
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=r * 0.6 * ss * U, radius2=r * 0.3 * ss * U, depth=h * 0.12 * ss * U)
    cup = bpy.context.active_object
    cup.rotation_euler = (math.pi / 2, 0, 0)
    cup.location = (0, P(0, foot - h * 0.03)[1], z0 * ss * U)
    cup.data.materials.append(iron)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=bar * 1.6 * ss * U, location=(0, P(0, foot + h * 0.09)[1], z0 * ss * U))
    fin = bpy.context.active_object
    fin.scale = (1, 1.6, 1)
    fin.data.materials.append(iron)
    # The coal, alive in it.
    coal = K.coal(r * 1.35 * ss, 29)
    coal.location = (0, P(0, cg["y"] + h * 0.12)[1], z0 * ss * U)
    cmat = K.coal_material(3)
    coal.data.materials.append(cmat)
    # The short chain it hangs by, from the band down to its loop: links on end and flat in turn.
    chn = spec["chain"]
    L, Wd, wr = chn["length"] * ss, chn["width"] * ss, chn["wire"] * ss
    pitch = L - 4 * wr
    links = []
    for i in range(chn["links"]):
        cy = loop_y - 5 - (i + 0.5) * pitch / ss
        ob, _ = C.link_mesh(f"hang{i}", L * U, Wd * U, wr * U)
        standing = i % 2 == 0
        ob.rotation_euler = ((math.pi / 2 if standing else 0.0), 0.0, math.pi / 2)
        ob.location = (0, P(0, cy)[1], z0 * ss * U)
        ob.data.materials.append(iron)
        links.append(ob)
    bpy.context.view_layer.update()
    C.mark_wear(links, wr * U)
    # Its coal at rest, then blown bright (a level gained).
    heat = spec.get("heat", [5, 16])
    em = None
    for nd in cmat.node_tree.nodes:
        if nd.type == "MATH" and nd.operation == "MULTIPLY" and abs(nd.inputs[1].default_value - 5.0) < 1e-6:
            em = nd
    for name, hv in (("lamp", heat[0]), ("lamp_lit", heat[1])):
        if em is not None:
            em.inputs[1].default_value = hv
        sc.render.filepath = os.path.join(out, name + ".png")
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
