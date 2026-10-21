#!/usr/bin/env python3
"""The town's roof kit (E9b2): our own roofs, gable fronts, spires and chimneys standing in for KayKit's.

    python tools/assets/env_roof_atlas.py      # the roof sheet, first (and env_house_atlas.py: the walls' sheet)
    python tools/assets/env_roof.py [name ...] # the presets (all, or those named): numpy only, no Blender

Each preset is built in its KayKit piece's own frame (houses.ts buildHouse): a roof body (Roof_RoundTiles_WxD)
at the top of the walls, its ridge along z, the walls at x = +-W/2 and z = +-D/2; a gable front
(Roof_Front_BrickW) at a gable wall, its outer face at z = 0, +z out of the house; the tower's spire
(Roof_Tower_RoundTiles) over a 4 m tower; a chimney (Prop_Chimney) from its foot at y = 0 (0.4 m above the
walls' top). So each stands where the kit piece stood (props_own.json "walls" "pieces" maps them).

Roof body: the roof line (profile()) runs at the main pitch down to the walls' face, then kicks out at a
shallower pitch over the eaves (a sprocketed eave), 40-60 cm past the walls (the preset's "eave"), the verge
35 cm past the gables; courses of tiles or shingles as real steps (a riser at each butt), so a low sun draws
their lines; half-round clay ridge caps (or a pair of ridge boards on shingles); rafter ends under the eaves,
their soffit boarding, barge boards up both verges, the ridge beam's and purlins' ends out of the gables.
Ridge and eaves sag (sag(): a parabola along the ridge, zero at the gables, the preset's "sag" in metres, and a
few millimetres of wobble); the vertex colour's alpha carries the same weight, so the game sags each house
further by its own amount (kit.gdshader OWN_ROOF, 0-4 cm by the copy's hash).

Gable front: the triangle under the roof, closed in lime plaster on the walls' sheet (material Wall_Own: the
house's plaster tint and timber treatment), a tie beam at its foot and the treatment's timbers (plain: a
king post; crosses: a king post and a St Andrew's cross either side; braces: a king post and raking struts),
an owl hole under the apex.

Vertex colour (Roof_Own): r occlusion, g the face's hash (each course's run of tiles varies again in the
shader by its tile's id and this), b 1 on the roof's covering (tiles, shingles, caps: it takes moss and soot),
a the sag weight. Wall_Own as env_house.py.

Out: godot/art/world/house/<preset>.glb and house/props.json (each preset's triangles, box, and for a roof its
measures: sag, eave overhang, pitch).
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "assets"))
import env_house as H  # noqa: E402

OUT = H.OUT
DATA = ROOT / "tools" / "assets" / "env_roof.json"
ATL_H = json.loads((OUT / "house_atlas.json").read_text())
ATL_R = json.loads((OUT / "roof_atlas.json").read_text())
H.ATL = {"regions": {**ATL_H["regions"], **ATL_R["regions"]}}
COURSE = ATL_R["course"]

PITCH = {4: 1.47, 6: 1.46, 8: 1.33}   # the main pitch (rise per run) by the house's width: KayKit's heights
KICK = 0.55                          # the eave's pitch
KNEE_Y = 0.20                        # the roof's top over the walls' face (just outside the plate band)
BLEND = 0.25                         # the knee's curve, either side
COVER = 0.09                         # the covering's depth over the boarding (top to soffit, vertical)
STEP = 0.016                         # a course's butt over the course below
VERGE = 0.35


def hsh(*a):
    x = math.sin(sum(v * k for v, k in zip(a, (12.9898, 78.233, 37.719, 4.581)))) * 43758.5453
    return x - math.floor(x)


class Roof:
    """A roof's line across its slopes (x), the same for its body and its gable fronts."""

    def __init__(self, w, eave=0.5):
        self.hw = w / 2
        self.t = PITCH[w]
        self.xk = self.hw + 0.1
        self.eave = eave
        self.xe = self.hw + eave

    def top(self, xa):
        """The covering's top at |x| = xa (before the sag)."""
        xa = abs(xa)
        xk, t, yk = self.xk, self.t, KNEE_Y
        a, b = xk - BLEND, xk + BLEND
        if xa <= a:
            return yk + t * (xk - xa)
        if xa >= b:
            return yk - KICK * (xa - xk)
        # a quadratic between the two lines' tangents at a and b
        ya, yb = yk + t * BLEND, yk - KICK * BLEND
        yc = yk
        u = (xa - a) / (b - a)
        return (1 - u) ** 2 * ya + 2 * u * (1 - u) * yc + u * u * yb

    def under(self, xa):
        return self.top(xa) - COVER

    def ridge(self):
        return self.top(0.0)


def profile(R, n_main=10, n_kick=4):
    """Points (x, y) from the ridge down to the eave on the +x side, dense through the knee."""
    xs = list(np.linspace(0.0, R.xk - BLEND, n_main)) + list(np.linspace(R.xk - BLEND, R.xk + BLEND, 4))[1:] + \
        list(np.linspace(R.xk + BLEND, R.xe, n_kick))[1:]
    return [(x, R.top(x)) for x in xs]


def arclen(pts):
    L = [0.0]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        L.append(L[-1] + math.hypot(x1 - x0, y1 - y0))
    return L


def at_len(pts, L, s):
    """The point and the downslope unit tangent at arc length s (from the ridge)."""
    s = min(max(s, 0.0), L[-1])
    for i in range(len(pts) - 1):
        if L[i + 1] >= s - 1e-9:
            k = (s - L[i]) / max(L[i + 1] - L[i], 1e-9)
            p = np.array(pts[i]) + k * (np.array(pts[i + 1]) - np.array(pts[i]))
            d = np.array(pts[i + 1]) - np.array(pts[i])
            return p, d / np.linalg.norm(d)
    return np.array(pts[-1]), np.array([1.0, 0.0])


