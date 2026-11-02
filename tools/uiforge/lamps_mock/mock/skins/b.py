"""Direction B, The Lamplighter's Wheel: a bronze astrolabe over smoked glass. Skin hooks as in ../SKINS.md, plus the
optional begin(view, tod) and ornament(rgb, view). A's layout code (card, header, wick, prompts) is reused, rebound to
this module's palette and materials."""
import math, types
import numpy as np
import cv2
import draw as D
import text as T
from draw import hexc, Patch
from view import lamp_d, FLARE_KINDS
import skins.a as A
from skins.a import glyph, stamp_glyph, icon, stamp_icon, _shield, CHIP, INK, INK_BODY, INK_DIM, GOLD, RED, DARK, FOCUS
from board import Board

NAME = 'B'
LABEL_SKIP = ('oldroad',)          # the Old Roads' names are engraved in the wheel's band
VALLEY_DY = 29                     # the Valley view sits 29 px low so the wheel's top clears the header (see report)

# ---------------------------------------------------------------- palette (the HUD's bronze)
BR_DEEP, BR_BODY, BR_HI, BR_TOP = hexc('#2a1d12'), hexc('#8a6538'), hexc('#d8b578'), hexc('#f4e2b0')
INLAY = hexc('#e2c06e'); ENGRAVE = hexc('#c9a46a'); GROOVE = hexc('#07090c')
COL_LO, COL_HI = hexc('#6b4c2a'), hexc('#d4ae6c')
RIM_GOLD = ENGRAVE
GLASS_IN, GLASS_OUT = hexc('#2a2c30'), hexc('#0b0c0e')
LIT_STOPS = [(0, hexc('#fff1c4')), (0.55, hexc('#f2a640')), (1, hexc('#8a4a14'))]
LIT_RIM, LIT_HALO = hexc('#ffd98a'), hexc('#ffb04a')
BLUE_NEAR = [(0, hexc('#23459e')), (1, hexc('#0e1c40'))]
BLUE_LIT = [(0, hexc('#d8e8ff')), (0.35, hexc('#7fb0ff')), (1, hexc('#1d3e9e'))]
BLUE_HALO = hexc('#5d8dff')
FL_UNLIT = [(0, hexc('#3a2416')), (1, hexc('#0e0a08'))]
FL_LIT = [(0, hexc('#fff3cf')), (0.3, hexc('#ffd27a')), (1, hexc('#d0561c'))]
FL_HALO = hexc('#ff7a2a')
ASLEEP = hexc('#a9b4c2'); EMBER = hexc('#ff9a3c')
WIRE, WIRE_SPEC = hexc('#e8c06a'), hexc('#fff3c8')
FUSE, PREVIEW = hexc('#f2a23c'), hexc('#ffc46a')
ROAD_LIT, ROAD_COLD = WIRE, hexc('#8a7a62')
LIGHT = np.array([-0.50, -0.62, 0.60], np.float32); LIGHT /= np.linalg.norm(LIGHT)
HALF = LIGHT + np.array([0, 0, 1], np.float32); HALF /= np.linalg.norm(HALF)

# the wheel, in board units
R_IN, R_OUT, R_BOSS = 1290.0, 1350.0, 30.0
CIRCLES = (300.0, 650.0, 1040.0)
BOSSES = (45, 135, 225, 315)

_V = {'O': (960.0, 522.0), 's': 0.8, 'stop': 'road'}


def _rebind(f):
    return types.FunctionType(f.__code__, globals(), f.__name__, f.__defaults__, f.__closure__)


def begin(view, tod):
    _V['O'] = view(0.0, 0.0); _V['s'] = view.s; _V['stop'] = view.stop; _V['tod'] = tod


def _polar():
    Y, X = np.mgrid[0:1080, 0:1920].astype(np.float32)
    ox, oy = _V['O']
    return X + 0.5 - ox, Y + 0.5 - oy


def ramp(v):
    """bronze tone ramp: v 0 deep shadow .. 1 highlight .. >1 hot spec"""
    ts = [0.0, 0.18, 0.55, 0.92, 1.25]
    cs = [BR_DEEP * 0.55, BR_DEEP, BR_BODY, BR_HI, BR_TOP]
    out = np.zeros(np.shape(v) + (3,), np.float32)
    for k in range(3):
        out[..., k] = np.interp(v, ts, [c[k] for c in cs])
    return out


