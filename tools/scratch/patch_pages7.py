p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a1a394643aabfb169\tools\uiforge\pages.py'
s = open(p, encoding='utf-8').read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b)


rep('''def column_divider_stone():''', '''def periodic(R, m, P, fn):
    """A surface field that repeats every P file px from m in from the edge both ways: what a
    nine-slice repeats is exactly one period of it, so its strips and middle tile with no seam
    and need no blending."""
    ss = R.ss
    base = fn(P * ss, P * ss)
    yy = (np.arange(R.h) - m * ss) % (P * ss)
    xx = (np.arange(R.w) - m * ss) % (P * ss)
    return base[yy[:, None], xx[None, :]]


def frame_sd(X, Y, x0, y0, x1, y1):
    return np.minimum(np.minimum(X - x0, x1 - X), np.minimum(Y - y0, y1 - Y))


def along_edge(X, Y, W, H):
    """A coordinate along whichever edge is nearest (for the wire's twist and the nails)."""
    return np.where(np.minimum(X, W - X) < np.minimum(Y, H - Y), Y, X)


def twist(R, across, along, th, pitch, base, height):
    s_ = along / pitch
    tw = np.zeros_like(across)
    for k0 in (0.0, 0.5):
        uu = ((across / th) - (((s_ + k0) % 1.0) - 0.5)) % 1.0 - 0.5
        tw = np.maximum(tw, np.sqrt(np.clip(1 - (uu / 0.5) ** 2, 0, 1)))
    m = np.clip((th / 2 - np.abs(across)) * R.ss + 0.5, 0, 1)
    edge = np.sqrt(np.clip(1 - (across / (th / 2)) ** 2, 0, 1))
    return base + (tw * 0.55 + edge * 0.45) * height, m


def hero_plate(ss=2, samples=160):
    """The heavy frame round the figure on a page (frames/hero_plate.png, 512x512, 256x256
    shown, slice 56 each side, Tile, Out 12; the middle clear). Strap iron, chamfered and
    planished, the binders' twisted wire laid in a channel along it and nailed either side;
    at each corner a forged block with a binders' coin, its ember asleep, and a lamp-iron
    bracket's scrolls running out along both edges; inside, a bead and a shadow, so the
    figure stands back in it."""
    W = H = 512
    o, m = 24, 112                  # the overhang past the control, the slice margin (file px)
    P = W - 2 * m
    R = RL.Relief(W, H, ss)
    X, Y = R.xx / ss, R.yy / ss
    sd = frame_sd(X, Y, o, o, W - o, H - o)
    strap_w = 36.0
    on = (sd >= 0) & (sd < strap_w + 4)
    # The strap: outer chamfer, a crowned face, the channel, an inner chamfer down to a bead.
    t_out = np.clip(sd / 5.0, 0, 1)
    t_in = np.clip((strap_w - sd) / 5.0, 0, 1)
    face = 10.0 + 1.2 * np.sin(np.clip(sd / strap_w, 0, 1) * math.pi)
    h = np.where(sd < strap_w, np.minimum(t_out, t_in) * face, 0)
    bead = np.exp(-((sd - (strap_w + 1.5)) / 1.6) ** 2) * 3.0
    h = np.maximum(h, bead * (sd > strap_w - 2))
    across = sd - strap_w / 2
    groove = np.clip((4.0 - np.abs(across)) * ss * 0.5 + 0.5, 0, 1) * (sd > 0) * (sd < strap_w)
    h = h - groove * 2.4
    along = along_edge(X, Y, W, H)
    wh, wm = twist(R, across, along - m, 6.0, P / 30.0, 8.6, 3.0)
    h = np.where((wm > 0.5) & on, np.maximum(h, wh), h)
    shape = h.copy()
    # Nails either side of the wire, one every 48 px along (six to a repeat).
    nails = np.zeros_like(X)
    for side in (7.0, strap_w - 7.0):
        u = ((along - m) % 48.0) - 24.0
        dd = np.hypot(u, sd - side)
        dome = np.sqrt(np.clip(1 - (dd / 2.8) ** 2, 0, 1)) * 2.2 + face
        nm = (dd < 2.8) & on
        h = np.where(nm, np.maximum(h, dome), h)
        shape = np.where(nm, np.maximum(shape, dome), shape)
        nails = np.maximum(nails, nm.astype(np.float32))
    # Planishing and dents, periodic over the repeat.
    facet = periodic(R, m, P, lambda a, b: F.facets(a, b, cell=20.0 * ss, tilt=0.02, seed=111, soften=1.5 * ss)) / ss
    dents = periodic(R, m, P, lambda a, b: F.worley_dents(a, b, cell=7.0 * ss, depth=0.26 * ss, seed=112)) / ss
    plain = on & (wm < 0.5) & (nails < 0.5)
    h = h + (facet + dents) * plain
    # The corners: a forged block over the strap, the coin on it, the bracket's scrolls.
    import chrome as CH
    blocks = np.zeros_like(X)
    coins = np.zeros_like(X)
    holes = np.zeros_like(X)
    arms = np.zeros_like(X)
    glow = np.zeros((R.h, R.w, 3), np.float32)
    for cx, cy, sx, sy in ((o + 26, o + 26, 1, 1), (W - o - 26, o + 26, -1, 1), (o + 26, H - o - 26, 1, -1),
                           (W - o - 26, H - o - 26, -1, -1)):
        for pts in CH.bracket_scrolls(cx, cy, sx, sy, 36, 9.0, 0):
            bh, bm = RL.bar(R, pts, 9.0, 3.6)
            bh = bh + 12.0
            h = np.where(bm > 0.5, np.maximum(h, bh), h)
            shape = np.where(bm > 0.5, np.maximum(shape, bh), shape)
            arms = np.maximum(arms, bm)
        bsd = np.minimum(29.0 - np.abs(X - cx), 29.0 - np.abs(Y - cy))
        bsd = np.minimum(bsd, (40.0 - (np.abs(X - cx) + np.abs(Y - cy))) / math.sqrt(2))
        blk = bsd > 0
        bprof = 12.5 + np.clip(bsd / 4.0, 0, 1) * 2.0
        h = np.where(blk, np.maximum(h, bprof), h)
        shape = np.where(blk, np.maximum(shape, bprof), shape)
        blocks = np.maximum(blocks, blk.astype(np.float32))
        chh, cm, hm = RL.coin(R, cx, cy, 30.0, 14.5, hole=0.36)
        h = np.where(cm > 0.5, np.maximum(h, chh), h)
        shape = np.where(cm > 0.5, np.maximum(shape, chh), shape)
        coins = np.maximum(coins, cm)
        holes = np.maximum(holes, hm)
        glow += ember_light(R, hm, cx, cy, 30.0, seed=113 + int(cx))
    bd = RL.hammered(R, cell=5.0, depth=0.22, seed=117) / ss
    h = h + bd * (blocks > 0.5) * (coins < 0.5)
    cover = np.clip(sd * ss + 0.5, 0, 1) * (sd < strap_w + 4)
    cover = np.maximum.reduce([cover, arms, (blocks > 0.5).astype(np.float32), coins])
    R.height = (h * ss * (cover > 0.02)).astype(np.float32)
    R.shape_height = (shape * ss * (cover > 0.02)).astype(np.float32)
    R.alpha = cover.astype(np.float32)
    R.mat[:] = RL.IDS["iron"]
    R.mat[(wm > 0.5) & on & (blocks < 0.5)] = RL.IDS["gold"]
    R.mat[coins > 0.5] = RL.IDS["gold_dim"]
    R.mat[holes > 0.5] = RL.IDS["ember"]
    R.tint = (np.ones((R.h, R.w, 3), np.float32) * np.array([1.0, 0.96, 0.9], np.float32)).astype(np.float32)
    R.emit = glow
    img = R.render("page_hero_plate", samples=samples, wear=1.3, grime=0.9, seed=118)
    small = R.file_size(img)
    # The shadow inside: the figure stands back in the frame.
    sdf = frame_sd(*np.meshgrid(np.arange(W) + 0.5, np.arange(H) + 0.5), o, o, W - o, H - o)
    sh = np.clip(1 - (sdf - (strap_w + 3)) / 26.0, 0, 1) ** 1.8 * 0.6 * (sdf > strap_w + 1)
    a = small[..., 3]
    out_a = a + sh * (1 - a)
    rgb = small[..., :3] * a[..., None] / np.maximum(out_a[..., None], 1e-4)
    return np.dstack([rgb, out_a]).astype(np.float32)


def card_light(ss=3, samples=160):
    """A lighter frame for cards and tooltips (frames/card_light.png, 320x320, 160x160 shown,
    slice 20 each side, Tile): a dark vellum, a little translucent, blind-tooled with a fine
    line; round its edge a slim bead of iron, and at the corners small forged caps nailed
    through. Quiet behind words."""
    W = H = 320
    m = 40
    P = W - 2 * m
    R = RL.Relief(W, H, ss)
    X, Y = R.xx / ss, R.yy / ss
    sd = frame_sd(X, Y, 0, 0, W, H)
    bead_w = 9.0
    bead = np.where(sd < bead_w, np.sqrt(np.clip(1 - ((sd - bead_w / 2) / (bead_w / 2)) ** 2, 0, 1)) * 5.0 + 1.0, 0)
    fibre = periodic(R, m, P, lambda a, b: F.fbm(a, b, scale=1.4 * ss * K, octaves=2, seed=121)) / ss
    cockle = periodic(R, m, P, lambda a, b: F.fbm(a, b, scale=40 * ss * K, octaves=3, seed=122)) / ss
    vellum = sd >= bead_w
    h = np.where(vellum, 1.2 + fibre * 0.12 + cockle * 0.5, bead)
    tool = np.clip((0.8 - np.abs(sd - 17.0)) * ss * 0.5 + 0.5, 0, 1)
    h = h - tool * 0.6
    shape = np.where(vellum, 1.2 - tool * 0.6, bead)
    dents = periodic(R, m, P, lambda a, b: F.worley_dents(a, b, cell=4.0 * ss, depth=0.18 * ss, seed=123)) / ss
    h = h + dents * (~vellum)
    caps = np.zeros_like(X)
    for cx, cy, sx, sy in ((0, 0, 1, 1), (W, 0, -1, 1), (0, H, 1, -1), (W, H, -1, -1)):
        u, v = (X - cx) * sx, (Y - cy) * sy
        cap = ((u < 30) & (v < 13)) | ((u < 13) & (v < 30))
        csd = np.minimum(np.where(u < 13, 30 - v, 13 - v), np.where(v < 13, 30 - u, 13 - u))
        cprof = 6.5 + np.clip(csd / 2.5, 0, 1) * 1.6
        h = np.where(cap, np.maximum(h, cprof), h)
        shape = np.where(cap, np.maximum(shape, cprof), shape)
        caps = np.maximum(caps, cap.astype(np.float32))
        dd = np.hypot(u - 6.5, v - 6.5)
        nail = dd < 2.6
        h = np.where(nail, np.maximum(h, 8.3 + np.sqrt(np.clip(1 - (dd / 2.6) ** 2, 0, 1)) * 1.6), h)
    R.height = (h * ss).astype(np.float32)
    R.shape_height = (shape * ss).astype(np.float32)
    R.alpha = np.ones_like(X, np.float32)
    R.mat[:] = RL.IDS["iron"]
    R.mat[vellum & (caps < 0.5)] = RL.IDS["paper"]
    cloud = periodic(R, m, P, lambda a, b: F.fbm(a, b, scale=60 * ss * K, octaves=4, seed=124)) * 0.5 + 0.5
    vt = (0.115 + 0.05 * cloud) * (1 - tool * 0.3)
    tint = np.where(vellum[..., None] & (caps[..., None] < 0.5), vt[..., None] * np.array([1.0, 0.86, 0.7], np.float32), 1.0)
    R.tint = tint.astype(np.float32)
    img = R.render("page_card_light", samples=samples, wear=1.2, grime=0.6, seed=125)
    small = R.file_size(img)
    # The vellum a little translucent, so the world behind is felt and not seen.
    sdf = frame_sd(*np.meshgrid(np.arange(W) + 0.5, np.arange(H) + 0.5), 0, 0, W, H)
    small[..., 3] = np.where(sdf > bead_w + 1, 0.93, small[..., 3])
    return small


def column_divider_stone():''')
rep('''    "section_mark": ("ornaments/section_mark.png", section_mark),''', '''    "section_mark": ("ornaments/section_mark.png", section_mark),
    "hero_plate": ("frames/hero_plate.png", hero_plate),
    "card_light": ("frames/card_light.png", card_light),''')
open(p, 'w', encoding='utf-8').write(s)
print('ok')
