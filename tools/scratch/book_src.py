def book(samples=96):
    """The Journal lying open (book/open.png, 3400x1704, 1700x852 shown): the survivor's
    ledger in a cover of oxblood leather worn at its edges, blind-tooled with a double line,
    its corners shod in the house's iron caps each nailed with a binders' coin. Two pages of
    laid rag paper curving down into the gutter, where the stitching shows, the page block's
    edges stacked along the outer sides and the foot. The pages are blank and even where the
    words go (78 in from the cover's outer edges, 34 from the spine, 68 from top and foot)."""
    W, H = 3400, 1704
    S = 1
    R = RL.Relief(W, H, S)
    X, Y = R.xx, R.yy
    k = 2.0  # file px per shown px
    cx = W / 2
    # The cover.
    cov = rect_sd(X, Y, 0, 0, W, H)
    cover_h = np.clip(cov / (4 * k), 0, 1) ** 0.6 * 7 * k
    # The page block: inset from the cover's edges, two pages meeting at the gutter.
    m_out, m_tb = 26 * k, 22 * k
    blk = rect_sd(X, Y, m_out, m_tb, W - m_out, H - m_tb)
    page = blk > 0
    gd = np.abs(X - cx)                       # from the gutter
    # The pages' surface: down into the gutter, up to a crown, rolling off at the outer edge.
    rise = 1 - np.exp(-gd / (70 * k))
    roll = np.clip(blk / (14 * k), 0, 1) ** 0.5
    page_h = (14 * k + 10 * k * rise) * (0.55 + 0.45 * roll)
    # The block's edge: stacked leaves along the outer sides and the foot, a step per leaf.
    leaves = np.clip(-blk / (3.0 * k), 0, 1)
    stack = (blk > -6 * k) & (blk <= 0) & ((np.abs(X - cx) > W / 2 - m_out - 2 * k) | (Y > H - m_tb - 2 * k))
    stack_h = 9 * k - np.floor(np.clip(-blk, 0, None) / (1.2 * k)) * 0.8 * k
    h = cover_h.copy()
    h = np.where(stack, np.maximum(h, stack_h), h)
    h = np.where(page, np.maximum(h, page_h), h)
    # The gutter: a deep fold and the sewing (four stitches of linen thread).
    fold = np.exp(-(gd / (5 * k)) ** 2) * 9 * k
    h = np.where(page, h - fold, h)
    stitch = np.zeros_like(X)
    for sy in (0.2, 0.4, 0.6, 0.8):
        y0 = m_tb + (H - 2 * m_tb) * sy
        d = np.hypot(np.clip(np.abs(Y - y0) - 16 * k, 0, None), X - cx)
        stitch = np.maximum(stitch, np.clip((2.2 * k - d) / k, 0, 1))
    h = np.where(stitch > 0, np.maximum(h, page_h * 0 + 6 * k + stitch * 2 * k), h)
    # The tooling: a double line pressed into the leather round the cover.
    t1 = np.abs(cov - 9 * k) < 0.9 * k
    t2 = np.abs(cov - 13 * k) < 0.6 * k
    tool = (t1 | t2) & ~page & ~stack
    h = np.where(tool, h - 1.6 * k, h)
    shape = h.copy()
    # The iron caps at the cover's corners, each a forged triangle with a coin nailed through.
    caps = np.zeros_like(X)
    holes = np.zeros_like(X)
    glow = np.zeros_like(X)
    for (sx, sy, x0, y0) in ((1, 1, 0, 0), (-1, 1, W, 0), (1, -1, 0, H), (-1, -1, W, H)):
        u = (X - x0) * sx
        v = (Y - y0) * sy
        L = 70 * k
        tri = (u + v < L) & (u > -2) & (v > -2)
        dtri = np.minimum(np.minimum(u, v), (L - u - v) / math.sqrt(2))
        cap_h = 10 * k + np.clip(dtri / (3 * k), 0, 1) * 3 * k
        h = np.where(tri, np.maximum(h, cap_h), h)
        shape = np.where(tri, np.maximum(shape, cap_h), shape)
        caps = np.maximum(caps, tri.astype(np.float32))
        ccx, ccy = x0 + sx * 20 * k, y0 + sy * 20 * k
        chh, cm, hm = RL.coin(R, ccx, ccy, 22 * k, 12.5 * k, hole=0.34)
        h = np.where(cm > 0.5, np.maximum(h, chh), h)
        shape = np.where(cm > 0.5, np.maximum(shape, chh), shape)
        caps = np.maximum(caps, cm)
        holes = np.maximum(holes, hm)
        dh = np.hypot(X - ccx, Y - ccy) / (22 * k * 0.34 / 2)
        glow = np.maximum(glow, hm * np.exp(-dh ** 2 * 1.6))
    # Grain: the leather's pebble, the paper's fibre (fine, so the pages stay even).
    grain_l = F.fbm(H, W, scale=3.0 * k, octaves=3, seed=71)
    grain_p = F.fbm(H, W, scale=1.2 * k, octaves=2, seed=72)
    cockle = F.fbm(H, W, scale=90 * k, octaves=3, seed=73)
    leather = ~page & ~stack & (caps < 0.5)
    h = h + np.where(leather, grain_l * 0.6 * k, 0) + np.where(page, grain_p * 0.15 * k + cockle * 1.5 * k, 0)
    R.height = h.astype(np.float32)
    R.shape_height = shape.astype(np.float32)
    R.alpha = np.ones_like(X)
    R.mat[:] = RL.IDS["leather"]
    R.mat[page | stack] = RL.IDS["paper"]
    R.mat[(caps > 0.5)] = RL.IDS["iron"]
    R.mat[holes > 0.5] = RL.IDS["ember"]
    R.mat[stitch > 0.5] = RL.IDS["bone"]
    # Colour: the leather blotched and darkest in its hollows; the paper cream, browning only
    # at its rims (away from the words), the stacked edges a little darker.
    cloud = F.fbm(H, W, scale=120 * k, octaves=4, seed=74) * 0.5 + 0.5
    t = np.ones((H, W), np.float32)
    t = np.where(leather, 0.75 + 0.5 * cloud, t)
    rim = np.clip(1 - blk / (30 * k), 0, 1) ** 2 * page
    t = np.where(page, (1 - 0.18 * rim) * (0.97 + 0.06 * cloud), t)
    t = np.where(stack, 0.8, t)
    tint = t[..., None] * np.ones(3, np.float32)
    tint = np.where(page[..., None], tint * (1 - rim[..., None] * np.array([0.0, 0.08, 0.2], np.float32)), tint)
    R.tint = tint.astype(np.float32)
    n2 = F.fbm(H, W, scale=W / 40, octaves=3, seed=75) * 0.5 + 0.5
    R.emit = ((glow * (0.5 + 0.6 * n2))[..., None] * (F.hexc("#ff6a1a") * 0.9 + F.hexc("#8a1c04") * 0.5)).astype(np.float32)
    img = R.render("book_open", samples=samples, wear=1.0, grime=0.8, seed=76)
    return R, img, page


def book_final():
    R, img, page = book()
    import paintover as PO
    key = hashlib.sha1(np.ascontiguousarray((img[::4, ::4] * 255).astype(np.uint8)).tobytes()).hexdigest()[:8]
    # The pages keep their render (blank and even, where the words go); the cover takes the hand.
    protect = cv2.GaussianBlur(page.astype(np.float32), (0, 0), 6) * 0.85
    lit = cv2.GaussianBlur((R.emit.max(axis=2) > 0.04).astype(np.float32), (0, 0), 3)
    protect = np.maximum(protect, np.clip(lit * 1.5, 0, 1))
    out = PO.paint(img, "an open old leather-bound ledger seen from above, dark oxblood leather cover worn at the "
                   "edges, blind-tooled lines, forged iron corner caps with square coins, two blank cream laid paper pages, "
                   "isolated on a pure black background", f"book_{key}", denoise=0.24, seed=11, target=2048,
                   keep_light=0.75, protect=protect)
    return out


