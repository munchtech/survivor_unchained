#!/usr/bin/env python3
"""The survivor's letter (Cinematics 8, C04 A insert): one open sheet, folded twice when carried, run to blue water.

    python tools/assets/letter_prop.py            (needs a Blender turn: it runs Blender for the mesh)
      ->  godot/art/props/letter/letter_open.glb
    python tools/assets/letter_prop.py --tex      (the maps only, into .shots/letter_prop/, no Blender)

The sheet is 20 x 14 cm of rag paper, unfolded: one vertical and one horizontal crease (the second fold made through
the doubled sheet, so the horizontal crease is a valley on one half and a ridge on the other), a slight tent along the
vertical crease, a curl at two corners, a little cockle from the wetting. Origin at its centre, the written face +Z,
the text upright along +Y (glTF frame).

The hand is drawn here from the Hershey script glyphs (public domain, A. V. Hershey, US NBS 1967; the strokes in
tools/assets/hershey_script.json), with our own pen: thicker on the downstrokes, a jittered baseline, a slant, each
word a little different. No font files. Nine lines and a signature; every line but one is washed to illegible streaks
(warped, bloomed, dragged down the sheet, its cores eaten), the iron-gall ink gone pale blue-grey. The one line,
"Come home by the Low Ford.", sat where the water barely reached: feathered a little, still crisp.

Maps (2048 x 1436, the sheet's 20 x 14 aspect): albedo (sRGB), normal (OpenGL, +Y up), and roughness in G of the
glTF metal-roughness map. All procedural; no credit owed.
"""
import json
import math
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
TEXDIR = os.path.join(ROOT, '.shots', 'letter_prop')
OUT = os.path.join(ROOT, 'godot', 'art', 'props', 'letter', 'letter_open.glb')
BLENDER = r'C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe'
TW, TH = 2048, 1436            # texture, px (20 x 14 cm)
SW, SH = 0.20, 0.14            # sheet, m
LEGIBLE = 'Come home by the Low Ford.'
PEBBLE = False                 # round 2: the pebble on the corner read as a burnt hole in the shot; off
LINES = [
    'My dearest, the river is high again and the',
    'lower fields are lost to it as far as the mill.',
    'Mother asks after you each evening and I tell',
    'her you are coming. They have shut the bridge',
    'road and the Watch turns all back at the gate.',
    LEGIBLE,
    'Wait for the morning, when the water is low.',
    'I will be down at the stones with a light for',
    'you, every night until you come. Be quick.',
    'ever yours, M.',
]


# ================================================================ textures (plain Python) ==

