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
        # the house light with its cool strip low right turned down (SPEC light), so the iron's
        # lower right falls into its dark crescent instead of a second bright rim
        lt = SPEC.get("light", {})
        for nd in bpy.context.scene.world.node_tree.nodes:
            if nd.type == "MATH" and nd.operation == "MULTIPLY" and abs(nd.inputs[1].default_value - 2.5) < 1e-6:
                nd.inputs[1].default_value *= lt.get("rim_world", 1.0)
        self.suns[2].data.energy *= lt.get("rim_sun", 1.0)
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

def facets(m, seed, cell=9.0, tilt=0.085, deep=2.2):
    """Hammer facets: each Voronoi cell (about `cell` shown px across, so at 1080 they read as
    forged planes, never as grain) tilts the normal its own way (flat facets with crisp edges
    between them); one cell in six of a coarser pattern is struck deep."""
    scale = 1.0 / (cell * SPEC["scale"] * U)
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


def body_heat_material(name, seed, strength=1.0):
    """A thick iron body warming through (the lock as the chain nears full): still the chain's iron
    with its sheen, a dull red coming up from its core and fading toward its edges, which cool
    first, broken by dark scale; only the hottest of it reaches the leading links' orange."""
    m = C.iron_chain_material()
    m.name = name
    nt = m.node_tree
    n, k = nt.nodes, nt.links
    bsdf = n["Principled BSDF"]
    gen = n.new("ShaderNodeTexCoord")
    sep = n.new("ShaderNodeSeparateXYZ")
    k.new(gen.outputs["Generated"], sep.inputs[0])
    # the core: 1 in the middle of the face, 0 at its edge (generated coords span the body)
    dx = n.new("ShaderNodeMath")
    dx.operation = "SUBTRACT"
    dx.inputs[1].default_value = 0.5
    k.new(sep.outputs["X"], dx.inputs[0])
    dy = n.new("ShaderNodeMath")
    dy.operation = "SUBTRACT"
    dy.inputs[1].default_value = 0.56
    k.new(sep.outputs["Y"], dy.inputs[0])
    cmb = n.new("ShaderNodeCombineXYZ")
    k.new(dx.outputs[0], cmb.inputs["X"])
    k.new(dy.outputs[0], cmb.inputs["Y"])
    ln = n.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    k.new(cmb.outputs[0], ln.inputs[0])
    core = n.new("ShaderNodeMapRange")
    core.interpolation_type = "SMOOTHSTEP"
    core.inputs["From Min"].default_value = 0.52
    core.inputs["From Max"].default_value = 0.08
    k.new(ln.outputs["Value"], core.inputs["Value"])
    crust = scale_crust(n, k, seed)
    heat = n.new("ShaderNodeMath")
    heat.operation = "MULTIPLY"
    k.new(core.outputs[0], heat.inputs[0])
    k.new(crust, heat.inputs[1])
    heat_ramp(n, k, heat.outputs[0], bsdf, strength,
              [(0.0, "#0c0100"), (0.5, "#5a0e04"), (0.85, "#c84a18"), (1.0, "#ff7a28")])
    return facets(m, seed, cell=8.0, tilt=0.1)


def scale_crust(n, k, seed, px=7.0):
    """Forge scale on hot iron: a few broad dark flakes over the glow, irregular (a low-detail,
    distorted noise some `px` shown px across, cut hard), never an even pebble of cells."""
    tco = n.new("ShaderNodeTexCoord")
    mp = n.new("ShaderNodeMapping")
    mp.inputs["Location"].default_value = (seed * 1.7, seed * 2.9, 0)
    k.new(tco.outputs["Object"], mp.inputs["Vector"])
    nz = n.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 1.0 / (px * SPEC["scale"] * U)
    nz.inputs["Detail"].default_value = 1.5
    nz.inputs["Distortion"].default_value = 0.8
    k.new(mp.outputs[0], nz.inputs["Vector"])
    crust = n.new("ShaderNodeMapRange")
    k.new(nz.outputs["Fac"], crust.inputs["Value"])
    crust.inputs["From Min"].default_value = 0.38
    crust.inputs["From Max"].default_value = 0.5
    crust.inputs["To Min"].default_value = 0.35
    crust.inputs["To Max"].default_value = 1.0
    return crust.outputs[0]


