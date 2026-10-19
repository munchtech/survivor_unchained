"""A steady flame (one tall tongue with licks) simulated in Blender (Mantaflow) for the flame kit's flipbook
(godot/art/fx/fb/flame_kit, FlameKit.cs). Our own art: nothing third-party goes in.

    blender -b -P tools/fxsim/flame_sim.py -- OUT_DIR [--res 192] [--frames 220] [--set "k=v;k=v"]

No render: the baked flame field is projected from the side (summed through the depth, an emissive volume seen
orthographically) straight into OUT_DIR/flame.npz (frames x height x width, float32, bottom row = the floor), so
the frames are noise-free. tools/fxsim/flame_pack.py loops, packs and adds motion vectors.
"""
import json
import os
import sys

import bpy
import numpy as np

T = dict(dom=(1.0, 1.0, 2.4), emit_r=0.11, emit_z=0.12, emit_flat=0.5, fuel=1.0, temp=1.2, vort=0.08, beta=1.2,
         alpha=0.0, burn=0.7, flame_vort=0.6, flame_ignition=1.25, flame_max_temp=1.75, tscale=1.0, dissolve=0)


def args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    o = dict(out=a[0], res=192, frames=220, set="")
    i = 1
    while i < len(a):
        k = a[i].lstrip("-")
        o[k] = type(o[k])(a[i + 1]) if not isinstance(o.get(k), str) else a[i + 1]
        i += 2
    return o


def main():
    o = args()
    t = dict(T)
    for kv in filter(None, o["set"].split(";")):
        k, v = kv.split("=", 1)
        t[k] = eval(v)
    out = os.path.abspath(o["out"])
    os.makedirs(out, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, o["frames"]
    sc.render.fps = 24
    W, D, H = t["dom"]
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, H / 2))
    dom = bpy.context.object
    dom.scale = (W, D, H)
    bpy.ops.object.transform_apply(scale=True)
    ds = dom.modifiers.new("Fluid", "FLUID")
    ds.fluid_type = "DOMAIN"
    ds = ds.domain_settings
    ds.domain_type = "GAS"
    ds.resolution_max = o["res"]
    ds.cache_type = "ALL"
    ds.cache_frame_start, ds.cache_frame_end = 1, o["frames"]
    ds.use_adaptive_domain = False
    ds.vorticity = t["vort"]
    ds.beta = t["beta"]
    ds.alpha = t["alpha"]
    ds.burning_rate = t["burn"]
    ds.flame_smoke = 0.0
    ds.flame_vorticity = t["flame_vort"]
    ds.flame_ignition = t["flame_ignition"]
    ds.flame_max_temp = t["flame_max_temp"]
    ds.time_scale = t["tscale"]
    ds.use_collision_border_bottom = True
    # A low flattened ball of fuel at the floor: the wick's bed.
    bpy.ops.mesh.primitive_uv_sphere_add(radius=t["emit_r"], location=(0, 0, t["emit_z"]))
    em = bpy.context.object
    em.scale = (1, 1, t["emit_flat"])
    f = em.modifiers.new("Fluid", "FLUID")
    f.fluid_type = "FLOW"
    fs = f.flow_settings
    fs.flow_type = "FIRE"
    fs.flow_behavior = "INFLOW"
    fs.flow_source = "MESH"
    fs.surface_distance = 0.02
    fs.subframes = 2
    fs.fuel_amount = t["fuel"]
    fs.temperature = t["temp"]
    ds.cache_directory = os.path.join(out, "cache")
    with bpy.context.temp_override(object=dom, active_object=dom, selected_objects=[dom], scene=sc):
        bpy.ops.fluid.bake_all()
    print("BAKED", flush=True)
    imgs = []
    for fr in range(1, o["frames"] + 1):
        sc.frame_set(fr)
        ev = dom.evaluated_get(bpy.context.evaluated_depsgraph_get()).modifiers["Fluid"].domain_settings
        res = [int(v) for v in ev.domain_resolution]
        n = res[0] * res[1] * res[2]
        a = np.empty(n, np.float32)
        try:
            ev.flame_grid.foreach_get(a)
        except Exception:
            a = np.array(ev.flame_grid, np.float32)
        if a.size != n:
            imgs.append(np.zeros((res[2], res[0]), np.float32))
            continue
        g = a.reshape(res[2], res[1], res[0])
        h = max(W, D, H) / max(res)
        imgs.append(g.sum(axis=1) * h)  # (z, x): the side view, emission summed through the depth
        if fr % 20 == 0:
            print("FRAME", fr, "max %.3f" % imgs[-1].max(), flush=True)
    np.savez_compressed(os.path.join(out, "flame.npz"), frames=np.stack(imgs))
    json.dump({"settings": t, "args": o}, open(os.path.join(out, "take.json"), "w"), indent=1)
    print("SAVED", out)


main()
