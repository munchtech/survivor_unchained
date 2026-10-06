p = r'C:\Users\munch\Desktop\survivorsunchained\tools\assets\heroine_outfits.py'
s = open(p, encoding='utf-8').read()


def rep(a, b, n=1):
    global s
    assert a in s, a[:70]
    s = s.replace(a, b, n)


# ---- piece(): the slot opt-out, and the bridge across it.
rep('''budget=None, filled=False, edge=30):''', '''budget=None, filled=False, edge=30, slot=True, bridge=False):''')
rep('''    f = smooth_field(np.minimum.reduce([field, (0.3 - wsum(*keep_off)) * 0.1, (0.5 - HAIR) * 0.1,
                                        np.where(SLOT, -0.004, 1.0)]), soften)''',
    '''    slot_m = SLOT if slot is True else (SLOT & (X < 0) if slot == "right" else (SLOT & (X > 0) if slot == "left" else np.zeros(len(P), bool)))
    f = smooth_field(np.minimum.reduce([field, (0.3 - wsum(*keep_off)) * 0.1, (0.5 - HAIR) * 0.1,
                                        np.where(slot_m, -0.004, 1.0)]), soften)''')
rep('''    pos, at, tris = clip(f, P_FILLED if (dome or filled) else P, attr, TRI)
    if len(tris) == 0:
        print("EMPTY", name)
        return []
    pos, at, tris = weld(pos, at, tris)''', '''    # A garment crossing her crotch is cut off just in front of and just
    # behind the slot between her thighs (`gap` is how far a point is out
    # of that box), and the two cut edges joined by a strip under her.
    gap = np.maximum.reduce([GAP_F - Y, Y - GAP_B, Z - GAP_Z, np.abs(X) - 0.07]) if bridge else np.ones(len(P))
    pos, at, tris = clip(np.minimum(f, gap), P_FILLED if (dome or filled) else P, np.hstack([attr, gap[:, None]]), TRI)
    if len(tris) == 0:
        print("EMPTY", name)
        return []
    pos, at, tris = weld(pos, at, tris)
    gap_at, at = at[:, -1], at[:, :-1]''')
rep('''    made = [finish(name, pos, at[:, 3:3 + NB], tris, mkey, thick, bevel, budget or (8000 if dome else 3000))]
    if studs:''', '''    made = [finish(name, pos, at[:, 3:3 + NB], tris, mkey, thick, bevel, budget or (8000 if dome else 3000))]
    if bridge:
        made += crotch_bridge(name, pos, tris, gap_at, mkey, thick, bevel, trim, lift)
    if studs:''')

