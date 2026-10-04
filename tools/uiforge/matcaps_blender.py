"""The interface's one light, baked into material spheres (matcaps).

Every forged piece of the interface is shaded from these: a sphere of each
material under the house light (a warm key from the upper left, a soft fill
from the front, a faint cool rim from behind on the lower right), seen
orthographically. tools/uiforge/forge.py looks a surface's normal up on the
sphere, so a plate, a button, a medallion and a cursor share exactly the
same light, and none of it is painted by hand.

Run with Blender 4.5:
    blender -b -P tools/uiforge/matcaps_blender.py

Writes tools/uiforge/matcaps/*.exr (linear float RGBA, 512 square).
"""
import math
import os

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "matcaps")
SIZE = 512

# White metal at several roughnesses (tinted by the forge), a white diffuse
# (dielectric with no specular), and black dielectric specular at several
# roughnesses (added over the tinted diffuse).
MATS = {
    "metal_15": dict(base=(1, 1, 1), metallic=1.0, rough=0.15),
    "metal_30": dict(base=(1, 1, 1), metallic=1.0, rough=0.30),
    "metal_45": dict(base=(1, 1, 1), metallic=1.0, rough=0.45),
    "metal_65": dict(base=(1, 1, 1), metallic=1.0, rough=0.65),
    "diffuse": dict(base=(1, 1, 1), metallic=0.0, rough=0.9, spec=0.0),
    "spec_08": dict(base=(0, 0, 0), metallic=0.0, rough=0.08, spec=0.5),
    "spec_30": dict(base=(0, 0, 0), metallic=0.0, rough=0.30, spec=0.5),
    "spec_60": dict(base=(0, 0, 0), metallic=0.0, rough=0.60, spec=0.5),
}


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def world():
    w = bpy.data.worlds.new("house")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    # A dark room, a touch warmer below (the fire) than above (the night).
    grad = nt.nodes.new("ShaderNodeTexGradient")
    coord = nt.nodes.new("ShaderNodeTexCoord")
    mapn = nt.nodes.new("ShaderNodeMapping")
    mapn.inputs["Rotation"].default_value = (0, math.radians(90), 0)
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.030, 0.018, 0.012, 1)
    ramp.color_ramp.elements[1].color = (0.012, 0.014, 0.024, 1)
    nt.links.new(coord.outputs["Generated"], mapn.inputs["Vector"])
    nt.links.new(mapn.outputs["Vector"], grad.inputs["Vector"])
    nt.links.new(grad.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 1.0


def area(name, loc, size, energy, color, shape="RECTANGLE", size_y=None):
    d = bpy.data.lights.new(name, "AREA")
    d.shape = shape
    d.size = size
    if size_y is not None:
        d.size_y = size_y
    d.energy = energy
    d.color = color
    o = bpy.data.objects.new(name, d)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    # Aim at the origin.
    direction = -o.location.normalized()
    o.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    return o


def lights():
    # Key: a warm softbox up and to the left, fairly low, so bevels facing it
    # shine and flat faces (which see the dark room behind the viewer) stay dark.
    area("key", (-6.0, 6.5, 4.5), 3.0, 1400, (1.0, 0.93, 0.84))
    # Sky: broad and dim from above, cooler: top edges read, nothing glares.
    area("sky", (0.0, 9.0, 2.5), 10.0, 380, (0.82, 0.86, 1.0))
    # Rim: a thin cool strip behind, low right: the night behind the plate.
    area("rim", (6.5, -5.5, -2.0), 6.0, 700, (0.62, 0.66, 1.0), shape="RECTANGLE", size_y=1.0)
    # Front: a broad soft lamp behind the viewer's shoulder, so flat metal
    # shows its colour (gold reads as gold face-on) without glare.
    area("front", (-1.5, 1.5, 12.0), 16.0, 170, (1.0, 0.95, 0.88))
    # A small hot kicker up left for crisp speculars on polished edges.
    area("kick", (-3.6, 4.2, 3.4), 0.5, 120, (1.0, 0.92, 0.8), shape="DISK")


def material(name, base, metallic, rough, spec=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*base, 1)
    p.inputs["Metallic"].default_value = metallic
    p.inputs["Roughness"].default_value = rough
    p.inputs["Specular IOR Level"].default_value = spec
    return m


def main():
    os.makedirs(OUT, exist_ok=True)
    clear()
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 256
    sc.cycles.use_denoising = True
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "OPTIX"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        sc.cycles.device = "GPU"
    except Exception:
        pass
    sc.render.resolution_x = sc.render.resolution_y = SIZE
    sc.render.film_transparent = True
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    # Linear and unclipped: the forge tone-maps after shading.
    sc.render.image_settings.file_format = "OPEN_EXR"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.image_settings.color_depth = "32"
    world()
    lights()
    bpy.ops.mesh.primitive_uv_sphere_add(segments=128, ring_count=64, radius=1.0)
    sphere = bpy.context.active_object
    bpy.ops.object.shade_smooth()
    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 2.0
    cam = bpy.data.objects.new("cam", cam_data)
    sc.collection.objects.link(cam)
    cam.location = (0, 0, 10)
    cam.rotation_euler = (0, 0, 0)
    sc.camera = cam
    import numpy as np
    caps = {}
    for name, spec in MATS.items():
        m = material(name, spec["base"], spec["metallic"], spec["rough"], spec.get("spec", 0.5))
        sphere.data.materials.clear()
        sphere.data.materials.append(m)
        exr = os.path.join(OUT, f"{name}.exr")
        sc.render.filepath = exr
        bpy.ops.render.render(write_still=True)
        # Kept small for the repository: 256 square, half floats, top row first.
        im = bpy.data.images.load(exr)
        w, h = im.size
        px = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1]
        px = px.reshape(h // 2, 2, w // 2, 2, 4).mean(axis=(1, 3))
        caps[name] = px[..., :3].astype(np.float16)
        bpy.data.images.remove(im)
        os.remove(exr)
        print("matcap", name, float(px[..., :3].max()), px[h // 4, w // 4, :3], flush=True)
    np.savez_compressed(os.path.join(OUT, "matcaps.npz"), **caps)


main()
