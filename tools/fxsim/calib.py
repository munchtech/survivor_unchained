"""Tiny Mantaflow bakes that measure what a setting does in metres and frames (so a take's numbers are chosen, not
guessed): how fast a turbulence field stirs, how far an initial velocity throws, how long fuel burns.

    blender -b -P tools/fxsim/calib.py -- OUT_DIR [case ...]
"""
import os
import sys

import bpy
import numpy as np

CASES = {
    # name: (domain overrides, flow overrides, turbulence strength, frames)
    "turb1": (dict(beta=0.0, alpha=0.0), dict(kind="SMOKE"), 1.0, 10),
    "turb5": (dict(beta=0.0, alpha=0.0), dict(kind="SMOKE"), 5.0, 10),
    "vel10": (dict(beta=0.0, alpha=0.0), dict(kind="SMOKE", vel=(0.0, 0.0, 10.0)), 0.0, 10),
    "fire": (dict(beta=2.5, alpha=0.3, burn=0.5), dict(kind="BOTH", fuel=2.5, temp=3.0), 0.0, 24),
    "fire_slow": (dict(beta=2.5, alpha=0.3, burn=0.3), dict(kind="BOTH", fuel=3.0, temp=3.0), 0.0, 24),
    "fire_ts4": (dict(beta=2.5, alpha=0.3, burn=0.5, ts=4.0), dict(kind="BOTH", fuel=2.5, temp=3.0), 0.0, 16),
    "vel10_ts4": (dict(beta=0.0, alpha=0.0, ts=4.0), dict(kind="SMOKE", vel=(0.0, 0.0, 10.0)), 0.0, 10),
    "turb5_ts4": (dict(beta=0.0, alpha=0.0, ts=4.0), dict(kind="SMOKE"), 5.0, 10),
    "fire12": (dict(beta=2.5, alpha=0.3, burn=0.5, size=12.0), dict(kind="BOTH", fuel=2.5, temp=3.0), 0.0, 16),
}


def case(out, name):
    dset, fset, turb, frames = CASES[name]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, frames
    sc.render.fps = 24
    S = dset.get("size", 6.0)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, S / 2))
    dom = bpy.context.object
    dom.scale = (S, S, S)
    bpy.ops.object.transform_apply(scale=True)
    fm = dom.modifiers.new("Fluid", "FLUID"); fm.fluid_type = "DOMAIN"
    ds = fm.domain_settings
    ds.domain_type = "GAS"; ds.resolution_max = 96; ds.cache_type = "ALL"
    ds.cache_frame_start, ds.cache_frame_end = 1, frames
    ds.beta = dset["beta"]; ds.alpha = dset["alpha"]; ds.burning_rate = dset.get("burn", 0.75)
    ds.vorticity = 0.0
    ds.time_scale = dset.get("ts", 1.0)
    ds.use_collision_border_bottom = True
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=0.6, location=(0, 0, 1.5))
    em = bpy.context.object
    f = em.modifiers.new("Fluid", "FLUID"); f.fluid_type = "FLOW"
    fs = f.flow_settings
    fs.flow_type = fset["kind"]; fs.flow_behavior = "INFLOW"; fs.flow_source = "MESH"
    fs.surface_distance = 0.1
    fs.density = 1.0
    if fset["kind"] != "SMOKE":
        fs.fuel_amount = fset["fuel"]; fs.temperature = fset["temp"]
    else:
        fs.temperature = 0.0
    if "vel" in fset:
        fs.use_initial_velocity = True; fs.velocity_factor = 0.0; fs.velocity_normal = 0.0
        fs.velocity_coord = fset["vel"]
    for fr, on in ((1, True), (2, True), (3, False)):
        fs.use_inflow = on; fs.keyframe_insert("use_inflow", frame=fr)
    em.hide_render = True
    if turb:
        bpy.ops.object.effector_add(type="TURBULENCE", location=(0, 0, 1.5))
        tf = bpy.context.object.field
        tf.strength = turb; tf.size = 1.0; tf.flow = 0.0; tf.noise = 0.0
    ds.cache_directory = os.path.join(out, name)
    if not READ_ONLY:
        with bpy.context.temp_override(object=dom, active_object=dom, selected_objects=[dom], scene=sc):
            bpy.ops.fluid.bake_all()
    res = None
    for fr in range(1, frames + 1):
        sc.frame_set(fr)
        ev = dom.evaluated_get(bpy.context.evaluated_depsgraph_get()).modifiers["Fluid"].domain_settings
        if res is None:
            res = [int(v) for v in ev.domain_resolution] if max(ev.domain_resolution) else [96, 96, 96]
            h = S / max(res)
            print(f"CASE {name} res {res} cell {h:.4f} m")
            zc = (np.arange(res[2]) + 0.5) * h
            xc = (np.arange(res[0]) + 0.5) * h - S / 2
        d = np.array(ev.density_grid, np.float32)
        if d.size != res[0] * res[1] * res[2]:
            print(" frame", fr, "grid size", d.size); continue
        d = d.reshape(res[2], res[1], res[0])  # axis 2 fastest
        m = d.sum() + 1e-9
        cen = [float((d.sum(tuple(j for j in range(3) if j != ax)) * ((np.arange(d.shape[ax]) + 0.5) * h)).sum() / m)
               for ax in range(3)]
        cz = cen[0]
        cx2 = 0.0
        if fr in (1, 4, 8, 12, 16, 24):
            print("   centroids per axis (m from the domain's corner):", ["%.2f" % c for c in cen])
        v = np.array(ev.velocity_grid, np.float32)
        sp = np.sqrt((v.reshape(-1, 3) ** 2).sum(1)) if v.size == 3 * d.size else np.zeros(1)
        msk = d.reshape(-1) > 0.05
        fl = np.array(ev.flame_grid, np.float32) if fset["kind"] != "SMOKE" else np.zeros(1)
        print(f" f{fr:02d} mass {m:9.1f} cz {cz:5.2f} m  sx {np.sqrt(cx2):4.2f} m  vmax {sp.max():8.3f}"
              f"  vmean(smoke) {sp[msk].mean() if msk.any() else 0:8.3f}  flame max {fl.max():5.2f}"
              f" mean>0.05 {fl[fl > 0.05].mean() if (fl > 0.05).any() else 0:5.2f} cells {(fl > 0.1).sum()}")


READ_ONLY = "--read" in sys.argv


def main():
    a = [v for v in sys.argv[sys.argv.index("--") + 1:] if v != "--read"]
    out = os.path.abspath(a[0])
    for name in a[1:] or list(CASES):
        case(out, name)


main()