def heat_ramp(n, k, heat, bsdf, strength, stops=None):
    """Heat (0 to 1) to the forge's colours, as emission: black-red, dull red, the leading
    links' orange, and at the top of the ramp yellow-white."""
    stops = stops or [(0.0, "#0c0100"), (0.45, "#5e1004"), (0.78, "#d8521a"), (1.0, "#ffb050")]
    ramp = n.new("ShaderNodeValToRGB")
    e = ramp.color_ramp.elements
    e[0].position, e[0].color = stops[0][0], B.hexc(stops[0][1])
    e[1].position, e[1].color = stops[-1][0], B.hexc(stops[-1][1])
    for p, c in stops[1:-1]:
        e.new(p).color = B.hexc(c)
    k.new(heat, ramp.inputs["Fac"])
    k.new(ramp.outputs["Color"], bsdf.inputs["Emission Color"])
    st = n.new("ShaderNodeMath")
    st.operation = "MULTIPLY"
    st.inputs[1].default_value = strength
    k.new(heat, st.inputs[0])
    k.new(st.outputs[0], bsdf.inputs["Emission Strength"])


def collar_heat_material(name, seed, strength=1.6):
    """A seat's collar heated from the seat inward (it can evolve): the chain's iron, its emission
    from the vertex colour 'heat' (0 at the collar's outer edge, 1 at its inner wall) broken by
    forge scale: dull red outside, the leading links' orange across the face, yellow-white at the
    inner edge. The iron's facets and sheen keep."""
    m = C.iron_chain_material()
    m.name = name
    nt = m.node_tree
    n, k = nt.nodes, nt.links
    bsdf = n["Principled BSDF"]
    at = n.new("ShaderNodeAttribute")
    at.attribute_name = "heat"
    crust = scale_crust(n, k, seed, px=6.0)
    # the scale lies on the cooler outer iron; the inner edge burns through it
    mix = n.new("ShaderNodeMix")
    mix.data_type = "FLOAT"
    k.new(at.outputs["Fac"], mix.inputs[0])
    k.new(crust, mix.inputs[2])
    mix.inputs[3].default_value = 1.0
    heat = n.new("ShaderNodeMath")
    heat.operation = "MULTIPLY"
    k.new(at.outputs["Fac"], heat.inputs[0])
    k.new(mix.outputs[0], heat.inputs[1])
    heat_ramp(n, k, heat.outputs[0], bsdf, strength,
              [(0.0, "#0a0100"), (0.3, "#4a0c03"), (0.62, "#c8461a"), (0.86, "#ffa040"), (1.0, "#fff0c0")])
    return facets(m, seed, cell=8.0, tilt=0.085)


def plate(name, color, seed):
    """A dark iron plate (a seat's floor): the chain's iron in a darker colour, less worn."""
    keep = dict(C.SPEC)
    C.SPEC.update({"iron": color, "rust": "#1a120c", "worn": "#5a5660", "worn_rough": 0.35})
    m = iron(name, seed, tilt=0.05)
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


