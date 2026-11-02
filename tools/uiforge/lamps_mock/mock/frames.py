"""python frames.py A|B|C day|night|valley|all  ->  out/<X>_<frame>.png (1920x1080, 1:1)
Layout, state and placement live here; every pixel's look comes from the skin (skins/<x>.py, see SKINS.md)."""
import os, sys, math, zlib, importlib
import numpy as np
import draw as D
from draw import hexc
import foot as F
from board import Board
from state import State, RITE_TAGS, DIM_REASON, FEEDS_TEXT, SPARE, FROM_LEVELS, FROM_STORY, TYPE
from view import View, STOPS, FIELD, lamp_d, lamp_r_toward

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
CENTER = (430.0, -250.0)
SEAT_CHOSEN = 2                      # Sunder isn't seated in the shot: seat 3 is repainted as Sunder (foot.paint_seat)
WICK_RECT = (650, 666, 1290, 948)      # r3: grows up 54 px (the card's gone; the Turn row holds it all)      # 640 wide; bottom 948 (not 968): the keeper's bowl is 11 px from (1290, 968); now >= 24 px clear of both statues
LABEL_KINDS_ROAD = ('hearth', 'road', 'bridge', 'crossing', 'oldroad')
FEEDS = [('glyph/slash', True), ('glyph/sword', True)]


def seed(i):
    return zlib.crc32(i.encode())


# ---------------------------------------------------------------- labels
def label_specs(b, stop, skip=()):
    out = []
    if stop == 'valley':
        for c in ('warden', 'reaver', 'arcanist', 'stalker'):
            ids = [l for l in b.lamps.values() if l.get('calling') == c and l['region'] in ('hearth', 'road', 'bridge')]
            out.append((c.upper(), ids))
        out.append(('THE FORD', [l for l in b.lamps.values() if l['group'] == 'ford']))
        for g in b.groups.values():
            if g['kind'] == 'oldroad' and 'oldroad' not in skip:
                out.append((g['name'].upper(), [l for l in b.lamps.values() if l['group'] == g['id']]))
    else:
        for g in b.groups.values():
            if g['kind'] in LABEL_KINDS_ROAD and g['kind'] not in skip:
                out.append((b.group_name(g['id']), [l for l in b.lamps.values() if l['group'] == g['id']]))
    return out


