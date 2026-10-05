"""Single chain links, each its own sprite, for a chain the code lays out and moves (the tab
chain): flat ones and ones on edge, no two alike, worn where their neighbours would rub them,
and one heated through (the chosen tab's). Rendered in Blender under the house light, each
with its shadow caught on the page.

    blender -b -P tools/uiforge/blender_links.py -- spec.json OUTDIR

    {"cell": [W, H], "ss": 3, "samples": 64, "link": {"length": 48, "width": 28, "wire": 4},
     "pitch": 32, "variants": 6, "seed": 5, "material": {...}}

Writes OUTDIR/face_K.png, edge_K.png (K < variants), hot.png (heated through) and open.png
(pried open at its lower side, ember in the break), each a cell of W x H file px with the link
at its centre, its long axis along x.
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
import blender_chainline as C  # noqa: E402  (its main() is guarded by the module check below)

U = B.U


def heated_material():
    """Iron heated through: its own colour gone to a dull red glow, orange-hot along its crown."""
    m = C.iron_chain_material()
    m.name = "chain_heated"
    nt = m.node_tree
    n, k = nt.nodes, nt.links
    bsdf = n["Principled BSDF"]
    lw = n.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.4
    inv = n.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    k.new(lw.outputs["Facing"], inv.inputs[1])
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = B.hexc("#3a0802")
    ramp.color_ramp.elements[1].color = B.hexc("#ff9a40")
    k.new(inv.outputs[0], ramp.inputs["Fac"])
    k.new(ramp.outputs["Color"], bsdf.inputs["Emission Color"])
    st = n.new("ShaderNodeMath")
    st.operation = "MULTIPLY"
    st.inputs[1].default_value = 1.7
    k.new(inv.outputs[0], st.inputs[0])
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
    iron = C.iron_chain_material()
    hot = heated_material()
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    plane = bpy.context.active_object
    plane.scale = (W * U * 1.5, H * U * 1.5, 1)
    plane.is_shadow_catcher = True
    rnd = random.Random(spec.get("seed", 5))
    jobs = [("face", k) for k in range(spec["variants"])] + [("edge", k) for k in range(spec["variants"])] + [("hot", 0), ("open", 0)]
    for kind, k in jobs:
        standing = kind == "edge"
        sl = 1 + rnd.uniform(-0.05, 0.05)
        sw = 1 + rnd.uniform(-0.07, 0.07)
        gap = spec.get("gap", 12) * ss * U if kind == "open" else 0.0
        ob, tips = C.link_mesh(f"{kind}{k}", length * sl * U, width * sw * U, wire * (1 + rnd.uniform(-0.06, 0.06)) * U, gap=gap)
        tilt = rnd.uniform(-0.14, 0.14) if kind != "open" else 0.0
        ob.rotation_euler = ((math.pi / 2 if standing else 0.0) + tilt, rnd.uniform(-0.05, 0.05), rnd.uniform(-0.05, 0.05))
        ob.location = (0, 0, ((width / 2) if standing else wire) * U)
        # The chosen tab's link: pried open and heated through, so it reads at a glance.
        ob.data.materials.append(hot if kind in ("hot", "open") else iron)
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
        sc.render.filepath = os.path.join(out, f"{kind}_{k}.png" if kind in ("face", "edge") else f"{kind}.png")
        bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(ob, do_unlink=True)


if __name__ == "__main__":
    main()
