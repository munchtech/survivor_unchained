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
        burn=0.10, flame_smoke=2.0, dissolve=40, noise=0, noise_k=1.0,
        fuel=2.0, temp=3.0, smoke=0.3, vfac=0.3, out=1.0, vol=1.0, surf=0.1,
        core_r=0.85, core_keys=((1, 0.6, 1.0), (2, 3.0, 1.2), (3, 4.8, 1.4), (4, 6.0, 1.55), (5, 6.6, 1.65)),
        core_off=6, lump=0.9, lump_s=0.55,
        root_r=1.15, root_fuel=((1, 2.0), (6, 1.6), (10, 0.8), (12, 0.3)), root_off=13, root_up=3.0,
        jets=22, jet_long=(3.0, 4.6), jet_short=(1.4, 2.8), jet_r=(0.35, 0.75), jet_t=3, jet_seed=5, jet_fuel=2.0,
        turb=((1, 4.0), (12, 2.5), (30, 1.0), (48, 0.5)), turb_size=1.0,
        ramp=((0, (0, 0, 0)), (0.05, (0.10, 0.008, 0)), (0.2, (0.55, 0.06, 0.005)), (0.45, (1.0, 0.28, 0.02)),
              (0.7, (1.0, 0.52, 0.08)), (0.9, (1.0, 0.70, 0.22)), (1.0, (1.0, 0.80, 0.38))),
        fnoise=0.45, fnoise_s=2.2, flame_pow=1.3, emit_k=1.2,
        smoke_k=12.0, dpow=1.0, smoke_rgb=(0.09, 0.075, 0.062), fmask=(0.12, 0.7, 0.08), zfade=(8.0, 11.5),
        smoke_keys=((1, 1.0), (22, 1.0), (38, 0.4), (47, 0.0)), fire_keys=(),
        amb=0.15, look=4.5, ortho=16.0,
        tone=dict(exp=0.8, knee=0.45, hot=0.0, sat=2.0, amb=(0.030, 0.025, 0.020)),
    ),
    # Seeded round (the jets' starfish and the solid charges' grey blocks gone): a white-hot core from a source half
    # a metre across, swelling to 4.7 m in three frames inside a torn shell of soot 9 m across, its fuel uneven
    # (a clouds texture), so it burns out in patches and tongues; a small source on the ground burns on five frames
    # (0.15 s in the game), the dark stem the rising ball trails. Shaded as a source function (src_material): the
    # fire's light is its own heat's colour, the soot near-black and opaque, the fire seen through it reddened.
    "burns_boom4": dict(
        dom=(13.0, 13.0, 13.0), tscale=4.0, steps_max=4, vort=0.45, flame_vort=1.5, beta=1.5, alpha=0.3,
        burn=0.05, flame_smoke=4.0, dissolve=60, noise=0, noise_k=1.0, sub=0,
        fuel=2.0, temp=3.0, smoke=0.12, vfac=0.0, out=0.0, vol=1.0, surf=0.15,
        ball=True,
        ball_keys=((1, 1.3, 0.65), (2, 1.3, 1.5), (3, 1.3, 2.1), (4, 1.3, 2.4)), core_on=(1, 4), core_up=0.0,
        core_vd=((1, 1.0), (2, 0.75), (3, 0.5), (4, 0.38)),
        core_tex=(0.055, 1.6, 1.1), lump=0.30, lump_s=0.55,
        shell_keys=((1, 1.6, 0.7), (2, 1.6, 2.4), (3, 1.6, 3.5), (4, 1.6, 4.2)), shell_on=(2, 4),
        shell_smoke=0.09, shell_temp=2.0, shell_tex=(0.09, 2.5, 1.0), shell_lump=0.30, shell_up=0.0,
        stem=dict(r=0.32, z=0.35, on=(1, 5), fuel=1.0, temp=2.0, smoke=0.6, up=2.0),
        turb=((1, 3.0), (8, 3.0), (20, 1.5), (36, 0.8)), turb_size=1.2, turb_z=(2.5, 8.0),
        src=True,
        smoke_k=45.0, dpow=1.0, smoke_rgb=(0.05, 0.045, 0.04), absorb=(0.45, 0.25, 0.08),
        flame_k=8.0, fq=1.0, flame_pow=1.0, emit_k=3.5, emit_m=3.0, heat_fire=(0.55, 1.0), heat_w=0.9,
        soot_noise=(0.9, 0.35, 4.0), soot_up=5.0,
        ramp=((0.0, (0.0, 0.0, 0.0)), (0.10, (0.60, 0.04, 0.0)), (0.30, (0.95, 0.13, 0.01)),
              (0.50, (1.0, 0.32, 0.02)), (0.70, (1.0, 0.52, 0.07)), (0.85, (1.0, 0.70, 0.22)),
              (0.93, (1.0, 0.84, 0.48)), (1.0, (1.0, 0.95, 0.80))),
        fnoise=0.3, fnoise_s=2.5, fnoise_up=4.0,
        glow_rgb=(1.0, 0.22, 0.04), glow_k=0.0, glow_heat=(0.5, 1.0),
        heat_keys=((1, 0.25), (4, 0.3), (8, 0.85), (12, 1.0), (20, 0.75), (28, 0.35)),
        zfade=(9.0, 12.5), smoke_keys=((1, 1.0), (26, 1.0), (36, 0.5)), fire_keys=(),
        amb=0.15, look=4.5, ortho=16.0,
        tone=dict(exp=1.0, knee=0.6, hot=0.0, sat=1.0, amb=(0.0, 0.0, 0.0)),
    ),
    # Never one sphere (so never a disc): the blast is a cluster of lumpy puffs flung out of one heart. f1 is the heart
    # alone, white-hot and lumpy, 1.4 m; fire puffs thrown out along even directions, fast then slowing (full size by
    # f5), each its own fuel, so they burn out by turns, in patches; soot puffs riding out on the fire's front a frame
    # behind, patchy, so the fire shows between them and tears through them. In a 15 m box, so the cloud never meets
    # its walls. Shaded as burns_boom4 (src_material), but the fire is the flame alone (the hot gas only a dull ember
    # red, never an orange-lit fog), and burning gas is clear (the soot thick where the fire has died).
    "burns_boom5": dict(
        dom=(15.0, 15.0, 15.0), tscale=4.0, steps_max=4, vort=0.5, flame_vort=2.0, beta=1.4, alpha=0.3,
        burn=0.03, flame_smoke=4.0, dissolve=60, noise=0, noise_k=1.0, sub=3,
        fuel=2.0, temp=3.0, smoke=0.0, vfac=0.0, out=0.0, vol=1.0, surf=0.12,
        burst=True, burst_c=(0.0, 0.0, 1.5),
        heart=dict(keys=((1, 0.62), (2, 0.85), (3, 1.0)), on=(1, 3), fuel=3.6, temp=3.0, smoke=0.0,
                   tex=(0.45, 1.3, 1.0), lump=0.45),
        fp=dict(n=30, seed=11, start=(1, 1), end=(4, 6), d0=(0.15, 0.45), d1=(1.0, 2.1), r0=(0.32, 0.45),
                r1=(0.65, 1.15), zmin=-0.3, fuel=(0.6, 3.8), fuel_pow=2.0, temp=3.0, smoke=(0.08, 0.3), lump=0.45,
                tex=(0.6, 2.2, 1.0), ease=2.0, vfac=0.08, jit=0.25),
        sp=dict(n=22, seed=23, start=(3, 3), end=(5, 7), d1=(3.0, 3.8), d0_rel=(0.75, 0.9), r0=(0.25, 0.35),
                r1=(0.5, 0.95), zmin=-0.45, zmax=0.25, smoke=(0.2, 0.6), temp=1.4, lump=0.5, tex=(0.6, 1.6, 1.0),
                ease=2.0, vfac=0.08, jit=0.3),
        stem=dict(r=0.32, z=0.35, on=(1, 5), fuel=1.0, temp=2.0, smoke=0.6, up=2.0),
        turb=((1, 2.5), (8, 2.0), (20, 1.0), (36, 0.4)), turb_size=1.2, turb_z=(2.5, 10.0), turb_xy=(0.0, 0.0),
        src=True,
        smoke_k=45.0, dpow=1.0, smoke_rgb=(0.04, 0.036, 0.032), absorb=(0.45, 0.25, 0.08),
        flame_k=8.0, fq=1.0, flame_pow=1.0, emit_k=3.5, emit_m=2.5, heat_fire=(0.55, 1.0), heat_w=0.0,
        # The fire's threshold follows its own dying (the bake's flame max: 1.0 to f7, 0.53 at f13, 0.37 at f19), so
        # it shrinks into pockets and tongues edged sharp against the soot, its light raised as it goes (fire_keys).
        fvis=((1, 0.05, 0.3), (5, 0.3, 0.5), (8, 0.45, 0.6), (12, 0.36, 0.48), (16, 0.28, 0.4), (20, 0.22, 0.33),
              (26, 0.2, 0.3)), vmin=0.05,
        fmask=(0.0, 0.0, 0.08), side=(1.6, 0.35),
        soot_noise=(0.9, 0.2, 4.0), soot_up=5.0,
        ramp=((0.0, (0.0, 0.0, 0.0)), (0.10, (0.55, 0.03, 0.0)), (0.30, (0.92, 0.12, 0.01)),
              (0.50, (1.0, 0.30, 0.02)), (0.70, (1.0, 0.50, 0.06)), (0.85, (1.0, 0.70, 0.20)),
              (0.93, (1.0, 0.84, 0.46)), (1.0, (1.0, 0.95, 0.80))),
        fnoise=0.1, fnoise_s=1.4, fnoise_up=4.0,
        glow_rgb=(1.0, 0.22, 0.04), glow_k=0.0, glow_heat=(0.5, 1.0),
        heat_keys=((1, 0.6), (4, 0.6), (10, 1.0), (18, 0.8), (26, 0.35), (34, 0.0)),
        zfade=(8.5, 12.0), smoke_keys=((1, 1.0), (30, 1.0), (36, 0.5), (41, 0.18), (46, 0.0)),
        fire_keys=((1, 1.0), (8, 1.0), (13, 1.8), (17, 2.6), (21, 3.2), (26, 2.0)),
        amb=0.15, look=4.5, ortho=16.0,
        tone=dict(exp=1.0, knee=0.6, hot=0.0, sat=1.0, amb=(0.0, 0.0, 0.0)),
    ),
}