# ================================================================= the world: smoked glass inside, dimmed outside
def grade(rgb, tod):
    dx, dy = _polar()
    d = np.hypot(dx, dy)
    s = _V['s']
    inside = np.clip((R_IN + R_OUT) / 2 * s - d + 0.5, 0, 1)[..., None]
    lum = (rgb * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(-1, keepdims=True)
    gin = (lum + (rgb - lum) * 0.60)
    gin = cv2.GaussianBlur(gin, (0, 0), 1.1) * 0.28
    Y, X = np.mgrid[0:1080, 0:1920].astype(np.float32)
    t = np.clip(np.hypot(X, Y) / (0.40 * math.hypot(1920, 1080)), 0, 1)
    refl = (0.06 * (1 - D.smoothstep(0, 1, t)))[..., None] * hexc('#fff0d8')
    gin = 1 - (1 - gin) * (1 - refl)
    gout = (lum + (rgb - lum) * 0.70) * 0.55
    return gin * inside + gout * (1 - inside)


def pools(graded, world, pts, stop):
    return graded                                     # the glass glows, not the ground


# ================================================================= the wheel
def _arc_strip(words, f, track, gap):
    """the name as a straight 3x strip mask; words split around a boss gap (px at 3x) if gap"""
    from PIL import Image, ImageDraw
    asc, desc = f.getmetrics()
    parts = [' '.join(words)] if not gap else [words[0], ' '.join(words[1:])]
    ws = [T.width(p, f, track) for p in parts]
    W = int(sum(ws) + (gap or 0)) + 8
    H = asc + desc + 8
    im = Image.new('L', (W, H), 0); dr = ImageDraw.Draw(im)
    x = 4
    xc = 4 + sum(ws) / 2 if not gap else 4 + ws[0] + gap / 2      # the strip's anchor: its middle, or the boss gap's
    for k, p in enumerate(parts):
        for c in p:
            dr.text((x, 4 + asc), c, font=f, fill=255, anchor='ls')
            x += f.getlength(c) + track * f.size
        x += -track * f.size + (gap or 0)
    cap = f.getbbox('H', anchor='ls')
    crow = 4 + asc + (cap[1] + cap[3]) / 2           # the caps' middle row
    return np.asarray(im, np.float32) / 255, crow, W, xc


def _arc_text(text, ang, rc, size, gap_px=0.0):
    """coverage (1x, full screen) of text engraved along the circle r = rc (screen px) centered on board angle ang"""
    ss = 3
    f = T.font('cinzel-600', size * ss)
    words = text.split(' ')
    M, crow, Wm, xc = _arc_strip(words, f, 0.20, gap_px * ss if gap_px else 0)
    ox, oy = _V['O']
    phc = -math.radians(ang)
    top = math.sin(phc) <= 1e-6                        # upper half (and the right side): tops outward, clockwise
    half = max(xc, Wm - xc) / ss / rc + 0.02
    pts = [(ox + r * math.cos(phc + a), oy + r * math.sin(phc + a)) for a in np.linspace(-half, half, 24)
           for r in (rc - size, rc + size)]
    x0, y0 = max(0, int(min(p[0] for p in pts)) - 2), max(0, int(min(p[1] for p in pts)) - 2)
    x1, y1 = min(1920, int(max(p[0] for p in pts)) + 3), min(1080, int(max(p[1] for p in pts)) + 3)
    out = np.zeros((1080, 1920), np.float32)
    if x1 <= x0 or y1 <= y0:
        return out
    gy, gx = np.mgrid[0:(y1 - y0) * ss, 0:(x1 - x0) * ss].astype(np.float32)
    X, Y = x0 + (gx + 0.5) / ss - ox, y0 + (gy + 0.5) / ss - oy
    rho = np.hypot(X, Y)
    dph = (np.arctan2(Y, X) - phc + np.pi) % (2 * np.pi) - np.pi
    if top:
        u = dph * rc * ss + xc
        v = crow - (rho - rc) * ss
    else:
        u = -dph * rc * ss + xc
        v = crow + (rho - rc) * ss
    m = cv2.remap(M, u.astype(np.float32), v.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT,
                  borderValue=0)
    out[y0:y1, x0:x1] = m.reshape(y1 - y0, ss, x1 - x0, ss).mean((1, 3))
    return out


def _over(rgb, cov, col):
    c = np.clip(cov, 0, 1)[..., None]
    return rgb * (1 - c) + np.asarray(col, np.float32) * c


def ornament(rgb, view):
    s = _V['s']
    valley = _V['stop'] == 'valley'
    dx, dy = _polar()
    d = np.hypot(dx, dy) + 1e-6
    ex, ey = dx / d, dy / d
    # ---- the engraved circles inside (hearths, roads, crossings): a dark line + a bronze catch-light 1 px down-right
    for r in CIRCLES:
        rp = r * s
        dl = np.abs(d - rp) - 0.5
        hl = np.abs(np.hypot(dx - 1, dy - 1) - rp) - 0.5
        rgb = _over(rgb, np.clip(0.5 - hl, 0, 1) * 0.25, ENGRAVE)
        rgb = _over(rgb, np.clip(0.5 - dl, 0, 1) * 0.55, GROOVE)
    rm, hw = (R_IN + R_OUT) / 2 * s, (R_OUT - R_IN) / 2 * s
    band = np.abs(d - rm) - hw                          # sdf of the band
    near = band < 40
    if not near.any():
        return rgb
    # ---- its shadow on the glass and the world (light from the upper left: shadow falls down-right)
    cov = np.clip(0.5 - band, 0, 1)
    sh = cv2.GaussianBlur(np.roll(np.roll(cov, 3, 0), 3, 1), (0, 0), 3.0 if not valley else 1.6)
    rgb = rgb * (1 - 0.55 * sh * (1 - cov))[..., None]
    # ---- the band: two rolled rims (outside the inlays) around a flat, recessed, polished track (the names' ground)
    ins = 4.0 if not valley else 3.0
    ta = hw - ins - 1.0                                  # the track's half width
    ad = np.abs(d - rm)
    sg = np.sign(d - rm)
    w_ = np.clip((ad - ta) / (hw - ta), 0, 1)
    th_rim = sg * (-0.55 + 1.65 * w_)
    th_trk = 0.10 * (d - rm) / ta
    rimm = D.smoothstep(-0.6, 0.6, ad - ta)             # 0 on the track, 1 on the rims
    v = None
    for th, wgt in ((th_trk, 1 - rimm), (th_rim, rimm)):
        nx, ny, nz = ex * np.sin(th), ey * np.sin(th), np.cos(th)
        ndl = np.clip(nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2], 0, 1)
        ndh = np.clip(nx * HALF[0] + ny * HALF[1] + nz * HALF[2], 0, 1)
        if wgt is rimm:
            vv = 0.05 + 0.40 * ndl + 0.85 * ndh ** 18 + 0.15 * ndh ** 4
        else:
            vv = 0.04 + 0.30 * ndl + 0.22 * ndh ** 30
        v = vv * wgt if v is None else v + vv * wgt
    # brushed: fine circumferential streaks (noise across the radius only), a soft broad sheen along the angle
    rng = np.random.default_rng(7)
    nr = cv2.GaussianBlur(rng.standard_normal((1, 4096)).astype(np.float32), (0, 0), 1.2)[0]
    nr /= nr.std() + 1e-6
    idx = np.clip(((d - rm + hw) * 2).astype(np.int32), 0, 4095)
    ang = np.arctan2(dy, dx)
    v = v * (1 + 0.035 * nr[idx]) * (1 + 0.05 * np.sin(2 * ang + 0.7))
    body = ramp(v)
    rgb = _over(rgb, cov, body)
    # ---- the gold inlay, 1 px, 4 px inside each edge
    for rl in (rm + hw - ins - 0.5, rm - hw + ins + 0.5):
        ln = np.clip(0.5 - (np.abs(d - rl) - 0.5), 0, 1) * cov
        lit = np.clip(-(ex * LIGHT[0] + ey * LIGHT[1]) * (1 if rl > rm else -1), -1, 1)
        col = INLAY[None, None] * (0.88 + 0.16 * lit)[..., None]
        rgb = rgb * (1 - ln[..., None]) + col * ln[..., None]
        # the inlay's cut: a faint dark line just outside it, on the side away from the light
        cut = np.clip(0.5 - (np.abs(d - (rl + (1 if rl > rm else -1))) - 0.5), 0, 1) * cov * 0.22
        rgb = _over(rgb, cut, BR_DEEP * 0.5)
    # ---- the Old Roads' names, engraved
    b = Board()
    size = 13 if valley else 19
    for g in b.groups.values():
        if g['kind'] != 'oldroad':
            continue
        name = g['name'].upper().replace("'", '’')
        a = float(g['angle'])
        gap = 0.0
        if any(abs((a - q + 180) % 360 - 180) < 6 for q in BOSSES):
            gap = 2 * R_BOSS * s + (14 if not valley else 8)
        m = _arc_text(name, a, rm, size, gap) * cov
        if not m.any():
            continue
        shifted = np.zeros_like(m); shifted[1:, 1:] = m[:-1, :-1]
        inner = np.clip(m - shifted, 0, 1) * (0.55 if not valley else 0.40)
        rgb = _over(rgb, m, ENGRAVE)
        rgb = _over(rgb, inner, hexc('#140d07'))
    # ---- four bosses at the quarters
    rb = R_BOSS * s
    ox, oy = _V['O']
    for q in BOSSES:
        bx, by = ox + rm * math.cos(-math.radians(q)), oy + rm * math.sin(-math.radians(q))
        if not (-rb < bx < 1920 + rb and -rb < by < 1080 + rb):
            continue
        x0, y0 = int(bx - rb - 8), int(by - rb - 8)
        x1, y1 = int(bx + rb + 9), int(by + rb + 9)
        xa, ya, xb, yb = max(0, x0), max(0, y0), min(1920, x1), min(1080, y1)
        ss = 3
        gy, gx = np.mgrid[0:(y1 - y0) * ss, 0:(x1 - x0) * ss].astype(np.float32)
        X, Y = x0 + (gx + 0.5) / ss - bx, y0 + (gy + 0.5) / ss - by
        q2 = np.hypot(X, Y) / rb
        cv_ = np.clip((1 - q2) * rb * ss + 0.5, 0, 1)
        nz = np.sqrt(np.clip(1 - q2 ** 2, 0, 1))
        nx_, ny_ = X / rb, Y / rb
        # a dome flattened a little on top
        nx_, ny_ = nx_ * 0.9, ny_ * 0.9
        nn = np.sqrt(nx_ ** 2 + ny_ ** 2 + nz ** 2) + 1e-6
        dl = np.clip((nx_ * LIGHT[0] + ny_ * LIGHT[1] + nz * LIGHT[2]) / nn, 0, 1)
        dh = np.clip((nx_ * HALF[0] + ny_ * HALF[1] + nz * HALF[2]) / nn, 0, 1)
        vv = 0.05 + 0.70 * dl + 0.75 * dh ** 48 + 0.12 * dh ** 8
        col = ramp(vv)
        # its base: a 1 px dark seat ring and a soft contact shadow down-right
        sh_ = np.clip((1 - np.hypot(X - 2, Y - 2) / (rb + 1.5)) * rb * ss * 0.25 + 0.5, 0, 1)
        dn = lambda a_: a_.reshape(y1 - y0, ss, x1 - x0, ss, *a_.shape[2:]).mean((1, 3))
        cvd, shd, cold = dn(cv_), dn(sh_), dn(col * cv_[..., None])
        ring = dn(np.clip(0.5 - np.abs(np.hypot(X, Y) - rb + 0.5) * ss, 0, 1))
        reg = rgb[ya:yb, xa:xb]
        sl = (slice(ya - y0, yb - y0), slice(xa - x0, xb - x0))
        reg[:] = reg * (1 - 0.6 * shd[sl][..., None] * (1 - cvd[sl][..., None]))
        reg[:] = reg * (1 - cvd[sl][..., None]) + cold[sl]
        reg[:] = _over(reg, ring[sl] * 0.55, BR_DEEP * 0.4)
    return rgb


