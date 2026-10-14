"""Her closed smile's bow dots, cleaned in five whole-face keys of her exported glb (heroine.glb).

WIP (bow solver, 14 October 2026), UNJUDGED. On Doe, Saffron, Moonlit, Fey and Highborn small dark dots sat about
1 mm over her upper lip's border, 10-11 mm over her lips' line, 4-6 mm either side of her mouth's middle, at rest and
in the closed smile. The cause is in the face keys' normals, not their shape: her head's base normals there are
authored (her own face's border fold: points on the fold's underside face back), and each face key's normal delta
was made against them while its shape opens the fold, so on the face a few points that now face the front keep a
normal facing back or down (Doe's 7826 and 9146: 136 deg off their own surface), and their neighbours spike 60-70
deg against their rings (own: 41-45). This step leaves every position alone: in each of the five face keys, on the
bow's window, the points seen from in front (at rest or in smile .8) whose normal is far off the face's own surface
(DEV) or off its ring (LAP) get a new unit normal at rest, filled smoothly from their seen neighbours (started from
the face's surface normal; the set grows by any neighbour the fill leaves spiking), and the key's normal delta there
is rewritten to give it. Nothing else in the glb changes (other keys, faces, the base, every position).
Measured (lap.py's spike, deg, at 7752 9202 7876 9114): 53-66 to 0 at rest, 47-64 to 4-6 in smile .8; its window's
max 10-14 on the five. Left: in the smile, 7983 and 8988 still dip (shade 0.4-0.5 under their ring; was 1.4-1.6),
set by the smile key's own normals there (see POSES): a smile-key or per-face corrective fix, not a face-key one.

    python tools/assets/heroine_face_bow.py IN.glb [OUT.glb]           (run: the five face keys)
    python tools/assets/heroine_face_bow.py --keys IN.glb [OUT.glb]    (run_keys: the last step)

run goes first in the heroine build chain (before heroine_teethshade); run_keys goes LAST, after heroine_smile_lip.run
(whose ease rewrites smile's and mouth_open's normals over the border and makes smile_open's and smile_hold's). Each
does nothing on a glb it has already done (its head's extras say face_bow / face_bow_keys).

run_keys (bow solver r2, 14 October 2026, UNJUDGED): the smile's own normals at 7983/8988 (and 7826/9146) were made
against her head's authored base fold (points under the fold face back), so the smile, every expression and the four
faces run left out (Vixen, Sunborn, Wildling, Hard-won: rest dips 147-166) dipped there. On the same window, positions
untouched, it redoes (_fill: the smooth fill of seen neighbours, as face_fix; a point is redone where any of its poses
spikes past KLAP off its ring or faces back past KNZ): the base at rest; each face key at rest (from the second round
also in each expression at .8 and her laugh, weighed FACE_COMBO_W); each expression key (KEYS_EXPR) at .8 and 1 on all
ten faces; smile_open and smile_hold in her laugh on all ten faces; ROUNDS times, each on the others. A key's normal
is written as its absolute unit normal less the new base, the way Godot blends (base + sum w (key - base), made unit).
Measured (bow2/meas.py, dip / light x100, max over the window on ten faces): rest 85-166 / 61 to 11 / 26; smile .8
41-167 / 81 to 14 / 25; smile 1 75-168 / 79 to 15 / 24; laugh 70-158 / 86 to 25 / 20; open, pucker, snarl, frown (.8,
1) 181 to 14 dark; Saffron's pucker keeps a light spot 59 at 7130/9834 (was 62: its ring's points just outside the
window face back). Left: the creator sliders lips_upper-, mouth_height-, cupids_bow-, lips_forward+, mouth_width+ carry
the same kind of spike at weight 1 (not redone).
"""
import contextlib
import copy
import io
import os
import sys
import tempfile

import numpy as np
from scipy import sparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_seam as hs        # noqa: E402
import heroine_mouth as hmo      # noqa: E402
import heroine_smile_lip as sl   # noqa: E402

