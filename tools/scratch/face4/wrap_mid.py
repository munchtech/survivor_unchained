# ------------------------------------------------------------ 2. placed --
n_l = min(len(L0), len(Lt))
wc = np.zeros(n_l)
wc[[i for i in CORE if i < n_l]] = 1.0
wc *= hit[:n_l] & ok_t[:n_l]
use = wc > 0
s_, R_, t_ = umeyama(Lt[:n_l][use], L0[:n_l][use], wc[use])
TVh = s_ * TV @ R_.T + t_
Lt = s_ * Lt @ R_.T + t_
_turn = math.degrees(math.acos(min(1, (np.trace(R_) - 1) / 2)))
print("PLACED: scaled %.4f, turned %.1f deg; landmarks %.1f mm from hers (rms, eyes nose mouth)" % (
    s_, _turn, 1000 * np.sqrt((wc[use] * ((Lt[:n_l][use] - L0[:n_l][use]) ** 2).sum(1)).sum() / wc[use].sum())))
for nm, g in (("oval", OVAL), ("lips", LIPS), ("eyes", EYE_A + EYE_B), ("brows", BROWS), ("nose", NOSE)):
    g = [i for i in g if i < n_l and hit[i] and ok_t[i]]
    dd = (Lt - L0)[g]
    print("MOVES %-6s %.1f mm (rms): across %.1f, up %.1f, in depth %.1f" % (
        nm, 1000 * np.sqrt((dd ** 2).sum(1).mean()), 1000 * np.sqrt((dd[:, 0] ** 2).mean()), 1000 * np.sqrt((dd[:, 2] ** 2).mean()),
        1000 * np.sqrt((dd[:, 1] ** 2).mean())))
shape_ob.data.vertices.foreach_set("co", TVh.ravel())
shape_ob.data.update()
TBVH = BVHTree.FromObject(shape_ob, bpy.context.evaluated_depsgraph_get())
TTREE = cKDTree(TVh)

# Where TRELLIS's head is hair, not skin (its colours: unlike her cheeks'
# and forehead's): her skull lies under it, a little in (HAIR_DEPTH).
HAIR_DEPTH = float(os.environ.get("WRAP_HAIR_DEPTH", "0.005"))
_ca = paint_ob.data.color_attributes[0]
_cols = np.zeros(len(_ca.data) * 4)
_ca.data.foreach_get("color", _cols)
_cols = _cols.reshape(-1, 4)[:, :3]
if _ca.domain == "CORNER":
    _vi = np.zeros(len(paint_ob.data.loops), int)
    paint_ob.data.loops.foreach_get("vertex_index", _vi)
    _acc = np.zeros((len(TV), 3))
    np.add.at(_acc, _vi, _cols)
    _cnt = np.bincount(_vi, minlength=len(TV))
    _cols = _acc / np.maximum(_cnt, 1)[:, None]
_skin_at = [i for i in (50, 280, 151, 108, 337, 9, 205, 425) if i < n_l and ok_t[i]]
_skin = np.median(_cols[TTREE.query(Lt[_skin_at])[1]], 0)
_lum = _cols @ [0.3, 0.59, 0.11]
_chroma = _cols / (_cols.sum(1)[:, None] + 1e-6)
_sk_ch = _skin / _skin.sum()
_d = np.linalg.norm(_chroma - _sk_ch, axis=1) * 6 + np.abs(np.log((_lum + 0.01) / (_skin @ [0.3, 0.59, 0.11] + 0.01)))
HAIR_T = float(os.environ.get("WRAP_HAIR_T", "0.6"))
_hair = (_d > HAIR_T).astype(float)
# (smoothed over 4 mm, and never her brows or anything below them in front)
_nb = TTREE.query_ball_point(TVh, 0.004 / max(s_, 1e-9) * s_)
HAIR = np.array([_hair[k].mean() for k in _nb])
_brow_zone = (TVh[:, 2] < L0[BROWS, 2].max() + 0.012) & (TVh[:, 1] < L0[[234, 454], 1].mean())
HAIR[_brow_zone] = 0.0
print("HAIR: %.0f%% of TRELLIS's head (skin %s)" % (100 * (HAIR > 0.5).mean(), np.round(_skin, 3)))

