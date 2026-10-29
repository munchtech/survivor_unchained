"""The Ford-Warden's lantern (BossViews WardenView, Pendant; LampIron.MakeWarden), concept A, boss-prop detail.

    blender -b -P tools/assets/warden_lamp.py

Concept A (warden_concepts/pick/A_fist.png): a tall narrow black-iron cage, about 2:1, under a ribbed
arched dome with a collar, a finial and the ring it hangs by. Angle-iron corners, one flat strap down
each side's middle, four riveted flat bands (a rim under the dome, one over the flame, one at its foot, one at the base), a hinged
door post and latch, a stepped base on four ball feet, a small oil font with its wick, dark glass behind
the bars and in the dome. A chain link through the ring for the fist (LampIron shows it when hung).
The helpers (box, lathe, tube, rivet, build) and the iron masks are lamp_iron.py's: the sill lamp
(keeper_lamp.glb) is unchanged.

Out: godot/art/props/keeper_lamp/warden_lamp.glb, nodes
  Cage       the iron that throws the straps' shadows (corners, straps, bands, rivets)
  Trim       the rim's lip, the hinge and latch, the base and font (no shadow: the flame lights up and down past them)
  Cap        the dome's ribs, collar, finial and ring (no shadow: the flame's light reaches up past it)
  Bail       the link the fist closes on
  Glass      the four panes (UV: u across, v down each pane)
  GlassDome  the dome's glass (UV: u across each quarter, v low = sooty)
Frame (the game's, y up): the ring's centre at the origin; the wick's top at y = WICK, the feet at FOOT
(LampIron.Warden* mirror these).
"""
import math
import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lamp_iron as L  # noqa: E402  (its main() only runs as a script)
from lamp_iron import T, RY, RX, box, lathe, tube, rivet, build, tris  # noqa: E402

HALF = 0.060           # the posts' outer faces
POST = 0.0095
TOP = -0.078           # the rim under the dome
BASE = -0.258          # the base plate's top
DOME_H = 0.050
COLLAR_R = 0.0125
# (Warden 7 r1 judge: the thin square bars read as a round birdcage at the play camera. Concept A's flat riveted
# straps instead: angle-iron corners, one broad flat strap down each side's middle, four riveted bands.)
STRAP_W, STRAP_T = 0.0092, 0.0026      # the side's middle strap
ANGLE_W, ANGLE_T = 0.0125, 0.0026      # each leaf of a corner's angle iron
BANDS = ((TOP - 0.0045, 0.011), (-0.140, 0.0085), (-0.2245, 0.0085), (BASE + 0.0055, 0.011))   # (centre y, height)
WICK = -0.2085
FOOT = -0.282


def dome_pt(u, v, out=0.0):
    """The dome over the square cage: u round the perimeter (0..4, a side each, corners at the integers),
    v up (0 the rim, 1 the collar); square at the rim easing to round, a quarter-ellipse arch."""
    k = int(math.floor(u)) % 4
    f = u - math.floor(u)
    x, z = -HALF + 2 * HALF * f, HALF
    c, s = math.cos(-k * math.pi / 2), math.sin(-k * math.pi / 2)
    sx, sz = x * c + z * s, -x * s + z * c
    a = math.atan2(sz, sx)
    ease = v * v * (3 - 2 * v)
    bx = sx + (HALF * 1.04 * math.cos(a) - sx) * ease
    bz = sz + (HALF * 1.04 * math.sin(a) - sz) * ease
    hs = COLLAR_R / HALF + (1 - COLLAR_R / HALF) * math.cos(v * math.pi / 2)
    rr = math.hypot(bx, bz)
    k2 = (rr * hs + out) / max(rr, 1e-6)
    return (bx * k2, TOP + DOME_H * math.sin(v * math.pi / 2), bz * k2)


def cage_parts():
    parts = []
    H, yc = TOP - BASE, (TOP + BASE) / 2
    for sx in (-1, 1):
        for sz in (-1, 1):
            # The corner's angle iron: two flat leaves on the outer faces, a thin core where they meet.
            parts.append((box(ANGLE_W, H, ANGLE_T, 0.0008), T(sx * (HALF - ANGLE_W / 2), yc, sz * (HALF - ANGLE_T / 2))))
            parts.append((box(ANGLE_T, H, ANGLE_W, 0.0008), T(sx * (HALF - ANGLE_T / 2), yc, sz * (HALF - ANGLE_W / 2))))
            parts.append((box(0.0045, H, 0.0045, 0.0006), T(sx * (HALF - 0.0035), yc, sz * (HALF - 0.0035))))
    for k in range(4):
        side = RY(k * math.pi / 2)
        # The side's middle strap, flat to the glass, under the bands.
        parts.append((box(STRAP_W, H, STRAP_T, 0.0008), side @ T(0, yc, HALF - STRAP_T / 2)))
        for y, h in BANDS:
            th = 0.0032
            parts.append((box(2 * HALF + 2 * th, h, th, 0.0010), side @ T(0, y, HALF + th / 2)))
            for x in (-HALF + ANGLE_W / 2, 0.0, HALF - ANGLE_W / 2):
                parts.append((rivet(0.0026 if x == 0.0 else 0.0024), side @ T(x, y, HALF + th) @ RX(math.pi / 2)))
        # The strap's own rivets between the bands (where it is riveted to the frame).
        for y in ((TOP - 0.0045 + -0.140) / 2, (-0.140 + -0.2245) / 2):
            parts.append((rivet(0.0021), side @ T(0, y, HALF) @ RX(math.pi / 2)))
    return parts


