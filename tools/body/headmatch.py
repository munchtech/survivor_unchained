"""Stage 2: our subdivided MakeHuman head laid onto her shipped head (A's HeroineHead), and the 1:1 correspondence.

Her shipped head is this same MakeHuman head, subdivided once (subdiv.py) and placed by a similarity (scale s, turn
R, move t: tools/assets/heroine_head.py `place`); only points within 5 cm of SPLIT were fitted after (and later
passes reshaped her ears). So:
  solve_place:  ICP at a free scale, then Umeyama on the points that coincide; it converges when the unmoved points
                agree to float precision (their residual is reported);
  correspond:   A's welded head points -> ours. Anchors: the points that coincide (< 1e-6 m, one to one); the rest
                by topology: each of A's triangles is half of one of our quads, so a triangle with two points known
                names its third among the quads on that edge (the nearest when two could). Every triangle is then
                checked to be in one quad of ours.
Coordinates: MakeHuman's world (Blender: z up, front -y); A's glb is y up: to_blender / to_gltf.
"""
import numpy as np
from scipy.spatial import cKDTree


def to_blender(P):
    P = np.asarray(P, float)
    return np.stack([P[:, 0], -P[:, 2], P[:, 1]], 1)


def to_gltf(P):
    P = np.asarray(P, float)
    return np.stack([P[:, 0], P[:, 2], -P[:, 1]], 1)


def s_split(P):
    """Above SPLIT is her head: under her chin in front, under her skull behind (heroine_head.py)."""
    return P[:, 2] - (1.625 + 0.27 * (P[:, 1] + 0.02))


def place(P, sim):
    s, R, T = sim
    return s * np.asarray(P) @ R.T + T


def umeyama(A, B):
    ma, mb = A.mean(0), B.mean(0)
    C = (B - mb).T @ (A - ma) / len(A)
    U, D, Vt = np.linalg.svd(C)
    sg = np.diag([1, 1, np.sign(np.linalg.det(U @ Vt))])
    R = U @ sg @ Vt
    s = np.trace(np.diag(D) @ sg) / ((A - ma) ** 2).sum(1).mean()
    return s, R, mb - s * R @ ma


def rough_place(P, HP, iters=60):
    """ICP at a free scale: our head's top 25 cm onto A's head points (from a start by heights)."""
    top = P[:, 2].max()
    src = P[P[:, 2] > top - 0.25]
    s = (HP[:, 2].max() - np.percentile(HP[:, 2], 5)) / (src[:, 2].max() - np.percentile(src[:, 2], 5))
    R = np.eye(3)
    T = np.array([0.0, HP[:, 1].mean() - s * src[:, 1].mean(), HP[:, 2].max() - s * top])
    tree = cKDTree(HP)
    for _ in range(iters):
        d, k = tree.query(place(src, (s, R, T)))
        m = d < np.percentile(d, 80)
        s, R, T = umeyama(src[m], HP[k[m]])
    return s, R, T


def refine_place(P_of_sim, HP, sim, rounds=4):
    """Umeyama on the fixed points (> 5 cm above SPLIT) nearest A's, the half that agree best; P_of_sim(sim) gives
    our subdivided points for a placement (the subdivision's smoothing depends on it near the eyes)."""
    tree = cKDTree(HP)
    for _ in range(rounds):
        P = P_of_sim(sim)
        Pp = place(P, sim)
        fx = s_split(Pp) > 0.05
        d, k = tree.query(Pp[fx])
        m = d <= max(np.percentile(d, 50), 1e-9)
        sim = umeyama(P[fx][m], HP[k[m]])
    P = P_of_sim(sim)
    Pp = place(P, sim)
    fx = s_split(Pp) > 0.05
    d, _ = tree.query(Pp[fx])
    stats = {"fixed_points": int(fx.sum()), "coincide_1e-6": int((d < 1e-6).sum()), "coincide_1e-5": int((d < 1e-5).sum()),
             "coincide_median_m": float(np.median(d[d < 1e-5])), "coincide_max_m": float(d[d < 1e-5].max()),
             "moved_after_max_m": float(d.max())}
    return sim, P, stats


