#!/usr/bin/env python3
"""The town's wall kit (E9b1): our own wall pieces standing in for KayKit's village walls.

    python tools/assets/env_house_atlas.py      # the trim sheet, first
    python tools/assets/env_house.py [name ...] # the presets (all, or those named): numpy only, no Blender

Each preset is built in its KayKit piece's own frame and box (x along the wall, -1..1 on the 2 m grid;
y up, 0 to the 3 m storey, its top band 2.877-3.123 overlapping the storey above as KayKit's does;
z out of the house, the outer face at z = 0, the inner at -0.2), so it stands exactly where the kit
piece stood and tiles with its neighbours (godot/data/zones/<zone>/props_own.json "walls" names which
preset stands in for which kit piece; Dressing.Walls draws them).

Presets are data (tools/assets/env_house.json): a kind, the wall it is (stone: coursed rubble with a
dressed coping band; plaster: lime plaster over the storey below's plate, with a timber pattern; base:
a ground storey of plaster on a rubble plinth and a timber sill beam), a timber pattern (plain, x: a
St Andrew's cross under a rail, k: a rail and a brace, posts: corner posts only), an opening (window
wide_round, thin_round, wide_flat; door round, flat) and a seed (each variant's texture offsets, its
face's bow and its beams' sag).

Faces are cut where a trim-sheet region repeats (env_house_atlas.py: every region tiles), so no UV
leaves its region; flat faces are bowed a centimetre or two between their edges (never at a shared
edge), beams sag and lean a little. Vertex colour: r occlusion (reveals, under the plate), g the stain
mask under a sill (the shader streaks it), b 1 on timber that takes the house's timber tint (else 0),
a 1. One material, "Wall_Own": the game draws it with kit.gdshader's OWN_WALL (KitLook.Wall).

Out: godot/art/world/house/<preset>.glb and house/props.json (each preset's triangles and box).
"""
import json
import math
import struct
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "godot" / "art" / "world" / "house"
DATA = ROOT / "tools" / "assets" / "env_house.json"

TOP = 3.0          # the storey
BAND = (2.877, 3.123)  # the plate band (KayKit's top trim: overlaps the next storey's foot)
FACE_IN = -0.2     # the inner face
PROUD = 0.092      # the band's reach out of the face (KayKit's)
SKIRT = -0.7       # the foundation, below the piece's foot, set back (a step in the ground, a slope)


class Rng:
    def __init__(self, seed):
        self.r = np.random.default_rng(seed)

    def __call__(self, a=0.0, b=1.0):
        return float(self.r.uniform(a, b))


# ----------------------------------------------------------------- atlas --
ATL = None


def region(name):
    global ATL
    if ATL is None:
        ATL = json.loads((OUT / "house_atlas.json").read_text())
    r = ATL["regions"][name]
    return r["uv"], r["m"]


# ------------------------------------------------------------------ mesh --
class Mesh:
    def __init__(self):
        self.P, self.N, self.T, self.C, self.I = [], [], [], [], []

    def poly(self, pts, nrm, uvs, cols):
        b = len(self.P)
        for p, t, c in zip(pts, uvs, cols):
            self.P.append(p)
            self.N.append(nrm)
            self.T.append(t)
            self.C.append(c)
        for k in range(1, len(pts) - 1):
            self.I += [b, b + k, b + k + 1]

    def tris(self):
        return len(self.I) // 3


def clip(poly, axis, val, keep_ge):
    """Sutherland-Hodgman: the part of a convex polygon (list of (s, t)) on one side of s or t = val."""
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        ina = (a[axis] >= val) if keep_ge else (a[axis] <= val)
        inb = (b[axis] >= val) if keep_ge else (b[axis] <= val)
        if ina:
            out.append(a)
        if ina != inb:
            k = (val - a[axis]) / (b[axis] - a[axis])
            out.append((a[0] + k * (b[0] - a[0]), a[1] + k * (b[1] - a[1])))
    return out


def area(poly):
    return 0.5 * sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))


def cuts(lo, hi, off, period, sign=1):
    """Values in (lo, hi) where off + sign * x hits a multiple of period."""
    out = []
    if period <= 0:
        return out
    a, b = sorted((off + sign * lo, off + sign * hi))
    k = math.floor(a / period) + 1
    while k * period < b - 1e-6:
        out.append((k * period - off) / sign)
        k += 1
    return out


