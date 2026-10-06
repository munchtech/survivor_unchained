p = r'C:\Users\munch\Desktop\survivorsunchained\tools\assets\heroine_outfits.py'
s = open(p, encoding='utf-8').read()


def rep(a, b, n=1):
    global s
    assert a in s, a[:80]
    s = s.replace(a, b, n)


BIND = '''# ------------------------------------------------------------- bindings --
def smooth_closed(curve, sigma, step=0.002):
    """A closed line resampled evenly (every `step`) and eased with a
    Gaussian `sigma` long, so it runs as one fair curve."""
    c = np.vstack([curve, curve[:1]])
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))]
    n = max(24, int(d[-1] / step))
    t = np.linspace(0, d[-1], n, endpoint=False)
    r = np.stack([np.interp(t, d, c[:, k]) for k in range(3)], 1)
    sg = sigma / (d[-1] / n)
    if sg > 0.3:
        k = int(np.ceil(3 * sg))
        g = np.exp(-0.5 * (np.arange(-k, k + 1) / sg) ** 2)
        g /= g.sum()
        r = sum(np.roll(r, -i, 0) * g[i + k] for i in range(-k, k + 1))
    return r


def tube(name, curve, nrm, outward, mkey, width, height, overhang, thick, src_pos, src_wt, closed=True, nv=12):
    """A rolled edge along a line: a flattened tube `width` across, centred
    so it reaches `overhang` past the line on its `outward` side, and stands
    `height` proud of a sheet `thick` thick lying under it (half its
    height above the sheet, wrapping its cut edge). Weights from the
    nearest point of the sheet it binds."""
    n = len(curve)
    c0 = curve + outward * (overhang - width / 2) + nrm * (thick / 2)
    rw, rh = width / 2, thick / 2 + height
    th = np.linspace(0, 2 * np.pi, nv, endpoint=False)
    pts = (c0[:, None, :] + outward[:, None, :] * (rw * np.cos(th))[None, :, None]
           + nrm[:, None, :] * (rh * np.sin(th))[None, :, None]).reshape(-1, 3)
    rows = n + (0 if closed else -1)
    tris = []
    for i in range(rows):
        i1 = (i + 1) % n
        for j in range(nv):
            j1 = (j + 1) % nv
            a, b, c, d = i * nv + j, i * nv + j1, i1 * nv + j, i1 * nv + j1
            tris += [(a, c, b), (b, c, d)]
    tris = np.array(tris)
    if not closed:
        # Ends closed with a fan.
        caps = []
        for i in (0, n - 1):
            ci = len(pts) + len(caps)
            caps.append(c0[i])
            for j in range(nv):
                j1 = (j + 1) % nv
                tris = np.vstack([tris, [(ci, i * nv + j1, i * nv + j)] if i == 0 else [(ci, i * nv + j, i * nv + j1)]])
        pts = np.vstack([pts, np.array(caps)])
    cen = np.vstack([np.repeat(c0, nv, 0), c0[[0, -1]]]) if not closed else np.repeat(c0, nv, 0)
    vn = vertex_normals(pts, tris)
    if ((pts - cen) * vn).sum(1).mean() < 0:
        tris = tris[:, ::-1]
    _, j = cKDTree(src_pos).query(pts)
    obj = finish(name, pts, src_wt[j], tris, mkey, 0.0, 0.0, 10 ** 7)
    obj["hides"] = True
    return obj


def bind_edges(name, pos, at, tris, key, width, height, overhang, thick, sigma=0.007):
    """A sheet's cut outline made fair and bound: each edge loop eased into
    one smooth curve, the sheet's own edge points moved onto it, and a
    rolled edge laid along it that covers the cut, as a garment's edges are
    bound or a plate's are rolled."""
    loops = rim_loops(pos, tris)
    if not loops:
        return pos, []
    nor = vertex_normals(pos, tris)
    tree = cKDTree(pos)
    beads = []
    pos = pos.copy()
    moved = np.zeros(len(pos), bool)
    for k, loop in enumerate(loops):
        cur = smooth_closed(pos[loop], sigma)
        # Back onto the sheet, and the sheet's normal there.
        _, j = tree.query(cur)
        nrm = nor[j].copy()
        for _ in range(4):
            nrm = (np.roll(nrm, 1, 0) + 2 * nrm + np.roll(nrm, -1, 0)) / 4
        cur = cur + nrm * ((pos[j] - cur) * nrm).sum(1)[:, None]
        tg = np.roll(cur, -1, 0) - np.roll(cur, 1, 0)
        tg /= np.linalg.norm(tg, axis=1)[:, None] + 1e-12
        nrm = nrm - tg * (nrm * tg).sum(1)[:, None]
        nrm /= np.linalg.norm(nrm, axis=1)[:, None] + 1e-12
        bn = np.cross(nrm, tg)
        # Outward: away from the sheet's points near the line.
        votes = []
        for i in range(0, len(cur), 4):
            near = tree.query_ball_point(cur[i], 0.02)
            if near:
                votes.append(((pos[near].mean(0) - cur[i]) @ bn[i]))
        sgn = -1.0 if np.median(votes) > 0 else 1.0
        outward = bn * sgn
        # The sheet's edge points onto the fair line.
        lt = cKDTree(cur)
        _, jj = lt.query(pos[loop])
        pos[loop] = cur[jj]
        moved[loop] = True
        beads.append(tube(f"{name}_bind{k}" if k else f"{name}_bind", cur, nrm, outward, key, width, height, overhang, thick,
                          pos, at[:, 3:3 + NB]))
    # The points next to the edge eased, so the sheet meets its new edge
    # without a crease.
    A = adjacency(len(pos), tris)
    near = (A @ moved.astype(float)) > 0
    near &= ~moved
    for _ in range(6):
        pos = np.where(near[:, None], 0.5 * pos + 0.5 * (A @ pos), pos)
    print("BOUND", name, len(loops), "edge loops")
    return pos, beads


def domes(name, pts, nrms, mkey, r=0.0028, src=None):
    """Small domed studs (eyelets, rivets) at points, standing on normals."""
    P2, T2 = [], []
    nu, nv = 12, 4
    for p0, n in zip(pts, nrms):
        n = n / np.linalg.norm(n)
        t = np.cross(n, [0, 0, 1.0]) if abs(n[2]) < 0.9 else np.cross(n, [1.0, 0, 0])
        t /= np.linalg.norm(t)
        b = np.cross(n, t)
        o = sum(len(x) for x in P2)
        q = [p0 + n * r * 0.7]
        for k in range(1, nv + 1):
            th = (np.pi / 2) * k / nv
            for j in range(nu):
                ph = 2 * np.pi * j / nu
                q.append(p0 + (np.cos(ph) * t + np.sin(ph) * b) * r * np.sin(th) + n * r * 0.7 * np.cos(th))
        tri = [(o, o + 1 + j, o + 1 + (j + 1) % nu) for j in range(nu)]
        for k in range(nv - 1):
            a0, b0 = o + 1 + k * nu, o + 1 + (k + 1) * nu
            for j in range(nu):
                j1 = (j + 1) % nu
                tri += [(a0 + j, b0 + j, b0 + j1), (a0 + j, b0 + j1, a0 + j1)]
        P2.append(np.array(q))
        T2.append(np.array(tri))
    pp, tt = np.vstack(P2), np.vstack(T2)
    cen = np.repeat(np.array(pts), nu * nv + 1, 0)
    if ((pp - cen) * vertex_normals(pp, tt)).sum(1).mean() < 0:
        tt = tt[:, ::-1]
    sp, sw = (P, W) if src is None else src
    _, j = cKDTree(sp).query(pp)
    obj = finish(name, pp, sw[j].astype(float), tt, mkey, 0.0, 0.0, 10 ** 7)
    obj["hides"] = True
    return [obj]


def frame(name, centre, nrm, up, w, h, mkey, r=0.002, corner=0.004, lift=0.0):
    """A buckle frame: a rounded rectangle of rod `r` thick, `w` by `h`,
    standing on a surface at `centre` (normal `nrm`, `up` its long way)."""
    n = nrm / np.linalg.norm(nrm)
    u = up - n * (up @ n)
    u /= np.linalg.norm(u)
    v = np.cross(n, u)
    pts = []
    hw, hh = w / 2 - corner, h / 2 - corner
    for cx, cy, a0 in ((hw, hh, 0), (-hw, hh, np.pi / 2), (-hw, -hh, np.pi), (hw, -hh, 3 * np.pi / 2)):
        for a in np.linspace(a0, a0 + np.pi / 2, 8, endpoint=False):
            pts.append(centre + n * lift + v * (cx + corner * np.cos(a)) + u * (cy + corner * np.sin(a)))
    pts = np.array(pts)
    nr = np.repeat(n[None], len(pts), 0)
    tg = np.roll(pts, -1, 0) - np.roll(pts, 1, 0)
    tg /= np.linalg.norm(tg, axis=1)[:, None]
    out = np.cross(nr, tg)
    if ((pts - pts.mean(0)) * out).sum(1).mean() < 0:
        out = -out
    _, j = cKDTree(P).query(pts)
    return [tube(name, pts, nr, out, mkey, 2 * r, 0.0, r, 2 * r, P, W.astype(float))]


'''
rep('''# ----------------------------------------------------------------- pieces --
NB = len(BONES)''', BIND + '''# ----------------------------------------------------------------- pieces --
NB = len(BONES)''')

