"""Face 30 S3: the tail, ponytail chain and braid tie changes to tools/assets/heroine_hair.py (applied once)."""
p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\tools\assets\heroine_hair.py"
s = open(p, encoding="utf-8").read()


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:60], s.count(a))
    s = s.replace(a, b)


# cards: per-point facing
rep('def cards(P, width, columns, off, root=None, narrow=0.55, face=None, floor=0.0015):',
    'def cards(P, width, columns, off, root=None, narrow=0.55, face=None, floor=0.0015, out_pts=None):')
rep('''    at its root, widening to its full width a quarter of the way down."""
    S, K, _ = P.shape''', '''    at its root, widening to its full width a quarter of the way down. With
    `out_pts` (a way per point), each point faces that way instead (a tail's
    cards round its bundle)."""
    S, K, _ = P.shape''')
rep('''        out = out * 0.3 + np.asarray(face, float)[None, None] * 0.7
    for _ in range(3):''', '''        out = out * 0.3 + np.asarray(face, float)[None, None] * 0.7
    if out_pts is not None:
        out = np.array(out_pts, float)
    for _ in range(3):''')

# chain spheres: a margin per ball
rep('''def chain_spheres():
    """What the chain is kept out of: the back of her head, and her neck and
    back, a ball every 5 cm down her spine (each moving with the spine bone
    nearest it), reaching to the skin of her back there."""''', '''def chain_spheres(margin=0.008):
    """What the chain is kept out of: the back of her head, and her neck and
    back, a ball every 5 cm down her spine (each moving with the spine bone
    nearest it), reaching to the skin of her back there, and `margin` more (a
    number, or one for each ball's height: the hair's own depth on the side
    toward her, from the chain, so its strands, not only its middle, stay out
    of her)."""
    mg = margin if callable(margin) else (lambda z: margin)''')
rep('''        out.append({"bone": name, "at": c, "r": r + 0.008})''', '''        out.append({"bone": name, "at": c, "r": r + float(mg(z))})''')

# build: margin written
rep('''"spheres": [{"bone": sp["bone"], "at": g(sp["at"]), "r": sp["r"]} for sp in chain_spheres()]}''',
    '''"spheres": [{"bone": sp["bone"], "at": g(sp["at"]), "r": sp["r"]} for sp in chain_spheres(chain_margin(layers))]}''')
rep('''def follow_head(o, at):''', '''def chain_margin(layers):
    """How far the chain is kept off her back beyond her skin: CHAIN's
    "margin" (a number), or for "depth", at each height the swinging hair's
    depth toward her from the chain there (its strands' deepest, on the side
    toward her back, and 3 mm), 8 mm to 4 cm. (18 October, face 30: kept only
    8 mm off, the chain let a tail 3-5 cm thick sink 1.5 cm into her back.)"""
    m = CHAIN.get("margin", 0.008)
    if m != "depth":
        return m
    V = np.vstack([c["V"] for c in layers if c.get("swing") and c.get("mat", 0) != 2])
    Cp = resample(np.asarray(CHAIN["points"])[None], 64)[0]
    order = np.argsort(Cp[:, 2])

    def depth(z):
        near = np.abs(V[:, 2] - z) < 0.03
        if near.sum() < 20 or z > Cp[:, 2].max() or z < Cp[:, 2].min():
            return 0.008
        y = np.interp(z, Cp[order, 2], Cp[order, 1])           # (the chain's way out from her back: +y)
        return float(np.clip(y - V[near, 1].min() + 0.003, 0.008, 0.04))
    print("  chain margin:", ", ".join("%.2f m %.1f mm" % (z, depth(z) * 1000) for z in np.arange(1.62, 1.1, -0.05)))
    return depth


def follow_head(o, at):''')

# tail: flattened toward her back, cards round the bundle
rep('''def tail(T, axis, layers, length, spread=0.014, fan=3.0, points=24):
    """The tail from a tie at T: strands from a bundle there (a disc across
    `axis`), out along it a way, then let fall all together; as they fall
    each keeps its place in the bundle, the bundle widening to `fan` times as
    wide at the tips (hair has body: it does not fall to a string). Its
    layers (each so many strands, so wide, from such columns) after."""
    e1 = np.cross(axis, [1.0, 0.0, 0.0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(axis, e1)
    n = sum(ly[0] for ly in layers)
    r, a = spread * np.sqrt(RNG.random(n)), RNG.uniform(0, 2 * np.pi, n)
    disc = e1 * (r * np.cos(a))[:, None] + e2 * (r * np.sin(a))[:, None]
    disc -= disc.mean(0)''', '''def tail(T, axis, layers, length, spread=0.014, fan=3.0, points=24, flat=0.6, fan_thick=1.5):
    """The tail from a tie at T: strands from a bundle there (a disc across
    `axis`), out along it a way, then let fall all together; as they fall
    each keeps its place in the bundle, the bundle widening to `fan` times as
    wide at the tips (hair has body: it does not fall to a string). Its
    layers (each so many strands, so wide, from such columns) after.
    (18 October, face 30: a round bundle fanned 3x every way stood 3-5 cm
    thick off her back, and sank into it as it swung; its cards all faced out
    from her, so from the side it read as one flat ribbon. Now the bundle is
    `flat` as deep toward her back as it is wide, fanning only `fan_thick`
    times that way, and each card faces out round the bundle, as it lies in
    it: a round, full tail, wide on her back, not thick into it.)"""
    e1 = np.cross(axis, [1.0, 0.0, 0.0])
    e1 /= np.linalg.norm(e1)                                       # (toward her: her back's way in)
    e2 = np.cross(axis, e1)                                        # (side to side)
    n = sum(ly[0] for ly in layers)
    r, a = spread * np.sqrt(RNG.random(n)), RNG.uniform(0, 2 * np.pi, n)
    thick = e1 * (flat * r * np.cos(a))[:, None]
    wide = e2 * (r * np.sin(a))[:, None]
    thick -= thick.mean(0)
    wide -= wide.mean(0)
    disc = thick + wide''')