def trim_parts():
    """The lamp's solid iron above and below the flame and its small fittings: no shadow (Warden 7 r1: the rim's lip
    and the base plate in the flame's light threw cones that kept his fist, his hood and the pool on the river dark)."""
    parts = []
    # The rim's lip, proud of the top band, that the dome sits in.
    parts.append((box(2 * HALF + 0.011, 0.0035, 2 * HALF + 0.011, 0.0012), T(0, TOP + 0.0005, 0)))
    # The door: two hinge knuckles on the front-left post, a latch on the front-right.
    for y in (-0.105, -0.19):
        parts.append((lathe([(0.0034, y - 0.008), (0.0036, y - 0.0065), (0.0036, y + 0.0065), (0.0034, y + 0.008)], 8),
                      T(-HALF + 0.0005, 0, HALF + 0.0005)))
    parts.append((box(0.006, 0.014, 0.004, 0.0009), T(HALF - POST / 2, -0.15, HALF + 0.0022)))
    parts.append((box(0.0035, 0.004, 0.006, 0.0008), T(HALF - POST / 2 - 0.004, -0.15, HALF + 0.004)))
    # The base: a plate, a step under it, four ball feet; the oil font on the plate, its burner, its wick.
    parts.append((box(2 * HALF + 0.012, 0.010, 2 * HALF + 0.012, 0.0020), T(0, BASE - 0.005, 0)))
    parts.append((box(2 * HALF - 0.004, 0.005, 2 * HALF - 0.004, 0.0014), T(0, BASE - 0.0125, 0)))
    for sx in (-1, 1):
        for sz in (-1, 1):
            parts.append((lathe([(0.0001, FOOT), (0.004, FOOT + 0.0008), (0.0062, FOOT + 0.003), (0.0068, FOOT + 0.0055),
                                 (0.0058, FOOT + 0.0082), (0.0045, FOOT + 0.0095)], 8, math.pi / 8),
                          T(sx * (HALF - 0.010), 0, sz * (HALF - 0.010))))
    parts.append((lathe([(0.024, BASE), (0.027, BASE + 0.004), (0.027, BASE + 0.012), (0.022, BASE + 0.020),
                         (0.012, BASE + 0.025), (0.0072, BASE + 0.027), (0.0066, BASE + 0.036), (0.0082, BASE + 0.039),
                         (0.0076, BASE + 0.043), (0.005, BASE + 0.045), (0.0, BASE + 0.045)], 18), T(0, 0, 0)))
    parts.append((lathe([(0.0017, BASE + 0.044), (0.0014, WICK - 0.001), (0.0, WICK)], 6), T(0, 0, 0)))
    return parts


def cap_parts():
    parts = []
    # Eight ribs over the dome: the corners and the sides' middles.
    for u in (0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5):
        pts = [dome_pt(u, j / 14, 0.0022) for j in range(15)]
        parts.append((tube(pts, 0.0026 if u == int(u) else 0.0021, 4, False), T(0, 0, 0)))
    yc = TOP + DOME_H
    parts.append((lathe([(COLLAR_R + 0.0025, yc - 0.003), (COLLAR_R + 0.003, yc), (COLLAR_R + 0.0025, yc + 0.003),
                         (0.009, yc + 0.0045), (0.0065, yc + 0.0075), (0.0078, yc + 0.0105), (0.0078, yc + 0.0125),
                         (0.005, yc + 0.0155), (0.0042, yc + 0.0185), (0.0, yc + 0.019)], 16, math.pi / 16), T(0, 0, 0)))
    R, r = 0.0145, 0.0033
    pts = [(R * math.cos(a), R * math.sin(a), 0) for a in (k * math.tau / 28 for k in range(28))]
    parts.append((tube(pts, r, 8, True), T(0, 0, 0)))
    return parts


def bail_parts():
    """A chain link through the ring, in the y-z plane, up to where the fist closes (0.092 at the top, as lamp_iron's)."""
    a, b, w, r = 0.006, 0.092, 0.0115, 0.0034
    pts = []
    for k in range(9):
        t = math.pi + k * math.pi / 8
        pts.append((0, a + w + w * math.sin(t), w * math.cos(t)))
    for k in range(9):
        t = k * math.pi / 8
        pts.append((0, b - w + w * math.sin(t), w * math.cos(t)))
    return [(tube(pts, r, 8, True), T(0, 0, 0))]


