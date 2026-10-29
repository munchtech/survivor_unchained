"""The world's lamp holders, made here from nothing (no kit, no scan).

    blender -b -P tools/assets/env_lamps.py

Four holders, each one GLB in godot/art/world/lamps/ with its LOD1 (about
40% of the triangles, the node named <name>_LOD1) beside it:

  ford_lamp      the keeper's lamp-iron (BossViews.cs LampIron: a square
                 black-iron cage, four corner posts, top plate, cap and
                 ring), big (cage about 0.5 m), glass panes, for the Low
                 Ford's three pylons. Origin: the foot, centred.
  post_lantern   the Watch's road lamp: a timber post, an arm out along +Z
                 braced from below, the lamp-iron hanging from it. In the
                 KayKit post_lantern's frame: the lamp's middle at
                 (0, 2.17, 1.12), where the web game hangs its flame.
  lantern_standing  a lamp-iron with a bail, to stand on the ground, in the
                 KayKit lantern_standing's box (0.925 tall).
  torch_mounted  an iron wall bracket holding a wrapped torch, in the KayKit
                 torch_mounted's frame (the wall at z = 0, out along +Z),
                 the head's top under the web game's flame (0, 0.75, 0.35).

Two materials each: lamp_atlas (iron | pitch | wood, one 512 map baked here
from noise, with its roughness/metal map) and lamp_glass (replaced in the
game by a fresnel shader, shaders/lamp_glass.gdshader). The flame is the
game's (FlameKit); where it sits is written to lamps.json beside the GLBs.
Look bible 10 and 11: <= 1.5k triangles, iron albedo >= 0.04 linear.
"""
import json
import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'godot', 'art', 'world', 'lamps')
TEX = 512

# Atlas regions (u0, u1) over the full height; physical size each spans (m).
REG = {'iron': (0.0, 0.25, 0.8), 'pitch': (0.25, 0.375, 0.5), 'wood': (0.375, 1.0, 3.4)}


# ------------------------------------------------------------- textures --