# ================================================================= roads: grooves and gold wire
def roads(L, Lglow, segs, stop):
    valley = stop == 'valley'
    for s in segs:
        (ax, ay), (bx, by) = s['a'], s['b']
        n = math.hypot(bx - ax, by - ay)
        if n < 1:
            continue
        k = s['kind']
        pad = 4
        P = Patch(min(ax, bx) - pad, min(ay, by) - pad, max(ax, bx) + pad, max(ay, by) + pad)
        if k == 'cold':
            fa = s.get('fade', 1.0)
            w = 1.0 if valley else 1.25
            dh, _, _ = D.segment(P, ax, ay + 1, bx, by + 1)
            P.fill(dh - 0.5, ENGRAVE, 0.18 * fa)
            d, _, _ = D.segment(P, ax, ay, bx, by)
            P.fill(d - w / 2, GROOVE, 0.70 * fa)
            P.stamp(L)
        elif k == 'lit':
            w = 1.5 if valley else 2.0
            d, _, _ = D.segment(P, ax, ay, bx, by)
            P.fill(d - w / 2, WIRE, 1.0)
            G = Patch(P.x0, P.y0, P.x1, P.y1); G.a = P.a.copy()
            if not valley:                              # the specular on its upper edge
                nx_, ny_ = -(by - ay) / n, (bx - ax) / n
                if ny_ > 0:
                    nx_, ny_ = -nx_, -ny_
                ds, _, _ = D.segment(P, ax + nx_ * 0.5, ay + ny_ * 0.5, bx + nx_ * 0.5, by + ny_ * 0.5)
                P.fill(np.maximum(ds - 0.5, d - w / 2), WIRE_SPEC, 0.60)
            P.stamp(L)
            G.stamp(Lglow)
        else:
            w = 1.5 if k == 'fuse' else 1.75
            d, t, sl = D.segment(P, ax, ay, bx, by)
            on, period = 4.0, 8.0
            uu = (sl + s.get('phase', 0.0)) % period
            dd = np.maximum(d - w / 2, np.abs(uu - on / 2) - on / 2)
            if k == 'path':
                dh, _, _ = D.segment(P, ax, ay + 1, bx, by + 1)
                P.fill(dh - 0.5, ENGRAVE, 0.18)
                P.fill(d - 0.625, GROOVE, 0.6)
            col, al = (FUSE, 0.85) if k == 'fuse' else (PREVIEW, 0.95)
            P.fill(dd, col, al)
            P.stamp(L)
            g = Patch(P.x0, P.y0, P.x1, P.y1); g.a = P.a * 0.5
            g.stamp(Lglow)


