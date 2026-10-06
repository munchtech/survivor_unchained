"""Her head textured with an image (unlit, as it is in UV), seen from the front at 1536: what the paint holds, without
Godot. Usage: blender -b X.blend --python uv_front.py -- image.png out.png"""
import bpy, sys
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
img_path, out = argv[0], argv[1]
sc = bpy.context.scene
head = bpy.data.objects["HeroineHead"]
for o in sc.objects:
    if o.type == "MESH" and o.name not in ("HeroineHead",):
        o.hide_render = True
mat = bpy.data.materials.new("uvview")
mat.use_nodes = True
nt = mat.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = bpy.data.images.load(img_path)
tex.interpolation = "Cubic"
em = nt.nodes.new("ShaderNodeEmission")
outn = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(tex.outputs["Color"], em.inputs["Color"])
nt.links.new(em.outputs["Emission"], outn.inputs["Surface"])
head.data.materials.clear()
head.data.materials.append(mat)
sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE"
sc.view_settings.view_transform = "Standard"
sc.render.resolution_x = sc.render.resolution_y = 1536
sc.render.film_transparent = False
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.6, 0.55, 0.5, 1)
teeth = bpy.data.objects["HeroineTeeth"]
tb = [teeth.matrix_world @ Vector(c) for c in teeth.bound_box]
m = Vector((0.0, min(v.y for v in tb) - 0.012, max(v.z for v in tb) - 0.004))
c = m + Vector((0, 0, 0.055))
cam_d = bpy.data.cameras.new("cv"); cam_d.type = "ORTHO"; cam_d.ortho_scale = 0.26
cam = bpy.data.objects.new("cv", cam_d); sc.collection.objects.link(cam); sc.camera = cam
cam.location = c + Vector((0, -0.6, 0))
cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
