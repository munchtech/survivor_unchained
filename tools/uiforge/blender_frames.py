"""Forged frames modelled and rendered in Blender (Cycles), from a JSON spec.

    blender -b -P tools/uiforge/blender_frames.py -- spec.json out.png

The spec describes one frame in FILE pixels (y down), at its exact nine-slice
layout, so the render is the file: no fitting distorts it.

    {"size": [W, H], "ss": 2, "margins": [l, t, r, b],        # file px
     "strap": {"inset": 0, "width": 30, "thick": 8, "bevel": 3, "chamfer": 10, "radius": 0,
               "rough": 0.45, "color": "#2a2630", "hammer": 1.0, "tint": [1,1,1]},
     "panel": {"inset": 20, "color": "#16131a", "depth": 3} | null,
     "wire":  {"offset": 16, "radius": 2.2, "pitch": 7, "color": "#d9b56a"} | null,
     "coins": [{"x": 20, "y": 20, "size": 40, "hole": 0.3, "ember": 1.0, "rot": 45}],
     "rivets": [{"x": 50, "y": 15, "r": 4}],
     "scrolls": [{"pts": [[x, y], ...], "w0": 9, "w1": 3, "thick": 5}],
     "seam": {"offset": 32, "strength": 0.0, "color": "#ff8a3a"},
     "world": "night"}

Textures are periodic over the middle of each side (the space between the
margins), so the frame repeats there (UiArt Tile) without a seam.
"""
import json
import math
import os
import sys

import bpy
import bmesh
from mathutils import Vector

U = 0.01  # Blender units per file pixel