def wear(st, ob, k0=0.22, k1=0.85, ztop=None, zw=0.0, seed=0, zlow=None):
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
        if zlow is not None:                        # nothing rubs down in the hollows
            w *= min(1.0, max(0.0, (v.co.z / (U * S) - zlow) / 1.2))
        # broken up in patches some 6 px across, smoothly (a hard step at 2 px read as salt and
        # pepper at 1080)
        nz = noise.noise(v.co * (1.0 / (U * S * 6.0)) + off)
        w = w * (0.7 + 0.3 * (nz + 1) / 2)
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
    mat = iron("band", seed, cell=10.0 if big else 7.0)
    parts = []
    if big:
        hg, jt, lg = cs["hinge"], cs["joint"], cs["lug"]
        band = ring_band(st, "band", cx, cy, ri, ro, 7.0, seams=(hg["angle"], jt["angle"]), seed=seed, n=2200)
        wear(st, band, ztop=7.0, zw=cs.get("zw", 0.3), seed=1)
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
        # the lug: a forged bar of round-backed section under both bands toward the draught (its
        # crown lit along its upper side, so it reads as a bar `width` px across at 1080, not a
        # line), riveted through each band with a proud domed head
        dx, dy = lg["to"]
        la = math.degrees(math.atan2(dy, dx))
        dist = math.hypot(dx, dy)
        lz, lb = lg.get("z", 4.6), lg.get("bevel", 2.0)
        strap = slab(st, "lug", tab(cx, cy, la, ro - 9, dist - SPEC["small"]["outer_r"] + 6 - lb, lg["width"] - 2 * lb), 0.0, lz, lb)
        wear(st, strap, k0=0.18, k1=0.7, ztop=lz, zw=0.35, seed=4)
        strap.data.materials.append(iron("lug", seed + 7, cell=7.0))
        parts.append(strap)
        rr = lg["rivet_r"]
        rv = dome(st, "lugrivet", cx + rr * math.cos(math.radians(la)), cy + rr * math.sin(math.radians(la)),
                  lg.get("rivet_z", 7.4), lg.get("rivet", 2.5), flat=0.75)
        wear(st, rv, k0=0.15, k1=0.6, seed=5)
        rv.data.materials.append(iron("rivet", seed + 8, tilt=0.04))
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
        wear(st, band, ztop=4.4, zw=cs.get("zw", 0.3), seed=1)
        band.data.materials.append(mat)
        la = math.degrees(math.atan2(-SPEC["cuff"]["lug"]["to"][1], -SPEC["cuff"]["lug"]["to"][0]))
        rr = (ri + ro) / 2 + 0.4
        rv = dome(st, "lugrivet", cx + rr * math.cos(math.radians(la)), cy + rr * math.sin(math.radians(la)),
                  cs.get("rivet_z", 4.9), cs.get("rivet", 2.2), flat=0.75)
        wear(st, rv, k0=0.15, k1=0.6, seed=5)
        rv.data.materials.append(iron("rivet", seed + 8, tilt=0.04))
        # the hole drilled through the band's crown at 6 o'clock, where the key tag's link goes in
        hr = cs.get("hole_r", 26.5)
        hole = slab(st, "hole", circle(cx, cy + hr, cs.get("hole", 1.05), 24), -1.0, 6.0, 0.1)
        hole.data.materials.append(B.plain_material("hole", "#030202", 0.0, 0.9))
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