def textures():
    import numpy as np
    import cv2
    from PIL import Image

    rng = np.random.default_rng(1107)
    H, W = TH, TW
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

    def noise(scale, seed, octaves=4):
        r = np.random.default_rng(seed)
        out = np.zeros((H, W), np.float32)
        amp, tot = 1.0, 0.0
        for o in range(octaves):
            s = max(2, int(scale / 2 ** o))
            g = r.random((H // s + 3, W // s + 3)).astype(np.float32)
            up = cv2.resize(g, ((W // s + 3) * s, (H // s + 3) * s), interpolation=cv2.INTER_CUBIC)
            out += amp * up[s:s + H, s:s + W]
            tot += amp
            amp *= 0.5
        return out / tot

    # ---------------------------------------------------------------- the hand --
    glyphs = json.load(open(os.path.join(ROOT, 'tools', 'assets', 'hershey_script.json')))['scripts']
    SS = 3                                   # supersample for the pen
    left, right = 170, W - 150
    top, step = 150, 122
    density = []                             # per line: (ink mask at full res, its box)
    rnd = np.random.default_rng(31)
    for li, text in enumerate(LINES):
        legible = text == LEGIBLE
        # measure, to fit the line in the margins
        adv = sum(glyphs.get(c, glyphs[' '])['w'] for c in text)
        scale = min(3.05, (right - left) / (adv * 1.0))
        if li == len(LINES) - 1:
            scale = 3.05
        canvas = np.zeros((H * 1, W * 1), np.float32)
        big = np.zeros((step * 3 * SS, W * SS), np.float32)
        fade_at = text.index('Ford') + 2 if legible else -1      # its 'r' faded to a ghost (round 2)
        bigf = np.zeros_like(big)
        base = int(step * 1.6 * SS)          # base line in the strip
        x = (left + (0 if li != len(LINES) - 1 else 980) + rnd.uniform(-6, 10)) * SS
        if li == 0:
            x = left * SS
        slope = rnd.uniform(-0.012, 0.006)   # the line drifts a little
        word_dy, word_s = 0.0, 1.0
        for ci, c in enumerate(text):
            g = glyphs.get(c, glyphs[' '])
            if c == ' ':
                word_dy = rnd.normal(0, 1.2)
                word_s = rnd.uniform(0.96, 1.04)
                x += g['w'] * scale * SS * rnd.uniform(0.85, 1.1)
                continue
            s = scale * word_s * SS
            for stroke in g['s']:
                pts = []
                for px, py in stroke:
                    X = x + (px - g['l']) * s
                    Y = base + (py - 9) * s + word_dy * SS + slope * (X / SS - left) * SS
                    pts.append((X, Y))
                # the pen: per segment, heavier going down (a quill on rag)
                for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                    d = math.hypot(x1 - x0, y1 - y0) + 1e-6
                    down = max(0.0, (y1 - y0) / d)
                    wpx = (1.7 + 1.7 * down ** 1.5) * SS
                    cv2.line(bigf if ci == fade_at else big, (int(x0 * 16), int(y0 * 16)), (int(x1 * 16), int(y1 * 16)), 1.0,
                             max(1, int(round(wpx))), cv2.LINE_AA, shift=4)
            x += g['w'] * s * rnd.uniform(0.97, 1.02)
        strip = cv2.resize(big + 0.3 * bigf, (W, step * 3), interpolation=cv2.INTER_AREA)
        y0 = int(top + li * step + rnd.uniform(-4, 4) - step * 1.6 + step * 0.55)
        a, b = max(0, y0), min(H, y0 + step * 3)
        canvas[a:b] = strip[a - y0:b - y0]
        # a gentle wave in each line (the hand moving fast)
        wave = (np.sin(xx / rnd.uniform(260, 420) + rnd.uniform(0, 6)) * 2.0).astype(np.float32)
        canvas = cv2.remap(canvas, xx, yy + wave, cv2.INTER_LINEAR)
        density.append((canvas, legible, top + li * step))

    # ---------------------------------------------------------------- the water --
    leg_y = [cy for _, l, cy in density if l][0] + step * 0.25
    leg_x0, leg_x1 = left + 40, left + 1300
    # wetness: a low field, high at the lower right where it lay in the water; an island kept dry round the line
    wet = 0.8 * noise(1100, 5, 3) + 0.1 * noise(220, 6, 3) + 0.45 * (xx / W) + 0.3 * (yy / H) - 0.1
    dx = np.clip(np.maximum(leg_x0 - xx, xx - leg_x1), 0, None)
    dy = np.abs(yy - leg_y)
    island = np.exp(-(dx / 240.0) ** 2 - (dy / 62.0) ** 2)
    # the island only spares the ink (and lightens the stain a little): the tide lines cross the sheet on their own
    tides = [0.5, 0.66]                    # successive wettings, each with its rim
    soaked = np.clip((wet - 0.05) / 0.25, 0, 1) * (1 - 0.45 * island)
    rim = np.zeros_like(wet)
    for k, t in enumerate(tides):
        jag = t + 0.006 * (noise(30, 40 + k, 3) - 0.5)
        d = wet - jag
        # sharp outside the rim, a soft fade inside (the water dried from its edge)
        rim += np.where(d < 0, np.exp(-(d / 0.004) ** 2), np.exp(-(d / 0.016) ** 2)) * (0.9 - 0.18 * k)
    rim = np.clip(rim, 0, 1.4)

    # ---------------------------------------------------------------- the ink --
    ink = np.zeros((H, W), np.float32)
    keep_n = noise(30, 71, 4)
    for i, (m, legible, cy) in enumerate(density):
        if legible:
            # the band the fold kept dry: feathered 1-2 px, a faint bleed below
            core = cv2.GaussianBlur(m, (0, 0), 0.75)
            feather = cv2.GaussianBlur(m, (0, 0), 2.0)
            thin = 0.85 + 0.15 * noise(12, 90 + i, 2)
            run = cv2.filter2D(feather, -1, np.exp(-np.arange(24, dtype=np.float32) / 7.0)[:, None] / 7.0, anchor=(0, 0))
            d = np.clip(0.92 * core * thin + 0.3 * feather + 0.1 * run, 0, 1)
        else:
            wx = (noise(90, 200 + i, 3) - 0.5) * 16
            wy = (noise(90, 300 + i, 3) - 0.5) * 10
            mw = cv2.remap(m, xx + wx, yy + wy, cv2.INTER_LINEAR)
            # what the water left of the words: fragments, a word part here and there, the rest lifted off
            frag = np.clip((noise(110, 600 + i, 3) - 0.56) * 4.0, 0, 1) * np.clip((noise(16, 650 + i, 2) - 0.2) * 2.5, 0, 1)
            core = cv2.GaussianBlur(mw, (0, 0), 1.3) * frag * 0.7
            halo = cv2.GaussianBlur(mw, (0, 0), 3.2)
            # the ink running down the page: rivulets (tall thin blobs), each ending in a darker tide-line front
            src = cv2.GaussianBlur(mw, (0, 0), 1.5)
            Lr = 300
            ker = (np.exp(-np.arange(Lr, dtype=np.float32) / 110.0))[:, None]
            ker /= ker.sum() / 6.0
            run = cv2.filter2D(src, -1, ker, anchor=(0, 0), borderType=cv2.BORDER_CONSTANT)
            vr = np.random.default_rng(700 + i).random((H // 90 + 2, W // 13 + 2)).astype(np.float32)
            riv = cv2.resize(vr, ((W // 13 + 2) * 13, (H // 90 + 2) * 90), interpolation=cv2.INTER_CUBIC)[:H, :W]
            riv = np.clip((riv - 0.58) * 2.8, 0, 1)
            run = run * riv * (0.5 + soaked) * (1 - island)
            m_run = (run > 0.06).astype(np.uint8)
            m_run = cv2.morphologyEx(m_run, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
            below = np.zeros_like(m_run); below[:-3] = m_run[3:]
            front = cv2.GaussianBlur(((m_run == 1) & (below == 0)).astype(np.float32), (0, 0), 1.2)
            d = 0.62 * core + 0.12 * halo + 0.22 * np.clip(run, 0, 1) * m_run + 0.42 * front
            d = np.clip(d, 0, 0.75)
        ink = np.maximum(ink, d) + 0.25 * np.minimum(ink, d)
    ink = np.clip(ink, 0, 1)
    # the ink the water carried, left along the tide lines
    ink_run = cv2.GaussianBlur(ink, (0, 0), 40.0)
    ink = np.clip(ink + rim * (0.05 + 0.9 * ink_run), 0, 1)

    # ---------------------------------------------------------------- the creases --
    cx, cy = W / 2.0 + 3, H / 2.0 - 2
    dvx = np.abs(xx - cx - 2.0 * np.sin(yy / 230.0))
    dhy = np.abs(yy - cy - 1.5 * np.sin(xx / 310.0))
    crease = np.maximum(np.exp(-(dvx / 2.2) ** 2), np.exp(-(dhy / 2.0) ** 2))
    worn = np.maximum(np.exp(-(dvx / 9.0) ** 2), np.exp(-(dhy / 8.0) ** 2)) * (0.5 + 0.5 * noise(20, 77, 2))
    ink = ink * (1 - 0.35 * worn)

    # ---------------------------------------------------------------- the paper --
    paper = np.array([234, 226, 204], np.float32) / 255.0
    n = 0.55 * noise(260, 11, 4) + 0.3 * noise(40, 12, 3) + 0.15 * noise(4, 13, 2)
    col = np.ones((H, W, 3), np.float32) * paper * (0.93 + 0.1 * n)[..., None]
    # laid and chain lines (rag on a mould), barely there
    laid = 0.5 + 0.5 * np.sin(yy * (math.tau / 9.5) + 0.8 * noise(200, 14, 2))
    chain = np.exp(-((np.mod(xx + 60, 256) - 128) / 3.0) ** 2)
    col *= (1 - 0.018 * laid - 0.025 * chain)[..., None]
    # fibres: short dark and light hairs
    fib = np.zeros((H, W), np.float32)
    for _ in range(1400):
        x0, y0 = rng.uniform(0, W), rng.uniform(0, H)
        a = rng.uniform(0, math.pi)
        ln = rng.uniform(6, 26)
        cv2.line(fib, (int(x0), int(y0)), (int(x0 + ln * math.cos(a)), int(y0 + ln * math.sin(a))),
                 float(rng.choice([-1, 1]) * rng.uniform(0.4, 1)), 1, cv2.LINE_AA)
    col *= (1 + 0.05 * fib)[..., None]
    # the wetting: the soaked part darker and yellowed, browner rims, foxing
    stain = np.array([0.95, 0.91, 0.82], np.float32)
    col *= (1 - soaked[..., None] * (1 - stain) * (0.7 + 0.3 * noise(120, 15, 3))[..., None])
    rimc = np.array([0.66, 0.55, 0.40], np.float32)
    col *= (1 - np.clip(rim, 0, 1)[..., None] * (1 - rimc) * 0.4)
    for _ in range(60):
        fx, fy, fr = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(2, 9)
        dd = np.sqrt((xx - fx) ** 2 + (yy - fy) ** 2)
        spot = 0.16 * np.clip(1 - dd / fr, 0, 1) ** 1.5
        col *= 1 - spot[..., None] * np.array([0.8, 1.0, 1.25], np.float32)
    # the edges handled and grubby, the creases' fibres broken and dirtied
    edge = np.minimum(np.minimum(xx, W - 1 - xx), np.minimum(yy, H - 1 - yy))
    e = np.clip(1 - edge / 70.0, 0, 1) ** 2 * (0.5 + 0.7 * noise(30, 16, 3))
    col *= (1 - 0.22 * e)[..., None]
    col *= (1 - 0.05 * crease * (0.6 + 0.4 * noise(10, 17, 2)))[..., None]
    col *= (1 - 0.07 * worn)[..., None]
    # iron gall washed out: pale blue-grey, a touch browner where it lay thick
    inkc = np.array([0.36, 0.42, 0.52], np.float32)
    inkd = np.array([0.30, 0.31, 0.36], np.float32)
    thick = np.clip((ink - 0.55) * 2.5, 0, 1)[..., None]
    ic = inkc * (1 - thick) + inkd * thick
    a = np.clip(ink * 0.9, 0, 0.92)[..., None]
    col = col * (1 - a) + col * ic * a / np.maximum(paper, 0.1)
    lum = (col @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
    col = (lum + 0.75 * (col - lum)) * 0.76
    col = np.clip(col, 0, 1)

    # ---------------------------------------------------------------- normal and roughness --
    h = (1.4 * (noise(380, 21, 3) - 0.5) * (0.4 + 0.9 * soaked)       # cockle where it was wet
         + 0.12 * (noise(6, 22, 2) - 0.5) + 0.04 * laid + 0.25 * fib
         - 0.5 * worn - 0.25 * np.clip(rim, 0, 1))
    h = cv2.GaussianBlur(h.astype(np.float32), (0, 0), 0.8)
    gx = cv2.Sobel(h, cv2.CV_32F, 1, 0, ksize=3) / 8.0
    gy = cv2.Sobel(h, cv2.CV_32F, 0, 1, ksize=3) / 8.0
    k = 3.0
    nx, ny, nz = -gx * k, gy * k, np.ones_like(h)   # rows run down, v up: +Y = -d/drow -> ny = +gy
    ln_ = np.sqrt(nx * nx + ny * ny + nz * nz)
    nrm = np.stack([nx / ln_, ny / ln_, nz / ln_], -1) * 0.5 + 0.5
    rough = 0.9 - 0.06 * soaked - 0.08 * np.clip(rim, 0, 1) - 0.14 * ink + 0.04 * (n - 0.5)
    mr = np.stack([np.ones_like(rough), np.clip(rough, 0, 1), np.zeros_like(rough)], -1)

    os.makedirs(TEXDIR, exist_ok=True)
    pr = np.random.default_rng(55)
    pn = cv2.resize(pr.random((9, 9)).astype(np.float32), (128, 128), interpolation=cv2.INTER_CUBIC)
    pf = cv2.resize(pr.random((40, 40)).astype(np.float32), (128, 128), interpolation=cv2.INTER_LINEAR)
    pc = np.array([0.40, 0.37, 0.33], np.float32) * (0.75 + 0.3 * pn + 0.12 * pf)[..., None]
    pc = np.where((pf > 0.86)[..., None], pc * 0.6, pc)
    Image.fromarray((np.clip(pc, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(TEXDIR, 'letter_pebble.png'))
    Image.fromarray((col * 255 + 0.5).astype(np.uint8)).save(os.path.join(TEXDIR, 'letter_albedo.png'))
    Image.fromarray((nrm * 255 + 0.5).astype(np.uint8)).save(os.path.join(TEXDIR, 'letter_normal.png'))
    Image.fromarray((mr * 255 + 0.5).astype(np.uint8)).save(os.path.join(TEXDIR, 'letter_mr.png'))
    print('LETTER maps ->', TEXDIR)


# ================================================================ mesh (Blender) ==

def blender_build():
    import bpy
    import bmesh
    from mathutils import Matrix, Vector

    bpy.ops.wm.read_factory_settings(use_empty=True)
    NX, NY = 100, 70                    # even: the creases fall on grid lines (x = 0, y = 0)
    hx, hy = SW / 2, SH / 2

    def lerp_noise(x, y, seed):
        # a few smooth sines for the cockle (no numpy in Blender's frame needed)
        s = 0.0
        for k, (fx, fy, ph) in enumerate(((23, 17, 0.3), (41, 29, 1.7), (13, 37, 2.9))):
            s += math.sin(x * fx + seed + ph) * math.cos(y * fy - seed * 0.7 + ph) / (k + 1)
        return s

    def z_of(x, y):
        # (round 2: r1's tent and curl draped like cloth.) Flat panels meeting at shallow creases (about 7 degrees
        # each), the paper cockled in small bumps where it dried, one corner lifted a few mm.
        u, v = x / hx, y / hy                          # -1..1
        z = 0.0062 * (1 - abs(u))                      # the vertical crease: a ridge, 2 x 3.5 degrees
        side = -1.0 if u < 0 else 1.0                  # the horizontal: a valley on the left half, a ridge on the right
        z += side * 0.0021 * min(1.0, abs(u) / 0.12) * (1 - abs(v))
        z += 0.0035 * max(0.0, (u - 0.72) / 0.28) ** 2 * max(0.0, (-v - 0.55) / 0.45) ** 1.5 * 4.0
        z += 0.0007 * lerp_noise(x * 5, y * 5, 1.3)          # (low and irregular: a fine sine grid read as hatching)
        return max(z, 0.0)

    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    grid = []
    for j in range(NY + 1):
        row = []
        for i in range(NX + 1):
            x = -hx + SW * i / NX
            y = -hy + SH * j / NY
            row.append(bm.verts.new((x, y, z_of(x, y))))
        grid.append(row)
    for j in range(NY):
        for i in range(NX):
            f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            for l in f.loops:
                co = l.vert.co
                l[uvl].uv = ((co.x + hx) / SW, (co.y + hy) / SH)
    bm.edges.ensure_lookup_table()
    for e in bm.edges:
        a, b = e.verts
        on_v = abs(a.co.x) < 1e-7 and abs(b.co.x) < 1e-7
        on_h = abs(a.co.y) < 1e-7 and abs(b.co.y) < 1e-7
        if on_v or on_h:
            e.smooth = False                           # sharp: the creases
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY')
    me = bpy.data.meshes.new('letter_open')
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new('letter_open', me)
    bpy.context.scene.collection.objects.link(ob)
    # Blender (z out of the page, text up +y) -> after the exporter's y-up turn the page faces glTF +Z, text up +Y:
    # turn +90 degrees about x here (z -> -y, y -> z).
    ob.data.transform(Matrix.Rotation(math.radians(90), 4, 'X'))

    def img(name, fn, color):
        im = bpy.data.images.load(os.path.join(TEXDIR, fn))
        im.name = name
        im.colorspace_settings.name = 'sRGB' if color else 'Non-Color'
        return im

    m = bpy.data.materials.new('letter_paper')
    m.use_nodes = True
    m.use_backface_culling = False
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    ta = nt.nodes.new('ShaderNodeTexImage'); ta.image = img('letter_albedo', 'letter_albedo.png', True)
    tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = img('letter_normal', 'letter_normal.png', False)
    tr = nt.nodes.new('ShaderNodeTexImage'); tr.image = img('letter_mr', 'letter_mr.png', False)
    nm = nt.nodes.new('ShaderNodeNormalMap')
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(ta.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(tn.outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    nt.links.new(tr.outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
    nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    me.materials.append(m)

    # a pebble on the upper-left corner (round 2): a flattened, lumpy river stone, grey-brown
    pb = bmesh.new()
    bmesh.ops.create_icosphere(pb, subdivisions=3, radius=0.0115)
    for v in pb.verts:
        d = v.co.normalized()
        v.co = Vector((v.co.x * 1.15, v.co.y * 0.85, v.co.z * 0.55)) * (1 + 0.07 * lerp_noise(d.x * 3, d.y * 3 + d.z, 2.2))
    pu = pb.loops.layers.uv.new('UVMap')
    for f in pb.faces:
        for l in f.loops:
            d = l.vert.co.normalized()
            l[pu].uv = (0.5 + 0.5 * d.x, 0.5 + 0.5 * d.y)
    pz = z_of(-0.083, 0.055)
    pb.transform(Matrix.Translation((-0.083, 0.055, pz + 0.0045)) @ Matrix.Rotation(0.5, 4, 'Z'))
    pm = bpy.data.meshes.new('pebble')
    pb.to_mesh(pm)
    pb.free()
    for p in pm.polygons:
        p.use_smooth = True
    pm.transform(Matrix.Rotation(math.radians(90), 4, 'X'))
    po = bpy.data.objects.new('letter_pebble', pm)
    bpy.context.scene.collection.objects.link(po)
    st = bpy.data.materials.new('letter_pebble')
    st.use_nodes = True
    sb_ = st.node_tree.nodes['Principled BSDF']
    ts = st.node_tree.nodes.new('ShaderNodeTexImage'); ts.image = img('letter_pebble', 'letter_pebble.png', True)
    st.node_tree.links.new(ts.outputs['Color'], sb_.inputs['Base Color'])
    sb_.inputs['Roughness'].default_value = 0.78
    pm.materials.append(st)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    po.select_set(PEBBLE)
    bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True, export_yup=True,
                              export_image_format='AUTO', export_materials='EXPORT', export_tangents=True)
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    print(f'LETTER {OUT}: {tris} tris')


if __name__ == '__main__':
    try:
        import bpy  # noqa: F401
        blender_build()
    except ImportError:
        textures()
        if '--tex' not in sys.argv:
            subprocess.run([BLENDER, '-b', '--factory-startup', '-P', os.path.abspath(__file__)], check=True)
