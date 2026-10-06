def scroll_arm(R, c, r_arm, a0, a1, curl, w0, w1, sgn):
    """A lamp-iron's arm laid along a circle (file px) from angle a0 to a1 (0 at the top,
    clockwise; sgn the side), then curling outward in a scroll of radius `curl`. Returns its
    distance field's (height, mask) as a drawn bar, thick at its root, thin at its end."""
    X, Y = R.xx / R.ss, R.yy / R.ss
    pts, widths = [], []
    n1 = 36
    for t in np.linspace(0, 1, n1):
        a = sgn * (a0 + (a1 - a0) * t)
        pts.append((c + math.sin(a) * r_arm, c - math.cos(a) * r_arm))
        widths.append(w0 + (w1 - w0) * 0.6 * t)
    a_end = sgn * a1
    # The curl's centre: outward of the arm's end, so it turns away from the vessel.
    ccx, ccy = c + math.sin(a_end) * (r_arm + curl), c - math.cos(a_end) * (r_arm + curl)
    ex, ey = pts[-1]
    b0 = math.atan2(ey - ccy, ex - ccx)
    for t in np.linspace(0, 1, 30)[1:]:
        b = b0 + sgn * 1.35 * 2 * math.pi * t
        rr = curl * (1 - 0.72 * t)
        pts.append((ccx + math.cos(b) * rr, ccy + math.sin(b) * rr))
        widths.append(w0 + (w1 - w0) * (0.6 + 0.4 * t))
    pts = np.array(pts, np.float32)
    widths = np.array(widths, np.float32)
    # Distance and the nearest point's width, by brute force over the segments.
    best = np.full(X.shape, 1e9, np.float32)
    wbest = np.full(X.shape, w1, np.float32)
    for i in range(len(pts) - 1):
        ax, ay = pts[i]
        bx, by = pts[i + 1]
        ex_, ey_ = bx - ax, by - ay
        tt = np.clip(((X - ax) * ex_ + (Y - ay) * ey_) / (ex_ * ex_ + ey_ * ey_ + 1e-9), 0, 1)
        d = np.hypot(X - ax - ex_ * tt, Y - ay - ey_ * tt)
        w = widths[i] + (widths[i + 1] - widths[i]) * tt
        closer = d < best
        best = np.where(closer, d, best)
        wbest = np.where(closer, w, wbest)
    half = wbest / 2
    m = np.clip((half - best) * R.ss + 0.5, 0, 1)
    h = np.sqrt(np.clip(1 - (best / np.maximum(half, 0.1)) ** 2, 0, 1)) * half * 1.4
    return h * (m > 0), m


