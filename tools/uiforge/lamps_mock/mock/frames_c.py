"""Direction C, The Day's Book.  python frames_c.py [day|night|all]  ->  out/C_day.png, out/C_night.png, out/C_crops.png
The base is the game's own frame with the book open at today's Lamps page (camera shifted for the book). The panel's
frame, head, tab chain and prompt row stay as the game draws them; the content rect is cleared to the panel's own clean
ground and the board, header, card, wick tabs and wick panel are drawn in it with A's language (skins/c.py)."""
import os, sys, math
import numpy as np
import cv2
from PIL import Image
import draw as D
import frames as FR                       # before foot (foot puts tools/uiforge, which has a frames.py, first on the path)
import foot as F
from board import Board
from state import State, ROOT as ROOT_ID, SPARE, FROM_LEVELS, FROM_STORY, TYPE
from view import View, STOPS, lamp_d
import view as VW
import text as T
import skins.c as S

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
SHOT = os.path.join(os.path.dirname(HERE), 'shoot', 'out')
CACHE = os.path.join(os.path.dirname(HERE), 'c_work')

CLEAR = (1016, 145, 1891, 950)          # the panel's inner content area, cleared of today's list (x0, y0, x1, y1 excl.)
CONTENT = (1030, 152, 1876, 948)        # the layout rect inside it
BOARD = (1030, 232, 1876, 874)          # the board's window (feathered over 48 px, no edge line)
TABS_Y = 911
WICK_RECT = (1040, 634, 1866, 862)      # the wick panel, the panel's lower third (826 x 228)
FOCUS_X = 1418                          # day: the focus lamp's screen x (card to its right, inside the panel)
SEAT_SKILLS = 5


# ---------------------------------------------------------------- the panel's ground
def _nconv(img, m, s):
    m = m.astype(np.float32)
    num = cv2.GaussianBlur(img * m[..., None], (0, 0), s)
    den = cv2.GaussianBlur(m, (0, 0), s)[..., None]
    return num / np.maximum(den, 1e-4), den[..., 0]