# ------------------------------------------------------------ 3. laid on it --
chin_z = L0[152, 2]
brow_z = L0[BROWS, 2].max()
region = BODY & (P[:, 2] > chin_z - 0.09)
idx = np.where(region)[0]
n = len(idx)
loc = -np.ones(NV, int)
loc[idx] = np.arange(n)
Fr = F[region[F].all(1)]
e = loc[np.vstack([Fr[:, [0, 1]], Fr[:, [1, 2]], Fr[:, [2, 0]]])]
Adj = sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)).tocsr()
Adj = ((Adj + Adj.T) > 0).astype(float)
Lap = sp.eye(n) - sp.diags(1 / np.maximum(np.asarray(Adj.sum(1)).ravel(), 1)) @ Adj
LTL = (Lap.T @ Lap).tocsr()
ear_x = np.abs(L0[[234, 454], 0]).max()
ear_y = L0[[234, 454], 1].mean()
ear_top = L0[[234, 454], 2].mean() + 0.025
Pi = P[idx]
# Held: her neck below her jaw (her body's, and what she wears there), and
# her nape behind her ears (where TRELLIS's head had its hair tied).
hold = np.max([smooth01((chin_z - 0.035 - Pi[:, 2]) / 0.04),
               smooth01((Pi[:, 1] - ear_y - 0.02) / 0.03) * smooth01((ear_top - 0.03 - Pi[:, 2]) / 0.03)], 0)
# Her ears are carried along (bent as little as can be), not laid on its ears.
ears = smooth01((np.abs(Pi[:, 0]) - ear_x + 0.004) / 0.006) * smooth01((Pi[:, 1] - ear_y + 0.016) / 0.008) \
    * smooth01((Pi[:, 2] - L0[2, 2] + 0.02) / 0.008) * smooth01((ear_top + 0.012 - Pi[:, 2]) / 0.008)
# Her eyes: each eye's opening made the shape of TRELLIS's (an affine map,
# across her face, of her lids' landmarks onto its; moved in depth as its
# lids lie), her lids and socket carried with it, her eyeball moved whole
# (4). Her mouth's inside only carried along.
eye_c, eye_map = [], []
goal = np.zeros((n, 3))
wgoal = np.zeros(n)
for ring in (EYE_A, EYE_B):
    sx = np.sign(L0[ring, 0].mean())
    _ev = (member["helper-l-eye"] | member["helper-r-eye"]) & (np.sign(P[:, 0]) == sx)
    c0 = P[_ev].mean(0)
    r0 = np.linalg.norm(P[_ev] - c0, axis=1).mean()
    rg = [i for i in ring if ok_t[i] and hit[i]]
    src, dst = L0[rg][:, [0, 2]], Lt[rg][:, [0, 2]]
    Xa = np.c_[src, np.ones(len(src))]
    M = np.linalg.lstsq(Xa, dst, rcond=None)[0]                       # (3 x 2: dst = [x z 1] M)
    dy = float(np.median(Lt[rg, 1] - L0[rg, 1]))
    eye_c.append((c0, r0))
    eye_map.append((M, dy))

    def mapped(Q, M=M, dy=dy):
        out = Q.copy()
        out[:, [0, 2]] = np.c_[Q[:, [0, 2]], np.ones(len(Q))] @ M
        out[:, 1] += dy
        return out
    dist = np.linalg.norm(Pi - c0, axis=1) - r0
    w = 1 - smooth01((dist - 0.004) / 0.009)
    mine = w > wgoal
    goal[mine] = (mapped(Pi) - Pi)[mine]
    wgoal = np.maximum(wgoal, w)
    A2 = M[:2].T
    print("EYE at x %+.3f: its opening %.2f wide and %.2f tall as hers, tilted %+.1f deg; %.1f mm %s" % (
        sx * 0.03, np.linalg.norm(A2[:, 0]), np.linalg.norm(A2[:, 1]), math.degrees(math.atan2(A2[1, 0], A2[0, 0])),
        1000 * abs(dy), "deeper" if dy > 0 else "further out"))