def road_glow(rgb, Lglow, stop):
    g = D.gauss(Lglow[..., :3], 1.4 if stop == 'valley' else 2.0) * 0.30 * 1.6
    return D.screen_add(rgb, np.dstack([g, g[..., :1]]))


def light(rgb, Lhalo):
    return D.screen_add(rgb, Lhalo)


# ================================================================= lamps: glass cabochons in bronze collets
def _graded(P, x, y, R, lo=COL_LO, hi=COL_HI):
    """bronze graded from the lower right (lo) to the upper left (hi)"""
    t = np.clip((-(P.X - x) - (P.Y - y)) / (1.414 * max(R, 1)) * 0.5 + 0.5, 0, 1)[..., None]
    t = t * t * (3 - 2 * t)
    return lo * (1 - t) + hi * t


def _specular(P, x, y, rg, a=0.35):
    """an ellipse highlight on the glass's upper left"""
    cx, cy = x - 0.36 * rg, y - 0.40 * rg
    c, s_ = math.cos(-math.pi / 4), math.sin(-math.pi / 4)
    u = ((P.X - cx) * c + (P.Y - cy) * s_) / (0.30 * rg)
    v = (-(P.X - cx) * s_ + (P.Y - cy) * c) / (0.16 * rg)
    dd = (np.hypot(u, v) - 1) * 0.16 * rg
    P.fill(dd, hexc('#ffffff'), a, soft=0.35)