# burns_boom5 with its birth graded (lead 6): the ramp's exponent high to f5, back to 1 by f10, the light kept.
TAKES["burns_boom5b"] = dict(TAKES["burns_boom5"], pow_keys=((1, 1.8), (5, 1.6), (10, 1.0)))
# burns_boom5 with its birth regraded (solver 7): rendered from bake b5's cache rewritten by tools/fxsim/birth.py
# (preset b5c) for f1-f9, its fire lit by the designed heat there (src_material's birth branch), handed back to
# burns_boom5's own shading at f10 (so f10-f48 are b5g's).
TAKES["burns_boom5c"] = dict(TAKES["burns_boom5"], birth=dict(
    keys=((1, 1.0), (9, 1.0), (10, 0.0)), m=3.0, k=2.3, op=((1, 0.55), (5, 0.55), (8, 0.75), (10, 1.0))))
# burns_boom5d (solver 8): birth.py preset b5d's heat read through the birth's own ramp of (T, colour, light), set
# from an in-game calibration (opaque patches at arena night: the atlas's colour after gain, exposure, AgX and grade)
# so the game shows creases ~0.25, rims orange-red ~0.4, a yellow-orange body ~0.65 and a white-yellow core > 0.92;
# its light raised from the fourth frame (the game's exposure dips 38% there), handed back to the bake's own by f10.
TAKES["burns_boom5d"] = dict(TAKES["burns_boom5"], birth=dict(
    keys=((1, 1.0), (6, 1.0), (7, 0.8), (8, 0.55), (9, 0.3), (10, 0.0)), op=((1, 0.55), (5, 0.55), (8, 0.75), (10, 1.0)),
    kk=((1, 1.0), (2, 1.0), (3, 1.15), (4, 1.4), (6, 1.4), (8, 1.2), (9, 1.0)),
    ramp=((0.0, (1.0, 0.05, 0.0), 0.0), (0.30, (1.0, 0.08, 0.005), 0.05), (0.45, (1.0, 0.12, 0.01), 0.15),
          (0.58, (1.0, 0.20, 0.02), 0.26), (0.70, (1.0, 0.33, 0.04), 0.42), (0.80, (1.0, 0.42, 0.06), 0.60),
          (0.88, (1.0, 0.62, 0.20), 1.0), (0.92, (1.0, 0.82, 0.48), 1.6), (0.95, (1.0, 0.97, 0.86), 3.0), (1.0, (1.0, 1.0, 0.95), 4.0))))