def place_labels(b, view, S, stop, lamp_px, blockers, forbid=None, ytop=96, ybot=952, lit=()):
    """each label beside its group's centroid, pushed outward from the Ford, clear of lamps and other labels.
    forbid: an optional bool map (H, W) no label box may touch; ytop / ybot: the label boxes' vertical limits"""
    placed = []
    I = None
    if forbid is not None:
        I = np.pad(forbid.astype(np.int32), ((1, 0), (1, 0))).cumsum(0).cumsum(1)

    def hit(box):
        if I is None:
            return False
        x0, y0 = max(int(box[0]), 0), max(int(box[1]), 0)
        x1, y1 = min(int(np.ceil(box[2])), 1920), min(int(np.ceil(box[3])), 1080)
        if x1 <= x0 or y1 <= y0:
            return False
        return I[y1, x1] - I[y0, x1] - I[y1, x0] + I[y0, x0] > 0

    def free(box):
        if box[0] < 58 or box[2] > 1862 or box[1] < ytop or box[3] > ybot:
            return False
        if any(box[0] < q[2] and q[0] < box[2] and box[1] < q[3] and q[1] < box[3] for q in placed + blockers):
            return False
        if any(box[0] - r < lx < box[2] + r and box[1] - r < ly < box[3] + r and
               math.hypot(lx - min(max(lx, box[0]), box[2]), ly - min(max(ly, box[1]), box[3])) < r
               for lx, ly, r in lamp_px):
            return False
        return not hit(box)

    for text, ls in label_specs(b, stop, getattr(S, 'LABEL_SKIP', ())):
        cx = sum(l['x'] for l in ls) / len(ls); cy = sum(l['y'] for l in ls) / len(ls)
        n = math.hypot(cx, cy) or 1
        ux, uy = cx / n, -cy / n                         # outward, in screen space (y down)
        X, Y = view(cx, cy)
        w, h = S.label_size(text, stop)
        if not (-w < X < 1920 + w and 84 < Y < 960):
            continue
        best = None
        wide = 'HEARTH' in text and any(l['id'] in lit for l in ls)   # her own hearth always gets its name
        passes = [[(a, l) for a in range(-30, 191, 4) for l in range(-64, 65, 4)]]
        if wide:
            passes.append([(a, l) for a in range(-60, 321, 8) for l in range(-200, 201, 8)])
        for cands in passes:
            for a, lat in sorted(cands, key=lambda q: (q[0] if q[0] >= 0 else -2.5 * q[0]) + 1.4 * abs(q[1])):
                px, py = X + ux * a - uy * lat, Y + uy * a + ux * lat
                box = (px - w / 2 - 6, py - h / 2 - 7, px + w / 2 + 6, py + h / 2 + 7)
                if free(box):
                    best = (0, px, py, box); break
            if best:
                break
        home = (X - w / 2 - 6, Y - h / 2 - 7, X + w / 2 + 6, Y + h / 2 + 7)
        if not best and forbid is not None and (hit(home) or home[3] > ybot or home[1] < ytop):
            sgn = 1 if home[1] < ytop else -1          # pushed off the field: the nearest free spot above (below the header)
            for dy in range(0, 420, 4):
                for lat in sorted(range(-96, 97, 8), key=abs):
                    py0 = max(Y, ytop + h / 2 + 8) if sgn > 0 else min(Y, ybot - h / 2 - 8)
                    px, py = X + lat, py0 + sgn * dy
                    box = (px - w / 2 - 6, py - h / 2 - 7, px + w / 2 + 6, py + h / 2 + 7)
                    if free(box):
                        best = (0, px, py, box); break
                if best:
                    break
        if best:
            placed.append(best[3])
            yield text, best[1], best[2]


