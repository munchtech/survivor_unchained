"""A fire-and-smoke burst simulated in Blender (Mantaflow) and rendered at the game's camera angle, frame by frame,
as RGBA on transparent (premultiplied), for a Flare's flipbook (tools/fxsim/pack.py cuts the atlas). Our own art:
nothing third-party goes in.

    blender -b -P tools/fxsim/boom_sim.py -- OUT_DIR [--take burns_boom] [--res 160] [--frames 48] [--px 512]
        [--pitch 66] [--samples 48] [--bake-only] [--render-only]

Takes are named presets (TAKES below): each is one look, fixed, so a take can be made again exactly.
OUT_DIR gets cache/ (the sim) and f_NNN.png (the frames). Units are metres; the domain's floor is the ground.
"""
import json
import math
import os
import random
import sys

import bpy

TAKES = {
    # Burns Twice's last word: one column of fire punched up out of the crater, a skirt of flame thrown along the
    # ground, rolling into a fireball that climbs and darkens to smoke, thinning fast so it never hangs over her.
    "burns_boom": dict(
        dom=(11.0, 11.0, 12.0), emit_r=0.7, emit_z=0.5, top=7.0, rise=5, out=4.0, burst=(1, 6),
        fuel=2.5, temp=3.0, smoke=0.5, vort=0.6, beta=2.5, alpha=0.3, burn=0.5, flame_smoke=0.8,
        dissolve=12, noise_k=1.0, flame_pow=1.6, smoke_k=4.0, noise=2, skirt=True, skirt_to=3.4, skirt_burst=(1, 4), vfac=0.8, tscale=1.0, emit_k=7.0,
        look_z=0.5, ortho=15.4,
    ),
    # The same, its fire carried on thrown puffs (born torn, cauliflowered), in a wider domain.
    "burns_boom2": dict(
        dom=(13.0, 13.0, 13.0), emit_r=0.6, emit_z=0.5, top=7.0, rise=5, out=4.0, burst=(1, 6),
        fuel=2.0, temp=3.0, smoke=1.0, vort=0.3, beta=2.5, alpha=0.3, burn=0.55, flame_smoke=0.8,
        dissolve=14, noise_k=1.0, flame_pow=2.0, smoke_k=8.0, flame_vort=1.5,
        noise=0, skirt=False, skirt_to=3.4, skirt_burst=(1, 3), vfac=0.6, tscale=1.0, emit_k=4.0,
        look_z=0.5, ortho=17.0, particles=True,
        col_n=260, col_f=5, col_v=26.0, col_r=7.0, col_life=7, col_g=0.6, col_size=5.0,
        bl_n=360, bl_f=3, bl_v=17.0, bl_r=5.0, bl_life=9, bl_g=1.0, bl_size=4.0, bl_up=2.5, bl_drag=0.35,
    ),
    # Solid lumpy charges (displaced in world space, so a moving one boils as it goes, never a smooth bulb), the sim
    # run at four times its own speed (at 12 m Mantaflow's buoyancy rises about 0.3 m in 16 frames: tools/fxsim/
    # calib.py), so the fire tears, rolls and climbs at a real fireball's pace: a core punched to 7.3 m in four
    # frames, a root that keeps the pillar alight, and fourteen tongues of flame thrown out along the ground.
    "burns_boom3": dict(
        dom=(12.5, 12.5, 12.5), tscale=4.0, steps_max=4, vort=0.3, flame_vort=1.0, beta=2.5, alpha=0.3,
        burn=0.12, flame_smoke=1.0, dissolve=40, noise=0, noise_k=1.0,
        fuel=2.0, temp=3.0, smoke=0.6, vfac=0.3, out=1.0, vol=1.0, surf=0.1,
        core_r=0.85, core_keys=((1, 0.6, 1.0), (2, 3.0, 1.2), (3, 4.8, 1.4), (4, 6.0, 1.55), (5, 6.6, 1.65)),
        core_off=6, lump=0.9, lump_s=0.55,
        root_r=1.15, root_fuel=((1, 2.0), (6, 1.6), (10, 0.8), (12, 0.3)), root_off=13, root_up=3.0,
        jets=14, jet_long=(3.2, 4.3), jet_short=(1.6, 2.6), jet_r=(0.3, 0.6), jet_t=3, jet_seed=5, jet_fuel=2.0,
        turb=((1, 4.0), (12, 2.5), (30, 1.0), (48, 0.5)), turb_size=1.0,
        flame_pow=1.6, emit_k=1.0, smoke_k=6.0, dpow=1.3, smoke_rgb=(0.16, 0.13, 0.11),
        smoke_keys=((1, 1.0), (16, 1.0), (32, 0.35), (46, 0.0)), fire_keys=(),
        amb=0.25, look=3.75, ortho=14.6,
        tone=dict(exp=1.0, knee=0.65, hot=0.25, amb=(0.030, 0.025, 0.020)),
    ),
}


