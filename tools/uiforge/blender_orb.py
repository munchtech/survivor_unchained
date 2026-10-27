"""The life orb's iron casing, modelled and rendered in Blender under the house light (the world and
suns of blender_frames.py): UI 16, the owner's "lets have what they are encased in show our themes".

    blender -b -P tools/uiforge/blender_orb.py -- spec.json out.png

Two forms (spec "form"):
  link  one great forged link, a little wider than tall, gripping the glass; snapped open on its upper
        right, the two ends pried ~25 deg apart, each a rough fracture face tilted to the eye
  ring  the glass ringed by forged links (the Flare emblem's ring, blender_chain.py, sized for the orb),
        flat and on edge in turn, one snapped open and splayed the same way
Both: hammer dimples over every bar (their ridges rubbed bright on the crown), forge scale in the
iron's colour and roughness, a dark recessed back plate behind the glass (only its crescents show), and
a forged eye welded on the lower right that the HUD's chain leaves from.

Sizes in the spec are 1080 px; the render is `px` render px per 1080 px (6: the HUD art is twice 1080,
supersampled 3x). Writes out.png (RGBA, straight alpha, transparent ground) and out.json: the glass's
opening (centre, radius) and the eye in render px (y down), for lamp_life_cut.py's ORBS.

Spec: {"form": "link", "px": 6, "samples": 128, "glass_r": 49, "wire": 14, "aspect": 1.13,
       "break_deg": 48, "gap": 20, "splay": 25, "lug_deg": -38,
       "ring": {"n": 7, "width": 27, "wire": 5.6, "open_deg": 62.9, "tilt": 48},
       "dent": [6.5, 0.9], "iron": "#17171c", "iron2": "#26262d", "worn": "#9aa0ad", "frac": "#7c818b"}
"""
import json
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Vector, noise
from mathutils.kdtree import KDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import blender_frames as B  # noqa: E402

U = B.U
SP = {}
K = 1.0  # Blender units per 1080 px


def P(v):
    return v * K


# ------------------------------------------------------------- paths --

def ellipse(a, b, n):
    return [Vector((a * math.cos(2 * math.pi * i / n), b * math.sin(2 * math.pi * i / n), 0)) for i in range(n)]


def superellipse(a, b, p, n):
    """A rounded-square oval (|x/a|^p + |y/b|^p = 1), resampled to even spacing: a forged link's
    straighter sides."""
    raw = []
    for i in range(n * 4):
        t = 2 * math.pi * i / (n * 4)
        c, s_ = math.cos(t), math.sin(t)
        raw.append(Vector((a * math.copysign(abs(c) ** (2 / p), c), b * math.copysign(abs(s_) ** (2 / p), s_), 0)))
    seg = [(raw[(i + 1) % len(raw)] - raw[i]).length for i in range(len(raw))]
    total = sum(seg)
    out, acc, j = [], 0.0, 0
    for k in range(n):
        target = total * k / n
        while acc + seg[j] < target:
            acc += seg[j]
            j += 1
        f = (target - acc) / seg[j]
        out.append(raw[j].lerp(raw[(j + 1) % len(raw)], f))
    return out


def stadium(length, width, wire, n_end=40, step=None):
    """A chain link's centreline (as blender_chainline.link_mesh): straight sides, half-circle ends."""
    r = width / 2 - wire
    st = max(length - width, 0) / 2
    step = step or r * math.pi / n_end
    pts = []
    ns = max(2, int(2 * st / step))
    for i in range(ns):                                   # lower side, left to right
        pts.append(Vector((-st + 2 * st * i / ns, -r, 0)))
    for i in range(n_end):                                # right end
        t = -math.pi / 2 + math.pi * i / n_end
        pts.append(Vector((st + r * math.cos(t), r * math.sin(t), 0)))
    for i in range(ns):                                   # upper side, right to left
        pts.append(Vector((st - 2 * st * i / ns, r, 0)))
    for i in range(n_end):                                # left end
        t = math.pi / 2 + math.pi * i / n_end
        pts.append(Vector((-st + r * math.cos(t), r * math.sin(t), 0)))
    return pts