def noise(shape, seed, octaves=5, base=4):
    rng = np.random.default_rng(seed)
    h, w = shape
    out = np.zeros(shape, np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        n = base * 2 ** o
        g = rng.random((n + 1, n + 1)).astype(np.float32)
        g[-1, :] = g[0, :]
        g[:, -1] = g[:, 0]
        ys = np.linspace(0, n, h, endpoint=False)
        xs = np.linspace(0, n, w, endpoint=False)
        y0, x0 = ys.astype(int), xs.astype(int)
        fy, fx = (ys - y0)[:, None], (xs - x0)[None, :]
        fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
        a = g[y0][:, x0]; b = g[y0][:, x0 + 1]; c = g[y0 + 1][:, x0]; d = g[y0 + 1][:, x0 + 1]
        out += amp * ((a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy)
        tot += amp
        amp *= 0.55
    return out / tot


def atlas():
    """Albedo (linear) and roughness/metal, TEX square, row 0 at the bottom (v = 0)."""
    H = W = TEX
    col = np.zeros((H, W, 3), np.float32)
    rough = np.zeros((H, W), np.float32)
    metal = np.zeros((H, W), np.float32)
    u = (np.arange(W) + 0.5) / W
    for seed, (name, (u0, u1, _)) in enumerate(REG.items()):
        x0, x1 = int(u0 * W), int(u1 * W)
        w = x1 - x0
        n1 = noise((H, w), 100 + seed, 5, 4)
        n2 = noise((H, w), 200 + seed, 4, 16)
        if name == 'iron':
            # Hammered black iron, never pure black (>= 0.04 linear), rust
            # in patches, the odd bright scuff where a hand has worn it.
            v = 0.052 + 0.03 * (n1 - 0.5) + 0.018 * (n2 - 0.5)
            rust = np.clip((noise((H, w), 31, 4, 6) - 0.62) * 5, 0, 1)
            c = np.stack([v, v * 0.96, v * 0.92], -1)
            r = np.stack([0.11 + 0.03 * n2, 0.055 + 0.015 * n2, 0.03 + 0.01 * n2], -1)
            c = c * (1 - rust[..., None]) + r * rust[..., None]
            col[:, x0:x1] = np.maximum(c, 0.042)
            rough[:, x0:x1] = 0.5 + 0.12 * n2 + 0.25 * rust
            metal[:, x0:x1] = 0.7 * (1 - rust) + 0.1
        elif name == 'pitch':
            # Rag wound round and soaked in pitch: bands across, charred.
            yy = np.arange(H)[:, None] / H
            band = 0.5 + 0.5 * np.sin((yy * 38 + 0.6 * n1) * math.tau)
            v = 0.045 + 0.03 * band * n2 + 0.02 * (n1 - 0.5)
            col[:, x0:x1] = np.stack([v * 1.1, v * 0.95, v * 0.8], -1)
            rough[:, x0:x1] = 0.75 - 0.2 * band * n2
            metal[:, x0:x1] = 0
        else:
            # Weathered timber: grey-brown, grain along v, wavy, with dark
            # checks; light enough to read under a 20-degree moon.
            xx = np.arange(w)[None, :] / w
            yy = np.arange(H)[:, None] / H
            warp = noise((H, w), 77, 3, 3)
            grain = 0.5 + 0.5 * np.sin((xx * 46 + warp * 3.0 + 0.4 * np.sin(yy * 9)) * math.tau)
            checks = np.clip((noise((H, w), 91, 3, 24) - 0.7) * 6, 0, 1) * (grain > 0.8)
            v = 0.62 + 0.18 * grain + 0.25 * (n1 - 0.5) + 0.1 * (n2 - 0.5)
            v = v * (1 - 0.6 * checks)
            base = np.array([0.235, 0.168, 0.11], np.float32)
            grey = np.array([0.2, 0.182, 0.158], np.float32)
            weather = np.clip(noise((H, w), 13, 3, 5) * 1.2 - 0.1, 0, 1)[..., None]
            col[:, x0:x1] = (base * (1 - weather) + grey * weather) * v[..., None]
            rough[:, x0:x1] = 0.82 + 0.1 * n2
            metal[:, x0:x1] = 0
    return col, np.clip(rough, 0, 1), np.clip(metal, 0, 1)


def image(name, rgb, linear):
    img = bpy.data.images.new(name, TEX, TEX, alpha=False)
    img.colorspace_settings.name = 'Non-Color' if linear else 'sRGB'
    px = np.ones((TEX, TEX, 4), np.float32)
    if not linear:
        rgb = np.where(rgb <= 0.0031308, rgb * 12.92, 1.055 * np.power(np.clip(rgb, 0, None), 1 / 2.4) - 0.055)
    px[..., :3] = np.clip(rgb, 0, 1)
    img.pixels.foreach_set(px.ravel())
    img.file_format = 'PNG'
    img.pack()
    return img


def materials():
    col, rough, metal = atlas()
    a = image('lamp_atlas_albedo', col, False)
    mr = image('lamp_atlas_mr', np.stack([np.ones_like(rough), rough, metal], -1), True)
    m = bpy.data.materials.new('lamp_atlas')
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
    g = bpy.data.materials.new('lamp_glass')
    g.use_nodes = True
    b = g.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.32, 0.28, 0.2, 1)
    b.inputs['Alpha'].default_value = 0.22
    b.inputs['Roughness'].default_value = 0.12
    g.blend_method = 'BLEND'
    return m, g


# ------------------------------------------------------------- geometry --
# Everything is written in the game's frame (y up, +z out) and turned to
# Blender's (z up) only when a piece goes into its mesh: (x, y, z) -> (x, -z, y).

G2B = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))


class Part:
    """One piece in its own frame (its long axis local y), the atlas region
    its UVs go to (or 'glass'), placed by a matrix in the game's frame."""

    def __init__(self, bm, region, at=Matrix.Identity(4)):
        self.bm, self.region, self.at = bm, region, at


def cube(sx, sy, sz, bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, segments=1, affect='EDGES', profile=0.5)
    return bm


