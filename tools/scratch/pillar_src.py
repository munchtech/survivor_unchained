def rect_sd(X, Y, x0, y0, x1, y1, ch_top=0.0, ch_bot=0.0):
    """Signed distance inside a rectangle (file px) with its top and bottom corners cut."""
    d = np.minimum(np.minimum(X - x0, x1 - X), np.minimum(Y - y0, y1 - Y))
    if ch_top:
        d = np.minimum(d, ((X - x0) + (Y - y0) - ch_top) / math.sqrt(2))
        d = np.minimum(d, ((x1 - X) + (Y - y0) - ch_top) / math.sqrt(2))
    if ch_bot:
        d = np.minimum(d, ((X - x0) + (y1 - Y) - ch_bot) / math.sqrt(2))
        d = np.minimum(d, ((x1 - X) + (y1 - Y) - ch_bot) / math.sqrt(2))
    return d


def straight_rope(R, pts_sd, th, pitch, base, height):
    """The binders' twist along any line given its signed distance field (0 on the line) and a
    coordinate along it: here the caller passes (across, along)."""
    across, along = pts_sd
    s = along / pitch
    hgt = np.zeros_like(across)
    for k in (0.0, 0.5):
        u = ((across / th) - (((s + k) % 1.0) - 0.5)) % 1.0 - 0.5
        hgt = np.maximum(hgt, np.sqrt(np.clip(1 - (u / 0.5) ** 2, 0, 1)))
    m = np.clip((th / 2 - np.abs(across)) * R.ss + 0.5, 0, 1)
    edge = np.sqrt(np.clip(1 - (across / (th / 2)) ** 2, 0, 1))
    return base + (hgt * 0.55 + edge * 0.45) * height, m


