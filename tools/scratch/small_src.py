def ribbon(ss=4, samples=128):
    """A section's ribbon in the Journal (book/ribbon.png, 264x172, stretched to 132x66-86):
    a length of pale ivory silk laid over the book's head, its foot cut in a swallowtail, a
    soft fold or two along it, its edges turned and stitched. The code dyes it the section's
    colour and casts its shadow, so it is painted pale and even."""
    W, H = 264, 172
    S = ss
    R = RL.Relief(W, H, ss)
    X, Y = R.xx / S, R.yy / S
    side = 8.0
    notch = 30.0
    # The swallowtail: the foot cut in a V from both corners up to the middle.
    foot = H - 2 - notch * (1 - np.abs(X - W / 2) / (W / 2 - side))
    sd = np.minimum(np.minimum(X - side, W - side - X), np.minimum(Y + 50, foot - Y))
    cover = np.clip(sd * S + 0.5, 0, 1)
    # Folds along its length, a slight belly, the turned hems at its sides.
    u = (X - side) / (W - 2 * side)
    folds = 2.2 * np.sin(u * math.pi * 2.0 + 0.6) + 1.2 * np.sin(u * math.pi * 5.0 + 1.3)
    belly = 5.0 * np.sin(np.clip(u, 0, 1) * math.pi)
    hem = np.exp(-(np.clip(sd, 0, None) / 2.2) ** 2) * 1.6
    h = 6.0 + folds + belly + hem
    # The stitch line just inside each side.
    for xs in (side + 5.5, W - side - 5.5):
        st = (np.abs(X - xs) < 0.7) & ((Y % 6.0) < 3.6) & (Y < foot - 4)
        h = np.where(st, h - 0.6, h)
    weave = F.fbm(R.h, R.w, scale=0.6 * S, octaves=1, seed=81) * 0.08
    h = h + weave * (sd > 0)
    R.height = (h * S * cover).astype(np.float32)
    R.shape_height = R.height
    R.alpha = cover
    R.mat[:] = RL.IDS["silk"]
    img = R.render("ribbon", samples=samples, wear=0.0, grime=0.3, seed=82, grain=0.2)
    return R.file_size(img)


def plaque_rule(ss=8, samples=128):
    """The rule beside a page's name (ornaments/plaque_rule.png, 480x24, drawn to the title's
    right and mirrored to its left, stretched 90-180 px): at its left end, toward the words,
    a binders' coin with the ember asleep in it; from it the twisted gold wire runs out,
    thinning, and ends in a small knop."""
    W, H = 480, 24
    S = ss
    R = RL.Relief(W, H, ss)
    X, Y = R.xx / S, R.yy / S
    cy = H / 2
    x0, x1 = 22.0, W - 8.0
    t = np.clip((X - x0) / (x1 - x0), 0, 1)
    th = 5.2 - 2.6 * t
    across = Y - cy
    s_ = X / 3.2
    hgt = np.zeros_like(X)
    for k in (0.0, 0.5):
        uu = ((across / th) - (((s_ + k) % 1.0) - 0.5)) % 1.0 - 0.5
        hgt = np.maximum(hgt, np.sqrt(np.clip(1 - (uu / 0.5) ** 2, 0, 1)))
    wm = np.clip((th / 2 - np.abs(across)) * S + 0.5, 0, 1) * (X > x0 - 4) * (X < x1)
    edge = np.sqrt(np.clip(1 - (across / (th / 2)) ** 2, 0, 1))
    h = np.where(wm > 0.5, (hgt * 0.55 + edge * 0.45) * th * 0.6 + 1.0, 0)
    # The knop at the far end.
    dk = np.hypot(X - x1, Y - cy)
    knop = np.clip((3.0 - dk) * S + 0.5, 0, 1)
    h = np.where(knop > 0.5, np.maximum(h, np.sqrt(np.clip(1 - (dk / 3.0) ** 2, 0, 1)) * 3.0 + 1.0), h)
    chh, cm, hm = RL.coin(R, 12.0, cy, 18.0, 1.0, hole=0.38)
    h = np.where(cm > 0.5, np.maximum(h, chh), h)
    cover = np.maximum(np.maximum(wm, knop), cm)
    R.height = (h * S * cover).astype(np.float32)
    R.shape_height = R.height
    R.alpha = cover
    R.mat[:] = RL.IDS["gold"]
    R.mat[cm > 0.5] = RL.IDS["iron"]
    R.mat[hm > 0.5] = RL.IDS["ember"]
    dh = np.hypot(X - 12.0, Y - cy) / (18 * 0.38 / 2)
    glow = hm * np.exp(-dh ** 2 * 1.4)
    R.emit = (glow[..., None] * (F.hexc("#ff7a22") * 1.4 + F.hexc("#a02404") * 0.6)).astype(np.float32)
    img = R.render("plaque_rule", samples=samples, wear=0.8, grime=0.5, seed=83)
    return R.file_size(img)


