"""Stage 5: weights as build steps. Every rule here is one function; the numbers are RULES below.

1 map      MakeHuman's CC0 weights (rigs/standard/weights.default.json, 163 bones) onto our primary bones by
           skeleton.json "mh" (spine05..01 -> spine_01..05, neck01+02 -> neck_01, neck03 -> neck_02, clavicle +
           shoulder01 -> clavicle, upperarm01/02 -> upperarm, ..., toes -> ball, root + pelvis.L/R -> pelvis, the
           face's bones -> Head); every MakeHuman bone is mapped exactly once (checked);
2 mirror   made exactly symmetric on the base mesh (each point and its mirror: the mean of its weights and its
           mirror's, sides swapped);
3 subdiv   through the subdivision (the same sparse matrix as the points);
4 chains   a chain bone's weight shared along its chain by each point's parameter t along the bone (0 head,
           1 tail), smooth hats over the nodes (smoothstep between neighbours: a partition of one);
5 shares   at the shoulder, elbow, hip and knee: of a point's blend between the bones above and below the joint
           (a above, b below, r = b / (a + b)), the share takes f = 4 r (1 - r) of it (all at an even blend, none
           where one side has it all), both sides giving in proportion; at the elbow, hip and knee none on the
           crease (the side the bend folds into), eased out over `reach` metres from the joint's line;
6 points   the elbow's olecranon and the knee's patella: on the side away from the crease, a patch round the
           joint's line (full within `half` degrees of straight behind / in front, eased out by `fade`; along the
           bone within `feather` metres of the joint) whose share weight goes to the point bone;
7 muscles  delt, trap, pec, lat, scap, glute: each takes `amount` of its PARENT's weight over its muscle (a soft
           ball round its tail on the skin, its own side only): bound where its parent was, so it moves nothing
           until a driver moves it (neutral at rest and in every pose the v1 poser makes);
8 breast   the breast's weight shared with breast_tip by t from its base to its tip;
9 cap      at most 8 influences (the smallest dropped), normalised.
"""
import fnmatch

import numpy as np
import scipy.sparse as sp
from scipy.spatial import cKDTree

RULES = {
    "upperarm": [("upperarm_twist_01", 0.0), ("upperarm_twist_02", 0.25), ("upperarm_twist_03", 0.5),
                 ("upperarm_twist_04", 0.75), ("upperarm", 1.0)],
    "lowerarm": [("lowerarm", 0.0), ("lowerarm_twist_01", 0.4), ("lowerarm_twist_02", 0.8)],
    "thigh": [("thigh_twist_01", 0.0), ("thigh_twist_02", 0.5), ("thigh", 1.0)],
    "calf": [("calf", 0.0), ("calf_twist_01", 0.4), ("calf_twist_02", 0.8)],
    # joint: (above, below chain, share, (crease bone, the sign of its Z toward the crease), crease reach m)
    "shares": [("shoulder", ["clavicle"], "upperarm", "upperarm_share", None, 0.0),
               ("elbow", "upperarm", "lowerarm", "lowerarm_share", ("lowerarm", 1.0), 0.035),
               ("hip", ["pelvis"], "thigh", "thigh_share", ("thigh", -1.0), 0.035),
               ("knee", "thigh", "calf", "calf_share", ("calf", 1.0), 0.035)],
    # point: (bone, its share, the joint's lower bone, side (+1 the crease's, -1 away), half deg, fade deg, feather m)
    "points": [("lowerarm_point", "lowerarm_share", "lowerarm", -1.0, 20.0, 40.0, 0.03),
               ("calf_point", "calf_share", "calf", -1.0, 25.0, 45.0, 0.04)],
    # muscle: (bone, amount of its parent's weight, ball radius at full, fade m) round the bone's tail on the skin
    "muscles": [("delt", 0.5, 0.035, 0.04), ("trap", 0.5, 0.03, 0.035), ("pec", 0.5, 0.04, 0.04),
                ("lat", 0.5, 0.04, 0.05), ("scap", 0.5, 0.04, 0.04), ("glute", 0.5, 0.05, 0.05)],
    "breast_tip": [0.2, 0.8],      # t from base to tip: none of it to the tip below 0.2, all above 0.8
    "cap": 8,
}