def globe_rim(ss=4, samples=160):
    """The health globe's rim (hud/globe_rim.png, 288 square, 144 shown round the 66 px
    liquid): the heart's setting grown into a vessel. A forged band the glass is set in, the
    binders' chain coiled round it in a channel (in the story each link of the chain is
    anchored in a heart), and at its head the link pried open with the ember at the break,
    held in a lamp-iron collar whose scrolled arms run down the band either side. Its
    middle open."""
    W = 288
    c = W / 2
    S = ss
    R = RL.Relief(W, W, ss)
    r, th = R.polar(c, c)
    X, Y = R.xx / S, R.yy / S
    r_out = 141.0 + RL.ragged(th, 0.8, seed=31, lobes=(3, 5, 8, 13))
    r_in = 0.835 * c          # reaches in over the liquid's edge
    top = 9.0
    cover = np.clip((r_out - r) * S + 0.5, 0, 1) * np.clip((r - r_in + 1.5) * S + 0.5, 0, 1)
    h = band_profile(r, r_out, r_in, top, outer_ch=4.0, inner_ch=3.0, shoulder=1.6)
    span = np.clip((r - r_in) / (r_out - r_in), 0, 1)
    h = h + np.sin(span * math.pi) * 1.6 * (h > 0)
    on_band = smoothstep(0.7, 0.95, h / top)
    # The channel the chain lies in.
    rc = (r_in + 141.0) / 2 + 0.5
    chw = 8.2
    chan = np.clip((chw - np.abs(r - rc)) * S / 2, 0, 1)
    floor = 2.5
    h = h * (1 - chan) + floor * chan
    shape = h.copy()
    link_h, link_m, brk = chain_round(R, c, rc, 40, 21.0, 11.5, 2.5, floor + 0.6, open_at=0, gap=3.2)
    # The lamp-iron collar at the head: a forged block across the band, the open link set
    # proud on it, nailed either side.
    al = c - Y              # up from the centre
    ac = X - c
    cap_sd = np.minimum(14.0 - np.abs(ac), np.minimum(al - (r_in - 1.0), 144.5 - al))
    cap = np.clip(cap_sd * S + 0.5, 0, 1)
    cap_h = top + 2.0 + np.sqrt(np.clip(cap_sd / 3.0, 0, 1)) * 1.8
    h = np.where(cap > 0.5, np.maximum(h, cap_h), h)
    shape = np.where(cap > 0.5, np.maximum(shape, cap_h), shape)
    # The chain: on the collar the open link rides on top of it.
    on_cap = (cap > 0.5) & (np.abs(ac) < 15.0)
    link_h = np.where(on_cap & (link_m > 0.5), link_h - (floor + 0.6) + cap_h.max() - 0.6, link_h)
    h = np.where(link_m > 0.5, np.maximum(h, link_h), h)
    shape = np.where(link_m > 0.5, np.maximum(shape, link_h), shape)
    # The arms: from the collar along the band's outer edge, curling outward at the end.
    arms_m = np.zeros_like(r)
    for sgn in (-1, 1):
        ah, am = scroll_arm(R, c, 136.5, math.radians(7), math.radians(40), 5.5, 6.5, 2.4, sgn)
        ah = ah + top + 0.8
        h = np.where(am > 0.5, np.maximum(h, ah), h)
        shape = np.where(am > 0.5, np.maximum(shape, ah), shape)
        arms_m = np.maximum(arms_m, am)
    for sx in (-1, 1):
        x0, y0 = c + sx * 9.5, c - (r_in + 5.0)
        d = np.hypot(X - x0, Y - y0)
        rv = np.sqrt(np.clip(1 - (d / 2.5) ** 2, 0, 1)) * 1.6 + cap_h.max()
        h = np.where(d < 2.5, np.maximum(h, rv), h)
        shape = np.where(d < 2.5, np.maximum(shape, rv), shape)
    facet = F.facets(R.h, R.w, cell=10.0 * S, tilt=0.022, seed=32, soften=1.5 * S) / S
    dents = RL.hammered(R, cell=5.0, depth=0.22, seed=33) / S
    plain = (link_m < 0.5) & (arms_m < 0.5)
    h = h + (facet + dents) * on_band * (1 - chan) * plain
    cover = np.maximum(cover, np.maximum(cap, arms_m))
    R.height = (h * S * cover).astype(np.float32)
    R.shape_height = (shape * S * cover).astype(np.float32)
    R.alpha = cover
    R.mat[:] = RL.IDS["iron"]
    R.mat[link_m > 0.5] = RL.IDS["chain"]
    R.tint = np.where(((chan > 0.5) & (link_m < 0.5) & (cap < 0.5))[..., None], 0.4, 1.0).astype(np.float32)
    n = F.fbm(R.h, R.w, scale=R.w / 12, octaves=3, seed=34) * 0.5 + 0.5
    emit = (brk * (0.8 + 0.5 * n))[..., None] * (F.hexc("#ff8a2a") * 2.2 + F.hexc("#c02a06") * 0.8)
    heat = cv2.GaussianBlur(brk, (0, 0), 3.0 * S) * 0.5
    R.emit = (emit + heat[..., None] * F.hexc("#c02a06") * 0.5).astype(np.float32)
    img = R.render("globe_rim", samples=samples, wear=1.3, grime=0.9, seed=35)
    return R, img


def globe_glass(ss=2, samples=256):
    """The globe's glass (hud/globe_glass.png, 288 square): only the light on it. A glass
    dome rendered under the house light with no colour of its own; what reflects is kept,
    its brightness as its coverage, so it lays over the liquid as light."""
    W = 288
    c = W / 2
    S = ss
    R = RL.Relief(W, W, ss)
    r, th = R.polar(c, c)
    rad = 0.917 * c
    cover = np.clip((rad - r) * S + 0.5, 0, 1)
    t = np.clip(r / rad, 0, 1)
    dome = np.sqrt(np.clip(1 - t ** 2, 0, 1)) * rad * 0.9
    R.height = (dome * S).astype(np.float32)
    R.alpha = cover
    R.mat[:] = RL.IDS["soot"]
    img = R.render("globe_glass", samples=samples, wear=0.0, grime=0.0, seed=36)
    return R, img