def snap(pts, at, gap, splay_deg, bend_len, lift=0.0):
    """Open a closed centreline: cut `gap` long round the point nearest `at`, and pry each end out
    (away from the loop's middle) by splay/2, bending over `bend_len` back from its tip. Returns the open
    polyline (tip B ... tip A), extended 1.6 wires past each tip for the fracture cut, and the tips with
    their outward tangents."""
    n = len(pts)
    c = min(range(n), key=lambda i: (pts[i] - at).length)
    seg = [(pts[(i + 1) % n] - pts[i]).length for i in range(n)]
    # walk out from the cut's middle both ways until gap/2
    def walk(direction, dist):
        i, d = c, 0.0
        while d < dist:
            j = (i + direction) % n
            d += (pts[j] - pts[i]).length
            i = j
        return i
    ia, ib = walk(1, gap / 2), walk(-1, gap / 2)     # first kept index on each side
    seq = []
    i = ia
    while True:
        seq.append(pts[i].copy())
        if i == ib:
            break
        i = (i + 1) % n
    mid = sum(pts, Vector()) / n
    half = math.radians(splay_deg / 2)
    # pry: each end rotated about a pivot bend_len back from its tip, graded so the bar bends
    for end in (0, 1):
        idx = range(len(seq)) if end == 0 else range(len(seq) - 1, -1, -1)
        idx = list(idx)
        acc, k = 0.0, 0
        while acc < bend_len and k < len(idx) - 1:
            acc += (seq[idx[k + 1]] - seq[idx[k]]).length
            k += 1
        piv = seq[idx[k]]
        tip = seq[idx[0]]
        best = None
        for sgn in (-1, 1):
            v = (tip - piv)
            ang = sgn * half
            rv = Vector((v.x * math.cos(ang) - v.y * math.sin(ang), v.x * math.sin(ang) + v.y * math.cos(ang), 0))
            if best is None or ((piv + rv) - mid).length > best[1]:
                best = (sgn, ((piv + rv) - mid).length)
        sgn = best[0]
        for m in range(k):
            p = seq[idx[m]]
            u = 1 - m / k
            ang = sgn * half * (u ** 0.7)
            v = p - piv
            seq[idx[m]] = piv + Vector((v.x * math.cos(ang) - v.y * math.sin(ang), v.x * math.sin(ang) + v.y * math.cos(ang),
                                        v.z + lift * (u ** 2) * (1 if end == 0 else -1)))
    tips = []
    out = []
    for end in (0, 1):
        t0, t1 = (seq[0], seq[2]) if end == 0 else (seq[-1], seq[-3])
        tan = (t0 - t1).normalized()
        tips.append((t0.copy(), tan))
    ext = SP["_wire_now"] * 1.7
    pre = [tips[0][0] + tips[0][1] * ext * f for f in (1.0, 0.66, 0.33)]
    post = [tips[1][0] + tips[1][1] * ext * f for f in (0.33, 0.66, 1.0)]
    out = pre + seq + post
    return out, tips


# -------------------------------------------------------------- meshes --

def tube(name, pts, wire, closed, res=12):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = wire
    cu.bevel_resolution = res
    cu.use_fill_caps = False
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (p.x, p.y, p.z, 1)
    sp.use_cyclic_u = closed
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    for o in bpy.context.selected_objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.convert(target="MESH")
    return bpy.context.view_layer.objects.active


