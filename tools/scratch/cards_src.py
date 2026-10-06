def iron_card(name, W, H, o, margins, border=22.0, chamfer=10.0, crest=0.0, coin=34.0, brackets=0.0,
              oxblood=False, prompt="", denoise=0.24, ss=2, samples=128):
    """A forged card or plate as a nine-slice that repeats (UiArt Tile): a strap round it with
    the binders' wire, a binders' coin at each corner (the ember asleep in its hole), lamp-iron
    brackets at its top corners if `brackets` (their arms' length), a crest plate lapped over
    its head `crest` px deep if asked (the code tints it), a plain face. Everything that is
    one-off sits in the corners (inside `margins`, file px); the strips between repeat."""
    S = ss
    R = RL.Relief(W, H, ss)
    X, Y = R.xx / S, R.yy / S
    x0, y0, x1, y1 = o, o, W - o, H - o
    sd = rect_sd(X, Y, x0, y0, x1, y1, ch_top=chamfer, ch_bot=chamfer)
    cover = np.clip(sd * S + 0.5, 0, 1)
    top = 8.0

    def edge(d, ch, sh):
        lo = np.clip(d / ch, 0, 1) * 0.8
        hi = 0.8 + 0.2 * np.sqrt(np.clip(1 - (1 - np.clip((d - ch) / sh, 0, 1)) ** 2, 0, 1))
        return np.where(d < ch, lo, hi) * (d > 0)
    inner = sd - border
    step = np.clip(inner / 2.0, 0, 1)
    face = 4.2
    h = np.where(sd < border, edge(sd, 3.5, 1.5) * top, top * (1 - step) + face * step)
    across = sd - border / 2
    along = np.where(np.abs(X - W / 2) * (y1 - y0) > np.abs(Y - H / 2) * (x1 - x0), Y, X)
    wh, wm = straight_rope(R, (across, along), 5.0, 8.0, top - 1.0, 2.5)
    groove = np.clip((3.0 - np.abs(across)) * S / 2, 0, 1) * (sd > 0)
    h = h - groove * 1.2
    h = np.where(wm > 0.5, np.maximum(h, wh), h)
    shape = h.copy()
    crest_m = np.zeros_like(X, bool)
    if crest:
        # The crest: a plate lapped over the card's head, its lower edge rounded over the face.
        cy1 = y0 + crest
        csd = np.minimum(np.minimum(X - (x0 + border - 2), (x1 - border + 2) - X), cy1 - Y)
        crest_m = (csd > 0) & (Y > y0 + border - 2)
        prof = face + 1.0 + 2.6 * np.sqrt(np.clip(csd / 2.5, 0, 1))
        h = np.where(crest_m, np.maximum(h, prof), h)
        shape = np.where(crest_m, np.maximum(shape, prof), shape)
        # Rivets along its foot, at the corners only (the middle repeats).
        for rx in (x0 + border + 16, x1 - border - 16):
            dd = np.hypot(X - rx, Y - (cy1 - 7))
            rv = np.sqrt(np.clip(1 - (dd / 3.0) ** 2, 0, 1)) * 2.0 + face + 3.6
            h = np.where(dd < 3.0, np.maximum(h, rv), h)
            shape = np.where(dd < 3.0, np.maximum(shape, rv), shape)
    coins = np.zeros_like(X)
    holes = np.zeros_like(X)
    glow = np.zeros_like(X)
    arms = np.zeros_like(X)
    import chrome as CH
    for cx, cy, sx, sy in ((x0 + 8, y0 + 8, 1, 1), (x1 - 8, y0 + 8, -1, 1), (x0 + 8, y1 - 8, 1, -1), (x1 - 8, y1 - 8, -1, -1)):
        if brackets and sy == 1:
            for pts in CH.bracket_scrolls(cx, cy, sx, sy, brackets, brackets * 0.18, 0):
                bh, bm = RL.bar(R, pts, coin * 0.3, coin * 0.1)
                bh = bh + top + 0.5
                h = np.where(bm > 0.5, np.maximum(h, bh), h)
                shape = np.where(bm > 0.5, np.maximum(shape, bh), shape)
                arms = np.maximum(arms, bm)
        chh, cm, hm = RL.coin(R, cx, cy, coin, top + 1.0, hole=0.34)
        h = np.where(cm > 0.5, np.maximum(h, chh), h)
        shape = np.where(cm > 0.5, np.maximum(shape, chh), shape)
        coins = np.maximum(coins, cm)
        holes = np.maximum(holes, hm)
        dh = np.hypot(X - cx, Y - cy) / (coin * 0.34 / 2)
        glow = np.maximum(glow, hm * np.exp(-dh ** 2 * 1.6))
    facet = F.facets(R.h, R.w, cell=18.0 * S, tilt=0.02, seed=61, soften=1.5 * S) / S
    dents = RL.hammered(R, cell=7.0, depth=0.28, seed=62) / S
    plain = (wm < 0.5) & (coins < 0.5) & (arms < 0.5)
    h = h + (facet + dents) * plain
    cover = np.maximum(cover, np.maximum(coins, arms))
    R.height = (h * S * cover).astype(np.float32)
    R.shape_height = (shape * S * cover).astype(np.float32)
    R.alpha = cover
    R.mat[:] = RL.IDS["iron"]
    R.mat[wm > 0.5] = RL.IDS["gold"]
    R.mat[holes > 0.5] = RL.IDS["ember"]
    face_m = (sd > border + 2) & ~crest_m
    t = np.where(face_m, 0.72, 1.0)
    # The crest a shade paler, so the code's tint reads on it.
    t = np.where(crest_m, 1.25, t)
    tint = t[..., None] * np.ones(3, np.float32)
    if oxblood:
        # Oxblood stain soaked into the iron, uneven, darkest in the hollows.
        n = F.fbm(R.h, R.w, scale=R.w / 5, octaves=5, seed=63) * 0.5 + 0.5
        stain = np.clip(0.45 + 0.7 * n, 0, 1)[..., None]
        ox = np.array([1.55, 0.55, 0.45], np.float32)
        tint = tint * (1 - stain + stain * ox)
    R.tint = tint.astype(np.float32)
    n2 = F.fbm(R.h, R.w, scale=R.w / 10, octaves=3, seed=64) * 0.5 + 0.5
    R.emit = ((glow * (0.5 + 0.6 * n2))[..., None] * (F.hexc("#ff6a1a") * 0.9 + F.hexc("#8a1c04") * 0.5)).astype(np.float32)
    img = R.render(name, samples=samples, wear=1.2, grime=0.9, seed=65)
    img = paint(img, R, name, prompt, denoise, protect=(face_m.astype(np.float32) * 0.6))
    small = R.file_size(img)
    import nineslice as N
    l, t_, r_, b = margins
    small = N.tileable(small, (l, t_, r_, b), blend=max(4, min(l, t_) // 10))
    return small


def crest_card():
    return iron_card("crest_card", 600, 700, 20, (80, 144, 80, 80), crest=116, coin=36, brackets=40,
                     prompt="an empty tall card of " + IRON + ", a thin twisted gold wire inlaid round its edge, a plain "
                     "paler iron crest plate riveted across its head, square iron coins with round holes at the corners, "
                     "curled iron brackets at its top corners, its face plain and flat")


def crest_row():
    return iron_card("crest_row", 600, 184, 16, (80, 72, 80, 56), border=18, chamfer=8, crest=46, coin=28,
                     prompt="an empty wide low plate of " + IRON + ", a thin twisted gold wire inlaid round its edge, a "
                     "paler iron crest strip riveted along its top, small square iron coins at the corners, its face plain")


def banner():
    return iron_card("banner", 512, 192, 8, (48, 28, 48, 28), border=18, chamfer=8, coin=30, brackets=30, oxblood=True,
                     prompt="an empty wide plate of hand-forged iron stained dark oxblood red, hammer marks, worn edges, a thin "
                     "twisted gold wire inlaid round its edge, square iron coins at the corners, curled iron brackets "
                     "at its top corners, its face plain and flat")