def floor_material(name, seed, span=None, inset=0.0):
    """A seat's floor: a dark iron plate, rough and only half metal, so the house light lies on it
    and the collar's shadow can be seen falling across it (a mirror-flat plate seen from above
    reflects only the dark room and reads as a hole). With `vignette` [px, darkest] the plate
    darkens toward the walls (soot and the walls' own shade gathering there): a smooth step over
    that many px from the opening's edge, measured on the slab's own coordinates (`span` px
    across, the opening `inset` px in from the slab's edge)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    n, k = nt.nodes, nt.links
    b = n["Principled BSDF"]
    fs = SPEC["seat"]
    col = B.hexc(fs.get("floor", "#1e1b20"))
    b.inputs["Base Color"].default_value = col
    b.inputs["Metallic"].default_value = fs.get("floor_metal", 0.2)
    b.inputs["Roughness"].default_value = fs.get("floor_rough", 0.8)
    b.inputs["Specular IOR Level"].default_value = fs.get("floor_spec", 0.3)
    vg = fs.get("vignette")
    if vg and span:
        tc = n.new("ShaderNodeTexCoord")
        sep = n.new("ShaderNodeSeparateXYZ")
        k.new(tc.outputs["Generated"], sep.inputs[0])

        def edge(sock):                              # px in from the opening's edge on one axis
            inv = n.new("ShaderNodeMath")
            inv.operation = "SUBTRACT"
            inv.inputs[0].default_value = 1.0
            k.new(sock, inv.inputs[1])
            mn = n.new("ShaderNodeMath")
            mn.operation = "MINIMUM"
            k.new(sock, mn.inputs[0])
            k.new(inv.outputs[0], mn.inputs[1])
            ma = n.new("ShaderNodeMath")
            ma.operation = "MULTIPLY_ADD"
            ma.inputs[1].default_value = span
            ma.inputs[2].default_value = -inset
            k.new(mn.outputs[0], ma.inputs[0])
            return ma.outputs[0]
        dmin = n.new("ShaderNodeMath")
        dmin.operation = "MINIMUM"
        k.new(edge(sep.outputs["X"]), dmin.inputs[0])
        k.new(edge(sep.outputs["Y"]), dmin.inputs[1])
        mr = n.new("ShaderNodeMapRange")
        mr.interpolation_type = "SMOOTHSTEP"
        mr.inputs["From Min"].default_value = 0.0
        mr.inputs["From Max"].default_value = vg[0]
        mr.inputs["To Min"].default_value = vg[1]
        mr.inputs["To Max"].default_value = 1.0
        k.new(dmin.outputs[0], mr.inputs["Value"])
        sc = n.new("ShaderNodeVectorMath")
        sc.operation = "SCALE"
        sc.inputs[0].default_value = col[:3]
        k.new(mr.outputs["Result"], sc.inputs["Scale"])
        k.new(sc.outputs[0], b.inputs["Base Color"])
    return facets(m, seed, cell=8.0, tilt=fs.get("floor_tilt", 0.03), deep=1.8)


def seat(k, state):
    sp = SPEC["seat"]
    cw_ = sp["canvas"]
    st = Stage(cw_, cw_)
    ax, ay = sp["at"]
    s, f = sp["size"], sp["face"]
    rnd = random.Random(100 + k)
    # path: the face's middle line, a hand-forged square (sides bowed a little, corners each their
    # own; every corner rounder than the inner wall's reach, so the sweep never folds)
    m = f / 2
    x0, y0, x1, y1 = ax + m, ay + m, ax + s - m, ay + s - m
    c0, c1 = sp.get("corners", [3.9, 4.8])
    pts = B.densify(B.outline(x0, y0, x1, y1, corners=[rnd.uniform(c0, c1) for _ in range(4)], n_round=18), 0.12)
    cxs, cys = (x0 + x1) / 2, (y0 + y1) / 2
    bow = [rnd.uniform(-0.35, 0.35) for _ in range(4)]

    def bowed(x, y):
        u, v = (x - cxs) / ((x1 - x0) / 2), (y - cys) / ((y1 - y0) / 2)
        return (x + bow[0] * (1 - v * v) * (1 if u > 0 else -1) * (abs(u) > 0.95),
                y + bow[1] * (1 - u * u) * (1 if v > 0 else -1) * (abs(v) > 0.95))
    path = [bowed(x, y) for (x, y) in pts]
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
    # the profile (d outward from the middle line, z up): a battered outer wall; a rounded face
    # whose flanks lie near 30 deg, so seen from above the flank toward the light shows a clean
    # stroke of worn steel (the outer edge of the top and left bars, the inner edge of the bottom
    # and right ones) and the other flank stays dark; then a chamfer down into the seat (lit on
    # the lower right, in shade on the upper left) and a plain wall to the floor `sink` px below
    # the crown, the collar's shadow lying on the floor beside it
    top, hz, sink = sp.get("top", 6.5), sp.get("round", 1.2), sp.get("sink", 4.0)
    cp, cw, ca = sp.get("cap_p", 1.3), sp.get("chamfer", 1.5), math.radians(sp.get("chamfer_deg", 35))
    zc, zf = top - hz, top - sink
    zch = zc - cw * math.tan(ca)

    def surf(d):
        if d >= -m:
            return zc + hz * (1 - min(1.0, abs(d) / m) ** cp)
        return zc - (-m - d) * math.tan(ca)
    fo = sp.get("fillet", 0.7)                       # the outer wall rounds into the face
    prof = [(m + 0.5, 0.0)]
    for i in range(1, 6):
        prof.append((m + 0.5 * (1 - i / 6) ** 1.5, (zc - fo) * i / 5))
    for i in range(1, 7):                            # quarter round from the wall up onto the face
        t = math.pi / 2 * i / 6
        d = m + 0.08 - fo * 0.45 * (1 - math.cos(t)) + 0.0
        prof.append((d, zc - fo + (fo + hz * (1 - min(1.0, abs(d) / m) ** cp)) * math.sin(t)))
    for i in range(1, 36):
        d = m * (1 - 2 * i / 36)
        if d < prof[-1][0]:
            prof.append((d, surf(d)))
    j_ch = len(prof)                                  # the chamfer, from the arris down
    for i in range(0, 9):
        d = -m - cw * i / 8
        prof.append((d, surf(d)))
    j_ch1 = len(prof)
    prof += [(-m - cw - 0.05, zf - 0.25), (-m - cw - 0.05, 0.0), (0.0, 0.0)]
    # eight rank dimples punched in the lower bar's lit inner slope, spread wide enough to count:
    # "ball" a round dent; "cyl" a punched hole (steep walls, a level floor that sees only the
    # dark room), so each reads as a dark pit with lit iron on both sides of it
    dim = []
    rp, dp = sp.get("dimple_r", 1.3), sp.get("dimple_depth", 0.9)
    span, dd = sp.get("dimple_span", 9.5), sp.get("dimple_d", 1.6)
    shape = sp.get("dimple_shape", "ball")
    dx0, dx1 = ax + span, ax + s - span
    for i in range(sp["dimples"]):
        qx = dx0 + (dx1 - dx0) * i / (sp["dimples"] - 1) + rnd.uniform(-0.2, 0.2)
        qy = bowed(qx, ay + s - m)[1] - dd + rnd.uniform(-0.08, 0.08)
        dim.append((qx, qy))
    Rs = (rp * rp + dp * dp) / (2 * dp)               # the punch's ball
    zpit = surf(-dd) - dp + Rs                        # its centre
    zb = surf(-dd) - dp                               # the hole's level floor
    lip = sp.get("dimple_lip", 0.3)
    # this casting's own hammer marks: a few dents in the face, two nicks in its outer edge
    drnd = random.Random(300 + k)
    dents = []
    for _ in range(sp.get("dents", 5)):
        i0 = drnd.randrange(n)
        q = drnd.uniform(-0.7, 0.7) * m
        dents.append((path[i0][0] + nrm[i0][0] * q, path[i0][1] + nrm[i0][1] * q, drnd.uniform(1.2, 2.2), drnd.uniform(0.3, 0.6)))
    nicks = [(drnd.randrange(n), drnd.uniform(0.35, 0.65)) for _ in range(sp.get("nicks", 2))]

    def mod(i, x, y, d, z):
        for i0, dep in nicks:
            di = min(abs(i - i0), n - abs(i - i0))
            if di < 10 and d > 0.4 * m:
                d -= dep * (1 - di / 10) ** 2 * min(1.0, (d - 0.4 * m) / (0.6 * m))
        px, py = x + nrm[i][0] * d, y + nrm[i][1] * d
        if z > zch:
            for (qx, qy, dr, dep) in dents:
                r2 = (px - qx) ** 2 + (py - qy) ** 2
                if r2 < dr * dr:
                    z -= dep * (1 - r2 / (dr * dr)) ** 2
        for (qx, qy) in dim:
            r2 = (px - qx) ** 2 + (py - qy) ** 2
            if shape == "cyl":
                r = math.sqrt(r2)
                if r < rp + lip:
                    t = min(1.0, max(0.0, (rp + lip - r) / (2 * lip)))
                    t = t * t * (3 - 2 * t)
                    z = min(z, z + (zb - z) * t)
            elif r2 < Rs * Rs:
                z = min(z, max(zpit - math.sqrt(Rs * Rs - r2), zch - 0.6))
        return d, z

    if "rim" in sp:
        st.suns[2].data.energy *= sp["rim"]
    col = sweep(st, "collar", path, nrm, prof, mod)
    wear(st, col, k0=sp.get("k0", 0.2), k1=0.95, ztop=top, zw=sp.get("zw", 0.45), seed=k, zlow=zch - 0.4)
    # the chamfer into the seat is filed, not left in its scale: a little brighter iron, so the
    # walls facing the light (the lower and right) catch it and those turned away stay dark;
    # nothing bright inside the rank's pits
    cwr = sp.get("chamfer_wear", 0.0)
    if cwr > 0 or shape == "cyl":
        ca_ = col.data.color_attributes["wear"]
        Mp = len(prof)
        vs = col.data.vertices
        off = Vector((k * 5.3, k * 2.9, k * 7.7))
        for v in vs:
            j = v.index % Mp
            w = ca_.data[v.index].color[0]
            if j_ch <= j < j_ch1 and cwr > 0:
                nz = noise.noise(v.co * (1.0 / (U * st.S * 2.6)) + off)
                w = max(w, cwr * (0.75 + 0.25 * nz))
            if shape == "cyl":
                vx = v.co.x / (U * st.S) + cw_ / 2
                vy = cw_ / 2 - v.co.y / (U * st.S)
                for (qx, qy) in dim:
                    if (vx - qx) ** 2 + (vy - qy) ** 2 < (rp + lip * 0.5) ** 2:
                        w = 0.0
            ca_.data[v.index].color = (w, w, w, 1)
    if state == "hot":
        # how far in across the collar each vertex lies: 0 at its outer edge, 1 at its inner wall
        Mp = len(prof)
        if "heat" not in col.data.color_attributes:
            col.data.color_attributes.new("heat", "FLOAT_COLOR", "POINT")
        ha = col.data.color_attributes["heat"]
        for v in col.data.vertices:
            j = v.index % Mp
            u = 1.0 if j >= j_ch1 else min(1.0, max(0.0, (m - prof[j][0]) / (2 * m + cw)))
            u = u ** sp.get("heat_pow", 1.4)
            ha.data[v.index].color = (u, u, u, 1)
        col.data.materials.append(collar_heat_material("collar_hot", 40 + k, sp.get("heat_strength", 1.6)))
    else:
        col.data.materials.append(iron("collar", 40 + k, cell=8.0, tilt=0.085))
    e = m + 1.0
    fl = slab(st, "floor", rrect(ax + e, ay + e, ax + s - e, ay + s - e, 1.2), 0.0, zf, 0.25)
    fl.data.materials.append(floor_material("floor", 60 + k, span=s - 2 * e, inset=m + cw + 0.05 - 1.0))
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
    ob.data.materials.append(iron("sill", 70 + N, cell=10.0))
    for i in range(N - 1):
        x = sp["over"] + sp["seat"] + 3 + sp["pitch"] * i + rnd.uniform(-0.2, 0.2)
        r = dome(st, f"r{i}", x, 3.5, 2.4, 1.55, flat=0.6)
        wear(st, r, seed=i)
        r.data.materials.append(iron(f"rv{i}", 80 + i, tilt=0.05))
    st.render(f"sill_{N}")


def tag(w):
    """A key tag: a plate of the chain's iron, w by 16, an ear on its top whose hole a small link
    threads. The link runs up `cut` px to the band it hangs from and is cut there by a holdout
    (in the game the band covers that line). The plate hangs turned a little toward the light,
    its face rubbed by handling, so the code's pressed letter reads dark on it."""
    from mathutils import Euler, Matrix
    sp = SPEC["tag"]
    h = sp["height"]
    ax, ay = sp["at"]
    st = Stage(w + ax + 6, ay + h + 6)
    cxp, bv = ax + w / 2, 0.55
    plate = slab(st, "tag", rrect(ax + bv, ay + bv, ax + w - bv, ay + h - bv, 2.0), 0.2, 1.9, bv)
    ew, eh = sp.get("ear", [9.0, 5.0])
    hy = ay - sp.get("hole_y", 1.7)
    ear = slab(st, "ear", rrect(cxp - ew / 2 + bv, ay - eh + 1.0 + bv, cxp + ew / 2 - bv, ay + 2.0, 2.2), 0.4, 1.7, bv,
               holes=[circle(cxp, hy, 1.45, 24)[::-1]])
    piv = st.P(cxp, hy, 1.0)
    R = Euler([-math.radians(a) for a in sp.get("tilt", [7.0, 5.0])] + [0.0]).to_matrix().to_4x4()
    for o in (plate, ear):
        o.matrix_world = Matrix.Translation(piv) @ R @ Matrix.Translation(-piv) @ o.matrix_world
    L, Wd, wr = sp.get("link", [10.5, 6.6, 0.95])
    lk, _ = C.link_mesh("tlink", L * st.S * U, Wd * st.S * U, wr * st.S * U)
    lk.rotation_euler = (math.radians(sp.get("link_turn", 55)), 0, math.pi / 2)
    lk.location = st.P(cxp, hy + 0.5 - (L / 2 - wr), 1.05)
    st.add(lk)
    bpy.context.view_layer.update()
    C.mark_wear([lk, ear], wr * st.S * U)
    lk.data.materials.append(iron("tlink", 95 + w, cell=6.0, tilt=0.03))
    for o, s in ((plate, w), (ear, w + 1)):
        wear(st, o, k0=0.3, k1=1.0, ztop=0.85, zw=sp.get("zw", 0.75), seed=s)
        o.data.materials.append(iron("tag", 90 + s, cell=9.0, tilt=0.05))
    cut = ay - sp.get("cut", 7.0)
    W_ = w + ax + 6
    ho = slab(st, "cutter", [(-4, -12), (W_ + 4, -12), (W_ + 4, cut), (-4, cut)], -1.0, 14.0, 0.05)
    ho.is_holdout = True
    ho.visible_shadow = False
    st.render(f"tag_{w}")