def uvq(reg, u0, u1, v0, v1):
    """A region's UV for (u, v) fractions in it."""
    (a, b, c, d), _ = H.region(reg)
    return [(a + (c - a) * u0, b + (d - b) * v0), (a + (c - a) * u1, b + (d - b) * v0),
            (a + (c - a) * u1, b + (d - b) * v1), (a + (c - a) * u0, b + (d - b) * v1)]


def quad(m, P, uv, col, out):
    """A quad (or a triangle with a repeated corner) facing out (a rough outward direction)."""
    P = [np.asarray(p, float) for p in P]
    n = np.cross(P[2] - P[0], P[3] - P[1])
    if np.linalg.norm(n) < 1e-12:
        return
    n = n / np.linalg.norm(n)
    if np.dot(n, np.asarray(out, float)) < 0:
        P, uv, n = P[::-1], uv[::-1], -n
    m.poly([tuple(p) for p in P], tuple(n), uv, [col] * 4)


def zbreaks(z0, z1, phase, step=2.0):
    """z0..z1 cut where a 4 m region repeats (phase + multiples of 4) and every step metres between."""
    zs = [z0, z1]
    k = math.ceil((z0 - phase) / step)
    while phase + k * step < z1 - 1e-6:
        zs.append(phase + k * step)
        k += 1
    return sorted(set(round(z, 6) for z in zs))


# ------------------------------------------------------------ the body --
def courses(m, R, side, z0, z1, kind, seed):
    """The covering on one slope (side +1 or -1): courses of the region's course from the eave up."""
    reg = kind
    c = COURSE[kind]
    rows = round(ATL_R["regions"][reg]["m"][1] / c)
    pts = profile(R)
    L = arclen(pts)
    total = L[-1]
    n = math.ceil(total / c)
    phase = z0 - 4.0 * hsh(seed, 3.1)
    zs = zbreaks(z0, z1, phase, 0.75)
    tw = 0.333 if kind == 'pantile' else 0.17   # a tile's or shingle's width (a slipped one)

    def jit(k, z):
        """Each course's butts off their line (E9b3: +-2-3 cm along the slope, never a ruler edge)."""
        f = [hsh(seed, k, i, 9.1) for i in range(4)]
        return 0.026 * (0.55 * math.sin(z * (1.3 + f[0]) + 6.283 * f[1]) + 0.45 * math.sin(z * (2.4 + 1.2 * f[2]) + 6.283 * f[3]))

    for k in range(n):
        se, sr = total - k * c, max(total - (k + 1) * c, 0.0)  # the butt (eave side), the top (ridge side), from the ridge
        pe, de = at_len(pts, L, se)
        ps, ds = at_len(pts, L, sr)
        ne = np.array([de[1], -de[0]]) * -1  # the outward normal (up and out)
        ne = ne if ne[1] > 0 else -ne
        # the top runs on 4 cm under the course above (whose butts wander), so no gap opens
        ext = 0.04 if sr > 0 else 0.0
        pt, _ = at_len(pts, L, max(sr - ext, 0.0))
        row = (k + int(seed * 7)) % rows
        v_top, v_butt = row / rows, (row + 1) / rows
        frac = (se - sr) / c  # the last course at the ridge, partial: its top cut off
        v_top = v_butt - frac / rows
        v_ext = max(v_top - (sr - max(sr - ext, 0.0)) / c / rows, row / rows - 0.004)
        for za, zb in zip(zs, zs[1:]):
            kk = math.floor((za - phase) / 4.0 + 1e-6)
            ua, ub = (za - phase) / 4.0 - kk, (zb - phase) / 4.0 - kk
            g = hsh(seed, k, kk, side)
            ja, jb = (jit(k, za), jit(k, zb)) if k > 0 else (0.0, 0.0)
            ba, bb = pe + ne * STEP + de * ja, pe + ne * STEP + de * jb
            P = [(side * ba[0], ba[1], za), (side * bb[0], bb[1], zb), (side * pt[0], pt[1], zb), (side * pt[0], pt[1], za)]
            quad(m, P, uvq(reg, ua, ub, v_butt, v_ext), (1.0, g, 1.0, 1.0), (side * 0.5, 1, 0))
            # the riser under this course's butt, down to the course below (or the fascia's top at the eave)
            if k > 0:
                la, lb = pe + de * ja, pe + de * jb
                P = [(side * la[0], la[1], za), (side * lb[0], lb[1], zb), (side * bb[0], bb[1], zb), (side * ba[0], ba[1], za)]
                quad(m, P, uvq(reg, ua, ub, v_butt, v_butt - 0.05 / rows), (0.6, g, 1.0, 1.0), (side * de[0], de[1], 0))
        # now and then a slipped tile (or shingle): 5-8 cm down its course, proud of it, a little askew
        if 1 < k < n - 2:
            zz = z0 + 0.3
            while zz < z1 - 0.3 - tw:
                if hsh(seed, k, zz * 3.1, side, 4.4) < 0.008 * tw / 0.17:
                    slip = 0.05 + 0.03 * hsh(seed, k, zz, 1.9)
                    sk = 0.02 * (hsh(seed, k, zz, 2.7) - 0.5)
                    lift = ne * (STEP * 0.75)
                    b0 = pe + de * slip + lift
                    t0 = ps + de * slip + lift + ne * 0.004
                    za, zb = zz, zz + tw
                    kk = math.floor((za - phase) / 4.0 + 1e-6)
                    ua = (za - phase) / 4.0 - kk
                    ub = min(ua + tw / 4.0, 1.0)
                    g = hsh(seed, k, zz, 6.6)
                    P = [(side * b0[0], b0[1], za + sk), (side * b0[0], b0[1], zb + sk), (side * t0[0], t0[1], zb), (side * t0[0], t0[1], za)]
                    quad(m, P, uvq(reg, ua, ub, (row + 1) / rows, row / rows + 0.002), (0.95, g, 1.0, 1.0), (side * 0.5, 1, 0))
                    lo = b0 - lift - ne * 0.002
                    P = [(side * lo[0], lo[1], za + sk), (side * lo[0], lo[1], zb + sk), (side * b0[0], b0[1], zb + sk), (side * b0[0], b0[1], za + sk)]
                    quad(m, P, uvq(reg, ua, ub, (row + 1) / rows, (row + 1) / rows - 0.05 / rows), (0.85, g, 1.0, 1.0), (side * de[0], de[1], 0))
                    zz += tw * 3
                zz += tw
    return pts, L