def hexc(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


def P(x, y, W, H, z=0.0):
    """File pixel (y down) to Blender (centred, y up)."""
    return Vector(((x - W / 2) * U, (H / 2 - y) * U, z * U))


# ----------------------------------------------------------------- scene --

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 96
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
    sc.render.film_transparent = True
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.image_settings.color_depth = "16"
    return sc


def world(kind="night"):
    """A dark room with a big warm softbox up and to the left and a cool strip low right:
    what the metal reflects, so bevels shine and flats stay dark, the same everywhere."""
    w = bpy.data.worlds.new("w")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nodes, links = nt.nodes, nt.links
    bg = nodes["Background"]
    tc = nodes.new("ShaderNodeTexCoord")
    key = Vector((-0.6, 0.67, 0.30)).normalized()
    rim = Vector((0.7, -0.62, 0.35)).normalized()

    # Sum of lobes as a colour: key*warm*s + rim*cool*s + base.
    def lobe_rgb(direction, power, color, strength):
        dot = nodes.new("ShaderNodeVectorMath")
        dot.operation = "DOT_PRODUCT"
        dot.inputs[1].default_value = direction
        links.new(tc.outputs["Generated"], dot.inputs[0])
        cl = nodes.new("ShaderNodeMath")
        cl.operation = "MAXIMUM"
        cl.inputs[1].default_value = 0.0
        links.new(dot.outputs["Value"], cl.inputs[0])
        pw = nodes.new("ShaderNodeMath")
        pw.operation = "POWER"
        pw.inputs[1].default_value = power
        links.new(cl.outputs[0], pw.inputs[0])
        sc = nodes.new("ShaderNodeMath")
        sc.operation = "MULTIPLY"
        sc.inputs[1].default_value = strength
        links.new(pw.outputs[0], sc.inputs[0])
        mix = nodes.new("ShaderNodeVectorMath")
        mix.operation = "SCALE"
        mix.inputs[0].default_value = color[:3]
        links.new(sc.outputs[0], mix.inputs["Scale"])
        return mix

    a = lobe_rgb(key, 6.0, hexc("#ffe8cc"), 6.0)
    b = lobe_rgb(rim, 14.0, hexc("#b8c4ff"), 2.5)
    up = lobe_rgb(Vector((0, 0.2, 1)).normalized(), 3.0, hexc("#c8ccff"), 0.05)
    add1 = nodes.new("ShaderNodeVectorMath")
    add1.operation = "ADD"
    links.new(a.outputs[0], add1.inputs[0])
    links.new(b.outputs[0], add1.inputs[1])
    add2 = nodes.new("ShaderNodeVectorMath")
    add2.operation = "ADD"
    links.new(add1.outputs[0], add2.inputs[0])
    links.new(up.outputs[0], add2.inputs[1])
    links.new(add2.outputs[0], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 1.0


def suns():
    def sun(name, direction, energy, color, angle):
        d = bpy.data.lights.new(name, "SUN")
        d.energy = energy
        d.color = color[:3]
        d.angle = math.radians(angle)
        o = bpy.data.objects.new(name, d)
        bpy.context.scene.collection.objects.link(o)
        o.rotation_euler = (-Vector(direction)).to_track_quat("-Z", "Y").to_euler()
    sun("key", (-0.62, 0.62, 0.48), 3.2, hexc("#ffe2c0"), 12)
    sun("fill", (0.2, 0.35, 1.0), 0.35, hexc("#c8d0ff"), 30)
    sun("rim", (0.7, -0.7, 0.25), 0.8, hexc("#a8b8ff"), 8)


def camera(W, H):
    cam_d = bpy.data.cameras.new("cam")
    cam_d.type = "ORTHO"
    cam_d.ortho_scale = max(W, H) * U
    cam = bpy.data.objects.new("cam", cam_d)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (0, 0, 10)
    bpy.context.scene.camera = cam
    sc = bpy.context.scene
    sc.render.resolution_x = W
    sc.render.resolution_y = H
    sc.render.resolution_percentage = 100


# -------------------------------------------------------------- textures --

def periodic_coords(nt, W, H, margins, period_scale=1.0):
    """A 4D point on a torus for each surface point: periodic in x over the middle
    width and in y over the middle height (file px), so the textures repeat there."""
    l, t, r, b = margins
    Pw, Ph = W - l - r, H - t - b
    n, k = nt.nodes, nt.links
    tc = n.new("ShaderNodeTexCoord")
    sep = n.new("ShaderNodeSeparateXYZ")
    k.new(tc.outputs["Object"], sep.inputs[0])

    def angle(comp, centre_px, period_px, origin_px, flip):
        # x_px = comp/U + W/2 (or y_px = H/2 - comp/U); theta = 2pi (px - origin)/period
        m1 = n.new("ShaderNodeMath")
        m1.operation = "MULTIPLY_ADD"
        m1.inputs[1].default_value = (-1 if flip else 1) / U * 2 * math.pi / period_px
        m1.inputs[2].default_value = (centre_px - origin_px) * 2 * math.pi / period_px
        k.new(comp, m1.inputs[0])
        return m1

    ax = angle(sep.outputs["X"], W / 2, Pw, l, False)
    ay = angle(sep.outputs["Y"], H / 2, Ph, t, True)
    Rx = Pw / (2 * math.pi) * U * 100 * period_scale  # radius: texture units ~ px/100
    Ry = Ph / (2 * math.pi) * U * 100 * period_scale

    def trig(a, op, R):
        s = n.new("ShaderNodeMath")
        s.operation = op
        k.new(a.outputs[0], s.inputs[0])
        m = n.new("ShaderNodeMath")
        m.operation = "MULTIPLY"
        m.inputs[1].default_value = R
        k.new(s.outputs[0], m.inputs[0])
        return m

    cx, sx = trig(ax, "COSINE", Rx), trig(ax, "SINE", Rx)
    cy, sy = trig(ay, "COSINE", Ry), trig(ay, "SINE", Ry)
    comb = n.new("ShaderNodeCombineXYZ")
    k.new(cx.outputs[0], comb.inputs[0])
    k.new(sx.outputs[0], comb.inputs[1])
    k.new(cy.outputs[0], comb.inputs[2])
    return comb.outputs[0], sy.outputs[0]


def iron_material(name, W, H, margins, spec):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    n, k = nt.nodes, nt.links
    bsdf = n["Principled BSDF"]
    vec, w = periodic_coords(nt, W, H, margins)
    hammer = spec.get("hammer", 1.0)
    # Hammer dents: Voronoi F1 (round bowls), big and shallow.
    vor = n.new("ShaderNodeTexVoronoi")
    vor.voronoi_dimensions = "4D"
    vor.feature = "F1"
    vor.inputs["Scale"].default_value = spec.get("dent_scale", 0.10)
    k.new(vec, vor.inputs["Vector"])
    k.new(w, vor.inputs["W"])
    # Pitting and grain.
    noi = n.new("ShaderNodeTexNoise")
    noi.noise_dimensions = "4D"
    noi.inputs["Scale"].default_value = spec.get("grain_scale", 0.9)
    noi.inputs["Detail"].default_value = 6
    noi.inputs["Roughness"].default_value = 0.6
    k.new(vec, noi.inputs["Vector"])
    k.new(w, noi.inputs["W"])
    big = n.new("ShaderNodeTexNoise")
    big.noise_dimensions = "4D"
    big.inputs["Scale"].default_value = 0.05
    big.inputs["Detail"].default_value = 3
    k.new(vec, big.inputs["Vector"])
    k.new(w, big.inputs["W"])
    # Height: dents + grain -> bump.
    hsum = n.new("ShaderNodeMath")
    hsum.operation = "MULTIPLY_ADD"
    hsum.inputs[1].default_value = 0.35
    k.new(noi.outputs["Fac"], hsum.inputs[0])
    k.new(vor.outputs["Distance"], hsum.inputs[2])
    bump = n.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.6 * hammer
    bump.inputs["Distance"].default_value = 0.02
    k.new(hsum.outputs[0], bump.inputs["Height"])
    k.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    # Colour: dark violet iron, wandering a little; worn bright at convex edges (pointiness).
    geo = n.new("ShaderNodeNewGeometry")
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.505
    ramp.color_ramp.elements[1].position = 0.56
    k.new(geo.outputs["Pointiness"], ramp.inputs["Fac"])
    base = hexc(spec.get("color", "#2a2630"))
    tint = spec.get("tint", [1, 1, 1])
    base = tuple(base[i] * tint[i] for i in range(3)) + (1,)
    mixc = n.new("ShaderNodeMix")
    mixc.data_type = "RGBA"
    mixc.inputs[6].default_value = base
    mixc.inputs[7].default_value = hexc(spec.get("worn", "#8a8794"))
    wear = n.new("ShaderNodeMath")
    wear.operation = "MULTIPLY"
    wear.inputs[1].default_value = spec.get("wear", 0.75)
    k.new(ramp.outputs["Color"], wear.inputs[0])
    k.new(wear.outputs[0], mixc.inputs[0])
    vary = n.new("ShaderNodeMix")
    vary.data_type = "RGBA"
    vary.blend_type = "MULTIPLY"
    vary.inputs[0].default_value = 0.35
    k.new(mixc.outputs[2], vary.inputs[6])
    k.new(big.outputs["Color"], vary.inputs[7])
    ao = n.new("ShaderNodeAmbientOcclusion")
    ao.inputs["Distance"].default_value = spec.get("ao_dist", 0.08)
    grime = n.new("ShaderNodeMix")
    grime.data_type = "RGBA"
    grime.blend_type = "MULTIPLY"
    grime.inputs[0].default_value = 1.0
    k.new(vary.outputs[2], grime.inputs[6])
    k.new(ao.outputs["Color"], grime.inputs[7])
    k.new(grime.outputs[2], bsdf.inputs["Base Color"])
    bsdf.inputs["Metallic"].default_value = spec.get("metal", 0.85)
    rr = n.new("ShaderNodeMath")
    rr.operation = "MULTIPLY_ADD"
    rr.inputs[1].default_value = 0.35
    rr.inputs[2].default_value = spec.get("rough", 0.42) - 0.12
    k.new(noi.outputs["Fac"], rr.inputs[0])
    k.new(rr.outputs[0], bsdf.inputs["Roughness"])
    return m


def plain_material(name, color, metal=1.0, rough=0.3, emit=None, emit_strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = hexc(color)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = hexc(emit)
        b.inputs["Emission Strength"].default_value = emit_strength
    return m


def emission_material(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = hexc(color)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs[0])
    return m


# ---------------------------------------------------------------- shapes --

def outline(x0, y0, x1, y1, chamfer=0.0, radius=0.0, n_round=8, corners=None, shrink=0.0):
    """A rectangle's outline (file px), clockwise from the top left. Corners cut (chamfer),
    rounded (radius) or each its own (corners: [tl, tr, br, bl] radii); `shrink` is how far
    this outline lies inside the shape's outer edge (radii and cuts shrink with it)."""
    if corners is None and chamfer > 0:
        c = max(0.0, chamfer - shrink * 0.414)
        if c <= 0:
            return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        return [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c), (x1 - c, y1), (x0 + c, y1), (x0, y1 - c), (x0, y0 + c)]
    rs = corners if corners is not None else [radius] * 4
    rs = [max(0.0, r - shrink) for r in rs]
    pts = []
    for (cx, cy, a0), r in zip(((x0, y0, 180), (x1, y0, -90), (x1, y1, 0), (x0, y1, 90)), rs):
        if r <= 0:
            pts.append((cx, cy))
            continue
        ox = cx + (r if a0 in (180, 90) else -r)
        oy = cy + (r if a0 in (180, -90) else -r)
        for t in range(n_round + 1):
            a = math.radians(a0 + 90 * t / n_round)
            pts.append((ox + math.cos(a) * r, oy + math.sin(a) * r))
    return pts


def shape_of(spec, x0, y0, x1, y1, shrink=0.0):
    return outline(x0, y0, x1, y1, spec.get("chamfer", 0), spec.get("radius", 0), corners=spec.get("corners"), shrink=shrink)


def densify(pts, step=6.0, closed=True):
    out = []
    n = len(pts)
    for i in range(n if closed else n - 1):
        a, b = Vector(pts[i]), Vector(pts[(i + 1) % n])
        L = (b - a).length
        m = max(1, int(L / step))
        for j in range(m):
            out.append(tuple(a + (b - a) * (j / m)))
    if not closed:
        out.append(pts[-1])
    return out


def curve_object(name, splines, W, H, extrude=0.0, bevel=0.0, z=0.0, fill="BOTH", res=4, closed=True):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "2D" if fill else "3D"
    if fill:
        cu.fill_mode = fill
    cu.extrude = extrude * U
    cu.bevel_depth = bevel * U
    cu.bevel_resolution = res
    for pts in splines:
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for i, (x, y) in enumerate(pts):
            v = P(x, y, W, H)
            sp.points[i].co = (v.x, v.y, 0, 1)
        sp.use_cyclic_u = closed
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    ob.location.z = z * U
    return ob


def strap(spec, W, H, margins, mat):
    s = spec
    i = s.get("inset", 0)
    wdt = s["width"]
    outer = densify(shape_of(s, i, i, W - i, H - i), 8)
    inner = densify(shape_of(s, i + wdt, i + wdt, W - i - wdt, H - i - wdt, shrink=wdt), 8)[::-1]
    ob = curve_object("strap", [outer, inner], W, H, extrude=s.get("thick", 8) / 2, bevel=s.get("bevel", 3),
                      z=s.get("thick", 8) / 2)
    ob.data.materials.append(mat)
    return ob


def panel(spec, sspec, W, H, mat):
    i = spec["inset"]
    si = sspec.get("inset", 0)
    pts = densify(shape_of(sspec, i, i, W - i, H - i, shrink=i - si), 8)
    ob = curve_object("panel", [pts], W, H, extrude=0.5, bevel=0, z=spec.get("z", 1.0))
    ob.data.materials.append(mat)
    return ob


def wire(spec, sspec, W, H, margins, mat):
    """A twisted gold wire laid in the strap: a two-strand rope, its twist in phase over
    the tiled middle of each side."""
    l, t, r, b = margins
    Pw, Ph = W - l - r, H - t - b
    off = spec["offset"]
    i = sspec.get("inset", 0)

    def ring(d):
        return shape_of(sspec, i + d, i + d, W - i - d, H - i - d, shrink=d)
    pts = densify(ring(off), 1.5)
    pitch = spec.get("pitch", 7.0)
    nx = max(1, round(Pw / pitch))
    ny = max(1, round(Ph / pitch))
    px, py = Pw / nx, Ph / ny
    rr = spec["radius"]
    z = sspec.get("thick", 8) + sspec.get("bevel", 0) + rr * 0.1
    arc = spec.get("phase") == "arc"
    if arc:
        # A closed loop (a ring): the twist follows the length along it, a whole number of turns.
        seg = [math.hypot(pts[(j + 1) % len(pts)][0] - pts[j][0], pts[(j + 1) % len(pts)][1] - pts[j][1]) for j in range(len(pts))]
        total = sum(seg)
        turns = max(1, round(total / pitch))
        cum = [0.0]
        for d_ in seg[:-1]:
            cum.append(cum[-1] + d_)
    for strand in (0, 1):
        cu = bpy.data.curves.new(f"wire{strand}", "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = rr * 0.55 * U
        cu.bevel_resolution = 3
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for j, (x, y) in enumerate(pts):
            if arc:
                ph = 2 * math.pi * turns * cum[j] / total + strand * math.pi
                a, b_ = Vector(pts[j - 1]), Vector(pts[(j + 1) % len(pts)])
                tng = (b_ - a).normalized()
                nrm = Vector((-tng.y, -tng.x, 0))  # across the wire (file y is flipped)
            else:
                # Twist phase from the position along the side, so it repeats with the tile.
                horizontal = abs(y - (i + off)) < 0.5 or abs(y - (H - i - off)) < 0.5
                if not horizontal and not (abs(x - (i + off)) < 0.5 or abs(x - (W - i - off)) < 0.5):
                    horizontal = abs(y - H / 2) > abs(x - W / 2) * H / W
                ph = 2 * math.pi * ((x - l) / px if horizontal else (y - t) / py) + strand * math.pi
                nrm = Vector((0, 1, 0)) if horizontal else Vector((1, 0, 0))
            # The two strands circle the wire's centre line, across it and up and down.
            v = P(x, y, W, H, 0) + nrm * (math.cos(ph) * rr * 0.45 * U)
            sp.points[j].co = (v.x, v.y, (z + math.sin(ph) * rr * 0.45) * U, 1)
        sp.use_cyclic_u = True
        ob = bpy.data.objects.new(f"wire{strand}", cu)
        bpy.context.scene.collection.objects.link(ob)
        ob.data.materials.append(mat)
    # The groove the wire lies in: a darker channel.
    g = curve_object("groove", [densify(ring(off - rr * 1.2), 8), densify(ring(off + rr * 1.2), 8)[::-1]],
                     W, H, extrude=0.2, z=sspec.get("thick", 8) + sspec.get("bevel", 0) + 0.3)
    g.data.materials.append(plain_material("groove", "#08070a", 0.5, 0.7))


def coin(spec, W, H, mat, ember_mat, top):
    """The binders' square coin set on its point, a round hole through it; ember beneath."""
    x, y, s = spec["x"], spec["y"], spec["size"]
    rot = math.radians(spec.get("rot", 45))
    half = s / 2
    sq = []
    for k in range(4):
        a = rot + k * math.pi / 2 + math.pi / 4
        sq.append((x + math.cos(a) * half * math.sqrt(2) * 0.98, y + math.sin(a) * half * math.sqrt(2) * 0.98))
    # A slightly rounded square outline.
    hole_r = s * spec.get("hole", 0.3) / 2
    hole = [(x + math.cos(a) * hole_r, y + math.sin(a) * hole_r) for a in [2 * math.pi * j / 32 for j in range(32)]][::-1]
    th = spec.get("thick", s * 0.12)
    ob = curve_object("coin", [densify(sq, 4), hole], W, H, extrude=th / 2, bevel=s * 0.05, z=top + th / 2 + 0.5)
    ob.data.materials.append(mat)
    # A raised rim round the hole.
    ring = curve_object("coinring", [hole[::-1]], W, H, bevel=s * 0.035, fill=None, z=top + th + s * 0.02)
    ring.data.materials.append(mat)
    if spec.get("ember", 0) > 0:
        disc = [(x + math.cos(a) * hole_r * 1.1, y + math.sin(a) * hole_r * 1.1) for a in [2 * math.pi * j / 24 for j in range(24)]]
        e = curve_object("ember", [disc], W, H, extrude=0.1, z=top + 0.6)
        e.data.materials.append(ember_mat)


def rivet(spec, W, H, mat, top):
    x, y, r = spec["x"], spec["y"], spec["r"]
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=r * U, location=P(x, y, W, H, top))
    o = bpy.context.active_object
    o.scale.z = 0.55
    bpy.ops.object.shade_smooth()
    o.data.materials.append(mat)


def scroll(spec, W, H, mat, top):
    """A drawn bar along a path (the brackets' arms and scrolls), tapering."""
    pts = spec["pts"]
    w0, w1 = spec.get("w0", 8), spec.get("w1", 3)
    cu = bpy.data.curves.new("scroll", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = w0 * 0.5 * U
    cu.bevel_resolution = 4
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    n = len(pts)
    for j, (x, y) in enumerate(pts):
        v = P(x, y, W, H, 0)
        sp.points[j].co = (v.x, v.y, 0, 1)
        sp.points[j].radius = 1.0 - (1.0 - w1 / w0) * (j / max(1, n - 1))
    ob = bpy.data.objects.new("scroll", cu)
    bpy.context.scene.collection.objects.link(ob)
    # Flattened about its own centre line, which lies on the surface it is laid on.
    ob.location.z = (top + spec.get("lift", 1.0)) * U
    ob.scale.z = spec.get("flat", 0.6)
    ob.data.materials.append(mat)


def poly(spec, W, H, mat, top):
    """A flat forged piece of any outline (a finial, a strap end), extruded and bevelled."""
    th = spec.get("thick", 4)
    ob = curve_object("poly", [densify(spec["pts"], 3)], W, H, extrude=th / 2, bevel=spec.get("bevel", 1.5),
                      z=top + spec.get("lift", 0) + th / 2)
    ob.data.materials.append(mat)


def seam(spec, sspec, W, H, top):
    """Light along a ring inside the frame (the ember awake in the seam)."""
    i = sspec.get("inset", 0)
    d = spec["offset"]
    pts = densify(shape_of(sspec, i + d, i + d, W - i - d, H - i - d, shrink=d), 6)
    ob = curve_object("seam", [pts], W, H, bevel=spec.get("radius", 1.5), fill=None, z=spec.get("z", top * 0.5))
    ob.data.materials.append(emission_material("seam", spec.get("color", "#ff8a3a"), spec.get("strength", 3.0)))


def gem(spec, W, H, top):
    """A cut stone (the binders' amethyst, a rare's frost): a low brilliant, glossy, a little lit."""
    x, y, s = spec["x"], spec["y"], spec["size"]
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=s / 2 * U, location=P(x, y, W, H, top + s * 0.15))
    o = bpy.context.active_object
    o.scale.z = 0.55
    o.rotation_euler.z = math.radians(spec.get("rot", 0))
    m = plain_material("gem", spec.get("color", "#c070ff"), 0.0, 0.06, emit=spec.get("color", "#c070ff"),
                       emit_strength=spec.get("glow", 0.6))
    o.data.materials.append(m)


def crystal(spec, W, H, top):
    """An ice needle lying out from a corner (river rime)."""
    x, y = spec["x"], spec["y"]
    L, w = spec["len"], spec.get("w", spec["len"] * 0.22)
    a = math.radians(spec.get("angle", 0))
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=w / 2 * U, radius2=0, depth=L * U)
    o = bpy.context.active_object
    # Lie it along the surface, pointing at `angle` (file px space, y down).
    o.rotation_euler = (math.radians(90), 0, 0)
    bpy.ops.object.transform_apply(rotation=True)
    o.rotation_euler = (0, 0, -a - math.radians(90))
    o.location = P(x + math.cos(a) * L / 2, y + math.sin(a) * L / 2, W, H, top + w * 0.3)
    m = plain_material("ice", spec.get("color", "#bfe4ff"), 0.0, 0.05, emit=spec.get("glow_color", "#5aa8ff"),
                       emit_strength=spec.get("glow", 0.35))
    o.data.materials.append(m)


def crack(spec, W, H, top):
    """A crack in the iron with ember light in it."""
    pts = spec["pts"]
    cu = bpy.data.curves.new("crack", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = spec.get("w", 1.0) * U
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for j, (x, y) in enumerate(pts):
        v = P(x, y, W, H, top + 0.2)
        sp.points[j].co = (v.x, v.y, v.z, 1)
        sp.points[j].radius = 1.0 - 0.7 * j / max(1, len(pts) - 1)
    ob = bpy.data.objects.new("crack", cu)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(emission_material("crack", spec.get("color", "#ff7a2a"), spec.get("strength", 6.0)))


# ------------------------------------------------------------------ main --

def build(spec, out):
    W, H = spec["size"]
    ss = spec.get("ss", 2)
    margins = spec.get("margins", [W // 4] * 4)
    sc = reset()
    world(spec.get("world", "night"))
    suns()
    # Model in render pixels (file px * ss); textures periodic over the scaled middle.
    Ws, Hs = W * ss, H * ss
    ms = [m * ss for m in margins]

    def S(v):
        return v * ss

    def scale_spec(d, keys):
        d = dict(d)
        for k in keys:
            if k in d and d[k] is not None:
                d[k] = S(d[k])
        return d

    camera(Ws, Hs)
    st = scale_spec(spec["strap"], ["inset", "width", "thick", "bevel", "chamfer", "radius"])
    if st.get("corners"):
        st["corners"] = [c * ss for c in st["corners"]]
    st_spec = dict(spec["strap"])
    st_spec["dent_scale"] = st_spec.get("dent_scale", 0.10) / ss
    st_spec["grain_scale"] = st_spec.get("grain_scale", 0.9) / ss
    iron = iron_material("iron", Ws, Hs, ms, st_spec)
    strap(st, Ws, Hs, ms, iron)
    if spec.get("panel"):
        pn = scale_spec(spec["panel"], ["inset", "chamfer", "radius", "z"])
        pspec = dict(spec["panel"])
        pspec.setdefault("color", "#16131a")
        pspec["metal"] = pspec.get("metal", 0.5)
        pspec["rough"] = pspec.get("rough", 0.6)
        pspec["wear"] = 0.0
        pspec["dent_scale"] = pspec.get("dent_scale", 0.05) / ss
        pspec["grain_scale"] = pspec.get("grain_scale", 0.6) / ss
        pspec["hammer"] = pspec.get("hammer", 0.4)
        panel(pn, st, Ws, Hs, iron_material("panel", Ws, Hs, ms, pspec))
    top = st["thick"] + st.get("bevel", 0)  # the strap's top face (the bevel rounds out past the extrusion)
    if spec.get("wire"):
        wr = scale_spec(spec["wire"], ["offset", "radius", "pitch"])
        wire(wr, st, Ws, Hs, ms, plain_material("gold", spec["wire"].get("color", "#d9b56a"), 1.0, spec["wire"].get("rough", 0.28)))
    cmat = iron_material("coin", Ws, Hs, ms, dict(st_spec, wear=0.9, hammer=0.6))
    ember = emission_material("ember", spec.get("ember_color", "#ff6a1a"), spec.get("ember_strength", 6.0))
    for c in spec.get("coins", []):
        coin(scale_spec(c, ["x", "y", "size", "thick"]), Ws, Hs, cmat, ember, top)
    rmat = iron_material("rivet", Ws, Hs, ms, dict(st_spec, wear=1.0, hammer=0.3, rough=0.35))
    # The brackets' drawn iron: a shade lighter and more worn than the strap they lie on.
    smat = iron_material("bracket", Ws, Hs, ms, dict(st_spec, color="#2c2833", wear=1.0, hammer=0.7, rough=0.34))
    for r_ in spec.get("rivets", []):
        rivet(scale_spec(r_, ["x", "y", "r"]), Ws, Hs, rmat, top + (spec.get("rivet_lift", 0) * ss))
    for s_ in spec.get("scrolls", []):
        d = dict(s_)
        d["pts"] = [(x * ss, y * ss) for x, y in s_["pts"]]
        d = scale_spec(d, ["w0", "w1", "lift"])
        scroll(d, Ws, Hs, smat, top)
    for pl in spec.get("polys", []):
        d = dict(pl)
        d["pts"] = [(x * ss, y * ss) for x, y in pl["pts"]]
        poly(scale_spec(d, ["thick", "bevel", "lift"]), Ws, Hs, smat, top)
    if spec.get("seam"):
        sm = scale_spec(spec["seam"], ["offset", "radius", "z"])
        seam(sm, st, Ws, Hs, top)
    for g in spec.get("gems", []):
        gem(scale_spec(g, ["x", "y", "size"]), Ws, Hs, top)
    for c in spec.get("crystals", []):
        crystal(scale_spec(c, ["x", "y", "len", "w"]), Ws, Hs, top)
    for c in spec.get("cracks", []):
        d = dict(c)
        d["pts"] = [(x * ss, y * ss) for x, y in c["pts"]]
        crack(scale_spec(d, ["w"]), Ws, Hs, top)
    for t_ in spec.get("thorns", []):
        d = dict(t_)
        d["pts"] = [(x * ss, y * ss) for x, y in t_["pts"]]
        d = scale_spec(d, ["w0", "w1", "lift"])
        scroll(d, Ws, Hs, plain_material("thorn", t_.get("color", "#2e3a1e"), 0.0, 0.45), top)
    for f_ in spec.get("flames", []):
        d = dict(f_)
        d["pts"] = [(x * ss, y * ss) for x, y in f_["pts"]]
        d = scale_spec(d, ["w0", "w1", "lift"])
        scroll(d, Ws, Hs, plain_material("flame", f_.get("color", "#e0a848"), 1.0, 0.25,
                                         emit="#ff9a3a", emit_strength=f_.get("glow", 0.0)), top)
    sc.cycles.samples = spec.get("samples", 96)
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:]
    spec = json.load(open(argv[0], encoding="utf-8"))
    build(spec, argv[1])
