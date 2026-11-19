"""A bending plate's weights fitted to her skin's motion, correctives in (armor-D l6, 17 Nov 2026).

An exact-installed free mesh takes her skin's weights at the closest place (pin_shipped.pin). Plain LBS on those weights
is not what her skin does where she has corrective shapes and driven helpers (her back armpit in a leap: the arm-hang
shapes; her crotch: the hip-flex shapes): the skin goes out through a plate a few mm off it. Here, where the recipe
names it (piece params "bend_fit", set per body through build.json "by_body"), each bending point near the named bones
gets the weights (non-negative, summing to 1, over her bones there) whose LBS best follows the place it should keep: the
same offset off her posed skin, along her posed normal, through every frame of her clips (bodies.clip_source: the
chosen body's). A ridge holds them to her weights; the change is smoothed over the plate, so it fades out at the
region's edge. Pure data -> data: rerunnable from the recipe on any body.

spec (piece params "bend_fit"):
    bones   bone-name prefixes ("upperarm_share_", "thigh_"): a point is fitted when her weights there on them sum to
            at least `min` (default 0.05)
    offer   bone names every fitted point may also take ("spine_04", "clavicle_{s}"; {s} = the point's side, l for x > 0)
    box     optional [[x0, y0, z0], [x1, y1, z1]] (her rest, metres): only points inside are fitted
    lam_mm  the ridge: a weight change of 1.0 costs as much as this rms error in mm (default 3)
    smooth  the change's gaussian over the plate, metres (default 0.008)
    clips   default: every clip of hers the body has (bodies.clip_source); step: frame step (default 1)
    shapes, hold   her worn-rest shapes {name: w} and springs [amount, squash], as wearcheck poses her for the piece:
            set by the ship path from the piece (pose_for); offline, pass them in the spec

    python tools/armor/bend_fit.py <in.gltf> <out.gltf> '<spec json>'   (offline: a copy refitted, for wearcheck --file)
"""
import json
import os
import sys

import numpy as np
from scipy.optimize import nnls
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools", "anim"))

DEF_CLIPS = ("idle_warden", "run_warden", "sword_heavy", "leap")


def her_motion(clips=None, step=1, shapes=None, hold=None):
    """Her skin (helpers on): the Body, her skin's rest points, tris, and per frame (globals, posed points, posed
    normals). As wearcheck poses her for the piece (l7, 17 Nov): `shapes` {name: w} her worn-rest shapes in her rest
    points (kit_build.worn_shapes of a worn_rest piece); `hold` [amount, squash] her springs (None: no springs)."""
    import bodies
    import skin
    bodies.clip_source(skin)
    sk = skin.Skeleton.load(bodies.skeleton_for(skin))
    jig = skin.Jiggle(sk, amount=float(hold[0]), squash=float(hold[1])) if hold is not None else None
    body = skin.Body(sk, [(bodies.glb_for(skin), lambda n: n == "Heroine", "skin")], jig, label="her", helpers=True)
    if shapes:
        import wearcheck
        body.P = body.P + wearcheck.shape_delta(bodies.glb_for(skin), shapes, len(body.P))
    T = body.T
    have = [c for c in (clips or DEF_CLIPS) if (skin.OUT / "clips" / f"{c}.json").exists()]
    frames = []
    for c in have:
        fr = body.frames(body.clip(c))
        for f in range(0, len(fr), step):
            P = body.pose(fr[f])
            frames.append((fr[f], P, skin._normals(P, T)))
    return body, frames, have


