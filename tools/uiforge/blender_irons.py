"""Her irons: the HUD's forged cuffs, seats, sill, tags and lock (docs/design/HUD_V2.md 3, 5, 6),
modelled and rendered in Blender (Cycles) in the chain's own iron and house light: the world and
suns of blender_frames, iron_chain_material of blender_chainline (the tab chain's colours, so a
cuff and a link are one metal), heated_material of blender_links for the hot variants.

    blender -b -P tools/uiforge/blender_irons.py -- tools/uiforge/irons.json OUTDIR [piece ...]

Every piece is modelled in shown px (y down) and rendered at `scale` render px per shown px (the
file's 2x, 3x supersampled). Hammer facets are a seeded Voronoi tilt of the normal (flat facets, a
few deep), wear is the mesh's own convexity (edges and crowns rubbed to steel); no image textures.
The house key light keeps its low angle on the iron; the shadow on the world comes from a steeper
sun light-linked to the catcher alone, so it falls 3 to 5 px down and to the right. Writes raw
straight-alpha renders OUTDIR/<piece>_<layer>.png; irons.py downsamples and files them.
"""
import json
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Vector, noise

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import blender_frames as B  # noqa: E402
import blender_chainline as C  # noqa: E402
import blender_links as L  # noqa: E402

U = B.U
SPEC = {}
OUT = ""


class Stage:
    """One render set-up: house world and suns, an ortho camera over a canvas of W x H shown px."""

    def __init__(self, W, H):
        self.W, self.H, self.S = W, H, SPEC["scale"]
        sc = B.reset()
        sc.cycles.samples = SPEC["samples"]
        sc.render.image_settings.color_depth = "16"
        B.world()
        B.suns()
        self.sc = sc
        self.suns = [bpy.data.objects[n] for n in ("key", "fill", "rim")]
        B.camera(W * self.S, H * self.S)
        self.iron = bpy.data.collections.new("iron")
        self.catch = bpy.data.collections.new("catch")
        sc.collection.children.link(self.iron)
        sc.collection.children.link(self.catch)
        for o in self.suns:
            o.light_linking.receiver_collection = self.iron
        el = math.radians(SPEC["shadow"]["elevation"])
        d = Vector((-0.707 * math.cos(el), 0.707 * math.cos(el), math.sin(el)))
        ld = bpy.data.lights.new("shadow", "SUN")
        ld.energy, ld.angle = 4.0, math.radians(9)
        self.shadow_sun = bpy.data.objects.new("shadow", ld)
        sc.collection.objects.link(self.shadow_sun)
        self.shadow_sun.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
        self.shadow_sun.light_linking.receiver_collection = self.catch
        bpy.ops.mesh.primitive_plane_add(size=1)
        pl = bpy.context.active_object
        for c in pl.users_collection:
            c.objects.unlink(pl)
        self.catch.objects.link(pl)
        pl.scale = (W * self.S * U * 1.4, H * self.S * U * 1.4, 1)
        pl.is_shadow_catcher = True
        self.ground = pl

    def P(self, x, y, z=0.0):
        return B.P(x * self.S, y * self.S, self.W * self.S, self.H * self.S, z * self.S)

    def add(self, ob, catcher=False):
        for c in ob.users_collection:
            c.objects.unlink(ob)
        (self.catch if catcher else self.iron).objects.link(ob)
        return ob

    def render(self, name):
        self.sc.render.filepath = os.path.join(OUT, name + ".png")
        bpy.ops.render.render(write_still=True)


# ------------------------------------------------------------------ materials --

