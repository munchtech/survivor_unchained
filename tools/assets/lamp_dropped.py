"""The dropped lamp (Cinematics 8, C04 A): "On the stones at the water's edge, a lamp lies on its side. It has gone out."

    blender -b --factory-startup -P tools/assets/lamp_dropped.py   ->  godot/art/props/lamp_dropped/lamp_dropped.glb

A woman's hand lantern, the kind carried down to the water to wait for someone: small (11 cm square, 30 cm to the
ring), env_lamps.py's lamp-iron at hand size with a bail, a tallow candle in the burner cup burnt down and out, its
wick black, wax run sideways onto the lower pane where it fell lit. One pane (the one toward +Z, the camera's side)
starred from a blow on the stones, one shard gone from it and lying beside the lamp. Wet: the iron's roughness down,
the glass sooted toward the cap. Not the Ford-Warden's keeper lamp (BossViews.cs LampIron; env_lamps ford_lamp).

Built lying on its side: its long axis along X (the cap toward -X), resting on its base plate's and top frame's edges,
rolled a few degrees. The bail fallen to the stones. Origin at the resting contact, up +Y (glTF frame).
Materials: env_lamps' atlas (iron | pitch, and a tallow band in place of its wood) as 'lamp_dropped_atlas', and
'lamp_dropped_glass' (alpha, its soot in a small map; named apart from 'lamp_glass' so Lamps.cs never swaps it).
All procedural; no credit owed.
"""
import math
import os
import random
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import env_lamps as L  # noqa: E402  (its helpers; its main() only runs as a script)

ROOT = L.ROOT
OUT = os.path.join(ROOT, 'godot', 'art', 'props', 'lamp_dropped', 'lamp_dropped.glb')
W, H = 0.11, 0.19
L.REG['wax'] = (0.375, 0.5, 0.3)
rnd = random.Random(4417)


# ------------------------------------------------------------- materials --