# burns_boom5e (solver 9, judge 5a 1b/1c/1e): the whole life from birth.py preset b5e (every frame regraded, so no
# hand-over cut): the birth's ramp of (T, colour, light) as 5d's, the fire's visibility a plain threshold of the
# designed flame, no taper boost; the charred soot lit by the fire still burning near it through the glow (the heat
# grid carries the soot's light where the fire has gone: hg = heat^2 * glow_k).
TAKES["burns_boom5e"] = dict(TAKES["burns_boom5d"], birth=dict(
    TAKES["burns_boom5d"]["birth"], keys=((1, 1.0), (48, 1.0)), kk=((1, 1.0), (48, 1.0)),
    op=((1, 0.55), (5, 0.55), (8, 0.75), (10, 0.9), (48, 0.9))),
    fire_keys=((1, 1.0), (48, 1.0)), fvis=((1, 0.2, 0.45), (48, 0.2, 0.45)), vmin=0.0,
    glow_k=1.0, glow_heat=(0.0, 1.0), glow_rgb=(1.0, 0.45, 0.12), heat_keys=((1, 1.0), (48, 1.0)))


def args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    o = dict(out=a[0], take="burns_boom", res=160, frames=48, px=512, pitch=66.0, samples=48,
             bake_only=False, render_only=False, set="", only="", fmt="exr", vbounce=1, step=1.0, dry=False, cache="",
             stats=False, norender=False)
    i = 1
    while i < len(a):
        k = a[i].lstrip("-").replace("-", "_")
        if k in ("bake_only", "render_only", "dry", "stats", "norender"):
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


