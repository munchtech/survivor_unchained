def globe_glass(ss=4, samples=0):
    """The globe's glass (hud/globe_glass.png, 288 square): only the light on it, painted
    as a painter paints glass: the room's window caught upper left (four leaded panes, as
    the Waystation's), a softer bloom round it, a thin rim of the cool light along the lower
    right edge, a faint brightening all round the edge where glass turns away. The rest
    clear, so the liquid and the number show."""
    W = 288
    c = W / 2
    S = ss
    R = RL.Relief(W, W, ss)
    X, Y = R.xx / S, R.yy / S
    rad = 0.917 * c
    dx, dy = (X - c) / rad, (Y - c) / rad
    rr = np.hypot(dx, dy)
    inside = np.clip((1 - rr) * rad * S + 0.5, 0, 1)
    # The window: a small curved quad upper left, its panes split by lead, bent to the dome.
    # Coordinates on the dome: map to a sphere's tangent near the highlight.
    hx, hy, ang = -0.42, -0.46, math.radians(-38)
    u = (dx - hx) * math.cos(ang) + (dy - hy) * math.sin(ang)
    v = -(dx - hx) * math.sin(ang) + (dy - hy) * math.cos(ang)
    # Curved: the window's edges bow with the glass.
    v = v + 0.9 * u * u
    win_w, win_h = 0.17, 0.11
    soft = 0.012
    win = np.clip((win_w - np.abs(u)) / soft, 0, 1) * np.clip((win_h - np.abs(v)) / soft, 0, 1)
    lead = np.clip((0.010 - np.abs(u)) / 0.006, 0, 1) + np.clip((0.008 - np.abs(v)) / 0.005, 0, 1)
    win = win * (1 - np.clip(lead, 0, 1) * 0.85)
    # Brighter toward its upper left corner (the light's direction).
    win = win * (0.75 + 0.25 * np.clip(-(u + v) / 0.2 + 0.5, 0, 1))
    bloom = np.exp(-((u / 0.34) ** 2 + (v / 0.24) ** 2)) * 0.22
    # The rim: a thin crescent of cool light inside the lower right edge.
    a = np.arctan2(dx, -dy)  # 0 at the top, clockwise
    side = np.clip(np.cos(a - math.radians(135)), 0, 1) ** 2.5
    rim = np.exp(-((rr - 0.94) / 0.025) ** 2) * side * 0.6
    edge = np.clip((rr - 0.80) / 0.2, 0, 1) ** 3 * 0.10
    a_hl = np.clip(win * 0.78 + bloom + rim + edge, 0, 0.9) * inside
    warm = F.hexc("#fff0dc", lin=False)
    cool = F.hexc("#c8d4ff", lin=False)
    mixw = np.clip((win * 0.78 + bloom) / np.maximum(a_hl / np.maximum(inside, 1e-3), 1e-4), 0, 1)
    col = warm[None, None, :] * mixw[..., None] + cool[None, None, :] * (1 - mixw[..., None])
    img = np.dstack([col, a_hl]).astype(np.float32)
    return R, img