def _fill(img, hole, seed):
    """holes: the local tone (normalized convolution, growing sigma) plus grain matched to the local clean grain"""
    known = ~hole
    tone = np.zeros_like(img); got = np.zeros(hole.shape, bool)
    for s in (2, 4, 8, 16, 32, 64):
        t, den = _nconv(img, known, s)
        ok = (den > 0.15) & ~got & hole
        tone[ok] = t[ok]; got |= ok
    hp = img - cv2.GaussianBlur(img, (0, 0), 2)
    far = known & ~cv2.dilate(hole.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    sd = np.sqrt(np.maximum(_nconv(hp ** 2, far, 12)[0].mean(2, keepdims=True), 0))
    g = np.random.default_rng(seed).normal(0, 1, img.shape[:2]).astype(np.float32)
    g = cv2.GaussianBlur(g, (0, 0), 0.7); g /= g.std()
    out = img.copy()
    out[hole] = (tone + g[..., None] * sd)[hole]
    return out


def clean_grounds():
    """today's list removed from both bases. Day: the Lamps and Wicks pages share the camera, so where one page has
    type the other usually shows the bare ground; below the shorter Wicks panel the raw world shows, and the panel is
    measured as ground = 0.163 * world + 20 (no blur, fitted). Night: the same type mask, filled by tone + grain."""
    pd, pn = os.path.join(CACHE, 'C_ground_day.png'), os.path.join(CACHE, 'C_ground_night.png')
    if os.path.exists(pd) and os.path.exists(pn):
        return D.load_rgb(pd), D.load_rgb(pn)
    ld = lambda n: np.asarray(Image.open(os.path.join(SHOT, n)).convert('RGB')).astype(np.float32)
    A, Wk, N = ld('u25_today_lamps.png'), ld('u25_today_wicks.png'), ld('u25_today_lamps_night.png')
    x0, y0, x1, y1 = CLEAR
    a, w, n = A[y0:y1, x0:x1], Wk[y0:y1, x0:x1], N[y0:y1, x0:x1]
    H, Wd = a.shape[:2]
    yw = 772 - y0                                        # the Wicks panel's bottom edge
    K, C = np.array([0.163, 0.161, 0.156], np.float32), np.array([21.83, 18.28, 19.51], np.float32)
    up = np.zeros((H, Wd), bool); up[:yw - 16] = True
    lo = np.zeros((H, Wd), bool); lo[yw + 1:] = True
    agree = (np.abs(a - w).max(2) < 5) & up
    # type both pages share at the same pixels (the hint line): a stroke stands far off its local median
    med = cv2.medianBlur(np.clip(a, 0, 255).astype(np.uint8), 9).astype(np.float32)
    agree &= np.abs(a - med).max(2) < 12
    P = w * K + C
    B, _ = _nconv(a, agree, 4)
    da, dw = np.abs(a - B).max(2), np.abs(w - B).max(2)
    TA = up & ~agree & ((da >= dw) | (da > 7))
    TA |= up & (np.abs(a - med).max(2) >= 12)
    TA |= lo & (np.abs(a - P).max(2) > 6)
    band = ~up & ~lo
    Bb, _ = _nconv(a, ~TA & (up | lo), 5)
    TA |= band & (np.abs(a - Bb).max(2) > 5)
    TA = cv2.dilate(TA.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    wclean = up & (np.abs(w - B).max(2) < 6) & (np.abs(w - med).max(2) < 12)
    day, hole = a.copy(), TA.copy()
    m = TA & wclean; day[m] = w[m]; hole &= ~m
    m = TA & lo; day[m] = P[m]; hole &= ~m
    day = _fill(day, hole, 1)
    night = _fill(n, TA, 2)
    A[y0:y1, x0:x1] = day; N[y0:y1, x0:x1] = night
    os.makedirs(CACHE, exist_ok=True)
    for arr, p in ((A, pd), (N, pn)):
        Image.fromarray(np.clip(arr + 0.5, 0, 255).astype(np.uint8)).save(p)
    return D.load_rgb(pd), D.load_rgb(pn)


# ---------------------------------------------------------------- the wick tabs' art (the HUD's seats)
def tab_discs():
    fo, _ = F.foot_rgb('town_day')
    if hasattr(F, 'paint_seat'):
        fo = F.paint_seat(fo, 0)                           # Sunder in the first seat (as the A frames show it)
    discs = [S.seat_disc(fo, F.SEATS[i]) for i in range(SEAT_SKILLS)]
    empty = S.seat_disc(fo, F.SEATS[5])
    return discs, empty


def clip(Lr, rect):
    x0, y0, x1, y1 = rect
    m = np.zeros(Lr.shape[:2], np.float32); m[y0:y1, x0:x1] = 1
    Lr *= m[..., None]
    return Lr


FEATHER = 48                             # the board fades to 0 over 48 px inside its window's edge (C1)
BAND_TOP = WICK_RECT[1]                  # night: the wick band's top (its hairline); the board's window ends here
PROMPT_HOLE = (1262, 953, 1648, 991)     # the game's prompt row (stand-in caps), cleared to the ground and redrawn (C6)
WICK_LAY = dict(kx=256, braid=40, lx0=350, pitch=60, tx=519, row0=44, pitch_y=64, text_gap=39, right=24, sum_cx=532, kind_dx=-20)  # r3


def feather(rect, f=FEATHER):
    x0, y0, x1, y1 = rect
    X = np.arange(1920, dtype=np.float32)[None, :] + 0.5
    Y = np.arange(1080, dtype=np.float32)[:, None] + 0.5
    m = D.smoothstep(0, f, X - x0) * D.smoothstep(0, f, x1 - X) * D.smoothstep(0, f, Y - y0) * D.smoothstep(0, f, y1 - Y)
    return m.astype(np.float32)


def _rect_circle_hit(rect, x, y, r):
    x0, y0, x1, y1 = rect
    return math.hypot(x - min(max(x, x0), x1), y - min(max(y, y0), y1)) < r


def _inside(rect, x, y, r):
    x0, y0, x1, y1 = rect
    return x0 <= x - r and x + r <= x1 and y0 <= y - r and y + r <= y1


def place_card_c(fx, fy, R, h, discs, protect, window, w=380):
    """C3: right of the lamp, left, above, below (22 px from its rim), each shifted in 8 px steps up to +-120 px; the
    first spot where no lamp disc crosses the card's edge band (rect grown by 6), no protected point (lit, path,
    focus) lies under it, and the card stays 16 px inside the window. Else the least overlap."""
    wx0, wy0, wx1, wy1 = window
    shifts = [0] + [s for k in range(8, 121, 8) for s in (k, -k)]
    best = None
    for side in ('right', 'left', 'above', 'below'):
        for s in shifts:
            if side == 'right':
                x0, y0 = fx + R + 22, fy - h / 2 + s
            elif side == 'left':
                x0, y0 = fx - R - 22 - w, fy - h / 2 + s
            elif side == 'above':
                x0, y0 = fx - w / 2 + s, fy - R - 22 - h
            else:
                x0, y0 = fx - w / 2 + s, fy + R + 22
            x0, y0 = int(round(x0)), int(round(y0))
            if x0 < wx0 + 16 or x0 + w > wx1 - 16 or y0 < wy0 + 16 or y0 + h > wy1 - 16:
                continue
            g = (x0 - 6, y0 - 6, x0 + w + 6, y0 + h + 6)
            cross = sum(1 for (x, y, r) in discs
                        if _rect_circle_hit(g, x, y, r) and not _inside((x0, y0, x0 + w, y0 + h), x, y, r))
            cover = sum(1 for (x, y, r) in protect if _rect_circle_hit(g, x, y, r))
            score = cross + 100 * cover
            if score == 0:
                return x0, y0, side, s, 0
            if best is None or score < best[-1]:
                best = (x0, y0, side, s, score)
    return best


def card_shadow(L, x0, y0, w, h):
    """a soft 20 px drop shadow (black, 45%) under a card"""
    pad = 44
    m = np.zeros((h + 2 * pad, w + 2 * pad), np.float32)
    m[pad + 4:pad + 4 + h, pad:pad + w] = 1.0                 # 4 px down
    m = D.gauss(m, 8.0) * 0.45
    p = np.zeros(m.shape + (4,), np.float32); p[..., 3] = m
    D.stamp(L, x0 - pad, y0 - pad, p)


def clear_prompt_row(base):
    x0, y0, x1, y1 = PROMPT_HOLE
    X0, Y0, X1, Y1 = x0 - 60, y0 - 9, x1 + 60, y1 + 9
    crop = base[Y0:Y1, X0:X1].copy()
    hole = np.zeros(crop.shape[:2], bool); hole[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0] = True
    base = base.copy()
    base[Y0:Y1, X0:X1] = _fill(crop, hole, 7)
    return base


def prompt_row(L, items, cx=1455, cy=971):
    """the book's prompt row: caps (as the header's Space / Z) then the word, centered on the panel"""
    f = T.font('alegreya-sans-500', 16)
    gap, sep = 9, 32
    tot = sum(S.cap_width(k) + gap + T.width(wd, f) for k, wd in items) + sep * (len(items) - 1)
    x = cx - tot / 2
    for k, wd in items:
        x += S.cap(L, k, int(round(x)), cy, 28) + gap
        T.draw(L, x, cy + 6, wd, f, S.INK_BODY, 0.95)
        x += T.width(wd, f) + sep


# ---------------------------------------------------------------- frames
def frame(which):
    ground_day, ground_night = clean_grounds()
    base = ground_night if which == 'night' else ground_day
    base = clear_prompt_row(base)
    b = Board(); st = State(b)
    stop = 'road'
    s = STOPS['road']
    night = which == 'night'
    win = (BOARD[0], BOARD[1], BOARD[2], BAND_TOP if night else BOARD[3])
    wx0, wy0, wx1, wy1 = win
    rmax = max(lamp_d(b.lamps[i]['kind'], stop) for i in st.lit) / 2
    wick_card = card = None
    if not night:
        focus = 'sunderer.morning_in_the_steel'
        path = st.path(focus)[0]
        ids = list(st.lit) + list(path) + [focus]
        xs = [b.lamps[i]['x'] for i in ids]; ys = [b.lamps[i]['y'] for i in ids]
        # C2: the build's bbox (lit + path + focus) centered in the window; zoom out only if a lit lamp would sit < 96 px in
        s = min(s, (wx1 - wx0 - 2 * 96 - 2 * rmax) / max(max(xs) - min(xs), 1),
                (wy1 - wy0 - 2 * 96 - 2 * rmax) / max(max(ys) - min(ys), 1))
        c = FR.card_for(b, st, focus, stop)
        c['prompts'] = [('key:Click', 'Light the path')]
        h = S.card_height(c)
        R = lamp_d(b.lamps[focus]['kind'], stop) * 1.1 / 2
        src = st.path(focus)[1]
        bc = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
        # if no clean card spot exists with the build dead center (C2 vs C3), slide the build the least distance that
        # gives one, keeping every lit lamp >= 96 px inside the window
        offs = sorted(((ox, oy) for ox in range(-240, 241, 8) for oy in range(-160, 161, 8)), key=lambda o: math.hypot(*o))
        best = None
        for ox, oy in offs:
            v = View(bc, s, screen_c=((wx0 + wx1) / 2 + ox, (wy0 + wy1) / 2 + oy), stop=stop)
            pos = {i: v(l['x'], l['y']) for i, l in b.lamps.items()}
            if min(min(pos[i][0] - wx0, wx1 - pos[i][0], pos[i][1] - wy0, wy1 - pos[i][1]) -
                   lamp_d(b.lamps[i]['kind'], stop) / 2 for i in st.lit) < 96:
                continue
            discs = [(x, y, lamp_d(b.lamps[i]['kind'], stop) / 2) for i, (x, y) in pos.items()
                     if wx0 - 30 < x < wx1 + 30 and wy0 - 30 < y < wy1 + 30]
            prot = [(pos[i][0], pos[i][1], lamp_d(b.lamps[i]['kind'], stop) / 2 + 4) for i in ids]
            chain = [src] + list(path)
            for a_, c_ in zip(chain, chain[1:]):
                (ax, ay), (cx_, cy_) = pos[a_], pos[c_]
                for t in np.linspace(0, 1, 12):
                    prot.append((ax + (cx_ - ax) * t, ay + (cy_ - ay) * t, 3))
            fx, fy = pos[focus]
            r = place_card_c(fx, fy, R + 5, h, discs, prot, win)
            if r and (best is None or r[-1] < best[1][-1]):
                best = ((ox, oy), r)
            if r and r[-1] == 0:
                break
        (ox, oy), (x0, y0, side, shift, score) = best
        y0 += 14                                            # r3: both unlit lamps above clear its edge (top at 644)
        card = (c, x0, y0, h)
        print('card: %s of the focus, shift %d, overlap %d, build offset (%d, %d), at %s' %
              (side, shift, score, ox, oy, (x0, y0, x0 + 380, y0 + h)))
        view = View(bc, s, screen_c=((wx0 + wx1) / 2 + ox, (wy0 + wy1) / 2 + oy), stop=stop)
    else:
        focus = None
        # r3: no card; the board recenters in the band (header row -> wick band): the hearth, its spokes and every lit
        # lamp >= 96 px inside the window; zoom out continuously if needed (shapes scale with it)
        fx0, fy0, fx1, fy1 = wx0 + 96, wy0 + 96, wx1 - 96, wy1 - 96
        keep = list(st.lit) + [j for j in b.adj[ROOT_ID] if j not in st.lit]
        pts = [b.lamps[i] for i in keep]
        xs = [l['x'] for l in pts]; ys = [l['y'] for l in pts]
        s = min(0.80, (fx1 - fx0) / (max(xs) - min(xs) + 2 * rmax / 0.80), (fy1 - fy0) / (max(ys) - min(ys) + 2 * rmax / 0.80))
        bc = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
        VW.SHAPE_K[0] = s / 0.80
        print('night view: scale %.2f, kept %d lamps' % (s, len(keep)))
        view = View(bc, s, screen_c=((fx0 + fx1) / 2, (fy0 + fy1) / 2), stop=stop)
    BL = FR.board_layers(S, st, view, which, focus, wick_open=night)
    fm = feather(win)
    for k in ('Lroad', 'Lglow', 'Lhalo', 'Llamp'):
        BL[k] *= fm[..., None]
    # check: every lit lamp's inset (C2: 96 px by day; C3: 48 px in the band by night)
    ins = min(min(BL['pos'][i][0] - wx0, wx1 - BL['pos'][i][0], BL['pos'][i][1] - wy0, wy1 - BL['pos'][i][1])
              - lamp_d(b.lamps[i]['kind'], stop) / 2 for i in st.lit)
    rgb = base.copy()
    if night:                                              # C5: the wick band, the panel's ground x0.65, no box
        X = np.arange(1920, dtype=np.float32)[None, :] + 0.5
        Y = np.arange(1080, dtype=np.float32)[:, None] + 0.5
        bm = D.smoothstep(BAND_TOP, BAND_TOP + 24, Y) * (1 - D.smoothstep(WICK_RECT[3], WICK_RECT[3] + 24, Y)) * \
             D.smoothstep(BOARD[0], BOARD[0] + 24, X) * D.smoothstep(BOARD[2], BOARD[2] - 24, X)
        rgb = rgb * (1 - 0.35 * bm)[..., None]
    # r3: a 15% warm glow on the page under the lit cluster (radial, #ffcf86, 1.6x the cluster's bbox), A's pools on paper
    lx_ = [BL['pos'][i][0] for i in st.lit]; ly_ = [BL['pos'][i][1] for i in st.lit]
    gcx, gcy = (min(lx_) + max(lx_)) / 2, (min(ly_) + max(ly_)) / 2
    grx, gry = max(max(lx_) - min(lx_), 40) * 0.8, max(max(ly_) - min(ly_), 40) * 0.8
    Xg = np.arange(1920, dtype=np.float32)[None, :] + 0.5; Yg = np.arange(1080, dtype=np.float32)[:, None] + 0.5
    rr = np.sqrt(((Xg - gcx) / grx) ** 2 + ((Yg - gcy) / gry) ** 2)
    wg = (1 - D.smoothstep(0.0, 1.0, rr)) * 0.15 * feather(CLEAR, 24)
    rgb = 1 - (1 - rgb) * (1 - wg[..., None] * D.hexc('#ffcf86'))
    rgb = D.over(rgb, BL['Lroad'])
    rgb = S.road_glow(rgb, BL['Lglow'], stop)
    rgb = S.light(rgb, BL['Lhalo'])
    rgb = D.over(rgb, BL['Llamp'])
    # labels: never in the feather, and >= 40 px from the header, the cards and the wick band (N6)
    blockers = [(0, 0, wx0 + 40, 1080), (wx1 - 40, 0, 1920, 1080), (0, 0, 1920, wy0 + 40), (0, wy1 - 40, 1920, 1080)]
    if focus:
        _, x0, y0, h = card
        blockers.append((x0 - 40, y0 - 40, x0 + 420, y0 + h + 40))
    Llab = D.layer()
    for text, x, y in FR.place_labels(b, view, S, stop, BL['lamp_px'], blockers, lit=st.lit):
        S.label(Llab, x, y, text, stop)
    rgb = D.over(rgb, Llab * fm[..., None])
    VW.SHAPE_K[0] = 1.0
    Lui, Lh2 = D.layer(), D.layer()
    if night:
        ws = FR.wick_spec()                                 # r3: no hairline: the band's feathered top is its edge
        ws.pop('smoke', None)
        ws['rect'] = WICK_RECT
        ws['boxless'] = True
        ws['lay'] = WICK_LAY
        wp = S.wick(Lui, Lh2, ws)
        sd = tab_discs()[0][0]                              # the skill's own seat art (the HUD's Sunder seat, 56 px)
        D.stamp(Lui, WICK_RECT[0] + 46 - sd.shape[1] // 2, WICK_RECT[1] + 50 - sd.shape[0] // 2, sd)
        tx, ty, tr = wp['turn0']
        S.focus_ring(Lui, Lh2, tx, ty - 2, tr + 2)          # the focus: the Turn (ring clears its flame crown)
        import text as T_                                   # its plan numeral back over the ring (r3: upper left)
        T_.draw(Lui, tx - 16, ty - 16 + 4.5, '4', T_.font('alegreya-sans-800', 12), S.GOLD, 1.0, align='center',
                halo=(3, 1.0, S.DARK))
    if card:
        card_shadow(Lui, card[1], card[2], 380, card[3])
        S.card(Lui, card[1], card[2], card[0])
    lit_n = len(st.lit)
    hd = dict(count=SPARE, sub='%d lit · %d from levels, %d from the story' % (lit_n, FROM_LEVELS, FROM_STORY),
              post=None if night else 'At the Waystation’s lamp-post: lamps go out free',
              night='By night the board is read only' if night else None,
              coins=1, layout_name=TYPE, keys=[('Space', 'Light my way'), ('Z', 'Open wide')])
    S.header(Lui, Lh2, hd, CONTENT)
    discs, empty = tab_discs()
    centers = S.tabs(Lui, Lh2, dict(discs=discs, chosen=0, y=TABS_Y, x0=CONTENT[0], x1=CONTENT[2], all_learned=empty))
    S.tab_ring(Lui, Lh2, centers[0], 28.0, stem_to=wp['knot'] if night else None)   # r3: the stem is the braid's root
    if night:
        prompt_row(Lui, [('Click', 'Plan'), ('Space', 'Light my way'), ('Tab', 'Board')])
    else:
        prompt_row(Lui, [('Click', 'Choose a wick'), ('Tab', 'Wick'), ('F', 'Find'), ('H', 'Home')])
    rgb = S.light(rgb, Lh2)
    rgb = D.over(rgb, Lui)
    p = os.path.join(OUT, 'C_%s.png' % which)
    D.save(p, rgb)
    print('wrote', p, '| scale %.3f' % s, '| lit inset min %.0f px' % ins, '| focus:', focus)
    return p


def crops():
    d = Image.open(os.path.join(OUT, 'C_day.png')).crop((BOARD[0] - 14, BOARD[1] - 82, BOARD[2] + 14, 960))
    n = Image.open(os.path.join(OUT, 'C_night.png')).crop((BOARD[0] - 14, BOARD[1] - 82, BOARD[2] + 14, 960))
    c = Image.new('RGB', (d.width * 2 + 8, d.height), (0, 0, 0))
    c.paste(d, (0, 0)); c.paste(n, (d.width + 8, 0))
    c.save(os.path.join(OUT, 'C_crops.png'))


if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    for w in (['day', 'night'] if which == 'all' else [which]):
        frame(w)
    if os.path.exists(os.path.join(OUT, 'C_day.png')) and os.path.exists(os.path.join(OUT, 'C_night.png')):
        crops()