def glass_parts():
    parts = []
    z = HALF - 0.0072
    w, y0, y1 = 2 * (HALF - POST) + 0.004, BASE, TOP
    for k in range(4):
        bm = bmesh.new()
        uv = bm.loops.layers.uv.verify()
        cols, rows = 4, 8
        vs = [[bm.verts.new((-w / 2 + w * i / cols, y1 - (y1 - y0) * j / rows,
                             z + 0.001 * math.sin(math.pi * i / cols) * math.sin(math.pi * j / rows)))
               for i in range(cols + 1)] for j in range(rows + 1)]
        for j in range(rows):
            for i in range(cols):
                f = bm.faces.new((vs[j + 1][i], vs[j + 1][i + 1], vs[j][i + 1], vs[j][i]))
                for l, (ii, jj) in zip(f.loops, ((i, j + 1), (i + 1, j + 1), (i + 1, j), (i, j))):
                    l[uv].uv = (ii / cols, 1 - jj / rows)
        parts.append((bm, RY(k * math.pi / 2)))
    return parts


def dome_glass():
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()
    nu, nv = 32, 8
    vs = [[bm.verts.new(dome_pt(4 * i / nu if i < nu else 3.99999, j / nv, -0.0004)) for i in range(nu + 1)] for j in range(nv + 1)]
    for j in range(nv):
        for i in range(nu):
            f = bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
            for l, (ii, jj) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                fu = (ii % (nu // 4)) / (nu // 4) if not (ii == i + 1 and ii % (nu // 4) == 0) else 1.0
                # glTF's v down: the rim at 0.3, the collar at 0 (the shader's soot toward the top).
                l[uv].uv = (fu, 0.3 * (1 - jj / nv))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return [(bm, T(0, 0, 0))]


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    iron = bpy.data.materials.new('keeper_iron')
    iron.diffuse_color = (0.04, 0.038, 0.035, 1)
    glass = bpy.data.materials.new('keeper_glass')
    glass.diffuse_color = (0.3, 0.32, 0.3, 0.3)
    obs = [build('Cage', cage_parts(), iron), build('Trim', trim_parts(), iron), build('Cap', cap_parts(), iron), build('Bail', bail_parts(), iron),
           build('Glass', glass_parts(), glass, colour=False), build('GlassDome', dome_glass(), glass, colour=False)]
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:
        o.select_set(True)
    path = os.path.join(L.OUT, 'warden_lamp.glb')
    kw = dict(filepath=path, export_format='GLB', use_selection=True, export_apply=True, export_yup=True,
              export_materials='EXPORT')
    try:
        bpy.ops.export_scene.gltf(**kw, export_vertex_color='ACTIVE')
    except TypeError:
        bpy.ops.export_scene.gltf(**kw, export_colors=True)
    fix_colours(path)
    print('LAMP tris', {o.name: tris(o) for o in obs}, 'total', sum(tris(o) for o in obs))
    # A look at it (Workbench, dark iron and the glass dim): for checking the shape before the game.
    if os.environ.get('LAMP_PREVIEW'):
        sc = bpy.context.scene
        sc.render.engine = 'BLENDER_WORKBENCH'
        sc.display.shading.light = 'STUDIO'
        sc.display.shading.color_type = 'SINGLE'
        sc.display.shading.single_color = (0.35, 0.35, 0.37)
        sc.render.resolution_x, sc.render.resolution_y = 600, 900
        cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
        sc.collection.objects.link(cam)
        cam.location = (0.62, -0.92, -0.13)
        cam.data.lens = 85
        cam.rotation_euler = (math.radians(92), 0, math.radians(34))
        sc.camera = cam
        sc.render.filepath = os.environ['LAMP_PREVIEW']
        bpy.ops.render.render(write_still=True)


def fix_colours(path):
    """Blender 4.5's exporter writes a white COLOR_0 and the real 'Col' layer as COLOR_1; Godot reads only COLOR_0, so
    keeper_iron saw every vertex white (R convexity 1 = all worn edge, B part-random 1). Point COLOR_0 at the real layer
    (same fix as watch_blade.py)."""
    import json, struct
    d = open(path, 'rb').read()
    jl = struct.unpack('<I', d[12:16])[0]
    j = json.loads(d[20:20 + jl])
    for m in j['meshes']:
        for p in m['primitives']:
            a = p['attributes']
            if 'COLOR_1' in a:
                a['COLOR_0'] = a.pop('COLOR_1')
    js = json.dumps(j, separators=(',', ':')).encode()
    js += b' ' * (-len(js) % 4)
    rest = d[20 + jl:]
    out = struct.pack('<4sII', b'glTF', 2, 12 + 8 + len(js) + len(rest)) + struct.pack('<I4s', len(js), b'JSON') + js + rest
    open(path, 'wb').write(out)


if __name__ == '__main__':
    main()
