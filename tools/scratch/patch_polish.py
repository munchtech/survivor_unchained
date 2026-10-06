p = r'C:\Users\munch\Desktop\survivorsunchained\tools\assets\heroine_outfits.py'
s = open(p, encoding='utf-8').read()


def rep(old, new, count=1):
    global s
    assert old in s, old[:80]
    s = s.replace(old, new, count)


# ---- fur from a real scan, darkened to a wolf's brown.
rep('''    "fur": ("faux_fur_geometric", (0.6, 0.48, 0.36), None, 4, 0.0, None),''',
    '''    "fur": ("curly_teddy_natural", (0.55, 0.42, 0.32), 70, 4, 0.0, 0.9),''')

# ---- steel without its white flecks: highlights held near the plate's own colour.
rep('''    if mean:
        col = col * (mean / col.mean())''', '''    if mean:
        col = col * (mean / col.mean())
    if key in ("steel", "darksteel", "gold", "bronze"):
        # Scratches and flecks in the scan read as white specks at this scale.
        med = np.median(col.reshape(-1, 3), 0)
        col = np.minimum(col, med * 1.18)''')

# ---- thinning keeps the edges at full resolution, so cut lines stay smooth.
rep('''    if len(me.polygons) > budget:
        dc = obj.modifiers.new("thin", "DECIMATE")
        dc.decimate_type = "COLLAPSE"
        dc.ratio = budget / len(me.polygons)''', '''    if len(me.polygons) > budget:
        # Only the inside is thinned: the edge and two rows in from it keep
        # every point, so a cut line stays the smooth curve it was made.
        e = np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]])
        uk, c = np.unique(np.sort(e, 1), axis=0, return_counts=True)
        keep = np.zeros(len(pos))
        keep[uk[c == 1].ravel()] = 1
        A = adjacency(len(pos), tris)
        for _ in range(2):
            keep = np.maximum(keep, (A @ keep > 0).astype(float))
        inner = obj.vertex_groups.new(name="_thin")
        inner.add([int(i) for i in np.where(keep == 0)[0]], 1.0, "REPLACE")
        dc = obj.modifiers.new("thin", "DECIMATE")
        dc.decimate_type = "COLLAPSE"
        dc.vertex_group = "_thin"
        dc.vertex_group_factor = 1000.0
        dc.ratio = budget / len(me.polygons)''')
rep('''    for mod in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)
    me.set_sharp_from_angle(angle=math.radians(50))''', '''    for mod in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)
    if "_thin" in obj.vertex_groups:
        obj.vertex_groups.remove(obj.vertex_groups["_thin"])
    me.set_sharp_from_angle(angle=math.radians(50))''')

# ---- rivets along a piece's edge.
rep('''def finish(name, pos, wt, tris, mkey, thick, bevel, budget=3000):''', '''def rivets(name, pos, at, tris, thick, mkey, spacing=0.028, inset=0.011, r=0.0032):
    """Domed rivets set in from a piece's edge every `spacing`, on its
    outer face: the detail that makes a plate read as made."""
    f = at[:, -1]
    cand = np.where(np.abs(f - inset) < 0.0025)[0]
    if len(cand) == 0:
        return []
    picked = []
    tree_p = []
    for i in cand[np.argsort(pos[cand, 2])]:
        if all(np.linalg.norm(pos[i] - q) >= spacing for q in tree_p):
            picked.append(i)
            tree_p.append(pos[i])
    nor = vertex_normals(pos, tris)
    P2, W2, T2 = [], [], []
    nu, nv = 12, 4
    for i in picked:
        n = nor[i]
        t = np.cross(n, [0, 0, 1.0]) if abs(n[2]) < 0.9 else np.cross(n, [1.0, 0, 0])
        t /= np.linalg.norm(t)
        b = np.cross(n, t)
        base = pos[i] + n * (thick + 0.0003)
        pts = [base + n * r * 0.75]
        for k in range(1, nv + 1):
            th = (np.pi / 2) * k / nv
            for j in range(nu):
                ph = 2 * np.pi * j / nu
                pts.append(base + (np.cos(ph) * t + np.sin(ph) * b) * r * np.sin(th) + n * r * 0.75 * np.cos(th))
        o = sum(len(x) for x in P2)
        tri = [(o, o + 1 + j, o + 1 + (j + 1) % nu) for j in range(nu)]
        for k in range(nv - 1):
            a0, b0 = o + 1 + k * nu, o + 1 + (k + 1) * nu
            for j in range(nu):
                j1 = (j + 1) % nu
                tri += [(a0 + j, b0 + j, b0 + j1), (a0 + j, b0 + j1, a0 + j1)]
        P2.append(np.array(pts))
        W2.append(np.repeat(at[i:i + 1, 3:3 + NB], len(pts), 0))
        T2.append(np.array(tri))
    if not P2:
        return []
    pp, ww, tt = np.vstack(P2), np.vstack(W2), np.vstack(T2)
    if (vertex_normals(pp, tt) * (pp - np.repeat(np.array([pos[i] for i in picked]), (nv * nu + 1), 0))).sum(1).mean() < 0:
        tt = tt[:, ::-1]
    print("RIVETS", name, len(picked))
    return [finish(name + "_rivets", pp, ww, tt, mkey, 0.0002, 0.0, 10 ** 7)]


def finish(name, pos, wt, tris, mkey, thick, bevel, budget=3000):''')