def lamp(L, Lhalo, x, y, kind, st, stop, dim=False, focus=False, onpath=False, gate=0, seed=0, breathe=0.85, fade=1.0,
         near=True):
    valley = stop == 'valley'
    D_ = lamp_d(kind, stop) * (1.1 if focus else 1.0)
    R = D_ / 2
    lit = st == 'lit'
    flare = kind in FLARE_KINDS
    blue = kind == 'blue'
    far_blue = blue and not lit and not near
    asleep = lit and dim
    blocked = st == 'blocked'
    rng = np.random.default_rng(seed)
    flick = 1.0 + (rng.uniform(-0.04, 0.04) if not valley else 0.0)
    op = (0.5 if dim else 1.0) * fade
    pad = R + 9
    P = Patch(x - pad, y - pad, x + pad, y + pad)

    if kind == 'rite':
        body = D.lozenge(P, x, y, R, R)
    elif kind == 'attribute':
        body = D.rbox(P, x, y, R, R, R * 0.35)
    elif kind == 'link' and not valley:
        body = D.stadium(P, x, y, R, R * 14 / 22)
    elif kind == 'ultimate' and not valley:
        body = D.star(P, x, y, R * 0.58, R, 8, -np.pi / 2)
    elif kind == 'ultimateMod' and not valley:
        body = D.teardrop(P, x, y + R * 0.08, R * 2.0, R * 1.25)
    else:
        body = D.circle(P, x, y, R)

    if valley:                                          # dots: a bead of glass in a hairline collet
        if lit:
            stops = BLUE_LIT if blue else FL_LIT if flare else LIT_STOPS
            P.fill(body, D.radial(P, x - R * 0.2, y - R * 0.25, R * 1.2, stops))
            D.glow_spot(Lhalo, x, y, max(R * 1.3, 2.5), BLUE_HALO if blue else FL_HALO if flare else LIT_HALO, 0.50)
        else:
            stops = BLUE_NEAR if (blue and not far_blue) else FL_UNLIT if flare else [(0, GLASS_IN), (1, GLASS_OUT)]
            P.fill(body, D.radial(P, x - R * 0.3, y - R * 0.3, R * 1.3, stops), 0.95)
            P.fill(D.ring(body + 0.5, 1.0), _graded(P, x, y, R), 0.85 if not blocked else 0.5)
            if st == 'available':
                P.fill(D.ring(body + 0.5, 1.2), EMBER, 0.9 * breathe)
                D.glow_spot(Lhalo, x, y, 3.0, EMBER, 0.35 * breathe)
        if focus:
            P.fill(D.ring(D.circle(P, x, y, R + 4), 1.5), FOCUS, 1.0)
            D.glow_spot(Lhalo, x, y, R + 5, FOCUS, 0.15)
        P.stamp(L, op)
        return

    cw = 2.0 if D_ >= 14 else 1.5                      # the collet's width
    glass = body + cw

    # ---- the link: a bronze chain link, or gold wire when lit
    if kind == 'link':
        rd = D.ring(body + 1.0, 2.0)
        if lit:
            P.fill(D.ring(body + 1.0, 3.2), hexc('#1a1008'), 0.5)
            P.fill(rd, WIRE, 1.0)
            P.fill(np.maximum(D.ring(body + 0.5, 1.0), (P.Y - y)), WIRE_SPEC, 0.55)
            D.glow_spot(Lhalo, x, y, R * 0.9, LIT_HALO, 0.40 * flick)
        else:
            P.fill(D.ring(body + 1.0, 3.4), GROOVE, 0.55)
            P.fill(rd, _graded(P, x, y, R), 0.9 if not blocked else 0.5)
    else:
        # ---- the glass
        if lit and not asleep:
            stops = BLUE_LIT if blue else FL_LIT if flare else LIT_STOPS
            P.fill(glass, D.radial(P, x - R * 0.10, y - R * 0.14, R * 1.05, stops) * flick)
            # glowing from within: a soft hot core
            core = np.exp(-((P.X - x) ** 2 + (P.Y - y + R * 0.05) ** 2) / (2 * (R * 0.32) ** 2))
            cc = P.cov(glass) * core * 0.55
            P.a[..., :3] += cc[..., None] * (hexc('#fff8e6') - P.a[..., :3]) * 0.9
            halo = BLUE_HALO if blue else FL_HALO if flare else LIT_HALO
            D.glow_spot(Lhalo, x, y, 0.8 * R, halo, 0.45 * flick)
            D.glow_spot(Lhalo, x, y, 1.8 * R, halo, 0.07 * flick)
            _specular(P, x, y, R - cw, 0.35)
        else:
            if blue and not far_blue:
                stops = BLUE_NEAR
            elif flare:
                stops = FL_UNLIT
            else:
                stops = [(0, GLASS_IN), (1, GLASS_OUT)]
            P.fill(glass, D.radial(P, x - R * 0.28, y - R * 0.32, R * 1.3, stops), 0.96)
            if onpath:                                  # a warm inner glow at 40%
                gl = np.exp(-((P.X - x) ** 2 + (P.Y - y) ** 2) / (2 * (R * 0.55) ** 2))[..., None] * hexc('#ffb860')
                cov = P.cov(glass)[..., None] * 0.40
                P.a[..., :3] = P.a[..., :3] + gl * cov
            # the lower-right rim light, inside the glass's edge
            rim = np.clip(((P.X - x) + (P.Y - y)) / (1.414 * R) * 1.6 - 0.2, 0, 1)
            band = P.cov(glass) - P.cov(glass + 1.3)
            c = np.clip(band * rim, 0, 1) * 0.15 * (0.6 if blocked else 1)
            P.a[..., :3] = P.a[..., :3] * (1 - c[..., None]) + ENGRAVE * c[..., None]
            if not asleep and kind not in ('ultimateMod',):
                _specular(P, x, y, R - cw, 0.35 if not blocked else 0.22)
        # ---- the collet
        if dim:
            th = np.arctan2(P.Y - y, P.X - x)
            per = 4.0 / max(R, 1)
            dots = (np.abs(((th / per) % 1.0) - 0.5) * 2 - 0.5) * per * R / 2
            P.fill(np.maximum(D.ring(body + cw / 2, cw), dots), hexc('#8c8f95'), 0.85)
        else:
            col = _graded(P, x, y, R)
            if blocked:
                col = col * 0.62
            P.fill(D.ring(body + cw / 2, cw), col, 1.0)
            # a hairline catch-light on the collet's outer upper-left edge
            hl = np.clip((-(P.X - x) - (P.Y - y)) / (1.414 * R), 0, 1)
            P.fill(np.maximum(D.ring(body + 0.35, 0.7), -hl + 0.35), hexc('#f2dca0'), 0.5 * (0.5 if blocked else 1))
        if blue:                                        # the 4 prongs: claws over the stone's edge
            for k in range(4):
                a = np.pi / 4 + k * np.pi / 2
                ux, uy = np.cos(a), np.sin(a)
                dseg, _, _ = D.segment(P, x + ux * (R - 0.16 * R), y + uy * (R - 0.16 * R),
                                       x + ux * (R + 0.20 * R), y + uy * (R + 0.20 * R))
                pc = _graded(P, x, y, R) * (0.62 if blocked else 1.0)
                P.fill(dseg - 1.75, GROOVE, 0.45, soft=0.4)
                P.fill(dseg - 1.45, pc, 1.0)

    # ---- the kind's marks, cut in the glass
    mark_c = hexc('#7a3e10') if (lit and not asleep) else ENGRAVE
    mark_a = 0.75 if lit else 0.45
    if kind == 'notable':
        P.fill(D.ring(D.circle(P, x, y, R * 0.55), 1.0), mark_c, 0.55 if lit else 0.40)
    elif kind == 'entry':
        P.fill(D.ring(D.circle(P, x, y, R - cw - 2.5), 1.0), _graded(P, x, y, R), 0.85 if not blocked else 0.5)
    elif kind == 'start':
        col = _graded(P, x, y, R)
        P.fill(D.ring(body + 1.75, 3.5), col, 1.0)                                    # the heavy collet
        P.fill(np.maximum(D.ring(body + 0.35, 0.7), -np.clip((-(P.X - x) - (P.Y - y)) / (1.414 * R), 0, 1) + 0.35),
               hexc('#f2dca0'), 0.5)
        for k in range(4):
            a = k * np.pi / 2 + np.pi / 4
            ux, uy = np.cos(a), np.sin(a)
            dseg, _, _ = D.segment(P, x + ux * (R + 1.0), y + uy * (R + 1.0), x + ux * (R + 6.5), y + uy * (R + 6.5))
            P.fill(dseg - 1.4, GROOVE, 0.4, soft=0.4)
            P.fill(dseg - 1.1, col, 1.0)
        P.fill(_shield(P, x, y + 0.5, R * 0.34), hexc('#6a3a10') if lit else ENGRAVE, 0.85 if lit else 0.6)
    elif kind == 'form':
        dch = np.maximum(np.abs(P.Y - y) * 0.9 + (P.X - x) - R * 0.25, -(np.abs(P.Y - y) * 0.9 + (P.X - x) - R * 0.25) - 1.3)
        P.fill(np.maximum(dch, np.abs(P.Y - y) - R * 0.40), mark_c, mark_a)
    elif kind == 'reflex':
        arc = D.ring(D.circle(P, x + R * 0.22, y, R * 0.42), 1.1)
        P.fill(np.maximum(arc, (P.X - (x + R * 0.1)) * 1.0), mark_c, mark_a)

    if asleep:
        P.fill(D.teardrop(P, x, y + R * 0.1, R * 0.6, R * 0.34), ASLEEP, 0.9)

    # ---- available: the ember rim, breathing, over the collet
    if st == 'available':
        P.fill(D.ring(body + cw / 2, 1.75), EMBER, 0.85 * breathe)
        D.glow_spot(Lhalo, x, y, R + 3.0, EMBER, 0.22 * breathe)

    if dim:                                              # desaturated
        lum = (P.a[..., :3] * np.array([0.3, 0.59, 0.11], np.float32)).sum(-1, keepdims=True)
        P.a[..., :3] = P.a[..., :3] * 0.25 + lum * 0.75
    P.stamp(L, op)
    if kind == 'hand':                                   # an open palm, cut in the glass: palm, four fingers, a thumb
        c = hexc('#6a3a10') if lit else ENGRAVE
        H = Patch(x - R, y - R, x + R, y + R)
        k = R / 9.0
        palm = D.rbox(H, x + 0.3 * k, y + 2.2 * k, 3.1 * k, 2.6 * k, 1.6 * k)
        fing = None
        for i, (fx, top) in enumerate(((-2.1, -3.4), (-0.4, -4.6), (1.3, -4.3), (2.9, -3.0))):
            sd, _, _ = D.segment(H, x + fx * k, y + 0.5 * k, x + fx * k, y + top * k)
            sd = sd - 0.75 * k
            fing = sd if fing is None else np.minimum(fing, sd)
        th_, _, _ = D.segment(H, x - 2.6 * k, y + 2.6 * k, x - 4.6 * k, y + 0.2 * k)
        H.fill(np.minimum(np.minimum(palm, fing), th_ - 0.75 * k), c, (0.9 if lit else 0.65) * op)
        H.stamp(L)
    if blocked and gate and stop != 'valley':
        notch(L, x, y, R, gate)
    if focus:
        focus_ring(L, Lhalo, x, y, R)