def materials():
    col, rough, metal = L.atlas()
    T = L.TEX
    # tallow over the wood's first band: a greasy off-white, yellowed, with soot specks
    x0, x1 = int(0.375 * T), int(0.5 * T)
    n = L.noise((T, x1 - x0), 611, 4, 6)
    # (round 2: the r1 tallow read as a white spool by day; yellowed, grimy, smoke-browned toward the top)
    vv = (np.arange(T)[:, None] + 0.5) / T
    c = np.stack([0.105 + 0.03 * n, 0.083 + 0.024 * n, 0.045 + 0.014 * n], -1) * (1 - 0.45 * vv[..., None] ** 2)
    specks = (L.noise((T, x1 - x0), 612, 3, 40) > 0.66)[..., None]
    col[:, x0:x1] = np.where(specks, c * 0.3, c)
    rough[:, x0:x1] = 0.55 + 0.1 * n
    metal[:, x0:x1] = 0
    # Seen at an arm's length by day (C04 A0), env_lamps' night iron read as one black: a hand lamp's iron instead,
    # worn dark grey-brown, rust blooming in patches (orange-brown where it is thick), and wet: low roughness on the
    # bare iron, so the low sun finds its edges; less metallic, so its colour reads under a grey sky.
    i1 = int(0.25 * T)
    n1 = L.noise((T, i1), 621, 5, 4)
    n2 = L.noise((T, i1), 622, 4, 18)
    # (round 2: blackened by its own smoke, dull; the r1 grey-brown read as a navy plastic frame in cold light)
    rust = np.clip((L.noise((T, i1), 623, 4, 7) - 0.66) * 3.0, 0, 1) * (0.4 + 0.4 * n2)
    v = 0.038 + 0.016 * (n1 - 0.5) + 0.012 * (n2 - 0.5)
    iron = np.stack([v, v * 0.93, v * 0.86], -1)
    rc = np.stack([0.19 + 0.05 * n2, 0.085 + 0.025 * n2, 0.035 + 0.012 * n2], -1)
    col[:, :i1] = np.maximum(iron * (1 - rust[..., None]) + rc * rust[..., None], 0.045)
    rough[:, :i1] = np.clip(0.52 + 0.16 * n2 + 0.2 * rust, 0.35, 0.9)
    metal[:, :i1] = 0.35 * (1 - rust) + 0.05
    # the pitch band: the wick, the cup's char: dead black
    p0, p1 = int(0.25 * T), int(0.375 * T)
    col[:, p0:p1] = 0.018 + 0.008 * L.noise((T, p1 - p0), 631, 3, 8)[..., None]
    rough[:, p0:p1] = 0.85
    a = L.image('lamp_dropped_albedo', col, False)
    mr = L.image('lamp_dropped_mr', np.stack([np.ones_like(rough), rough, metal], -1), True)
    m = bpy.data.materials.new('lamp_dropped_atlas')
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    ta = nt.nodes.new('ShaderNodeTexImage'); ta.image = a
    tm = nt.nodes.new('ShaderNodeTexImage'); tm.image = mr
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(ta.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(tm.outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
    nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])

    # the glass's soot: clear low, smoked toward the top (v = 1, the cap), in runs; alpha rises with it
    G = 256
    v = (np.arange(G)[:, None] + 0.5) / G
    u = (np.arange(G)[None, :] + 0.5) / G
    runs = L.noise((G, G), 613, 3, 3)
    soot = np.clip((v - 0.3) / 0.45, 0, 1) ** 1.1 * (0.75 + 0.6 * runs) + 0.18 * L.noise((G, G), 614, 4, 8)
    soot = np.clip(soot, 0, 1)
    rgba = np.zeros((G, G, 4), np.float32)
    clear = np.array([0.22, 0.24, 0.19])
    for k in range(3):
        rgba[..., k] = clear[k] * (1 - soot) + 0.01 * soot
    rgba[..., 3] = 0.3 + 0.68 * soot    # clear enough to see the candle, present enough that the star in it reads
    gi = bpy.data.images.new('lamp_dropped_glass_soot', G, G, alpha=True)
    px = rgba.copy()
    px[..., :3] = np.where(px[..., :3] <= 0.0031308, px[..., :3] * 12.92, 1.055 * np.power(px[..., :3], 1 / 2.4) - 0.055)
    gi.pixels.foreach_set(px.ravel())
    gi.file_format = 'PNG'
    gi.pack()
    g = bpy.data.materials.new('lamp_dropped_glass')
    g.use_nodes = True
    gt = g.node_tree
    b = gt.nodes['Principled BSDF']
    tg = gt.nodes.new('ShaderNodeTexImage'); tg.image = gi
    gt.links.new(tg.outputs['Color'], b.inputs['Base Color'])
    gt.links.new(tg.outputs['Alpha'], b.inputs['Alpha'])
    b.inputs['Roughness'].default_value = 0.08
    g.blend_method = 'BLEND'
    g.use_backface_culling = False
    return m, g


# ------------------------------------------------------------- the cracked pane --

def shards(w, h):
    """The pane (local xy, facing +z, foot at y = 0) starred from a point near its lower corner: wedges to the
    border, one split again, each pulled in a hair from its neighbours. Returns ([polygon], the missing one)."""
    P = Vector((w * 0.12, h * 0.34))
    n = 8
    angs = sorted(rnd.uniform(0, math.tau) for _ in range(n))
    # spread them a little more evenly
    angs = [a * 0.5 + (k * math.tau / n + angs[0]) * 0.5 for k, a in enumerate(angs)]
    corners = [Vector((-w / 2, 0)), Vector((w / 2, 0)), Vector((w / 2, h)), Vector((-w / 2, h))]

    def hit(a):
        d = Vector((math.cos(a), math.sin(a)))
        ts = []
        for t in ((-w / 2 - P.x) / d.x if abs(d.x) > 1e-9 else 1e9, (w / 2 - P.x) / d.x if abs(d.x) > 1e-9 else 1e9,
                  (0 - P.y) / d.y if abs(d.y) > 1e-9 else 1e9, (h - P.y) / d.y if abs(d.y) > 1e-9 else 1e9):
            if t > 0:
                q = P + d * t
                if -w / 2 - 1e-7 <= q.x <= w / 2 + 1e-7 and -1e-7 <= q.y <= h + 1e-7:
                    ts.append(t)
        return P + d * min(ts)

    def ang(q):
        return math.atan2(q.y - P.y, q.x - P.x)

    polys = []
    for k in range(n):
        a0, a1 = angs[k], angs[(k + 1) % n] + (math.tau if k == n - 1 else 0)
        pts = [P, hit(a0)]
        cs = []
        for c in corners:
            ac = ang(c)
            while ac < a0:
                ac += math.tau
            if ac < a1:
                cs.append((ac, c))
        pts += [c for _, c in sorted(cs)]
        pts.append(hit(a1))
        polys.append(pts)
    # a cross crack through the biggest wedge, at a third of its length: two pieces
    big = max(range(n), key=lambda k: sum((p - P).length for p in polys[k]))
    pg = polys.pop(big)
    r = 0.45 * max((p - P).length for p in pg)
    e0, e1 = pg[1], pg[-1]
    m0, m1 = P + (e0 - P).normalized() * r, P + (e1 - P).normalized() * r
    inner = [P, m0, m1]
    outer = [m0] + pg[1:] + [m1]
    polys += [inner, outer]
    # pull each in from its edges (the cracks read dark between)
    out = []
    for pg in polys:
        c = sum(pg, Vector((0, 0))) / len(pg)
        out.append([c + (p - c) * 0.965 for p in pg])
    # the missing one: the inner piece of the split wedge (at the impact), a hole the light shows through
    gone = out.pop(len(out) - 2)
    return out, gone