# piece(): rivets and a budget of its own.
rep('''cut=None, iron=0, hull=None):''', '''cut=None, iron=0, hull=None, studs=None, budget=None):''')
rep('''    made = [finish(name, pos, at[:, 3:3 + NB], tris, mkey, thick, bevel, 8000 if dome else 3000)]''',
    '''    made = [finish(name, pos, at[:, 3:3 + NB], tris, mkey, thick, bevel, budget or (8000 if dome else 3000))]
    if studs:
        made += rivets(name, pos, at, tris, thick, studs)''')

# ---- warden: rivets in gold on plate.
for nm in ('warden.pauldron_{sd}', 'warden.vambrace_{sd}', 'warden.greave_{sd}'):
    pass
rep('''"steel", lift=0.012, thick=0.004, smooth=14, trim=gold(0.01)),''', '''"steel", lift=0.012, thick=0.004, smooth=14, trim=gold(0.01), studs="gold"),''')
rep('''legs=False), "steel", lift=0.006, smooth=8, trim=gold()),''', '''legs=False), "steel", lift=0.006, smooth=8, trim=gold(), studs="gold"),''')
rep('''front_dip=0.04), "steel", lift=0.008, smooth=12, trim=gold()),''', '''front_dip=0.04), "steel", lift=0.008, smooth=12, trim=gold(), studs="gold"),''')
rep('''*piece("warden.plate", plate, "steel", lift=0.006, thick=0.003, smooth=6, trim=gold(0.006)),''',
    '''*piece("warden.plate", plate, "steel", lift=0.006, thick=0.003, smooth=6, trim=gold(0.006), studs="gold"),''')
# ranger: bronze rivets on bracers.
rep('''legs=False), "bronze", lift=0.007, smooth=8, trim=gold(0.006, "brownleather")),''',
    '''legs=False), "bronze", lift=0.007, smooth=8, trim=gold(0.006, "brownleather"), studs="darksteel"),''')
# reaver: iron studs on bracers; tattoos never thinned and clear of the skin.
rep('''legs=False), "oldleather", lift=0.004, smooth=6, trim=edge()),''', '''legs=False), "oldleather", lift=0.004, smooth=6, trim=edge(), studs="rust"),''')
s = s.replace('"ink", lift=0.0006, thick=0.0002, bevel=0.0, soften=0),', '"ink", lift=0.0012, thick=0.0002, bevel=0.0, soften=0, budget=10 ** 7),')
# G-string: a thin leather strap behind, riding over her cleft.
rep('''            AND(0.5 - FRONT, 0.007 - np.abs(X), (belt_z + 0.005) - Z, Z - (CROTCH - 0.03))), "oldleather", lift=0.002, smooth=2, soften=0),''',
    '''            AND(0.5 - FRONT, 0.009 - np.abs(X), (belt_z + 0.005) - Z, Z - (CROTCH - 0.03))), "oldleather", lift=0.003, thick=0.003, smooth=10, soften=0),''')
open(p, 'w', encoding='utf-8').write(s)
print("patched")