def args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    o = dict(out=a[0], take="burns_boom", res=160, frames=48, px=512, pitch=66.0, samples=48,
             bake_only=False, render_only=False, set="", only="", fmt="exr")
    i = 1
    while i < len(a):
        k = a[i].lstrip("-").replace("-", "_")
        if k in ("bake_only", "render_only"):
            o[k] = True; i += 1; continue
        v = a[i + 1]; i += 2
        o[k] = type(o[k])(v) if k in o else v
    return o


def keyed(nt, name, keys, default):
    """A Value node animated through (frame, value) keys (linear), so a take can thin its smoke or cool its fire on a
    schedule the sim alone would not keep."""
    v = nt.nodes.new("ShaderNodeValue"); v.name = name
    v.outputs[0].default_value = default
    for fr, val in keys:
        v.outputs[0].default_value = val
        v.outputs[0].keyframe_insert("default_value", frame=fr)
    if keys and nt.animation_data and nt.animation_data.action:
        for fc in nt.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
    return v


def flame_material(t):
    """Fire from the sim's flame field (raised to a power, so the heart is hot and the edges cool to deep red)
    through a black-red-orange-yellow ramp; smoke a dark warm grey, lit by the fire inside it. Its density is the
    sim's raised to dpow (the thin late smoke clears faster than the thick early smoke) times a keyed taper."""
    m = bpy.data.materials.new("boom_volume")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    pv = nt.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Color"].default_value = tuple(t.get("smoke_rgb", (0.07, 0.06, 0.055))) + (1,)
    pv.inputs["Density"].default_value = t.get("smoke_k", 4.0)
    pv.inputs["Anisotropy"].default_value = 0.3
    pv.inputs["Absorption Color"].default_value = (0.02, 0.02, 0.02, 1)
    pv.inputs["Blackbody Intensity"].default_value = 0.0
    if "dpow" in t:
        pv.inputs["Density Attribute"].default_value = ""
        da = nt.nodes.new("ShaderNodeAttribute"); da.attribute_name = "density"
        dp = nt.nodes.new("ShaderNodeMath"); dp.operation = "POWER"; dp.inputs[1].default_value = t["dpow"]
        dk = nt.nodes.new("ShaderNodeMath"); dk.operation = "MULTIPLY"; dk.inputs[1].default_value = t.get("smoke_k", 4.0)
        dt = nt.nodes.new("ShaderNodeMath"); dt.operation = "MULTIPLY"
        tap = keyed(nt, "smoke_taper", t.get("smoke_keys", ()), 1.0)
        nt.links.new(da.outputs["Fac"], dp.inputs[0])
        nt.links.new(dp.outputs["Value"], dk.inputs[0])
        nt.links.new(dk.outputs["Value"], dt.inputs[0])
        nt.links.new(tap.outputs[0], dt.inputs[1])
        nt.links.new(dt.outputs["Value"], pv.inputs["Density"])
    fl = nt.nodes.new("ShaderNodeAttribute"); fl.attribute_name = "flame"
    src = fl.outputs["Fac"]
    if t.get("fnoise", 0.0) > 0:
        # Licks finer than the grid: the flame broken by a 3D noise that climbs with the fire.
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = t.get("fnoise_s", 2.5)
        nz.inputs["Detail"].default_value = 4.0; nz.inputs["Roughness"].default_value = 0.6
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
        loc = mp.inputs["Location"]
        loc.default_value = (0, 0, 0); loc.keyframe_insert("default_value", frame=1)
        loc.default_value = (0, 0, -t.get("fnoise_up", 4.0)); loc.keyframe_insert("default_value", frame=49)
        sub = nt.nodes.new("ShaderNodeMath"); sub.operation = "MULTIPLY_ADD"
        sub.inputs[1].default_value = 2.0 * t["fnoise"]; sub.inputs[2].default_value = 1.0 - t["fnoise"]
        nt.links.new(nz.outputs["Fac"], sub.inputs[0])
        mf = nt.nodes.new("ShaderNodeMath"); mf.operation = "MULTIPLY"; mf.use_clamp = True
        nt.links.new(src, mf.inputs[0]); nt.links.new(sub.outputs["Value"], mf.inputs[1])
        src = mf.outputs["Value"]
    pw = nt.nodes.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = t.get("flame_pow", 1.6)
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.elements[0].position = 0.0; cr.elements[0].color = (0, 0, 0, 1)
    cr.elements[1].position = 1.0; cr.elements[1].color = (1.0, 0.9, 0.7, 1)
    for p, c in ((0.06, (0.12, 0.01, 0.0, 1)), (0.25, (0.75, 0.1, 0.008, 1)), (0.55, (1.0, 0.4, 0.04, 1)),
                 (0.82, (1.0, 0.72, 0.28, 1))):
        e = cr.elements.new(p); e.color = c
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = t["emit_k"]
    nt.links.new(src, pw.inputs[0])
    nt.links.new(pw.outputs["Value"], ramp.inputs["Fac"])
    nt.links.new(pw.outputs["Value"], mul.inputs[0])
    nt.links.new(ramp.outputs["Color"], pv.inputs["Emission Color"])
    strength = mul.outputs["Value"]
    if t.get("fire_keys"):
        fk = keyed(nt, "fire_taper", t["fire_keys"], 1.0)
        fm = nt.nodes.new("ShaderNodeMath"); fm.operation = "MULTIPLY"
        nt.links.new(strength, fm.inputs[0]); nt.links.new(fk.outputs[0], fm.inputs[1])
        strength = fm.outputs["Value"]
    nt.links.new(strength, pv.inputs["Emission Strength"])
    nt.links.new(pv.outputs["Volume"], out.inputs["Volume"])
    return m