def fracture(ob, tips, wire, seed):
    """Each tip cut on a slant (the face tilted toward the eye so it reads from the front), the hole filled,
    the face broken up: a rough, torn, crystalline face (material slot 1)."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    rnd = random.Random(seed)
    for f in bm.faces:
        f.material_index = 0
    planes = []
    for ti, (tip, tan) in enumerate(tips):
        other = tips[1 - ti][0] if len(tips) > 1 else tip + tan * 1e6
        beta = math.radians(rnd.uniform(*SP.get("slant", [20, 28])))
        side = Vector((-tan.y, tan.x, 0)) * rnd.uniform(-0.25, 0.25)
        nrm = (tan * math.cos(beta) + Vector((0, 0, math.sin(beta))) + side).normalized()
        planes.append(nrm)

        def mine(c):
            return (c - tip).length < wire * 3.2 and (c - tip).length < (c - other).length
        near = [e for e in bm.verts[:] + bm.edges[:] + bm.faces[:]
                if mine(e.co if isinstance(e, bmesh.types.BMVert) else
                        (e.verts[0].co + e.verts[1].co) / 2 if isinstance(e, bmesh.types.BMEdge) else e.calc_center_median())]
        bmesh.ops.bisect_plane(bm, geom=near, plane_co=tip, plane_no=nrm, clear_outer=True, dist=wire * 1e-4)
        bnd = [e for e in bm.edges if e.is_boundary and mine((e.verts[0].co + e.verts[1].co) / 2)]
        res = bmesh.ops.holes_fill(bm, edges=bnd, sides=0)
        for f in res["faces"]:
            pk = bmesh.ops.poke(bm, faces=[f])
            for f2 in pk["faces"]:
                f2.material_index = 1
            for v in pk["verts"]:
                v.co += nrm * wire * rnd.uniform(-0.15, 0.25)
    # subdivide the cap fans for interior detail (their material carries), then tear the face
    capf = [f for f in bm.faces if f.material_index == 1]
    inner = list({e for f in capf for e in f.edges if all(lf.material_index == 1 for lf in e.link_faces)})
    bmesh.ops.subdivide_edges(bm, edges=inner, cuts=4, use_grid_fill=True)
    bm.normal_update()
    capv = {v for f in bm.faces if f.material_index == 1 for v in f.verts}
    skinv = {v for f in bm.faces if f.material_index == 0 for v in f.verts}
    for ti, (tip, tan) in enumerate(tips):
        nrm = planes[ti]
        for v in bm.verts:
            d = v.co - tip
            if d.length > wire * 3.2:
                continue
            sd = d.dot(nrm)                         # 0 on the cut, negative back along the bar
            if sd < -wire * 0.9 or sd > wire * 0.05:
                continue
            q = v.co / wire + Vector((seed * 1.7, ti * 3.1, 0))
            # torn: the break's line ragged along the bar (teeth and a shear lip), fading back into the skin
            jag = 0.42 * noise.noise(q * 1.6) + 0.18 * noise.noise(q * 4.3)
            fall = max(0.0, 1 + sd / (wire * 0.9))
            v.co += tan * wire * jag * fall
            if v in capv and v not in skinv:
                # the face itself: coarse crystalline steps
                h = 0.22 * noise.noise(q * 2.2) + 0.10 * noise.noise(q * 6.5)
                v.co += nrm * wire * h
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()


def hammer(ob, cell, depth, wire, seed):
    """Hammer blows over the bar: shallow spherical dents (the deepest wins), their ridges left high; a slow
    unevenness in the bar's thickness; returns each vertex's ridge-ness (1 on a ridge, 0 deep in a dent)."""
    me = ob.data
    me.update()
    rnd = random.Random(seed)
    vs = [v for v in me.vertices]
    capf = set()
    for p in me.polygons:
        if p.material_index == 1:
            capf.update(p.vertices)
    area = sum(p.area for p in me.polygons)
    nseed = int(area / (cell * cell) * 1.3)
    pick = rnd.sample(range(len(vs)), min(nseed, len(vs)))
    kd = KDTree(len(pick))
    for i, j in enumerate(pick):
        kd.insert(vs[j].co, i)
    kd.balance()
    R = cell * 0.8
    ridge = [1.0] * len(vs)
    moves = []
    for v in vs:
        if v.index in capf:
            moves.append(None)
            continue
        dent = 0.0
        for (co, i, d) in kd.find_range(v.co, R):
            dd = depth * (0.6 + 0.8 * ((i * 7919) % 97) / 97) * (1 - (d / R) ** SP.get("dent_pow", 2))
            dent = max(dent, dd)
        lo = wire * 0.045 * noise.noise(v.co / (wire * 2.6) + Vector((seed, 1, 2)))
        ridge[v.index] = 1 - dent / (depth * 1.4)
        moves.append((v.normal.copy(), lo - dent))
    # (the dents about the bar's true surface, not all into it: the bar keeps its size, so the glass meets it)
    mean = sum(m[1] for m in moves if m is not None) / max(1, sum(1 for m in moves if m is not None))
    for v, m in zip(vs, moves):
        if m is not None:
            v.co += m[0] * (m[1] - mean)
    me.update()
    return ridge


def wear(ob, ridge, seed, contacts=()):
    """'wear' (a colour attribute the iron reads): the crown and the upper-left rims rubbed bright where the
    hammering left them high, patchy; and wherever another piece rubs (contacts: points, radius)."""
    me = ob.data
    if "wear" not in me.color_attributes:
        me.color_attributes.new("wear", "FLOAT_COLOR", "POINT")
    ca = me.color_attributes["wear"]
    me.calc_loop_triangles()
    key = Vector((-0.6, 0.62, 0.5)).normalized()
    graze = Vector((-0.66, 0.66, 0.22)).normalized()
    capf = set()
    for p in me.polygons:
        if p.material_index == 1:
            capf.update(p.vertices)
    for v in me.vertices:
        n = v.normal
        crown = max(0.0, n.z) ** 4
        rim = max(0.0, n.dot(key)) ** 6
        patch = 0.5 + 0.5 * noise.noise(v.co * (1.0 / (SP.get("wear_patch", 9) * K)) + Vector((seed, 3, 5)))
        r = max(0.0, ridge[v.index] if ridge else 1.0)
        edge = max(0.0, n.dot(graze)) ** SP.get("edge_pow", 14)
        w = 0.7 * crown * (r ** 2.2) * min(1.0, max(0.0, (patch - 0.4) * 2.6)) + 0.35 * rim * r ** 2 + edge * (0.55 + 0.45 * r)
        w = min(1.0, w)
        for (pt, rad) in contacts:
            d = (v.co - pt).length
            w = max(w, max(0.0, 1 - d / rad) ** 1.5 * 0.9)
        if v.index in capf:
            w = 0.0
        ca.data[v.index].color = (w, w, w, 1)


def place(ob, loc=(0, 0, 0), rot=(0, 0, 0)):
    ob.location = loc
    ob.rotation_euler = rot
    bpy.context.view_layer.update()


# ----------------------------------------------------------- materials --

def iron_material():
    m = bpy.data.materials.new("orb_iron")
    m.use_nodes = True
    nt = m.node_tree
    n, k = nt.nodes, nt.links
    bsdf = n["Principled BSDF"]
    tco = n.new("ShaderNodeTexCoord")
    attr = n.new("ShaderNodeAttribute")
    attr.attribute_name = "wear"
    # forge scale: broad patches of darker, rougher scale over the blued iron, flaking at their edges
    big = n.new("ShaderNodeTexNoise")
    big.inputs["Scale"].default_value = 1.0 / (SP.get("scale_size", 7.0) * K)
    big.inputs["Detail"].default_value = 6.0
    big.inputs["Roughness"].default_value = 0.62
    k.new(tco.outputs["Object"], big.inputs["Vector"])
    flake = n.new("ShaderNodeMapRange")
    k.new(big.outputs["Fac"], flake.inputs["Value"])
    flake.inputs["From Min"].default_value = 0.44
    flake.inputs["From Max"].default_value = 0.56
    fine = n.new("ShaderNodeTexNoise")
    fine.inputs["Scale"].default_value = 1.0 / (1.1 * K)
    fine.inputs["Detail"].default_value = 4.0
    k.new(tco.outputs["Object"], fine.inputs["Vector"])
    base = n.new("ShaderNodeMix")
    base.data_type = "RGBA"
    k.new(flake.outputs[0], base.inputs[0])
    base.inputs[6].default_value = B.hexc(SP.get("iron2", "#25252c"))
    base.inputs[7].default_value = B.hexc(SP.get("iron", "#141418"))
    worn = n.new("ShaderNodeMix")
    worn.data_type = "RGBA"
    k.new(attr.outputs["Fac"], worn.inputs[0])
    k.new(base.outputs[2], worn.inputs[6])
    worn.inputs[7].default_value = B.hexc(SP.get("worn", "#9aa0ad"))
    ao = n.new("ShaderNodeAmbientOcclusion")
    ao.inputs["Distance"].default_value = 5.0 * K
    aom = n.new("ShaderNodeMix")
    aom.data_type = "RGBA"
    aom.blend_type = "MULTIPLY"
    aom.inputs[0].default_value = 0.65
    k.new(worn.outputs[2], aom.inputs[6])
    k.new(ao.outputs["AO"], aom.inputs[7])
    k.new(aom.outputs[2], bsdf.inputs["Base Color"])
    rough = n.new("ShaderNodeMapRange")
    k.new(flake.outputs[0], rough.inputs["Value"])
    rough.inputs["To Min"].default_value = SP.get("rough_metal", 0.36)
    rough.inputs["To Max"].default_value = SP.get("rough_scale", 0.72)
    rough2 = n.new("ShaderNodeMix")
    rough2.data_type = "FLOAT"
    k.new(attr.outputs["Fac"], rough2.inputs[0])
    k.new(rough.outputs[0], rough2.inputs[2])
    rough2.inputs[3].default_value = SP.get("rough_worn", 0.24)
    k.new(rough2.outputs[0], bsdf.inputs["Roughness"])
    met = n.new("ShaderNodeMapRange")
    k.new(flake.outputs[0], met.inputs["Value"])
    met.inputs["To Min"].default_value = 0.95
    met.inputs["To Max"].default_value = 0.45
    k.new(met.outputs[0], bsdf.inputs["Metallic"])
    bump = n.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = SP.get("grain", 0.18)
    bump.inputs["Distance"].default_value = 0.4 * K
    k.new(fine.outputs["Fac"], bump.inputs["Height"])
    k.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def fracture_material():
    m = bpy.data.materials.new("orb_fracture")
    m.use_nodes = True
    nt = m.node_tree
    n, k = nt.nodes, nt.links
    bsdf = n["Principled BSDF"]
    tco = n.new("ShaderNodeTexCoord")
    vor = n.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 1.0 / (SP.get("frac_cell", 2.2) * K)
    k.new(tco.outputs["Object"], vor.inputs["Vector"])
    col = n.new("ShaderNodeMix")
    col.data_type = "RGBA"
    k.new(vor.outputs["Distance"], col.inputs[0])
    col.inputs[6].default_value = B.hexc(SP.get("frac", "#7c818b"))
    col.inputs[7].default_value = B.hexc(SP.get("frac2", "#4a4e57"))
    k.new(col.outputs[2], bsdf.inputs["Base Color"])
    bsdf.inputs["Metallic"].default_value = 1.0
    bsdf.inputs["Roughness"].default_value = SP.get("frac_rough", 0.5)
    bump = n.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = SP.get("frac_bump", 0.35)
    bump.inputs["Distance"].default_value = 0.6 * K
    k.new(vor.outputs["Distance"], bump.inputs["Height"])
    k.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def plate_material():
    return B.plain_material("orb_plate", SP.get("plate", "#0b0b0e"), metal=0.6, rough=0.62)


# --------------------------------------------------------------- forms --

def bar_piece(name, centre, wire, closed, tips, seed, mats, contacts=()):
    SP["_wire_now"] = wire
    ob = tube(name, centre, wire, closed, res=SP.get("res", 12))
    for m in mats:
        ob.data.materials.append(m)
    if tips:
        fracture(ob, tips, wire, seed)
    cell, depth = SP.get("dent", [6.5, 0.9])
    f = max(0.45, min(1.0, wire / P(14)))   # (thin bars take smaller, shallower blows)
    ridge = hammer(ob, cell * K * f, depth * K * f, wire, seed)
    wear(ob, ridge, seed, contacts)
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def lug(at_deg, outer_pt, outward, mats, seed):
    """The forged eye the HUD's chain leaves from: a small ring lying in the casing's plane, welded on."""
    rr, rw = P(SP.get("lug_r", 6.5)), P(SP.get("lug_wire", 2.5))
    c = outer_pt + outward * (rr + rw * 0.2)
    pts = ellipse(rr, rr, 64)
    SP["_wire_now"] = rw
    ring_ = tube("lug", [p + c for p in pts], rw, True, res=8)
    for m in mats:
        ring_.data.materials.append(m)
    ridge = hammer(ring_, P(3.0), P(0.35), rw, seed + 9)
    wear(ring_, ridge, seed + 9)
    for p in ring_.data.polygons:
        p.use_smooth = True
    # the weld: a squat blob where the ring meets the bar
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=24, ring_count=12, location=outer_pt + outward * rw * 0.4)
    wd = bpy.context.active_object
    wd.scale = (rw * 1.9, rw * 1.9, rw * 1.3)
    wd.rotation_euler = (0, 0, math.atan2(outward.y, outward.x))
    wd.data.materials.append(mats[0])
    bpy.ops.object.shade_smooth()
    return c


def form_link(mats):
    r = P(SP.get("glass_r", 49))
    w = P(SP.get("wire", 14))
    b = r + w
    a = b * SP.get("aspect", 1.13)
    cl = superellipse(a, b, SP.get("square", 2.3), 420)
    th = math.radians(SP.get("break_deg", 48))
    at = min(cl, key=lambda p: abs(math.atan2(p.y, p.x) - th))
    SP["_wire_now"] = w
    path, tips = snap(cl, at, P(SP.get("gap", 20)) + 2 * w * 0.6, SP.get("splay", 25), P(SP.get("bend", 46)), lift=P(2.0))
    ob = bar_piece("link", path, w, False, tips, 11, mats)
    la = math.radians(SP.get("lug_deg", -38))
    # the outer point of the bar at that angle (the ellipse's outward normal)
    i = min(range(len(cl)), key=lambda j: abs(math.atan2(cl[j].y, cl[j].x) - la))
    p = cl[i]
    tg = cl[(i + 1) % len(cl)] - cl[i - 1]
    nrm = Vector((tg.y, -tg.x, 0)).normalized()
    eye = lug(la, p + nrm * w * 0.92, nrm, mats, 11)
    # the back plate, recessed (only its crescents beside the glass show)
    plate(a - w * 0.88, b - w * 0.85, w)   # (under the bar, not past it: where the break springs the bar away, the world shows)
    ext = (a + w + 2 * P(SP.get("lug_r", 6.5)) + 3 * P(2.5), b + w)
    return dict(open_c=(0.0, 0.0), open_r=r, eye=eye, ext=ext, tips=[t[0] for t in tips])


def plate(a, b, w):
    bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=1.0, depth=w * 0.3, location=(0, 0, -w * 0.75))
    pl = bpy.context.active_object
    pl.scale = (a, b, 1)
    pl.data.materials.append(plate_material())


def form_ring(mats):
    g = SP["ring"]
    r = P(SP.get("glass_r", 49))
    n = g.get("n", 7)
    Wd, wire = P(g["width"]), P(g["wire"])
    R = r + Wd / 2 - P(g.get("bite", 3.0))
    pitch = 2 * math.pi * R / n
    L = pitch + Wd * g.get("overlap", 0.55)
    a0 = math.radians(g.get("open_deg", 62.9))
    eye = None
    tipsall = []
    for i in range(n):
        a = a0 - i * 2 * math.pi / n
        cl = stadium(L, Wd, wire, n_end=40)
        SP["_wire_now"] = wire
        tips = []
        if i == 0:
            # the break on its outer side (+y in the link's own frame: the frame turns +x along the ring's tangent)
            path, tips = snap(cl, Vector((0, Wd / 2 - wire, 0)), P(g.get("gap", 13)) + wire * 1.2, SP.get("splay", 25),
                              P(g.get("bend", 22)), lift=P(1.5))
            closed = False
        else:
            path, closed = cl, True
        ob = bar_piece(f"ring{i}", path, wire, closed, tips, 20 + i, mats)
        tilt = 0.0 if i % 2 == 0 else math.radians(g.get("tilt", 48))
        # +y of the link's frame must face outward: z rotation a - 90deg puts +x along -tangent, +y outward
        place(ob, (math.cos(a) * R, math.sin(a) * R, 0), (tilt, 0, a - math.pi / 2))
        tipsall += [ob.matrix_world @ t[0] for t in tips]
        if i == g.get("lug_i", 2):
            out = Vector((math.cos(a), math.sin(a), 0))
            eye = lug(math.degrees(a), out * (R + Wd / 2 - wire * 0.2), out, mats, 30)
    plate(R, R, wire * 2.2)
    ext = (R / math.cos(math.pi / n) + Wd / 2 + 2 * P(SP.get("lug_r", 6.5)) + 3 * P(2.5),) * 2
    return dict(open_c=(0.0, 0.0), open_r=r, eye=eye, ext=ext, tips=tipsall)


def main():
    global K
    argv = sys.argv[sys.argv.index("--") + 1:]
    SP.update(json.load(open(argv[0], encoding="utf-8")))
    out = argv[1]
    px = SP.get("px", 6)
    K = px * U
    sc = B.reset()
    sc.cycles.samples = SP.get("samples", 128)
    sc.render.image_settings.color_depth = "8"
    B.world()
    B.suns()
    mats = [iron_material(), fracture_material()]
    geo = form_link(mats) if SP.get("form", "link") == "link" else form_ring(mats)
    # the glass's own light on the iron's inner flanks (cool, dim: the orb is lit glass, not fire), unseen itself,
    # so the bar's inside reads as iron round the glass rather than a black gap
    bpy.ops.mesh.primitive_circle_add(vertices=96, radius=geo["open_r"] * 0.97, fill_type="NGON", location=(0, 0, 0))
    gl = bpy.context.active_object
    gl.data.materials.append(B.emission_material("glass_light", SP.get("glass_light", "#8a96ae"), SP.get("glass_light_k", 0.9)))
    gl.visible_camera = False
    gl.visible_shadow = False
    ex, ey = geo["ext"]
    m = SP.get("margin", 4)
    W = 2 * int(math.ceil((ex / K + m) * px))
    H = 2 * int(math.ceil((ey / K + m) * px))
    W, H = W + W % 2, H + H % 2
    B.camera(W, H)
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    # render px (y down) from Blender units: the camera centred, U per render px
    to_px = lambda v: [round(W / 2 + v[0] / U, 2), round(H / 2 - v[1] / U, 2)]
    res = dict(size=[W, H], px=px, open_c=to_px(geo["open_c"]), open_r=round(geo["open_r"] / U, 2),
               eye=to_px(geo["eye"]), tips=[to_px(t) for t in geo["tips"]], spec=SP.get("form"))
    json.dump(res, open(os.path.splitext(out)[0] + ".json", "w"), indent=1)
    print("ORB", json.dumps(res))


if __name__ == "__main__":
    main()