def pillar(ss=2, samples=128):
    """The attribute's stele (frames/pillar.png, 424x728, drawn one to one over a 188x340
    control, reaching 12 past it): a narrow standing plate of planished iron, its strap and
    the binders' wire round it; at its head a round seat (a raised collar) for the 120 px
    medallion 10-130 px down; its shaft plain for the name and words; its foot a plinth
    nailed with two of the binders' coins; lamp-iron brackets at its shoulders whose arms
    run along the top and down the sides and curl outward past it. Neutral iron: the code
    draws an ember hairline when points wait."""
    W, H = 424, 728
    o = 24
    S = ss
    R = RL.Relief(W, H, ss)
    X, Y = R.xx / S, R.yy / S
    x0, y0, x1, y1 = o, o, W - o, H - o
    sd = rect_sd(X, Y, x0, y0, x1, y1, ch_top=22, ch_bot=10)
    cover = np.clip(sd * S + 0.5, 0, 1)
    top = 8.0
    bw = 22.0
    # The strap round its edge: chamfered out, a step down to the face inside.
    def edge(d, ch, sh):
        lo = np.clip(d / ch, 0, 1) * 0.8
        hi = 0.8 + 0.2 * np.sqrt(np.clip(1 - (1 - np.clip((d - ch) / sh, 0, 1)) ** 2, 0, 1))
        return np.where(d < ch, lo, hi) * (d > 0)
    strap = edge(sd, 3.5, 1.5) * np.where(sd < bw, 1.0, 0.0) * top
    inner = sd - bw
    face = 4.0 + 0.6 * np.clip(inner / 30, 0, 1)
    step = np.clip(inner / 2.0, 0, 1)
    h = np.where(sd < bw, strap, top * (1 - step) + face * step)
    h = np.where(sd < bw - 0.5, h, np.minimum(h, np.maximum(face, top * (1 - step))))
    # The wire along the strap's middle.
    across = sd - bw / 2
    along = np.where(np.abs(X - W / 2) * (y1 - y0) > np.abs(Y - H / 2) * (x1 - x0), Y, X)
    wh, wm = straight_rope(R, (across, along), 5.2, 8.0, top - 1.0, 2.6)
    groove = np.clip((3.2 - np.abs(across)) * S / 2, 0, 1) * (sd > 0)
    h = h - groove * 1.2
    h = np.where(wm > 0.5, np.maximum(h, wh), h)
    shape = h.copy()
    # The seat at the head: a raised collar round the medallion's place.
    cx, cy = W / 2, o + 20 + 120
    rr = np.hypot(X - cx, Y - cy)
    r_in, r_out = 121.0, 140.0
    collar = band_profile(rr, r_out, r_in, top + 2.0, outer_ch=4.0, inner_ch=2.5, shoulder=1.5)
    collar = collar + np.sin(np.clip((rr - r_in) / (r_out - r_in), 0, 1) * math.pi) * 1.2 * (collar > 0)
    ch_m = (rr > r_in) & (rr < r_out)
    h = np.where(ch_m, np.maximum(h, collar), h)
    # The seat's floor inside the collar: sunk, dark (the medallion covers most of it).
    seat = rr <= r_in
    h = np.where(seat, 2.5, h)
    rw, rm = RL.rope(R, cx, cy, (r_in + r_out) / 2, 5.0, 7.0, 2.6)
    cgroove = np.clip((3.0 - np.abs(rr - (r_in + r_out) / 2)) * S / 2, 0, 1)
    h = np.where(ch_m, h - cgroove * 1.2, h)
    h = np.where(rm > 0.5, np.maximum(h, top + 0.6 + rw / S), h)
    shape = np.where(ch_m | seat, h, shape)
    # The foot: a plinth across the shaft, nailed with two coins.
    py0 = y1 - 70
    plinth_sd = np.minimum(Y - py0, sd)
    plinth = edge(plinth_sd, 3.0, 1.2) * (top + 2.5)
    pm = (Y > py0) & (sd > 0)
    h = np.where(pm, np.maximum(h, plinth), h)
    shape = np.where(pm, np.maximum(shape, plinth), shape)
    coins = np.zeros_like(X)
    holes = np.zeros_like(X)
    glow = np.zeros_like(X)
    for cxp in (x0 + 34, x1 - 34):
        cyp = y1 - 34
        chh, cm, hm = RL.coin(R, cxp, cyp, 30.0, top + 2.5, hole=0.36)
        h = np.where(cm > 0.5, np.maximum(h, chh), h)
        shape = np.where(cm > 0.5, np.maximum(shape, chh), shape)
        coins = np.maximum(coins, cm)
        holes = np.maximum(holes, hm)
        dh = np.hypot(X - cxp, Y - cyp) / (30 * 0.36 / 2)
        glow = np.maximum(glow, hm * np.exp(-dh ** 2 * 1.6))
    # The brackets at the shoulders: a coin at each top corner, arms along the top and down the
    # side, curling back outward past the stele.
    import chrome as CH
    arms = np.zeros_like(X)
    for cxp, sx in ((x0 + 10, 1), (x1 - 10, -1)):
        cyp = y0 + 10
        chh, cm, hm = RL.coin(R, cxp, cyp, 40.0, top + 1.0, hole=0.34)
        for pts in CH.bracket_scrolls(cxp, cyp, sx, 1, 54, 10, 0):
            bh, bm = RL.bar(R, pts, 12.0, 4.0)
            bh = bh + top + 0.5
            h = np.where(bm > 0.5, np.maximum(h, bh), h)
            shape = np.where(bm > 0.5, np.maximum(shape, bh), shape)
            arms = np.maximum(arms, bm)
        h = np.where(cm > 0.5, np.maximum(h, chh), h)
        shape = np.where(cm > 0.5, np.maximum(shape, chh), shape)
        coins = np.maximum(coins, cm)
        holes = np.maximum(holes, hm)
        dh = np.hypot(X - cxp, Y - cyp) / (40 * 0.34 / 2)
        glow = np.maximum(glow, hm * np.exp(-dh ** 2 * 1.6))
    facet = F.facets(R.h, R.w, cell=18.0 * S, tilt=0.022, seed=51, soften=1.5 * S) / S
    dents = RL.hammered(R, cell=7.0, depth=0.3, seed=52) / S
    plain = (wm < 0.5) & (rm < 0.5) & (coins < 0.5) & (arms < 0.5)
    h = h + (facet + dents) * plain
    cover = np.maximum(cover, np.maximum(coins, arms))
    R.height = (h * S * cover).astype(np.float32)
    R.shape_height = (shape * S * cover).astype(np.float32)
    R.alpha = cover
    R.mat[:] = RL.IDS["iron"]
    R.mat[(wm > 0.5) | (rm > 0.5)] = RL.IDS["gold"]
    R.mat[holes > 0.5] = RL.IDS["ember"]
    # The face a little darker than the strap, darker still in the seat.
    face_t = np.where((sd > bw + 2) & ~ch_m & ~pm, 0.72, 1.0)
    face_t = np.where(seat, 0.45, face_t)
    R.tint = (face_t[..., None] * np.ones(3, np.float32)).astype(np.float32)
    n = F.fbm(R.h, R.w, scale=R.w / 10, octaves=3, seed=53) * 0.5 + 0.5
    R.emit = ((glow * (0.5 + 0.6 * n))[..., None] * (F.hexc("#ff6a1a") * 0.9 + F.hexc("#8a1c04") * 0.5)).astype(np.float32)
    img = R.render("pillar", samples=samples, wear=1.2, grime=0.9, seed=54)
    img = paint(img, R, "pillar", "a tall narrow standing plate of " + IRON + ", a thin twisted gold wire inlaid round its "
                "edge, a round raised collar at its head, a plinth at its foot with two square iron coins, curled iron "
                "brackets at its top corners, its face plain and flat", 0.26)
    return R.file_size(img)