FACES = tuple(os.environ.get("FACE_BOW_FACES", "doe,saffron,moonlit,fey,highborn").split(","))
MID = 0.00205                    # (m: her mouth's middle x)
WIN_X = 0.012                    # (m off the middle: the bow's window, either side)
WIN_H = (0.0065, 0.0125)         # (m over her lips' line, on her own head: the window's height)
WIN_Z = 0.08                     # (m: only her face's front)
DEV = float(os.environ.get("FACE_BOW_DEV", "25"))   # (deg: a seen point's normal this far off the face's surface is redone)
LAP = float(os.environ.get("FACE_BOW_LAP", "15"))   # (deg: or this far off its ring's mean)
ITS = int(os.environ.get("FACE_BOW_ITS", "80"))     # (fill passes)
GROW = 4                         # (rounds the redone set may grow by the neighbours a fill leaves spiking)
GROW_LAP = 10                    # (deg: past this, and past what it was, a neighbour joins)
POSES = (({"smile": 0.8}, float(os.environ.get("FACE_BOW_SMILE_W", "0")), True),)
# (besides rest, the poses that pick points to redo: (pose, weight in the fill, whether a point spiking in it is redone).
#  Her closed smile picks points; the fill weighs only rest. The smile cannot be reached from a face key at the four
#  points the smile darkens (7826, 7983, 8988, 9146): the smile key's own normal offset there, as Godot blends it
#  (0.8 x (unit(base + delta) - base)), is longer than 1 and faces back, so no unit face normal turns it to the front.
#  Weighing the smile at 1, .5 or .25 left its dip there 41-52 (x100) all the same and cost rest's spikes 10-20 deg.)
MARK = "face_bow"


def _unit(a):
    return a / (np.linalg.norm(a, axis=1)[:, None] + 1e-20)


def _ang(a, b):
    return np.degrees(np.arccos(np.clip((a * b).sum(-1), -1, 1)))


def mesh(js, binc, hp, names):
    """Her head welded: P, N (per copy), first, inv, Tw (welded triangles), A (welded ring adjacency), line."""
    P = hs._read(js, binc, hp["attributes"]["POSITION"])
    N = hs._read(js, binc, hp["attributes"]["NORMAL"])
    T = hs._read(js, binc, hp["indices"]).astype(np.int64).reshape(-1, 3)
    first, inv = sl._weld(P)
    n, Tw = len(first), inv[T]
    e = np.r_[Tw[:, [0, 1]], Tw[:, [1, 2]], Tw[:, [2, 0]]]
    A = sparse.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)).tocsr()
    A = ((A + A.T) > 0).astype(float)
    line = hmo.lips_line(P, hs._read(js, binc, hp["targets"][names.index("mouth_open")]["POSITION"]))
    return P, N, first, inv, Tw, A, line


def seen(Q, Tw):
    """Welded points on at least one triangle facing the front (+z) in the shape Q."""
    a, b, c = Q[Tw[:, 0]], Q[Tw[:, 1]], Q[Tw[:, 2]]
    fz = np.cross(b - a, c - a)[:, 2]
    v = np.zeros(len(Q), bool)
    v[Tw[fz > 0].ravel()] = True
    return v


def seen_area(Q, Tw):
    """Per welded point: a third of the front-facing (+z) projected area of its triangles."""
    a, b, c = Q[Tw[:, 0]], Q[Tw[:, 1]], Q[Tw[:, 2]]
    fz = 0.5 * np.cross(b - a, c - a)[:, 2]
    ar = np.zeros(len(Q))
    np.add.at(ar, Tw[fz > 0].ravel(), np.repeat(fz[fz > 0], 3) / 3)
    return ar