# ---------------------------------------------------------------- the board
def board_layers(S, st, view, tod, focus=None, wick_open=False, fmask=None):
    b = st.b
    stop = view.stop
    Lroad, Lglow, Lhalo, Llamp = D.layer(), D.layer(), D.layer(), D.layer()
    pos = {i: view(l['x'], l['y']) for i, l in b.lamps.items()}
    path, src = [], None
    if focus and focus in b.lamps and focus not in st.lit:
        r = st.path(focus)
        if r:
            path, src = r
    on = set(path)
    path_edges = {}
    if path:
        chain = [src] + path
        acc = 0.0
        for a, c in zip(chain, chain[1:]):
            path_edges[frozenset((a, c))] = (a, c, acc)
            acc += math.hypot(pos[c][0] - pos[a][0], pos[c][1] - pos[a][1])
    states = {i: st.state(i) for i in b.lamps}
    segs = []
    for a, c in b.edges:
        (ax, ay), (cx, cy) = pos[a], pos[c]
        if max(ax, cx) < -40 or min(ax, cx) > 1960 or max(ay, cy) < -40 or min(ay, cy) > 1120:
            continue
        key = frozenset((a, c))
        if key in path_edges:
            a, c, ph = path_edges[key]; kind = 'path'
        elif states[a] == 'lit' and states[c] == 'lit':
            kind, ph = 'lit', 0.0
        elif states[a] == 'lit' and states[c] == 'available' and not view.stop == 'valley':
            kind, ph = 'fuse', 0.0
        elif states[c] == 'lit' and states[a] == 'available' and not view.stop == 'valley':
            a, c = c, a; kind, ph = 'fuse', 0.0
        else:
            kind, ph = 'cold', 0.0
        (ax, ay), (cx, cy) = pos[a], pos[c]
        dx, dy = cx - ax, cy - ay
        L = math.hypot(dx, dy) or 1
        ra = lamp_r_toward(b.lamps[a]['kind'], stop, dx, dy) + (2 if stop != 'valley' else 1.5)
        rc = lamp_r_toward(b.lamps[c]['kind'], stop, dx, dy) + (2 if stop != 'valley' else 1.5)
        if L <= ra + rc + 1:
            continue
        segs.append(dict(a=(ax + dx / L * ra, ay + dy / L * ra), b=(cx - dx / L * rc, cy - dy / L * rc), kind=kind,
                         phase=-(ph + ra) if kind == 'path' else -ra,
                         fade=1.0 if kind != 'cold' else min(st.fade(a), st.fade(c))))
    order = {'cold': 0, 'fuse': 1, 'lit': 2, 'path': 3}
    S.roads(Lroad, Lglow, sorted(segs, key=lambda s: order[s['kind']]), stop)
    lamp_px = []
    # gate notches (N4): one per gated stretch, at its threshold (a blocked lamp touching a non-blocked one) + the focus
    door, seen = set(), set()
    for i in sorted((i for i in b.lamps if states[i] == 'blocked' and any(states[j] != 'blocked' for j in b.adj[i])),
                    key=lambda i: (st.steps.get(i, 99), i)):
        if b.lamps[i]['group'] not in seen:
            seen.add(b.lamps[i]['group']); door.add(i)
    ids = sorted(b.lamps, key=lambda i: (states[i] == 'lit', i == focus))
    for i in ids:
        l = b.lamps[i]
        x, y = pos[i]
        if not view.visible(l['x'], l['y']):
            continue
        dim = i in st.dim
        # her light reaches so far (brief §5): unlit lamps fade by road steps; gate notches near her or on the focus's road
        lit_or_path = states[i] == 'lit' or i in on or i == focus
        fade = 1.0 if lit_or_path else st.fade(i)
        near = lit_or_path or st.near(i)
        show_gate = (i in door and near) or i == focus
        chip = 1.0
        if fmask is not None:                   # r3: a chip fades with its lamp: the edge feather once more on top
            xi, yi = int(min(max(x, 0), 1919)), int(min(max(y, 0), 1079))
            chip = float(fmask[yi, xi])
        S.lamp(Llamp, Lhalo, x, y, l['kind'], states[i], stop, dim=dim, focus=(i == focus and not wick_open),
               onpath=(i in on), gate=l['gate'] if show_gate else 0, seed=seed(i), fade=fade, near=near, chip=chip)
        lamp_px.append((x, y, lamp_d(l['kind'], stop) / 2 + 5))
    lit_px = [pos[i] for i in st.lit]
    return dict(Lroad=Lroad, Lglow=Lglow, Lhalo=Lhalo, Llamp=Llamp, pos=pos, path=path, lamp_px=lamp_px, lit_px=lit_px)


def place_card(S, c, lx, ly, lr, below=None):
    h = S.card_height(c)
    w = 380
    x0 = lx + lr + 22 if lx < 1300 else lx - lr - 22 - w
    y0 = ly - h / 2
    y0 = min(max(y0, 100), 952 - h)
    return int(round(x0)), int(round(y0)), h


def card_for(b, st, i, stop):
    l = b.lamps[i]
    line, price = b.line_and_price(i)
    c = dict(name=b.name(i) or '', kind=l['kind'], place=b.group_name(l['group']), line=line, price=price,
             feeds=FEEDS, feeds_text=FEEDS_TEXT)
    s = st.state(i)
    if i in st.dim:
        c['state'] = DIM_REASON.get(RITE_TAGS[i][0], 'Sleeps')
    elif s == 'lit':
        c['state'] = 'Lit · lamps go out at a town’s lamp-post, by day'
    elif s == 'blocked':
        c['state'] = 'Opens at %d lit on this road · %d lit' % (l['gate'], st.lit_on(l['group']))
        c['state_color'] = hexc('#c9a46a')
    elif s == 'available':
        c['state'] = 'Light it: 1 lamp'; c['prompts'] = [('pad_a', 'Light')]
    else:
        r = st.path(i)
        n = len(r[0]) if r else 0
        c['state'] = '%d lamps away · you have %d' % (n, st.spare)
        c['prompts'] = [('pad_a', 'Light the path')]
    return c