# ---- the box, the roof, the bridge, and paths along the roof.
rep('''print("SLOT", int(SLOT.sum()), "points of her inner thighs under the crotch")''', '''print("SLOT", int(SLOT.sum()), "points of her inner thighs under the crotch")
# The box a crossing garment is cut out of: from in front of the slot to
# behind it, below just over the crotch.
GAP_F, GAP_B, GAP_Z = CROTCH_Y - 0.03, CROTCH_Y + 0.04, CROTCH + 0.012


def roof_z(x, y):
    """Height of her skin straight above a point under her crotch (the top
    of the slot between her thighs), seen from below."""
    hit = BVH.ray_cast(Vector((x, y, CROTCH - 0.3)), Vector((0, 0, 1)), 0.6)
    return hit[0].z if hit[0] is not None else CROTCH


def roof_path(y0, y1, n=12, x=0.0, lift=0.003):
    """Points along the top of the slot, under her, from y0 to y1."""
    return [np.array([x, y, roof_z(x, y) - lift]) for y in np.linspace(y0, y1, n)]


def crotch_bridge(name, pos, tris, gap_at, mkey, thick, bevel, trim, lift, rows=18, cols=13):
    """The strip that carries a garment across her crotch: from its front
    cut edge to its back one, each row straight across, its middle along
    the top of the slot (so it spans the gap as cloth does, never dipping
    in), its edges running into her thighs either side."""
    e = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
    uk, c = np.unique(np.sort(e, 1), axis=0, return_counts=True)
    bv = np.unique(uk[c == 1])
    cutv = bv[(np.abs(gap_at[bv]) < 0.0025) & (pos[bv, 2] < GAP_Z + 0.004)]
    front = cutv[pos[cutv, 1] < CROTCH_Y]
    back = cutv[pos[cutv, 1] >= CROTCH_Y]
    if len(front) < 2 or len(back) < 2:
        print("BRIDGE", name, "no edges to join", len(front), len(back))
        return []

    def resample(ids):
        q = pos[ids][np.argsort(pos[ids, 0])]
        d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(q, axis=0), axis=1))]
        t = np.linspace(0, d[-1], cols)
        return np.stack([np.interp(t, d, q[:, k]) for k in range(3)], 1)

    fr, bk = resample(front), resample(back)
    g = np.zeros((rows, cols, 3))
    for i in range(rows):
        t = i / (rows - 1)
        g[i] = fr * (1 - t) + bk * t
    # The middle of each row along the roof of the slot; the whole row
    # lowered with it, so it stays straight across.
    for i in range(1, rows - 1):
        mid = g[i, cols // 2]
        target = min(mid[2], roof_z(mid[0], mid[1]) - lift)
        g[i, :, 2] += target - mid[2]
    for _ in range(6):
        g[1:-1] = (g[:-2] + 2 * g[1:-1] + g[2:]) / 4
    pts = g.reshape(-1, 3)
    tt = grid(rows, cols)
    nor = vertex_normals(pts, tt)
    if nor[:, 2].mean() > 0:            # facing down, out of her
        tt = tt[:, ::-1]
        nor = -nor
    _, j = cKDTree(P).query(pts)
    width = np.linalg.norm(g[:, -1] - g[:, 0], axis=1)
    col = np.tile(np.arange(cols), rows)
    edge = np.minimum(col, cols - 1 - col) / (cols - 1) * np.repeat(width, cols)
    at = np.hstack([nor, W[j].astype(float), edge[:, None]])
    made = trimmed(name + "_bridge", pts, at, tt, mkey, thick, bevel, trim, budget=10 ** 7)
    for o in made:
        o["hides"] = True
    print("BRIDGE", name, "%.1f cm wide in front, %.1f behind" % (width[0] * 100, width[-1] * 100))
    return made''')

# ---- who bridges, who keeps a side of the slot.
rep('''*piece("warden.bottom", bot, "darkleather", lift=0.003, smooth=2),''', '''*piece("warden.bottom", bot, "darkleather", lift=0.003, smooth=2, bridge=True),''')
rep('''*piece("ranger.suit", lower, "greenleather", lift=0.0025, smooth=3),''', '''*piece("ranger.suit", lower, "greenleather", lift=0.0025, smooth=3, slot="right"),''')
# Arcanist: the front panel narrows to the strap's width at the crotch, and
# the strap runs from her back, down the cleft and under her, to tuck under it.
rep("    w = (0.02 + 0.4 * np.maximum(Z - CROTCH, 0)) * FRONT", "    w = (0.0095 + 0.42 * np.maximum(Z - CROTCH, 0)) * FRONT")
rep('''*ribbon("arcanist.thong", back_string(CROTCH + 0.155, CROTCH - 0.03),''',
    '''*ribbon("arcanist.thong", thong_path(CROTCH + 0.155),''')
rep('''def roof_z(x, y):''', '''def thong_path(z_top, y_front=None):
    """A thong's line: down the cleft behind from z_top, then forward
    under her along the top of the slot, to tuck under the front."""
    back = back_string(z_top, CROTCH + 0.012)
    y0 = back[-1][1] - 0.004
    y1 = (GAP_F - 0.006) if y_front is None else y_front
    return back + roof_path(y0, y1, 10)


def roof_z(x, y):''')
open(p, 'w', encoding='utf-8').write(s)
print("patched")
