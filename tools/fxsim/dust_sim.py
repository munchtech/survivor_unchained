"""The Long Cut's dust jet (lc_dust): rock dust burst up out of a 2 m stretch of the split, rolling over into a low
grey-brown curtain of smoke, simulated in Blender (Mantaflow, smoke only) and rendered at the game's camera pitch as
straight-alpha 16-bit PNG frames (tools/fxsim/pack.py cuts the atlas). Not emissive: lit by a cold key from above and
the sky, so it has a lit top and a shadowed underside; the game tints it. Our own art: nothing third-party goes in.

    blender -b -P tools/fxsim/dust_sim.py -- OUT_DIR [--res 128] [--frames 64] [--fps 32] [--px 512] [--pitch 66]
        [--samples 64] [--seed 3] [--noise 2] [--render-only] [--bake-only] [--stats] [--only 4,10,30]
    python tools/fxsim/pack.py atlas OUT_DIR godot/art/fx/fb/lc_dust.png --cols 8 --cell 256 --fps 32

The line runs along X (-1..1 m), up is Z. Each jet is a charge punched up from the split, keyed (ease-out) so it
slows as it climbs, leaving its column behind; a drag field and slightly heavy dust make it hang and spread instead
of flying off; a turbulence field tears its edges.
"""
import json
import math
import os
import random
import sys

import bpy


def args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    o = dict(out=a[0], res=128, frames=64, fps=32, px=512, pitch=66.0, samples=64, seed=3, noise=2,
             bake_only=False, render_only=False, stats=False, only="", ortho=7.0, look_z=0.9,
             smoke_k=9.0, alpha=-0.25, vort=0.35, dissolve=70, drag=1.6, turb=1.6, up=(2.0, 3.8), dpow=1.0, cut=0.0, cache="", key=6.0, amb=0.2, jets=9, base=12, fade=(26.0, 0.0))
    i = 1
    while i < len(a):
        k = a[i].lstrip("-").replace("-", "_")
        if k in ("bake_only", "render_only", "stats"):
            o[k] = True; i += 1; continue
        v = a[i + 1]; i += 2
        o[k] = (tuple(float(x) for x in v.split(",")) if isinstance(o.get(k), tuple) else type(o[k])(v)) if k in o else v
    return o


def lumpy(obj, k, s=0.25):
    tx = bpy.data.textures.get("lumps") or bpy.data.textures.new("lumps", "CLOUDS")
    tx.noise_scale = s; tx.noise_depth = 2; tx.contrast = 1.3
    d = obj.modifiers.new("lumps", "DISPLACE"); d.texture = tx; d.texture_coords = "GLOBAL"
    d.strength = k; d.mid_level = 0.5


def charge(obj, name, on, keys, dens, vfac, vcoord=(0, 0, 0), tex=None):
    obj.name = name
    f = obj.modifiers.new("Fluid", "FLUID"); f.fluid_type = "FLOW"
    fs = f.flow_settings
    fs.flow_type = "SMOKE"; fs.flow_behavior = "INFLOW"; fs.flow_source = "MESH"
    if hasattr(fs, "use_absolute"):
        fs.use_absolute = True
    fs.surface_distance = 0.06; fs.volume_density = 1.0; fs.subframes = 6
    fs.density = dens; fs.temperature = 0.0
    fs.smoke_color = (0.5, 0.45, 0.4)
    fs.use_initial_velocity = True; fs.velocity_factor = vfac; fs.velocity_coord = vcoord
    if tex:
        tx = bpy.data.textures.new(name + "_tex", "CLOUDS")
        tx.noise_scale, tx.contrast, tx.intensity = tex; tx.noise_depth = 3
        fs.use_texture = True; fs.noise_texture = tx; fs.texture_map_type = "AUTO"; fs.texture_size = 1.0
    a, b = on
    for fr, v in ((1, a <= 1), (a, True), (b, True), (b + 1, False)):
        fs.use_inflow = v; fs.keyframe_insert("use_inflow", frame=fr)
    for fr, loc, s in keys:
        obj.location = loc; obj.scale = (s, s, s) if isinstance(s, float) else s
        obj.keyframe_insert("location", frame=fr); obj.keyframe_insert("scale", frame=fr)
    obj.hide_render = True