# ---- piece(): bind instead of trim.
rep('''budget=None, filled=False, edge=30, slot=True, bridge=False):''',
    '''budget=None, filled=False, edge=30, slot=True, bridge=False, bind=True):''')
rep('''    if not dome and not filled:
        pos = clear_of_skin(pos, lift if clear is None else clear)
    made = [finish(name, pos, at[:, 3:3 + NB], tris, mkey, thick, bevel, budget or (8000 if dome else 3000))]''',
    '''    if not dome and not filled:
        pos = clear_of_skin(pos, lift if clear is None else clear)
    # Every edge bound: in the trim's colour where one is asked, else in the
    # piece's own (a rolled hem). Sheer and painted pieces are left as cut.
    beads = []
    if bind and len(SPEC[mkey]) < 7 and mkey != "ink":
        if trim:
            tkey, w, h, tt = trim
            bspec = (tkey, max(w, 0.005), max(h, 0.0006), 0.0018)
        else:
            bspec = (mkey, 0.0045, 0.0005, 0.0015)
        pos, beads = bind_edges(name, pos, at, tris, bspec[0], bspec[1], bspec[2], bspec[3], thick)
        trim = None
    made = [finish(name, pos, at[:, 3:3 + NB], tris, mkey, thick, bevel, budget or (8000 if dome else 3000))] + beads''')

