"""Sheets of a rigged beast's clips: each clip's frames side by side, seen
from its left at its own height and from the game's camera (64 degrees
down), so a clip can be judged at a glance.

    blender -b --python tools/creatures/clip_sheet.py -- RIGGED.blend OUT_DIR [--clips trot,gallop] [--frames 8] [--size 360]
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:]
src, out = argv[0], argv[1]
os.makedirs(out, exist_ok=True)
want = argv[argv.index("--clips") + 1].split(",") if "--clips" in argv else None
count = int(argv[argv.index("--frames") + 1]) if "--frames" in argv else 8
size = int(argv[argv.index("--size") + 1]) if "--size" in argv else 360

bpy.ops.wm.open_mainfile(filepath=src)
scene = bpy.context.scene
arm = next(o for o in scene.objects if o.type == "ARMATURE")
for o in scene.objects:
    if o.type == "MESH" and o.name in ("Sculpt", "Form"):
        o.hide_render = True
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.show_cavity = True
scene.render.resolution_x = scene.render.resolution_y = size
scene.display.shading.background_type = "VIEWPORT"
scene.display.shading.background_color = (0.75, 0.76, 0.72)
for m in bpy.data.materials:
    m.diffuse_color = {"Ivory": (0.9, 0.85, 0.7, 1), "Bristle": (0.08, 0.07, 0.06, 1)}.get(m.name, (0.42, 0.36, 0.32, 1))

cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
scene.collection.objects.link(cam)
scene.camera = cam
cam.data.type = "ORTHO"
cam.data.ortho_scale = 2.4


def look(frm, at, up=Vector((0, 0, 1))):
    z = (frm - at).normalized()
    x = up.cross(z).normalized()
    y = z.cross(x)
    cam.matrix_world = Matrix((x, y, z)).transposed().to_4x4()
    cam.location = frm


from PIL import Image  # noqa: E402

tracks = {t.name: t for t in arm.animation_data.nla_tracks}
for t in tracks.values():
    t.mute = True
names = [n for n in tracks if want is None or n in want]
for name in names:
    track = tracks[name]
    track.mute = False
    strip = track.strips[0]
    end = int(strip.action_frame_end)
    frames = [round(i * end / max(1, count - 1)) for i in range(count)]
    row = []
    for view in ("side", "game"):
        for f in frames:
            scene.frame_set(f)
            if view == "side":
                look(Vector((4, 0, 0.5)), Vector((0, 0, 0.5)))
            else:
                a = math.radians(64)
                look(Vector((2.2, 2.2 * 0.3, 0)) * math.cos(a) + Vector((0, 0, 4 * math.sin(a))) + Vector((0, 0, 0.4)), Vector((0, 0, 0.4)))
            path = os.path.join(out, f"_{name}_{view}_{f}.png")
            scene.render.filepath = path
            bpy.ops.render.render(write_still=True)
            row.append(path)
    track.mute = True
    sheet = Image.new("RGB", (size * count, size * 2))
    for i, p in enumerate(row):
        sheet.paste(Image.open(p), ((i % count) * size, (i // count) * size))
        os.remove(p)
    sheet.save(os.path.join(out, f"{name}.png"))
    print("SHEET", name, frames)