def face(m, O, U, V, polys, reg, off=(0.0, 0.0), rot=False, disp=None, col=None, grid=None):
    """Convex polygons in a face's (s, t) metres (s along U, t along V, the face's normal U x V), mapped onto
    a sheet region in metres and cut where the region repeats (and on a grid, for the bow)."""
    O, U, V = (np.asarray(x, float) for x in (O, U, V))
    Nn = np.cross(U, V)
    Nn /= np.linalg.norm(Nn)
    (u0, v0, u1, v1), (W, H) = region(reg)
    for poly in polys:
        if abs(area(poly)) < 1e-6:
            continue
        ss_ = [p[0] for p in poly]
        ts_ = [p[1] for p in poly]
        s0, s1, t0, t1 = min(ss_), max(ss_), min(ts_), max(ts_)
        if not rot:
            sc = cuts(s0, s1, off[0], W) + ([] if grid is None else cuts(s0, s1, 0.0, grid[0]))
            tc = cuts(t0, t1, off[1], H, -1) + ([] if grid is None else cuts(t0, t1, 0.0, grid[1]))
        else:
            sc = cuts(s0, s1, off[1], H) + ([] if grid is None else cuts(s0, s1, 0.0, grid[0]))
            tc = cuts(t0, t1, off[0], W) + ([] if grid is None else cuts(t0, t1, 0.0, grid[1]))
        sl = [s0 - 1] + sorted(set(round(c, 6) for c in sc)) + [s1 + 1]
        tl = [t0 - 1] + sorted(set(round(c, 6) for c in tc)) + [t1 + 1]
        for i in range(len(sl) - 1):
            pc = clip(clip(poly, 0, sl[i], True), 0, sl[i + 1], False) if len(sl) > 2 else poly
            if len(pc) < 3:
                continue
            for j in range(len(tl) - 1):
                q = clip(clip(pc, 1, tl[j], True), 1, tl[j + 1], False) if len(tl) > 2 else pc
                if len(q) < 3 or abs(area(q)) < 1e-7:
                    continue
                cs = sum(p[0] for p in q) / len(q)
                ct = sum(p[1] for p in q) / len(q)
                if not rot:
                    iu, iv = (cs + off[0]), (off[1] - ct)
                else:
                    iu, iv = (ct + off[0]), (cs + off[1])
                tu, tv = math.floor(iu / W), math.floor(iv / H)
                pts, uvs, cols = [], [], []
                for (s, t) in q:
                    d = disp(s, t) if disp else 0.0
                    pts.append(tuple(O + U * s + V * t + Nn * d))
                    if not rot:
                        mu, mv = s + off[0] - tu * W, off[1] - t - tv * H
                    else:
                        mu, mv = t + off[0] - tu * W, s + off[1] - tv * H
                    mu = min(max(mu, 0.0), W)
                    mv = min(max(mv, 0.0), H)
                    uvs.append((u0 + (u1 - u0) * mu / W, v0 + (v1 - v0) * mv / H))
                    cols.append(col(s, t) if col else (1.0, 0.0, 0.0, 1.0))
                m.poly(pts, tuple(Nn), uvs, cols)


def rect(s0, t0, s1, t1):
    return [(s0, t0), (s1, t0), (s1, t1), (s0, t1)]


def box(m, c, ax, ay, h, reg, off=(0.0, 0.0), skip=(), col=None, grain=0):
    """A box at c, its axes ax, ay (az = ax x ay), half sizes h; grain along ax (0) or ay (1).
    skip: faces left out ('+x', '-x', '+y', '-y', '+z', '-z')."""
    c, ax, ay = (np.asarray(x, float) for x in (c, ax, ay))
    ax /= np.linalg.norm(ax)
    ay /= np.linalg.norm(ay)
    az = np.cross(ax, ay)
    hx, hy, hz = h
    colf = (lambda s, t: col) if col is not None else None
    # each face: (name, origin corner, U, V, extents)
    F = [
        ('+z', c + az * hz - ax * hx - ay * hy, ax, ay, 2 * hx, 2 * hy),
        ('-z', c - az * hz + ax * hx - ay * hy, -ax, ay, 2 * hx, 2 * hy),
        ('+y', c + ay * hy - ax * hx + az * hz, ax, -az, 2 * hx, 2 * hz),
        ('-y', c - ay * hy - ax * hx - az * hz, ax, az, 2 * hx, 2 * hz),
        ('+x', c + ax * hx + az * hz - ay * hy, -az, ay, 2 * hz, 2 * hy),
        ('-x', c - ax * hx - az * hz - ay * hy, az, ay, 2 * hz, 2 * hy),
    ]
    for name, o, U, V, lu, lv in F:
        if name in skip:
            continue
        along_x = name in ('+z', '-z', '+y', '-y')
        rot = (grain == 0 and not along_x) or (grain == 1 and along_x)
        face(m, o, U, V, [rect(0, 0, lu, lv)], reg, off, rot=rot, col=colf)


JOINT = 0.02  # (E9b6) a dressed block's chamfer: its joints read as a V-groove, lit on top and dark under, at the play camera
JCOL = 0.45   # the chamfers' vertex r (the shader's occlusion: a joint reads darker than the stone's face in any light)


