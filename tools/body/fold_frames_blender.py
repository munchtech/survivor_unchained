"""Blender side of fold_frames.py (run in background: blender -b -P this -- job.json). Renders each frame bare and clothed."""
import json
import math
import sys
import time
from pathlib import Path

import bpy
from mathutils import Vector

job = json.loads(Path(sys.argv[sys.argv.index("--") + 1]).read_text())
od = Path(job["dir"])
CAMS = {"mid": dict(pitch=15, dist=4.2, h=1.0, fov=34), "near": dict(pitch=3, dist=2.80, h=1.6, fov=24)}
AZ = {"front": 0, "back": 180, "r34": 45, "side_r": 90}


def B(v):                      # glb (x, y up, z) -> Blender (x, -z, y)
    return Vector((v[0], -v[2], v[1]))


sc = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.render.image_settings.file_format = "PNG"
try:
    sc.render.engine = "BLENDER_EEVEE_NEXT"
    sc.eevee.taa_render_samples = 32
except Exception:
    sc.render.engine = "BLENDER_EEVEE"
sc.view_settings.view_transform = "Standard"
w = bpy.data.worlds.new("w")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.2, 0.2, 0.2, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 1.0


def mat(name, color=None, tex=None, rough=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = rough
    if tex:
        t = m.node_tree.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(tex)
        t.image.colorspace_settings.name = "sRGB"
        m.node_tree.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        bsdf.inputs["Base Color"].default_value = color
    return m


M_CLOTH = mat("cloth", color=(0.32, 0.37, 0.45, 1), rough=0.6)
_M = {}


def part_mat(tag):
    d = job["mats"].get(tag)
    if d is None:
        return M_CLOTH
    if tag not in _M:
        _M[tag] = mat(tag, color=tuple(d.get("color", (0.05, 0.05, 0.05, 1))), tex=d.get("tex"), rough=d.get("rough", 0.5))
    return _M[tag]

cam_d = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cam_d)
sc.collection.objects.link(cam)
sc.camera = cam
cam_d.sensor_fit = "VERTICAL"
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
sun.data.energy = 3.0
fill = bpy.data.objects.new("fill", bpy.data.lights.new("fill", "SUN"))
fill.data.energy = 0.8
sc.collection.objects.link(sun)
sc.collection.objects.link(fill)


def look(obj, pos, tgt):
    obj.location = pos
    obj.rotation_euler = (tgt - pos).to_track_quat("-Z", "Y").to_euler()


def sun_dir(o, cp, tgt, kx, ky):     # light comes from the camera's right-factor kx, up-factor ky (negative kx = left)
    fwd = (tgt - cp).normalized()
    right = fwd.cross(Vector((0, 0, 1))).normalized()
    up = right.cross(fwd).normalized()
    src = (-fwd + right * kx + up * ky).normalized()
    o.rotation_euler = (-src).to_track_quat("-Z", "Y").to_euler()


def load(fn, material):
    before = set(bpy.data.objects)
    bpy.ops.wm.obj_import(filepath=str(od / fn), forward_axis="NEGATIVE_Z", up_axis="Y")
    o = next(x for x in bpy.data.objects if x not in before)
    for poly in o.data.polygons:
        poly.use_smooth = True
    o.data.materials.clear()
    o.data.materials.append(material)
    return o


ts = []
for pose, pi in job["poses"].items():
    frames = [f for f in job["frames"] if f["pose"] == pose]
    body = [load(fn, part_mat(t)) for t, fn in pi["files"].items() if t not in ("top", "skirt")]
    cloth = [load(fn, M_CLOTH) for t, fn in pi["files"].items() if t in ("top", "skirt")]
    ax, az_ = pi["aim_xz"]
    for f in frames:
        c = CAMS[f["cam"]]
        pr = math.radians(c["pitch"])
        a = math.radians(AZ[f["az"]])
        tgt = B((ax, c["h"], az_))
        dirh = (-math.sin(a), math.cos(a))   # toward -x for + az; front = +z
        cp = B((ax + c["dist"] * math.cos(pr) * dirh[0], c["h"] + c["dist"] * math.sin(pr), az_ + c["dist"] * math.cos(pr) * dirh[1]))
        cam_d.angle = math.radians(c["fov"])
        cam_d.clip_start, cam_d.clip_end = 0.1, 50
        look(cam, cp, tgt)
        sun_dir(sun, cp, tgt, -0.8, 0.8)
        sun.data.energy = 3.0
        sun_dir(fill, cp, tgt, 0.8, 0.2)
        for kind in ("bare", "clothed"):
            if kind == "clothed" and not cloth:
                continue
            for o in cloth:
                o.hide_render = kind == "bare"
            sc.render.filepath = str(od / f"{job['name']}_{pose.replace(':', '-')}_{f['cam']}_{f['az']}_{kind}.png")
            t0 = time.time()
            bpy.ops.render.render(write_still=True)
            ts.append(time.time() - t0)
            print("rendered", sc.render.filepath, f"{ts[-1]:.1f}s", flush=True)
    for o in body + cloth:
        bpy.data.objects.remove(o)
print(f"FRAMES {len(ts)} mean {sum(ts) / max(len(ts), 1):.1f}s")
