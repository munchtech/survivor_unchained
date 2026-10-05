"""Live coals and the iron dish they lie in (Self's attribute points: a coal for each point to
spend, moved to an attribute as it is spent), modelled and rendered in Blender under the house
light, seen from above and a little in front, each with its shadow caught on the page.

    blender -b -P tools/uiforge/blender_coals.py -- spec.json OUTDIR

    {"ss": 3, "samples": 96, "tilt": 52, "coal": {"cell": [36, 28], "size": 13, "variants": 4},
     "dish": {"cell": [168, 68], "rx": 78, "ry": 78, "depth": 9, "wall": 2.6}, "material": {...}}

Writes OUTDIR/coal_K.png (cells of coal.cell file px), dish.png and dish_rim.png (the near rim
alone, to lay over the coals' feet), all from the same camera.
"""
import json
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Vector, noise

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import blender_frames as B  # noqa: E402
import blender_chainline as C  # noqa: E402

U = B.U


def camera(W, H, tilt):
    """An orthographic camera looking down at `tilt` degrees from straight above, from the
    front (the page's foot), covering W x H render px at the look-at point."""
    cam_d = bpy.data.cameras.new("cam")
    cam_d.type = "ORTHO"
    cam_d.ortho_scale = max(W, H) * U
    cam = bpy.data.objects.new("cam", cam_d)
    bpy.context.scene.collection.objects.link(cam)
    a = math.radians(tilt)
    cam.location = (0, -10 * math.sin(a), 10 * math.cos(a))
    cam.rotation_euler = (a, 0, 0)
    bpy.context.scene.camera = cam
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = W, H
    sc.render.resolution_percentage = 100


def coal_material(seed):
    """A coal: a dull grey-black crust, the fire showing through its cracks (the edges of a
    cell noise), brightest where the cracks are widest; a dull red under the crust's thin skin."""
    m = bpy.data.materials.new(f"coal{seed}")
    m.use_nodes = True
    nt = m.node_tree
    n, k = nt.nodes, nt.links
    bsdf = n["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = B.hexc("#191515")
    bsdf.inputs["Roughness"].default_value = 0.92
    tco = n.new("ShaderNodeTexCoord")
    mp = n.new("ShaderNodeMapping")
    mp.inputs["Location"].default_value = (seed * 3.1, seed * 1.7, seed * 2.3)
    k.new(tco.outputs["Object"], mp.inputs["Vector"])
    vor = n.new("ShaderNodeTexVoronoi")
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = 2.2 / (13 * 3 * U)
    k.new(mp.outputs["Vector"], vor.inputs["Vector"])
    crack = n.new("ShaderNodeMapRange")
    k.new(vor.outputs["Distance"], crack.inputs["Value"])
    crack.inputs["From Min"].default_value = 0.0
    crack.inputs["From Max"].default_value = 0.035
    crack.inputs["To Min"].default_value = 1.0
    crack.inputs["To Max"].default_value = 0.0
    pw = n.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 1.8
    k.new(crack.outputs[0], pw.inputs[0])
    nz = n.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 1.4 / (13 * 3 * U)
    k.new(mp.outputs["Vector"], nz.inputs["Vector"])
    live = n.new("ShaderNodeMapRange")
    k.new(nz.outputs["Fac"], live.inputs["Value"])
    live.inputs["From Min"].default_value = 0.42
    live.inputs["From Max"].default_value = 0.62
    live.inputs["To Min"].default_value = 0.0
    live.inputs["To Max"].default_value = 1.0
    heat = n.new("ShaderNodeMath")
    heat.operation = "MULTIPLY"
    k.new(pw.outputs[0], heat.inputs[0])
    k.new(live.outputs[0], heat.inputs[1])
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = B.hexc("#3a0601")
    ramp.color_ramp.elements[1].color = B.hexc("#ff8a34")
    k.new(heat.outputs[0], ramp.inputs["Fac"])
    k.new(ramp.outputs["Color"], bsdf.inputs["Emission Color"])
    st = n.new("ShaderNodeMath")
    st.operation = "MULTIPLY"
    st.inputs[1].default_value = 5.0
    k.new(heat.outputs[0], st.inputs[0])
    k.new(st.outputs[0], bsdf.inputs["Emission Strength"])
    # The crust: black, greyed with ash in patches.
    ashn = n.new("ShaderNodeTexNoise")
    ashn.inputs["Scale"].default_value = 2.6 / (13 * 3 * U)
    k.new(mp.outputs["Vector"], ashn.inputs["Vector"])
    ashm = n.new("ShaderNodeMapRange")
    k.new(ashn.outputs["Fac"], ashm.inputs["Value"])
    ashm.inputs["From Min"].default_value = 0.5
    ashm.inputs["From Max"].default_value = 0.7
    mix = n.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    k.new(ashm.outputs[0], mix.inputs[0])
    mix.inputs[6].default_value = B.hexc("#141111")
    mix.inputs[7].default_value = B.hexc("#4a4441")
    k.new(mix.outputs[2], bsdf.inputs["Base Color"])
    return m


def coal(size, seed):
    """A lump of coal about `size` render px across: a subdivided ball pushed about by noise,
    flattened a little where it lies."""
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=size / 2 * U, location=(0, 0, 0))
    ob = bpy.context.active_object
    rnd = random.Random(seed)
    sx, sy, sz = rnd.uniform(0.9, 1.15), rnd.uniform(0.75, 0.95), rnd.uniform(0.6, 0.75)
    off = Vector((seed * 7.1, seed * 3.3, seed * 5.9))
    for v in ob.data.vertices:
        p = v.co.normalized()
        d = 1 + 0.22 * noise.noise(p * 1.6 + off) + 0.08 * noise.noise(p * 4.5 + off)
        # Faceted, as broken coal is: the push rounded to a few levels.
        d = round(d * 7) / 7 * 0.6 + d * 0.4
        v.co = Vector((p.x * sx, p.y * sy, p.z * sz)) * d * size / 2 * U
    ob.location = (0, 0, size / 2 * sz * 0.8 * U)
    ob.rotation_euler = (0, 0, rnd.uniform(0, math.pi))
    bpy.ops.object.shade_smooth()
    return ob