def hanger():
    """One of the two hangers tying the seats' sill to the chain (so cuff, chain and seats are one
    object): an eye under the strap, a link face-on through it, and a link on edge through that
    one, whose foot the game lays inside a face-on link of the chain (drawn over it). Anchor: the
    eye's foot bar (SPEC hanger.eye)."""
    sp = SPEC["hanger"]
    W, H = sp["canvas"]
    st = Stage(W, H)
    ex, ey = sp["eye"]
    re_, rw = sp.get("eye_r", 0.9), sp["wire"]
    L, Wd = sp["link"]
    bpy.ops.mesh.primitive_torus_add(major_radius=1.9 * st.S * U, minor_radius=re_ * st.S * U, major_segments=48,
                                     minor_segments=12, location=st.P(ex, ey - 1.9, 1.6))
    eye = bpy.context.active_object
    eye.rotation_euler = (0, math.pi / 2, 0)
    bpy.ops.object.transform_apply(rotation=True)
    eye.data.polygons.foreach_set("use_smooth", [True] * len(eye.data.polygons))
    st.add(eye)
    ya = ey - re_ - rw + L / 2 - rw                    # A hooked over the eye's foot bar
    yb = ya + (L / 2 - rw) - 2 * rw + (L / 2 - rw)     # B hooked over A's foot bar
    a, _ = C.link_mesh("hangA", L * st.S * U, Wd * st.S * U, rw * st.S * U)
    a.rotation_euler = (0, 0, math.pi / 2)
    a.location = st.P(ex, ya, 1.6)
    b, _ = C.link_mesh("hangB", L * st.S * U, Wd * st.S * U, rw * st.S * U)
    b.rotation_euler = (math.radians(90 - sp.get("turn", 25)), 0, math.pi / 2)
    b.location = st.P(ex, yb, 1.6)
    st.add(a)
    st.add(b)
    bpy.context.view_layer.update()
    C.mark_wear([eye, a, b], rw * st.S * U)
    for i, o in enumerate((eye, a, b)):
        o.data.materials.append(iron(f"hang{i}", 140 + i, cell=6.0, tilt=0.03))
    st.render("hanger")


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
    kh = circle(ax, by + sp.get("keyhole_y", 21.5), 1.3, 24)[::-1]
    ky = by + sp.get("keyhole_y", 21.5)
    slot = [(ax - 0.5, ky + 0.6), (ax + 0.5, ky + 0.6), (ax + 0.7, ky + 3.4), (ax - 0.7, ky + 3.4)][::-1]
    body = slab(st, "body", body_pts, 1.5, 7.5, 2.0, holes=[kh])
    wear(st, body, k0=0.25, k1=0.9, seed=1)
    body.data.materials.append(body_heat_material("body", 120, SPEC["lock"].get("heat", 1.0)) if state == "hot"
                               else iron("body", 120, cell=8.0, tilt=0.11))
    core = slab(st, "core", circle(ax, ky + 1.5, 3.0, 24), 2.0, 3.0, 0.2)
    core.data.materials.append(B.plain_material("dark", "#050404", 0.2, 0.8))
    slt = slab(st, "slot", slot, 6.6, 7.7, 0.1)
    slt.data.materials.append(B.plain_material("dark2", "#060505", 0.2, 0.8))
    # the shackle: a U of round bar, its apex up behind the link's upper bar, its legs down in
    # front of the lower one into the body
    Rs, bar = 7.0, 1.85
    apex = ay - sp.get("apex", 6.8)          # its crown above the link's upper bar (drawn over it in the game)
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
    want = set(argv[2:]) or {"cuff", "small", "seats", "sill", "tags", "hanger", "lock"}
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
    if "hanger" in want:
        hanger()
    if "lock" in want:
        for s in ("", "open", "hot"):
            lock(s)


if __name__ == "__main__":
    main()