def eaves(m, R, side, z0, z1, rng, nraft):
    """The fascia board, the soffit boarding under the overhang, the rafters' ends."""
    xe = R.xe
    ytop = R.top(xe) + STEP
    ysof = R.under(xe)
    phase = z0
    zs = zbreaks(z0, z1, phase, 1.0)
    # fascia: a board's face at the eave edge, its top under the first course's butt
    for za, zb in zip(zs, zs[1:]):
        kk = math.floor((za - phase) / 4.0 + 1e-6)
        ua, ub = (za - phase) / 4.0 - kk, (zb - phase) / 4.0 - kk
        P = [(side * xe, ysof - 0.03, za), (side * xe, ysof - 0.03, zb), (side * xe, ytop, zb), (side * xe, ytop, za)]
        quad(m, P, uvq('boards', ua, ub, 1.0, 0.2), (0.6, 0.5, 0.0, 1.0), (side, 0, 0))   # (E9b3: 0.6, it read as a pale band)
        # its underside lip
    # soffit: from the eave edge in to the wall's face, under the boarding (two strips through the knee)
    xs = [R.xe, R.xk + BLEND * 0.3, R.hw + 0.02]
    for xa, xb in zip(xs, xs[1:]):
        for za, zb in zip(zs, zs[1:]):
            kk = math.floor((za - phase) / 4.0 + 1e-6)
            ua, ub = (za - phase) / 4.0 - kk, (zb - phase) / 4.0 - kk
            va, vb = (R.xe - xa) / 0.25, (R.xe - xb) / 0.25
            P = [(side * xa, R.under(xa), za), (side * xa, R.under(xa), zb), (side * xb, R.under(xb), zb), (side * xb, R.under(xb), za)]
            occ = 0.75 if xb > R.hw + 0.1 else 0.55
            quad(m, P, uvq('soffit', ua, ub, min(va, 1.0), min(vb, 1.0)), (occ, 0.5, 0.0, 1.0), (0, -1, 0))
    # rafters: under the soffit, from inside the wall's face to just short of the fascia, ends cut plumb
    hd = (z1 - z0) / 2 - VERGE
    zr = np.linspace(-hd + 0.25, hd - 0.25, nraft)
    x_in, x_out = R.hw - 0.12, R.xe - 0.05
    for i, zc in enumerate(zr):
        zc += rng(-0.03, 0.03)
        a = np.array([x_in, R.under(x_in)])
        b = np.array([x_out, R.under(x_out)])
        ax = (b - a) / np.linalg.norm(b - a)
        nrm = np.array([ax[1], -ax[0]])  # downward normal of the rafter's top
        if nrm[1] > 0:
            nrm = -nrm
        dep, hwz = 0.13 + rng(-0.01, 0.01), 0.045
        tip_drop = rng(-0.006, 0.006)
        A0, B0 = a, b + np.array([0, tip_drop])
        A1, B1 = A0 + nrm * dep, B0 + nrm * dep
        B1 = np.array([B0[0], B1[1]])  # plumb cut: the end's foot straight under its top
        Lr = np.linalg.norm(B0 - A0)
        off = rng(0, 3.5)
        for sz in (-1, 1):  # the sides
            z = zc + sz * hwz
            P = [(side * A0[0], A0[1], z), (side * B0[0], B0[1], z), (side * B1[0], B1[1], z), (side * A1[0], A1[1], z)]
            quad(m, P, uvq('boards', off / 4, (off + Lr) / 4, 0.1, 0.6), (0.7, 0.5, 0.0, 1.0), (0, 0, sz))
        P = [(side * A1[0], A1[1], zc - hwz), (side * B1[0], B1[1], zc - hwz), (side * B1[0], B1[1], zc + hwz), (side * A1[0], A1[1], zc + hwz)]
        quad(m, P, uvq('boards', off / 4, (off + Lr) / 4, 0.6, 0.95), (0.65, 0.5, 0.0, 1.0), (0, -1, 0))
        P = [(side * B0[0], B0[1], zc - hwz), (side * B0[0], B0[1], zc + hwz), (side * B1[0], B1[1], zc + hwz), (side * B1[0], B1[1], zc - hwz)]
        quad(m, P, uvq('endgrain', 0.1, 0.1 + 2 * hwz / 0.25, 0.1, 0.1 + dep / 0.25), (0.9, 0.5, 0.0, 1.0), (side, 0, 0))