def dish(rx, ry, depth, wall, iron, ash):
    """A shallow forged dish: a round bowl drawn out under the hammer, its lip turned out, a
    floor of ash in it. rx, ry, depth, wall in render px."""
    bm = bmesh.new()
    prof = []
    for i in range(25):                                   # the bowl's section, centre to lip
        t = i / 24
        r = t
        z = depth * (t ** 2.2)
        prof.append((r, z))
    prof.append((1.06, depth + wall * 0.4))              # the lip turned out
    segs = 96
    rings = []
    for (r, z) in prof:
        ring = []
        for j in range(segs):
            a = 2 * math.pi * j / segs
            ham = 1 + 0.012 * noise.noise(Vector((math.cos(a) * 3, math.sin(a) * 3, r * 4)))
            ring.append(bm.verts.new((math.cos(a) * r * rx * ham * U, math.sin(a) * r * ry * ham * U, z * U)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for j in range(segs):
            bm.faces.new((rings[i][j], rings[i][(j + 1) % segs], rings[i + 1][(j + 1) % segs], rings[i + 1][j]))
    bm.faces.new(rings[0][::-1])
    me = bpy.data.meshes.new("dish")
    bm.to_mesh(me)
    ob = bpy.data.objects.new("dish", me)
    bpy.context.scene.collection.objects.link(ob)
    sol = ob.modifiers.new("solid", "SOLIDIFY")
    sol.thickness = wall * U
    sol.offset = -1
    ob.data.materials.append(iron)
    for p in ob.data.polygons:
        p.use_smooth = True
    # The ash in its floor.
    bpy.ops.mesh.primitive_circle_add(vertices=64, radius=1, fill_type="NGON", location=(0, 0, depth * 0.22 * U))
    a = bpy.context.active_object
    a.scale = (rx * 0.62 * U, ry * 0.62 * U, 1)
    a.data.materials.append(ash)
    return ob, a


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    spec = json.load(open(argv[0], encoding="utf-8"))
    out = argv[1]
    os.makedirs(out, exist_ok=True)
    C.SPEC.update(spec.get("material", {}))
    sc = B.reset()
    if spec.get("cpu", True):
        sc.cycles.device = "CPU"
    sc.cycles.samples = spec.get("samples", 96)
    B.world()
    B.suns()
    ss = spec.get("ss", 3)
    tilt = spec.get("tilt", 52)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    plane = bpy.context.active_object
    plane.scale = (6, 6, 1)
    plane.is_shadow_catcher = True
    # Coals, one at a time in their own cell.
    cw, ch = spec["coal"]["cell"]
    camera(cw * ss, ch * ss, tilt)
    for kk in range(spec["coal"]["variants"]):
        ob = coal(spec["coal"]["size"] * ss, 11 + kk * 17)
        ob.data.materials.append(coal_material(kk))
        sc.render.filepath = os.path.join(out, f"coal_{kk}.png")
        bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.objects.remove(bpy.data.objects["cam"], do_unlink=True)
    # The dish, whole and then its near rim alone.
    d = spec["dish"]
    dw, dh = d["cell"]
    camera(dw * ss, dh * ss, tilt)
    iron = C.iron_chain_material()
    ash = bpy.data.materials.new("ash")
    ash.use_nodes = True
    ash.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = B.hexc("#2a2422")
    ash.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1.0
    ob, a = dish(d["rx"] * ss, d["ry"] * ss, d["depth"] * ss, d["wall"] * ss, iron, ash)
    sc.render.filepath = os.path.join(out, "dish.png")
    bpy.ops.render.render(write_still=True)
    # The near rim: what lies in front of the dish's middle and above its floor, so it can be
    # laid over the coals' feet. Everything else is held out (it still shades, but is not drawn).
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier="solid")
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    floor = d["depth"] * ss * 0.35 * U
    gone = [f for f in bm.faces if f.calc_center_median().y > 0 or f.calc_center_median().z < floor]
    bmesh.ops.delete(bm, geom=gone, context="FACES")
    bm.to_mesh(ob.data)
    a.hide_render = True
    sc.render.filepath = os.path.join(out, "dish_rim.png")
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
