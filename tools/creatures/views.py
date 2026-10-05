"""Orthographic pictures of what is in a .blend (or a mesh file), with a
grid in metres drawn over them, for reading off landmarks and judging shape.

    blender -b --python tools/creatures/views.py -- IN.(blend|glb) OUT_PREFIX [--size 1400] [--views side,front,top,back] [--solid]

Blender's axes: the beast faces -Y, +Z is up, +X its left. "side" looks at
its left flank (from +X), "front" at its face (from -Y), "top" down on it.
Each picture is saved with the frame it covers, and the grid's lines are
every 10 cm (darker every 50 cm), labelled in metres.
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:]
src, prefix = argv[0], argv[1]
size = int(argv[argv.index("--size") + 1]) if "--size" in argv else 1400
views = (argv[argv.index("--views") + 1] if "--views" in argv else "side,front,top").split(",")
solid = "--solid" in argv

if src.endswith(".blend"):
    bpy.ops.wm.open_mainfile(filepath=src)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)

scene = bpy.context.scene
objs = [o for o in scene.objects if o.type == "MESH" and o.visible_get()]
lo = Vector((1e9, 1e9, 1e9))
hi = -lo
deps = bpy.context.evaluated_depsgraph_get()
for o in objs:
    e = o.evaluated_get(deps)
    for c in e.bound_box:
        w = o.matrix_world @ Vector(c)
        lo = Vector(map(min, lo, w))
        hi = Vector(map(max, hi, w))
centre = (lo + hi) / 2
span = max(hi - lo) * 1.15

scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL" if solid else "TEXTURE"
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = "BOTH"
scene.render.resolution_x = scene.render.resolution_y = size
scene.render.film_transparent = False
scene.world = scene.world or bpy.data.worlds.new("w")
scene.display.shading.background_type = "VIEWPORT"
scene.display.shading.background_color = (0.82, 0.82, 0.8)

cam_data = bpy.data.cameras.new("ortho")
cam_data.type = "ORTHO"
cam_data.ortho_scale = span
cam = bpy.data.objects.new("ortho", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

DIRS = {
    "side": (Vector((1, 0, 0)), Vector((0, 0, 1))),     # from its left: its front (-Y) to the picture's left
    "front": (Vector((0, -1, 0)), Vector((0, 0, 1))),
    "top": (Vector((0, 0, 1)), Vector((0, -1, 0))),
    "back": (Vector((0, 1, 0)), Vector((0, 0, 1))),
    "right": (Vector((-1, 0, 0)), Vector((0, 0, 1))),
}

from PIL import Image, ImageDraw  # noqa: E402

for v in views:
    d, up = DIRS[v]
    cam.location = centre + d * span * 3
    cam.rotation_mode = "QUATERNION"
    # The camera's frame: it looks down its -Z (toward the beast), its Y is the picture's up.
    z = d.normalized()
    y = (up - z * up.dot(z)).normalized()
    x = y.cross(z)
    R = Matrix((x, y, z)).transposed()
    cam.rotation_quaternion = R.to_quaternion()
    bpy.context.view_layer.update()
    path = f"{prefix}_{v}.png"
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    # The grid: picture x runs along camera x, y along camera y (down in pixels).
    img = Image.open(path).convert("RGB")
    dr = ImageDraw.Draw(img)
    px = size / span

    def to_px(p):
        q = p - cam.location
        return size / 2 + q.dot(x) * px, size / 2 - q.dot(y) * px

    # Lines every 10 cm along the picture's two world axes.
    for axis, other in ((x, y), (y, x)):
        # which world axis is this?
        wa = max(range(3), key=lambda i: abs(axis[i]))
        sgn = 1 if axis[wa] > 0 else -1
        c0 = cam.location[wa]
        k0 = math.floor((c0 - span / 2) * 10)
        k1 = math.ceil((c0 + span / 2) * 10)
        for k in range(k0, k1 + 1):
            val = k / 10
            p = cam.location.copy()
            p[wa] = val
            u, w_ = to_px(p)
            strong = k % 5 == 0
            col = (90, 90, 90) if strong else (160, 160, 160)
            if axis is x:
                dr.line([(u, 0), (u, size)], fill=col, width=1)
                if strong:
                    dr.text((u + 2, 2), f"{'xyz'[wa]}{val:+.1f}", fill=(0, 0, 0))
            else:
                dr.line([(0, w_), (size, w_)], fill=col, width=1)
                if strong:
                    dr.text((2, w_ + 2), f"{'xyz'[wa]}{val:+.1f}", fill=(0, 0, 0))
    img.save(path)
    print("VIEW", v, path)