def facets(m, seed, scale=5.5, tilt=0.16, deep=2.6):
    """Hammer facets: each Voronoi cell tilts the normal its own way (flat facets with crisp
    edges between them); one cell in six of a coarser pattern is struck deep."""
    nt = m.node_tree
    n, k = nt.nodes, nt.links
    bsdf = n["Principled BSDF"]
    tc = n.new("ShaderNodeTexCoord")
    mp = n.new("ShaderNodeMapping")
    mp.inputs["Location"].default_value = (seed * 3.71, seed * 1.37, seed * 2.13)
    k.new(tc.outputs["Object"], mp.inputs["Vector"])
    vo = n.new("ShaderNodeTexVoronoi")
    vo.inputs["Scale"].default_value = scale
    k.new(mp.outputs[0], vo.inputs["Vector"])
    vd = n.new("ShaderNodeTexVoronoi")
    vd.inputs["Scale"].default_value = scale * 0.45
    k.new(mp.outputs[0], vd.inputs["Vector"])
    sep = n.new("ShaderNodeSeparateColor")
    k.new(vd.outputs["Color"], sep.inputs[0])
    gt = n.new("ShaderNodeMath")
    gt.operation = "GREATER_THAN"
    gt.inputs[1].default_value = 0.83
    k.new(sep.outputs[0], gt.inputs[0])
    amt = n.new("ShaderNodeMath")
    amt.operation = "MULTIPLY_ADD"
    amt.inputs[1].default_value = tilt * (deep - 1)
    amt.inputs[2].default_value = tilt
    k.new(gt.outputs[0], amt.inputs[0])
    sub = n.new("ShaderNodeVectorMath")
    sub.operation = "SUBTRACT"
    sub.inputs[1].default_value = (0.5, 0.5, 0.5)
    k.new(vo.outputs["Color"], sub.inputs[0])
    scl = n.new("ShaderNodeVectorMath")
    scl.operation = "SCALE"
    k.new(sub.outputs[0], scl.inputs[0])
    k.new(amt.outputs[0], scl.inputs["Scale"])
    geo = n.new("ShaderNodeNewGeometry")
    add = n.new("ShaderNodeVectorMath")
    add.operation = "ADD"
    k.new(geo.outputs["Normal"], add.inputs[0])
    k.new(scl.outputs[0], add.inputs[1])
    nrm = n.new("ShaderNodeVectorMath")
    nrm.operation = "NORMALIZE"
    k.new(add.outputs[0], nrm.inputs[0])
    k.new(nrm.outputs[0], bsdf.inputs["Normal"])
    return m


def iron(name, seed, state="", **kw):
    """The chain's iron (cold) or its heated states, faceted."""
    if state == "hot":
        m = L.heated_material(name, "#2a0602", "#ff7a28", 1.5)
    elif state == "warm":
        m = L.heated_material(name, "#100200", "#7a1404", 0.75)
    else:
        m = C.iron_chain_material()
        m.name = name
    return facets(m, seed, **kw)


def plate(name, color, seed):
    """A dark iron plate (a seat's floor): the chain's iron in a darker colour, less worn."""
    keep = dict(C.SPEC)
    C.SPEC.update({"iron": color, "rust": "#1a120c", "worn": "#5a5660", "worn_rough": 0.35})
    m = iron(name, seed, tilt=0.07)
    C.SPEC.clear()
    C.SPEC.update(keep)
    return m


def glow_material():
    m = B.emission_material("glow", "#ffffff", 6.0)
    return m


# ------------------------------------------------------------------- geometry --