def smooth01(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def swap_side(n):
    if n.endswith("_l"):
        return n[:-2] + "_r"
    if n.endswith("_r"):
        return n[:-2] + "_l"
    return n


def mh_face_bones(mh_rig):
    """MakeHuman's head and every bone under it (the face): all to our Head."""
    kids = {}
    for k, v in mh_rig.items():
        kids.setdefault(v["parent"], []).append(k)
    out, st = [], ["head"]
    while st:
        b = st.pop()
        out.append(b)
        st.extend(kids.get(b, []))
    return out


def map_mh(skel, mh_rig, mh_w, nV, names):
    """Step 1: MakeHuman's weights as [nV, our bones] by skeleton.json "mh"."""
    owner = {}
    for d in skel["bones"]:
        if "mh" not in d:
            continue
        for s, X in (("l", "L"), ("r", "R")) if "{s}" in d["name"] else (("", ""),):
            n = d["name"].replace("{s}", s)
            pats = mh_face_bones(mh_rig) if d["mh"] == "face" else [p.replace("{X}", X) for p in d["mh"]]
            for p in pats:
                for b in sorted(mh_w):
                    if fnmatch.fnmatchcase(b, p):
                        assert b not in owner, (b, owner.get(b), n)
                        owner[b] = n
    missing = sorted(set(mh_w) - set(owner))
    assert not missing, missing
    idx = {n: i for i, n in enumerate(names)}
    r, c, v = [], [], []
    for b in sorted(mh_w):
        j = idx[owner[b]]
        for i, w in mh_w[b]:
            r.append(int(i)), c.append(j), v.append(float(w))
    W = sp.csr_matrix((v, (r, c)), shape=(nV, len(names))).toarray()
    return W, owner


def mirror_pairs(P, tol=1e-4):
    """Each point's mirror (x -> -x) within tol, else -1."""
    d, k = cKDTree(P).query(P * np.array([-1.0, 1, 1]))
    return np.where(d < tol, k, -1)


def symmetrize(W, pairs, names):
    """Step 2: the mean of each point's weights and its mirror's (sides swapped)."""
    sw = np.array([names.index(swap_side(n)) for n in names])
    out = W.copy()
    ok = pairs >= 0
    out[ok] = 0.5 * (W[ok] + W[pairs[ok]][:, sw])
    return out


def seg_t(P, h, t):
    d = t - h
    return ((P - h) @ d) / max(float(d @ d), 1e-12)


def chain_split(W, P, names, ends, side):
    """Step 4: each chain's primary bone's weight over its nodes."""
    idx = {n: i for i, n in enumerate(names)}
    for chain in ("upperarm", "lowerarm", "thigh", "calf"):
        nodes = RULES[chain]
        prim = idx[f"{chain}_{side}"]
        w = W[:, prim].copy()
        h, t = ends[f"{chain}_{side}"]
        tt = np.clip(seg_t(P, h, t), 0, 1)
        ts = np.array([x for _, x in nodes])
        share = np.zeros((len(P), len(nodes)))
        for i in range(len(nodes)):
            up = smooth01((tt - ts[i - 1]) / (ts[i] - ts[i - 1])) if i > 0 else np.ones(len(P))
            dn = 1 - smooth01((tt - ts[i]) / (ts[i + 1] - ts[i])) if i + 1 < len(nodes) else np.ones(len(P))
            share[:, i] = np.where(tt <= ts[i], up, dn)
        share /= share.sum(1, keepdims=True)
        W[:, prim] = 0
        for k, (n, _) in enumerate(nodes):
            W[:, idx[f"{n}_{side}"]] += w * share[:, k]
    return W


def chain_cols(names, chain, side):
    if isinstance(chain, list):
        return [names.index(f"{c}_{side}" if f"{c}_{side}" in names else c) for c in chain]
    return [names.index(f"{n}_{side}") for n, _ in RULES[chain]]


def shares(W, P, names, frames, side):
    """Step 5."""
    for joint, above, below, share, crease, reach in RULES["shares"]:
        A = chain_cols(names, above, side)
        B = chain_cols(names, below, side)
        a, b = W[:, A].sum(1), W[:, B].sum(1)
        m = a + b
        r = np.where(m > 1e-9, b / np.maximum(m, 1e-12), 0.0)
        f = 4 * r * (1 - r)
        if crease is not None:
            G = frames[f"{crease[0]}_{side}"]
            c = (P - G[:3, 3]) @ (crease[1] * G[:3, 2])
            f = f * (1 - smooth01(c / reach))
        W[:, A] *= (1 - f)[:, None]
        W[:, B] *= (1 - f)[:, None]
        W[:, names.index(f"{share}_{side}")] += f * m
    return W


def points(W, P, names, frames, side):
    """Step 6."""
    for pt, share, lower, way, half, fade, feather in RULES["points"]:
        G = frames[f"{lower}_{side}"]
        y, z = G[:3, 1], G[:3, 2]
        rel = P - G[:3, 3]
        along = rel @ y
        rad = rel - along[:, None] * y
        cosang = (rad @ (way * z)) / np.maximum(np.linalg.norm(rad, axis=1), 1e-9)
        ang = np.degrees(np.arccos(np.clip(cosang, -1, 1)))
        patch = (1 - smooth01((ang - half) / fade)) * (1 - smooth01(np.abs(along) / feather))
        s_, p_ = names.index(f"{share}_{side}"), names.index(f"{pt}_{side}")
        W[:, p_] += W[:, s_] * patch
        W[:, s_] *= 1 - patch
    return W


def muscles(W, P, names, parents, tails, side):
    """Step 7."""
    for m, amount, r0, fade in RULES["muscles"]:
        n = f"{m}_{side}"
        j = names.index(n)
        p = parents[j]
        sx = 1.0 if side == "l" else -1.0
        own = smooth01(P[:, 0] * sx / 0.01 + 0.5)
        ball = 1 - smooth01((np.linalg.norm(P - tails[n], axis=1) - r0) / fade)
        t = amount * ball * own * W[:, p]
        W[:, p] -= t
        W[:, j] += t
    return W


def breast(W, P, names, ends, side):
    """Step 8."""
    b, t = names.index(f"breast_{side}"), names.index(f"breast_tip_{side}")
    h = ends[f"breast_{side}"][0]
    tip = ends[f"breast_tip_{side}"][1]
    lo, hi = RULES["breast_tip"]
    k = smooth01((seg_t(P, h, tip) - lo) / (hi - lo))
    W[:, t] += W[:, b] * k
    W[:, b] *= 1 - k
    return W


def cap(W, k=8):
    """Step 9: the k largest (the lower joint index first on a tie), normalised: (J [n,k], Wk [n,k])."""
    W = np.where(W < 1e-6, 0.0, W)
    order = np.argsort(-W, axis=1, kind="stable")[:, :k]
    Wk = np.take_along_axis(W, order, 1)
    Wk = Wk / np.maximum(Wk.sum(1, keepdims=True), 1e-12)
    J = np.where(Wk > 0, order, 0)
    return J, Wk