_CLEAN = {}


def _stamp_clean(L, name, cx, cy, px, color, alpha=1.0):
    """a painterly glyph as a clean silhouette: its alpha thresholded at full size, then area-downsampled"""
    k = (name, px)
    if k not in _CLEAN:
        import os
        from PIL import Image
        a = np.asarray(Image.open(os.path.join(A.ICONS, name + '.png')).convert('RGBA'), np.float32)[..., 3] / 255
        a = cv2.GaussianBlur(a, (0, 0), 2.0)
        a = np.clip((a - 0.45) * 8, 0, 1)
        _CLEAN[k] = cv2.resize(a, (px, px), interpolation=cv2.INTER_AREA)
    a = _CLEAN[k] * alpha
    p = np.zeros(a.shape + (4,), np.float32)
    p[..., :3] = a[..., None] * np.asarray(color, np.float32); p[..., 3] = a
    D.stamp(L, int(round(cx - px / 2)), int(round(cy - px / 2)), p)


def notch(L, x, y, R, gate):
    """the gate numeral on a small bronze tab at the lamp's lower right"""
    cx, cy = x + R * 0.72 + 5, y + R * 0.72 + 4
    P = Patch(cx - 10, cy - 9, cx + 10, cy + 9)
    w = 7.5 if gate >= 10 else 5.5
    tab = D.rbox(P, cx, cy, w, 7, 2.0)
    P.fill(tab, hexc('#17110b'), 0.94)
    P.fill(D.ring(tab + 0.5, 1.0), COL_LO, 0.9)
    P.stamp(L)
    T.draw(L, cx + 0.5, cy + 4, str(gate), T.font('alegreya-sans-800', 11), hexc('#cdae72'), 1.0, align='center')