def mesh_object(st, name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return st.add(ob)


def sweep(st, name, path, normals, profile, mod=None):
    """A closed profile [(d, z)] (d outward from the path, shown px) swept round a closed path."""
    bm = bmesh.new()
    rows = []
    for i, ((x, y), (nx, ny)) in enumerate(zip(path, normals)):
        row = []
        for j, (d, z) in enumerate(profile):
            if mod:
                d, z = mod(i, x, y, d, z)
            row.append(bm.verts.new(st.P(x + nx * d, y + ny * d, z)))
        rows.append(row)
    N, M = len(rows), len(profile)
    for i in range(N):
        for j in range(M):
            bm.faces.new((rows[i][j], rows[(i + 1) % N][j], rows[(i + 1) % N][(j + 1) % M], rows[i][(j + 1) % M]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_object(st, name, bm)


def to_mesh(ob):
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.selected_objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.ops.object.convert(target="MESH")
    o = bpy.context.view_layer.objects.active
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return o


def slab(st, name, pts, z0, z1, bevel, holes=()):
    """A flat forged piece of any outline (shown px), z0 to z1, its edges rounded by `bevel`."""
    S = st.S
    sp = [[(x * S, y * S) for x, y in B.densify(pts, 0.6)]] + [[(x * S, y * S) for x, y in h] for h in holes]
    ob = B.curve_object(name, sp, st.W * S, st.H * S, extrude=(z1 - z0) / 2 * S - bevel * S,
                        bevel=bevel * S, z=(z0 + z1) / 2 * S, res=5)
    return st.add(to_mesh(ob))


def circle(cx, cy, r, n=48, a0=0.0):
    return [(cx + r * math.cos(a0 + 2 * math.pi * i / n), cy + r * math.sin(a0 + 2 * math.pi * i / n)) for i in range(n)]


def tab(cx, cy, ang, r0, r1, w):
    """A tongue of iron from radius r0 out to r1 along `ang` (deg, y down), rounded at its end."""
    a = math.radians(ang)
    ux, uy, vx, vy = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
    h = w / 2
    e = r1 - h
    pts = [(cx + ux * r0 - vx * h, cy + uy * r0 - vy * h)]
    for i in range(25):
        t = -math.pi / 2 + math.pi * i / 24
        pts.append((cx + ux * (e + h * math.cos(t)) + vx * h * math.sin(t), cy + uy * (e + h * math.cos(t)) + vy * h * math.sin(t)))
    pts.append((cx + ux * r0 + vx * h, cy + uy * r0 + vy * h))
    return pts


def dome(st, name, x, y, z, r, flat=0.55, mat=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40, ring_count=20, radius=r * st.S * U, location=st.P(x, y, z))
    o = bpy.context.active_object
    o.scale.z = flat
    bpy.ops.object.transform_apply(scale=True)
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    if mat:
        o.data.materials.append(mat)
    return st.add(o)


def wear(st, ob, k0=0.22, k1=0.85, ztop=None, zw=0.0, seed=0):
    """Rubbed bright where the iron is convex (its edges, a rivet's crown), and on its highest
    face if `ztop` (shown px) is given; broken up by noise. Written as the colour 'wear' that
    iron_chain_material reads."""
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.normal_update()
    S = st.S
    kap = []
    for v in bm.verts:
        s, c = 0.0, 0
        for e in v.link_edges:
            d = v.co - e.other_vert(v).co
            Ld = d.length
            if Ld > 1e-9:
                s += v.normal.dot(d) / (Ld * Ld)
                c += 1
        kap.append(2 * s / max(c, 1) * U * S)          # 1 / radius, in 1/shown px
    for _ in range(2):
        nk = list(kap)
        for v in bm.verts:
            nb = [kap[e.other_vert(v).index] for e in v.link_edges]
            if nb:
                nk[v.index] = 0.5 * kap[v.index] + 0.5 * sum(nb) / len(nb)
        kap = nk
    if "wear" not in me.color_attributes:
        me.color_attributes.new("wear", "FLOAT_COLOR", "POINT")
    ca = me.color_attributes["wear"]
    off = Vector((seed * 7.1, seed * 3.3, seed * 5.7))
    for v in bm.verts:
        w = min(1.0, max(0.0, (kap[v.index] - k0) / (k1 - k0)))
        if ztop is not None:
            z = v.co.z / (U * S)
            w = max(w, zw * min(1.0, max(0.0, (z - (ztop - 1.0)) / 1.0)))
        nz = noise.noise(v.co * (1.0 / (U * S * 2.2)) + off)
        w = w * (0.6 + 0.4 * (nz + 1) / 2) * (0.75 + 0.25 * math.copysign(1, nz))
        ca.data[v.index].color = (w ** 1.2, w ** 1.2, w ** 1.2, 1)
    bm.free()


# --------------------------------------------------------------------- pieces --

def band_profile(ri, ro, crown, chamfer=2.6):
    """A manacle's band, inner radius ri to outer ro: the glass meets its inner wall `chamfer` px
    below a chamfer, then a half-round face to its crown, a rounded foot on the outside."""
    w = ro - ri
    rc, hw = ri + w * 0.58, w * 0.42
    zb = crown * 0.2
    pr = [(ri, 0.0), (ri, chamfer * 0.9), (ri + 0.25, chamfer)]
    zc = zb + (crown - zb) * 0.45
    pr.append((ri + w * 0.14, zc))
    for i in range(1, 25):
        t = math.pi * (1 - i / 24)
        r = rc + hw * math.cos(t)
        z = zb + (crown - zb) * math.sin(t)
        if r > ri + w * 0.16:
            pr.append((r, z))
    pr += [(ro - 0.1, zb * 0.6), (ro, zb * 0.25), (ro - 0.3, 0.0), ((ri + ro) / 2, 0.0)]
    return pr


def ring_band(st, name, cx, cy, ri, ro, crown, seams=(), seed=0, n=1800):
    pr = band_profile(ri, ro, crown, chamfer=crown * 0.37)
    rm = (ri + ro) / 2
    prof = [(r - rm, z) for r, z in pr]
    path, nrm = [], []
    for i in range(n):
        a = 2 * math.pi * i / n
        path.append((cx + rm * math.cos(a), cy + rm * math.sin(a)))
        nrm.append((math.cos(a), math.sin(a)))
    rnd = random.Random(seed)
    ph = [rnd.uniform(0, 6.28) for _ in range(4)]

    def mod(i, x, y, d, z):
        a = 2 * math.pi * i / n
        # hand-forged: the outer edge and crown wander a little round the band
        wob = 0.22 * math.sin(3 * a + ph[0]) + 0.14 * math.sin(7 * a + ph[1])
        hz = 0.25 * math.sin(5 * a + ph[2]) + 0.12 * math.sin(11 * a + ph[3])
        f = max(0.0, (d + (rm - ri)) / (ro - ri))       # 0 at the inner wall, 1 at the outer edge
        d2 = d + wob * f
        z2 = z * (1 + hz / max(crown, 1) * f)
        for sa in seams:                                 # a fine cut across the band
            da = math.degrees(math.atan2(math.sin(a - math.radians(sa)), math.cos(a - math.radians(sa)))) * math.pi / 180 * (rm + d)
            if abs(da) < 0.55 and z > 0.3:
                z2 -= 1.3 * (1 - abs(da) / 0.55) ** 1.5 * min(1, z2 / 2)
        return d2, z2

    return sweep(st, name, path, nrm, prof, mod)


def cuff(name, big=True):
    cs = SPEC["cuff"] if big else SPEC["small"]
    W, H = cs["canvas"]
    st = Stage(W, H)
    cx, cy = cs["center"]
    ri, ro = cs["glass_r"], cs["outer_r"]
    seed = SPEC["seed"] + (0 if big else 5)
    mat = iron("band", seed, scale=5.5 if big else 7.5)
    parts = []
    if big:
        hg, jt, lg = cs["hinge"], cs["joint"], cs["lug"]
        band = ring_band(st, "band", cx, cy, ri, ro, 7.0, seams=(hg["angle"], jt["angle"]), seed=seed, n=2200)
        wear(st, band, ztop=7.0, zw=0.55, seed=1)
        band.data.materials.append(mat)
        parts.append(band)
        # the hinge at 9 o'clock: three knuckles and a peened pin
        hx = cx - hg["r"]
        kr = hg["knuckle_r"]
        Lh = hg["length"]
        kl = (Lh - 2 * 0.9) / 3
        for i in range(3):
            y0 = cy - Lh / 2 + i * (kl + 0.9)
            bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=kr * st.S * U, depth=kl * st.S * U,
                                                location=st.P(hx, y0 + kl / 2, kr))
            o = bpy.context.active_object
            o.rotation_euler = (math.pi / 2, 0, 0)
            bpy.ops.object.transform_apply(rotation=True)
            bv = o.modifiers.new("b", "BEVEL")
            bv.width, bv.segments = 0.7 * st.S * U, 4
            sub = o.modifiers.new("s", "SUBSURF")
            sub.levels = sub.render_levels = 1
            bpy.ops.object.modifier_apply(modifier="b")
            bpy.ops.object.modifier_apply(modifier="s")
            st.add(o)
            wear(st, o, seed=2 + i)
            o.data.materials.append(iron(f"knuckle{i}", seed + 3 + i))
            parts.append(o)
        for sy in (-1, 1):
            p = dome(st, f"pin{sy}", hx, cy + sy * (Lh / 2 + 0.2), kr, 1.9, flat=1.0, mat=None)
            p.scale.y = 0.6
            wear(st, p, seed=9)
            p.data.materials.append(mat)
            parts.append(p)
        # the lug: a strap under both bands toward the draught, riveted through each
        dx, dy = lg["to"]
        la = math.degrees(math.atan2(dy, dx))
        dist = math.hypot(dx, dy)
        strap = slab(st, "lug", tab(cx, cy, la, ro - 9, dist - SPEC["small"]["outer_r"] + 6, lg["width"]), 0.0, 3.2, 1.0)
        wear(st, strap, seed=4)
        strap.data.materials.append(iron("lug", seed + 7))
        parts.append(strap)
        rv = dome(st, "lugrivet", cx + lg["rivet_r"] * math.cos(math.radians(la)), cy + lg["rivet_r"] * math.sin(math.radians(la)),
                  6.4, 2.3, flat=0.6)
        wear(st, rv, seed=5)
        rv.data.materials.append(iron("rivet", seed + 8, tilt=0.05))
        parts.append(rv)
        # the joint, 32 deg below level on the inner side: two ears, a domed rivet
        ja = jt["angle"]
        back = slab(st, "ear_back", tab(cx, cy, ja, ro - 4, jt["rivet_r"] + jt["ear_w"] / 2, jt["ear_w"]), 0.0, 2.0, 0.6)
        wear(st, back, seed=6)
        back.data.materials.append(iron("earb", seed + 9))
        parts.append(back)
        front = slab(st, "ear_front", tab(cx, cy, ja, ro - 8, jt["rivet_r"] + jt["ear_w"] / 2, jt["ear_w"] * 1.04), 5.3, 7.6, 0.8)
        wear(st, front, seed=7)
        front.data.materials.append(iron("earf", seed + 10))
        jx, jy = cx + jt["rivet_r"] * math.cos(math.radians(ja)), cy + jt["rivet_r"] * math.sin(math.radians(ja))
        jr = dome(st, "jrivet", jx, jy, 7.5, jt["rivet"], flat=0.55)
        wear(st, jr, seed=8)
        jr.data.materials.append(iron("jrivet", seed + 11, tilt=0.05))
        # the first link of the chain, there only to catch the front ear's shadow
        lk, _ = C.link_mesh("link0", 24 * st.S * U, 15.2 * st.S * U, 2.56 * st.S * U)
        lk.location = st.P(jx + 4.4, jy, 2.56)
        st.add(lk, catcher=True)
        lk.is_shadow_catcher = True
        glow = slab(st, "glowdisc", circle(cx, cy, ri - 1.5, 96), 0.6, 1.0, 0.1)
        glow.data.materials.append(glow_material())
        glow.visible_camera = False
        glow.visible_shadow = False
        glow.hide_render = True
        # cuff: band, hinge, lug, back ear (the front ear and its rivet unseen and casting nothing)
        for o in (front, jr, lk):
            o.hide_render = True
        st.render(name)
        # cuff_front: the front ear and rivet alone, the band held out under them, their shadow on the link
        for o in (front, jr, lk):
            o.hide_render = False
        for o in parts:
            o.is_holdout = True
        st.render(name + "_front")
        # cuff_glow: only the light of the glass on the iron (house lights and world off)
        for o in (front, jr, lk):
            o.hide_render = True
        for o in parts:
            o.is_holdout = False
        for o in st.suns:
            o.hide_render = True
        st.shadow_sun.hide_render = True
        bpy.context.scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.0
        glow.hide_render = False
        st.ground.hide_render = True
        st.render(name + "_glow")
    else:
        band = ring_band(st, "band", cx, cy, ri, ro, 4.4, seed=seed, n=1200)
        wear(st, band, ztop=4.4, zw=0.55, seed=1)
        band.data.materials.append(mat)
        la = math.degrees(math.atan2(-SPEC["cuff"]["lug"]["to"][1], -SPEC["cuff"]["lug"]["to"][0]))
        rr = (ri + ro) / 2 + 0.4
        rv = dome(st, "lugrivet", cx + rr * math.cos(math.radians(la)), cy + rr * math.sin(math.radians(la)), 4.0, 1.9, flat=0.6)
        wear(st, rv, seed=5)
        rv.data.materials.append(iron("rivet", seed + 8, tilt=0.05))
        ring = tag_ring(st, cx, cy + ro - 2.2, cy + cs["ring_hole_y"] + 0.9, seed)
        st.render(name)


def tag_ring(st, x, y0, y1, seed):
    """A small ring on edge (its plane across the screen, turned 35 deg), from y0 to y1."""
    R = (y1 - y0) / 2
    bpy.ops.mesh.primitive_torus_add(major_radius=R * st.S * U, minor_radius=0.85 * st.S * U, major_segments=64,
                                     minor_segments=16, location=st.P(x, (y0 + y1) / 2, 2.2))
    o = bpy.context.active_object
    o.rotation_euler = (0, math.radians(90 - 35), 0)
    bpy.ops.object.transform_apply(rotation=True)
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    st.add(o)
    wear(st, o, seed=seed)
    o.data.materials.append(iron("ring", seed + 4, tilt=0.04))
    return o


def rrect(x0, y0, x1, y1, r, n=10):
    return B.outline(x0, y0, x1, y1, radius=r, n_round=n)


def seat(k, state):
    sp = SPEC["seat"]
    cw = sp["canvas"]
    st = Stage(cw, cw)
    ax, ay = sp["at"]
    s, f = sp["size"], sp["face"]
    rnd = random.Random(100 + k)
    # path: the face's middle line, a hand-forged square (sides bowed a little, corners each their own)
    m = f / 2
    x0, y0, x1, y1 = ax + m, ay + m, ax + s - m, ay + s - m
    pts = B.densify(B.outline(x0, y0, x1, y1, corners=[rnd.uniform(2.4, 3.6) for _ in range(4)], n_round=14), 0.12)
    cxs, cys = (x0 + x1) / 2, (y0 + y1) / 2
    bow = [rnd.uniform(-0.35, 0.35) for _ in range(4)]
    path = []
    for (x, y) in pts:
        u, v = (x - cxs) / ((x1 - x0) / 2), (y - cys) / ((y1 - y0) / 2)
        path.append((x + bow[0] * (1 - v * v) * (1 if u > 0 else -1) * (abs(u) > 0.95),
                     y + bow[1] * (1 - u * u) * (1 if v > 0 else -1) * (abs(v) > 0.95)))
    n = len(path)
    nrm = []
    for i in range(n):
        (xa, ya), (xb, yb) = path[i - 1], path[(i + 1) % n]
        tx, ty = xb - xa, yb - ya
        L_ = math.hypot(tx, ty) or 1
        nrm.append((ty / L_, -tx / L_))
    # outward: the normal must point away from the middle
    if (path[0][0] - cxs) * nrm[0][0] + (path[0][1] - cys) * nrm[0][1] < 0:
        nrm = [(-a, -b) for a, b in nrm]
    top = 4.9
    prof = [(m, 0.0), (m, top - 1.3)]
    for i in range(1, 9):
        t = i / 8 * math.pi / 2
        prof.append((m - 0.9 + 0.9 * math.cos(t), top - 1.3 + 1.3 * math.sin(t) * 0.95))
    for i in range(1, 16):
        d = (m - 0.9) - (2 * m - 1.6) * i / 16
        prof.append((d, top - 0.06 * math.sin(math.pi * i / 16) - 0.05))
    for i in range(1, 7):
        t = i / 6 * math.pi / 2
        prof.append((-m + 0.7 - 0.7 * math.sin(t), top - 0.05 - 0.7 * (1 - math.cos(t))))
    prof += [(-m, 1.6), (-m, 0.0), (0.0, 0.0)]
    dim = []
    dx0, dx1 = ax + 12.5, ax + s - 12.5
    for i in range(sp["dimples"]):
        dim.append((dx0 + (dx1 - dx0) * i / (sp["dimples"] - 1) + rnd.uniform(-0.25, 0.25), ay + s - m + rnd.uniform(-0.15, 0.15)))

    def mod(i, x, y, d, z):
        px, py = x + nrm[i][0] * d, y + nrm[i][1] * d
        for (qx, qy) in dim:
            r2 = (px - qx) ** 2 + (py - qy) ** 2
            if r2 < 1.2 ** 2 and z > top - 0.6:
                z -= 0.6 * math.sqrt(1 - r2 / 1.44)
        return d, z

    col = sweep(st, "collar", path, nrm, prof, mod)
    wear(st, col, k0=0.3, k1=1.0, seed=k)
    col.data.materials.append(iron("collar", 40 + k, state=state, scale=7.0, tilt=0.13))
    fl = slab(st, "floor", rrect(ax + f - 0.6, ay + f - 0.6, ax + s - f + 0.6, ay + s - f + 0.6, 1.0), 0.0, 1.0, 0.3)
    fl.data.materials.append(plate("floor", "#0c0b0e", 60 + k))
    tagn = {"": "seat", "hot": "seat_hot"}[state]
    st.render(f"{tagn}_{k}")
    if state == "":
        fl.is_holdout = True
        st.render(f"seat_collar_{k}")
    return dim


def sill(N):
    sp = SPEC["sill"]
    Lx = sp["pitch"] * N + sp["over"]
    st = Stage(Lx + 5, 10)
    rnd = random.Random(200 + N)
    pts = B.densify(rrect(0.5, 1.0, Lx - 0.5, 1.0 + sp["height"], 1.9), 0.5)
    pts = [(x, y + 0.12 * math.sin(x / 37.0 + N)) for x, y in pts]
    ob = slab(st, "sill", pts, 0.0, 2.4, 0.8)
    wear(st, ob, k0=0.3, k1=1.0, seed=N)
    ob.data.materials.append(iron("sill", 70 + N, scale=6.5))
    for i in range(N - 1):
        x = sp["over"] + sp["seat"] + 3 + sp["pitch"] * i + rnd.uniform(-0.2, 0.2)
        r = dome(st, f"r{i}", x, 3.5, 2.4, 1.55, flat=0.6)
        wear(st, r, seed=i)
        r.data.materials.append(iron(f"rv{i}", 80 + i, tilt=0.05))
    st.render(f"sill_{N}")


def tag(w):
    sp = SPEC["tag"]
    h = sp["height"]
    ax, ay = sp["at"]
    st = Stage(w + 6, h + 6)
    hx, hy = ax + w * sp["hole"][0], ay + sp["hole"][1]
    ob = slab(st, "tag", rrect(ax, ay, ax + w, ay + h, 2.4), 0.3, 1.9, 0.55, holes=[circle(hx, hy, 1.45, 24)[::-1]])
    wear(st, ob, k0=0.3, k1=1.0, seed=w)
    ob.data.materials.append(iron("tag", 90 + w, scale=8.0, tilt=0.1))
    st.render(f"tag_{w}")


def ring_only():
    st = Stage(12, 16)
    tag_ring(st, 6, 1.5, 12.5, 3)
    st.render("tag_ring")


def lock(state):
    sp = SPEC["lock"]
    W, H = sp["canvas"]
    st = Stage(W, H)
    ax, ay = sp["anchor"]
    bw, bh = sp["body"]
    open_ = state == "open"
    drop = 5.0 if open_ else 0.0
    by = sp["body_top"] + drop
    x0, x1 = ax - bw / 2, ax + bw / 2
    body_pts = B.outline(x0, by, x1, by + bh, corners=[8, 8, 13, 13], n_round=16)
    kh = circle(ax, by + 19.5, 1.75, 24)[::-1]
    slot = [(ax - 0.7, by + 20.2), (ax + 0.7, by + 20.2), (ax + 0.9, by + 24.2), (ax - 0.9, by + 24.2)][::-1]
    body = slab(st, "body", body_pts, 1.5, 7.5, 2.0, holes=[kh])
    wear(st, body, k0=0.25, k1=0.9, seed=1)
    body.data.materials.append(iron("body", 120, state="hot" if state == "hot" else "", scale=6.0))
    core = slab(st, "core", circle(ax, by + 21.5, 3.6, 24), 2.0, 3.0, 0.2)
    core.data.materials.append(B.plain_material("dark", "#050404", 0.2, 0.8))
    slt = slab(st, "slot", slot, 6.6, 7.7, 0.1)
    slt.data.materials.append(B.plain_material("dark2", "#060505", 0.2, 0.8))
    # the shackle: a U of round bar, its apex up behind the link's upper bar, its legs down in
    # front of the lower one into the body
    Rs, bar = 7.0, 1.85
    apex = ay - 4.0
    pts = []
    ly = by - 2.5 if open_ else by + 3       # sprung, the short leg stands clear of the body
    for i in range(40):                      # left leg up
        y = ly - (ly - (apex + Rs)) * i / 40
        pts.append((ax - Rs, y))
    for i in range(41):                      # the arc over the top
        t = math.pi + math.pi * i / 40
        pts.append((ax + Rs * math.cos(t), apex + Rs + Rs * math.sin(t)))
    for i in range(1, 41):                   # right leg down
        y = apex + Rs + (by + 4 - (apex + Rs)) * i / 40
        pts.append((ax + Rs, y))
    cu = bpy.data.curves.new("shackle", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = bar * st.S * U
    cu.bevel_resolution = 6
    s_ = cu.splines.new("POLY")
    s_.points.add(len(pts) - 1)
    for i, (x, y) in enumerate(pts):
        yy = y
        zz = 2.6 + 3.2 * math.sin(math.pi / 2 * min(1.0, max(0.0, (yy - apex) / 8.0))) - 1.4 * max(0.0, (yy - apex - 8) / 10)
        v = st.P(x, y, zz)
        s_.points[i].co = (v.x, v.y, v.z, 1)
    sh = bpy.data.objects.new("shackle", cu)
    bpy.context.scene.collection.objects.link(sh)
    sh = st.add(to_mesh(sh))
    if open_:
        # sprung: the short left leg out of the body, the shackle turned 35 deg on its long leg
        piv = st.P(ax + Rs, 0, 0)
        for v in sh.data.vertices:
            p = v.co - Vector((piv.x, 0, 0))
            a = math.radians(35)
            v.co = Vector((piv.x + p.x * math.cos(a), p.y, p.z - p.x * math.sin(a) * 0.6))
    wear(st, sh, k0=0.3, k1=0.9, seed=2)
    sh.data.materials.append(iron("shackle", 121, state="warm" if state == "hot" else "", tilt=0.06))
    # the chain's middle link (face_K at 4/5), held out: where its upper bar lies over the
    # shackle the lock is cut away, and the lock's shadow falls on it
    rnd = random.Random(5)
    K = sp["link_variant"]
    for _ in range(K):
        for _ in range(6):
            rnd.uniform(0, 1)
    sl, sw = 1 + rnd.uniform(-0.05, 0.05), 1 + rnd.uniform(-0.07, 0.07)
    wf = 1 + rnd.uniform(-0.06, 0.06)
    tilt = rnd.uniform(-0.14, 0.14)
    ry, rz = rnd.uniform(-0.05, 0.05), rnd.uniform(-0.05, 0.05)
    lk, _ = C.link_mesh("mid", 24 * sl * st.S * U, 15.2 * sw * st.S * U, 2.56 * wf * st.S * U)
    lk.rotation_euler = (tilt, ry, rz)
    lk.location = st.P(ax, ay, 2.56 * wf)
    st.add(lk, catcher=True)
    lk.is_shadow_catcher = True
    lk.is_holdout = False
    st.render({"": "lock", "open": "lock_open", "hot": "lock_hot"}[state])


def main():
    global OUT
    argv = sys.argv[sys.argv.index("--") + 1:]
    SPEC.update(json.load(open(argv[0], encoding="utf-8")))
    if os.environ.get("IRONS_SAMPLES"):
        SPEC["samples"] = int(os.environ["IRONS_SAMPLES"])
    OUT = argv[1]
    os.makedirs(OUT, exist_ok=True)
    C.SPEC.update(SPEC["material"])
    want = set(argv[2:]) or {"cuff", "small", "seats", "sill", "tags", "lock"}
    if "cuff" in want:
        cuff("cuff", True)
    if "small" in want:
        cuff("cuff_small", False)
    if "seats" in want:
        dims = {}
        for k in SPEC["seat"]["variants"]:
            dims[k] = seat(k, "")
            seat(k, "hot")
        json.dump({str(k): [[round(x, 2), round(y, 2)] for x, y in v] for k, v in dims.items()},
                  open(os.path.join(OUT, "dimples.json"), "w"), indent=1)
    if "sill" in want:
        for N in SPEC["sill"]["counts"]:
            sill(N)
    if "tags" in want:
        for w in SPEC["tag"]["widths"]:
            tag(w)
        ring_only()
    if "lock" in want:
        for s in ("", "open", "hot"):
            lock(s)


if __name__ == "__main__":
    main()