def main():
    o = args()
    t = dict(TAKES[o["take"]])
    for kv in filter(None, o["set"].split(";")):
        k, v = kv.split("=")
        t[k] = type(t[k])(v) if k in t and not isinstance(t[k], (tuple, bool)) else eval(v)
    print("TAKE", t)
    out = os.path.abspath(o["out"])
    os.makedirs(out, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, o["frames"]
    sc.render.fps = 24

    W, D, H = t["dom"]
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, H / 2))
    dom = bpy.context.object; dom.name = "domain"
    dom.scale = (W, D, H)
    bpy.ops.object.transform_apply(scale=True)
    fm = dom.modifiers.new("Fluid", "FLUID"); fm.fluid_type = "DOMAIN"
    ds = fm.domain_settings
    ds.domain_type = "GAS"
    ds.resolution_max = o["res"]
    ds.cache_type = "ALL"
    ds.cache_frame_start, ds.cache_frame_end = 1, o["frames"]
    ds.use_adaptive_domain = False
    ds.vorticity = t["vort"]
    ds.beta = t["beta"]
    ds.alpha = t["alpha"]
    ds.burning_rate = t["burn"]
    ds.flame_smoke = t["flame_smoke"]
    ds.flame_vorticity = t.get("flame_vort", 0.6)
    ds.flame_smoke_color = (0.06, 0.05, 0.045)
    ds.use_dissolve_smoke = True
    ds.dissolve_speed = t["dissolve"]
    ds.use_dissolve_smoke_log = True
    ds.use_noise = t["noise"] > 0
    if t["noise"]:
        ds.noise_scale = t["noise"]
        ds.noise_strength = t.get("noise_k", 1.0)
    ds.use_collision_border_bottom = True
    dom.data.materials.append(flame_material(t))

    ds.time_scale = t.get("tscale", 1.0)
    if "steps_max" in t:
        ds.timesteps_max = t["steps_max"]

    def emitter(name, obj, normal, burst, keys):
        """keys: (frame, location, scale) the emitter moves through; it trails fuel along its way (it hands on its
        own motion to what it emits), so a core punched upward leaves the column behind it."""
        obj.name = name
        f = obj.modifiers.new("Fluid", "FLUID"); f.fluid_type = "FLOW"
        fs = f.flow_settings
        fs.flow_type = "BOTH"; fs.flow_behavior = "INFLOW"; fs.flow_source = "MESH"
        fs.surface_distance = 0.35; fs.subframes = 6
        fs.fuel_amount = t["fuel"]; fs.temperature = t["temp"]; fs.density = t["smoke"]
        fs.smoke_color = (0.06, 0.05, 0.045)
        fs.use_initial_velocity = True
        fs.velocity_factor = t.get("vfac", 0.8)
        fs.velocity_normal = normal
        fs.velocity_random = t.get("vrand", 0.0)
        if t.get("tex", 0.0) > 0:
            # Uneven fuel: a cloud texture over the emitter, so the burst is born torn, never a smooth bulb.
            tx = bpy.data.textures.get("emit_clouds") or bpy.data.textures.new("emit_clouds", "CLOUDS")
            tx.noise_scale = t["tex"]; tx.noise_depth = 3; tx.contrast = 1.6
            fs.use_texture = True; fs.noise_texture = tx; fs.texture_map_type = "AUTO"; fs.texture_size = 1.0
        a, b = burst
        for fr, on in ((1, True), (b, True), (b + 1, False)):
            fs.use_inflow = on
            fs.keyframe_insert("use_inflow", frame=fr)
        for fr, loc, s in keys:
            obj.location = loc; obj.scale = (s[0], s[1], s[2])
            obj.keyframe_insert("location", frame=fr); obj.keyframe_insert("scale", frame=fr)
        obj.hide_render = True
        return obj

    def puffs(name, obj, count, frames, vel, rand, life, grav, size, up=0.0, drag=0.0, seed=1):
        """A burst of fuel carried on thrown particles (each a little puff that burns along its flight), so the fire
        is born lumpy and torn, the way a real blast's is, never a smooth bulb."""
        obj.name = name
        ps_mod = obj.modifiers.new("ps", "PARTICLE_SYSTEM")
        p = ps_mod.particle_system.settings
        ps_mod.particle_system.seed = seed
        p.count = count; p.frame_start = frames[0]; p.frame_end = frames[1]; p.lifetime = life; p.lifetime_random = 0.4
        p.emit_from = "FACE"; p.use_emit_random = True; p.distribution = "RAND"
        p.normal_factor = vel; p.factor_random = rand; p.object_align_factor = (0, 0, up)
        p.effector_weights.gravity = grav; p.drag_factor = drag
        p.render_type = "NONE"; p.display_method = "DOT"
        f = obj.modifiers.new("Fluid", "FLUID"); f.fluid_type = "FLOW"
        fs = f.flow_settings
        fs.flow_type = "BOTH"; fs.flow_behavior = "INFLOW"; fs.flow_source = "PARTICLES"
        fs.particle_system = ps_mod.particle_system
        fs.use_particle_size = True; fs.particle_size = size; fs.subframes = 4
        fs.fuel_amount = t["fuel"]; fs.temperature = t["temp"]; fs.density = t["smoke"]
        fs.smoke_color = (0.06, 0.05, 0.045)
        fs.use_initial_velocity = True; fs.velocity_factor = t.get("vfac", 0.8)
        obj.hide_render = True
        return obj

    def lumpy(obj, k):
        """A clouds displacement sampled in world space: the charge's outline boils as it moves, so neither it nor
        the trail it lays is ever a smooth bulb or a smooth tube."""
        tx = bpy.data.textures.get("lumps") or bpy.data.textures.new("lumps", "CLOUDS")
        tx.noise_scale = t.get("lump_s", 0.55); tx.noise_depth = 2; tx.contrast = 1.3
        d = obj.modifiers.new("lumps", "DISPLACE"); d.texture = tx; d.texture_coords = "GLOBAL"
        d.strength = k; d.mid_level = 0.5

    def charge(name, obj, on, keys=(), fuel=1.0, temp=3.0, smoke=0.5, vcoord=None, vfac=0.0, normal=0.0,
               fuel_keys=()):
        """A solid flow (it fills its volume, not a shell) of fuel, heat and smoke, on for frames on[0]..on[1];
        keys: (frame, location, scale), linear, so a punch starts at full speed."""
        obj.name = name
        f = obj.modifiers.new("Fluid", "FLUID"); f.fluid_type = "FLOW"
        fs = f.flow_settings
        fs.flow_type = "BOTH"; fs.flow_behavior = "INFLOW"; fs.flow_source = "MESH"
        fs.surface_distance = t.get("surf", 0.1); fs.volume_density = t.get("vol", 1.0); fs.subframes = 8
        fs.fuel_amount = fuel; fs.temperature = temp; fs.density = smoke
        fs.smoke_color = (0.06, 0.05, 0.045)
        fs.use_initial_velocity = True
        fs.velocity_factor = vfac; fs.velocity_normal = normal
        if vcoord:
            fs.velocity_coord = vcoord
        a, b = on
        for fr, v in ((1, a <= 1), (a, True), (b, True), (b + 1, False)):
            fs.use_inflow = v; fs.keyframe_insert("use_inflow", frame=fr)
        for fr, v in fuel_keys:
            fs.fuel_amount = v; fs.keyframe_insert("fuel_amount", frame=fr)
        for fr, loc, sc_ in keys:
            obj.location = loc; obj.scale = sc_
            obj.keyframe_insert("location", frame=fr); obj.keyframe_insert("scale", frame=fr)
        if obj.animation_data and obj.animation_data.action:
            for fc in obj.animation_data.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"
        obj.hide_render = True
        return obj

    if t.get("core_keys"):
        # The core: punched up out of the crater, trailing the pillar.
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=t["core_r"], location=(0, 0, 0.6))
        c = bpy.context.object
        lumpy(c, t["lump"])
        charge("core", c, (1, t["core_off"] - 1), [(fr, (0, 0, z), (k, k, k)) for fr, z, k in t["core_keys"]],
               t["fuel"], t["temp"], t["smoke"], vfac=t["vfac"], normal=t["out"])
        # The root: the crater keeps burning, a flattened lumpy charge, its fuel running down.
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1.0, location=(0, 0, 0.2))
        rt = bpy.context.object
        rt.scale = (t["root_r"], t["root_r"], t["root_r"] * 0.4)
        lumpy(rt, 0.5)
        charge("root", rt, (1, t["root_off"] - 1), (), t["root_fuel"][0][1], t["temp"], t["smoke"],
               vcoord=(0.0, 0.0, t["root_up"]), fuel_keys=t["root_fuel"])
        # The tongues: thrown out flat along the ground, long and short by turns, fastest at the start.
        rng = random.Random(t["jet_seed"])
        n = t["jets"]
        T = t["jet_t"]
        for i in range(n):
            ang = (i + rng.uniform(-0.35, 0.35)) * 2 * math.pi / n
            L = rng.uniform(*(t["jet_long"] if i % 2 == 0 else t["jet_short"]))
            r_a, r_b = t["jet_r"]
            r_b *= rng.uniform(0.75, 1.15) * (1.0 if i % 2 == 0 else 0.8)
            keys = []
            for j in range(T + 1):
                u = j / T
                rr = 0.7 + (L - 0.7) * (1 - (1 - u) ** 2)
                k = r_a + (r_b - r_a) * u
                keys.append((1 + j, (rr * math.cos(ang), rr * math.sin(ang), 0.3 + 0.35 * u), (k, k, k * 0.8)))
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0, location=keys[0][1])
            jt = bpy.context.object
            lumpy(jt, 0.8)
            charge(f"jet{i}", jt, (1, T + 1), keys, t["jet_fuel"], t["temp"] * 0.9, t["smoke"] * 0.7, vfac=t["vfac"])
        if t.get("turb"):
            # A turbulence field, scrolled upward: early tearing at the scale of a licking tongue.
            bpy.ops.object.effector_add(type="TURBULENCE", location=(0, 0, 2.0))
            tb = bpy.context.object
            tb.field.size = t.get("turb_size", 1.0); tb.field.flow = 0.0; tb.field.noise = 0.0
            for fr, v in t["turb"]:
                tb.field.strength = v; tb.field.keyframe_insert("strength", frame=fr)
            tb.location = (0, 0, 2.0); tb.keyframe_insert("location", frame=1)
            tb.location = (0.4, -0.3, 8.0); tb.keyframe_insert("location", frame=o["frames"])
    r0 = t.get("emit_r", 0.7)
    top = t.get("top", 7.0)
    if t.get("core_keys"):
        pass
    elif t.get("particles"):
        # The column: puffs thrown straight up out of the crater, fast; the blast: puffs thrown out flat along the
        # ground from a ring (an open cylinder's sides face outward), a little upward.
        if t.get("core_mesh"):
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=r0, location=(0, 0, t["emit_z"]))
            emitter("core", bpy.context.object, t["out"] * 0.3, t["burst"],
                    [(1, (0, 0, t["emit_z"]), (1, 1, 1)), (t["rise"], (0, 0, top), (1.6, 1.6, 1.6))])
        else:
          bpy.ops.mesh.primitive_circle_add(vertices=24, radius=r0, fill_type="NGON", location=(0, 0, 0.25))
          puffs("column", bpy.context.object, t["col_n"], (1, t["col_f"]), t["col_v"], t["col_r"], t["col_life"],
                t["col_g"], t["col_size"], seed=3)
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=r0 * 1.1, depth=0.5, end_fill_type="NOTHING", location=(0, 0, 0.35))
        puffs("blast", bpy.context.object, t["bl_n"], (1, t["bl_f"]), t["bl_v"], t["bl_r"], t["bl_life"],
              t["bl_g"], t["bl_size"], up=t["bl_up"], drag=t["bl_drag"], seed=7)
    else:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=r0, location=(0, 0, t["emit_z"]))
        emitter("core", bpy.context.object, t["out"] * 0.3, t["burst"],
                [(1, (0, 0, t["emit_z"]), (1, 1, 1)), (t["rise"], (0, 0, top), (1.6, 1.6, 1.6))])
    if t.get("skirt") and not t.get("particles") and not t.get("core_keys"):
        # The skirt: a flat ring at the ground spreading fast, throwing flame outward along it.
        bpy.ops.mesh.primitive_torus_add(major_radius=r0 * 1.2, minor_radius=0.22, location=(0, 0, 0.25))
        sk = t["skirt_to"]
        emitter("skirt", bpy.context.object, 2.0, t["skirt_burst"],
                [(1, (0, 0, 0.25), (1, 1, 1)), (t["skirt_burst"][1], (0, 0, 0.3), (sk, sk, 1))])

    # Last: changing any domain setting after this frees (deletes) the baked cache, so a render-only run would
    # find it gone.
    ds.cache_directory = os.path.join(out, "cache")
    if not o["render_only"]:
        with bpy.context.temp_override(object=dom, active_object=dom, selected_objects=[dom], scene=sc):
            bpy.ops.fluid.bake_all()
        print("BAKED", ds.cache_directory)
    if o["bake_only"]:
        return

    # The camera: the game's pitch, orthographic, looking at the column's middle, framing the whole domain.
    pitch = math.radians(o["pitch"])
    cam_d = bpy.data.cameras.new("cam"); cam_d.type = "ORTHO"; cam_d.ortho_scale = t["ortho"]
    cam = bpy.data.objects.new("cam", cam_d); sc.collection.objects.link(cam)
    look = (0.0, 0.0, t["look"] if "look" in t else H * t["look_z"])
    dist = 60.0
    cam.location = (look[0], look[1] - dist * math.cos(pitch), look[2] + dist * math.sin(pitch))
    cam.rotation_euler = (math.pi / 2 - pitch, 0, 0)
    sc.camera = cam
    # A faint cold key from the sky (the night's moon), so the smoke has a side away from the fire.
    sun_d = bpy.data.lights.new("moon", "SUN"); sun_d.energy = 0.35; sun_d.color = (0.6, 0.7, 1.0)
    sun = bpy.data.objects.new("moon", sun_d); sc.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(35), 0, math.radians(30))
    world = bpy.data.worlds.new("w"); sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    if "amb" in t:
        # A dim ambient from the whole sky, so the smoke has form and a dark warm grey of its own (never pure
        # black by day); the frames are transparent, so the sky itself is never seen.
        bg.inputs["Color"].default_value = (0.6, 0.6, 0.62, 1); bg.inputs["Strength"].default_value = t["amb"]
    else:
        bg.inputs["Color"].default_value = (0.004, 0.005, 0.008, 1)

    r = sc.render
    r.engine = "CYCLES"
    sc.cycles.device = "GPU"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for kind in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = kind
            prefs.get_devices()
            for d in prefs.devices:
                d.use = d.type == kind
            break
        except Exception:
            continue
    sc.cycles.samples = o["samples"]
    sc.cycles.use_denoising = True
    sc.cycles.volume_step_rate = 1.0
    sc.cycles.volume_max_steps = 512
    sc.cycles.max_bounces = 4; sc.cycles.volume_bounces = 1
    r.film_transparent = True
    r.resolution_x = r.resolution_y = o["px"]
    if o["fmt"] == "exr":
        # Scene-linear premultiplied half floats: fire brighter than its own opacity survives (a straight-alpha PNG
        # clips it to its alpha), and pack.py tone-maps it.
        r.image_settings.file_format = "OPEN_EXR"; r.image_settings.color_mode = "RGBA"
        r.image_settings.color_depth = "16"; r.image_settings.exr_codec = "ZIP"
    else:
        r.image_settings.file_format = "PNG"; r.image_settings.color_mode = "RGBA"; r.image_settings.color_depth = "16"
    sc.view_settings.view_transform = t.get("view", "Standard")
    json.dump({"take": o["take"], "settings": t, "args": o}, open(os.path.join(out, "take.json"), "w"), indent=1,
              default=str)
    only = [int(v) for v in o["only"].split(",") if v] or range(1, o["frames"] + 1)
    for f in only:
        sc.frame_set(f)
        r.filepath = os.path.join(out, f"f_{f:03d}." + ("exr" if o["fmt"] == "exr" else "png"))
        bpy.ops.render.render(write_still=True)
    print("RENDERED", out)


main()