def focus_ring(L, Lhalo, x, y, R):
    P = Patch(x - R - 10, y - R - 10, x + R + 10, y + R + 10)
    P.fill(D.ring(D.circle(P, x, y, R + 5), 1.5), FOCUS, 1.0)
    P.stamp(L)
    D.glow_spot(Lhalo, x, y, R + 6, FOCUS, 0.12)
    G = Patch(x - R - 16, y - R - 16, x + R + 16, y + R + 16)
    G.fill(D.ring(D.circle(G, x, y, R + 5), 1.5), FOCUS, 0.30, soft=3.0)
    G.stamp(Lhalo, 1.0, 'add')


# ================================================================= labels: engraved gold
def label_font(stop):
    return T.font('cinzel-600', 16 if stop == 'valley' else 15)


def label_size(s, stop):
    return T.width(s, label_font(stop), 0.16), 11 if stop == 'valley' else 10


def label(L, x, y, s, stop):
    f = label_font(stop)
    _, ch = label_size(s, stop)
    T.draw(L, x, y + ch / 2 + 1, s, f, hexc('#0a0604'), 0.95, track=0.16, align='center')
    T.draw(L, x, y + ch / 2, s, f, ENGRAVE, 1.0, track=0.16, align='center')


# ================================================================= panels: the HUD's bronze plate
def _plate_sdf(P, x0, y0, x1, y1, ch=2.0):
    cx, cy, hw, hh = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
    box = D.rbox(P, cx, cy, hw, hh, 0.0)
    cham = ((np.abs(P.X - cx) - hw) + (np.abs(P.Y - cy) - hh) + ch) / 1.41421
    return np.maximum(box, cham)


