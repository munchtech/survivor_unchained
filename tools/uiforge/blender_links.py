"""Single chain links, each its own sprite, for a chain the code lays out and moves (the tab
chain): face-on ones and ones on edge, no two alike, worn where their neighbours would rub
them; each rendered cold, warm (dull red, cooling) and hot (drawn from the fire) with the same
geometry, so the code can heat a link by fading between them; and one pried open and hot (the
emblem, the chosen tab's middle link). Rendered in Blender under the house light, each with
its shadow caught on the page.

    blender -b -P tools/uiforge/blender_links.py -- spec.json OUTDIR

    {"cell": [W, H], "ss": 3, "samples": 64, "link": {"length": 60, "width": 38, "wire": 6.4},
     "pitch": 34, "variants": 6, "seed": 5, "material": {...}}

Writes OUTDIR/face_K.png, edge_K.png, warm_face_K.png, warm_edge_K.png, hot_face_K.png,
hot_edge_K.png (K < variants) and open.png: cells of W x H file px, the link at the centre,
its long axis along x.
"""
import json
import math
import os
import random
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import blender_frames as B  # noqa: E402
import blender_chainline as C  # noqa: E402

U = B.U


def heated_material(name, cold_rim, hot_core, strength):
    """Iron with heat in it, still iron: its shape and its sheen keep, and a glow comes up
    through it, hottest along the bar's crown (where it faces the eye) and darker round its
    sides, mottled where scale has crusted on it; from `cold_rim` to `hot_core`."""
    m = C.iron_chain_material()
    m.name = name
    nt = m.node_tree
    n, k = nt.nodes, nt.links
    bsdf = n["Principled BSDF"]
    lw = n.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.35
    inv = n.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    k.new(lw.outputs["Facing"], inv.inputs[1])
    pw = n.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 1.6
    k.new(inv.outputs[0], pw.inputs[0])
    tco = n.new("ShaderNodeTexCoord")
    scale = n.new("ShaderNodeTexNoise")
    scale.inputs["Scale"].default_value = 14.0
    scale.inputs["Detail"].default_value = 4.0
    k.new(tco.outputs["Object"], scale.inputs["Vector"])
    crust = n.new("ShaderNodeMapRange")
    k.new(scale.outputs["Fac"], crust.inputs["Value"])
    crust.inputs["From Min"].default_value = 0.35
    crust.inputs["From Max"].default_value = 0.65
    crust.inputs["To Min"].default_value = 0.55
    crust.inputs["To Max"].default_value = 1.0
    heat = n.new("ShaderNodeMath")
    heat.operation = "MULTIPLY"
    k.new(pw.outputs[0], heat.inputs[0])
    k.new(crust.outputs[0], heat.inputs[1])
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = B.hexc(cold_rim)
    ramp.color_ramp.elements[1].color = B.hexc(hot_core)
    k.new(heat.outputs[0], ramp.inputs["Fac"])
    k.new(ramp.outputs["Color"], bsdf.inputs["Emission Color"])
    st = n.new("ShaderNodeMath")
    st.operation = "MULTIPLY"
    st.inputs[1].default_value = strength
    k.new(heat.outputs[0], st.inputs[0])
    k.new(st.outputs[0], bsdf.inputs["Emission Strength"])
    return m


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    spec = json.load(open(argv[0], encoding="utf-8"))
    out = argv[1]
    os.makedirs(out, exist_ok=True)
    C.SPEC.update(spec.get("material", {}))
    sc = B.reset()
    if spec.get("cpu", True):
        sc.cycles.device = "CPU"
    sc.cycles.samples = spec.get("samples", 64)
    B.world()
    B.suns()
    ss = spec.get("ss", 3)
    Wf, Hf = spec["cell"]
    W, H = Wf * ss, Hf * ss
    B.camera(W, H)
    L = spec["link"]
    length, width, wire = L["length"] * ss, L["width"] * ss, L["wire"] * ss
    pitch = spec["pitch"] * ss
    states = {
        "": C.iron_chain_material(),
        "warm_": heated_material("chain_warm", "#100200", "#7a1404", 0.75),
        "hot_": heated_material("chain_hot", "#2a0602", "#ff7a28", 1.5),
    }
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    plane = bpy.context.active_object
    plane.scale = (W * U * 1.5, H * U * 1.5, 1)
    plane.is_shadow_catcher = True
    rnd = random.Random(spec.get("seed", 5))
    jobs = [] if spec.get("only_eye") else \
        [("face", k) for k in range(spec["variants"])] + [("edge", k) for k in range(spec["variants"])] + [("open", 0)]
    for kind, k in jobs:
        standing = kind == "edge"
        sl = 1 + rnd.uniform(-0.05, 0.05)
        sw = 1 + rnd.uniform(-0.07, 0.07)
        gap = spec.get("gap", 14) * ss * U if kind == "open" else 0.0
        ob, tips = C.link_mesh(f"{kind}{k}", length * sl * U, width * sw * U, wire * (1 + rnd.uniform(-0.06, 0.06)) * U, gap=gap)
        tilt = rnd.uniform(-0.14, 0.14) if kind != "open" else 0.0
        ob.rotation_euler = ((math.pi / 2 if standing else 0.0) + tilt, rnd.uniform(-0.05, 0.05), rnd.uniform(-0.05, 0.05))
        ob.location = (0, 0, ((width / 2) if standing else wire) * U)
        # Its neighbours, there only to find where they rub it, then gone before the picture.
        nbrs = []
        for sgn in (-1, 1):
            nb, _ = C.link_mesh(f"nb{kind}{k}{sgn}", length * U, width * U, wire * U)
            nb.rotation_euler = ((0.0 if standing else math.pi / 2), 0, 0)
            nb.location = (sgn * pitch * U, 0, ((wire) if standing else width / 2) * U)
            nbrs.append(nb)
        bpy.context.view_layer.update()
        C.mark_wear([nbrs[0], ob, nbrs[1]], wire * U)
        for nb in nbrs:
            bpy.data.objects.remove(nb, do_unlink=True)
        for prefix, mat in (states.items() if kind != "open" else (("hot_", states["hot_"]),)):
            ob.data.materials.clear()
            ob.data.materials.append(mat)
            name = f"{prefix}{kind}_{k}.png" if kind != "open" else "open.png"
            sc.render.filepath = os.path.join(out, name)
            bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(ob, do_unlink=True)
    if spec.get("eye"):
        eye(spec, sc, out, ss, length, width, wire, states[""], plane)


