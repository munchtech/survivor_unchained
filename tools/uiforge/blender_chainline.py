"""A length of forged chain hung against the page, modelled and rendered in Blender under the
house light (the world and suns of blender_frames.py), its shadow caught on the page.

    blender -b -P tools/uiforge/blender_chainline.py -- spec.json out.png

The spec, in FILE pixels (y down), the render being the file:

    {"size": [W, H], "ss": 2, "samples": 64,
     "link": {"length": 30, "width": 18, "wire": 2.4},
     "chains": [{"from": [x, y], "to": [x, y], "sag": 30, "open": [k], "gap": 1.1}],
     "staples": [{"x": x, "y": y}],
     "ember": 6.0}

Links stand alternately flat on the page and on edge, as a chain hangs against a wall. Each
is worn bright where its neighbours rub it (the contact found from the meshes themselves)
and darkened with rust and grime in its hollows. A link listed in `open` is pried apart at
its lower end, ember light in the break.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import blender_frames as B  # noqa: E402

U = B.U
SPEC = {}
# How far from a neighbour's surface a link is rubbed bright, in bar radii.
WEAR_REACH = 1.1


def catenary(p0, p1, sag, n=400):
    """Points (file px, y down) of a chain hung between two points at the same height, `sag`
    px at its lowest. Returns the curve and its arc lengths."""
    (x0, y0), (x1, y1) = p0, p1
    h = (x1 - x0) / 2
    lo, hi = 1e-3, 1e6
    for _ in range(200):          # a with a*(cosh(h/a) - 1) = sag
        a = math.sqrt(lo * hi)
        if a * (math.cosh(h / a) - 1) > sag:
            lo = a
        else:
            hi = a
    xc = (x0 + x1) / 2
    pts = []
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        dy = a * (math.cosh((x - xc) / a) - math.cosh(h / a))      # 0 at the ends, -sag at the middle
        t = i / n
        pts.append((x, y0 + (y1 - y0) * t - dy))
    s = [0.0]
    for i in range(1, len(pts)):
        s.append(s[-1] + math.dist(pts[i - 1], pts[i]))
    return pts, s


def at(pts, s, d):
    """The point and unit tangent at arc length d."""
    for i in range(1, len(s)):
        if s[i] >= d:
            f = (d - s[i - 1]) / max(s[i] - s[i - 1], 1e-9)
            p = (pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * f, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * f)
            t = (pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])
            n = math.hypot(*t) or 1
            return p, (t[0] / n, t[1] / n)
    return pts[-1], (1.0, 0.0)


def link_mesh(name, length, width, wire, gap=0.0, where="side"):
    """A stadium-shaped link of round bar, as a mesh, and the tips of its break if it has one.
    `gap` (Blender units) pries it open: in the middle of its lower side ("side"), or at its
    end toward -x ("minus") or +x ("plus"), the bar's ends there bent apart."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = wire
    cu.bevel_resolution = 5
    cu.use_fill_caps = True
    r = width / 2 - wire
    st = max(length - width, 0) / 2
    pts = []
    for i in range(24):                                   # lower side, middle to the right
        pts.append((st * i / 24, -r))
    for i in range(49):                                   # the right end
        t = -math.pi / 2 + math.pi * i / 48
        pts.append((st + r * math.cos(t), r * math.sin(t)))
    for i in range(1, 49):                                # the upper side
        pts.append((st - 2 * st * i / 48, r))
    for i in range(1, 49):                                # the left end
        t = math.pi / 2 + math.pi * i / 48
        pts.append((-st + r * math.cos(t), r * math.sin(t)))
    for i in range(1, 24):                                # lower side, back to the middle
        pts.append((-st + st * i / 24, -r))
    tips = []
    if gap:
        if where == "side":
            c = (0.0, -r)
            cut = [y < -r * 0.99 and abs(x) < gap / 2 for x, y in pts]
        elif where == "minus":
            c = (-st - r, 0.0)
            cut = [x < -st and abs(y) < gap / 2 for x, y in pts]
        else:
            c = (st + r, 0.0)
            cut = [x > st and abs(y) < gap / 2 for x, y in pts]
        n = len(pts)
        start = next(i for i in range(n) if not cut[i] and cut[i - 1])
        seq = [pts[(start + j) % n] for j in range(n) if not cut[(start + j) % n]]
        # Pried: the bar's ends near the break bent apart, away from the break's middle.
        m = max(6, len(seq) // 7)
        bent = []
        for j, (x, y) in enumerate(seq):
            f = max(0.0, 1 - min(j, len(seq) - 1 - j) / m) ** 2
            dx, dy = x - c[0], y - c[1]
            dl = math.hypot(dx, dy) or 1.0
            bent.append((x + f * gap * 0.45 * dx / dl, y + f * gap * 0.45 * dy / dl))
        pts = bent
        tips = [pts[0], pts[-1]]
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, (x, y) in enumerate(pts):
        sp.points[i].co = (x, y, 0, 1)
    sp.use_cyclic_u = not gap
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.selected_objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.ops.object.convert(target="MESH")
    return bpy.context.view_layer.objects.active, tips


def iron_chain_material():
    """Blackened iron: rubbed bright where the `wear` colour says, rust and grime in its hollows."""
    m = bpy.data.materials.new("chain_iron")
    m.use_nodes = True
    nt = m.node_tree
    n, k = nt.nodes, nt.links
    bsdf = n["Principled BSDF"]
    attr = n.new("ShaderNodeAttribute")
    attr.attribute_name = "wear"
    ao = n.new("ShaderNodeAmbientOcclusion")
    ao.inputs["Distance"].default_value = 6.0 * U
    tco = n.new("ShaderNodeTexCoord")
    noise = n.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 9.0 / U / 100.0
    noise.inputs["Detail"].default_value = 8.0
    k.new(tco.outputs["Object"], noise.inputs["Vector"])
    # Rust where it is hollow and the noise allows: (1 - AO) * noise.
    inv = n.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    k.new(ao.outputs["AO"], inv.inputs[1])
    rmask = n.new("ShaderNodeMath")
    rmask.operation = "MULTIPLY"
    k.new(inv.outputs[0], rmask.inputs[0])
    k.new(noise.outputs["Fac"], rmask.inputs[1])
    rk = n.new("ShaderNodeMath")
    rk.operation = "MULTIPLY"
    rk.inputs[1].default_value = 3.0
    rk.use_clamp = True
    k.new(rmask.outputs[0], rk.inputs[0])
    base = n.new("ShaderNodeMix")
    base.data_type = "RGBA"
    base.inputs[6].default_value = B.hexc(SPEC.get("iron", "#1f1b1b"))
    base.inputs[7].default_value = B.hexc(SPEC.get("rust", "#3a2214"))
    k.new(rk.outputs[0], base.inputs[0])
    worn = n.new("ShaderNodeMix")
    worn.data_type = "RGBA"
    k.new(attr.outputs["Fac"], worn.inputs[0])
    k.new(base.outputs[2], worn.inputs[6])
    worn.inputs[7].default_value = B.hexc(SPEC.get("worn", "#9c96a2"))
    k.new(worn.outputs[2], bsdf.inputs["Base Color"])
    # Rough where rusted, smooth where rubbed.
    rough = n.new("ShaderNodeMapRange")
    k.new(rk.outputs[0], rough.inputs["Value"])
    rough.inputs["To Min"].default_value = 0.42
    rough.inputs["To Max"].default_value = 0.9
    rough2 = n.new("ShaderNodeMix")
    rough2.data_type = "FLOAT"
    k.new(attr.outputs["Fac"], rough2.inputs[0])
    k.new(rough.outputs[0], rough2.inputs[2])
    rough2.inputs[3].default_value = SPEC.get("worn_rough", 0.22)
    k.new(rough2.outputs[0], bsdf.inputs["Roughness"])
    metal = n.new("ShaderNodeMapRange")
    k.new(rk.outputs[0], metal.inputs["Value"])
    metal.inputs["To Min"].default_value = 0.85
    metal.inputs["To Max"].default_value = 0.15
    k.new(metal.outputs[0], bsdf.inputs["Metallic"])
    return m


def hot_material(gap_pts, reach):
    """The pried link's iron, hot at its torn ends: ember light fading along the bar from the
    break (object space), the rest the chain's iron."""
    m = iron_chain_material()
    m.name = "chain_hot"
    nt = m.node_tree
    n, k = nt.nodes, nt.links
    bsdf = n["Principled BSDF"]
    tco = n.new("ShaderNodeTexCoord")
    heat = None
    for gp in gap_pts:
        d = n.new("ShaderNodeVectorMath")
        d.operation = "DISTANCE"
        d.inputs[1].default_value = gp
        k.new(tco.outputs["Object"], d.inputs[0])
        mr = n.new("ShaderNodeMapRange")
        k.new(d.outputs["Value"], mr.inputs["Value"])
        mr.inputs["From Min"].default_value = 0.0
        mr.inputs["From Max"].default_value = reach
        mr.inputs["To Min"].default_value = 1.0
        mr.inputs["To Max"].default_value = 0.0
        if heat is None:
            heat = mr
        else:
            mx = n.new("ShaderNodeMath")
            mx.operation = "MAXIMUM"
            k.new(heat.outputs[0], mx.inputs[0])
            k.new(mr.outputs[0], mx.inputs[1])
            heat = mx
    pw = n.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 2.2
    k.new(heat.outputs[0], pw.inputs[0])
    st = n.new("ShaderNodeMath")
    st.operation = "MULTIPLY"
    st.inputs[1].default_value = 9.0
    k.new(pw.outputs[0], st.inputs[0])
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = B.hexc("#a8200a")
    ramp.color_ramp.elements[1].color = B.hexc("#ffc060")
    k.new(pw.outputs[0], ramp.inputs["Fac"])
    k.new(ramp.outputs["Color"], bsdf.inputs["Emission Color"])
    k.new(st.outputs[0], bsdf.inputs["Emission Strength"])
    return m


def mark_wear(links, wire):
    """Each link's vertices near a neighbour's surface are rubbed bright (a colour 'wear')."""
    dg = bpy.context.evaluated_depsgraph_get()
    trees = [BVHTree.FromObject(o, dg) for o in links]
    for i, o in enumerate(links):
        me = o.data
        if "wear" not in me.color_attributes:
            me.color_attributes.new("wear", "FLOAT_COLOR", "POINT")
        ca = me.color_attributes["wear"]
        mw = o.matrix_world
        inv = [links[j].matrix_world.inverted() for j in range(len(links))]
        for v in me.vertices:
            p = mw @ v.co
            best = 1e9
            for j in (i - 1, i + 1):
                if 0 <= j < len(links):
                    loc, _, _, d = trees[j].find_nearest(inv[j] @ p)
                    if loc is not None:
                        best = min(best, (links[j].matrix_world @ loc - p).length)
            w = max(0.0, 1.0 - best / (wire * WEAR_REACH)) ** 1.2
            ca.data[v.index].color = (w, w, w, 1)


def staple(x, y, W, H, mat, wire, ss):
    """A forged staple driven into the rail: a small plate with two nails and a ring on edge
    (sizes in file px, times ss)."""
    bpy.ops.mesh.primitive_cube_add(size=1)
    pl = bpy.context.active_object
    pl.scale = (16 * ss * U, 11 * ss * U, 2.2 * ss * U)
    pl.location = B.P(x, y, W, H, 1.1 * ss)
    bev = pl.modifiers.new("b", "BEVEL")
    bev.width = 1.2 * ss * U
    bev.segments = 3
    pl.data.materials.append(mat)
    for sx in (-5.0, 5.0):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1.8 * ss * U, location=B.P(x + sx * ss, y, W, H, 2.2 * ss))
        nl = bpy.context.active_object
        nl.scale = (1, 1, 0.55)
        nl.data.materials.append(mat)
    bpy.ops.mesh.primitive_torus_add(major_radius=5.0 * ss * U, minor_radius=wire * U, location=B.P(x, y + 2 * ss, W, H, 5.0 * ss))
    rg = bpy.context.active_object
    rg.rotation_euler = (math.pi / 2, 0, 0)
    rg.data.materials.append(mat)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    spec = json.load(open(argv[0], encoding="utf-8"))
    SPEC.update(spec.get("material", {}))
    out = argv[1]
    sc = B.reset()
    if spec.get("cpu", True):
        sc.cycles.device = "CPU"
    sc.cycles.samples = spec.get("samples", 64)
    B.world()
    B.suns()
    ss = spec.get("ss", 2)
    Wf, Hf = spec["size"]
    W, H = Wf * ss, Hf * ss
    B.camera(W, H)
    L = spec["link"]
    length, width, wire = L["length"] * ss, L["width"] * ss, L["wire"] * ss
    pitch = length - 2 * 2 * wire                   # each link's inner length: where the next one sits
    mat = iron_chain_material()
    ember = B.emission_material("ember", "#ff7a1a", spec.get("ember", 6.0))
    for ci, ch in enumerate(spec["chains"]):
        p0 = (ch["from"][0] * ss, ch["from"][1] * ss)
        p1 = (ch["to"][0] * ss, ch["to"][1] * ss)
        pts, s = catenary(p0, p1, ch["sag"] * ss)
        total = s[-1]
        nlinks = max(1, int(total / pitch))
        start = (total - nlinks * pitch) / 2
        opens = ch.get("open", [])
        if opens == "middle":
            opens = [nlinks // 2]
        elif opens == "first":
            opens = [0]
        elif opens == "last":
            opens = [nlinks - 1]
        # An open link lies flat, so its break faces the eye.
        parity = (opens[0] % 2) if opens else 0
        links = []
        import random
        rnd = random.Random(ci * 1009 + 7)
        for i in range(nlinks):
            d = start + (i + 0.5) * pitch
            (px, py), (tx, ty) = at(pts, s, d)
            ang = math.atan2(-ty, tx)                   # y down to Blender's y up
            opened = i in opens
            gap = ch.get("gap", 7.0) * ss * U if opened else 0.0
            # Pried apart on its lower side (toward the page's foot).
            # Forged by hand: no two links quite alike, none lying quite true.
            sl = 1 + rnd.uniform(-0.05, 0.05)
            sw_ = 1 + rnd.uniform(-0.06, 0.06)
            where = ch.get("where", "side")
            if where == "end":
                where = "minus" if i == 0 else "plus"
            ob, tips = link_mesh(f"c{ci}_{i}", length * sl * U, width * sw_ * U, wire * U, gap=gap, where=where)
            standing = (i + parity) % 2 == 1
            tilt = rnd.uniform(-0.18, 0.18) if not opened else 0.0
            ob.rotation_euler = ((math.pi / 2 if standing else 0.0) + tilt, rnd.uniform(-0.05, 0.05), ang + rnd.uniform(-0.04, 0.04))
            ob.location = B.P(px, py, W, H, (width / 2) if standing else wire)
            ob.data.materials.append(hot_material([(tx_, ty_, 0) for tx_, ty_ in tips], gap * 1.6) if opened else mat)
            links.append(ob)
        bpy.context.view_layer.update()
        mark_wear(links, wire * U)
    for st in spec.get("staples", []):
        staple(st["x"] * ss, st["y"] * ss, W, H, mat, wire, ss)
    # The page under it catches its shadow.
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    pl = bpy.context.active_object
    pl.scale = (W * U * 1.2, H * U * 1.2, 1)
    pl.is_shadow_catcher = True
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