# ---------------------------------------------------------------- frames
def frame(skin, which):
    S = importlib.import_module('skins.' + skin.lower())
    b = Board(); st = State(b)
    tod = 'night' if which == 'night' else 'day'
    pair = 'ford_night' if tod == 'night' else 'town_day'
    fo, nf = F.foot_rgb(pair)
    stop = 'valley' if which == 'valley' else 'road'
    if stop == 'valley':
        view = View((0.0, 0.0), STOPS['valley'] * 0.9, screen_c=(960.0, 522.0 + getattr(S, 'VALLEY_DY', 0)), stop='valley')
    else:
        view = View(CENTER, STOPS['road'], screen_c=(960.0, 522.0 - (120 if which == 'night' else 0)), stop='road')
    focus = {'day': 'sunderer.morning_in_the_steel', 'valley': 'sunderer.weight_of_the_oath', 'night': None}[which]
    if which == 'day':
        for cand in ('sunderer.morning_in_the_steel', 'sunderer.rooted_stance'):
            r = st.path(cand)
            if r and 2 <= len(r[0]) <= 3 and len(r[0]) <= st.spare:
                focus = cand; break
    if hasattr(S, 'begin'):                      # optional: a skin that needs the view (B's wheel)
        S.begin(view, tod)
    g = S.grade(nf, tod)
    fm0, fdist = field_mask()
    fm = fm0 * she_mask(pair)                     # r3: nothing of the board crosses her
    BL = board_layers(S, st, view, tod, focus, wick_open=(which == 'night'), fmask=fm)
    for k in ('Lroad', 'Lglow', 'Lhalo', 'Llamp'):
        BL[k] *= fm[..., None]
    rgb = S.pools(g, nf, BL['lit_px'], stop)
    rgb = g + (rgb - g) * fm0[..., None]          # the pools' light obeys the field too
    if hasattr(S, 'ornament'):                   # optional: the board's object, under the roads (B's wheel)
        rgb = S.ornament(rgb, view)
    if stop == 'valley':
        Lgd = D.layer()
        guides(Lgd, b, view)
        rgb = D.over(rgb, Lgd * fm[..., None])
    rgb = D.over(rgb, BL['Lroad'])
    rgb = S.road_glow(rgb, BL['Lglow'], stop)
    rgb = S.light(rgb, BL['Lhalo'])
    rgb = D.over(rgb, BL['Llamp'])
    # labels
    Llab = D.layer()
    blockers = [(560, 10, 1360, 96), (10, 10, 360, 84), (1440, 10, 1910, 84),
                (290, 830, 660, 1080), (1250, 860, 1600, 1080), (576, 985, 1344, 1080), (1640, 970, 1910, 1080)]
    if which == 'night':
        blockers.append((WICK_RECT[0] - 40, WICK_RECT[1] - 40, WICK_RECT[2] + 40, 1080))
    wick_card_xy = None
    card = None
    if focus:
        fl = b.lamps[focus]
        fx, fy = BL['pos'][focus]
        c = card_for(b, st, focus, stop)
        R = lamp_d(fl['kind'], stop) * 1.1 / 2
        x0, y0, h = place_card(S, c, fx, fy, R)
        if which == 'day':
            y0 += 10                             # r3: clear the "16" chip and the pill above it
        card = (c, x0, y0)
        blockers.append((x0 - 40, y0 - 40, x0 + 420, y0 + h + 40))
    for text, x, y in place_labels(b, view, S, stop, BL['lamp_px'], blockers, forbid=fdist < 40, ytop=132, ybot=900, lit=st.lit):
        S.label(Llab, x, y, text, stop)
    rgb = D.over(rgb, Llab * fm[..., None])
    # card, wick, header
    Lui, Lhalo2 = D.layer(), D.layer()
    wick_pos = None
    if which == 'night':
        wick_pos = S.wick(Lui, Lhalo2, wick_spec())
    if card:
        S.card(Lui, card[1], card[2], card[0])
    if wick_card_xy:
        S.card(Lui, wick_card_xy[1], wick_card_xy[2], wick_card_xy[0])
    lit_n = len(st.lit)
    hd = dict(count=SPARE, sub='%d lit · %d from levels, %d from the story' % (lit_n, FROM_LEVELS, FROM_STORY),
              post=None if tod == 'night' else 'At the Waystation’s lamp-post: lamps go out free',
              night='By night the board is read only' if tod == 'night' else None,
              coins=1, layout_name=TYPE, keys=[('pad_y', 'Light my way'), ('pad_lstick', 'Find'), ('pad_b', 'Close')])
    S.header(Lui, Lhalo2, hd)
    rgb = S.light(rgb, Lhalo2)
    rgb = D.over(rgb, Lui)
    # the foot, as the game draws it
    rgb = F.composite(rgb, fo, nf)
    rgb = F.paint_seat(rgb, SEAT_CHOSEN)         # the chosen seat shows Sunder, as the wick panel's title
    Lp, Lph = D.layer(), D.layer()
    if which == 'night':
        sx, sy = F.SEATS[SEAT_CHOSEN]
        S.seat_ring(Lp, Lph, (sx, sy, F.SEAT_R), WICK_RECT[3])
    if which == 'night':                         # r3: the wick's own prompts while it's open
        S.prompts(Lp, [[(['pad_a'], 'Unplan')], [(['pad_y'], 'Light my way')], [(['pad_b'], 'Back')]])
    else:                                        # r3: Find shows once (the header's)
        S.prompts(Lp, [[(['pad_lt', 'pad_rt'], 'Zoom'), (['pad_lb', 'pad_rb'], 'Next lamp')],
                       [(['pad_rstick'], 'Home'), (['pad_view'], 'Layouts')]], y0=1022)
    rgb = S.light(rgb, Lph)
    rgb = D.over(rgb, Lp)
    p = os.path.join(OUT, '%s_%s.png' % (skin.upper(), which))
    D.save(p, rgb)
    print('wrote', p, '| disconnected lit:', st.disconnected, '| focus:', focus,
          '| path:', st.path(focus)[0] if focus and st.state(focus) != 'blocked' and st.path(focus) else None)
    return p