def fit(Q, W0, names, spec, motion=None):
    """Q [n, 3] her rest, W0 [n, len(names)] dense weights. Returns (W [n, len(names)], report)."""
    import skin
    min_ = float(spec.get("min", 0.05))
    pre = tuple(spec.get("bones", ()))
    bm = np.array([n.startswith(pre) for n in names]) if pre else np.zeros(len(names), bool)
    sel = W0[:, bm].sum(1) >= min_ if pre else np.ones(len(Q), bool)
    if spec.get("box"):
        lo, hi = np.asarray(spec["box"], float)
        sel &= ((Q >= lo) & (Q <= hi)).all(1)
    rep = {"fitted": int(sel.sum()), "points": len(Q)}
    if not sel.any():
        return W0.copy(), rep
    body, frames, have = motion or her_motion(spec.get("clips"), int(spec.get("step", 1)), spec.get("shapes"), spec.get("hold"))
    rep["clips"], rep["frames"] = have, len(frames)
    sk = body.sk
    P0 = body.P
    N0 = skin._normals(P0, body.T)
    idx = np.nonzero(sel)[0]
    q = Q[idx]
    # her surface under each point: inverse-square blend of her 4 nearest points
    dd, nn = cKDTree(P0).query(q, k=4)
    a = 1.0 / np.maximum(dd, 1e-5) ** 2
    a /= a.sum(1, keepdims=True)
    s0 = (P0[nn] * a[:, :, None]).sum(1)
    n0 = (N0[nn] * a[:, :, None]).sum(1)
    n0 /= np.linalg.norm(n0, axis=1, keepdims=True)
    d = q - s0
    h = (d * n0).sum(1)
    # her skin's blend at those points (dense over sk): bones a point may take
    nb = len(sk.names)
    Ws = np.zeros((len(P0), nb))
    for k in range(body.J.shape[1]):
        np.add.at(Ws, (np.arange(len(P0)), np.minimum(body.J[:, k], nb - 1)), body.W[:, k])
    Wsk = (Ws[nn] * a[:, :, None]).sum(1)                     # [m, nb]
    # targets per frame
    m, F = len(idx), len(frames)
    SQ = np.stack([body.skin_mats(G)[:nb] for G, _, _ in frames]).astype(np.float32)   # [F, nb, 4, 4]
    kds = [cKDTree(P) for _, P, _ in frames]
    sk_of = np.array([sk.index.get(n, -1) for n in names])
    offer = spec.get("offer", [])
    lam = float(spec.get("lam", 1.0))
    clear = float(spec.get("clear_mm", 1.5)) * 1e-3
    need = np.where(h > 0, np.minimum(clear, h), 0.0)
    cands, w0s = [], []
    for r, i in enumerate(idx):
        side = "l" if Q[i, 0] > 0 else "r"
        cand = set(np.nonzero(W0[i] > 1e-4)[0]) | {names.index(sk.names[j]) for j in np.nonzero(Wsk[r] > 0.02)[0] if sk.names[j] in names}
        cand |= {names.index(o.replace("{s}", side)) for o in offer if o.replace("{s}", side) in names}
        cand = np.array(sorted(c for c in cand if sk_of[c] >= 0))
        cands.append(cand)
        w0s.append(W0[i, cand] / max(W0[i, cand].sum(), 1e-12))
    Qh = np.c_[Q[idx], np.ones(m)].astype(np.float32)

    def posed():
        Wd = np.zeros((m, nb), np.float32)
        for r in range(m):
            Wd[r, sk_of[cands[r]]] = ws[r]
        X = np.zeros((F, m, 3), np.float32)
        for t in range(F):
            X[t] = np.einsum("mab,mb->ma", np.einsum("mj,jab->mab", Wd, SQ[t, :, :3, :]), Qh)
        return X

    def gaps(X):
        """Each point's gap off her NEAREST posed skin point (along its normal), per frame; and that skin point."""
        g, v = np.zeros((F, m)), np.zeros((F, m), int)
        for t, (_, P, N) in enumerate(frames):
            _, v[t] = kds[t].query(X[t])
            g[t] = ((X[t] - P[v[t]]) * N[v[t]]).sum(1)
        return g, v
    # her surface under each point (the rest correspondence above), posed, and its normal
    ST, NT = np.zeros((F, m, 3)), np.zeros((F, m, 3))
    for t, (_, P, N) in enumerate(frames):
        ST[t] = (P[nn] * a[:, :, None]).sum(1)
        nt = (N[nn] * a[:, :, None]).sum(1)
        NT[t] = nt / np.linalg.norm(nt, axis=1, keepdims=True)
    ws = []
    for r in range(m):
        # one-sided: the point's gap off her posed skin under it (along its normal) kept >= need in every frame, by the
        # least weight change (active set: the frames that break it, added until none do; nnls holds each as an
        # equality, so the point is kept just at its need there and frames where it stands well off are never pulled)
        cand, w0 = cands[r], w0s[r]
        A = np.einsum("fjab,b->fja", SQ[:, sk_of[cand], :3, :], Qh[r])          # [F, c, 3]
        An = np.einsum("fja,fa->fj", A, NT[:, r])
        sn = (ST[:, r] * NT[:, r]).sum(1)
        w = w0
        act = np.zeros(F, bool)
        for _ in range(8):
            bad = An @ w - sn < need[r] - 1e-5
            if not bad.any():
                break
            act |= bad
            wt = 30.0e3  # (a mm of gap weighs as a weight change of .03)
            Am = np.vstack([wt * An[act], np.sqrt(lam) * np.eye(len(cand)), 1e3 * np.ones((1, len(cand)))])
            ym = np.r_[wt * (sn[act] + need[r] + 2e-4), np.sqrt(lam) * w0, 1e3]
            w, _ = nnls(Am, ym, maxiter=50 * len(cand))
            w /= max(w.sum(), 1e-12)
        ws.append(w)
    # the veto: a point whose change brings it closer to ANY of her (her nearest posed skin point, e.g. her arm's at
    # her armpit, not only the skin under it) than it was and than its need, in any frame, keeps her weights
    g1, _ = gaps(posed())
    ws0 = ws
    ws = w0s
    g0, _ = gaps(posed())
    ws = ws0
    # (veto_mm: the floor a change may not take a point under; default its need. 0: only a change that puts it inside her)
    vfl = need[None] if spec.get("veto_mm") is None else float(spec["veto_mm"]) * 1e-3
    worse = ((g1 < np.minimum(g0, vfl) - 2e-4)).any(0) & bool(spec.get("veto", True))
    rep["vetoed"] = int(worse.sum())
    for r in np.nonzero(worse)[0]:
        ws[r] = w0s[r]
    g1, _ = gaps(posed())
    W = W0.copy()
    for r, i in enumerate(idx):
        W[i] = 0
        W[i, cands[r]] = ws[r]
    # the change smoothed over the plate (a gaussian over every point; unfitted points' change 0), renormalized
    D = W - W0
    sm = float(spec.get("smooth", 0.008))
    if sm > 0:
        kd = cKDTree(Q)
        Ds = np.zeros_like(D)
        nbr = kd.query_ball_point(Q[idx], 2.5 * sm)
        touched = set()
        for r, i in enumerate(idx):
            touched.update(nbr[r])
        touched = np.array(sorted(touched))
        lists = kd.query_ball_point(Q[touched], 2.5 * sm)
        for t_, i in enumerate(touched):
            js = np.array(lists[t_])
            g = np.exp(-0.5 * (np.linalg.norm(Q[js] - Q[i], axis=1) / sm) ** 2)
            Ds[i] = (D[js] * g[:, None]).sum(0) / g.sum()
        D = Ds
    W = np.clip(W0 + D, 0, None)
    W /= np.maximum(W.sum(1, keepdims=True), 1e-12)
    rep["changed"] = int((np.abs(W - W0).max(1) > 1e-3).sum())
    rep["dw_max"] = round(float(np.abs(W - W0).max()), 3)
    g0s, g1s = g0.min(0) * 1000, g1.min(0) * 1000
    rep["gap_min_mm"] = [round(float(g0s.min()), 2), round(float(g1s.min()), 2)]
    rep["under_clear"] = [int((g0s < clear * 1000 - 0.01).sum()), int((g1s < clear * 1000 - 0.01).sum())]
    return W, rep