def face_fix(P, N, first, inv, Tw, A, line, D, DN, poses):
    """One face key: (new normal delta per copy, the welded points redone). poses: (position, normal) offsets added
    to the face for each pose its bow is cleaned in (rest first: zeros). At each redone point the face's normal (the
    base's plus its delta, x) is chosen so every pose's normal there, unit(x + that pose's normal offset), meets the
    smooth fill of its seen neighbours in that pose, weighted by how much of it the front sees in that pose."""
    V = P[first]
    win = (np.abs(V[:, 0] - MID) < WIN_X) & (V[:, 1] - line > WIN_H[0]) & (V[:, 1] - line < WIN_H[1]) & (V[:, 2] > WIN_Z)
    X0 = (N + DN)[first].astype(np.float64)
    S = np.zeros(len(V), bool)
    Ms, Cs, Ws, Ngs, Vis, L0 = [], [], [], [], [], []
    Hard = []
    for dP, dN, pw, hard in poses:
        Q = (P + D + dP)[first]
        C = dN[first].astype(np.float64)
        G = _unit(X0 + C)
        Ng = sl.vnormals(Q, Tw)
        ar = seen_area(Q, Tw)
        vis = ar > 0
        lap = _ang(G, _unit(A @ G))
        if hard:
            S |= win & vis & ((_ang(G, Ng) > DEV) | (lap > LAP))
        Ms.append(A @ sparse.diags(vis.astype(float)))     # (a point's seen neighbours only)
        Cs.append(C); Ws.append(ar * pw); Ngs.append(Ng); Vis.append(vis); L0.append(lap); Hard.append(hard)
    X = X0
    for _ in range(GROW + 1):
        if not S.any():
            break
        X = X0.copy()
        m = np.linalg.norm(X[S], axis=1)
        # (start: the rest surface's own normal where it faces the front)
        X[S] = np.where((Ngs[0][S, 2] > 0)[:, None], Ngs[0][S] * m[:, None], X[S])
        W = np.stack([w[S] for w in Ws]) + 1e-12
        for _ in range(ITS):
            acc = np.zeros((S.sum(), 3))
            for M, C, w in zip(Ms, Cs, W):
                t = _unit(M @ _unit(X + C))[S]              # (this pose's fill target)
                s = np.linalg.norm(X[S] + C[S], axis=1)
                acc += w[:, None] * (s[:, None] * t - C[S])
            X[S] = _unit(acc)                               # (unit: Godot keeps a key's normals as directions only)
        # (a seen neighbour the fill left spiking past GROW_LAP, and past what it was, joins it, and the fill is redone)
        new = np.zeros_like(S)
        for C, vis, l0, hard in zip(Cs, Vis, L0, Hard):
            if not hard:
                continue
            G = _unit(X + C)
            new |= win & vis & ~S & (_ang(G, _unit(A @ G)) > np.maximum(GROW_LAP, l0 + 1))
        if not new.any():
            break
        S |= new
    rows = S[inv]
    out = DN.copy()
    out[rows] = X[inv[rows]] - N[rows]
    return out, np.where(S)[0]


def final_keys(js, chunks, keys):
    """These expression keys' (position, normal) offsets on her head as the build's later steps leave them
    (heroine_mouth.seat raises smile_open's upper lip; heroine_smile_lip eases their normals across her upper lip's
    border): both are run on a copy, here. Each does nothing on a glb it has already been run on."""
    js2, chunks2 = copy.deepcopy(js), dict(chunks)
    fd, tmp = tempfile.mkstemp(suffix=".glb")
    os.close(fd)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            hs._save(tmp, js2, chunks2)
            hmo.seat(tmp, tmp)
            js2, binc2 = hs._load(tmp)
            hm2, hp2 = hmo._prim(js2, "skin_head")
            chunks2 = {i: binc2[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]] for i, bv in enumerate(js2["bufferViews"])}
            if sl.ease(js2, binc2, chunks2, hm2, hp2):
                hs._save(tmp, js2, chunks2)
                js2, binc2 = hs._load(tmp)
                hm2, hp2 = hmo._prim(js2, "skin_head")
    finally:
        os.remove(tmp)
    names = hm2["extras"]["targetNames"]
    out = [(hs._read(js2, binc2, hp2["targets"][names.index(k)]["POSITION"]),
            hs._read(js2, binc2, hp2["targets"][names.index(k)]["NORMAL"])) for k in keys]
    return out