_FM = []
FACE = (470.0, 868.0)                          # the Drowned Girl's face (A frames)
_SHE = {}


def she_mask(pair):
    """r3: her silhouette from the nofoot backdrop (cv2.grabCut, cached in c_work by c_work/she_mask.py): 1 outside,
    0 inside, a 10 px feather outward"""
    if pair not in _SHE:
        import cv2
        p = os.path.join(os.path.dirname(HERE), 'c_work', 'she_%s.npy' % pair)
        sil = np.load(p).astype(np.uint8)
        dist = cv2.distanceTransform(1 - sil, cv2.DIST_L2, 5)
        _SHE[pair] = D.smoothstep(0, 10, dist).astype(np.float32)
    return _SHE[pair]


def field_mask():
    """A's field (A1): the board fades to 0 over y 84->124 and 900->960, and a 32 px soft knockout around the foot's
    figures and seat panel (0 inside, smoothstep over 32 px). Returns (mask, distance from the foot in px)."""
    if _FM:
        return _FM[0]
    import cv2
    Y = np.arange(1080, dtype=np.float32)[:, None] + 0.5
    m = D.smoothstep(84, 124, Y) * (1 - D.smoothstep(900, 960, Y))
    fa = (F.alpha() > 0.02).astype(np.uint8)
    dist = cv2.distanceTransform(1 - fa, cv2.DIST_L2, 5)
    # r3: the knockout widens to 48 px at the Drowned Girl's face (a lamp ring floated 25 px in front of it)
    Yg, Xg = np.mgrid[0:1080, 0:1920].astype(np.float32)
    face = np.exp(-(((Xg - FACE[0]) / 70.0) ** 2 + ((Yg - FACE[1]) / 70.0) ** 2))
    K = 32 + 16 * np.clip(face * 1.6, 0, 1)
    m = (m * D.smoothstep(0, 1, dist / K)).astype(np.float32)
    _FM.append((m, dist))
    return _FM[0]