def ridge_caps(m, R, z0, z1, rng, seed):
    """Half-round clay caps along the ridge, bedded in lime down to both slopes; each a little off true."""
    yr = R.ridge()
    L = z1 - z0
    n = max(2, round(L / 0.4))
    cl = L / n
    rx, ry = 0.135, 0.11
    yc = yr - 0.035
    # the cap's section: from the left bedding edge (on the slope) over the crown to the right
    xb = 0.2
    yb = R.top(xb) + 0.005
    sec = [(-xb, yb)] + [(rx * math.cos(a), yc + ry * math.sin(a)) for a in np.linspace(math.pi, 0, 6)] + [(xb, yb)]
    sl = arclen(sec)
    for i in range(n):
        za, zb = z0 + i * cl - (0.02 if i else 0), z0 + (i + 1) * cl
        s = 1.0 + (0.03 if i % 2 else 0.0)
        dy, tilt = (1 if i % 2 else -1) * rng(0.01, 0.02), rng(-0.02, 0.02)   # (E9b3) each cap stepped 2-4 cm off its neighbours
        ua, ub = (i % 10) / 10, (i % 10 + 1) / 10
        g = hsh(seed, i, 7.7)
        for j in range(len(sec) - 1):
            (xa_, ya_), (xb_, yb_) = sec[j], sec[j + 1]
            def P(x, y, z, lift):
                return (x * s + tilt * (z - za), y * (1 if j in (0, len(sec) - 2) else 1) + dy + lift, z)
            lift_a = (s - 1) * (ya_ - yc) if 0 < j < len(sec) - 1 else 0.0
            lift_b = (s - 1) * (yb_ - yc) if 0 < j + 1 < len(sec) - 1 else 0.0
            Q = [P(xa_, ya_, za, lift_a), P(xa_, ya_, zb, lift_a), P(xb_, yb_, zb, lift_b), P(xb_, yb_, za, lift_b)]
            quad(m, Q, uvq('ridge', ua, ub, sl[j] / sl[-1], sl[j + 1] / sl[-1]), (1.0, g, 1.0, 1.0), ((xa_ + xb_) / 2, (ya_ + yb_) / 2 - yc + 0.02, 0))
    # the end caps' faces at both verges (a half disc)
    for zf, fl in ((z0, False), (z1, True)):
        pts = [(rx * math.cos(a), yc + ry * math.sin(a)) for a in np.linspace(0, math.pi, 6)]
        for (xa_, ya_), (xb_, yb_) in zip(pts, pts[1:]):
            Q = [(0.0, yc, zf), (xa_, ya_, zf), (xb_, yb_, zf), (0.0, yc, zf)]
            quad(m, Q, uvq('ridge', 0.0, 0.05, 0.4, 0.6), (0.7, 0.5, 1.0, 1.0), (0, 0, 1 if fl else -1))


def ridge_boards(m, R, z0, z1, rng):
    """A shingled roof's ridge: two boards along the ridge, one lapping over the other."""
    yr = R.ridge() + 0.005
    zs = zbreaks(z0, z1, z0, 1.0)
    t = R.t
    c = 1 / math.hypot(1, t)
    for side, wid, lap in ((1, 0.2, 0.03), (-1, 0.17, 0.0)):
        # the board's top face on the slope, from the ridge (+lap past it) down wid
        x0, x1 = -lap * c * side, (wid * c) * side
        y0, y1 = yr + 0.03 + lap * c * t, yr + 0.03 - wid * c * t
        for za, zb in zip(zs, zs[1:]):
            kk = math.floor((za - z0) / 4.0 + 1e-6)
            ua, ub = (za - z0) / 4.0 - kk, (zb - z0) / 4.0 - kk
            P = [(x1, y1, za), (x1, y1, zb), (x0, y0, zb), (x0, y0, za)]
            quad(m, P, uvq('boards', ua, ub, 0.95, 0.15), (1.0, 0.5, 0.0, 1.0), (side * 0.3, 1, 0))
            P = [(x1, y1 - 0.035, za), (x1, y1 - 0.035, zb), (x1, y1, zb), (x1, y1, za)]
            quad(m, P, uvq('boards', ua, ub, 0.95, 0.85), (0.8, 0.5, 0.0, 1.0), (side, 0, 0))
            if lap:
                P = [(x0, y0 - 0.035, za), (x0, y0 - 0.035, zb), (x0, y0, zb), (x0, y0, za)]
                quad(m, P, uvq('boards', ua, ub, 0.95, 0.85), (0.8, 0.5, 0.0, 1.0), (-side, 0, 0))