# ---- girdle: arcs, flare, angles.
rep('''def hull_radius_grid(z0, z1, nu=160, step=0.004, mask=None):''', '''def hull_radius_grid(z0, z1, nu=160, step=0.004, mask=None, angles=None):''')
rep('''    zs = np.arange(z0, z1 + step, step)
    a = np.linspace(0, 2 * np.pi, nu, endpoint=False)
    d = np.stack([np.sin(a), -np.cos(a)], 1)
    m0 = body_pts & (np.abs(Z - (z0 + z1) / 2) < 0.02)''', '''    zs = np.arange(z0, z1 + step, step)
    a = np.linspace(0, 2 * np.pi, nu, endpoint=False) if angles is None else angles
    nu = len(a)
    d = np.stack([np.sin(a), -np.cos(a)], 1)
    m0 = body_pts & (np.abs(Z - (z0 + z1) / 2) < 0.02)''')
rep('''def girdle(name, zfun, width, mkey, lift=0.004, thick=0.004, trim=None, rows=9, nu=160, mask=None, gap=None):''',
    '''def girdle(name, zfun, width, mkey, lift=0.004, thick=0.004, trim=None, rows=9, nu=160, mask=None, gap=None, arc=None, flare=0.0):''')
rep('''    a = np.linspace(0, 2 * np.pi, nu, endpoint=False)
    zc = zfun(a)
    zs, _, R, cxy = hull_radius_grid(zc.min() - width, zc.max() + width, nu, mask=mask)
    off = np.linspace(-width / 2, width / 2, rows)
    pos = np.zeros((rows, nu, 3))
    for k, o in enumerate(off):
        z = zc + o
        r = np.array([np.interp(z[j], zs, R[:, j]) for j in range(nu)])
        pos[k] = np.stack([cxy[0] + (r + lift) * np.sin(a), cxy[1] - (r + lift) * np.cos(a), z], -1)
    for _ in range(3):
        pos = (np.roll(pos, 1, 1) + 2 * pos + np.roll(pos, -1, 1)) / 4
    pos = pos.reshape(-1, 3)
    idx = np.arange(rows * nu).reshape(rows, nu)
    idx = np.c_[idx, idx[:, :1]].ravel()
    tris = idx[grid(rows, nu + 1)]''', '''    a = np.linspace(0, 2 * np.pi, nu, endpoint=False) if arc is None else np.linspace(arc[0], arc[1], nu)
    zc = zfun(a)
    zs, _, R, cxy = hull_radius_grid(zc.min() - width, zc.max() + width, nu, mask=mask, angles=a)
    off = np.linspace(-width / 2, width / 2, rows)
    pos = np.zeros((rows, nu, 3))
    for k, o in enumerate(off):
        z = zc + o
        r = np.array([np.interp(z[j], zs, R[:, j]) for j in range(nu)])
        rl = r + lift + flare * k / (rows - 1)
        pos[k] = np.stack([cxy[0] + rl * np.sin(a), cxy[1] - rl * np.cos(a), z], -1)
    for _ in range(3):
        if arc is None:
            pos = (np.roll(pos, 1, 1) + 2 * pos + np.roll(pos, -1, 1)) / 4
        else:
            pos[:, 1:-1] = (pos[:, :-2] + 2 * pos[:, 1:-1] + pos[:, 2:]) / 4
    pos = pos.reshape(-1, 3)
    idx = np.arange(rows * nu).reshape(rows, nu)
    if arc is None:
        idx = np.c_[idx, idx[:, :1]].ravel()
        tris = idx[grid(rows, nu + 1)]
    else:
        tris = grid(rows, nu)''')
rep('''    edge = np.repeat(width / 2 - np.abs(off), nu)
    at = np.hstack([nor, W[j].astype(float), edge[:, None]])
    made = trimmed(name, pos, at, tris, mkey, thick, 0.0008, trim, budget=10 ** 7)
    for o in made:
        o["hides"] = True
    print("GIRDLE", name)''', '''    edge = np.repeat(width / 2 - np.abs(off), nu)
    if arc is not None:
        run = np.abs(np.diff(a)).mean() * np.mean(R)
        col = np.tile(np.arange(nu), rows)
        edge = np.minimum(edge, np.minimum(col, nu - 1 - col) * run)
    at = np.hstack([nor, W[j].astype(float), edge[:, None]])
    made = trimmed(name, pos, at, tris, mkey, thick, 0.0008, trim, budget=10 ** 7)
    for o in made:
        o["hides"] = True
    print("GIRDLE", name)''')
open(p, 'w', encoding='utf-8').write(s)
print("patched")
