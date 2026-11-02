FEATHER = 48                             # the board fades to 0 over 48 px inside its window's edge (C1)
BAND_TOP = WICK_RECT[1]                  # night: the wick band's top (its hairline); the board's window ends here
PROMPT_HOLE = (1262, 953, 1648, 991)     # the game's prompt row (stand-in caps), cleared to the ground and redrawn (C6)
WICK_LAY = dict(kx=256, braid=40, lx0=350, pitch=64, tx=556, row0=50, pitch_y=58, text_gap=24, right=18, sum_cx=532)


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
            cross = sum(1 for (x, y, r) in discs if _rect_circle_hit(g, x, y, r) and not _inside((x0, y0, x0 + w, y0 + h), x, y, r - 0.01) or
                        (_rect_circle_hit(g, x, y, r) and not _rect_circle_hit((x0 + 6, y0 + 6, x0 + w - 6, y0 + h - 6), x, y, r) and False))
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
    wick_card = None
    if not night:
        focus = 'sunderer.morning_in_the_steel'
        path = st.path(focus)[0]
        ids = list(st.lit) + list(path) + [focus]
        xs = [b.lamps[i]['x'] for i in ids]; ys = [b.lamps[i]['y'] for i in ids]
        # C2: the build's bbox (lit + path + focus) centered in the window; zoom out only if a lit lamp would sit < 96 px in
        s = min(s, (wx1 - wx0 - 2 * 96 - 2 * rmax) / max(max(xs) - min(xs), 1),
                (wy1 - wy0 - 2 * 96 - 2 * rmax) / max(max(ys) - min(ys), 1))
        view = View(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2), s,
                    screen_c=((wx0 + wx1) / 2, (wy0 + wy1) / 2), stop=stop)
    else:
        focus = None
        c = FR.wick_card()
        c['prompts'] = [('key:Click', 'Unplan'), ('key:Space', 'Light my way')]
        h = S.card_height(c)
        cx0, cy0 = WICK_RECT[2] - 380, WICK_RECT[1] - 14 - h
        wick_card = (c, cx0, cy0, h)
        # C3 night: the lit cluster in the free band (below the header, above the wick band, left of the card), every
        # lit lamp >= 48 px inside it; zoom out continuously if needed (>= 0.62, shapes scale with it)
        fx0, fy0, fx1, fy1 = wx0 + 48, wy0 + 48, cx0 - 30, wy1 - 48
        lit = [b.lamps[i] for i in st.lit]
        xs = [l['x'] for l in lit]; ys = [l['y'] for l in lit]
        dx, dy = max(xs) - min(xs), max(ys) - min(ys)
        s = min(0.80, (fx1 - fx0) / (dx + 2 * rmax / 0.80), (fy1 - fy0) / (dy + 2 * rmax / 0.80))
        s = max(s, 0.62)
        VW.SHAPE_K[0] = s / 0.80
        view = View(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2), s,
                    screen_c=((fx0 + fx1) / 2, (fy0 + fy1) / 2), stop=stop)
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
    rgb = D.over(rgb, BL['Lroad'])
    rgb = S.road_glow(rgb, BL['Lglow'], stop)
    rgb = S.light(rgb, BL['Lhalo'])
    rgb = D.over(rgb, BL['Llamp'])
    # labels: never in the feather, and >= 40 px from the header, the cards and the wick band (N6)
    blockers = [(0, 0, wx0 + 40, 1080), (wx1 - 40, 0, 1920, 1080), (0, 0, 1920, wy0 + 40), (0, wy1 - 40, 1920, 1080)]
    card = None
    if focus:
        fx, fy = BL['pos'][focus]
        c = FR.card_for(b, st, focus, stop)
        c['prompts'] = [('key:Click', 'Light the path')]
        R = lamp_d(b.lamps[focus]['kind'], stop) * 1.1 / 2
        h = S.card_height(c)
        discs = [(x, y, r - 5) for x, y, r in BL['lamp_px']]
        prot = [(BL['pos'][i][0], BL['pos'][i][1], lamp_d(b.lamps[i]['kind'], stop) / 2 + 4)
                for i in list(st.lit) + list(BL['path']) + [focus]]
        chain = [st.path(focus)[1]] + list(BL['path'])     # the path's roads, sampled
        for a_, c_ in zip(chain, chain[1:]):
            (ax, ay), (cx_, cy_) = BL['pos'][a_], BL['pos'][c_]
            for t in np.linspace(0, 1, 12):
                prot.append((ax + (cx_ - ax) * t, ay + (cy_ - ay) * t, 3))
        x0, y0, side, shift, score = place_card_c(fx, fy, R + 5, h, discs, prot, win)
        card = (c, x0, y0, h)
        blockers.append((x0 - 40, y0 - 40, x0 + 420, y0 + h + 40))
        print('card:', side, 'shift', shift, 'overlap', score, 'at', (x0, y0, x0 + 380, y0 + h))
    if wick_card:
        _, x0, y0, h = wick_card
        blockers.append((x0 - 40, y0 - 40, x0 + 420, y0 + h + 40))
    Llab = D.layer()
    for text, x, y in FR.place_labels(b, view, S, stop, BL['lamp_px'], blockers, lit=st.lit):
        S.label(Llab, x, y, text, stop)
    rgb = D.over(rgb, Llab * fm[..., None])
    VW.SHAPE_K[0] = 1.0
    Lui, Lh2 = D.layer(), D.layer()
    if night:
        S.band_rule(Lui, BOARD[0], BOARD[2], BAND_TOP)
        ws = FR.wick_spec()
        ws['rect'] = WICK_RECT
        ws['boxless'] = True
        ws['lay'] = WICK_LAY
        wp = S.wick(Lui, Lh2, ws)
        sd = tab_discs()[0][0]                              # the skill's own seat art (the HUD's Sunder seat, 56 px)
        D.stamp(Lui, WICK_RECT[0] + 46 - sd.shape[1] // 2, WICK_RECT[1] + 50 - sd.shape[0] // 2, sd)
        tx, ty, tr = wp['turn0']
        S.focus_ring(Lui, Lh2, tx, ty - 2, tr + 2)          # the focus: the Turn (ring clears its flame crown)
        import text as T_                                   # its plan numeral back over the ring, with its dark halo
        T_.draw(Lui, tx + tr * 0.62 + 4, ty - tr * 0.62 - 1, '4', T_.font('alegreya-sans-800', 12), S.GOLD, 1.0,
                halo=(3, 1.0, S.DARK))
    if card:
        card_shadow(Lui, card[1], card[2], 380, card[3])
        S.card(Lui, card[1], card[2], card[0])
    if wick_card:
        card_shadow(Lui, wick_card[1], wick_card[2], 380, wick_card[3])
        S.card(Lui, wick_card[1], wick_card[2], wick_card[0])
    lit_n = len(st.lit)
    hd = dict(count=SPARE, sub='%d lit · %d from levels, %d from the story' % (lit_n, FROM_LEVELS, FROM_STORY),
              post=None if night else 'At the Waystation’s lamp-post: lamps go out free',
              night='By night the board is read only' if night else None,
              coins=1, layout_name=TYPE, keys=[('Space', 'Light my way'), ('Z', 'Open wide')])
    S.header(Lui, Lh2, hd, CONTENT)
    discs, empty = tab_discs()
    centers = S.tabs(Lui, Lh2, dict(discs=discs, chosen=0, y=TABS_Y, x0=CONTENT[0], x1=CONTENT[2], all_learned=empty))
    S.tab_ring(Lui, Lh2, centers[0], 28.0, stem_to=BAND_TOP + 1 if night else None)
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


