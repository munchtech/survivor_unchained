import bpy, sys, math, mathutils
a = sys.argv[sys.argv.index("--") + 1:]
out = a[-1]
plys = a[:-1]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE_NEXT"
sc.render.resolution_x = sc.render.resolution_y = 700
sc.view_settings.view_transform = "Standard"
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[1].default_value = 0.25


def light(rot, e):
    L = bpy.data.lights.new("l", "SUN"); L.energy = e; L.angle = 0.05
    o = bpy.data.objects.new("l", L); sc.collection.objects.link(o)
    o.rotation_euler = [math.radians(r) for r in rot]


light((70, 0, 50), 4.0)
light((60, 0, -130), 0.6)
m = bpy.data.materials.new("c"); m.use_nodes = True
nt = m.node_tree; b = nt.nodes["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.5
at = nt.nodes.new("ShaderNodeVertexColor"); nt.links.new(at.outputs[0], b.inputs["Base Color"])
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 85
tgt = mathutils.Vector((0, 0.0, 1.56))
VIEWS = {"front": (0, -1, 0.05), "q3l": (0.75, -0.65, -0.15), "q3r": (-0.75, -0.65, -0.15), "low": (0.3, -0.6, -0.75)}
for pi, pf in enumerate(plys):
    for o in list(sc.objects):
        if o.type == "MESH":
            bpy.data.objects.remove(o)
    bpy.ops.wm.ply_import(filepath=pf)
    o = bpy.context.selected_objects[0]
    o.data.materials.append(m)
    bpy.ops.object.shade_smooth()
    for vn, d in VIEWS.items():
        d = mathutils.Vector(d).normalized()
        cam.location = tgt + d * 0.55
        cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = "%s_%d_%s.png" % (out, pi, vn)
        bpy.ops.render.render(write_still=True)