near_eye = np.min([np.linalg.norm(Pi - c, axis=1) - r for c, r in eye_c], 0)
mouth_in = inside(L0[INNER_LIPS][:, [0, 2]], Pi[:, [0, 2]]) & (Pi[:, 1] > L0[INNER_LIPS, 1].min() + 0.002)
wsurf = (1 - hold) * (1 - ears) * smooth01((near_eye - 0.008) / 0.006) * ~mouth_in
# Landmarks: her nose's and lips' (her eyes have their own map; her face's
# outline and brows are left to the surface: MediaPipe reads the one off a
# soft edge, and TRELLIS's brows are hair standing off its skin).
lm_w = np.zeros(n_l)
lm_w[[i for i in NOSE if i < n_l]] = 1.2
lm_w[[i for i in LIPS if i < n_l]] = 1.6
rows = np.arange(n_l)[hit[:n_l] & ok_t[:n_l] & (lm_w > 0)]
Bm = sp.coo_matrix((bary[rows].ravel(), (np.repeat(np.arange(len(rows)), 3), loc[tri[rows]].ravel())), shape=(len(rows), n)).tocsr()
wa = lm_w[rows]
Lgoal = Lt[rows]
L0r = (P[tri[rows]] * bary[rows][:, :, None]).sum(1)
D = np.zeros((n, 3))
K_LM, K_HOLD, K_EYE = 3.0, 20.0, 30.0
I3 = sp.identity(3, format="csr")
cranium = Pi[:, 2] > brow_z + 0.02


def solve(Q, Nq, ws, k_bend):
    """Her points' moves: onto the surface (point to plane, and a little
    point to point), landmarks to landmarks, her eyes' openings to theirs,
    bent as little as can be, held where held."""
    # (unknowns: every point's x, then every point's y, then z)
    Nc = sp.hstack([sp.diags(Nq[:, k]) for k in range(3)]).tocsr()          # (n x 3n: each point's move along its normal)
    r = ((Q - Pi) * Nq).sum(1)
    A = Nc.T @ sp.diags(ws) @ Nc + 0.05 * sp.kron(I3, sp.diags(ws)) + K_LM * sp.kron(I3, Bm.T @ sp.diags(wa) @ Bm) \
        + k_bend * sp.kron(I3, LTL) + K_HOLD * sp.kron(I3, sp.diags(hold)) + K_EYE * sp.kron(I3, sp.diags(wgoal)) \
        + 1e-8 * sp.identity(3 * n)
    b = Nc.T @ (ws * r) + 0.05 * np.concatenate([ws * (Q - Pi)[:, k] for k in range(3)]) \
        + K_LM * np.concatenate([Bm.T @ (wa * (Lgoal - L0r)[:, k]) for k in range(3)]) \
        + K_EYE * np.concatenate([wgoal * goal[:, k] for k in range(3)])
    x = spl.spsolve(A.tocsc(), b)
    return x.reshape(3, n).T