def glass_panel(L, x0, y0, x1, y1, Lbehind=None):
    """(the name is A's hook) the HUD panel's plate: dark bronze, 1 px bronze edge, 1 px gold inlay 3 px inside"""
    P = Patch(x0 - 2, y0 - 2, x1 + 2, y1 + 2)
    d = _plate_sdf(P, x0, y0, x1, y1)
    P.fill(d, hexc('#17110b'), 0.92)
    P.fill(D.ring(d + 0.5, 1.0), COL_LO, 1.0)
    P.fill(D.ring(d + 3.5, 1.0), INLAY, 0.80)
    P.stamp(L)


rule = _rebind(A.rule)
chip = _rebind(A.chip)
_card = _rebind(A._card)
card = _rebind(A.card)
card_height = _rebind(A.card_height)
header = _rebind(A.header)
prompts = A.prompts
_wick = _rebind(A.wick)
wick_lamp = _rebind(A.wick_lamp)
seat_ring = _rebind(A.seat_ring)


def coin(L, Lhalo, cx, cy, numeral, active):
    """a bronze coin: dark plate, bronze edge, the gold inlay ring lit when active"""
    R = 16
    P = Patch(cx - R - 3, cy - R - 3, cx + R + 3, cy + R + 3)
    d = D.circle(P, cx, cy, R)
    P.fill(d, D.radial(P, cx - 5, cy - 6, R * 1.4, [(0, hexc('#3a2a17') if active else hexc('#261b10')),
                                                    (1, hexc('#120d08'))]), 0.96)
    P.fill(D.ring(d + 0.5, 1.0), _graded(P, cx, cy, R), 1.0)
    P.fill(D.ring(d + 3.5, 1.0), INLAY, 0.85 if active else 0.28)
    P.stamp(L)
    if active:
        D.glow_spot(Lhalo, cx, cy, R * 0.9, hexc('#ffb04a'), 0.14)
    T.draw(L, cx + 0.5, cy + 5, numeral, T.font('cinzel-700', 14), hexc('#ffe2a6') if active else hexc('#7d6a4c'), 1.0,
           align='center')


def wick(L, Lhalo, w):
    pos = _wick(L, Lhalo, w)
    # the skill's own art, as the seat shows it: a tinted disc in a bronze collet
    x0, y0 = w['rect'][:2]
    ax, ay = x0 + 46, y0 + 50
    P = Patch(ax - 31, ay - 31, ax + 31, ay + 31)
    d = D.circle(P, ax, ay, 28)
    P.fill(d + 2.0, D.radial(P, ax - 4, ay - 5, 30, [(0, hexc('#6e4030')), (1, hexc('#090c0e'))]), 1.0)
    P.fill(D.ring(d + 1.0, 2.0), _graded(P, ax, ay, 28), 1.0)
    P.fill(np.maximum(D.ring(d + 0.35, 0.7), -np.clip((-(P.X - ax) - (P.Y - ay)) / 40, 0, 1) + 0.35), hexc('#f2dca0'), 0.5)
    P.stamp(L)
    stamp_glyph(L, w['glyph'], ax, ay, 42, hexc('#eacb9b'), 1.0, gain=1.15)
    return pos


def wick_turn(L, Lhalo, x, y, s, crossed):
    R = 17
    st = 'lit' if s == 'lit' else 'available' if s == 'planned' else 'unlit'
    lamp(L, Lhalo, x, y, 'turn', st, 'road', dim=crossed)
    P = Patch(x - R, y - R - 12, x + R, y - R + 6)          # the flame crown, in bronze (gold when lit)
    for dx, h in ((-6.5, 7.0), (0, 10.0), (6.5, 7.0)):
        td = D.teardrop(P, x + dx, y - R - h / 2 + 3, h, 4.2)
        if st == 'lit':
            P.fill(td, hexc('#ffd98a'), 0.95)
        else:
            P.fill(td, _graded(P, x, y - R, 8), 0.75 * (0.5 if crossed else 1))
    P.stamp(L)
    if st == 'lit':
        D.glow_spot(Lhalo, x, y - R - 3, 6, LIT_HALO, 0.35)
    if crossed:
        P = Patch(x - R - 6, y - R - 6, x + R + 6, y + R + 6)
        ds, _, _ = D.segment(P, x - R - 2, y + R + 2, x + R + 2, y - R - 2)
        P.fill(ds - 1.6, hexc('#050607'), 0.9)
        P.fill(np.abs(ds - 2.1) - 0.4, COL_HI, 0.30)
        P.stamp(L)