def shard_bm(pts):
    bm = bmesh.new()
    vs = [bm.verts.new((p.x, p.y, 0.0)) for p in pts]
    try:
        bm.faces.new(vs)
    except ValueError:
        pass
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    return bm


# ------------------------------------------------------------- the lamp --

def lamp_parts():
    parts, flame, top = L.lamp_iron(W, H, ring=False, bail=0.0, fine=True, rim=0.16, hood_gap=0.2)
    p = 0.075 * W
    y_base = 0.06 * W + 0.15 * W               # the burner cup's foot (lamp_iron's base_top)
    pw = W - 2 * p * 0.8
    g = 0.5 * W - p * 0.6
    # lamp_iron's panes come in order k = 0..3 (facing +z, +x, -z, -x); the one facing local +x is starred
    glass = [i for i, q in enumerate(parts) if q.region == 'glass']
    parts.pop(glass[1])
    paneframe = L.T(0, y_base, 0) @ L.R('Y', math.pi / 2) @ L.T(0, 0, g)
    pieces, gone = shards(pw, H)
    ground = [gone] + [pieces[k] for k in (1, 3, 6)]
    # (round 2) the pane is out: only two jagged teeth left in the frame (the wedges' outer thirds)
    rem = []
    for k in (0, 4):
        pg = pieces[k]
        c0 = pg[0]
        rem.append([pg[1] + (c0 - pg[1]) * 0.28] + pg[1:] + [pg[-1] + (c0 - pg[-1]) * 0.42])
    pieces = rem
    for k, pts in enumerate(pieces):
        tilt = L.R('Z', rnd.uniform(-0.02, 0.02)) @ L.R('X', rnd.uniform(-0.05, 0.05)) @ L.R('Y', rnd.uniform(-0.05, 0.05))
        parts.append(L.Part(shard_bm(pts), 'shard', paneframe @ L.T(0, 0, rnd.uniform(-0.0012, 0.0012)) @ tilt))
    # the candle: a tallow stub in the cup, burnt low and guttered (an uneven rim, a drip down one side), its crater
    # charred, the wick a thick black hook (round 2: r1's clean cylinder read as a white spool)
    cup_top = y_base + 0.11 * W
    cr = 0.11 * W
    cb = L.lathe([(cr, 0), (cr * 1.03, 0.12 * W), (cr * 0.99, 0.2 * W), (cr * 0.62, 0.17 * W), (0, 0.15 * W)], 14)
    for v in cb.verts:
        a = math.atan2(v.co.z, v.co.x)
        if v.co.y > 0.1 * W:
            v.co.y += 0.05 * W * (math.sin(3 * a + 0.7) * 0.5 + math.sin(5 * a) * 0.3)
        v.co.x *= 1 + 0.06 * math.sin(4 * a + 1.3); v.co.z *= 1 + 0.06 * math.sin(4 * a + 1.3)
    parts.append(L.Part(cb, 'wax', L.T(0, cup_top - 0.02 * W, 0)))
    parts[-1].smooth = True
    drip = L.lathe([(0.03 * W, 0), (0.034 * W, 0.08 * W), (0.022 * W, 0.15 * W), (0, 0.17 * W)], 6)
    parts.append(L.Part(drip, 'wax', L.T(cr * 0.96, cup_top + 0.02 * W, 0) @ L.R('X', math.pi)))
    parts[-1].smooth = True
    parts.append(L.Part(L.lathe([(cr * 0.66, 0), (cr * 0.45, 0.01 * W), (0, 0.014 * W)], 12), 'pitch',
                        L.T(0, cup_top - 0.02 * W + 0.155 * W, 0)))
    wick = L.rod((0, cup_top + 0.13 * W, 0), (0.01 * W, cup_top + 0.24 * W, 0.006 * W), 0.026 * W, segs=5, region='pitch')
    parts.append(wick)
    parts.append(L.rod((0.01 * W, cup_top + 0.24 * W, 0.006 * W), (0.05 * W, cup_top + 0.27 * W, 0.02 * W), 0.022 * W,
                       segs=5, region='pitch'))
    # wax run sideways when it fell lit: a flat tongue on the lower pane's inside (local +z goes down), toward the cap
    tongue = L.lathe([(0.0, 0), (0.045 * W, 0.0015), (0.035 * W, 0.004), (0, 0.005)], 7)
    for v in tongue.verts:
        v.co.x *= 1.0 + 0.3 * math.sin(v.co.z * 900 + 1.0)
    bmesh.ops.scale(tongue, vec=(1.3, 1.4, 3.2), verts=tongue.verts)
    parts.append(L.Part(tongue, 'wax', L.T(0, cup_top + 0.12 * W, g - 0.004) @ L.R('X', -math.pi / 2) @ L.R('Y', 0.3)))
    # the ring on the cap to hang it by (rounder than lamp_iron's)
    rr = 0.14 * W
    parts.append(L.Part(L.torus(rr, 0.028 * W, 16, 6), 'iron', L.T(0, top + rr + 0.01 * W, 0)))
    parts[-1].smooth = True
    # the bail: a hoop of rod from lugs on the top frame's sides, fallen toward the stones (local +z is down)
    yb = y_base + H + 0.15 * W * 0.4
    for sx in (-1, 1):
        parts.append(L.Part(L.cube(0.03 * W, 0.08 * W, 0.08 * W, 0.004 * W), 'iron', L.T(sx * 0.535 * W, yb, 0)))
    parts.append(L.Part(L.arc(0.55 * W, 0.024 * W, 16, 6, 0, math.pi), 'iron', L.T(0, yb, 0) @ L.R('X', math.radians(74))))
    parts[-1].smooth = True
    # the door's latch on the face toward local -z (up when it lies): a hasp and a turn-button
    parts.append(L.Part(L.cube(0.05 * W, 0.12 * W, 0.02 * W, 0.004 * W), 'iron', L.T(0.36 * W, y_base + 0.5 * H, -0.5 * W - 0.012 * W)))
    parts.append(L.Part(L.lathe([(0.025 * W, 0), (0.02 * W, 0.02 * W), (0, 0.025 * W)], 6), 'iron',
                        L.T(0.36 * W, y_base + 0.5 * H, -0.5 * W - 0.02 * W) @ L.R('X', -math.pi / 2)))
    # rivet heads where the band meets each post (8)
    for k in range(4):
        rot = L.T(0, y_base, 0) @ L.R('Y', k * math.pi / 2)
        for sx in (-1, 1):
            parts.append(L.Part(L.lathe([(0.018 * W, 0), (0.014 * W, 0.01 * W), (0, 0.014 * W)], 6), 'iron',
                                rot @ L.T(sx * (0.5 * W - p / 2), 0.62 * H, 0.5 * W + 0.018 * W) @ L.R('X', math.pi / 2)))
    return parts, ground, g, pw, y_base