def face_bow(js, binc, chunks, hm, hp):
    """The five face keys' normals redone on the bow; False if already done."""
    ex = hm.setdefault("extras", {})
    if ex.get(MARK):
        return False
    names = ex["targetNames"]
    P, N, first, inv, Tw, A, line = mesh(js, binc, hp, names)
    z = np.zeros_like(P)
    keys = sorted({k for p, _, _ in POSES for k in p})
    fk = dict(zip(keys, final_keys(js, chunks, keys)))
    # (as Godot blends: each key's normals are made unit on import, the pose's normal is the base's plus the weighted
    #  differences, made unit)
    fk = {k: (dP, _unit(N + dN) - N) for k, (dP, dN) in fk.items()}
    poses = [(z, z, 1.0, True)] + [(sum(w * fk[k][0] for k, w in p.items()), sum(w * fk[k][1] for k, w in p.items()), pw, hard)
                                   for p, pw, hard in POSES]
    done = {}
    for f in FACES:
        t = hp["targets"][names.index("face_" + f)]
        D, DN = hs._read(js, binc, t["POSITION"]), hs._read(js, binc, t["NORMAL"])
        new, S = face_fix(P, N, first, inv, Tw, A, line, D, DN, poses)
        hs._set(js, chunks, t["NORMAL"], new)
        done[f] = len(S)
    ex[MARK] = True
    print("FACE_BOW: bow normals redone on %s (lips' line y %.4f)" % (", ".join("%s %d" % kv for kv in done.items()), line))
    return True


def run(path, out=None):
    js, binc = hs._load(path)
    chunks = {i: binc[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]] for i, bv in enumerate(js["bufferViews"])}
    hm, hp = hmo._prim(js, "skin_head")
    if face_bow(js, binc, chunks, hm, hp):
        hs._save(out or path, js, chunks)
    elif out and out != path:
        open(out, "wb").write(open(path, "rb").read())


# ---- the last step: the base's and every key's normals on the bow, as Godot blends them ----
FACES_ALL = ("doe", "saffron", "moonlit", "fey", "highborn", "vixen", "sunborn", "wildling", "hardwon")
KEYS_EXPR = tuple(k for k in os.environ.get("FACE_BOW_KEYS", "smile,mouth_open,pucker,snarl,frown").split(",") if k)
EXPR_W = tuple(float(v) for v in os.environ.get("FACE_BOW_EXPR_W", "0.8,1").split(","))   # (each expression key is redone at these weights, on every face)
LAUGH = (("mouth_open", 0.6), ("smile", 0.8), ("smile_open", 0.8), ("smile_hold", 0.48))
# (smile_open and smile_hold are only ever seen in her laugh (People.cs: smile_open = smile when her lips part,
#  smile_hold = smile x mouth_open), so theirs are redone in it, on every face, each with the keys before it)
KLAP = float(os.environ.get("FACE_BOW_KLAP", "15"))   # (deg: a seen point this far off its ring's mean, in any pose, is redone)
KNZ = float(os.environ.get("FACE_BOW_KNZ", "0"))      # (or whose normal faces further back than this (z), in any pose)
ROUNDS = int(os.environ.get("FACE_BOW_ROUNDS", "5"))   # (rounds: faces, expressions, the laugh's helpers, each on the others)
FACE_COMBO_W = float(os.environ.get("FACE_BOW_COMBO_W", "0.5"))   # (a face's fill: its expressions' weight against its rest)
MARK_KEYS = "face_bow_keys"