rep('''            want = disc * (1 + (fan - 1) * k / (K - 1))''',
    '''            want = wide * (1 + (fan - 1) * k / (K - 1)) + thick * (1 + (fan_thick - 1) * k / (K - 1))''')
rep('''    P = wave(P, 0.004, 0.13, T + disc * 40)
    out, at = [], 0
    for k, width, cols, off in layers:
        c = cards(P[at:at + k], RNG.uniform(*width, k), list(cols), off, root=np.full(k, 0.3), narrow=0.3)''', '''    P = wave(P, 0.004, 0.13, T + disc * 40)
    # Each point's way out round the bundle: from the chain's nearest point,
    # across it (side to side over her back, and out from her), as far out in
    # the bundle as it lies (its depth over the bundle's, its width over its
    # width), a little more out from her than in.
    Cd = resample(middle[None], 64)[0]
    flat_p = P.reshape(-1, 3)
    j = cKDTree(Cd).query(flat_p)[1]
    tg = np.gradient(Cd, axis=0)[j]
    tg /= np.linalg.norm(tg, axis=1)[:, None] + 1e-9
    away = -e1 - tg * (tg @ -e1)[:, None]
    away /= np.linalg.norm(away, axis=1)[:, None] + 1e-9
    across = np.cross(tg, away)
    d = flat_p - Cd[j]
    f = j / (len(Cd) - 1)
    A = spread * (1 + (fan - 1) * f)
    B = spread * flat * (1 + (fan_thick - 1) * f)
    face = across * ((d * across).sum(1) / A)[:, None] + away * ((d * away).sum(1) / B + 0.25)[:, None]
    face /= np.linalg.norm(face, axis=1)[:, None] + 1e-9
    face = face.reshape(P.shape)
    out, at = [], 0
    for k, width, cols, off in layers:
        c = cards(P[at:at + k], RNG.uniform(*width, k), list(cols), off, root=np.full(k, 0.3), narrow=0.3, out_pts=face[at:at + k])''')

# ponytail chain
rep('''    CHAIN = {"points": middle, "bone": "Head", "stiff": 0.01, "bend": 0.03}''',
    '''    CHAIN = {"points": middle, "bone": "Head", "stiff": 0.006, "bend": 0.02, "margin": "depth"}''')

# braid tie, and braid margin
rep('''    parts.append(band(C[end], t[end], 0.0135 * taper[end], wide=0.014, thick=0.004))''',
    '''    # (18 October, face 30: a ring 9 mm round its middle, the band sank into
    # the braid, whose strands reach 3.4 cm across it and 1.8 out, and into
    # her: now it wraps them, as wide as they reach each way)
    parts.append(band(C[end], t[end], (0.019 + 0.0145) * taper[end] + 0.001, wide=0.014, thick=0.004,
                      e=(ac[end], out[end]), rb=(0.0075 + 0.0100) * taper[end] + 0.001))''')
rep('''"bone": "Head", "stiff": 0.012, "bend": 0.03, "corner": 60}''',
    '''"bone": "Head", "stiff": 0.012, "bend": 0.03, "corner": 60, "margin": 0.015}''')
rep('''def band(T, axis, radius, wide=0.007, thick=0.0035):
    """A leather tie round her hair at T, across `axis`."""
    e1 = np.cross(axis, [1.0, 0.0, 0.0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(axis, e1)
    a = np.linspace(0, 2 * np.pi, 33)
    ring = T + radius * (np.cos(a)[:, None] * e1 + np.sin(a)[:, None] * e2)''', '''def band(T, axis, radius, wide=0.007, thick=0.0035, e=None, rb=None):
    """A leather tie round her hair at T, across `axis` (with `e` and `rb`,
    an oval: `radius` along e[0], `rb` along e[1])."""
    if e is None:
        e1 = np.cross(axis, [1.0, 0.0, 0.0])
        e1 /= np.linalg.norm(e1)
        e2 = np.cross(axis, e1)
    else:
        e1, e2 = (np.asarray(v, float) / np.linalg.norm(v) for v in e)
    a = np.linspace(0, 2 * np.pi, 33)
    ring = T + np.cos(a)[:, None] * e1 * radius + np.sin(a)[:, None] * e2 * (radius if rb is None else rb)''')
open(p, "w", encoding="utf-8").write(s)
print("ok")