def build(parts, atlas_mat, glass_mat):
    bm = bmesh.new()
    for p in parts:
        if p.region in ('glass', 'shard'):
            uvl = p.bm.loops.layers.uv.verify()
            for f in p.bm.faces:
                for l in f.loops:
                    co = l.vert.co
                    l[uvl].uv = (0.5 + co.x / W, co.y / H)
        else:
            L.uv_part(p.bm, p.region)
        p.bm.transform(L.G2B @ p.at)
        me = bpy.data.meshes.new('tmp')
        p.bm.to_mesh(me)
        n0 = len(bm.faces)
        bm.from_mesh(me)
        bm.faces.ensure_lookup_table()
        for f in bm.faces[n0:]:
            f.material_index = 1 if p.region in ('glass', 'shard') else 0
            f.smooth = getattr(p, 'smooth', False)
        bpy.data.meshes.remove(me)
        p.bm.free()
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new('lamp_dropped')
    bm.to_mesh(me)
    bm.free()
    me.materials.append(atlas_mat)
    me.materials.append(glass_mat)
    ob = bpy.data.objects.new('lamp_dropped', me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    atlas_mat, glass_mat = materials()
    parts, ground, g, pw, y_base = lamp_parts()
    # Lay it down (game frame): local x -> +z (the starred pane toward the camera), local y -> -x (cap toward -X),
    # local z -> -y (down); then roll it a few degrees about its axis and turn it a touch.
    lay = Matrix(((0, -1, 0, 0), (0, 0, -1, 0), (1, 0, 0, 0), (0, 0, 0, 1)))
    lay = L.R('Y', math.radians(-8)) @ L.R('X', math.radians(6)) @ lay
    for p in parts:
        p.at = lay @ p.at
    ob = build(parts, atlas_mat, glass_mat)
    # rest it: lowest point to y = 0 (Blender z), origin at the contact patch's middle
    me = ob.data
    zs = [v.co.z for v in me.vertices]
    zmin = min(zs)
    low = [v.co for v in me.vertices if v.co.z < zmin + 0.004]
    cx = sum(c.x for c in low) / len(low)
    cy = sum(c.y for c in low) / len(low)
    me.transform(Matrix.Translation((-cx, -cy, -zmin)))
    # the pane's shards on the stones beside it (round 2: four, sprayed out from the open side), flat, a hair up
    spots = [(-0.03, 0.095, 0.9, 0.55), (0.05, 0.13, 2.2, 0.45), (0.12, 0.075, -0.6, 0.4), (-0.09, 0.16, 1.4, 0.35)]
    bm = bmesh.new()
    bm.from_mesh(me)
    for gone, (gx, gz, gr, sc) in zip(ground, spots):
        c0 = sum(gone, Vector((0, 0))) / len(gone)
        gone = [c0 + (q - c0) * sc for q in gone]
        if len(gone) > 2:
            gone.insert(2, (gone[1] + gone[2]) * 0.5 + (gone[1] - gone[2]).orthogonal().normalized() * 0.003)
        sb = shard_bm(gone)
        uvl = sb.loops.layers.uv.verify()
        for f in sb.faces:
            for l in f.loops:
                l[uvl].uv = (0.5 + l.vert.co.x / W, l.vert.co.y / H)
        c = sum(gone, Vector((0, 0))) / len(gone)
        at = (L.T(gx, 0.002, gz) @ L.R('Y', gr) @ L.R('Z', rnd.uniform(-0.12, 0.12))
              @ L.R('X', -math.pi / 2 + rnd.uniform(0.03, 0.09)) @ L.T(-c.x, -c.y, 0))
        sb.transform(L.G2B @ at)
        sm = bpy.data.meshes.new('tmp')
        sb.to_mesh(sm)
        sb.free()
        n0 = len(bm.faces)
        bm.from_mesh(sm)
        bm.faces.ensure_lookup_table()
        for f in bm.faces[n0:]:
            f.material_index = 1
            f.smooth = False
        bpy.data.meshes.remove(sm)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True, export_apply=True,
                              export_yup=True, export_image_format='AUTO', export_materials='EXPORT')
    xs = [v.co.x for v in me.vertices]; ys = [v.co.y for v in me.vertices]; zs = [v.co.z for v in me.vertices]
    print(f'LAMP_DROPPED {OUT}: {L.tris(ob)} tris, box x {min(xs):.3f}..{max(xs):.3f} '
          f'z(game -) {min(ys):.3f}..{max(ys):.3f} up {min(zs):.3f}..{max(zs):.3f}')


main()
