def binding(TW, H, rail, fillets, roll, pad_span, leather_span, name, shadow, ss=2, samples=192):
    """A band of the day's book's binding, tiled along (file TW x H; everything below in shown
    px): black morocco with an oxblood depth, padded between `pad_span` so the light runs
    across it, the binders' gilt fillets at `fillets` (y, half width), the twisted gold wire
    with a binders' coin every 128 px along `roll` (its y, or None), and the forged rail
    between `rail` (strap iron, a chamfered crown, the wire in a groove, domed nails).
    `shadow` is 'below' (what the band casts on the page under its rail) or 'above' (a soft
    seat where a foot band meets the page)."""
    tiles = 3
    W = TW * tiles
    R = RL.Relief(W, H, ss)
    X, Y = R.xx / ss, R.yy / ss
    y = Y / K
    xs = X / K
    rail0, rail1 = rail
    leather = (y >= leather_span[0]) & (y < leather_span[1])
    # Morocco: a fine pebbled grain, a few long soft creases, the board padded under it.
    pebble = tiled(R, TW, lambda h, w: F.fbm(h, w, scale=1.7 * K * ss, octaves=2, seed=81)) / ss
    crease = tiled(R, TW, lambda h, w: F.fbm(h, w, scale=70 * K * ss, octaves=3, seed=82)) / ss
    pad_t = np.clip((y - pad_span[0]) / (pad_span[1] - pad_span[0]), 0, 1)
    pad = np.clip(np.sin(pad_t * math.pi), 0, 1) ** 0.7 * 2.2 * K
    h = 4.0 * K + pad + pebble * 0.35 * K + crease * 0.9 * K
    # Its edge turned down where it meets the rail.
    if rail0 >= leather_span[1] - 2:   # (the rail at the foot)
        h = h - np.clip((y - (rail0 - 2.5)) / 2.5, 0, 1) ** 2 * 2.5 * K
    else:
        h = h - np.clip(((rail1 + 2.5) - y) / 2.5, 0, 1) ** 2 * 2.5 * K
    # The gilt: fillets pressed in and laid with gold (a round groove, so one wall takes the
    # light), and the wire in a pressed channel.
    gilt = np.zeros_like(X)
    gh = np.zeros_like(X)
    for yr, half in fillets:
        d = y - yr
        m = np.clip((half - np.abs(d)) * K * ss * 0.5 + 0.5, 0, 1)
        prof = 4.0 * K - 0.5 * K - (1 - rounded(d, half)) * 0.45 * K
        gh = np.where(m > 0.5, prof, gh)
        gilt = np.maximum(gilt, m)
    wm = np.zeros_like(X)
    coins = np.zeros_like(X)
    holes = np.zeros_like(X)
    coin_h = np.zeros_like(X)
    wire_h = np.zeros_like(X)
    if roll is not None:
        chan = np.clip((3.6 - np.abs(y - roll)) * K * ss * 0.5 + 0.5, 0, 1)
        h = h - chan * 0.9 * K
        wh, wm = wire(R, X, roll * K, 4.6 * K, TW / 150.0, 1.5 * K)   # (the pitch divides the tile)
        wire_h = 3.1 * K + wh
        # The binders' coin over the wire every 128 px: a square on its point, its face flat
        # and its edges chamfered to take the light, the round hole showing the leather.
        for k0 in range(int(W / K / 128) + 1):
            cx = (k0 + 0.5) * 128.0
            u, v = xs - cx, y - roll
            dia = np.abs(u) + np.abs(v)
            cm = np.clip((6.2 - dia) * K * ss * 0.5 + 0.5, 0, 1)
            bev = np.clip((6.2 - dia) / 1.5, 0, 1)
            bev = np.sqrt(1 - (1 - bev) ** 2)
            r = np.hypot(u, v)
            hm = np.clip((1.6 - r) * K * ss * 0.5 + 0.5, 0, 1)
            lip = np.exp(-((r - 2.1) / 0.45) ** 2) * 0.45
            ch = (4.4 + bev * 1.5 + lip) * K
            ch = np.where(hm > 0.5, 3.4 * K, ch)
            coin_h = np.where(cm > 0.5, np.maximum(coin_h, ch), coin_h)
            coins = np.maximum(coins, cm)
            holes = np.maximum(holes, hm * cm)
        # The wire stops short of each coin (the coin is set in it).
        clear = cv2.dilate((coins > 0.5).astype(np.uint8), np.ones((int(1.2 * K * ss) * 2 + 1,) * 2, np.uint8)) > 0
        wm = wm * (~clear)
    h = np.where(gilt > 0.5, gh, h)
    h = np.where(wm > 0.5, np.maximum(h, wire_h), h)
    h = np.where(coins > 0.5, np.maximum(h, coin_h), h)
    h = np.where(leather, h, 0)
    shape_h = np.where(leather, 4.0 * K + pad, 0)
    shape_h = np.where(wm > 0.5, np.maximum(shape_h, wire_h), shape_h)
    shape_h = np.where(coins > 0.5, np.maximum(shape_h, coin_h), shape_h)
    # The rail: strap iron with a chamfered crown, planished and dented.
    t = np.clip((y - rail0) / (rail1 - rail0), 0, 1)
    rail_prof = np.minimum(np.clip(t / 0.22, 0, 1), np.clip((1 - t) / 0.22, 0, 1)) ** 0.6 * 3.2 * K + 5.5 * K
    on_rail = (y >= rail0) & (y < rail1)
    facet = tiled(R, TW, lambda hh, ww: F.facets(hh, ww, cell=12.0 * K * ss, tilt=0.025, seed=83, soften=1.2 * ss, elong=0.4)) / ss
    dents = tiled(R, TW, lambda hh, ww: F.worley_dents(hh, ww, cell=4.0 * K * ss, depth=0.14 * K * ss, seed=84)) / ss
    rail_h = rail_prof + (facet + dents) * K * 0.6
    h = np.where(on_rail, rail_h, h)
    shape_h = np.where(on_rail, rail_prof, shape_h)
    yw = (rail0 + rail1) / 2
    groove = np.clip((2.3 - np.abs(y - yw)) * K * ss * 0.5 + 0.5, 0, 1) * on_rail
    h = h - groove * 1.4 * K
    rwh, rwm = wire(R, X, yw * K, 3.6 * K, 3.2 * K, 1.8 * K)
    rwm = rwm * on_rail
    rwire_h = 7.6 * K + rwh
    h = np.where(rwm > 0.5, np.maximum(h, rwire_h), h)
    shape_h = np.where(rwm > 0.5, np.maximum(shape_h, rwire_h), shape_h)
    # A domed nail through the rail every 64 px, either side of the wire, staggered.
    nails = np.zeros_like(X)
    for k0 in range(int(W / K / 64) + 1):
        for (nx, ny) in (((k0 + 0.25) * 64, rail0 + 2.5), ((k0 + 0.75) * 64, rail1 - 2.5)):
            dd = np.hypot(xs - nx, y - ny)
            r = 1.9
            dome = rounded(dd, r) * 1.3 * K + 8.9 * K
            m = dd < r
            h = np.where(m, np.maximum(h, dome), h)
            shape_h = np.where(m, np.maximum(shape_h, dome), shape_h)
            nails = np.maximum(nails, m.astype(np.float32))
    R.height = (h * ss).astype(np.float32)
    R.shape_height = (shape_h * ss).astype(np.float32)
    R.alpha = (leather | on_rail).astype(np.float32)
    R.mat[:] = RL.IDS["morocco"]
    R.mat[on_rail] = RL.IDS["iron"]
    R.mat[(nails > 0.5)] = RL.IDS["iron"]
    R.mat[(gilt > 0.5) & leather] = RL.IDS["gold"]
    R.mat[(wm > 0.5) & leather] = RL.IDS["gold"]
    R.mat[(coins > 0.5) & leather] = RL.IDS["gold"]
    R.mat[(holes > 0.5) & leather] = RL.IDS["morocco"]
    R.mat[rwm > 0.5] = RL.IDS["gold"]
    # The leather's colour: blotched as a hide is, darkest toward the screen's edge (the band
    # runs off it).
    cloud = tiled(R, TW, lambda hh, ww: F.fbm(hh, ww, scale=200 * K * ss, octaves=4, seed=85)) * 0.5 + 0.5
    at_foot = rail0 >= leather_span[1] - 2
    toward = np.clip(y / rail0, 0, 1) if at_foot else np.clip((leather_span[1] - y) / (leather_span[1] - rail1), 0, 1)
    fall = 0.7 + 0.3 * toward ** 0.7
    hide = (R.mat == RL.IDS["morocco"])
    tint = np.where(hide, (0.8 + 0.35 * cloud) * fall, 1.0)
    R.tint = (tint[..., None] * np.ones(3, np.float32)).astype(np.float32)
    # (the softbox's sheen greys a dark hide: the oxblood is pushed so it survives the light)
    R.tint = np.where(hide[..., None], R.tint * np.array([1.08, 0.7, 0.66], np.float32), R.tint).astype(np.float32)
    R.tint = np.where(on_rail[..., None] & (R.mat == RL.IDS["iron"])[..., None], R.tint * np.array([1.0, 0.95, 0.88], np.float32), R.tint).astype(np.float32)
    img = R.render(name, samples=samples, wear=1.0, grime=0.7, seed=86)
    small = R.file_size(img)
    band = small[:, TW:2 * TW]
    out = np.zeros((H, TW, 4), np.float32)
    out[...] = band
    yy = (np.arange(H, dtype=np.float32) / K)[:, None]
    if shadow == "below":
        sh = np.clip(1 - (yy - rail1) / 3.0, 0, 1) ** 1.2 * 0.75 * (yy >= rail1)
    else:
        sh = np.clip(1 - (rail0 - yy) / 4.0, 0, 1) ** 1.5 * 0.5 * (yy < rail0)
    a = out[..., 3]
    out[..., :3] = out[..., :3] * a[..., None]
    out[..., 3] = np.maximum(a, sh)
    out[..., :3] = np.where(out[..., 3:4] > 1e-4, out[..., :3] / np.maximum(out[..., 3:4], 1e-4), 0)
    return out


def header(ss=2, samples=192):
    """The band across every page's head (frames/header.png, 1024x200 file, 512x100 shown,
    slice 0 0 0 12, tiled along): the day's book's head. Along the top the twisted gold
    wire between two gilt fillets with a binders' coin every 128 px; one gilt fillet over
    the rail; the forged rail at the foot. The middle (y 18-78) is plain, for the tabs, the
    title and its line."""
    return binding(1024, 200, (84.0, 98.0), ((5.2, 0.75), (16.4, 0.75), (80.6, 0.6)), 10.8,
                   (19.0, 79.0), (0.0, 85.0), "page_header2", "below", ss, samples)


def footer(ss=2, samples=192):
    """The band across a page's foot (frames/footer.png, 1024x128 file, 512x64 shown, slice
    0 12 0 0, tiled along; placed with its top at y 1024 so it runs off the screen's foot):
    the book's foot, the header's twin turned over: a soft seat above, the forged rail along
    its top (y 4-18), a gilt fillet under it, then plain padded morocco where the prompts
    are written (y 20-56)."""
    return binding(1024, 128, (4.0, 18.0), ((21.4, 0.6),), None,
                   (22.0, 70.0), (17.0, 64.0), "page_footer", "above", ss, samples)