def guides(L, b, view):
    """the Valley's three faint rings about the board's center (A4): hearths, roads, Old Roads (median radii)"""
    cx, cy = view(0.0, 0.0)
    groups = {'hearth': [], 'road': [], 'oldroad': []}
    for l in b.lamps.values():
        k = 'oldroad' if b.groups[l['group']]['kind'] == 'oldroad' else l['region']
        if k in groups:
            groups[k].append(math.hypot(l['x'], l['y']))
    for k, ds in groups.items():
        r = float(np.median(ds)) * view.s
        P = D.Patch(cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2)
        P.fill(D.ring(D.circle(P, cx, cy, r), 1.0), hexc('#d8cfbd'), 0.18)
        P.stamp(L)


def wick_spec():
    return dict(rect=WICK_RECT, glyph='glyph/sword', name='SUNDER', rank='DAY RANK V', smoke=0.88,
                lay=dict(kx=140, braid=36, lx0=221, pitch=50, tx=371, row0=56, pitch_y=76, text_gap=31, right=24,
                         pad=24, sum_dy=26, kind_dx=-36),
                counts='5 of 12 lit · 8 planned',
                strands=[dict(kind='CALLING · LIGHT MY WAY', lamps=[('lit', 1), ('lit', 2), ('lit', 3)],
                              turn=dict(name='Splitting Stroke', line='Every 2nd swing is heavy and splits the ground; swings 15% slower.',
                                        state='lit', order=4,
                                        card_state='Lit · 4th in the plan · the ember lit it at day rank IV')),
                         dict(kind='SHAPE', lamps=[('lit', 5), ('planned', 6), ('cold', 0)],
                              turn=dict(name='Wide', line='One Turn a skill', state='cold', order=0, crossed=True)),
                         dict(kind='SCHOOL', lamps=[('planned', 7), ('planned', 8), ('cold', 0)],
                              turn=dict(name='Holy', line='One Turn a skill', state='cold', order=0, crossed=True))],
                sum='Damage 142 = 100 base · Hand ×1.15 · rites +12% · Turn: every 2nd swing heavy')


def wick_card():
    return dict(name='Splitting Stroke', kind='turn', place='SUNDER · CALLING · LIGHT MY WAY',
                line='Every 2nd swing is heavy and splits the ground; swings 15% slower.',
                feeds=[('glyph/slash', True)], feeds_text='Sunder’s Turn · one Turn a skill',
                state='Lit · 4th in the plan · the ember lit it at day rank IV',
                prompts=[('pad_a', 'Unplan'), ('pad_y', 'Light my way')])


def crops(skin):
    from PIL import Image
    a = Image.open(os.path.join(OUT, '%s_day.png' % skin)).crop((560, 200, 1360, 700))
    n = Image.open(os.path.join(OUT, '%s_night.png' % skin)).crop((560, 560, 1360, 1060))
    c = Image.new('RGB', (1600 + 8, 500), (0, 0, 0))
    c.paste(a, (0, 0)); c.paste(n, (808, 0))
    c.save(os.path.join(OUT, '%s_crops.png' % skin))


if __name__ == '__main__':
    skin = sys.argv[1] if len(sys.argv) > 1 else 'A'
    which = sys.argv[2] if len(sys.argv) > 2 else 'all'
    for w in (['day', 'night', 'valley'] if which == 'all' else [which]):
        frame(skin, w)
    if which == 'all' or (os.path.exists(os.path.join(OUT, '%s_day.png' % skin)) and os.path.exists(os.path.join(OUT, '%s_night.png' % skin))):
        crops(skin.upper())
