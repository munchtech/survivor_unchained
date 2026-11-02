def _cubic(p0, p1, p2, p3, n=60):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2, p3 = (np.asarray(p, np.float32) for p in (p0, p1, p2, p3))
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3


def _poly_dist(P, pts):
    """distance to a polyline, and the index of the nearest segment"""
    dmin = np.full(P.X.shape, 1e9, np.float32)
    idx = np.zeros(P.X.shape, np.int32)
    for i in range(len(pts) - 1):
        ds, t, _ = D.segment(P, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])
        m = ds < dmin
        dmin = np.where(m, ds, dmin); idx = np.where(m, i, idx)
    return dmin, idx


STRAND_GOLD, STRAND_PLAN, STRAND_SILVER = hexc('#f2c06b'), hexc('#e2b066'), hexc('#a7b1c2')


def braid(L, Lhalo, kx, ky, length, rows_y, x_end, kinds):
    """the three-ply braid: three 2 px strands plait out of the knot for `length` px (each outer strand crosses OVER the
    middle: lateral = sin u, depth = cos 2u), then part into the three rows (cubics to (x_end, ry)).
    kinds[r]: 'lit' | 'planned' | 'cold' for the strand that feeds row r."""
    A_, lam = 3.4, 13.0                       # lateral amplitude, wavelength (px)
    x0b, x1b = kx + 2.0, kx + length
    n_wave = max(1.0, round((x1b - x0b) / lam * 2) / 2)   # end on a half wave: offsets 0, +-0.87 A
    lam = (x1b - x0b) / n_wave
    phis = [0.0, 2 * np.pi / 3, 4 * np.pi / 3]
    uend = 2 * np.pi * n_wave
    ends = [np.sin(uend + ph) for ph in phis]
    order = np.argsort(ends)                  # most negative (highest on screen) first -> row 0
    P = Patch(kx - 6, min(rows_y) - 8, x_end + 4, max(rows_y) + 8)
    cols, dists, depths, alphas = [], [], [], []
    for r in range(3):
        ph = phis[order[r]]
        xs = np.linspace(x0b, x1b, 90)
        u = 2 * np.pi * (xs - x0b) / lam
        ys = ky + A_ * np.sin(u + ph) * np.clip((xs - x0b) / 5.0, 0.35, 1)        # they leave the knot together
        zs = np.cos(2 * (u + ph))
        bez = _cubic((x1b, ys[-1]), (x1b + (x_end - x1b) * 0.45, ys[-1]), (x_end - (x_end - x1b) * 0.55, rows_y[r]),
                     (x_end, rows_y[r]), 40)
        pts = np.concatenate([np.stack([xs, ys], 1), bez[1:]], 0)
        z = np.concatenate([zs, np.full(len(bez) - 1, -1.2)])
        d, idx = _poly_dist(P, pts)
        dists.append(d); depths.append(z[np.clip(idx, 0, len(z) - 1)].astype(np.float32))
        cols.append(STRAND_GOLD if kinds[r] == 'lit' else STRAND_PLAN if kinds[r] == 'planned' else STRAND_SILVER)
        alphas.append(0.95 if kinds[r] != 'cold' else 0.75)
    rank = np.argsort(np.stack(depths), 0)    # back to front, per sample
    inbraid = P.X < x1b + 1
    for lev in range(3):
        k = rank[lev]
        d = np.choose(k, dists)
        zz = np.choose(k, depths)
        col = np.stack([np.choose(k, [c[ch] * np.ones_like(d) for c in cols]) for ch in range(3)], -1)
        ka = np.choose(k, [np.full(d.shape, a, np.float32) for a in alphas])
        # the dark seam where one strand passes over another (inside the plait only)
        P.fill(np.where(inbraid, d - 1.75, 9.0), DARK, 0.85)
        shade = np.where(inbraid, 0.58 + 0.42 * (np.clip(zz, -1, 1) + 1) / 2, 1.0)[..., None]
        hi = (np.clip(1.0 - d, 0, 1) * 0.22 * inbraid)[..., None]
        c = P.cov(d - 1.0) * ka
        rgb = np.clip(col * shade + hi, 0, 1)
        P.a = np.concatenate([rgb * c[..., None], c[..., None]], -1) + P.a * (1 - c[..., None])
    P.fill(D.circle(P, kx, ky, 3.2), LIT_RIM, 1.0)
    P.stamp(L); P.stamp(Lhalo, 0.22, 'add')