def _fill(poses, Tw, A, win, K0, its=ITS):
    """One key's absolute unit normals K (welded) redone where any of its poses spikes. poses: (Q welded shape, R, wk):
    the pose's normal is unit(R + wk K) (R: the base's, the face's and the other keys' share). Returns (K, redone, the
    worst ring angle over the poses after)."""
    pre = []
    S = np.zeros(len(K0), bool)
    for pose in poses:
        Q, R, wk = pose[:3]
        pw = pose[3] if len(pose) > 3 else 1.0
        Ng = sl.vnormals(Q, Tw)
        vis = seen_area(Q, Tw) > 0
        M = (A @ sparse.diags(vis.astype(float))).tocsr()
        G0 = _unit(R + wk * K0)
        lap0 = _ang(G0, _unit(M @ G0))
        S |= win & vis & ((lap0 > KLAP) | (G0[:, 2] < KNZ))
        vis = vis.astype(float)
        pre.append((Q, R, wk, Ng, vis * pw, M, G0, lap0))

    def worst(K):
        return max(_ang(_unit(R + wk * K), _unit(M @ _unit(R + wk * K)))[win & (vis > 0)].max(initial=0)
                   for Q, R, wk, Ng, vis, M, G0, lap0 in pre)
    K = K0
    for _ in range(GROW + 1):
        if not S.any():
            break
        K = K0.copy()
        acc = np.zeros((S.sum(), 3))
        for Q, R, wk, Ng, vis, M, G0, lap0 in pre:      # (start: each pose's own surface where it faces front)
            st = np.where((Ng[S, 2] > 0)[:, None], Ng[S], G0[S])
            s = np.linalg.norm(R[S] + wk * K0[S], axis=1)
            acc += (vis[S] + 1e-3)[:, None] * (s[:, None] * st - R[S]) / wk
        K[S] = _unit(acc)
        MS = [M[np.where(S)[0]] for Q, R, wk, Ng, vis, M, G0, lap0 in pre]
        for _ in range(its):
            acc = np.zeros((S.sum(), 3))
            for (Q, R, wk, Ng, vis, M, G0, lap0), Ms in zip(pre, MS):
                t = _unit(Ms @ _unit(R + wk * K))
                s = np.linalg.norm(R[S] + wk * K[S], axis=1)
                acc += (vis[S] + 1e-3)[:, None] * (s[:, None] * t - R[S]) / wk
            K[S] = _unit(acc)
        new = np.zeros_like(S)
        for Q, R, wk, Ng, vis, M, G0, lap0 in pre:
            G = _unit(R + wk * K)
            new |= win & (vis > 0) & ~S & (_ang(G, _unit(M @ G)) > np.maximum(GROW_LAP, lap0 + 1))
        if not new.any():
            break
        S |= new
    return K, S, worst(K)


