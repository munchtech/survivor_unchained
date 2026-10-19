"""A neutral lookdev render of a built armor piece on her (the exported files, as the game loads them).

    blender -b --factory-startup --python tools/armor/lookdev.py -- <id> <out prefix>

Imports godot/art/people/heroine.glb and godot/art/armor/<id>.gltf (both in her bind pose, so they overlay
without posing), neutral grey world plus a soft key and fill, Eevee, 1280x720: <prefix>_front.png and
<prefix>_34.png. Nothing else of hers (outfits, hair) is loaded.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
PID, PREFIX = args[0], os.path.abspath(args[1])
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, "godot", "art", "people", "heroine.glb"))
bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, "godot", "art", "armor", f"{PID}.gltf"))
# (the vertex colours are the game shaders' data (her tuck, the outfit's baked edge and cavity), never colour:
# every colour-attribute node the importer wired in is replaced by white)
for m in bpy.data.materials:
    if not m.use_nodes:
        continue
    nt = m.node_tree
    for nd in [n for n in nt.nodes if n.type in ("VERTEX_COLOR", "ATTRIBUTE")]:
        rgb = nt.nodes.new("ShaderNodeRGB")
        rgb.outputs[0].default_value = (1, 1, 1, 1)
        for out in nd.outputs:
            for lk in list(out.links):
                if out.name in ("Color", "Fac") or out.type == "RGBA":
                    nt.links.new(rgb.outputs[0], lk.to_socket)
                else:
                    nt.links.remove(lk)
        nt.nodes.remove(nd)
sc = bpy.context.scene
for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try:
        sc.render.engine = eng
        break
    except TypeError:
        pass
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.render.film_transparent = False
sc.view_settings.view_transform = "AgX" if "AgX" in [i.identifier for i in sc.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
w = bpy.data.worlds.new("grey")
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.18, 0.18, 0.18, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.6
sc.world = w


def light(name, kind, loc, energy, size):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    if kind == "AREA":
        ld.size = size
    o = bpy.data.objects.new(name, ld)
    sc.collection.objects.link(o)
    o.location = loc
    d = Vector((0, 0, 1.35)) - Vector(loc)
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


light("key", "AREA", (-1.2, -2.0, 2.0), 260, 1.5)
light("fill", "AREA", (1.6, -1.6, 1.4), 90, 2.0)
light("rim", "AREA", (0.6, 1.8, 2.0), 120, 1.0)
cam_d = bpy.data.cameras.new("cam")
cam_d.lens = 70
cam = bpy.data.objects.new("cam", cam_d)
sc.collection.objects.link(cam)
sc.camera = cam
tgt = Vector((0.0, 0.0, 1.33))
for tag, ang in (("front", 0.0), ("34", 35.0), ("side", 90.0)):
    a = math.radians(ang)
    cam.location = tgt + Vector((1.25 * math.sin(a), -1.25 * math.cos(a), 0.05))
    cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = f"{PREFIX}_{tag}.png"
    bpy.ops.render.render(write_still=True)
    print("LOOKDEV", sc.render.filepath)