def sbox(m, c, ax, ay, h, reg, off=(0.0, 0.0), skip=(), col=None, bev=('+z',), b=JOINT):
    """A dressed block (E9b6): box() with the edges of its 'bev' faces chamfered by b, so a course of ashlar shows
    each stone and its joints instead of a flat band. An edge is chamfered where either of its faces is in bev
    (to a skipped face's plane too, closing the groove against a butting block); corners take a triangle."""
    c, ax, ay = (np.asarray(x, float) for x in (c, ax, ay))
    ax /= np.linalg.norm(ax)
    ay /= np.linalg.norm(ay)
    E = (ax, ay, np.cross(ax, ay))
    hh = h
    N = {('x', 1): '+x', ('x', -1): '-x', ('y', 1): '+y', ('y', -1): '-y', ('z', 1): '+z', ('z', -1): '-z'}
    A = 'xyz'
    b = min(b, 0.45 * min(hh))
    jc = (JCOL * (col[0] if col else 1.0), 0.0, 0.0, 1.0)

    def ch(f, g):
        return f in bev or g in bev

    def vert(a, sa, sig):
        """face (axis a, sign sa)'s vertex at the corner of signs sig, inset along each chamfered edge"""
        P = c + sum(sig[k] * hh[k] * E[k] for k in range(3))
        for k in range(3):
            if k != a and ch(N[(A[a], sa)], N[(A[k], sig[k])]):
                P = P - sig[k] * b * E[k]
        return P

    def poly3(pts, out, cl):
        O = pts[0]
        U = pts[1] - O
        if np.linalg.norm(U) < 1e-6:
            return
        U = U / np.linalg.norm(U)
        V = None
        for p in pts[2:]:
            d = (p - O) - np.dot(p - O, U) * U
            if np.linalg.norm(d) > 1e-6:
                V = d / np.linalg.norm(d)
                break
        if V is None:
            return
        if np.dot(np.cross(U, V), out) < 0:
            V = -V
        st = [(float(np.dot(p - O, U)), float(np.dot(p - O, V))) for p in pts]
        if area(st) < 0:
            st = st[::-1]
        face(m, O, U, V, [st], reg, off, col=lambda s, t: cl)

    colf = (lambda s, t: col) if col is not None else None
    for a in range(3):
        for sa in (1, -1):
            name = N[(A[a], sa)]
            if name in skip:
                continue
            k1, k2 = [k for k in range(3) if k != a]
            # the face's own frame as in box(): its corners, inset
            cs = [vert(a, sa, tuple(sa if k == a else (s1 if k == k1 else s2) for k in range(3))) for s1, s2 in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            out = sa * E[a]
            along_x = A[a] in 'zy'
            rot = not along_x
            # (box()'s mapping: U along its first axis; keep the grain the same way)
            U0, V0 = cs[1] - cs[0], cs[3] - cs[0]
            lu, lv = np.linalg.norm(U0), np.linalg.norm(V0)
            if lu < 1e-6 or lv < 1e-6:
                continue
            U0, V0 = U0 / lu, V0 / lv
            O = cs[0]
            if np.dot(np.cross(U0, V0), out) < 0:
                O, U0, lu = cs[1], -U0, lu
            face(m, O, U0, V0, [rect(0, 0, lu, lv)], reg, off, rot=rot and A[a] == 'x', col=colf)
    # the chamfers along the edges
    for a in range(3):
        for k in range(a + 1, 3):
            j = 3 - a - k
            for sa in (1, -1):
                for sk in (1, -1):
                    f, g = N[(A[a], sa)], N[(A[k], sk)]
                    if not ch(f, g) or (f in skip and g in skip) or not ((f in bev and f not in skip) or (g in bev and g not in skip)):
                        continue
                    sig = [0, 0, 0]
                    sig[a], sig[k] = sa, sk
                    pts = []
                    for (ax_, s_), sj in (((a, sa), -1), ((a, sa), 1), ((k, sk), 1), ((k, sk), -1)):
                        sg = list(sig)
                        sg[j] = sj
                        pts.append(vert(ax_, s_, tuple(sg)))
                    poly3(pts, sa * E[a] + sk * E[k], jc)
    # the corners
    for sx in (1, -1):
        for sy in (1, -1):
            for sz in (1, -1):
                sig = (sx, sy, sz)
                fs = [N[(A[k], sig[k])] for k in range(3)]
                if sum(f not in skip for f in fs) < 2 or not any(f in bev and f not in skip for f in fs):
                    continue
                pts = [vert(k, sig[k], sig) for k in range(3)]
                poly3(pts, sum(sig[k] * E[k] for k in range(3)), jc)


def beam(m, a, b, w, z0, d, rng, sag=0.012, reg='timber', col=(1.0, 0.0, 1.0, 1.0), skip=('-z', '-x', '+x'), segs=2):
    """A timber in the wall's face plane from a to b (x, y), w wide, from z0 out to z0 + d; it sags and
    leans a little (two lengths, its middle off the line). (E9b6 r4) Its end faces left out by default (they butt
    other timbers, 3-5 cm deep: the house under 25k triangles); a beam whose end shows passes skip=('-z',)."""
    a, b = np.array([a[0], a[1], 0.0]), np.array([b[0], b[1], 0.0])
    L = np.linalg.norm(b - a)
    ax = (b - a) / L
    ay = np.array([-ax[1], ax[0], 0.0])
    if ay[1] < 0:
        ay = -ay
    pts = [a + (b - a) * k / segs for k in range(segs + 1)]
    for k in range(1, segs):
        pts[k] = pts[k] - ay * sag * rng(0.5, 1.0) * math.sin(math.pi * k / segs)
    off = (rng(0, 3.0), rng(0, 0.25))
    for k in range(segs):
        p, q = pts[k], pts[k + 1]
        lk = np.linalg.norm(q - p)
        axk = (q - p) / lk
        ayk = np.array([-axk[1], axk[0], 0.0])
        if ayk[1] < 0:
            ayk = -ayk
        ext = 0.01 if 0 < k or segs == 1 else 0.0  # (lengths overlap a centimetre at the joint)
        cen = (p + q) / 2 + np.array([0, 0, z0 + d / 2])
        box(m, cen, axk, ayk, (lk / 2 + ext, w / 2, d / 2), reg, off=(off[0] + k * lk, off[1]), skip=skip, col=col)


# ---------------------------------------------------------- the opening --
OPENINGS = {
    # w, sill (0 a door), head (the spring for an arch), rise of the arch
    'wide_round': (1.0, 1.0, 2.1, 0.26),
    'thin_round': (0.62, 1.1, 2.15, 0.2),
    'wide_flat': (1.1, 0.95, 2.2, 0.0),
    'door_round': (1.1, 0.0, 1.92, 0.26),
    'door_flat': (1.1, 0.0, 2.15, 0.0),
}
ARCH_N = 8


def arch_y(x, w, head, rise):
    """The arch's soffit at x (a segment of a circle through the springs and the crown)."""
    if rise <= 0:
        return head
    hw = w / 2
    R = (hw * hw + rise * rise) / (2 * rise)
    return head + rise - R + math.sqrt(max(R * R - x * x, 0.0))


def outline_cols(op):
    """The face round an opening as convex pieces: (pieces, the opening's x edges)."""
    w, sill, head, rise = OPENINGS[op]
    hw = w / 2
    P = [rect(-1, 0, -hw, TOP), rect(hw, 0, 1, TOP)]
    if sill > 0:
        P.append(rect(-hw, 0, hw, sill))
    if rise <= 0:
        P.append(rect(-hw, head, hw, TOP))
    else:
        xs = [-hw + w * k / ARCH_N for k in range(ARCH_N + 1)]
        for a, b in zip(xs, xs[1:]):
            P.append([(a, arch_y(a, w, head, rise)), (b, arch_y(b, w, head, rise)), (b, TOP), (a, TOP)])
    return P


def opening_outline(op, n=ARCH_N):
    """The opening's edge, round from the sill's left: [(x, y)]."""
    w, sill, head, rise = OPENINGS[op]
    hw = w / 2
    pts = [(-hw, sill), (hw, sill)]
    if rise <= 0:
        pts += [(hw, head), (-hw, head)]
    else:
        pts += [(hw - w * k / n, arch_y(hw - w * k / n, w, head, rise)) for k in range(n + 1)]
    return pts


# ----------------------------------------------------------------- walls --
def bow(rng, amp, op=None):
    """A face's bow: out at most amp between its edges, never at x = +-1, y = 0 or the band, nor near an opening."""
    ph = [rng(0, 6.28) for _ in range(4)]
    w = OPENINGS[op][0] / 2 + 0.12 if op else 0.0
    sill = OPENINGS[op][1] if op else 0.0

    def d(s, t):
        e = math.sin(math.pi * (s + 1) / 2) * math.sin(math.pi * min(max(t / BAND[0], 0), 1))
        n = 0.6 + 0.25 * math.sin(2.1 * s + ph[0]) * math.sin(1.7 * t + ph[1]) + 0.15 * math.sin(4.3 * s + 3.1 * t + ph[2])
        k = 1.0
        if op:
            dx = max(abs(s) - w, 0.0)
            k = min(1.0, dx / 0.25) if t > sill - 0.12 else min(1.0, max(dx, sill - 0.12 - t) / 0.25)
        return amp * e * n * k
    return d


def occl_under_band(s, t):
    return (1.0 - 0.28 * max(0.0, 1 - (BAND[0] - t) / 0.35) if t <= BAND[0] + 1e-6 else 1.0, 0.0, 0.0, 1.0)


def stain_col(op, runs=None):
    """The vertex colour of a face round an opening: occlusion under the band, a stain under the sill; (E9b6) on
    plaster, 'runs' (phases): the rain off the plate band, stains 0.6-1.0 m down the face (the shader streaks them)."""
    w, sill, head, rise = OPENINGS[op] if op else (0, 0, 0, 0)

    def c(s, t):
        r = occl_under_band(s, t)[0]
        g = 0.0
        if op and sill > 0 and t <= sill + 1e-6 and abs(s) <= w / 2 + 0.05 + 1e-6:
            g = max(0.0, 1 - (sill - t) / 0.9)
        if runs:
            reach = 0.8 + 0.14 * math.sin(4.1 * s + runs[0]) + 0.08 * math.sin(9.3 * s + runs[1])
            g = max(g, 0.8 * min(1.0, max(0.0, 1 - (BAND[0] - t) / reach)))
        return (r, g, 0.0, 1.0)
    return c


def front_face(m, mat, rng, op, off, amp):
    """The outer face (z = 0): the material's region, round the opening, bowed."""
    reg = 'rubble' if mat == 'stone' else 'plaster'
    pieces = outline_cols(op) if op else [rect(-1, 0, 1, TOP)]
    # the face stops under the band (the band covers 2.877 up)
    pieces = [clip(p, 1, BAND[0] + 0.02, False) for p in pieces]
    pieces = [p for p in pieces if len(p) >= 3]
    xs = []
    if op:
        hw = OPENINGS[op][0] / 2
        xs = [-hw - 0.05, hw + 0.05]
    split = []
    for p in pieces:
        q = [p]
        for x in xs:  # (the stain's edge columns)
            q = [r for qq in q for r in (clip(qq, 0, x, False), clip(qq, 0, x, True)) if len(r) >= 3 and abs(area(r)) > 1e-7]
        split += q
    sill = OPENINGS[op][1] if op else 0.0
    if op and sill > 0:  # (the stain's fade line)
        y = max(sill - 0.9, 0.05)
        split = [r for qq in split for r in (clip(qq, 1, y, False), clip(qq, 1, y, True)) if len(r) >= 3 and abs(area(r)) > 1e-7]
    runs = (off[0] * 1.7, off[1] * 2.3) if mat == 'plaster' else None  # (phases from the sheet offset: the rng's draws unchanged)
    if runs:  # (the runs' foot: a cut at their longest reach, so the stain fades down to there, not to the next grid line)
        split = [r for qq in split for r in (clip(qq, 1, BAND[0] - 1.0, False), clip(qq, 1, BAND[0] - 1.0, True)) if len(r) >= 3 and abs(area(r)) > 1e-7]
    face(m, (0, 0, 0), (1, 0, 0), (0, 1, 0), split, reg, off, disp=bow(rng, amp, op), col=stain_col(op, runs), grid=(0.5, 0.75))
    # the inner face (seen only through the see-through window): plain plaster, dim
    inner = [rect(-1, 0, 1, BAND[0])] if not op else [clip(p, 1, BAND[0], False) for p in outline_cols(op)]
    inner = [[(-s, t) for (s, t) in reversed(p)] for p in inner if len(p) >= 3]
    face(m, (0, 0, FACE_IN), (-1, 0, 0), (0, 1, 0), inner, 'plaster', (off[0] + 1.3, off[1]), col=lambda s, t: (0.55, 0.0, 0.0, 1.0))
    # the foundation skirt (a step in the ground, a slope), set back a little
    face(m, (0, SKIRT, -0.02), (1, 0, 0), (0, 1, 0), [rect(-1, 0, 1, -SKIRT)], 'rubble', (off[0] + 0.7, 0.4), col=lambda s, t: (0.8, 0.0, 0.0, 1.0))


def band(m, mat, rng):
    """The top band, 2.877-3.123, out to z = 0.092 and in to -0.31 (KayKit's): an oak plate on plaster, a dressed
    coping on stone (it also caps a town wall), its top face for a wall that ends there."""
    y0, y1 = BAND
    if mat == 'stone':
        # dressed blocks with joints, each a few mm off the line
        x = -1.0
        while x < 1.0 - 1e-6:
            L = min(rng(0.45, 0.8), 1.0 - x)
            if 1.0 - x - L < 0.25:
                L = 1.0 - x
            dy = rng(-0.006, 0.006)
            sbox(m, (x + L / 2, (y0 + y1) / 2 + dy, (PROUD - 0.31) / 2), (1, 0, 0), (0, 1, 0), (L / 2 - 0.004, (y1 - y0) / 2, (PROUD + 0.31) / 2),
                 'ashlar', off=(rng(0, 2.4), rng(0, 0.1)), skip=('-z', '-x', '+x') if L > 0.3 else ('-z',), col=(1.0, 0.0, 0.0, 1.0))
            x += L
    else:
        beam(m, (-1.0, (y0 + y1) / 2), (1.0, (y0 + y1) / 2), y1 - y0, -0.31, PROUD + 0.31, rng, sag=0.008, skip=('-z', '-x', '+x'), segs=2)


PW = 0.17   # a post's width (half on each panel)
TD = 0.035  # a timber's reach out of the plaster


def pattern(m, pat, rng, op=None, base=False):
    """The panel's timbers (out of the plaster face, z 0 to TD)."""
    if pat == 'plain':
        return
    y0 = 0.75 if base else 0.0
    lo, hi = y0 + 0.02, BAND[0]
    # posts at the panel's ends (each half a post: the neighbour gives the other half)
    for sx in (-1, 1):
        a = (sx * (1 - PW / 4), lo)
        b = (sx * (1 - PW / 4) + rng(-0.006, 0.006), hi)
        beam(m, a, b, PW / 2, 0.0, TD, rng, sag=0.006, skip=('-z', '-x', '+x'), segs=2)
    if pat == 'posts':
        return
    if op:
        w, sill, head, rise = OPENINGS[op]
        hw = w / 2
        top = head + rise
        # a lintel over the opening, a sill rail under a window, studs beside it
        beam(m, (-1 + PW / 2, top + 0.09), (1 - PW / 2, top + 0.09), 0.16, 0.0, TD, rng, sag=0.012, skip=('-z',))
        if sill > 0:
            beam(m, (-1 + PW / 2, sill - 0.08), (1 - PW / 2, sill - 0.08), 0.15, 0.0, TD, rng, sag=0.01, skip=('-z',))
        for sx in (-1, 1):
            beam(m, (sx * (hw + 0.07), (sill - 0.16) if sill > 0 else lo), (sx * (hw + 0.07), top + 0.01), 0.13, 0.0, TD, rng, sag=0.004, skip=('-z', '-x', '+x'), segs=1)
        if pat == 'x' and sill > 0.6:
            for sx in (-1, 1):  # short braces under the sill
                beam(m, (sx * (1 - PW / 2), lo + 0.05), (sx * (hw + 0.12), sill - 0.16), 0.12, 0.0, TD * 0.9, rng, sag=0.0, skip=('-z',), segs=1)
        return
    rail = rng(1.05, 1.25) + (0.4 if base else 0.0)
    beam(m, (-1 + PW / 2, rail), (1 - PW / 2, rail), 0.15, 0.0, TD, rng, sag=0.014, skip=('-z',))
    if pat == 'x':
        for sgn in (-1, 1):
            beam(m, (-1 + PW / 2, lo + 0.04 if sgn > 0 else rail - 0.06), (1 - PW / 2, rail - 0.06 if sgn > 0 else lo + 0.04), 0.13, 0.0, TD * 0.9, rng, sag=0.006, skip=('-z',), segs=1)
        # a stud up the middle above the rail
        beam(m, (rng(-0.04, 0.04), rail + 0.06), (rng(-0.04, 0.04), hi), 0.13, 0.0, TD, rng, sag=0.005, skip=('-z',), segs=1)
    elif pat == 'frame':
        # (E9b6) a plain house's plain run, framed: a stud up the middle, below and above the rail (panels of 0.9 m by
        # 1.1-1.7 m), so no bare stretch of lime plaster runs 3 m and more at the play camera
        sx = rng(-0.06, 0.06)
        beam(m, (sx, lo + 0.03), (sx + rng(-0.01, 0.01), rail - 0.07), 0.13, 0.0, TD, rng, sag=0.004, skip=('-z',), segs=1)
        beam(m, (sx + rng(-0.01, 0.01), rail + 0.07), (sx + rng(-0.02, 0.02), hi), 0.13, 0.0, TD, rng, sag=0.004, skip=('-z',), segs=1)
    elif pat in ('k', 'k2'):
        sgn = 1 if pat == 'k' else -1
        beam(m, (sgn * (-1 + PW / 2), rail + 0.06), (sgn * (1 - PW / 2) * 0.15, hi - 0.03), 0.14, 0.0, TD * 0.9, rng, sag=0.008, skip=('-z',), segs=1)
        beam(m, (sgn * (1 - PW / 2) * 0.05, lo + 0.03), (sgn * (1 - PW / 2), rail - 0.06), 0.13, 0.0, TD * 0.9, rng, sag=0.006, skip=('-z',), segs=1)


def plinth(m, rng, off):
    """A plaster ground storey's foot: a rubble plinth to 0.55 m, a little proud, and an oak sill beam on it."""
    box(m, (0, 0.275, 0.015), (1, 0, 0), (0, 1, 0), (1.0, 0.275, 0.025), 'rubble', off=(off[0] + 0.5, 0.2), skip=('-z', '-x', '+x', '-y'),
        col=(1.0, 0.0, 0.0, 1.0))
    beam(m, (-1.0, 0.65), (1.0, 0.65), 0.2, 0.0, 0.05, rng, sag=0.006, skip=('-z', '-x', '+x'))


def reveal(m, mat, op, depth=0.13):
    """The opening's inner sides, from the face back to its frame; dim (occluded)."""
    reg = 'rubble' if mat == 'stone' else 'plaster'
    pts = opening_outline(op)
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        if math.dist(a, b) < 1e-6:
            continue
        e = np.array([b[0] - a[0], b[1] - a[1], 0.0])
        L = np.linalg.norm(e)
        U = e / L
        # the face looks into the opening: U along the edge (the outline runs anticlockwise), V into the wall (-z)
        face(m, (a[0], a[1], 0.0), tuple(U), (0, 0, -1), [rect(0, 0, L, depth)], reg, (0.3 * i, 0.2), rot=False,
             col=lambda s, t: (0.62 - 1.2 * t, 0.0, 0.0, 1.0))


def frame_and_glass(m, op, rng, depth=0.13):
    """An oak frame in the opening's back, and its glass (a window) or its door of boards with iron straps."""
    w, sill, head, rise = OPENINGS[op]
    hw = w / 2
    z = -depth
    fw = 0.07
    door = sill == 0
    col_t = (0.8, 0.0, 1.0, 1.0)
    # the frame: jambs, sill (a window's), head (a lintel or the arch in lengths)
    beam(m, (-hw + fw / 2, sill), (-hw + fw / 2, head), fw, z - 0.06, 0.08, rng, sag=0.0, col=col_t, segs=1)
    beam(m, (hw - fw / 2, sill), (hw - fw / 2, head), fw, z - 0.06, 0.08, rng, sag=0.0, col=col_t, segs=1)
    if not door:
        beam(m, (-hw, sill + fw / 2), (hw, sill + fw / 2), fw, z - 0.06, 0.08, rng, sag=0.0, col=col_t, segs=1)
    if rise <= 0:
        beam(m, (-hw, head - fw / 2), (hw, head - fw / 2), fw, z - 0.06, 0.08, rng, sag=0.0, col=col_t, segs=1)
    else:
        n = 4
        xs = [-hw + w * k / n for k in range(n + 1)]
        for a, b in zip(xs, xs[1:]):
            beam(m, (a, arch_y(a, w, head, rise) - fw / 2), (b, arch_y(b, w, head, rise) - fw / 2), fw, z - 0.06, 0.08, rng, sag=0.0, col=col_t, segs=1)
    # the infill, at the frame's back: glass, or the door's boards (grain up)
    zi = z - 0.05
    pieces = [rect(-hw + 0.01, sill + (0.01 if not door else 0.0), hw - 0.01, head)]
    if rise > 0:
        xs = [-hw + w * k / ARCH_N for k in range(ARCH_N + 1)]
        for a, b in zip(xs, xs[1:]):
            pieces.append([(a, head), (b, head), (b, arch_y(b, w, head, rise)), (a, arch_y(a, w, head, rise))])
    if door:
        face(m, (0, 0, zi), (1, 0, 0), (0, 1, 0), pieces, 'planks', (rng(0, 1), rng(0, 0.3)), rot=True, col=lambda s, t: (0.85, 0.0, 1.0, 1.0))
        # iron straps across, a ring handle's plate
        for y in (0.35, 1.55):
            box(m, (0, y, zi + 0.008), (1, 0, 0), (0, 1, 0), (hw - 0.06, 0.03, 0.006), 'iron', skip=('-z',), col=(0.9, 0.0, 0.0, 1.0))
        box(m, (hw - 0.22, 1.0, zi + 0.01), (1, 0, 0), (0, 1, 0), (0.04, 0.06, 0.008), 'iron', skip=('-z',), col=(0.9, 0.0, 0.0, 1.0))
        # boards' battens are behind; a plank seam shows by the sheet
    else:
        face(m, (0, 0, zi), (1, 0, 0), (0, 1, 0), pieces, 'glass', (rng(0, 0.3), rng(0, 0.2)), col=lambda s, t: (0.7, 0.0, 0.0, 1.0))
        # glazing bars: one upright, a transom (and two for a tall light)
        mb = 0.035
        beam(m, (0, sill), (0, head + rise - 0.02), mb, zi, 0.03, rng, sag=0.0, col=col_t, segs=1)
        for y in ([sill + (head - sill) * 0.5] if head - sill < 1.2 else [sill + (head - sill) / 3, sill + 2 * (head - sill) / 3]):
            beam(m, (-hw, y), (hw, y), mb, zi, 0.03, rng, sag=0.0, col=col_t, segs=1)


def dressings(m, mat, op, rng):
    """What frames the opening on the face: on stone, a dressed sill and a lintel or an arch of voussoirs;
    on plaster a timber sill (a window's) and lintel (the pattern gives them where it is framed)."""
    w, sill, head, rise = OPENINGS[op]
    hw = w / 2
    if mat == 'stone':
        if sill > 0:
            box(m, (0, sill - 0.05, 0.02), (1, 0, 0), (0, 1, 0), (hw + 0.1, 0.05, 0.06), 'ashlar', off=(rng(0, 2.5), 0.1), skip=('-z',), col=(1.0, 0.0, 0.0, 1.0))
        if rise <= 0:
            box(m, (rng(-0.01, 0.01), head + 0.13, 0.012), (1, 0, 0), (0, 1, 0), (hw + 0.16, 0.13, 0.03), 'ashlar', off=(rng(0, 2.5), 0.05), skip=('-z',), col=(1.0, 0.0, 0.0, 1.0))
        else:
            # voussoirs round the arch, a keystone at the crown
            n = 7 if w > 0.8 else 5
            R = (hw * hw + rise * rise) / (2 * rise)
            cy = head + rise - R
            a0 = math.atan2(head - cy, hw)
            for k in range(n):
                a = a0 + (math.pi - 2 * a0) * (k + 0.5) / n
                da = (math.pi - 2 * a0) / n
                depth = 0.26 if k == n // 2 else 0.22
                r = R + depth / 2
                c = (math.cos(a) * r, cy + math.sin(a) * r)
                ax = (-math.sin(a), math.cos(a), 0)
                ay = (math.cos(a), math.sin(a), 0)
                half = R * da / 2 * 1.0 + 0.005
                box(m, (c[0], c[1], 0.014 + (0.01 if k == n // 2 else 0)), ax, ay, (half - 0.004, depth / 2, 0.03), 'ashlar', off=(rng(0, 2.6), rng(0, 0.1)),
                    skip=('-z',), col=(1.0, 0.0, 0.0, 1.0), grain=1)
    else:
        if sill > 0:
            beam(m, (-hw - 0.08, sill - 0.035), (hw + 0.08, sill - 0.035), 0.07, 0.0, 0.06, rng, sag=0.003, segs=1, skip=('-z',))


def wall(p):
    rng = Rng(p['seed'])
    m = Mesh()
    mat, pat, op = p['wall'], p.get('pattern', 'plain'), p.get('opening')
    off = (p.get('off', [rng(0, 4), rng(0, 1.5)])[0], p.get('off', [0, rng(0, 1.5)])[1])
    front_face(m, 'stone' if mat == 'stone' else 'plaster', rng, op, off, 0.014 if mat == 'stone' else 0.011)
    band(m, 'stone' if mat == 'stone' else 'plaster', rng)
    if mat == 'base':
        plinth(m, rng, off)
    if mat != 'stone':
        pattern(m, pat, rng, op, base=(mat == 'base'))
    if op:
        reveal(m, 'stone' if mat == 'stone' else 'plaster', op)
        frame_and_glass(m, op, rng)
        dressings(m, 'stone' if mat == 'stone' else 'plaster', op, rng)
    return m


def quoin(p):
    """A stone storey's outer corner: dressed quoins in alternating courses, long and short, a few mm out of
    true, standing 3 cm proud of both faces (the corner at x = z = 0, the walls running to -x and -z).
    (E9b6) each stone long on one face and short on the other, by turns, so BOTH faces show the long-and-short
    rhythm (before, the side face's 'long' stones were 26-34 cm against 25 cm: a flat strip, read as a timber);
    each stone chamfered (sbox), so the joints read at the play camera."""
    rng = Rng(p['seed'])
    m = Mesh()
    y = SKIRT
    k = 0
    pr = 0.03
    while y < BAND[1] - 1e-6:
        h = rng(0.24, 0.32) if y >= 0 else -SKIRT
        h = min(h, BAND[1] - y)
        if BAND[1] - (y + h) < 0.12:
            h = BAND[1] - y
        last = y + h >= BAND[1] - 1e-6
        L = rng(0.44, 0.56)
        dx, dz = rng(-0.006, 0.006), rng(-0.006, 0.006)
        cy = y + h / 2
        col = (1.0, 0.0, 0.0, 1.0) if y >= 0 else (0.8, 0.0, 0.0, 1.0)
        sk = ('-z', '-y') + (() if last else ('+y',))
        if k % 2 == 0:  # long along the front (x), short along the side (z)
            sbox(m, (-(L - pr) / 2 + dx, cy, (pr - 0.22) / 2 + dz), (1, 0, 0), (0, 1, 0), ((L + pr) / 2, h / 2 - 0.005, (0.22 + pr) / 2), 'ashlar',
                 off=(rng(0, 2.4), rng(0, 0.05)), skip=sk, col=col, bev=('+z', '+x'))
        else:           # long along the side (z), short along the front
            sbox(m, ((pr - 0.22) / 2 + dx, cy, -(L - pr) / 2 + dz), (0, 0, -1), (0, 1, 0), ((L + pr) / 2, h / 2 - 0.005, (0.22 + pr) / 2), 'ashlar',
                 off=(rng(0, 2.4), rng(0, 0.05)), skip=sk, col=col, bev=('+z', '-x'))
        y += h
        k += 1
    return m


def post(p):
    """A plaster storey's corner post: a squared oak post, 0.2 m, a little out of plumb, a brace stub."""
    rng = Rng(p['seed'])
    m = Mesh()
    lean = (rng(-0.01, 0.01), rng(-0.01, 0.01))
    c0, c1 = np.array([0.0, 0.0, 0.0]), np.array([lean[0], BAND[1], lean[1]])
    ay = (c1 - c0) / np.linalg.norm(c1 - c0)
    box(m, (c0 + c1) / 2, (1, 0, 0), ay, (0.1, np.linalg.norm(c1 - c0) / 2, 0.1), 'timber', off=(rng(0, 3), rng(0, 0.2)), skip=('-y',),
        col=(1.0, 0.0, 1.0, 1.0), grain=1)
    return m


def pier(p):
    """A town wall's pier (E9b4): where the kit set a corner piece in the middle of a straight run (a joint every
    8 m), a dressed stone buttress, not a corner's quoins standing in the wall face like a post. In its wall's own
    frame (the face at z = 0, out to +z), centred on the joint: courses of ashlar in two blocks with the joint
    alternating, a weathered set-off at the top sloping back to the next reach (the lower storey: from 'reach' to
    'top'; the upper: from 'top' to the coping's 9 cm), a few mm out of true."""
    rng = Rng(p['seed'])
    m = Mesh()
    W = p.get('width', 0.72) / 2
    reach, top = p['reach'], p['top']
    y0 = SKIRT if p.get('foot', True) else 0.0
    ya, yb = BAND[0] - 0.32, BAND[0]
    col = (1.0, 0.0, 0.0, 1.0)
    y, k = y0, 0
    while y < ya - 1e-6:
        h = rng(0.27, 0.36) if y >= 0 else -y0
        h = min(h, ya - y)
        if ya - (y + h) < 0.12:
            h = ya - y
        cut = rng(0.08, 0.2) * (1 if k % 2 == 0 else -1)
        dz = rng(-0.005, 0.005)
        for x0, x1 in ((-W, cut), (cut, W)):
            sbox(m, ((x0 + x1) / 2 + rng(-0.003, 0.003), y + h / 2, reach / 2 + dz), (1, 0, 0), (0, 1, 0),
                 ((x1 - x0) / 2 - 0.004, h / 2 - 0.005, reach / 2), 'ashlar', off=(rng(0, 2.4), rng(0, 0.1)), skip=('-z', '-y'),
                col=col if y >= 0 else (0.8, 0.0, 0.0, 1.0))
        y += h
        k += 1
    # the set-off: the next reach's body up to the band, and a sloping slab from this reach back to it
    box(m, (0.0, (ya + yb + 0.246) / 2, top / 2), (1, 0, 0), (0, 1, 0), (W - 0.004, (yb + 0.246 - ya) / 2, top / 2), 'ashlar',
        off=(rng(0, 2.4), rng(0, 0.1)), skip=('-z', '-y'), col=col)
    A, B = np.array([0.0, ya, reach]), np.array([0.0, yb, top])
    sv = (B - A) / np.linalg.norm(B - A)
    az = np.cross([1.0, 0.0, 0.0], sv)
    t = 0.13
    box(m, (A + B) / 2 - az * t / 2 + np.array([0.0, 0.0, 0.0]), (1, 0, 0), sv,
        (W + 0.01, np.linalg.norm(B - A) / 2 + 0.02, t / 2), 'ashlar', off=(rng(0, 2.4), rng(0, 0.1)), skip=('-z', '-y'), col=col)
    return m


def shutters(p):
    """A window's two shutters, open against the wall beside it: boards (grain up), two ledges, iron hinges."""
    rng = Rng(p['seed'])
    m = Mesh()
    w, sill, head, rise = OPENINGS[p['opening']]
    hw = w / 2
    lw = hw - 0.01
    for sx in (-1, 1):
        x0 = sx * (hw + 0.04)
        x1 = sx * (hw + 0.04 + lw)
        cx = (x0 + x1) / 2
        tilt = rng(-0.004, 0.004)
        box(m, (cx, (sill + head) / 2, 0.035), (1, tilt, 0), (0, 1, 0), (lw / 2, (head - sill) / 2, 0.018), 'planks', off=(rng(0, 3), rng(0, 0.3)), skip=('-z',),
            col=(0.95, 0.0, 1.0, 1.0), grain=1)
        for y in (sill + 0.2, head - 0.2):
            box(m, (cx, y, 0.058), (1, 0, 0), (0, 1, 0), (lw / 2 - 0.02, 0.02, 0.006), 'iron', skip=('-z',), col=(0.9, 0.0, 0.0, 1.0))
    return m


KINDS = {'wall': wall, 'quoin': quoin, 'post': post, 'shutters': shutters, 'pier': pier}


# ------------------------------------------------------------------- glb --
def write_glb(path, name, m):
    P = np.array(m.P, np.float32)
    N = np.array(m.N, np.float32)
    T = np.array(m.T, np.float32)
    C = np.clip(np.array(m.C, np.float32), 0, 1)
    I = np.array(m.I, np.uint32)
    blobs, views, accs = [], [], []
    off = 0

    def add(arr, target, typ, ctype, minmax=False):
        nonlocal off
        b = arr.tobytes()
        pad = (-len(b)) % 4
        views.append({"buffer": 0, "byteOffset": off, "byteLength": len(b), "target": target})
        a = {"bufferView": len(views) - 1, "componentType": ctype, "count": int(arr.shape[0]), "type": typ}
        if minmax:
            a["min"] = arr.min(0).tolist()
            a["max"] = arr.max(0).tolist()
        accs.append(a)
        blobs.append(b + b"\0" * pad)
        off += len(b) + pad
        return len(accs) - 1
    ip = add(P, 34962, "VEC3", 5126, True)
    inn = add(N, 34962, "VEC3", 5126)
    it = add(T, 34962, "VEC2", 5126)
    ic = add(C, 34962, "VEC4", 5126)
    ii = add(I, 34963, "SCALAR", 5125)
    g = {
        "asset": {"version": "2.0", "generator": "env_house.py"},
        "scene": 0, "scenes": [{"nodes": [0]}],
        "nodes": [{"name": name, "mesh": 0}],
        "meshes": [{"name": name, "primitives": [{"attributes": {"POSITION": ip, "NORMAL": inn, "TEXCOORD_0": it, "COLOR_0": ic}, "indices": ii, "material": 0}]}],
        "materials": [{"name": "Wall_Own", "pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1], "metallicFactor": 0, "roughnessFactor": 0.9}}],
        "buffers": [{"byteLength": off}], "bufferViews": views, "accessors": accs,
    }
    js = json.dumps(g, separators=(",", ":")).encode()
    js += b" " * ((-len(js)) % 4)
    bin_ = b"".join(blobs)
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(bin_)))
        f.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
        f.write(struct.pack("<II", len(bin_), 0x004E4942) + bin_)
    return P


def main():
    data = json.loads(DATA.read_text())["presets"]
    names = sys.argv[1:] or list(data)
    meta_path = OUT / "props.json"
    info = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    for name in names:
        p = data[name]
        m = KINDS[p['kind']](p)
        P = write_glb(OUT / f"{name}.glb", name, m)
        info[name] = {"tris": m.tris(), "box": [round(float(v), 3) for v in list(P.min(0)) + list(P.max(0))]}
        print(f"HOUSE {name}: {info[name]}")
    meta_path.write_text(json.dumps(info, indent=1))


if __name__ == "__main__":
    main()