def src_material(t):
    """Fire as a source function (Kirchhoff): each point of fire emits its own heat's colour times its own opacity,
    so the light seen at a thick surface is that surface's heat: the hot heart white-yellow, the fire's cooler skin
    deep red, never a flat lit mass. Soot (the sim's density) is near-black (albedo smoke_rgb), opaque where dense,
    reddening the fire seen through it (absorb: red passes, blue is taken); its own heat a dull red glow that cools
    on heat_keys. Fire: flame^fq * flame_k of neutral opacity; light ramp(flame^flame_pow) * emit_k * fp^emit_m."""
    m = bpy.data.materials.new("boom_src")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    L = nt.links.new

    def math(op, a, b=None, c=None, clamp=False):
        n = nt.nodes.new("ShaderNodeMath"); n.operation = op; n.use_clamp = clamp
        for i, v in enumerate((a, b, c)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                L(v, n.inputs[i])
        return n.outputs["Value"]

    def attr(name):
        a = nt.nodes.new("ShaderNodeAttribute"); a.attribute_name = name
        return a.outputs["Fac"]

    def scale(vec, s):
        n = nt.nodes.new("ShaderNodeVectorMath"); n.operation = "SCALE"
        L(vec, n.inputs[0]); L(s, n.inputs["Scale"])
        return n.outputs["Vector"]

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    zf = None
    if t.get("zfade"):
        geo = nt.nodes.new("ShaderNodeNewGeometry"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        mr = nt.nodes.new("ShaderNodeMapRange"); mr.clamp = True
        mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = t["zfade"]
        mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = 1.0, 0.0
        L(geo.outputs["Position"], sep.inputs[0]); L(sep.outputs["Z"], mr.inputs["Value"])
        zf = mr.outputs["Result"]
    if t.get("side"):
        # A guard at the domain's side walls: all of it thinned to nothing over the last side[0] m before a wall
        # (side[1] m short of it), so no straight cut can ever show.
        geo = nt.nodes.new("ShaderNodeNewGeometry"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        L(geo.outputs["Position"], sep.inputs[0])
        w0, w1 = t["side"]
        sf = None
        for ax, half in (("X", t["dom"][0] / 2), ("Y", t["dom"][1] / 2)):
            mr = nt.nodes.new("ShaderNodeMapRange"); mr.clamp = True
            mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = half - w0 - w1, half - w1
            mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = 1.0, 0.0
            L(math("ABSOLUTE", sep.outputs[ax]), mr.inputs["Value"])
            sf = mr.outputs["Result"] if sf is None else math("MULTIPLY", sf, mr.outputs["Result"])
        zf = sf if zf is None else math("MULTIPLY", zf, sf)
    # Soot.
    tap = keyed(nt, "smoke_taper", t.get("smoke_keys", ()), 1.0).outputs[0]
    ds = math("MULTIPLY", math("POWER", attr("density"), t.get("dpow", 1.0)), t["smoke_k"])
    ds = math("MULTIPLY", ds, tap)
    if zf:
        ds = math("MULTIPLY", ds, zf)
    if t.get("soot_noise"):
        # Torn soot: holes in it where a climbing noise is low (the sim's shell is even), so the fire shows
        # through in tears and the soot lies in rags, thick in its pockets.
        sc_, th, gain = t["soot_noise"]
        tc2 = nt.nodes.new("ShaderNodeTexCoord"); mp2 = nt.nodes.new("ShaderNodeMapping")
        nz2 = nt.nodes.new("ShaderNodeTexNoise"); nz2.inputs["Scale"].default_value = sc_
        nz2.inputs["Detail"].default_value = 6.0; nz2.inputs["Roughness"].default_value = 0.62
        L(tc2.outputs["Object"], mp2.inputs["Vector"]); L(mp2.outputs["Vector"], nz2.inputs["Vector"])
        l2 = mp2.inputs["Location"]
        l2.default_value = (0, 0, 0); l2.keyframe_insert("default_value", frame=1)
        l2.default_value = (0.3, 0, -t.get("soot_up", 5.0)); l2.keyframe_insert("default_value", frame=33)
        mk = math("MULTIPLY", math("SUBTRACT", nz2.outputs["Fac"], th), gain, clamp=True)
        ds = math("MULTIPLY", ds, mk)
    # Fire: the flame broken finer than the grid by a noise that climbs with it.
    f = attr("flame")
    if t.get("fnoise", 0.0) > 0:
        tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
        nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = t.get("fnoise_s", 2.5)
        nz.inputs["Detail"].default_value = 4.0; nz.inputs["Roughness"].default_value = 0.6
        L(tc.outputs["Object"], mp.inputs["Vector"]); L(mp.outputs["Vector"], nz.inputs["Vector"])
        loc = mp.inputs["Location"]
        loc.default_value = (0, 0, 0); loc.keyframe_insert("default_value", frame=1)
        loc.default_value = (0, 0, -t.get("fnoise_up", 4.0)); loc.keyframe_insert("default_value", frame=49)
        ma = nt.nodes.new("ShaderNodeMath"); ma.operation = "MULTIPLY_ADD"
        L(nz.outputs["Fac"], ma.inputs[0])
        ma.inputs[1].default_value = 2.0 * t["fnoise"]; ma.inputs[2].default_value = 1.0 - t["fnoise"]
        f = math("MULTIPLY", f, ma.outputs["Value"], clamp=True)
    vis = vmod = None
    if t.get("fvis"):
        # The fire seen only where it burns hot enough: a smoothstep of the broken flame from lo to hi (keyed, as
        # fvis = ((frame, lo, hi), ...)), the fire below it kept at vmin of itself (a dull red under the soot). The
        # burnt-out gas is soot, so the fire shrinks into pockets as it dies, edged sharp against black.
        ks = t["fvis"]
        lo = keyed(nt, "fvis_lo", [(k[0], k[1]) for k in ks], ks[0][1]).outputs[0]
        hi = keyed(nt, "fvis_hi", [(k[0], k[2]) for k in ks], ks[0][2]).outputs[0]
        vr = nt.nodes.new("ShaderNodeMapRange"); vr.clamp = True; vr.interpolation_type = "SMOOTHSTEP"
        L(f, vr.inputs["Value"]); L(lo, vr.inputs["From Min"]); L(hi, vr.inputs["From Max"])
        vr.inputs["To Min"].default_value, vr.inputs["To Max"].default_value = 0.0, 1.0
        vis = vr.outputs["Result"]
        vmin = t.get("vmin", 0.15)
        vmod = math("MULTIPLY_ADD", vis, 1.0 - vmin, vmin)
        f = math("MULTIPLY", f, vmod)
    if t.get("fmask"):
        # Burning gas is clear: the soot thinned where the fire burns (to fmask[2] of itself), so the fire shows
        # where it burns at the cloud's skin and the soot lies thick where the fire has died. With fvis, the fire's
        # own visibility; else the raw flame mapped from fmask[0] to fmask[1].
        fm0, fm1, fmin = t["fmask"]
        if vis is not None:
            ds = math("MULTIPLY", ds, math("MULTIPLY_ADD", vis, fmin - 1.0, 1.0))
        else:
            fmr = nt.nodes.new("ShaderNodeMapRange"); fmr.clamp = True
            fmr.inputs["From Min"].default_value, fmr.inputs["From Max"].default_value = fm0, fm1
            fmr.inputs["To Min"].default_value, fmr.inputs["To Max"].default_value = 1.0, fmin
            L(attr("flame"), fmr.inputs["Value"])
            ds = math("MULTIPLY", ds, fmr.outputs["Result"])
    if t.get("heat_fire"):
        # Hot gas is fire too: its heat (the sim's buoyancy temperature, which outlives the flame) mapped to the
        # same scale, cooling on heat_keys, so burnt-out gas keeps a deep red glow and the fire dies as it cools.
        a0, a1 = t["heat_fire"]
        hf = nt.nodes.new("ShaderNodeMapRange"); hf.clamp = True
        hf.inputs["From Min"].default_value, hf.inputs["From Max"].default_value = a0, a1
        L(attr(t.get("heat_attr", "heat")), hf.inputs["Value"])
        hc = keyed(nt, "heat_cool_f", t.get("heat_keys", ()), 1.0).outputs[0]
        hw = math("MULTIPLY", math("MULTIPLY", hf.outputs["Result"], hc), t.get("heat_w", 0.8))
        if t.get("heat_cap"):
            hw = math("MINIMUM", hw, t["heat_cap"])  # hot gas only an ember red, never the fire's orange
        f = math("MAXIMUM", f, hw)
    ff = math("MULTIPLY", math("POWER", f, t.get("fq", 1.0)), t["flame_k"])
    if zf:
        ff = math("MULTIPLY", ff, zf)
    # pow_keys: the ramp's exponent keyed over frames (burns_boom5b: its birth read as a cream blob in the game; high
    # for f1-f5, only the densest heart reaches white, the rest burns yellow to orange).
    fp = math("POWER", f, t.get("flame_pow", 1.0))
    # (Only the colour: the light stays the flame's.)
    fpr = math("POWER", f, keyed(nt, "pow_f", t["pow_keys"], 1.0).outputs[0]) if t.get("pow_keys") else fp
    bw = None
    if t.get("birth"):
        # The birth (a cache regraded by tools/fxsim/birth.py): the fire's colour and light from its designed heat T
        # (the cache's temperature, read as `heat`), not the saturated flame: lobes hot, creases and limbs cooler, a
        # small white heart. Keyed in by w (1 through the birth, 0 after it, where the bake's own heat is back), T
        # dimmed with the fire's visibility (so it dies into pockets as the flame does), the fire semi-clear (op),
        # so each lobe's limb is seen through its own cooler skin.
        b = t["birth"]
        bw = keyed(nt, "birth_w", b["keys"], 0.0).outputs[0]
        T = attr("heat")
        if vmod is not None:
            T = math("MULTIPLY", T, vmod)
        fpr = math("MULTIPLY_ADD", math("SUBTRACT", T, fpr), bw, fpr)
        b_inten = math("MULTIPLY", math("POWER", T, b.get("m", 3.0)), b.get("k", 2.3))
        op = keyed(nt, "birth_op", b.get("op", ((1, 1.0),)), 1.0).outputs[0]
        ff = math("MULTIPLY", ff, math("MULTIPLY_ADD", math("SUBTRACT", op, 1.0), bw, 1.0))
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    rk = t["ramp"]
    cr.elements[0].position = rk[0][0]; cr.elements[0].color = tuple(rk[0][1]) + (1,)
    cr.elements[1].position = rk[-1][0]; cr.elements[1].color = tuple(rk[-1][1]) + (1,)
    for p, c in rk[1:-1]:
        e = cr.elements.new(p); e.color = tuple(c) + (1,)
    L(fpr, ramp.inputs["Fac"])
    col = ramp.outputs["Color"]
    inten = math("MULTIPLY", math("POWER", fp, t.get("emit_m", 2.0)), t["emit_k"])
    if bw is not None and b.get("ramp"):
        # The birth's own light (burns_boom5d): its heat T read through a ramp of (T, colour, light), the colour mixed
        # with the bake's own by w and the light keyed by `kk` (the game's exposure dips 38% from its fourth frame).
        rb = nt.nodes.new("ShaderNodeValToRGB"); rl = nt.nodes.new("ShaderNodeValToRGB")
        rk2 = b["ramp"]; top = max(s[2] for s in rk2)
        for r_, stops in ((rb, [(s[0], tuple(s[1])) for s in rk2]), (rl, [(s[0], (s[2] / top,) * 3) for s in rk2])):
            cr2 = r_.color_ramp
            cr2.elements[0].position = stops[0][0]; cr2.elements[0].color = stops[0][1] + (1,)
            cr2.elements[1].position = stops[-1][0]; cr2.elements[1].color = stops[-1][1] + (1,)
            for p_, c_ in stops[1:-1]:
                e = cr2.elements.new(p_); e.color = c_ + (1,)
            L(T, r_.inputs["Fac"])
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"
        L(bw, mx.inputs["Factor"]); L(col, mx.inputs[6]); L(rb.outputs["Color"], mx.inputs[7])
        col = mx.outputs[2]
        kk = keyed(nt, "birth_kk", b.get("kk", ((1, 1.0),)), 1.0).outputs[0]
        b_inten = math("MULTIPLY", math("MULTIPLY", rl.outputs["Color"], top), kk)
    if bw is not None:
        inten = math("MULTIPLY_ADD", math("SUBTRACT", b_inten, inten), bw, inten)
    if t.get("fire_keys"):
        inten = math("MULTIPLY", inten, keyed(nt, "fire_taper", t["fire_keys"], 1.0).outputs[0])
    fire_rgb = scale(col, math("MULTIPLY", ff, inten))
    # The soot's own heat: a dull red where the fire has warmed it, cooling on heat_keys.
    h0, h1 = t.get("glow_heat", (1.6, 3.0))
    hm = nt.nodes.new("ShaderNodeMapRange"); hm.clamp = True
    hm.inputs["From Min"].default_value, hm.inputs["From Max"].default_value = h0, h1
    L(attr(t.get("heat_attr", "heat")), hm.inputs["Value"])
    cool = keyed(nt, "heat_cool", t.get("heat_keys", ()), 1.0).outputs[0]
    hg = math("MULTIPLY", math("MULTIPLY", math("POWER", hm.outputs["Result"], 2.0), t.get("glow_k", 0.8)), cool)
    gc = nt.nodes.new("ShaderNodeRGB"); gc.outputs[0].default_value = tuple(t.get("glow_rgb", (1, 0.22, 0.04))) + (1,)
    glow_rgb = scale(gc.outputs[0], math("MULTIPLY", ds, hg))

    pv = nt.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Color"].default_value = tuple(t.get("smoke_rgb", (0.05, 0.045, 0.04))) + (1,)
    pv.inputs["Absorption Color"].default_value = tuple(t.get("absorb", (0.0, 0.0, 0.0))) + (1,)
    pv.inputs["Anisotropy"].default_value = 0.3
    pv.inputs["Density Attribute"].default_value = ""
    pv.inputs["Blackbody Intensity"].default_value = 0.0
    pv.inputs["Emission Strength"].default_value = 1.0
    L(ds, pv.inputs["Density"]); L(glow_rgb, pv.inputs["Emission Color"])
    ab = nt.nodes.new("ShaderNodeVolumeAbsorption"); ab.inputs["Color"].default_value = (0, 0, 0, 1)
    L(ff, ab.inputs["Density"])
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 1.0
    L(fire_rgb, em.inputs["Color"])
    a1 = nt.nodes.new("ShaderNodeAddShader"); a2 = nt.nodes.new("ShaderNodeAddShader")
    L(pv.outputs["Volume"], a1.inputs[0]); L(ab.outputs["Volume"], a1.inputs[1])
    L(a1.outputs[0], a2.inputs[0]); L(em.outputs["Emission"], a2.inputs[1])
    L(a2.outputs[0], out.inputs["Volume"])
    return m


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
        dens = dt.outputs["Value"]
        if t.get("fmask"):
            # Burning gas is clear and bright; the smoke is what the fire leaves: masked out where the flame is hot.
            fa = nt.nodes.new("ShaderNodeAttribute"); fa.attribute_name = "flame"
            fr_ = nt.nodes.new("ShaderNodeMapRange"); fr_.clamp = True
            fr_.inputs["From Min"].default_value, fr_.inputs["From Max"].default_value = t["fmask"][:2]
            fr_.inputs["To Min"].default_value, fr_.inputs["To Max"].default_value = 1.0, t["fmask"][2]
            fmm = nt.nodes.new("ShaderNodeMath"); fmm.operation = "MULTIPLY"
            nt.links.new(fa.outputs["Fac"], fr_.inputs["Value"])
            nt.links.new(dens, fmm.inputs[0]); nt.links.new(fr_.outputs["Result"], fmm.inputs[1])
            dens = fmm.outputs["Value"]
        if t.get("zfade"):
            # The smoke thins as it climbs, gone by zfade[1] m: no cap over the field, no cut at the domain's lid.
            geo = nt.nodes.new("ShaderNodeNewGeometry"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
            mr = nt.nodes.new("ShaderNodeMapRange"); mr.clamp = True
            mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = t["zfade"]
            mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = 1.0, 0.0
            zm = nt.nodes.new("ShaderNodeMath"); zm.operation = "MULTIPLY"
            nt.links.new(geo.outputs["Position"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
            nt.links.new(dens, zm.inputs[0]); nt.links.new(mr.outputs["Result"], zm.inputs[1])
            dens = zm.outputs["Value"]
        nt.links.new(dens, pv.inputs["Density"])
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
    ramp_k = t.get("ramp", ((0.0, (0, 0, 0)), (0.06, (0.12, 0.01, 0.0)), (0.25, (0.75, 0.1, 0.008)),
                            (0.55, (1.0, 0.4, 0.04)), (0.82, (1.0, 0.72, 0.28)), (1.0, (1.0, 0.9, 0.7))))
    cr.elements[0].position = ramp_k[0][0]; cr.elements[0].color = tuple(ramp_k[0][1]) + (1,)
    cr.elements[1].position = ramp_k[-1][0]; cr.elements[1].color = tuple(ramp_k[-1][1]) + (1,)
    for p, c in ramp_k[1:-1]:
        e = cr.elements.new(p); e.color = tuple(c) + (1,)
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
        k, v = kv.split("=", 1)
        d_ = t
        if "." in k:  # a nested setting: "fp.n=30"
            k0, k = k.split(".", 1)
            d_ = t[k0] = dict(t[k0])
        d_[k] = type(d_[k])(v) if k in d_ and isinstance(d_[k], (int, float, str)) and not isinstance(d_[k], bool) \
            else eval(v)
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
    dom.data.materials.append(src_material(t) if t.get("src") else flame_material(t))

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
               fuel_keys=(), kind="BOTH", tex=None, sub=8, vd_keys=()):
        """A solid flow (it fills its volume, not a shell) of fuel, heat and smoke, on for frames on[0]..on[1];
        keys: (frame, location, scale), linear, so a punch starts at full speed. tex (scale, contrast, brightness):
        a clouds texture over its emission (fuel and smoke, not heat), fixed to the object, so it burns unevenly."""
        obj.name = name
        f = obj.modifiers.new("Fluid", "FLUID"); f.fluid_type = "FLOW"
        fs = f.flow_settings
        fs.flow_type = kind; fs.flow_behavior = "INFLOW"; fs.flow_source = "MESH"
        if hasattr(fs, "use_absolute"):
            fs.use_absolute = True  # fuel and smoke set to the emitter's value, never piled up step on step
        if tex:
            tx = bpy.data.textures.new(name + "_tex", "CLOUDS")
            tx.noise_scale, tx.contrast, tx.intensity = tex; tx.noise_depth = 3
            fs.use_texture = True; fs.noise_texture = tx; fs.texture_map_type = "AUTO"; fs.texture_size = 1.0
        fs.surface_distance = t.get("surf", 0.1); fs.volume_density = t.get("vol", 1.0); fs.subframes = sub
        fs.fuel_amount = fuel; fs.temperature = temp; fs.density = smoke
        fs.smoke_color = (0.06, 0.05, 0.045)
        fs.use_initial_velocity = True
        fs.velocity_factor = vfac; fs.velocity_normal = normal
        if vcoord:
            fs.velocity_coord = vcoord
        a, b = on
        for fr, v in ((1, a <= 1), (a, True), (b, True), (b + 1, False)):
            fs.use_inflow = v; fs.keyframe_insert("use_inflow", frame=fr)
        for fr, v in vd_keys:
            fs.volume_density = v; fs.keyframe_insert("volume_density", frame=fr)
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
    if t.get("ball"):
        # The core: fire swelling out of a source half a metre across to full size in three frames, its fuel
        # uneven. It burns out where the fuel was thin first, so the fire breaks into patches and tongues.
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=1.0, location=(0, 0, 0.9))
        c = bpy.context.object
        lumpy(c, t["lump"])
        charge("core", c, t["core_on"], [(fr, (0, 0, z), (r, r, r)) for fr, z, r in t["ball_keys"]],
               t["fuel"], t["temp"], t["smoke"], vcoord=(0.0, 0.0, t.get("core_up", 0.0)), tex=t.get("core_tex"),
               sub=t.get("sub", 8), vd_keys=t.get("core_vd", ()))
        # The shell: soot thrown round it a frame later, torn (a clouds texture), cooler, so the fire shows through
        # its holes and glows red through its thin parts, dark at its rims.
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=1.0, location=(0, 0, 0.9))
        sh = bpy.context.object
        lumpy(sh, t["shell_lump"])
        charge("shell", sh, t["shell_on"], [(fr, (0, 0, z), (r, r, r)) for fr, z, r in t["shell_keys"]],
               0.0, t["shell_temp"], t["shell_smoke"], vcoord=(0.0, 0.0, t.get("shell_up", 0.0)), kind="SMOKE",
               tex=t.get("shell_tex"), sub=t.get("sub", 8))
        # The stem: the crater burning on, smoke and a little fuel thrown up into the ball.
        st = t["stem"]
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0, location=(0, 0, st["z"]))
        sm = bpy.context.object
        charge("stem", sm, st["on"], [(1, (0, 0, st["z"]), (st["r"],) * 3)], st["fuel"], st["temp"], st["smoke"],
               vcoord=(0.0, 0.0, st["up"]), sub=t.get("sub", 8))
        if t.get("turb"):
            bpy.ops.object.effector_add(type="TURBULENCE", location=(0, 0, 2.0))
            tb = bpy.context.object
            tb.field.size = t.get("turb_size", 1.0); tb.field.flow = 0.0; tb.field.noise = 0.0
            for fr, v in t["turb"]:
                tb.field.strength = v; tb.field.keyframe_insert("strength", frame=fr)
            z0, z1 = t.get("turb_z", (2.0, 8.0))
            tb.location = (0, 0, z0); tb.keyframe_insert("location", frame=1)
            tb.location = (0.4, -0.3, z1); tb.keyframe_insert("location", frame=o["frames"])
    if t.get("burst"):
        cx, cy, cz = t["burst_c"]

        def spiral(n, zmin, seed, jit, zmax=1.0):
            """n directions spread evenly over the sphere's band zmin..zmax (a jittered Fibonacci spiral), shuffled."""
            r = random.Random(seed)
            m = max(n, int(round(n * 2.0 / (zmax - zmin))))
            ga = math.pi * (3.0 - math.sqrt(5.0))
            out_ = []
            for k in range(m):
                z = 1.0 - 2.0 * (k + 0.5) / m
                if z < zmin or z > zmax:
                    continue
                rr = math.sqrt(max(0.0, 1.0 - z * z)); th = k * ga
                v = [rr * math.cos(th) + r.uniform(-jit, jit), rr * math.sin(th) + r.uniform(-jit, jit),
                     z + r.uniform(-jit, jit)]
                ln = math.sqrt(sum(c * c for c in v)) or 1.0
                out_.append(tuple(c / ln for c in v))
            r.shuffle(out_)
            return out_[:n]

        def fling(prefix, p, kind):
            """Puffs flung out from the heart along spiral() directions: from d0 to d1 m (or born at d0_rel of d1,
            on the front), radius r0 to r1, eased out (fast, then slowing), on from a frame in p["start"] to one in
            p["end"]; each lumpy, its emission broken by its own clouds."""
            r = random.Random(p["seed"] + 1)
            for i, dv in enumerate(spiral(p["n"], p["zmin"], p["seed"], p.get("jit", 0.25), p.get("zmax", 1.0))):
                a = r.randint(*p["start"]); b = max(r.randint(*p["end"]), a + 1)
                d1 = r.uniform(*p["d1"])
                d0 = d1 * r.uniform(*p["d0_rel"]) if p.get("d0_rel") else r.uniform(*p["d0"])
                r0_, r1_ = r.uniform(*p["r0"]), r.uniform(*p["r1"])
                keys = []
                for fr in range(a, b + 1):
                    e = 1.0 - (1.0 - (fr - a) / (b - a)) ** p.get("ease", 2.0)
                    d = d0 + (d1 - d0) * e; rad = r0_ + (r1_ - r0_) * e
                    keys.append((fr, (cx + dv[0] * d, cy + dv[1] * d, max(cz + dv[2] * d, 0.3)), (rad, rad, rad)))
                bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0, location=keys[0][1])
                ob = bpy.context.object
                lumpy(ob, p["lump"])
                if kind == "fire":
                    # Fuel skewed low (fuel_pow > 1): most puffs burn out early, a few rich ones burn on in pockets.
                    fu = p["fuel"][0] + (p["fuel"][1] - p["fuel"][0]) * r.random() ** p.get("fuel_pow", 1.0)
                    smk = p.get("smoke", 0.0)
                    smk = r.uniform(*smk) if isinstance(smk, (tuple, list)) else smk
                    charge(f"{prefix}{i}", ob, (a, b), keys, fu, p["temp"], smk,
                           vfac=p.get("vfac", 0.0), tex=p.get("tex"), sub=t.get("sub", 3))
                else:
                    charge(f"{prefix}{i}", ob, (a, b), keys, 0.0, p["temp"], r.uniform(*p["smoke"]),
                           vfac=p.get("vfac", 0.0), kind="SMOKE", tex=p.get("tex"), sub=t.get("sub", 3))
                fs_ = ob.modifiers["Fluid"].flow_settings
                if fs_.use_texture:
                    fs_.texture_offset = r.uniform(0.0, 10.0)  # each puff its own pattern

        # The heart: white-hot and lumpy on f1, swelling as the puffs leave it.
        hp = t["heart"]
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1.0, location=(cx, cy, cz))
        hb = bpy.context.object
        lumpy(hb, hp["lump"])
        charge("heart", hb, hp["on"], [(fr, (cx, cy, cz), (k, k, k)) for fr, k in hp["keys"]], hp["fuel"],
               hp["temp"], hp["smoke"], tex=hp.get("tex"), sub=t.get("sub", 3))
        fling("fire", t["fp"], "fire")
        fling("soot", t["sp"], "soot")
        st = t["stem"]
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0, location=(0, 0, st["z"]))
        sm = bpy.context.object
        charge("stem", sm, st["on"], [(1, (0, 0, st["z"]), (st["r"],) * 3)], st["fuel"], st["temp"], st["smoke"],
               vcoord=(0.0, 0.0, st["up"]), sub=t.get("sub", 3))
        if t.get("turb"):
            bpy.ops.object.effector_add(type="TURBULENCE", location=(0, 0, 2.0))
            tb = bpy.context.object
            tb.field.size = t.get("turb_size", 1.0); tb.field.flow = 0.0; tb.field.noise = 0.0
            for fr, v in t["turb"]:
                tb.field.strength = v; tb.field.keyframe_insert("strength", frame=fr)
            z0, z1 = t.get("turb_z", (2.0, 8.0))
            tx_, ty_ = t.get("turb_xy", (0.0, 0.0))
            tb.location = (0, 0, z0); tb.keyframe_insert("location", frame=1)
            tb.location = (tx_, ty_, z1); tb.keyframe_insert("location", frame=o["frames"])
    r0 = t.get("emit_r", 0.7)
    top = t.get("top", 7.0)
    if t.get("core_keys") or t.get("ball") or t.get("burst"):
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
    if t.get("skirt") and not t.get("particles") and not t.get("core_keys") and not t.get("burst"):
        # The skirt: a flat ring at the ground spreading fast, throwing flame outward along it.
        bpy.ops.mesh.primitive_torus_add(major_radius=r0 * 1.2, minor_radius=0.22, location=(0, 0, 0.25))
        sk = t["skirt_to"]
        emitter("skirt", bpy.context.object, 2.0, t["skirt_burst"],
                [(1, (0, 0, 0.25), (1, 1, 1)), (t["skirt_burst"][1], (0, 0, 0.3), (sk, sk, 1))])

    # Last: changing any domain setting after this frees (deletes) the baked cache, so a render-only run would
    # find it gone.
    ds.cache_directory = os.path.abspath(o["cache"]) if o["cache"] else os.path.join(out, "cache")
    if o["dry"]:
        for ob in sc.objects:
            if "Fluid" in ob.modifiers and ob.modifiers["Fluid"].fluid_type == "FLOW":
                fs = ob.modifiers["Fluid"].flow_settings
                print("FLOW", ob.name, fs.flow_type, "fuel", fs.fuel_amount, "smoke", fs.density, "temp", fs.temperature,
                      "tex", fs.use_texture, "abs", fs.use_absolute, "vel", tuple(fs.velocity_coord))
        print("DRY", len(sc.objects), "objects")
        return
    if not o["render_only"]:
        with bpy.context.temp_override(object=dom, active_object=dom, selected_objects=[dom], scene=sc):
            bpy.ops.fluid.bake_all()
        print("BAKED", ds.cache_directory)
    if o["bake_only"]:
        return
    if o["stats"]:
        # The bake's numbers per frame: the fire (flame > 0.25) and the soot (dense enough to see: density *
        # smoke_k > 1 per m), their extent in metres, and how near the soot comes to the side walls.
        import numpy as np
        dg = bpy.context.evaluated_depsgraph_get()
        for f in range(1, o["frames"] + 1):
            sc.frame_set(f)
            ev = dom.evaluated_get(bpy.context.evaluated_depsgraph_get()).modifiers["Fluid"].domain_settings
            res = [int(v) for v in ev.domain_resolution]
            n = res[0] * res[1] * res[2]
            h = max(W, D, H) / max(res)

            def grid(p):
                a = np.empty(n, np.float32)
                try:
                    p.foreach_get(a)
                except Exception:
                    a = np.array(p, np.float32)
                return a.reshape(res[2], res[1], res[0]) if a.size == n else None
            dn, fl, ht = grid(ev.density_grid), grid(ev.flame_grid), grid(ev.heat_grid)
            if dn is None:
                print("STAT", f, "no grid"); continue

            def ext(m):
                if not m.any():
                    return "-"
                zz, yy, xx = [np.nonzero(m.any(axis=tuple(j for j in range(3) if j != ax)))[0] for ax in range(3)]
                return "x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f" % (
                    xx[0] * h - W / 2, (xx[-1] + 1) * h - W / 2, yy[0] * h - D / 2, (yy[-1] + 1) * h - D / 2,
                    zz[0] * h, (zz[-1] + 1) * h)
            soot = dn * t.get("smoke_k", 30.0) > 1.0
            fire = fl > 0.25
            k = max(1, int(0.6 / h))
            wall = max(float(dn[:, :, :k].max()), float(dn[:, :, -k:].max()), float(dn[:, :k, :].max()),
                       float(dn[:, -k:, :].max())) * t.get("smoke_k", 30.0)
            print("STAT f%02d" % f, "flame max %.2f vol %.1f m3 [%s]" % (fl.max(), fire.sum() * h ** 3, ext(fire)),
                  "| soot vol %.1f m3 [%s] dmax %.2f" % (soot.sum() * h ** 3, ext(soot), dn.max()),
                  "| heat max %.2f mean(soot) %.2f" % (ht.max(), ht[soot].mean() if soot.any() else 0),
                  "| wall %.2f/m" % wall, flush=True)
    if o["norender"]:
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
    sc.cycles.volume_step_rate = o["step"]
    sc.cycles.denoiser = "OPENIMAGEDENOISE"; sc.cycles.denoising_input_passes = "RGB_ALBEDO_NORMAL"
    sc.cycles.denoising_prefilter = "ACCURATE"
    sc.cycles.volume_max_steps = 512
    sc.cycles.max_bounces = 4; sc.cycles.volume_bounces = o["vbounce"]
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