Floc = loc[Fr]
flip = None
for it, k_bend in enumerate((60.0, 25.0, 10.0, 5.0, 2.5, 1.5, 1.0, 0.7)):
    X = Pi + D
    Nx = vertex_normals(X, Floc)
    if (Nx[:, 1][(wsurf > 0.5) & ~cranium] < 0).mean() < 0.5:
        Nx = -Nx
    Q = X.copy()
    Nq = Nx.copy()
    ws = wsurf.copy()
    reach = np.where(cranium, 0.04, 0.015)
    cand = []
    for i in np.where(wsurf > 0.01)[0]:
        best = None
        for sgn in (1.0, -1.0):
            hit_ = TBVH.ray_cast(Vector(X[i]), Vector(sgn * Nx[i]), float(reach[i]))
            if hit_[0] is not None and (best is None or hit_[3] < best[3]):
                best = hit_
        cand.append((i, best))
    if flip is None:
        # (TRELLIS's faces may be wound inward: its normals turned to face out as hers do)
        flip = np.median([np.dot(b_[1][:], Nx[i]) for i, b_ in cand if b_ is not None]) < 0
        print("TRELLIS's normals %s" % ("turned out (they were wound inward)" if flip else "face out"))
    for i, b_ in cand:
        if b_ is None:
            ws[i] = 0
            continue
        nq = -np.array(b_[1][:]) if flip else np.array(b_[1][:])
        if np.dot(nq, Nx[i]) < 0.6:          # (a surface facing another way: not hers to lie on)
            ws[i] = 0
            continue
        q = np.array(b_[0][:])
        hq = HAIR[TTREE.query(q)[1]]
        Q[i], Nq[i] = q - nq * HAIR_DEPTH * hq, nq
    D = solve(Q, Nq, ws, k_bend)
    res = (((Pi + D - Q) * Nq).sum(1))[ws > 0.5]
    print("ICP %d (bend %.1f): %d of her points on its surface, %.2f mm off it (rms), %.2f the most; moved up to %.1f mm" % (
        it, k_bend, (ws > 0.5).sum(), 1000 * np.sqrt((res ** 2).mean()), 1000 * np.abs(res).max(), 1000 * np.linalg.norm(D, axis=1).max()))
got = Bm @ (Pi + D)
print("LANDMARKS within %.2f mm (rms)" % (1000 * np.sqrt(((got - Lgoal) ** 2).sum(1).mean())))
DD = np.zeros((NV, 3))
DD[idx] = D


# ------------------------------------------------------------- 4. eyes --
eyes_all = member["helper-l-eye"] | member["helper-r-eye"]
for (c0, r0), (M, dy), ring in zip(eye_c, eye_map, (EYE_A, EYE_B)):
    sx = np.sign(L0[ring, 0].mean())
    eye = eyes_all & (np.sign(P[:, 0]) == sx)
    # (her eyeball moved whole as the map moves its middle: never stretched)
    c1 = c0.copy()
    c1[[0, 2]] = np.r_[c0[[0, 2]], 1.0] @ M
    c1[1] += dy
    shift = c1 - c0
    DD[eye] = shift
    for jn in ("joint-l-eye", "joint-r-eye", "joint-l-eye-target", "joint-r-eye-target"):
        j = member.get(jn, np.zeros(NV, bool)) & (np.sign(P[:, 0]) == sx)
        DD[j] = shift
    # (and every point of her lids and socket as far off it as it was, the
    # nearer the more so: her lids lie on her eyeball)
    rad = np.linalg.norm(P - c0, axis=1)
    lid = BODY & (rad < r0 + 0.007)
    off0 = rad[lid] - r0
    Ql = P[lid] + DD[lid]
    u = (Ql - c1) / np.linalg.norm(Ql - c1, axis=1)[:, None]
    lay = c1 + u * (r0 + off0)[:, None]
    t = 1 - smooth01((off0 - 0.003) / 0.004)
    DD[lid] += (lay - Ql) * t[:, None]
    print("EYEBALL at x %+.3f: moved %.1f mm (%.1f deeper); %d points of lid and socket laid on it"
          % (sx * 0.03, 1000 * np.linalg.norm(shift), 1000 * shift[1], lid.sum()))
body_pts = np.where(BODY)[0]
tree = cKDTree(P[body_pts])
for gname in ("helper-l-eyelashes-1", "helper-l-eyelashes-2", "helper-r-eyelashes-1", "helper-r-eyelashes-2", "helper-hair",
              "joint-mouth", "joint-jaw", "joint-head", "joint-head-2", "joint-l-upperlid", "joint-l-lowerlid", "joint-r-upperlid",
              "joint-r-lowerlid"):
    g = member.get(gname)
    if g is None or not g.any():
        continue
    _, nn = tree.query(P[g], k=4)
    DD[g] = DD[body_pts[nn]].mean(1)
_mouth = DD[tri[INNER_LIPS]].mean((0, 1))
for gname in ("helper-upper-teeth", "helper-lower-teeth", "helper-tongue"):
    DD[member[gname]] = _mouth