def refit_gltf(src, dst, spec):
    """Offline: a copy of an installed piece with its bending meshes' weights refitted (rigid shells: their one blend
    kept). Joints: the file's own (a bone it lacks is not offered)."""
    import shutil
    import pin_shipped as pn
    bf, _Gl = pn.bf, pn._Gl
    if os.path.abspath(src) != os.path.abspath(dst):
        g = json.load(open(src))
        for b in g["buffers"]:
            shutil.copyfile(os.path.join(os.path.dirname(src), b["uri"]), os.path.join(os.path.dirname(dst), b["uri"]))
        shutil.copyfile(src, dst)
    G = _Gl(dst)
    g = G.g
    names = [g["nodes"][j]["name"] for j in g["skins"][0]["joints"]]
    rows = []
    for n, m, k, p in pn.prims(G):
        a = p["attributes"]
        if "JOINTS_0" not in a or "skin" not in n:
            continue
        X = G.get(a["POSITION"]).astype(float)
        J, Wt = bf._weights(G, a)
        Dn = np.zeros((len(X), len(names)))
        np.add.at(Dn, (np.repeat(np.arange(len(J)), J.shape[1]), J.ravel()), Wt.ravel())
        rows.append((p, X, Dn))
    Q = np.vstack([r[1] for r in rows])
    W0 = np.vstack([r[2] for r in rows])
    W, rep = fit(Q, W0, names, spec)
    o = 0
    for p, X, Dn in rows:
        Wp = W[o:o + len(X)]
        o += len(X)
        top = np.argsort(-Wp, 1)[:, :8]
        tw = np.take_along_axis(Wp, top, 1)
        tw[tw < 1e-4] = 0
        tw /= np.maximum(tw.sum(1, keepdims=True), 1e-12)
        top[tw <= 0] = 0
        a = p["attributes"]
        jt = g["accessors"][a["JOINTS_0"]]["componentType"]
        jd = np.uint8 if jt == 5121 else np.uint16
        a["JOINTS_0"] = bf._add_acc(G, top[:, :4].astype(jd), jt, "VEC4")
        a["WEIGHTS_0"] = bf._add_acc(G, tw[:, :4].astype(np.float32), 5126, "VEC4")
        a["JOINTS_1"] = bf._add_acc(G, top[:, 4:].astype(jd), jt, "VEC4")
        a["WEIGHTS_1"] = bf._add_acc(G, tw[:, 4:].astype(np.float32), 5126, "VEC4")
    g["buffers"][0]["byteLength"] = len(G.buf) - G.b0
    G.save()
    return rep


if __name__ == "__main__":
    import bodies
    bodies.take(sys.argv)
    print(json.dumps(refit_gltf(sys.argv[1], sys.argv[2], json.loads(sys.argv[3]))))