def wick(L, Lhalo, w):
    """w: rect (x0, y0, x1, y1), glyph, name, rank, counts, strands [dict(kind, lamps [state, order], turn
    (name, line, state, order, crossed))], sum; optional: boxless (no glass, no inner rule), lay (layout offsets).
    Returns {'turn0': (x, y, r), ...} lamp positions for the card."""
    x0, y0, x1, y1 = w['rect']
    boxless = w.get('boxless', False)
    lay = dict(kx=134, braid=38, lx0=215, pitch=50, tx=383, row0=54, pitch_y=56, text_gap=24, right=12, sum_cx=None)
    lay.update(w.get('lay', {}))
    if not boxless:
        glass_panel(L, x0, y0, x1, y1)
    # left block
    ax, ay = x0 + 46, y0 + 50
    P = Patch(ax - 31, ay - 31, ax + 31, ay + 31)
    d = D.circle(P, ax, ay, 28)
    P.fill(d, D.radial(P, ax - 6, ay - 8, 34, [(0, hexc('#1d2026')), (1, hexc('#08090c'))]))
    P.fill(D.ring(d + 0.75, 1.5), RIM_GOLD, 0.85)
    P.fill(D.ring(D.circle(P, ax, ay, 25.5), 0.8), hexc('#6b5532'), 0.6)
    P.stamp(L)
    stamp_glyph(L, w['glyph'], ax, ay, 40, hexc('#d6c4a0'), 0.95, gain=1.1)
    T.draw(L, x0 + 18, y0 + 118, w['name'], T.font('cinzel-700', 22), INK, 1.0, track=0.06)
    T.draw(L, x0 + 18, y0 + 140, w['rank'], T.font('alegreya-sans-700', 13), GOLD, 1.0, track=0.12)
    T.draw(L, x0 + 18, y0 + 160, w['counts'], T.font('alegreya-sans-400', 14), INK_DIM, 1.0)
    rows_y = [y0 + lay['row0'] + i * lay['pitch_y'] for i in range(3)]
    kx, ky = x0 + lay['kx'], rows_y[1]
    lx = [x0 + lay['lx0'] + i * lay['pitch'] for i in range(3)]
    tx = x0 + lay['tx']
    pos = {}
    kinds = []
    for r in range(3):
        s0 = w['strands'][r]['lamps'][0][0]
        kinds.append('lit' if s0 == 'lit' else 'planned' if s0 == 'planned' else 'cold')
    braid(L, Lhalo, kx, ky, lay['braid'], rows_y, lx[0] - 13, kinds)
    fl = T.font('alegreya-400', 15)
    txt_x = tx + lay['text_gap']
    txt_w = x1 - lay['right'] - txt_x
    for r, ry in enumerate(rows_y):
        st = w['strands'][r]
        T.draw(L, lx[0] - 11, ry - 19, st['kind'], T.font('alegreya-sans-700', 13), INK_DIM, 0.95, track=0.10)
        xs = lx + [tx]
        states = [s for s, _ in st['lamps']] + [st['turn']['state']]
        orders = [o for _, o in st['lamps']] + [st['turn']['order']]
        segs = []
        for i in range(3):
            a, b = xs[i], xs[i + 1]
            ra, rb = 11, (17 if i == 2 else 11)
            k = 'lit' if states[i] == 'lit' and states[i + 1] == 'lit' else \
                'path' if states[i] in ('lit', 'planned') and states[i + 1] == 'planned' else 'cold'
            segs.append(dict(a=(a + ra + 2, ry), b=(b - rb - 2, ry), kind=k, phase=0.0))
        Lg = D.layer()
        roads(L, Lg, segs, 'road')
        Lhalo += Lg * 0.6
        for i in range(4):
            s, o = states[i], orders[i]
            turn = i == 3
            x = xs[i]
            if turn:
                wick_turn(L, Lhalo, x, ry, s, st['turn'].get('crossed', False))
                pos['turn%d' % r] = (x, ry, 17)
            else:
                wick_lamp(L, Lhalo, x, ry, s)
                pos['lamp%d_%d' % (r, i)] = (x, ry, 11)
            if o:
                rr = 17 if turn else 11
                T.draw(L, x + rr * 0.62 + 4, ry - rr * 0.62 - 1, str(o), T.font('alegreya-sans-800', 12), GOLD, 1.0,
                       halo=(3, 0.8, DARK))
        tn = st['turn']
        crossed = tn.get('crossed')
        T.draw(L, txt_x, ry - 2, tn['name'], T.font('alegreya-700', 18), INK if not crossed else INK_DIM, 1.0)
        for j, ln in enumerate(T.wrap(tn['line'], fl, txt_w)[:2]):
            T.draw(L, txt_x, ry + 16 + j * 16, ln, fl, INK_BODY if not crossed else INK_DIM, 0.9)
    if not boxless:
        rule(L, x0 + 16, x1 - 16, y1 - 32, 0.22)
    scx = (x0 + x1) / 2 if lay['sum_cx'] is None else x0 + lay['sum_cx']
    T.draw(L, scx, y1 - 12, w['sum'], T.font('alegreya-sans-500', 14), INK_BODY, 0.95, align='center')
    return pos