def bow_keys(js, binc, chunks, hm, hp):
    """Her head's base normals, then each face key's, each expression key's and her laugh's two helpers', redone on the
    bow's window where they spike; False if already done."""
    ex = hm.setdefault("extras", {})
    if ex.get(MARK_KEYS):
        return False
    names = ex["targetNames"]
    P, N, first, inv, Tw, A, line = mesh(js, binc, hp, names)
    V = P[first]
    win = (np.abs(V[:, 0] - MID) < WIN_X) & (V[:, 1] - line > WIN_H[0]) & (V[:, 1] - line < WIN_H[1]) & (V[:, 2] > WIN_Z)
    Nw = N[first].astype(np.float64)
    z = np.zeros_like(Nw)
    # (the base: her own face at rest)
    Nn, S0, _ = _fill([(V, z, 1.0)], Tw, A, win, Nw)
    done = {"base": int(S0.sum())}
    Nr = N.copy()
    Nr[S0[inv]] = Nn[inv[S0[inv]]]
    if S0.any():
        hs._set_dense(js, chunks, hp["attributes"]["NORMAL"], Nr)
    fk = ["face_" + f for f in FACES_ALL if "face_" + f in names]
    hk = [k for k, _ in LAUGH if k not in KEYS_EXPR and k in names]
    tg = {k: hp["targets"][names.index(k)] for k in fk + [k for k in KEYS_EXPR if k in names] + hk}
    D = {k: hs._read(js, binc, t["POSITION"])[first] for k, t in tg.items()}
    DN = {k: hs._read(js, binc, t["NORMAL"]) for k, t in tg.items()}
    K = {k: _unit(Nn + DN[k][first]) for k in tg}   # (each key's absolute normal, welded, as Godot makes it)
    Sall = {k: np.zeros(len(V), bool) for k in tg}
    lw = dict(LAUGH)

    def redo(k, poses_of, starts):
        """From each start, filled: the one that spikes least in its poses."""
        best = None
        for K0 in starts:
            Kk, S, sc = _fill(poses_of(K0), Tw, A, win, K0)
            if best is None or sc < best[0]:
                best = (sc, Kk, S)
        K[k] = best[1]
        Sall[k] |= best[2]

    def laugh_of(Df, Kf, skip):
        """Her laugh on a face, every key but skip at its weight: (shape, normal share)."""
        Q, R = V + Df, Kf.copy()
        for j, wj in LAUGH:
            if j != skip and j in K:
                Q, R = Q + wj * D[j], R + wj * (K[j] - Nn)
        return Q, R

    def faces():                # (her own face, then each face key: shape, normal)
        return [(np.zeros_like(V), Nn)] + [(D[k], K[k]) for k in fk]
    ex_keys = [k for k in KEYS_EXPR if k in tg]
    for rnd in range(ROUNDS):
        for k in fk:            # (each face: at rest; from the second round also in each expression and her laugh)
            def fposes(K0, k=k):
                out = [(V + D[k], z, 1.0, 1.0)]
                if rnd:
                    out += [(V + D[k] + EXPR_W[0] * D[e], EXPR_W[0] * (K[e] - Nn), 1.0, FACE_COMBO_W) for e in ex_keys]
                    Q, R = laugh_of(D[k], Nn, None)
                    out.append((Q, R - Nn, 1.0, FACE_COMBO_W))
                return out
            redo(k, fposes, (_unit(Nw + DN[k][first]), _unit(Nn + DN[k][first])) if not rnd else (K[k],))
        for k in ex_keys:       # (each at EXPR_W on every face)
            redo(k, lambda K0, k=k: [(V + Df + w * D[k], Kf - w * Nn, w) for Df, Kf in faces() for w in EXPR_W],
                 (_unit(Nw + DN[k][first]), _unit(Nn + DN[k][first])) if not rnd else (K[k],))
        for k in hk:            # (the laugh's helpers on every face, the other keys at their laugh weights)
            def lposes(K0, k=k):
                out = []
                for Df, Kf in faces():
                    Q, R = laugh_of(Df, Kf, k)
                    out.append((Q + lw[k] * D[k], R - lw[k] * Nn, lw[k]))
                return out
            redo(k, lposes, (_unit(Nw + DN[k][first]), _unit(Nn + DN[k][first])) if not rnd else (K[k],))
    for k in tg:
        rows = (Sall[k] | S0)[inv]
        out = DN[k].copy()
        out[rows] = K[k][inv[rows]] - Nr[rows]
        hs._set(js, chunks, tg[k]["NORMAL"], out)
        done[k] = int(Sall[k].sum())
    ex[MARK_KEYS] = done
    print("FACE_BOW_KEYS: bow normals redone (points): %s" % ", ".join("%s %d" % kv for kv in done.items()))
    return True


def run_keys(path, out=None):
    """The last step of her build (after heroine_smile_lip.run)."""
    js, binc = hs._load(path)
    chunks = {i: binc[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]] for i, bv in enumerate(js["bufferViews"])}
    hm, hp = hmo._prim(js, "skin_head")
    if bow_keys(js, binc, chunks, hm, hp):
        hs._save(out or path, js, chunks)
    elif out and out != path:
        open(out, "wb").write(open(path, "rb").read())


if __name__ == "__main__":
    a = sys.argv[1:]
    f = run
    if a and a[0] == "--keys":
        f, a = run_keys, a[1:]
    f(a[0] if a else hmo.GLB, a[1] if len(a) > 1 else None)
