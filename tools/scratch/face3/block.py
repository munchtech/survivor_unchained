rows = np.arange(len(L0))[hit]
Bm = sp.coo_matrix((bary[rows].ravel(), (np.repeat(np.arange(len(rows)), 3), loc[tri[rows]].ravel())), shape=(len(rows), n)).tocsr()
wa = weights(len(L0))[rows]
K_LM, K_BEND, K_HOLD = 4.0, 0.05, 6.0
# 2a. Across her face (x and z, as the camera sees her): every landmark
# where the picture has it, her surface bent as little as can be.
M = K_LM * Bm.T @ sp.diags(wa) @ Bm + K_BEND * (Lap.T @ Lap) + K_HOLD * sp.diags(hold) + 1e-9 * sp.eye(n)
solve = spl.factorized(M.tocsc())
d = np.zeros((n, 3))
for k in (0, 2):
    d[:, k] = solve(K_LM * Bm.T @ (wa * (Lr - L0)[rows, k]))
got = Bm @ d
print("ACROSS: landmarks within %.2f mm (rms)" % (1000 * np.sqrt((((got - (Lr - L0)[rows])[:, [0, 2]]) ** 2).sum(1).mean())))
# 2b. In depth: each point of her skin brought to the picture's surface
# straight in front of or behind it (the picture's face as a height field
# over hers), from her brows to her chin, ear to ear, where she faces the
# camera; not round her eyes (her eyeballs and lids are moved whole, 3)
# nor in her mouth or nostrils. As deep as hers at her face's edges, where
# it meets her skull (the picture's depth there is least sure).
eye_c = []
for ring in (EYE_A, EYE_B):
    sx = np.sign(L0[ring, 0].mean())
    _ev = (member["helper-l-eye"] | member["helper-r-eye"]) & (np.sign(P[:, 0]) == sx)
    eye_c.append((P[_ev].mean(0), np.linalg.norm(P[_ev] - P[_ev].mean(0), axis=1).mean()))
Pa = P[idx] + d
oval2d = Lr[OVAL][:, [0, 2]]
cen = oval2d.mean(0)
in_face = inside(cen + (oval2d - cen) * 0.93, Pa[:, [0, 2]])
ring_ = in_face & ~inside(cen + (oval2d - cen) * 0.78, Pa[:, [0, 2]])
near_eye = np.min([np.linalg.norm(P[idx] - c, axis=1) - r for c, r in eye_c], 0)
mouth_open = inside(Lr[INNER_LIPS][:, [0, 2]], Pa[:, [0, 2]])
brow_z = Lr[BROWS, 2].max()
facing = np.clip(-Nv[idx, 1], 0, 1)
wb = (in_face & ~mouth_open) * smooth01((facing - 0.3) / 0.3) * smooth01((near_eye - 0.006) / 0.004) \
    * (1 - smooth01((Pa[:, 2] - brow_z - 0.015) / 0.02)) * (1 - hold)
hy = np.full(n, np.nan)
y0 = Lr[:, 1].min() - 0.1
for i in np.where(wb > 0.01)[0]:
    r = SURF.ray_cast(Vector((Pa[i, 0], y0, Pa[i, 2])), Vector((0, 1, 0)), 1.0)
    if r[0] is not None:
        hy[i] = r[0][1]
dy = hy - Pa[:, 1]
ok = np.isfinite(dy) & (np.abs(dy) < 0.015)
off = np.median(dy[ok & ring_]) if (ok & ring_).sum() > 20 else np.median(dy[ok])
dy = np.where(ok, dy - off, 0.0)
wb = wb * ok
Mb = sp.diags(wb) + 0.5 * (Lap.T @ Lap) + K_HOLD * sp.diags(hold) + 1e-9 * sp.eye(n)
d[:, 1] = spl.spsolve(Mb.tocsc(), wb * dy)
res = (d[:, 1] - dy)[wb > 0.5]
print("DEPTH: %d of her points on the picture's surface (its edge %.1f mm off hers); within %.2f mm (rms), %.1f mm the most moved"
      % ((wb > 0.5).sum(), 1000 * off, 1000 * np.sqrt((res ** 2).mean()), 1000 * np.abs(d[:, 1]).max()))
D = np.zeros((NV, 3))
D[idx] = d


# ------------------------------------------------------------ 3. eyes --
def sphere(Q):
    c = Q.mean(0)
    return c, np.linalg.norm(Q - c, axis=1).mean()


eyes_all = member["helper-l-eye"] | member["helper-r-eye"]
for ring in (EYE_A, EYE_B):
    sx = np.sign(L0[ring, 0].mean())
    eye = eyes_all & (np.sign(P[:, 0]) == sx)
    c0, r0 = sphere(P[eye])
    rad = np.linalg.norm(P - c0, axis=1)
    # (her eyeball moves as the skin of her lids round it has: across and in depth)
    rim = BODY & (rad < r0 + 0.006) & (rad > r0 - 0.002)
    shift = D[rim].mean(0)
    c1 = c0 + shift
    D[eye] = shift
    for jn in ("joint-l-eye", "joint-r-eye", "joint-l-eye-target", "joint-r-eye-target"):
        j = member.get(jn, np.zeros(NV, bool)) & (np.sign(P[:, 0]) == sx)
        D[j] = shift
    # (and every point of her lids and socket as far off it as it was, the
    # nearer the more so: her lids lie on her eyeball)
    lid = BODY & (rad < r0 + 0.007)
    off0 = rad[lid] - r0
    Q = P[lid] + D[lid]
    u = (Q - c1) / np.linalg.norm(Q - c1, axis=1)[:, None]
    lay = c1 + u * (r0 + off0)[:, None]
    t = 1 - smooth01((off0 - 0.003) / 0.004)
    D[lid] += (lay - Q) * t[:, None]
    print("EYE at x %+.3f: moved %.1f mm (%.1f deeper); %d points of lid and socket laid on it"
          % (sx * 0.03, 1000 * np.linalg.norm(shift), 1000 * shift[1], lid.sum()))