def eye(spec, sc, out, ss, length, width, wire, iron, plane):
    """The chain's anchor (the owner: the links must truly go through it): an eye-bolt driven
    into the band, its ring standing across the chain and leaning back, so a link passing
    through it goes under its near arc and over its far one. Rendered in two halves split at
    the chain's height: eye_back.png (the far arc, the shank, the washer, and every shadow) to
    lie under the links, eye_front.png (the near arc alone) over them."""
    import bmesh
    e = spec["eye"]
    R, bar = e["r"] * ss, e["bar"] * ss
    phi = math.radians(e.get("lean", 35))
    bpy.ops.mesh.primitive_torus_add(major_radius=R * U, minor_radius=bar * U, major_segments=128, minor_segments=24)
    ring = bpy.context.active_object
    ring.rotation_euler = (0, math.pi / 2 - phi, 0)
    zc = R * math.cos(phi) + bar * 0.4
    ring.location = (0, 0, zc * U)
    bpy.context.view_layer.update()
    bpy.ops.object.transform_apply(location=True, rotation=True)
    ring.data.materials.append(iron)
    # Where the chain has run through it: rubbed bright inside.
    lk, _ = C.link_mesh("pass", length * U, width * U, wire * U)
    lk.rotation_euler = (math.pi / 2, 0, 0)
    lk.location = (0, 0, zc * U)
    bpy.context.view_layer.update()
    C.mark_wear([lk, ring], wire * U * 1.6)
    bpy.data.objects.remove(lk, do_unlink=True)
    # Its shank down into the band from the ring's foot, and a washer under it.
    low = min(ring.data.vertices, key=lambda v: v.co.z).co
    bpy.ops.mesh.primitive_cylinder_add(radius=bar * 0.9 * U, depth=max(low.z, bar * U) * 1.2, location=(low.x, low.y, low.z / 2))
    shank = bpy.context.active_object
    shank.data.materials.append(iron)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=bar * 2.6 * U, depth=bar * 0.6 * U, location=(low.x, low.y, bar * 0.3 * U))
    washer = bpy.context.active_object
    bev = washer.modifiers.new("b", "BEVEL")
    bev.width = bar * 0.25 * U
    bev.segments = 3
    washer.data.materials.append(iron)
    # Split the ring at the chain's height: the near arc (above) and the far arc (below).
    front = ring.copy()
    front.data = ring.data.copy()
    bpy.context.scene.collection.objects.link(front)
    for ob, keep_above in ((front, True), (ring, False)):
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        gone = [f for f in bm.faces if (f.calc_center_median().z > zc * U) != keep_above]
        bmesh.ops.delete(bm, geom=gone, context="FACES")
        bm.to_mesh(ob.data)
        bm.free()
    # The back: far arc, shank and washer seen, the near arc only casting its shadow.
    front.visible_camera = False
    sc.render.filepath = os.path.join(out, "eye_back.png")
    bpy.ops.render.render(write_still=True)
    # The front: the near arc alone, nothing under it, no shadow of its own on the page.
    front.visible_camera = True
    for ob in (ring, shank, washer):
        ob.hide_render = True
    plane.hide_render = True
    sc.render.filepath = os.path.join(out, "eye_front.png")
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