def weld_rep(P, tol=1e-7):
    """Each point's representative (the first point at its place)."""
    q = np.round(np.asarray(P, float) / tol).astype(np.int64)
    _, first, inv = np.unique(q, axis=0, return_index=True, return_inverse=True)
    return first[inv.ravel()]


def _adj(T, n):
    """Neighbours per point (triangles' edges; for quads, edges and diagonals)."""
    nb = [set() for _ in range(n)]
    for t in T:
        for i in range(len(t)):
            for j in range(len(t)):
                if i != j:
                    nb[t[i]].add(int(t[j]))
    return nb


def correspond(Pp, F2, HPw, HT):
    """A's welded head points HPw [n,3] (their triangles HT) -> our points (Pp placed, quads F2). Returns
    (match [n] our point per A point, head_quads [our quad indices], info).

    Anchors are the points that coincide. Then, best first: an unknown point of A whose known neighbours (in A's
    triangles) map to points of ours is matched to the one point of ours that neighbours all their images (in our
    quads, edges or diagonals) and is not taken; the most constrained first, the nearest breaking a tie."""
    from heapq import heappush, heappop
    n = len(HPw)
    tree = cKDTree(Pp)
    d, k = tree.query(HPw)
    match = np.where(d < 1e-6, k, -1)
    u, c = np.unique(match[match >= 0], return_counts=True)
    for x in u[c > 1]:
        match[match == x] = -1
    anchors = int((match >= 0).sum())
    nbA = _adj(HT, n)
    nbO = _adj(F2, len(Pp))
    taken = set(match[match >= 0].tolist())

    def cands(i):
        known = [match[j] for j in nbA[i] if match[j] >= 0]
        if len(known) < 2:
            return len(known), []
        cs = set(nbO[known[0]])
        for q in known[1:]:
            cs &= nbO[q]
        cs -= taken
        return len(known), sorted(cs)
    heap = []

    def push(i):
        nk, cs = cands(i)
        if nk >= 2 and cs:
            dd = sorted(float(np.linalg.norm(Pp[c_] - HPw[i])) for c_ in cs)
            margin = (dd[1] - dd[0]) if len(dd) > 1 else 1.0
            heappush(heap, (-nk, -min(margin, 1.0), dd[0], i))
    for i in range(n):
        if match[i] < 0:
            push(i)
    while heap:
        _, _, _, i = heappop(heap)
        if match[i] >= 0:
            continue
        nk, cs = cands(i)
        if not cs:
            continue
        best = min(cs, key=lambda c_: (np.linalg.norm(Pp[c_] - HPw[i]), c_))
        match[i] = best
        taken.add(best)
        for j in nbA[i]:
            if match[j] < 0:
                push(j)
    info = {"anchors": anchors, "unmatched": int((match < 0).sum())}
    quad_of = {}
    for qi, f in enumerate(F2):
        for i in range(4):
            for j in range(i + 1, 4):
                quad_of.setdefault((min(f[i], f[j]), max(f[i], f[j])), []).append(qi)
    used = {}
    bad = 0
    for t in HT:
        m = match[t]
        if (m < 0).any():
            bad += 1
            continue
        q = [qi for qi in quad_of.get((min(m[0], m[1]), max(m[0], m[1])), []) if set(m.tolist()) <= set(F2[qi].tolist())]
        if len(q) != 1:
            bad += 1
        else:
            used[q[0]] = used.get(q[0], 0) + 1
    info["tris_not_in_a_quad"] = bad
    info["quads"] = len(used)
    info["quads_not_two_tris"] = int(sum(1 for v in used.values() if v != 2))
    u, c = np.unique(match[match >= 0], return_counts=True)
    info["many_to_one"] = int((c > 1).sum())
    ok = match >= 0
    info["moved_max_m"] = float(np.linalg.norm(Pp[match[ok]] - HPw[ok], axis=1).max())
    return match, np.array(sorted(used)), info
