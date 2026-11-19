"""A neutral lookdev render of a built armor piece on her (the exported files, as the game loads them).

    blender -b --factory-startup --python tools/armor/lookdev.py -- <id> <out prefix>

Imports godot/art/people/heroine.glb and godot/art/armor/<id>.gltf (both in her bind pose, so they overlay
without posing), neutral grey world plus a soft key and fill, Eevee, 1280x720: <prefix>_front.png and
<prefix>_34.png, <prefix>_side.png, <prefix>_back.png (<id> may be a .glb path: a free mesh before its install). Nothing else of hers (outfits, hair) is loaded.
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
bpy.ops.import_scene.gltf(filepath=PID if PID.endswith(".glb") else os.path.join(ROOT, "godot", "art", "armor", f"{PID}.gltf"))
# (optional: LOOKDEV_WITH="kit_bodice,<glb path>,.." worn with it, e.g. the set's other pieces)
for _w in [w for w in os.environ.get("LOOKDEV_WITH", "").split(",") if w]:
    bpy.ops.import_scene.gltf(filepath=_w if _w.endswith(".glb") else os.path.join(ROOT, "godot", "art", "armor", f"{_w}.gltf"))
# (the full piece only: its gameplay and shadow LODs (piece_lod.py) share the file)
for o in [o for o in bpy.data.objects if o.type == "MESH" and (".lod1." in o.name or o.name.endswith(".shadow") or "_lod1_" in o.name)]:
    bpy.data.objects.remove(o)
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
# (a free mesh's materials carry names only (the game's shaders draw them): a flat stand-in colour by name where the
# material has no texture, so the plate, trim and leather read apart)
TINT = {"steel": ((0.075, 0.068, 0.072, 1), 0.75, 0.38), "gold": ((0.95, 0.58, 0.16, 1), 1.0, 0.3),
        "darkleather": ((0.085, 0.045, 0.028, 1), 0.0, 0.6), "brownleather": ((0.16, 0.075, 0.035, 1), 0.0, 0.55)}
for m in bpy.data.materials:
    key = m.name.split(".")[0]
    print("MAT", m.name, m.use_nodes, [n.type for n in m.node_tree.nodes] if m.use_nodes else None)
    if key in TINT and m.use_nodes and not [n for n in m.node_tree.nodes if n.type == "TEX_IMAGE"]:
        bs = [n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"]
        if bs:
            for lk in list(bs[0].inputs["Base Color"].links):
                m.node_tree.links.remove(lk)
            bs[0].inputs["Base Color"].default_value, bs[0].inputs["Metallic"].default_value,                 bs[0].inputs["Roughness"].default_value = TINT[key]
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
# (optional: LOOKDEV_FRAME="<distance>,<target height>" frames more of her, e.g. "2.1,1.22" head to thigh)
_fr = [float(v) for v in os.environ.get("LOOKDEV_FRAME", "1.25,1.33").split(",")]
tgt = Vector((0.0, 0.0, _fr[1]))
for tag, ang in (("front", 0.0), ("34", 35.0), ("side", 90.0), ("back", 180.0)):
    a = math.radians(ang)
    cam.location = tgt + Vector((_fr[0] * math.sin(a), -_fr[0] * math.cos(a), 0.05))
    cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = f"{PREFIX}_{tag}.png"
    bpy.ops.render.render(write_still=True)
    print("LOOKDEV", sc.render.filepath)