def lathe(profile, segs, rot=0.0, cap=True):
    """A solid of revolution about local y: profile [(r, y)] bottom to top."""
    bm = bmesh.new()
    rings = []
    for r, y in profile:
        ring = []
        for k in range(segs if r > 1e-6 else 1):
            a = rot + k * math.tau / segs
            ring.append(bm.verts.new((r * math.cos(a), y, r * math.sin(a))))
        rings.append(ring)
    for r0, r1 in zip(rings, rings[1:]):
        if len(r0) == 1 and len(r1) == 1:
            continue
        for k in range(segs):
            if len(r0) == 1:
                bm.faces.new((r0[0], r1[(k + 1) % segs], r1[k]))
            elif len(r1) == 1:
                bm.faces.new((r0[k], r0[(k + 1) % segs], r1[0]))
            else:
                bm.faces.new((r0[k], r0[(k + 1) % segs], r1[(k + 1) % segs], r1[k]))
    if cap:
        if len(rings[0]) > 1:
            bm.faces.new(list(reversed(rings[0])))
        if len(rings[-1]) > 1:
            bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def torus(R, r, segs, tube):
    """A ring in the local xy plane (standing up, to hang by)."""
    bm = bmesh.new()
    grid = []
    for i in range(segs):
        a = i * math.tau / segs
        c, d = Vector((math.cos(a), math.sin(a), 0)), Vector((0, 0, 1))
        grid.append([bm.verts.new(c * (R + r * math.cos(b)) + d * (r * math.sin(b)))
                     for b in (j * math.tau / tube for j in range(tube))])
    for i in range(segs):
        for j in range(tube):
            a, b = grid[i], grid[(i + 1) % segs]
            bm.faces.new((a[j], b[j], b[(j + 1) % tube], a[(j + 1) % tube]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def arc(R, r, segs, tube, a0, a1):
    """An open bent rod in the local xy plane from angle a0 to a1."""
    bm = bmesh.new()
    grid = []
    for i in range(segs + 1):
        a = a0 + (a1 - a0) * i / segs
        c, d = Vector((math.cos(a), math.sin(a), 0)), Vector((0, 0, 1))
        grid.append([bm.verts.new(c * (R + r * math.cos(b)) + d * (r * math.sin(b)))
                     for b in (j * math.tau / tube for j in range(tube))])
    for i in range(segs):
        for j in range(tube):
            a, b = grid[i], grid[i + 1]
            bm.faces.new((a[j], b[j], b[(j + 1) % tube], a[(j + 1) % tube]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def rod(p0, p1, w, segs=4, region='iron'):
    """A rod from p0 to p1 (game frame), square (segs 4) or round."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    bm = lathe([(w, 0), (w, d.length)], segs, rot=math.pi / 4)
    q = Vector((0, 1, 0)).rotation_difference(d.normalized())
    return Part(bm, region, Matrix.Translation(p0) @ q.to_matrix().to_4x4())


def T(x, y, z):
    return Matrix.Translation((x, y, z))


def R(axis, a):
    return Matrix.Rotation(a, 4, axis)


def pane(w, h):
    """A flat quad in local xy, facing +z."""
    bm = bmesh.new()
    v = [bm.verts.new(p) for p in ((-w / 2, 0, 0), (w / 2, 0, 0), (w / 2, h, 0), (-w / 2, h, 0))]
    bm.faces.new(v)
    return bm


def lamp_iron(W, H, at=Matrix.Identity(4), ring=True, bail=0.0, feet=False, fine=True, stem=0.0, rim=0.14, hood_gap=0.16):
    """The keeper's lamp-iron, its foot at the origin: a stepped base, the
    burner cup, four corner posts with a band at mid height, glass between,
    a top plate, a four-sided cap with a finial and a ring to hang it by.
    stem raises the burner on a rod (m), rim is the top frame's width over W, hood_gap the
    hood's height over the frame over W: the ford's big iron, seen from the play camera
    (23 m, 55-60 degrees down), shows its flame through a wide open top under a high hood.
    Returns (parts, the flame's place, the top of the ring)."""
    parts = []
    t = 0.15 * W           # plate thickness
    y = 0.0
    if feet:
        for sx in (-1, 1):
            for sz in (-1, 1):
                parts.append(Part(lathe([(0.07 * W, 0), (0.05 * W, 0.08 * W), (0, 0.08 * W)], 4, math.pi / 4), 'iron',
                                  at @ T(sx * 0.4 * W, 0, sz * 0.4 * W)))
        y = 0.08 * W
    parts.append(Part(cube(1.08 * W, 0.06 * W, 1.08 * W, 0.012 * W if fine else 0), 'iron', at @ T(0, y + 0.03 * W, 0)))
    y += 0.06 * W
    parts.append(Part(cube(W, t, W, 0.02 * W if fine else 0), 'iron', at @ T(0, y + t / 2, 0)))
    y += t
    base_top = y
    # The burner: a squat cup with a lip (on a stem, raised).
    if stem > 0:
        r = rod((0, y, 0), (0, y + stem + 0.01 * W, 0), 0.03 * W)
        r.at = at @ r.at
        parts.append(r)
        y += stem
    parts.append(Part(lathe([(0.16 * W, 0), (0.13 * W, 0.1 * W), (0.16 * W, 0.13 * W), (0.12 * W, 0.13 * W), (0, 0.11 * W)], 6, cap=True), 'iron',
                      at @ T(0, y, 0)))
    flame = y + 0.13 * W
    # The corner posts and the glass between.
    p = 0.075 * W
    for sx in (-1, 1):
        for sz in (-1, 1):
            parts.append(Part(cube(p, H, p, 0.012 * W if fine else 0), 'iron', at @ T(sx * (0.5 * W - p / 2), y + H / 2, sz * (0.5 * W - p / 2))))
    g = 0.5 * W - p * 0.6
    for k in range(4):
        parts.append(Part(pane(W - 2 * p * 0.8, H), 'glass', at @ T(0, y, 0) @ R('Y', k * math.pi / 2) @ T(0, 0, g)))
    # A band round at mid height, and a cross-stay on each face below it (the cage).
    for k in range(4):
        rot = at @ T(0, y, 0) @ R('Y', k * math.pi / 2)
        parts.append(Part(cube(W - p, 0.045 * W, 0.04 * W), 'iron', rot @ T(0, 0.62 * H, 0.5 * W - p / 2)))
        if fine:
            parts.append(Part(cube(0.035 * W, 0.62 * H, 0.03 * W), 'iron', rot @ T(0, 0.31 * H, 0.5 * W - p / 2 + 0.005 * W)))
    y += H
    # The top: a square frame, open in the middle so the flame shows from the play camera's height (a
    # plate hid it), and over it on four short struts a small hood (the cap) that smoke leaves under.
    tf = rim * W
    th = t * 0.8 * min(1.0, rim / 0.14 + 0.25)
    for k in range(4):
        rot = at @ R('Y', k * math.pi / 2)
        parts.append(Part(cube(W * 1.04, th, tf), 'iron', rot @ T(0, y + th / 2, 0.52 * W - tf / 2)))
    y += th
    gap = hood_gap * W
    for sx in (-1, 1):
        for sz in (-1, 1):
            # (in the iron's frame: these stood at the holder's origin when the iron was hung elsewhere)
            r = rod((sx * 0.4 * W, y - 0.01 * W, sz * 0.4 * W), (sx * 0.17 * W, y + gap + 0.02 * W, sz * 0.17 * W), 0.02 * W)
            r.at = at @ r.at
            parts.append(r)
    y += gap
    parts.append(Part(lathe([(0.3 * W, 0), (0.27 * W, 0.03 * W), (0.1 * W, 0.18 * W), (0.07 * W, 0.2 * W), (0.07 * W, 0.25 * W), (0, 0.27 * W)], 4, math.pi / 4), 'iron',
                      at @ T(0, y, 0)))
    y += 0.27 * W
    top = y
    if ring:
        rr = 0.13 * W
        parts.append(Part(torus(rr, 0.03 * W, 10 if fine else 8, 4), 'iron', at @ T(0, y + rr + 0.02 * W, 0)))
        top = y + 2 * rr + 0.05 * W
    if bail > 0:
        # A bail: a hoop of rod over the cap from the top plate's sides.
        parts.append(Part(arc(0.5 * W, 0.022 * W, 10, 4, 0, math.pi), 'iron', at @ T(0, base_top + H + t * 0.4, 0)))
        top = max(top, base_top + H + t * 0.4 + 0.5 * W)
    return parts, flame, top


# --------------------------------------------------------------- pieces --

def ford_lamp():
    """The Warden's lamp-iron, big, standing on a pylon's top."""
    parts, flame, top = lamp_iron(0.44, 0.5, stem=0.08, rim=0.06, hood_gap=0.45)
    return parts, {'flame': [0, flame + 0.07, 0], 'height': top}


def post_lantern():
    """The Watch's lamp post in the KayKit frame (arm out along +Z)."""
    parts = []
    P = 0.15
    # The post: square timber, chamfered, sunk a little; a cap block on top.
    parts.append(Part(cube(P, 3.2, P, 0.018), 'wood', T(0, 2.9 - 1.6, 0)))
    parts.append(Part(cube(P + 0.04, 0.06, P + 0.04, 0.012), 'wood', T(0, 2.93, 0)))
    # The arm, its long axis along z (the wood's grain along local y, turned).
    arm_y = 2.72
    parts.append(Part(cube(0.09, 1.34, 0.11, 0.012), 'wood', T(0, arm_y, 0.6) @ R('X', math.pi / 2)))
    # The brace, from the post up to the arm's underside.
    a, b = Vector((0, 2.12, P / 2)), Vector((0, arm_y - 0.055, 0.68))
    d = b - a
    parts.append(Part(cube(0.065, d.length + 0.08, 0.065, 0.01), 'wood',
                      T(*((a + b) / 2)) @ Vector((0, 1, 0)).rotation_difference(d.normalized()).to_matrix().to_4x4()))
    # Iron: a strap round the post at the arm, a strap at the brace's foot, a hook at the arm's end.
    parts.append(Part(cube(P + 0.016, 0.05, P + 0.016), 'iron', T(0, arm_y, 0)))
    parts.append(Part(cube(P + 0.016, 0.04, P + 0.016), 'iron', T(0, 2.12, 0)))
    parts.append(Part(cube(0.1, 0.03, 0.14), 'iron', T(0, arm_y + 0.07, 1.12)))
    # The lamp-iron hanging: its middle at 2.17, by a ring on an S-hook from the arm.
    W, H = 0.24, 0.27
    foot = 2.17 - (0.06 * W + 0.15 * W + H / 2)
    lamp, flame, top = lamp_iron(W, H, T(0, foot, 1.12), fine=False)
    parts += lamp
    parts.append(rod((0, top + foot - 0.03, 1.12), (0, arm_y - 0.055, 1.12), 0.008))
    parts.append(Part(torus(0.03, 0.007, 8, 4), 'iron', T(0, arm_y - 0.08, 1.12) @ R('Y', math.pi / 2)))
    return parts, {'flame': [0, foot + flame + 0.035, 1.12], 'height': 2.96}


def lantern_standing():
    """A lamp-iron with feet and a bail, standing in the KayKit box (0.925 tall)."""
    W, H = 0.3, 0.36
    parts, flame, top = lamp_iron(W, H, feet=True, ring=False, bail=1.0)
    return parts, {'flame': [0, flame + 0.045, 0], 'height': top}


def torch_mounted():
    """An iron bracket on the wall (z = 0) holding a wrapped torch, leaning out."""
    parts = []
    # The wall plate, with four rivets.
    parts.append(Part(cube(0.11, 0.3, 0.02, 0.004), 'iron', T(0, 0.05, 0.01)))
    for sy in (-0.1, 0.2):
        parts.append(Part(lathe([(0.012, 0), (0.008, 0.008), (0, 0.009)], 4, math.pi / 4), 'iron', T(0, sy, 0.02) @ R('X', math.pi / 2)))
    # The shaft's line: from its foot out and up to under the head.
    foot, head = Vector((0, -0.2, 0.2)), Vector((0, 0.48, 0.33))
    axis = (head - foot).normalized()
    turn = Vector((0, 1, 0)).rotation_difference(axis).to_matrix().to_4x4()
    # The arm out from the plate to a collar round the shaft, and a stay under it.
    collar = foot + axis * 0.38
    parts.append(rod((0, 0.12, 0.02), (0, collar.y, collar.z - 0.035), 0.012))
    parts.append(rod((0, -0.07, 0.02), (0, collar.y - 0.14, collar.z - 0.03), 0.009))
    parts.append(Part(lathe([(0.04, -0.02), (0.04, 0.02)], 8, cap=False), 'iron', T(*collar) @ turn))
    parts.append(Part(lathe([(0.036, -0.012), (0.036, 0.012)], 8, cap=False), 'iron', T(*(foot + axis * 0.12)) @ turn))
    # A small cup the shaft's foot sits in, on a rod from the plate.
    parts.append(rod((0, -0.12, 0.02), (0, foot.y + 0.05, foot.z), 0.01))
    # The shaft, turned wood, tapering to the head.
    parts.append(Part(lathe([(0.02, 0), (0.026, 0.12), (0.03, 0.55), (0, 0.56)], 6, cap=True), 'wood', T(*foot) @ turn))
    # The head: rag wound fat about the shaft's top, in pitch.
    prof = [(0.028, 0), (0.046, 0.03), (0.052, 0.07), (0.049, 0.11), (0.054, 0.15), (0.044, 0.19), (0.02, 0.205), (0, 0.205)]
    parts.append(Part(lathe(prof, 8, cap=True), 'pitch', T(*(foot + axis * 0.5)) @ turn))
    tip = foot + axis * 0.7
    return parts, {'flame': [0, tip.y + 0.04, tip.z + 0.01], 'height': 0.75}


# ---------------------------------------------------------------- build --

def uv_part(bm, region):
    """Box-project the part's faces into its region of the atlas, in its own
    frame (so a timber's grain runs along its length, local y)."""
    uvl = bm.loops.layers.uv.verify()
    if region == 'glass':
        # The pane's own 0..1 (the game's v runs down: 0 at its top), for its soot.
        top = max(v.co.y for v in bm.verts) or 1.0
        for f in bm.faces:
            for l in f.loops:
                co = l.vert.co
                l[uvl].uv = (0.5 + co.x, co.y / top)
        return
    u0, u1, size = REG[region]
    # The region spans `size` metres down v and (u1 - u0) of that across u, at the same texel density.
    span_u = size * (u1 - u0)
    # Each part starts at its own place down the region, so like parts don't repeat.
    off = (len(bm.verts) * 0.137) % 0.5
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for l in f.loops:
            c = l.vert.co
            if ax == 1:
                a, b = c.x, c.z
            elif ax == 0:
                a, b = c.z, c.y
            else:
                a, b = c.x, c.y
            uu = a / span_u + 0.5
            vv = b / size + off
            l[uvl].uv = (u0 + (u1 - u0) * min(max(uu, 0.02), 0.98), min(max(vv, 0.0), 1.0))


def build(name, parts, atlas_mat, glass_mat):
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.verify()
    for p in parts:
        uv_part(p.bm, p.region)
        p.bm.transform(G2B @ p.at)
        idx = 1 if p.region == 'glass' else 0
        me = bpy.data.meshes.new('tmp')
        p.bm.to_mesh(me)
        n0 = len(bm.faces)
        bm.from_mesh(me)
        bm.faces.ensure_lookup_table()
        for f in bm.faces[n0:]:
            f.material_index = idx
        bpy.data.meshes.remove(me)
        p.bm.free()
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(atlas_mat)
    me.materials.append(glass_mat)
    for poly in me.polygons:
        poly.use_smooth = False
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def lod1(ob, ratio=0.4):
    c = ob.copy()
    c.data = ob.data.copy()
    c.name = ob.name + '_LOD1'
    bpy.context.scene.collection.objects.link(c)
    m = c.modifiers.new('dec', 'DECIMATE')
    m.ratio = ratio
    m.use_collapse_triangulate = True
    bpy.context.view_layer.objects.active = c
    bpy.ops.object.modifier_apply(modifier='dec')
    return c


def tris(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    os.makedirs(OUT, exist_ok=True)
    atlas_mat, glass_mat = materials()
    info = {}
    for name, fn in (('ford_lamp', ford_lamp), ('post_lantern', post_lantern),
                     ('lantern_standing', lantern_standing), ('torch_mounted', torch_mounted)):
        for o in list(bpy.context.scene.collection.objects):
            bpy.data.objects.remove(o)
        parts, meta = fn()
        ob = build(name, parts, atlas_mat, glass_mat)
        lo = lod1(ob)
        bpy.ops.object.select_all(action='DESELECT')
        ob.select_set(True)
        lo.select_set(True)
        path = os.path.join(OUT, name + '.glb')
        bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True,
                                  export_yup=True, export_image_format='AUTO', export_materials='EXPORT')
        meta.update({'tris': tris(ob), 'tris_lod1': tris(lo), 'materials': len(ob.data.materials)})
        info[name] = meta
        print(f'LAMP {name}: {meta}')
    with open(os.path.join(OUT, 'lamps.json'), 'w') as f:
        json.dump(info, f, indent=1)


if __name__ == '__main__':
    main()
