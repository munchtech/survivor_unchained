"""The emblem: seven forged chain links in a ring, the topmost pried open with ember
light at the break (hud/ring_art.png, round the art in hand). Modelled and rendered in
Blender under the house light (the world and suns of blender_frames.py).

    blender -b -P tools/uiforge/blender_chain.py -- out.png SIZE [open_index]
"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import blender_frames as B  # noqa: E402


def link_mesh(name, length, width, wire, gap=0.0, gap_at=0.0):
    """A stadium-shaped link of round bar (a curve with a circular bevel); `gap` opens it
    at its +x end (radians of the end's half circle)."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = wire
    cu.bevel_resolution = 6
    cu.use_fill_caps = True
    r = width / 2
    straight = max(length - width, 0) / 2
    pts = []
    n = 72
    for i in range(n):
        t = i / n * 2 * math.pi
        x = (straight if math.cos(t) >= 0 else -straight) + r * math.cos(t)
        y = r * math.sin(t)
        if gap and abs(((t - gap_at + math.pi) % (2 * math.pi)) - math.pi) < gap / 2:
            continue
        pts.append((x, y, t))
    # Rotate the list so the gap (if any) falls at the ends of the spline.
    if gap:
        k = next(i for i in range(1, len(pts)) if pts[i][2] - pts[i - 1][2] > 2 * math.pi / n * 1.5)
        pts = pts[k:] + pts[:k]
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, (x, y, _) in enumerate(pts):
        sp.points[i].co = (x, y, 0, 1)
    sp.use_cyclic_u = not gap
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    out, size = argv[0], int(argv[1])
    open_i = int(argv[2]) if len(argv) > 2 else 0
    sc = B.reset()
    sc.cycles.samples = 128
    B.world()
    B.suns()
    W = H = size * 2
    B.camera(W, H)
    U = B.U
    R = W * 0.425 * U         # the ring's radius (link centres): the middle stays open
    L = W * 0.42 * U          # link length
    Wd = W * 0.105 * U        # link width
    wire = W * 0.021 * U      # bar radius
    iron = B.iron_material("iron", W, H, [W // 4] * 4, dict(color="#1c1a21", worn="#9894a0", rough=0.42, hammer=1.4,
                                                         dent_scale=0.12, grain_scale=0.9, wear=0.9))
    ember = B.emission_material("ember", "#ff7a1a", 14.0)
    n = 7
    for i in range(n):
        a = math.pi / 2 - i * 2 * math.pi / n
        gap = 1.0 if i == open_i else 0.0
        # The open link is pried apart on its outer side, where the eye sees the break.
        ob = link_mesh(f"link{i}", L, Wd, wire, gap=gap, gap_at=math.pi / 2)
        ob.data.materials.append(iron)
        ob.location = (math.cos(a) * R, math.sin(a) * R, 0)
        # Each link lies along the ring; alternate links stand on edge, as a chain does.
        ob.rotation_euler = (math.radians(0 if i % 2 == 0 else 48), 0, a + math.pi / 2)
        if gap:
            # The ember at the break: two small hot spheres at the pried ends, light between.
            ob.rotation_euler = (0, 0, a + math.pi / 2)
            straight = max(L - Wd, 0) / 2
            for s_ in (-1, 1):
                local = Vector((s_ * Wd / 2 * math.sin(gap / 2) * 1.6, Wd / 2, 0))
                bpy.ops.mesh.primitive_uv_sphere_add(radius=wire * 0.9, location=(0, 0, 0))
                e = bpy.context.active_object
                e.data.materials.append(ember)
                e.parent = ob
                e.location = local
            # A glow card behind the break.
            bpy.ops.mesh.primitive_plane_add(size=Wd * 1.6)
            g = bpy.context.active_object
            gm = bpy.data.materials.new("glow")
            gm.use_nodes = True
            nt = gm.node_tree
            for nd in list(nt.nodes):
                nt.nodes.remove(nd)
            outn = nt.nodes.new("ShaderNodeOutputMaterial")
            em = nt.nodes.new("ShaderNodeEmission")
            em.inputs["Color"].default_value = B.hexc("#ff6a1a")
            tc = nt.nodes.new("ShaderNodeTexCoord")
            grad = nt.nodes.new("ShaderNodeTexGradient")
            grad.gradient_type = "SPHERICAL"
            mp = nt.nodes.new("ShaderNodeMapping")
            mp.inputs["Location"].default_value = (0, 0, 0)
            nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
            mp.inputs["Scale"].default_value = (1.4, 1.4, 1.4)
            nt.links.new(mp.outputs["Vector"], grad.inputs["Vector"])
            pw = nt.nodes.new("ShaderNodeMath")
            pw.operation = "POWER"
            pw.inputs[1].default_value = 2.5
            nt.links.new(grad.outputs["Fac"], pw.inputs[0])
            mul = nt.nodes.new("ShaderNodeMath")
            mul.operation = "MULTIPLY"
            mul.inputs[1].default_value = 6.0
            nt.links.new(pw.outputs[0], mul.inputs[0])
            nt.links.new(mul.outputs[0], em.inputs["Strength"])
            tr = nt.nodes.new("ShaderNodeBsdfTransparent")
            mix = nt.nodes.new("ShaderNodeAddShader")
            nt.links.new(em.outputs[0], mix.inputs[0])
            nt.links.new(tr.outputs[0], mix.inputs[1])
            nt.links.new(mix.outputs[0], outn.inputs[0])
            gm.blend_method = "BLEND" if hasattr(gm, "blend_method") else None
            g.data.materials.append(gm)
            bpy.context.view_layer.update()
            tip = ob.matrix_world @ Vector((0, Wd / 2, 0))
            g.location = (tip.x, tip.y, -wire * 1.5)
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)


main()
