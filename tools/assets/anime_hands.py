"""Her hands fitted to the skeleton, from the mesh alone (numpy, no Blender):
the wrist and elbow set in the middle of her arm, the hand turned at the
wrist to lie along the skeleton's hand, each finger's joints on the line
through the middle of that finger, and the hand's weights from those lines.

The skeleton's bones keep their own directions (the animations turn them
from there); only where the joints sit is hers."""
import numpy as np

FINGERS = ('index', 'middle', 'ring', 'pinky')
# Where a finger's middle and end joints fall between its knuckle and its
# tip (the lengths of the human finger's bones).
PHALANX = {'index': (0.50, 0.79), 'middle': (0.505, 0.80), 'ring': (0.49, 0.795), 'pinky': (0.49, 0.76)}


def smooth01(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def cut(V, M, o, u, a):
    """Where the mesh's edges cross the plane (p - o).u = a: the points, and
    which outline each is on (points joined by a face are one outline).
    M = (edges, polygon-edge pairs)."""
    E, PE = M
    s = (V - o) @ u
    s1, s2 = s[E[:, 0]], s[E[:, 1]]
    m = (s1 - a) * (s2 - a) < 0
    ei = np.where(m)[0]
    t = (a - s1[ei]) / (s2[ei] - s1[ei])
    pts = V[E[ei, 0]] + t[:, None] * (V[E[ei, 1]] - V[E[ei, 0]])
    pos = -np.ones(len(E), int)
    pos[ei] = np.arange(len(ei))
    rows = PE[m[PE[:, 1]]]
    rows = rows[np.argsort(rows[:, 0], kind='stable')]
    parent = np.arange(len(ei))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for i in np.where(rows[1:, 0] == rows[:-1, 0])[0]:
        a_, b_ = find(pos[rows[i, 1]]), find(pos[rows[i + 1, 1]])
        if a_ != b_: parent[a_] = b_
    lab = np.array([find(i) for i in range(len(ei))], dtype=int)
    return pts, lab


def outlines(pts, lab):
    """Each outline: (lo, hi, centre) of its points."""
    out = []
    for l in np.unique(lab):
        q = pts[lab == l]
        if len(q) < 3: continue
        lo, hi = q.min(0), q.max(0)
        out.append((lo, hi, (lo + hi) / 2))
    return out


def rotate(A, o, axis, ang):
    """Rows of A turned about the line through o along axis, by ang (per row)."""
    k = axis / np.linalg.norm(axis)
    d = A - o
    c, s = np.cos(ang)[:, None], np.sin(ang)[:, None]
    return o + d * c + np.cross(k, d) * s + np.outer(d @ k, k) * (1 - c)


def centre_arm(V, M, P, side, sx, log=print):
    """The elbow and the wrist in the middle of her arm (the skeleton's
    joints, scaled to her, sit on its line, not hers); the wrist where the
    arm is thinnest near where the skeleton has it."""
    ux = np.array([sx, 0.0, 0.0])
    def section(p, da=0.0):
        ol = [o for o in outlines(*cut(V, M, p, ux, da)) if np.linalg.norm((o[2] - p)[1:]) < 0.07]
        return min(ol, key=lambda o: np.linalg.norm((o[2] - p)[1:])) if ol else None
    e = P[f'lowerarm_{side}']
    c = section(e)[2]
    P[f'lowerarm_{side}'] = np.array([e[0], c[1], c[2]])
    w = P[f'hand_{side}']
    best = None
    for da in np.arange(-0.02, 0.0151, 0.0025):
        o = section(w, da)
        if o is None: continue
        ext = o[1] - o[0]
        if best is None or ext[1] * ext[2] < best[0]:
            best = (ext[1] * ext[2], da, o[2])
    _, da, c = best
    P[f'hand_{side}'] = np.array([w[0] + sx * da, c[1], c[2]])
    log(f'{side} elbow {np.round(e, 3)} -> {np.round(P[f"lowerarm_{side}"], 3)}; wrist {np.round(w, 3)} -> {np.round(P[f"hand_{side}"], 3)}')


def bend(V, pivot, have, want, sx, lo, hi):
    """Turn what lies past pivot (along the arm) from direction have to
    direction want, about pivot: fully past hi, not at all before lo, a
    smooth bend between. Returns the pivot, axis and per-vertex angle."""
    ux = np.array([sx, 0.0, 0.0])
    d = V - pivot
    a = d @ ux
    arm = (a > lo - 0.05) & (np.linalg.norm(d[:, 1:], axis=1) < 0.15)
    h = have / np.linalg.norm(have)
    t = want / np.linalg.norm(want)
    axis = np.cross(h, t)
    s = np.linalg.norm(axis)
    if s < 1e-6:
        return pivot, ux, np.zeros(len(V))
    ang = np.arctan2(s, h @ t)
    m = smooth01((a - lo) / (hi - lo)) * arm
    return pivot, axis / s, ang * m


def straighten_forearm(V, P, want, side, sx, log=print):
    """Her forearm (elbow to wrist, the middles of her arm) turned at the
    elbow to lie along the skeleton's."""
    e, w = P[f'lowerarm_{side}'], P[f'hand_{side}']
    o, axis, ang = bend(V, e, w - e, want, sx, -0.03, 0.03)
    log(f'{side} forearm turned {np.degrees(np.abs(ang).max()):.1f} deg at the elbow')
    return o, axis, ang


def straighten(V, P, target, side, sx, log=print):
    """Her hand turned at the wrist so that her fingers (their middle, seen
    from the wrist) lie along the skeleton's (target: the direction of its
    middle finger)."""
    W0 = P[f'hand_{side}']
    ux = np.array([sx, 0.0, 0.0])
    d = V - W0
    a = d @ ux
    arm = (a > -0.06) & (np.linalg.norm(d[:, 1:], axis=1) < 0.15)
    reach = a[arm].max()
    F = V[arm & (a > 0.55 * reach)]           # the fingers (the thumb stops short)
    dh = F.mean(0) - W0
    o, axis, ang = bend(V, W0, dh, target, sx, -0.02, 0.015)
    log(f'{side} hand turned {np.degrees(np.abs(ang).max()):.1f} deg at the wrist')
    return o, axis, ang


def fit_fingers(V, M, P, side, sx, log=print):
    """Each finger's joints on the line through the middle of that finger
    (its outline in sections across the hand, followed from the fingertip
    back to where it joins its neighbour or the palm), the knuckle a little
    before the web, the others at the proportions of a human finger."""
    W0 = P[f'hand_{side}']
    ux = np.array([sx, 0.0, 0.0])
    a = (V - W0) @ ux
    arm = (a > -0.06) & (np.linalg.norm((V - W0)[:, 1:], axis=1) < 0.15)
    reach = a[arm].max()
    tracks, live = [], []
    for aa in np.arange(reach - 0.0005, 0.02, -0.0015):
        ol = [o for o in outlines(*cut(V, M, W0, ux, aa))
              if abs(o[2][2] - W0[2]) < 0.07 and abs(o[2][1] - W0[1]) < 0.12 and o[1][1] - o[0][1] < 0.03]
        used, still = set(), []
        for t in live:
            _, y, z, _ = t[-1]
            cand = [(abs(o[2][1] - y) + abs(o[2][2] - z), i) for i, o in enumerate(ol)
                    if i not in used and abs(o[2][1] - y) < 0.0045 and abs(o[2][2] - z) < 0.006]
            if not cand: continue                   # joined the palm (or a neighbour)
            _, i = min(cand)
            used.add(i); still.append(t)
            t.append((aa, ol[i][2][1], ol[i][2][2], ol[i][1][1] - ol[i][0][1]))
        for i, o in enumerate(ol):
            if i in used: continue
            t = [(aa, o[2][1], o[2][2], o[1][1] - o[0][1])]
            tracks.append(t); still.append(t)
        live = still
    # The four fingers: the four that reach furthest (the thumb stops short),
    # index to little finger across the hand (the thumb's side is in front).
    tracks = [t for t in tracks if t[0][0] - t[-1][0] > 0.02]
    tracks = sorted(tracks, key=lambda t: -t[0][0])[:4]
    tracks = sorted(tracks, key=lambda t: np.mean([r[1] for r in t]))
    track = dict(zip(FINGERS, tracks))
    out = {}
    for f in FINGERS:
        R = np.array(track[f])
        tip, web = R[0, 0] + 0.00075, R[-1, 0]
        line = R[(R[:, 0] < tip - 0.006)]
        py = np.polyfit(line[:, 0], line[:, 1], 1)
        pz = np.polyfit(line[:, 0], line[:, 2], 1)
        at = (lambda py, pz: lambda aa: np.array([W0[0] + sx * aa, np.polyval(py, aa), np.polyval(pz, aa)]))(py, pz)
        out[f] = dict(tip=tip, web=web, at=at, rows=R)
    # The knuckles: a finger leaves the palm some way before the web between
    # the fingers (the web is skin); the knuckle line from the skeleton's
    # hand, where it sits relative to her webs.
    for f in FINGERS:
        o = out[f]
        L = o['tip'] - o['web']
        k = o['web'] - 0.22 * L
        # The knuckle's height: the middle of the palm's thickness there.
        kn = o['at'](k)
        pts, _ = cut(V, M, W0, ux, k)
        near = pts[(np.abs(pts[:, 1] - kn[1]) < 0.005) & (np.abs(pts[:, 2] - W0[2]) < 0.07)]
        if len(near) >= 2:
            kn[2] = (near[:, 2].min() + near[:, 2].max()) / 2
        p2, p3 = PHALANX[f]
        span = o['tip'] - k
        P[f'{f}_01_{side}'] = kn
        P[f'{f}_02_{side}'] = o['at'](k + p2 * span)
        P[f'{f}_03_{side}'] = o['at'](k + p3 * span)
        P[f'{f}_04_leaf_{side}'] = o['at'](o['tip'] - 0.004)
        log(f'{side} {f}: knuckle {k:.3f} web {o["web"]:.3f} tip {o["tip"]:.3f} (from the wrist)')
    return out


def fit_thumb(V, P, side, sx, log=print):
    """The thumb: the part of the hand in front of and below the index
    finger, its joints at a human thumb's proportions from its root by the
    wrist to its tip, each in the middle of the thumb there."""
    wrist = P[f'hand_{side}']
    ind = [P[f'index_0{i}_{side}'] for i in (1, 2, 3)] + [P[f'index_04_leaf_{side}']]
    k1 = ind[0]
    def seg_dist(X, a, b):
        ab = b - a
        t = np.clip((X - a) @ ab / max(ab @ ab, 1e-12), 0, 1)
        return np.linalg.norm(X - (a + t[:, None] * ab), axis=1)
    di = np.min([seg_dist(V, ind[i], ind[i + 1]) for i in range(3)], axis=0)
    T = V[(V[:, 0] * sx > wrist[0] * sx + 0.004) & (V[:, 0] * sx < ind[-1][0] * sx) &
          ((V[:, 0] * sx < k1[0] * sx) | (di > 0.011)) &
          (V[:, 1] < k1[1] - 0.004) & (np.abs(V[:, 2] - wrist[2]) < 0.09)]
    if len(T) < 8:
        log(f'{side} thumb not found ({len(T)})')
        return
    dw = np.linalg.norm(T - wrist, axis=1)
    base = T[dw < np.quantile(dw, 0.2)].mean(0)
    tipv = T[np.argmax(np.linalg.norm(T - base, axis=1))]
    names = [f'thumb_01_{side}', f'thumb_02_{side}', f'thumb_03_{side}', f'thumb_04_leaf_{side}']
    for c, t in zip(names, (0.0, 0.45, 0.76, 0.94)):
        p = base + (tipv - base) * t
        m = np.linalg.norm(T - p, axis=1) < 0.009
        P[c] = (T[m].min(0) + T[m].max(0)) / 2 if (m.sum() >= 3 and t > 0) else p
    log(f'{side} thumb {np.round(base, 3)} -> {np.round(tipv, 3)} ({len(T)} vertices)')


def hand_weights(V, P, side, sx):
    """Weights for the hand from its joint lines: every vertex rides the
    digit (or palm) it is nearest, and along it the bone it is on, blended
    across each joint. Returns (the vertices, how much the new weights
    replace the old there, {bone: weights})."""
    ux = np.array([sx, 0.0, 0.0])
    W0, E0 = P[f'hand_{side}'], P[f'lowerarm_{side}']
    d = V - W0
    a = d @ ux
    idx = np.where((a > -0.045) & (np.linalg.norm(d[:, 1:], axis=1) < 0.13))[0]
    X = V[idx]
    chains = []
    for f in FINGERS:
        tip = P[f'{f}_04_leaf_{side}'] + (P[f'{f}_04_leaf_{side}'] - P[f'{f}_03_{side}']) / max(1e-6, np.linalg.norm(P[f'{f}_04_leaf_{side}'] - P[f'{f}_03_{side}'])) * 0.01
        chains.append(([E0, W0, P[f'{f}_01_{side}'], P[f'{f}_02_{side}'], P[f'{f}_03_{side}'], tip],
                       [f'lowerarm_{side}', f'hand_{side}', f'{f}_01_{side}', f'{f}_02_{side}', f'{f}_03_{side}'],
                       [0.012, 0.007, 0.0045, 0.0035]))
    t4 = P[f'thumb_04_leaf_{side}']
    tip = t4 + (t4 - P[f'thumb_03_{side}']) / max(1e-6, np.linalg.norm(t4 - P[f'thumb_03_{side}'])) * 0.01
    chains.append(([E0, W0, P[f'thumb_01_{side}'], P[f'thumb_02_{side}'], P[f'thumb_03_{side}'], tip],
                   [f'lowerarm_{side}', f'hand_{side}', f'thumb_01_{side}', f'thumb_02_{side}', f'thumb_03_{side}'],
                   [0.012, 0.009, 0.005, 0.004]))
    D, S = [], []
    for pts, bones, betas in chains:
        best_d = np.full(len(X), 9.0); best_s = np.zeros(len(X))
        acc = 0.0
        for i in range(len(pts) - 1):
            p0, p1 = pts[i], pts[i + 1]
            ab = p1 - p0; L = np.linalg.norm(ab)
            t = np.clip((X - p0) @ ab / (L * L), 0, 1)
            dd = np.linalg.norm(X - (p0 + t[:, None] * ab), axis=1)
            m = dd < best_d
            best_d[m] = dd[m]; best_s[m] = acc + t[m] * L
            acc += L
        D.append(best_d); S.append(best_s)
    D = np.array(D); S = np.array(S)
    q = np.exp(-(D - D.min(0)) / 0.001)
    q /= q.sum(0)
    out = {}
    for c, (pts, bones, betas) in enumerate(chains):
        joints = np.cumsum([0] + [np.linalg.norm(pts[i + 1] - pts[i]) for i in range(len(pts) - 1)])[1:len(bones)]
        # joints[j] = arc length at the joint between bones[j] and bones[j+1]
        s = S[c]
        up = [smooth01((s - joints[j] + betas[j]) / (2 * betas[j])) for j in range(len(bones) - 1)]
        for b in range(len(bones)):
            lo = up[b - 1] if b > 0 else np.ones(len(X))
            hi = up[b] if b < len(bones) - 1 else np.zeros(len(X))
            w = q[c] * (lo - hi)
            out[bones[b]] = out.get(bones[b], 0) + w
    blend = smooth01((a[idx] + 0.045) / 0.02)
    return idx, blend, out
