"""Her throat under a light from her left side (as the portraits' key), white clay, EEVEE, her own normals: and the
same with her head and body told apart by colour. blender -b X.blend --python side_light.py -- out_prefix"""
import bpy, sys, math
from mathutils import Vector, Euler

out = sys.argv[sys.argv.index("--") + 1:][0]
sc = bpy.context.scene
for o in sc.objects:
    if o.type == "LIGHT":
        o.hide_render = True
keep = {"HeroineHead", "Heroine"}
for o in sc.objects:
    if o.type == "MESH" and o.name not in keep:
        o.hide_render = True
for o in sc.objects:
    if o.type == "MESH" and o.name in keep:
        for m in o.modifiers:
            if m.type != "ARMATURE":
                m.show_render = False


def mat(name, rgb):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*rgb, 1)
    m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.7
    return m


sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE"
sc.view_settings.view_transform = "Standard"
sc.render.resolution_x, sc.render.resolution_y = 900, 900
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[1].default_value = 0.05
ld = bpy.data.lights.new("key", "SUN"); ld.energy = 4.0
lo = bpy.data.objects.new("key", ld); sc.collection.objects.link(lo)
lo.rotation_euler = (Vector((0, 0, 0)) - Vector((1.5, -1.0, 1.2))).to_track_quat("-Z", "Y").to_euler()
cam_d = bpy.data.cameras.new("c"); cam_d.type = "ORTHO"; cam_d.ortho_scale = 0.32
cam = bpy.data.objects.new("c", cam_d); sc.collection.objects.link(cam); sc.camera = cam
tgt = Vector((0, -0.02, 1.53))
cam.location = tgt + Vector((-0.25, -1.0, 0.05))
cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
for tag, cols in (("clay", {"HeroineHead": (0.8, 0.8, 0.8), "Heroine": (0.8, 0.8, 0.8)}),
                  ("which", {"HeroineHead": (0.85, 0.3, 0.3), "Heroine": (0.3, 0.8, 0.35)})):
    for n, c in cols.items():
        o = bpy.data.objects[n]
        m = mat(tag + n, c)
        o.data.materials.clear() if False else None
        for i in range(len(o.material_slots)):
            o.material_slots[i].material = m
    sc.render.filepath = out + "_" + tag + ".png"
    bpy.ops.render.render(write_still=True)
print("SIDE done")