def main():
    o = args()
    print("ARGS", o)
    out = os.path.abspath(o["out"]); os.makedirs(out, exist_ok=True)
    rng = random.Random(o["seed"])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    F = o["frames"]
    sc.frame_start, sc.frame_end = 1, F
    sc.render.fps = o["fps"]

    W, D, H = 6.4, 4.4, 5.0
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, H / 2))
    dom = bpy.context.object; dom.name = "domain"; dom.scale = (W, D, H)
    bpy.ops.object.transform_apply(scale=True)
    fm = dom.modifiers.new("Fluid", "FLUID"); fm.fluid_type = "DOMAIN"
    ds = fm.domain_settings
    ds.domain_type = "GAS"; ds.resolution_max = o["res"]; ds.cache_type = "ALL"
    ds.cache_frame_start, ds.cache_frame_end = 1, F
    ds.use_adaptive_domain = False
    ds.vorticity = o["vort"]; ds.alpha = o["alpha"]; ds.beta = 0.0
    ds.cfl_condition = 2.0; ds.timesteps_max = 8; ds.timesteps_min = 2
    ds.use_dissolve_smoke = True; ds.dissolve_speed = o["dissolve"]; ds.use_dissolve_smoke_log = True
    ds.use_noise = o["noise"] > 0
    if o["noise"]:
        ds.noise_scale = o["noise"]; ds.noise_strength = 1.2
    ds.use_collision_border_bottom = True
    ds.effector_weights.gravity = 1.0

    # The jets: charges along the 2 m stretch, staggered by a frame or two, each punched up (fast, easing out) to
    # its own height (tall and short by turns: a ragged row, never a wall), leaning off the vertical, thin as it
    # leaves the split and swelling into a cap at the top, where it keeps feeding a frame or two (the rollover).
    n = o["jets"]
    for i in range(n):
        x = -0.95 + 1.9 * (i + rng.uniform(-0.3, 0.3)) / (n - 1)
        t0 = 1 + rng.choice([0, 0, 1, 1, 2, 3])
        top = rng.uniform(*o["up"]) * (rng.uniform(0.35, 0.6) if i % 2 else 1.0)
        lean = (rng.uniform(-0.4, 0.4), rng.uniform(-0.5, 0.5))
        T = rng.randint(6, 9)
        r0, r1 = rng.uniform(0.05, 0.08), rng.uniform(0.12, 0.24) * (0.7 if i % 2 else 1.0)
        keys = []
        for j in range(T + 1):
            u = j / T
            e = 1 - (1 - u) ** 2.4
            keys.append((t0 + j, (x + lean[0] * e, lean[1] * e, 0.08 + top * e), r0 + (r1 - r0) * u ** 2))
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0, location=keys[0][1])
        c = bpy.context.object
        lumpy(c, 0.18, 0.12)
        charge(c, f"jet{i}", (t0, t0 + T), keys, rng.uniform(0.8, 1.0), 0.55, tex=(0.35, 1.6, 1.0))
    # The base: puffs shoved out low both sides of the split, rolling out along the ground (dense at the foot).
    for i in range(o["base"]):
        side = 1 if i % 2 else -1
        x = rng.uniform(-1.0, 1.0)
        reach, T = rng.uniform(0.4, 1.0), rng.randint(6, 12)
        r0, r1 = rng.uniform(0.07, 0.11), rng.uniform(0.14, 0.24)
        keys = [(1 + j, (x + rng.uniform(-0.05, 0.05), side * (0.08 + reach * (1 - (1 - j / T) ** 2)),
                         0.1 + 0.25 * j / T), r0 + (r1 - r0) * j / T) for j in range(T + 1)]
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0, location=keys[0][1])
        b = bpy.context.object
        lumpy(b, 0.15, 0.12)
        charge(b, f"base{i}", (1, T - 2), keys, 0.9, 0.5, tex=(0.3, 1.8, 1.0))

    # Drag (the jets slow and hang), turbulence (torn edges), scrolled upward with the dust.
    if o["drag"] > 0:
        bpy.ops.object.effector_add(type="DRAG", location=(0, 0, 0))
        dg = bpy.context.object
        dg.field.linear_drag = o["drag"]; dg.field.quadratic_drag = 0.0
    bpy.ops.object.effector_add(type="TURBULENCE", location=(0, 0, 1.0))
    tb = bpy.context.object
    tb.field.size = 0.55; tb.field.flow = 0.0; tb.field.noise = 0.0
    for fr, v in ((1, o["turb"] * 2.0), (10, o["turb"]), (30, o["turb"] * 0.6), (F, o["turb"] * 0.3)):
        tb.field.strength = v; tb.field.keyframe_insert("strength", frame=fr)
    tb.keyframe_insert("location", frame=1)
    tb.location = (0.3, -0.2, 4.0); tb.keyframe_insert("location", frame=F)

    # The dust: a warm grey-brown scattering volume, a little dark absorption; its density the sim's times smoke_k.
    m = bpy.data.materials.new("dust"); m.use_nodes = True
    nt = m.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    outn = nt.nodes.new("ShaderNodeOutputMaterial")
    pv = nt.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Color"].default_value = (0.42, 0.36, 0.29, 1)
    pv.inputs["Absorption Color"].default_value = (0.05, 0.045, 0.04, 1)
    pv.inputs["Anisotropy"].default_value = 0.25
    pv.inputs["Density Attribute"].default_value = ""
    da = nt.nodes.new("ShaderNodeAttribute"); da.attribute_name = "density"
    dp = nt.nodes.new("ShaderNodeMath"); dp.operation = "POWER"; dp.inputs[1].default_value = o["dpow"]
    dk = nt.nodes.new("ShaderNodeMath"); dk.operation = "MULTIPLY"; dk.inputs[1].default_value = o["smoke_k"]
    # thin haze cut away (density below `cut` is clear air), so the dust has torn edges, never a fuzzy bulb
    dc = nt.nodes.new("ShaderNodeMath"); dc.operation = "SUBTRACT"; dc.inputs[1].default_value = o["cut"]
    dm = nt.nodes.new("ShaderNodeMath"); dm.operation = "MAXIMUM"; dm.inputs[1].default_value = 0.0
    nt.links.new(da.outputs["Fac"], dp.inputs[0]); nt.links.new(dp.outputs["Value"], dc.inputs[0])
    nt.links.new(dc.outputs["Value"], dm.inputs[0]); nt.links.new(dm.outputs["Value"], dk.inputs[0])
    nt.links.new(dk.outputs["Value"], pv.inputs["Density"])
    # thinning out: the whole cloud's density keyed from full at frame fade[0] to fade[1] of it at the last frame,
    # so the curtain is gone (not popped) when the flipbook ends
    f0, end = o["fade"]
    for fr, k in ((1, 1.0), (int(f0), 1.0), (int(f0 + (F - f0) * 0.5), 0.35 + 0.65 * end), (F, end)):
        dk.inputs[1].default_value = o["smoke_k"] * k; dk.inputs[1].keyframe_insert("default_value", frame=fr)
    nt.links.new(pv.outputs["Volume"], outn.inputs["Volume"])
    dom.data.materials.append(m)

    ds.cache_directory = os.path.abspath(o["cache"]) if o["cache"] else os.path.join(out, "cache")   # last: setting the domain after this frees the bake
    if not o["render_only"]:
        with bpy.context.temp_override(object=dom, active_object=dom, selected_objects=[dom], scene=sc):
            bpy.ops.fluid.bake_all()
        print("BAKED", ds.cache_directory)
    if o["bake_only"]:
        return
    if o["stats"]:
        import numpy as np
        for f in range(1, F + 1, 4):
            sc.frame_set(f)
            ev = dom.evaluated_get(bpy.context.evaluated_depsgraph_get()).modifiers["Fluid"].domain_settings
            res = [int(v) for v in ev.domain_resolution]
            a = np.empty(res[0] * res[1] * res[2], np.float32); ev.density_grid.foreach_get(a)
            if a.size != res[0] * res[1] * res[2]:
                print("STAT", f, "no grid"); continue
            a = a.reshape(res[2], res[1], res[0]); h = max(W, D, H) / max(res)
            m_ = a * o["smoke_k"] > 1.0
            if not m_.any():
                print("STAT", f, "empty"); continue
            zz = np.nonzero(m_.any(axis=(1, 2)))[0]; yy = np.nonzero(m_.any(axis=(0, 2)))[0]; xx = np.nonzero(m_.any(axis=(0, 1)))[0]
            print("STAT f%02d vol %.2f m3 x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f dmax %.2f" % (
                f, m_.sum() * h ** 3, xx[0] * h - W / 2, (xx[-1] + 1) * h - W / 2, yy[0] * h - D / 2,
                (yy[-1] + 1) * h - D / 2, zz[0] * h, (zz[-1] + 1) * h, a.max()), flush=True)

    pitch = math.radians(o["pitch"])
    cd = bpy.data.cameras.new("cam"); cd.type = "ORTHO"; cd.ortho_scale = o["ortho"]
    cam = bpy.data.objects.new("cam", cd); sc.collection.objects.link(cam)
    look = (0.0, 0.0, o["look_z"]); dist = 40.0
    cam.location = (look[0], look[1] - dist * math.cos(pitch), look[2] + dist * math.sin(pitch))
    cam.rotation_euler = (math.pi / 2 - pitch, 0, 0)
    sc.camera = cam
    sun_d = bpy.data.lights.new("key", "SUN"); sun_d.energy = o["key"]; sun_d.color = (1.0, 0.97, 0.92); sun_d.angle = 0.2
    sun = bpy.data.objects.new("key", sun_d); sc.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(55), math.radians(-10), math.radians(35))
    world = bpy.data.worlds.new("w"); sc.world = world; world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.55, 0.6, 0.7, 1); bg.inputs["Strength"].default_value = o["amb"]
    r = sc.render
    r.engine = "CYCLES"; sc.cycles.device = "GPU"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for kind in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = kind; prefs.get_devices()
            for d in prefs.devices:
                d.use = d.type == kind
            break
        except Exception:
            continue
    sc.cycles.samples = o["samples"]; sc.cycles.use_denoising = True
    sc.cycles.volume_max_steps = 512; sc.cycles.max_bounces = 4; sc.cycles.volume_bounces = 1
    r.film_transparent = True
    r.resolution_x = r.resolution_y = o["px"]
    r.image_settings.file_format = "PNG"; r.image_settings.color_mode = "RGBA"; r.image_settings.color_depth = "16"
    sc.view_settings.view_transform = "Standard"
    json.dump({"take": "lc_dust", "settings": {k: v for k, v in o.items()}}, open(os.path.join(out, "take.json"), "w"),
              indent=1, default=str)
    only = [int(v) for v in o["only"].split(",") if v] or range(1, F + 1)
    for f in only:
        sc.frame_set(f)
        r.filepath = os.path.join(out, f"f_{f:03d}.png")
        bpy.ops.render.render(write_still=True)
    print("RENDERED", out)


main()