def verges(m, R, hd, rng):
    """At each gable: the barge boards up both rakes, the soffit under the verge, the ridge beam's and the purlins' ends."""
    pts = profile(R, 6, 3)
    for zs in (1, -1):
        zo = zs * (hd + VERGE)
        zi = zs * (hd + VERGE - 0.04)
        for side in (1, -1):
            off = rng(0, 3.0)
            L = 0.0
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                ln = math.hypot(x1 - x0, y1 - y0)
                ya, yb = y0 + STEP + 0.02, y1 + STEP + 0.02
                d = 0.26
                # the outer face, the inner face, the lower edge
                for z, fl in ((zo, zs < 0), (zi, zs > 0)):
                    P = [(side * x0, ya - d, z), (side * x1, yb - d, z), (side * x1, yb, z), (side * x0, ya, z)]
                    quad(m, P, uvq('boards', (off + L) / 4 % 1, (off + L + ln) / 4 % 1 if (off + L) // 4 == (off + L + ln) // 4 else 1.0, 0.95, 0.05),
                         (0.85 if z == zo else 0.6, 0.5, 0.0, 1.0), (0, 0, zs if z == zo else -zs))
                P = [(side * x0, ya - d, zi), (side * x1, yb - d, zi), (side * x1, yb - d, zo), (side * x0, ya - d, zo)]
                quad(m, P, uvq('boards', 0.1, 0.3, 0.9, 1.0), (0.6, 0.5, 0.0, 1.0), (0, -1, 0))
                # the top of the board (over the tiles' ends)
                P = [(side * x0, ya, zi), (side * x1, yb, zi), (side * x1, yb, zo), (side * x0, ya, zo)]
                quad(m, P, uvq('boards', 0.1, 0.3, 0.0, 0.1), (0.9, 0.5, 0.0, 1.0), (0, 1, 0))
                # the verge's soffit, from the gable to the barge board
                zg = zs * hd
                P = [(side * x0, y0 - COVER, zg), (side * x1, y1 - COVER, zg), (side * x1, y1 - COVER, zi), (side * x0, y0 - COVER, zi)]
                quad(m, P, uvq('soffit', (off + L) / 4 % 1, min(((off + L) % 4 + ln) / 4, 1.0), 0.0, VERGE / 0.25 * 0.5), (0.55, 0.5, 0.0, 1.0), (0, -1, 0))
                L += ln
        # the ridge beam's end and a purlin's either side, out of the gable under the verge
        for xb_, wb, hb in ((0.0, 0.16, 0.2), (R.hw * 0.5, 0.13, 0.16), (-R.hw * 0.5, 0.13, 0.16)):
            yt = R.under(abs(xb_)) - (0.0 if xb_ == 0 else 0.0)
            za, zb = zs * hd, zs * (hd + VERGE - 0.06)
            cx, cy = xb_, yt - hb / 2
            for (sx, fl) in ((-1, True), (1, False)):
                P = [(cx + sx * wb / 2, cy - hb / 2, za), (cx + sx * wb / 2, cy - hb / 2, zb), (cx + sx * wb / 2, cy + hb / 2, zb), (cx + sx * wb / 2, cy + hb / 2, za)]
                quad(m, P, uvq('boards', 0.2, 0.3, 0.2, 0.8), (0.6, 0.5, 0.0, 1.0), (sx, 0, 0))
            P = [(cx - wb / 2, cy - hb / 2, za), (cx + wb / 2, cy - hb / 2, za), (cx + wb / 2, cy - hb / 2, zb), (cx - wb / 2, cy - hb / 2, zb)]
            quad(m, P, uvq('boards', 0.2, 0.3, 0.2, 0.8), (0.5, 0.5, 0.0, 1.0), (0, -1, 0))
            P = [(cx - wb / 2, cy - hb / 2, zb), (cx + wb / 2, cy - hb / 2, zb), (cx + wb / 2, cy + hb / 2, zb), (cx - wb / 2, cy + hb / 2, zb)]
            quad(m, P, uvq('endgrain', 0.1, 0.1 + wb / 0.25, 0.1, 0.1 + hb / 0.25), (0.8, 0.5, 0.0, 1.0), (0, 0, zs))


def sag(m, hd, amount, seed, wob=0.006, xe=None, rake=0.0):
    """Ridge and eaves down by amount at the middle (a parabola, nothing at the gables), a few mm of wobble; each
    slope dished by rake between ridge and eave (the rafters' own sag, E9b3: so a verge is never a ruler line); the
    vertex alpha the along-the-ridge weight (the game's own per-house sag)."""
    ph = [hsh(seed, i, 5.5) * 6.283 for i in range(3)]
    for i, (x, y, z) in enumerate(m.P):
        w = max(0.0, 1.0 - (z / hd) ** 2) if hd > 0 else 0.0
        wb = wob * (0.6 * math.sin(z * 1.3 + ph[0]) + 0.4 * math.sin(z * 3.1 + ph[1])) * min(abs(z) / max(hd, 1e-6), 1.0) * w ** 0.3
        dr = rake * math.sin(math.pi * min(abs(x) / xe, 1.0)) if xe else 0.0
        m.P[i] = (x, y - amount * w - wb - dr, z)
        r, g, b, _ = m.C[i]
        m.C[i] = (r, g, b, w)


def body(p):
    w, d = p['w'], p['d']
    kind = p['cover']  # pantile | shingle
    rng = H.Rng(p['seed'])
    R = Roof(w, p['eave'])
    hd = d / 2
    z0, z1 = -(hd + VERGE), hd + VERGE
    m = H.Mesh()
    for side in (1, -1):
        courses(m, R, side, z0, z1, kind, p['seed'] + side)
        eaves(m, R, side, z0, z1, rng, max(2, round((d - 0.5) / 0.62) + 1))
    if kind == 'pantile':
        ridge_caps(m, R, z0 - 0.02, z1 + 0.02, rng, p['seed'])
    else:
        ridge_boards(m, R, z0, z1, rng)
    verges(m, R, hd, rng)
    sag(m, hd, p['sag'], p['seed'], xe=R.xe, rake=p.get('rake', 0.035))
    meas = {"ridge_sag_cm": round(100 * p['sag'], 1), "eave_cm": round(100 * p['eave'], 1), "pitch_deg": round(math.degrees(math.atan(R.t)), 1),
            "ridge_y": round(R.ridge(), 3)}
    return {"Roof_Own": m}, meas


# ----------------------------------------------------------- the gable --
def gable(p):
    """The triangle under a roof at a gable wall: lime plaster to the roof's underside, a tie beam at its foot, the
    treatment's timbers, an owl hole."""
    w = p['w']
    R = Roof(w)
    hw = w / 2
    rng = H.Rng(p['seed'])
    m = H.Mesh()
    xs = [-hw] + [x for x in np.linspace(-(R.xk - BLEND), R.xk - BLEND, 9)] + [hw]
    xs = sorted(set([round(x, 5) for x in xs if abs(x) <= hw]))
    top = [(x, R.under(x)) for x in xs]
    poly = [(-hw, 0.0), (hw, 0.0)] + [(x, y) for x, y in top[::-1]]
    # (convex: the face's polygon with the roof's line over it)
    ph = [rng(0, 6.28) for _ in range(3)]
    yr = R.under(0)

    def disp(s, t):
        e = max(0.0, 1 - abs(s) / hw) * min(1.0, t / 0.4) * max(0.0, 1 - t / yr)
        return 0.012 * e * (0.7 + 0.3 * math.sin(2.3 * s + ph[0]) * math.sin(1.9 * t + ph[1]))

    def col(s, t):
        ut = R.under(s) - t
        # (E9b3) the water stain under the barge boards: the shader's sill streaks (vertex g), 20-40 cm down, ragged
        reach = 0.3 + 0.1 * math.sin(3.1 * s + ph[2]) + 0.05 * math.sin(7.3 * s + ph[0])
        st = min(1.0, max(0.0, 1 - (ut - 0.04) / reach)) * 0.85
        return (1.0 - 0.45 * max(0.0, 1 - ut / 0.6), st, 0.0, 1.0)
    H.face(m, (0, 0, 0), (1, 0, 0), (0, 1, 0), [poly], 'plaster', off=(rng(0, 4), rng(0, 1)), disp=disp, col=col, grid=(0.5, 0.25))
    # the owl hole under the apex: a dark triangle set in
    oy = yr - 0.75
    tri = [(-0.13, oy), (0.13, oy), (0.0, oy + 0.2)]
    H.face(m, (0, 0, 0.004), (1, 0, 0), (0, 1, 0), [tri], 'glass', col=lambda s, t: (0.15, 0.0, 0.0, 1.0))
    tc = (1.0, 0.0, 1.0, 1.0)
    # the tie beam: the gable's sill, a little proud of the wall's band
    H.beam(m, (-hw - 0.04, 0.1), (hw + 0.04, 0.1), 0.2, 0.0, 0.11, rng, sag=0.008, col=tc, segs=3)
    pat = p['pattern']
    TD = H.TD
    # a king post up the middle, under the owl hole
    H.beam(m, (rng(-0.02, 0.02), 0.2), (rng(-0.02, 0.02), oy - 0.06), 0.16, 0.0, TD, rng, sag=0.004, col=tc, segs=1)
    if pat == 'x':
        for sx in (-1, 1):
            x0, x1 = sx * 0.12, sx * (hw * 0.62)
            yt = R.under(x1) - 0.05
            H.beam(m, (x0, 0.24), (x1, yt * 0.9), 0.12, 0.0, TD * 0.9, rng, sag=0.0, col=tc, segs=1)
            H.beam(m, (x1, 0.24), (x0, min(yt * 0.9, R.under(x0) - 0.3)), 0.12, 0.0, TD * 0.9, rng, sag=0.0, col=tc, segs=1)
            H.beam(m, (x1 + sx * 0.04, 0.2), (x1 + sx * 0.04, R.under(x1) - 0.04), 0.13, 0.0, TD, rng, sag=0.003, col=tc, segs=1)
    elif pat == 'k':
        for sx in (-1, 1):
            # raking struts from the king post's foot up toward the rafters
            H.beam(m, (sx * 0.1, 0.24), (sx * hw * 0.55, R.under(hw * 0.55) - 0.08), 0.13, 0.0, TD * 0.9, rng, sag=0.004, col=tc, segs=1)
            # a collar under the apex
        H.beam(m, (-hw * 0.38, R.under(hw * 0.38) - 0.12), (hw * 0.38, R.under(hw * 0.38) - 0.12), 0.13, 0.0, TD, rng, sag=0.006, col=tc, segs=2)
    return {"Wall_Own": m}, {}


# ----------------------------------------------------------- the spire --
def spire(p):
    """The tower's roof: a square spire over a 4 m tower, its eaves kicked out 50 cm, hips capped, a lead cap and an
    iron finial. Faces in courses (tiles or shingles), cut at the hips."""
    kind = p['cover']
    rng = H.Rng(p['seed'])
    m = H.Mesh()
    hw = 2.0
    apex = p.get('apex', 4.9)
    t = (apex - KNEE_Y) / (hw + 0.1)
    xe = hw + p['eave']

    def ht(r):  # height at distance r (the square's half-size) from the axis
        xk = hw + 0.1
        return KNEE_Y + t * (xk - r) if r <= xk else KNEE_Y - KICK * (r - xk)
    c = COURSE[kind]
    rows = round(ATL_R["regions"][kind]["m"][1] / c)
    # the courses by their square half-size r, from the eave up (arc length along the face's middle line)
    rs = [xe]
    while rs[-1] > 0.05:
        r = rs[-1]
        slope = KICK if r > hw + 0.1 else t
        rs.append(max(r - c / math.hypot(1, slope), 0.0))
    rs[-1] = 0.0
    for f in range(4):
        ang = f * math.pi / 2
        ca, sa = math.cos(ang), math.sin(ang)

        def W(x, z, y):  # face-local (x across, z out) to piece space
            return (x * ca - z * sa, y, x * sa + z * ca)
        for k in range(len(rs) - 1):
            ra, rb = rs[k], rs[k + 1]
            ya, yb = ht(ra) + (STEP if k else STEP), ht(rb)
            g = hsh(p['seed'], f, k)
            row = (k + f) % rows
            ua0 = hsh(p['seed'], f, k, 1) * 0.5
            P = [W(-ra, ra, ya), W(ra, ra, ya), W(rb, rb, yb), W(-rb, rb, yb)]
            uv = uvq(kind, ua0, ua0 + 2 * ra / 4.0, (row + 1) / rows, row / rows)
            uv[2] = (uv[2][0] - (uv[1][0] - uv[0][0]) * (ra - rb) / (2 * ra) if ra > 0 else uv[2][0], uv[2][1])
            uv[3] = (uv[3][0] + (uv[1][0] - uv[0][0]) * (ra - rb) / (2 * ra) if ra > 0 else uv[3][0], uv[3][1])
            quad(m, P, uv, (1.0, g, 1.0, 1.0), W(0, 1, 0.5))
            if k > 0:
                yl = ht(ra)
                P = [W(-ra, ra, yl), W(ra, ra, yl), W(ra, ra, ya), W(-ra, ra, ya)]
                quad(m, P, uvq(kind, ua0, ua0 + 2 * ra / 4.0, (row + 1) / rows, (row + 0.95) / rows), (0.6, g, 1.0, 1.0), W(0, 1, -0.3))
        # the fascia and the soffit
        ye = ht(xe)
        P = [W(-xe, xe, ye - COVER - 0.03), W(xe, xe, ye - COVER - 0.03), W(xe, xe, ye + STEP), W(-xe, xe, ye + STEP)]
        quad(m, P, uvq('boards', 0.0, 2 * xe / 4, 1.0, 0.2), (0.9, 0.5, 0.0, 1.0), W(0, 1, 0))
        yi = ht(hw) - COVER
        P = [W(-xe, xe, ye - COVER), W(xe, xe, ye - COVER), W(hw, hw, yi), W(-hw, hw, yi)]
        quad(m, P, uvq('soffit', 0.0, 2 * xe / 4, 0.0, 1.0), (0.55, 0.5, 0.0, 1.0), (0, -1, 0))
        # rafter ends: five a side
        for i, xx in enumerate(np.linspace(-hw + 0.3, hw - 0.3, 5)):
            a = np.array([hw - 0.1, ht(hw - 0.1) - COVER])
            b = np.array([xe - 0.05, ht(xe - 0.05) - COVER])
            dep, hwz = 0.12, 0.04
            A1, B1 = a + np.array([0, -dep]), np.array([b[0], b[1] - dep])
            for sz in (-1, 1):
                P = [W(xx + sz * hwz, a[0], a[1]), W(xx + sz * hwz, b[0], b[1]), W(xx + sz * hwz, B1[0], B1[1]), W(xx + sz * hwz, A1[0], A1[1])]
                quad(m, P, uvq('boards', 0.1, 0.3, 0.1, 0.6), (0.7, 0.5, 0.0, 1.0), W(sz, 0, 0))
            P = [W(xx - hwz, A1[0], A1[1]), W(xx - hwz, B1[0], B1[1]), W(xx + hwz, B1[0], B1[1]), W(xx + hwz, A1[0], A1[1])]
            quad(m, P, uvq('boards', 0.1, 0.3, 0.6, 0.95), (0.65, 0.5, 0.0, 1.0), (0, -1, 0))
            P = [W(xx - hwz, b[0], b[1]), W(xx + hwz, b[0], b[1]), W(xx + hwz, B1[0], B1[1]), W(xx - hwz, B1[0], B1[1])]
            quad(m, P, uvq('endgrain', 0.1, 0.42, 0.1, 0.58), (0.9, 0.5, 0.0, 1.0), W(0, 1, 0))
        # the hip: a run of caps (or a board) from the corner up to the apex
        n = 9
        for i in range(n):
            ra, rb = xe * (1 - i / n), xe * (1 - (i + 1) / n)
            ya, yb = ht(ra) + 0.05, ht(rb) + 0.05
            wd = 0.08
            for sgn in (-1, 1):
                # the cap's two flanks: from its crown on the hip line down to each face
                fa = np.array(W(ra, ra, ya)); fb = np.array(W(rb, rb, yb))
                oa = np.array(W(ra - wd if sgn < 0 else ra, ra if sgn < 0 else ra - wd, ya - 0.07))
                ob = np.array(W(rb - wd if sgn < 0 else rb, rb if sgn < 0 else rb - wd, yb - 0.07))
                reg = 'ridge' if kind == 'pantile' else 'boards'
                quad(m, [oa, ob, fb, fa], uvq(reg, (i % 10) / 10, (i % 10 + 1) / 10, 0.5 + 0.4 * sgn, 0.5), (1.0, hsh(f, i), 1.0 if kind == 'pantile' else 0.0, 1.0), (0, 1, 0))
    # the lead cap and the finial
    ya = ht(0.0)
    def prism(r0, r1, y0, y1, reg, n=8, col=(0.9, 0.5, 0.0, 1.0), cap=False):
        for i in range(n):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            P = [(r0 * math.cos(a0), y0, r0 * math.sin(a0)), (r0 * math.cos(a1), y0, r0 * math.sin(a1)),
                 (r1 * math.cos(a1), y1, r1 * math.sin(a1)), (r1 * math.cos(a0), y1, r1 * math.sin(a0))]
            quad(m, P, uvq(reg, i / n, (i + 1) / n, 1.0, 0.0), col, (math.cos(a0 + math.pi / n), 0, math.sin(a0 + math.pi / n)))
    prism(0.24, 0.1, ya - 0.25, ya + 0.12, 'lead')
    prism(0.035, 0.03, ya + 0.12, ya + 1.0, 'iron', 6)
    prism(0.03, 0.09, ya + 1.0, ya + 1.09, 'iron', 6)
    prism(0.09, 0.0, ya + 1.09, ya + 1.2, 'iron', 6)
    prism(0.03, 0.01, ya + 1.2, ya + 1.75, 'iron', 6)
    # (no sag on a spire: its faces are short; the alpha 0)
    for i in range(len(m.C)):
        r, g, b, _ = m.C[i]
        m.C[i] = (r, g, b, 0.0)
    return {"Roof_Own": m}, {"eave_cm": round(100 * p['eave'], 1), "apex_y": round(ya, 3)}


# --------------------------------------------------------- the chimney --
def chimney(p):
    """A stack from inside the roof up past it: brick or stone, a corbelled course, a capstone (stone) or a brick
    cap and clay pots; the top's soot in the vertex colour's blue (the shader darkens by it)."""
    rng = H.Rng(p['seed'])
    m = H.Mesh()
    hx, hz = p.get('hx', 0.34), p.get('hz', 0.28)
    hgt = p['h']
    reg = p['wall']
    lean = (rng(-0.015, 0.015), rng(-0.015, 0.015))

    def soot(y):
        return min(1.0, max(0.0, (y - (hgt - 1.0)) / 1.0)) ** 1.5

    def stack(y0, y1, ex, ez, reg, top=False):
        for (ax, sx) in ((0, 1), (0, -1), (2, 1), (2, -1)):
            hh, ww = (ex, ez) if ax == 0 else (ez, ex)
            # face: normal along axis ax sign sx
            O = np.array([0.0, y0, 0.0])
            if ax == 0:
                O[0] = sx * ex
                U = np.array([0.0, 0.0, -sx * 1.0])
                Oc = O + np.array([0, 0, sx * ez])
                span = 2 * ez
            else:
                O[2] = sx * ez
                U = np.array([sx * 1.0, 0.0, 0.0])
                Oc = O + np.array([-sx * ex, 0, 0])
                span = 2 * ex
            V = np.array([lean[0], 1.0, lean[1]])
            H.face(m, Oc, U, V, [H.rect(0, 0, span, y1 - y0)], reg, off=(rng(0, 2), rng(0, 0.6)),
                   col=lambda s, t, y0=y0: (1.0, 0.5, soot(y0 + t), 1.0))
        if top:
            H.face(m, (-ex + lean[0] * y1, y1, ez + lean[1] * y1), (1, 0, 0), (0, 0, -1), [H.rect(0, 0, 2 * ex, 2 * ez)], reg,
                   col=lambda s, t: (0.4, 0.5, 1.0, 1.0))
    band = hgt - 0.32
    stack(0.0, band, hx, hz, reg)
    stack(band, band + 0.12, hx + 0.04, hz + 0.04, reg)
    stack(band + 0.12, hgt - 0.08, hx, hz, reg)
    if reg == 'stone':
        stack(hgt - 0.08, hgt, hx + 0.07, hz + 0.07, 'stone', top=True)
    else:
        stack(hgt - 0.08, hgt, hx + 0.03, hz + 0.03, 'brick', top=True)
    # the pots
    pots = p.get('pots', 0)
    for i in range(pots):
        cx = (i - (pots - 1) / 2) * 0.3 + lean[0] * hgt
        cz = lean[1] * hgt
        ph = rng(0.32, 0.45)
        n = 8
        for j in range(n):
            a0, a1 = 2 * math.pi * j / n, 2 * math.pi * (j + 1) / n
            for (r0, r1, y0, y1, c0, c1) in ((0.1, 0.085, hgt, hgt + ph, 0.9, 1.0), (0.085, 0.1, hgt + ph, hgt + ph + 0.05, 1.0, 1.0)):
                P = [(cx + r0 * math.cos(a0), y0, cz + r0 * math.sin(a0)), (cx + r0 * math.cos(a1), y0, cz + r0 * math.sin(a1)),
                     (cx + r1 * math.cos(a1), y1, cz + r1 * math.sin(a1)), (cx + r1 * math.cos(a0), y1, cz + r1 * math.sin(a0))]
                quad(m, P, uvq('pot', j / n, (j + 1) / n, 1.0, 0.0), (1.0, 0.5, c1, 1.0), (math.cos(a0 + math.pi / n), 0, math.sin(a0 + math.pi / n)))
            # the dark mouth
            P = [(cx, hgt + ph + 0.02, cz), (cx + 0.085 * math.cos(a0), hgt + ph + 0.05, cz + 0.085 * math.sin(a0)),
                 (cx + 0.085 * math.cos(a1), hgt + ph + 0.05, cz + 0.085 * math.sin(a1)), (cx, hgt + ph + 0.02, cz)]
            quad(m, P, uvq('iron', 0.4, 0.6, 0.4, 0.6), (0.1, 0.5, 1.0, 1.0), (0, 1, 0))
    for i in range(len(m.C)):
        r, g, b, _ = m.C[i]
        m.C[i] = (r, g, b, 0.0)
    return {"Roof_Own": m}, {"h": hgt}


KINDS = {"body": body, "gable": gable, "spire": spire, "chimney": chimney}


def write_glb(path, name, mats):
    """Several primitives (one per material) in one mesh."""
    import struct
    blobs, views, accs, prims, mlist = [], [], [], [], []
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
    allP = []
    for mi, (mname, m) in enumerate(mats.items()):
        P = np.array(m.P, np.float32)
        allP.append(P)
        attrs = {"POSITION": add(P, 34962, "VEC3", 5126, True), "NORMAL": add(np.array(m.N, np.float32), 34962, "VEC3", 5126),
                 "TEXCOORD_0": add(np.array(m.T, np.float32), 34962, "VEC2", 5126),
                 "COLOR_0": add(np.clip(np.array(m.C, np.float32), 0, 1), 34962, "VEC4", 5126)}
        prims.append({"attributes": attrs, "indices": add(np.array(m.I, np.uint32), 34963, "SCALAR", 5125), "material": mi})
        mlist.append({"name": mname, "pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1], "metallicFactor": 0, "roughnessFactor": 0.9}})
    g = {"asset": {"version": "2.0", "generator": "env_roof.py"}, "scene": 0, "scenes": [{"nodes": [0]}],
         "nodes": [{"name": name, "mesh": 0}], "meshes": [{"name": name, "primitives": prims}], "materials": mlist,
         "buffers": [{"byteLength": off}], "bufferViews": views, "accessors": accs}
    js = json.dumps(g, separators=(",", ":")).encode()
    js += b" " * ((-len(js)) % 4)
    bin_ = b"".join(blobs)
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(bin_)))
        f.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
        f.write(struct.pack("<II", len(bin_), 0x004E4942) + bin_)
    return np.concatenate(allP)


def main():
    data = json.loads(DATA.read_text())["presets"]
    names = sys.argv[1:] or list(data)
    meta_path = OUT / "props.json"
    info = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    for name in names:
        p = data[name]
        mats, meas = KINDS[p['kind']](p)
        P = write_glb(OUT / f"{name}.glb", name, mats)
        info[name] = {"tris": sum(m.tris() for m in mats.values()), "box": [round(float(v), 3) for v in list(P.min(0)) + list(P.max(0))], **meas}
        print(f"ROOF {name}: {info[name]}")
    meta_path.write_text(json.dumps(info, indent=1))


if __name__ == "__main__":
    main()
