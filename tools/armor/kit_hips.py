"""The kit's lower half (lane D, 16 Nov 2026): recipes for tools/armor/kit_build.py (build.json "module": "kit_hips").

    python tools/armor/kit_build.py kit_brief     (first: the belt rides over it)
    python tools/armor/kit_build.py kit_belt      (reads kit_bodice.glb and kit_brief.glb: it rides over both)

brief  a high-cut gunmetal brief: her own skin patch (subdivided once) cut by a field (waist top under the belt, leg
       lines high at the hip, cheeky at the back), smoothed (bridges the cleft), pushed out to `clear`, a shell with a
       gold rolled rim on every edge.
belt   a wide brown leather belt (a ruled band over the bodice's lower edge and the brief), gold studs, a big square
       gold buckle, two keeper tabs with gold rings; hanging from it, rigid by CLEARANCE: a V-pointed front tasset
       (centre keel, gold rim), hip plates and back plates each side (gold rim, a raised gold interlace band).
Every measure is in the piece's build.json.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit_build as kb  # noqa: E402
from native_build import Part, U, buckle, grid_tris, raycast, rivet, vertex_normals  # noqa: E402

smooth01 = kb.smooth01


# ---------------------------------------------------------------- mesh helpers

def subdivide(V, F):
    """1 -> 4 midpoint split (shared edge points)."""
    E = np.sort(np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), 1)
    Eu, inv = np.unique(E, axis=0, return_inverse=True)
    inv = inv.ravel()
    m = len(V) + np.arange(len(Eu))
    V2 = np.vstack([V, 0.5 * (V[Eu[:, 0]] + V[Eu[:, 1]])])
    n = len(F)
    a, b, c = m[inv[:n]], m[inv[n:2 * n]], m[inv[2 * n:]]
    F2 = np.vstack([np.c_[F[:, 0], a, c], np.c_[a, F[:, 1], b], np.c_[c, b, F[:, 2]], np.c_[a, b, c]])
    return V2, F2


def clip(V, F, g):
    """The part of a triangle mesh where g > 0 (cut on its edges by linear crossing)."""
    key, NV = {}, [V]
    nv = [len(V)]

    def cut(i, j):
        k = (min(i, j), max(i, j))
        if k not in key:
            t = g[i] / (g[i] - g[j])
            NV.append((V[i] + (V[j] - V[i]) * t)[None])
            key[k] = nv[0]
            nv[0] += 1
        return key[k]

    out = []
    for f in F:
        s = g[f] > 0
        if s.all():
            out.append(f)
        elif s.any():
            k = int(np.argmax(s != np.roll(s, 1))) if s.sum() == 1 else None
            if s.sum() == 1:
                i = int(np.nonzero(s)[0][0])
                a, b, c = f[i], f[(i + 1) % 3], f[(i + 2) % 3]
                out.append([a, cut(a, b), cut(a, c)])
            else:
                i = int(np.nonzero(~s)[0][0])
                a, b, c = f[i], f[(i + 1) % 3], f[(i + 2) % 3]
                ab, ac = cut(a, b), cut(a, c)
                out += [[ab, b, c], [ab, c, ac]]
            del k
    V2 = np.vstack(NV)
    F2 = np.array(out, np.int64)
    used = np.unique(F2)
    remap = np.full(len(V2), -1)
    remap[used] = np.arange(len(used))
    return V2[used], remap[F2]


def weld(V, F, tol=1e-6):
    q = np.round(V / tol).astype(np.int64)
    _, idx, inv = np.unique(q, axis=0, return_index=True, return_inverse=True)
    F = inv.ravel()[F]
    F = F[(F[:, 0] != F[:, 1]) & (F[:, 1] != F[:, 2]) & (F[:, 2] != F[:, 0])]
    return V[idx], F


def boundary_loops(F):
    E = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    k = np.sort(E, 1)
    u, c = np.unique(k, axis=0, return_counts=True)
    bset = {tuple(e) for e in u[c == 1]}
    nxt = {}
    for a, b in E:
        if (min(a, b), max(a, b)) in bset:
            nxt[a] = b
    loops, seen = [], set()
    for s in list(nxt):
        if s in seen:
            continue
        L, v = [], s
        while v not in seen and v in nxt:
            seen.add(v)
            L.append(v)
            v = nxt[v]
        if len(L) > 3:
            loops.append(np.array(L))
    return loops


def laplace(P, F, it, fixed=None, lam=0.5):
    n = len(P)
    E = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    E = np.vstack([E, E[:, ::-1]])
    deg = np.bincount(E[:, 0], minlength=n).astype(float)
    for _ in range(it):
        S = np.zeros_like(P)
        np.add.at(S, E[:, 0], P[E[:, 1]])
        Q = S / np.maximum(deg, 1)[:, None]
        mv = lam * (Q - P)
        if fixed is not None:
            mv[fixed] = 0
        P = P + mv
    return P


def shell(name, mat, P, F, N, thick, col_w=1.0):
    """A closed shell from an open patch: inner P, outer P + N thick, walls on its boundary."""
    rn = kb.rand01(name)
    parts = []
    for Q, sgn in ((P + N * thick, 1), (P, -1)):
        T = kb.orient(Q, F, N * sgn)
        parts.append(Part(name, mat, Q, T, uv0=np.c_[Q[:, 0] + Q[:, 2], Q[:, 1]] * 3.0,
                          col=np.tile([1.0, rn, 0.0, col_w], (len(Q), 1))))
    cen = P[F].mean(1)
    for L in boundary_loops(F):
        a, b = P[L], P[L] + N[L] * thick
        nb = len(L)
        V = np.vstack([a, b])
        T = grid_tris(2, nb, close=True)
        mid = 0.5 * (a + np.roll(a, -1, 0))
        # outward of the edge: away from the patch's nearest face centre
        from scipy.spatial import cKDTree
        _, ci = cKDTree(cen).query(mid)
        out = U(mid - cen[ci])
        T = kb.orient(V, T, np.vstack([out, out]))
        parts.append(Part(name, mat, V, T, uv0=np.c_[V[:, 0] + V[:, 2], V[:, 1]] * 3.0,
                          col=np.tile([1.0, rn, 0.0, 0.0], (len(V), 1))))
    return Part.join(name, mat, parts)


class Normals:
    """A stand-in Ref for kb.bead on a plate: closest() gives the plate's own normal at the nearest point."""

    def __init__(self, P, N):
        from scipy.spatial import cKDTree
        self.P, self.N, self.t = P, N, cKDTree(P)

    def closest(self, X):
        d, i = self.t.query(np.asarray(X, float))
        return self.P[i], self.N[i], d


def torus(c, n, up, R, r, name, mat, seg=28, tube=8):
    n, up = U(np.asarray(n, float)), U(np.asarray(up, float))
    x = U(np.cross(up, n))
    a = np.linspace(0, 2 * np.pi, seg, endpoint=False)
    b = np.linspace(0, 2 * np.pi, tube, endpoint=False)
    ring = np.cos(a)[:, None] * x + np.sin(a)[:, None] * up
    P = (c + ring[:, None, :] * (R + r * np.cos(b))[None, :, None] + n * (r * np.sin(b))[None, :, None]).reshape(-1, 3)
    T = grid_tris(seg, tube, close=True)
    T = np.vstack([T, T])[:len(T)]
    # wrap the seg rows too
    i = np.arange(tube)
    last = np.c_[(seg - 1) * tube + i, (seg - 1) * tube + (i + 1) % tube, (i + 1) % tube]
    last2 = np.c_[(seg - 1) * tube + i, (i + 1) % tube, i]
    T = np.vstack([T, last, last2])
    D = (P.reshape(seg, tube, 3) - (c + ring * R)[:, None, :]).reshape(-1, 3)
    T = kb.orient(P, T, D)
    return Part(name, mat, P, T, uv0=P[:, :2] * 2.5, uv1=np.tile([0.0, 0.9], (len(P), 1)),
                col=np.tile([0.95, kb.rand01(name), 0.0, 0.0], (len(P), 1)))


# ---------------------------------------------------------------- the brief

def bodice_bot(th, b):
    a = np.abs(th)
    v = b["point"] + (b["hip"] - b["point"]) * np.clip(a / b["v_theta"], 0, 1)
    return np.where(a > b["v_theta"], b["hip"] + (b["back_bot"] - b["hip"]) * smooth01((a - b["v_theta"]) / (180 - b["v_theta"])), v)


def belt_line(th, bl):
    """The belt's centre height round her (theta 0 front): low at the front (slung over the bodice's V), high at the hip."""
    a = np.abs(np.asarray(th, float))
    s = smooth01(a / bl["side_th"])
    y = bl["front_y"] + (bl["side_y"] - bl["front_y"]) * s
    return y + (bl["back_y"] - bl["side_y"]) * smooth01((a - bl["side_th"]) / (180 - bl["side_th"]))


def live_lines(cfg):
    """(build.json "live": true) the bodice's bottom line and the belt's line read from their own build.json, so the
    brief always tucks under what they are now (the bodice is another builder's)."""
    if not cfg.get("live"):
        return
    for key, pid, sub in (("bodice", "kit_bodice", "corset"), ("belt", "kit_belt", "belt")):
        f = os.path.join(kb.SRC, pid, "build.json")
        if os.path.exists(f):
            src = json.load(open(f, encoding="utf-8"))[sub]
            cfg[key] = {k: src[k] for k in cfg[key]}


def brief(cfg, ref):
    live_lines(cfg)
    M, bc, bl = cfg["mat"], cfg["brief"], cfg["belt"]
    z0 = cfg["axis_z"]
    V, F = ref.V, ref.T
    c = V[F].mean(1)
    sel = F[(c[:, 1] > bc["y_min"]) & (c[:, 1] < bc["y_max"]) & (np.abs(c[:, 0]) < 0.25)]
    used = np.unique(sel)
    remap = np.full(len(V), -1)
    remap[used] = np.arange(len(used))
    P, T = V[used], remap[sel]
    for _ in range(bc.get("subdiv", 1)):
        P, T = subdivide(P, T)
        P, _, _ = ref.closest(P)  # (new points back onto her skin)

    def field(X):
        th = np.degrees(np.arctan2(X[:, 0], X[:, 2] - z0))
        top = np.minimum(belt_line(th, bl) - bl["w"] / 2 + bc["tuck"], bodice_bot(th, cfg["bodice"]) - bc["under_bodice"])
        s = np.abs(X[:, 0])
        lf, lb = bc["leg_front"], bc["leg_back"]
        hF = lf["y0"] + (lf["y1"] - lf["y0"]) * np.clip(s / lf["s1"], 0, 1) ** lf["p"]
        hB = lb["y0"] + (lb["y1"] - lb["y0"]) * np.clip(s / lb["s1"], 0, 1) ** lb["p"]
        wf = smooth01((X[:, 2] - bc["z_mid"] + 0.03) / 0.06)
        h = np.minimum(wf * hF + (1 - wf) * hB, top - bc["side_w"])
        return np.minimum(top - X[:, 1], X[:, 1] - h)

    P, T = clip(P, T, field(P))
    P, T = weld(P, T, 1e-7)
    # keep the largest component
    import scipy.sparse as sp
    from scipy.sparse.csgraph import connected_components
    A = sp.coo_matrix((np.ones(len(T) * 3), (np.repeat(T[:, 0], 3), T.ravel())), shape=(len(P), len(P)))
    nc, lab = connected_components(A + A.T, directed=False)
    big = np.argmax(np.bincount(lab[T[:, 0]]))
    T = T[lab[T[:, 0]] == big]
    used = np.unique(T)
    remap = np.full(len(P), -1)
    remap[used] = np.arange(len(used))
    P, T = P[used], remap[T]
    # lift: her normal x clear, then smoothed (bridges the cleft and the crease) and never under clear_min
    q, n, _ = ref.closest(P)
    Q = q + n * cfg["clear"]
    bnd = np.concatenate(boundary_loops(T))
    Q = laplace(Q, T, bc["smooth"], lam=0.5)
    for _ in range(4):
        q, n, _ = ref.closest(Q)
        cl = ((Q - q) * n).sum(1)
        low = cl < cfg["clear_min"]
        Q[low] += n[low] * (cfg["clear_min"] - cl[low] + 1e-4)[:, None]
        Q = laplace(Q, T, 2, lam=0.3)
    q, n, _ = ref.closest(Q)
    cl = ((Q - q) * n).sum(1)
    low = cl < cfg["clear_min"]
    Q[low] += n[low] * (cfg["clear_min"] - cl[low] + 1e-4)[:, None]
    N = vertex_normals(Q, T)
    N = np.where(((N * n).sum(1) < 0)[:, None], -N, N)
    plate = [shell("brief", M["plate"], Q, T, N, cfg["thick"])]
    trim = []
    rim = cfg["rim"]
    for k, L in enumerate(boundary_loops(T)):
        trim.append(kb.bead(ref, f"trim_brief{k}", M["trim"], Q[L], rim, cfg["thick"] * 0.5 + 0.0003, True, relax_it=2))
    del bnd
    return plate, trim, [], []


# ---------------------------------------------------------------- the belt and its plates

def under_mesh(ref, files):
    """Her torso faces + the pieces she wears under the belt, as one mesh (n_skin: her faces come first)."""
    import gear_native as gn
    V, F = [ref.V], [ref.torso]
    off = len(ref.V)
    for f in files:
        for p in gn.read_parts(f):
            V.append(p["P"].astype(float))
            F.append(p["T"] + off)
            off += len(p["P"])
    return np.vstack(V), np.vstack(F), len(ref.torso)


def outer_rho(UV, UF, nsk, wrap, Y, TH, R=0.42):
    """Per (y, theta): the outermost surface along the wrap ray (cast inward from R); is it her skin."""
    D = wrap.dirs(TH.ravel())
    O = wrap.pt(Y.ravel(), TH.ravel(), np.full(Y.size, R))
    t, i = raycast(UV, UF, O, -D, R, chunk=64)
    rho = (R - t).reshape(Y.shape)
    return rho, (i < nsk).reshape(Y.shape)


SWEEP_CLIPS = ("idle_warden", "run_warden", "sword_heavy", "leap")   # the demo's clips (docs/handoff/armor.md, lead 2)


def sweep(rides, under_ids, z0, clips=SWEEP_CLIPS, y0=0.78, y1=1.26, dy=0.002, dth=1.0, verbose=True, extra=None):
    """The room each rigid ride needs: {name: E (ny, nth)}, the outermost radius (about the axis x = 0, z = z0) of her
    skin and of the pieces `under_ids` (installed, posed by their own weights), over every frame of the demo clips (and
    her rest), carried back into the rest frame of a rigid shell riding `rides[name]` ({bone: w}, as params.rigid_ride
    gives it): a lame on that blend clears her in every frame if it stands outside E. Her springs as wearcheck runs
    them (amount 1, squash 1); every triangle sampled at its corners, edge middles and centre. Cached by its inputs
    (with her hip hinges' spec: a ride may name thigh_hinge_*).
    extra: {name: [(P (n, 3) rest points, {bone: w})]}: rigid point sets riding their own blend (a lame on another
    ride that this ride's plate laps over), carried into that ride's room alone: E[name] then holds only them.
    Returns (E, ys, ths)."""
    import hashlib
    sys.path.insert(0, os.path.join(kb.REPO, "tools", "anim"))
    import helpers as hp_
    main = os.path.abspath(os.path.join(kb.REPO, "..", "..", ".."))   # (as wearcheck: the main checkout's built clips)
    os.environ.setdefault("ANIM_OUT", os.path.join(main if os.path.isdir(os.path.join(main, "tools", "anim", "out"))
                                                   else kb.REPO, "tools", "anim", "out"))
    import skin
    # (skin may already be imported (native_build / gear_native) with its default OUT, this worktree's unbuilt
    # tools/anim/out: point it at the built clips as wearcheck does)
    if not (skin.OUT / "clips").is_dir():
        from pathlib import Path
        skin.OUT = Path(os.path.join(main, "tools", "anim", "out"))
    ys = np.arange(y0, y1 + dy / 2, dy)
    ths = np.arange(-180.0, 180.0, dth)
    art = __import__("bodies").cur().art
    idx_rows = {r["id"]: r for r in json.load(open(os.path.join(art, "armor_index.json"))) if isinstance(r, dict)}
    paths = [os.path.join(art, f"{g}.gltf") for g in under_ids]
    kb.require_body_inputs(clips)
    deps = [kb.body_glb()] + paths + [str(skin.OUT / "clips" / f"{c}.json") for c in clips]
    stamp = [(os.path.basename(p), os.path.getsize(p), int(os.path.getmtime(p))) for p in deps]
    xh = hashlib.sha1()
    for k_ in sorted(extra or {}):
        for P_, w_ in extra[k_]:
            xh.update(k_.encode() + np.round(np.asarray(P_, float), 5).tobytes() + json.dumps(sorted(w_.items())).encode())
    key = hashlib.sha1(json.dumps(["v2 no arms", sorted((k, sorted(v.items())) for k, v in rides.items()), list(under_ids), list(clips),
                                   y0, y1, dy, dth, z0, stamp, hp_.SPEC.get("hinges"), xh.hexdigest() if extra else None]
                                  + ([hp_.SPEC.get("tassets")] if hp_.SPEC.get("tassets") else [])
                                  ).encode()).hexdigest()[:14]
    cache = os.path.join(kb.REPO, ".shots", "armor2", "kit_hips_sweep", key + ".npz")
    if os.path.exists(cache):
        z = np.load(cache)
        return {k: z[k] for k in rides}, ys, ths
    sk = skin.Skeleton.load(__import__("bodies").skeleton_path())
    files = [(skin.Path(kb.body_glb()), lambda n: n == "Heroine", "skin")]
    for g, p in zip(under_ids, paths):
        files.append((skin.Path(p), lambda n, s=frozenset(idx_rows[g]["meshes"]): n in s, "garment"))
    body = skin.Body(sk, files, skin.Jiggle(sk, 1, 1), label="her", helpers=True)
    sel = (body.P[body.T][..., 1] > y0 - 0.03).all(1) & (body.P[body.T][..., 1] < y1 + 0.03).all(1)
    # (not her arms and hands: they swing past the plates in the clips, and no plate is built to clear a hand)
    arm_j = np.array([str(n).startswith(skin.ARM_PARTS) for n in body.sk.names] + [False] * 64)
    arm_w = (body.W * arm_j[np.minimum(body.Jv, len(arm_j) - 1)]).sum(1)
    sel &= (arm_w[body.T] < 0.05).all(1)
    T = body.T[sel]
    idx, Tl = np.unique(T, return_inverse=True)
    Tl = Tl.reshape(T.shape)
    E_ = np.unique(np.sort(np.r_[Tl[:, [0, 1]], Tl[:, [1, 2]], Tl[:, [2, 0]]], 1), axis=0)
    names = list(body.sk.names)
    E = {k: np.full((len(ys), len(ths)), np.nan) for k in rides}
    ang = {}

    xr = set(extra or ())
    body_rides = [k for k in rides if k not in xr]

    def add(Q, S, only=None):
        for k, wts in rides.items():
            if (only is None and k in xr) or (only is not None and k != only):
                continue
            if S is None:
                X = Q
            else:
                M = sum(float(w) * S[names.index(b)] for b, w in wts.items()) / sum(wts.values())
                Mi = np.linalg.inv(M)
                X = Q @ Mi[:3, :3].T + Mi[:3, 3]
            iy = np.round((X[:, 1] - y0) / dy).astype(int)
            th = np.degrees(np.arctan2(X[:, 0], X[:, 2] - z0))
            it = np.round((th + 180.0) / dth).astype(int) % len(ths)
            ok = (iy >= 0) & (iy < len(ys))
            rho = np.hypot(X[:, 0], X[:, 2] - z0)
            A = E[k]
            flat = np.full(A.size, -1.0)
            np.maximum.at(flat, iy[ok] * len(ths) + it[ok], rho[ok])
            flat = flat.reshape(A.shape)
            E[k] = np.where(flat > 0, np.fmax(A, flat), A)

    def samples(P):
        return np.vstack([P, (P[E_[:, 0]] + P[E_[:, 1]]) / 2, P[Tl].mean(1)])

    def add_extra(S):
        for k in xr:
            for P_, w_ in extra[k]:
                P_ = np.asarray(P_, float)
                if S is None:
                    add(P_, None, k)
                    continue
                Me = sum(float(w) * S[names.index(b)] for b, w in w_.items()) / sum(w_.values())
                add(P_ @ Me[:3, :3].T + Me[:3, 3], S, k)

    if body_rides:
        add(samples(body.P[idx]), None)
    add_extra(None)
    for c in clips:
        clip = body.clip(c)
        frames = body.frames(clip)
        for G in frames:
            S = body.skin_mats(G)
            if body_rides:
                add(samples(body.pose(G, idx)), S)
            add_extra(S)
            for side, th_ in (("l", "thigh_l"), ("r", "thigh_r")):
                Rr = S[names.index("pelvis"), :3, :3].T @ S[names.index(th_), :3, :3]
                a = np.degrees(np.arccos(np.clip((np.trace(Rr) - 1) / 2, -1, 1)))
                ang[(c, side)] = max(ang.get((c, side), 0.0), a)
        if verbose:
            print(f"sweep: {c} {len(frames)} frames; thigh vs pelvis max deg l {ang[(c, 'l')]:.0f} r {ang[(c, 'r')]:.0f}", flush=True)
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    np.savez_compressed(cache, **E)
    return E, ys, ths


def dilate(E, ys, ths, need, rho_ref=0.16):
    """E grown by a ball of radius `need` (m) in (y, arc length at rho_ref): the radius a plate must stand at."""
    dy, dth = ys[1] - ys[0], np.radians(ths[1] - ths[0]) * rho_ref
    ky, kt = int(need / dy), int(need / dth)
    out = np.full_like(E, np.nan)
    for a in range(-ky, ky + 1):
        for b in range(-kt, kt + 1):
            h = need ** 2 - (a * dy) ** 2 - (b * dth) ** 2
            if h < 0:
                continue
            S_ = np.roll(E, (-a, -b), (0, 1))
            if a > 0:
                S_[-a:] = np.nan
            elif a < 0:
                S_[:-a] = np.nan
            out = np.fmax(out, S_ + np.sqrt(h))
    return out


def room_fn(R, ys, ths):
    """(y, th) -> the dilated room R at the four grid cells round it, the most of them (nan: nothing there)."""
    def f(y, th):
        fy = np.clip((np.asarray(y, float) - ys[0]) / (ys[1] - ys[0]), 0, len(ys) - 1.001)
        ft = ((np.asarray(th, float) + 180.0) % 360.0) / (ths[1] - ths[0])
        y0, t0 = np.floor(fy).astype(int), np.floor(ft).astype(int)
        out = np.full(np.broadcast(fy, ft).shape, np.nan)
        for a in (0, 1):
            for b in (0, 1):
                out = np.fmax(out, R[np.minimum(y0 + a, len(ys) - 1), (t0 + b) % len(ths)])
        return out
    return f


def upper_hull(s, r):
    """The least concave function over the points (s ascending): its knots."""
    h = []
    for p in zip(s, r):
        while len(h) >= 2 and (h[-1][0] - h[-2][0]) * (p[1] - h[-2][1]) - (h[-1][1] - h[-2][1]) * (p[0] - h[-2][0]) >= 0:
            h.pop()
        h.append(p)
    return np.array(h)


def hug_col(room, skin_rho, th, y_top, s0, r0, s1, a_in, smax, floor=None, ds=0.002, min_len=0.012):
    """One column of a hugging lame: its radius r(s) at drops s (below y_top) from (s0, r0) to s1, the least concave
    (outward-bowing) curve over the room (and `floor`), never leaning in faster than a_in deg; cut short where it would
    stand over smax off her rest skin, never shorter than min_len (a V's corner columns: a few mm). Returns (S, r)."""
    for _ in range(3):
        S = np.linspace(s0, max(s1, s0 + 2 * ds), max(int(round((s1 - s0) / ds)) + 1, 3))
        t = room(y_top - S, np.full(len(S), th))
        if floor is not None:
            t = np.fmax(t, floor(S))
        ok = np.isfinite(t)
        if ok[0]:  # (the top row follows the room too: never under it, hipv-2 r5; was the belt radius alone)
            r0 = max(r0, float(t[0]))
        ok[0] = False
        H = upper_hull(np.r_[s0, S[ok]], np.r_[r0, t[ok]])
        r = np.interp(S, H[:, 0], H[:, 1])
        k = np.tan(np.radians(a_in)) * (S[1] - S[0])
        for i in range(1, len(r)):
            r[i] = max(r[i], r[i - 1] - k)
        st = r - skin_rho(y_top - S, np.full(len(S), th))
        bad = np.nonzero(st[1:] > smax)[0]
        if not len(bad):
            return S, r
        s1 = max(S[bad[0]], s0 + min_len)
    return S, r


def hug_lame(room, skin_rho, ths, y_top, s0, r0, s1, rows, a_in, smax, floors=None, sig=1.0, min_len=0.012):
    """A hugging lame: a column per theta (hug_col), resampled to `rows` evenly down each, the radii raised to their
    smoothing across the columns (never lowered). Returns (S (rows, cols) drops, Rg radii, per-column functions r(s))."""
    from scipy.ndimage import gaussian_filter1d
    C = len(ths)
    Sg, Rg, fns = np.zeros((rows, C)), np.zeros((rows, C)), []
    for j in range(C):
        S, r = hug_col(room, skin_rho, ths[j], y_top[j], s0[j], r0[j], s1[j], a_in, smax,
                       None if floors is None else floors[j], min_len=min_len)
        Sg[:, j] = np.linspace(S[0], S[-1], rows)
        Rg[:, j] = np.interp(Sg[:, j], S, r)
    # (the lengths: a column cut short shortens its neighbours a little, so the edge runs smooth)
    L = Sg[-1] - Sg[0]
    L = np.minimum(L, gaussian_filter1d(L, sig, mode="nearest") + 0.004)
    for j in range(C):
        s_new = np.linspace(Sg[0, j], Sg[0, j] + L[j], rows)
        Rg[:, j] = np.interp(s_new, Sg[:, j], Rg[:, j])
        Sg[:, j] = s_new
    Rg = np.maximum(Rg, gaussian_filter1d(Rg, sig, axis=1, mode="nearest"))
    for j in range(C):
        fns.append(lambda s, a=Sg[:, j].copy(), b=Rg[:, j].copy(): np.interp(s, a, b, left=b[0], right=b[-1]))
    return Sg, Rg, fns


def hang(ref, wrap, name, ths, y_top, rho_top, length, a0, need, it=8, sig=1.5, rows=14, a_max=None):
    """A rigid hanging plate: columns at ths from (y_top, rho_top) down a cone tilted a0 (deg) out from vertical,
    each column's tilt raised until every point stands `need` (m, per row fraction) off her skin. Returns the inner
    grid (rows, cols, 3), its outward normals and the tilts."""
    from scipy.ndimage import gaussian_filter1d
    C = len(ths)
    a = np.full(C, np.radians(a0))
    v = np.linspace(0, 1, rows)[:, None] * length[None, :]
    o = wrap.dirs(ths)
    T0 = wrap.pt(y_top, ths, rho_top)
    nd = need(np.linspace(0, 1, rows))[:, None]

    def grid(a):
        d = np.array([0, -1.0, 0])[None, :] * np.cos(a)[:, None] + o * np.sin(a)[:, None]
        return T0[None] + v[..., None] * d[None]

    for _ in range(it):
        G = grid(a)
        q, n, _ = ref.closest(G.reshape(-1, 3))
        cl = ((G.reshape(-1, 3) - q) * n).sum(1).reshape(G.shape[:2])
        defi = np.max(np.where(v > 0.004, (nd - cl) / np.maximum(v, 1e-3), -1), 0)
        if (defi <= 1e-4).all():
            break
        a = a + np.clip(defi, 0, None) * 1.1
        a = np.maximum(a, gaussian_filter1d(a, sig, mode="nearest"))
        if a_max is not None:  # (a plate never flares past a_max: the design hangs them near her line)
            a = np.minimum(a, np.radians(a_max))
    G = grid(a)
    du = np.gradient(G, axis=1)
    dv = np.gradient(G, axis=0)
    N = U(np.cross(dv, du))
    N = np.where(((N * o[None]).sum(-1) < 0)[..., None], -N, N)
    return G, N, np.degrees(a)


def interlace(G, Nn, j0, j1, v0, v1, wl, name, mat, ref_n, beads):
    """A raised gold interlace band on a plate grid between columns j0..j1 and rows-fractions v0..v1: two borders
    and two crossing waves (a plait), plus a small boss at each crossing's eye."""
    R, C = G.shape[:2]
    from scipy.interpolate import RegularGridInterpolator
    gi = RegularGridInterpolator((np.linspace(0, 1, R), np.arange(C)), G)
    ni = RegularGridInterpolator((np.linspace(0, 1, R), np.arange(C)), Nn)
    rm = int(R * (v0 + v1) / 2)
    span = np.linalg.norm(G[rm, int(round(j1))] - G[rm, int(round(j0))])
    js = np.linspace(j0, j1, max(int(span / 0.0015), 20))
    s = (js - j0) / max(j1 - j0, 1e-6) * span
    mid, amp = (v0 + v1) / 2, (v1 - v0) / 2 * 0.72
    out = []
    lines = [np.full_like(js, v0), np.full_like(js, v1)]
    for ph in (0.0, np.pi):
        lines.append(mid + amp * np.sin(2 * np.pi * s / wl + ph))
    for k, vv in enumerate(lines):
        X = np.stack([vv, js], 1)
        E = gi(X)
        Nq = ni(X)
        rim = beads[0] if k < 2 else beads[1]
        out.append(kb.bead(Normals(E, U(Nq)), f"{name}{k}", mat, E, rim, ref_n, False, relax_it=1))
    return out


def belt(cfg, ref):
    M, bl, z0 = cfg["mat"], cfg["belt"], cfg["axis_z"]
    under = [os.path.join(kb.out_root(), f, f + ".glb") for f in cfg["under"]]
    UV, UF, nsk = under_mesh(ref, under)
    wrap = kb.Wrap(ref, z0, 0.90, 1.16)
    plate, trim, straps, rigid = [], [], [], []
    hw = bl["w"] / 2
    TH = np.arange(-180.0, 180.0, bl["col_step"])
    Cn = len(TH)
    yc = belt_line(TH, bl)
    rows = 7
    w = np.linspace(-1, 1, rows)
    Y = yc[None, :] + w[:, None] * hw
    THg = np.broadcast_to(TH[None], Y.shape)
    # what she wears there, sampled finer across the band
    ws = np.linspace(-1.15, 1.15, 13)
    Ys = yc[None, :] + ws[:, None] * hw
    rho_u, is_skin = outer_rho(UV, UF, nsk, wrap, Ys, np.broadcast_to(TH[None], Ys.shape))
    need = rho_u + np.where(is_skin, cfg["clear"], bl["gap"])
    need = np.where(np.isfinite(need), need, np.nan)
    need = kb.fill_rows(need)
    # ruled across: a line in y per column over every need point, smoothed round her
    from scipy.ndimage import gaussian_filter1d, maximum_filter1d
    A = np.c_[np.ones(len(ws)), ws * hw]
    coef = np.linalg.lstsq(A, need, rcond=None)[0]  # (2, C)
    coef = np.stack([gaussian_filter1d(coef[k], bl["sig"], mode="wrap") for k in range(2)])
    lift = np.max(need - A @ coef, 0)
    lift = gaussian_filter1d(maximum_filter1d(lift, 5, mode="wrap"), 1.5, mode="wrap")
    lift = np.maximum(lift, np.max(need - A @ coef, 0))
    rho_in = (np.c_[np.ones(rows), w * hw] @ coef) + lift[None]
    Pin = wrap.pt(Y, THg, rho_in)
    Nout = wrap.dirs(THg)
    bt = bl["thick"]
    straps.append(kb.slab("belt", M["strap"], Pin, Nout, bt, closed_c=True))

    def belt_pt(y, th, up):
        th = np.atleast_1d(np.asarray(th, float))
        y = np.atleast_1d(np.asarray(y, float))
        j = np.interp((th + 180) % 360 - 180, np.r_[TH, 180.0], np.arange(Cn + 1)) % Cn
        j0 = np.floor(j).astype(int)
        f = j - j0
        cf = coef[:, j0] * (1 - f) + coef[:, (j0 + 1) % Cn] * f
        lf = lift[j0] * (1 - f) + lift[(j0 + 1) % Cn] * f
        yy = y - (yc[j0] * (1 - f) + yc[(j0 + 1) % Cn] * f)
        r = cf[0] + cf[1] * yy + lf + up
        return wrap.pt(y, th, r), wrap.dirs(th)

    # edge stitching beads (thin, dark leather): skip; studs in gold along the centre line
    st = bl["studs"]
    for th in np.arange(-180.0, 180.0, st["step"]):
        if min(abs(th - s) for s in st["skip"]) < st["skip_w"] or abs(th) < st["skip_front"]:
            continue
        for dy in st["rows"]:
            p, n = belt_pt(belt_line(th, bl) + dy, th, bt)
            trim.append(rivet(p[0], n[0], r=st["r"], h=st["h"], name=f"stud{len(trim)}", material=M["trim"]))
    # buckle (rigid) at the front
    bk = bl["buckle"]
    p, n = belt_pt(belt_line(0.0, bl), 0.0, bt + 0.0008)
    up = U(belt_pt(belt_line(0.0, bl) + 0.01, 0.0, bt)[0][0] - belt_pt(belt_line(0.0, bl) - 0.01, 0.0, bt)[0][0])
    rigid.append(buckle(p[0], n[0], np.cross(up, n[0]) if False else up, w=bk["w"], h=bk["h"], bar=bk["bar"],
                        name="buckle_rigid", material=M["trim"]))
    # keeper tabs with rings
    rg = bl["rings"]
    for h in (1, -1):
        th = h * rg["th"]
        y1 = belt_line(th, bl) + hw - 0.004
        y0 = belt_line(th, bl) - hw - rg["drop"]
        ys = np.linspace(y0, y1, 8)
        tw = rg["tab_w"] / 2
        AA = th + np.degrees(np.array([-tw, -tw / 3, tw / 3, tw]) / 0.13)
        YY, AG = np.meshgrid(ys, AA, indexing="ij")
        PP, NN = belt_pt(YY.ravel(), AG.ravel(), bt + 0.0006)
        straps.append(kb.slab(f"tab_{h}", M["strap"], PP.reshape(YY.shape + (3,)), NN.reshape(YY.shape + (3,)), 0.0025))
        pc, nc = belt_pt(y0 - rg["R"] + 0.004, th, bt + rg.get("out", 0.004))
        rigid.append(torus(pc[0], nc[0], [0, 1.0, 0], rg["R"], rg["r"], f"ring_{'l' if h > 0 else 'r'}_rigid", M["trim"]))
        pr, nr = belt_pt(y0 + 0.006, th, bt + 0.003)
        rigid.append(rivet(pr[0], nr[0], r=0.003, h=0.002, name=f"tabrivet_{'l' if h > 0 else 'r'}_rigid",
                           material=M["trim"]))

    # ---- hanging plates
    rim = cfg["rim"]
    pt_th = cfg["plate_thick"]
    edge_off = pt_th * 0.5 + 0.0003
    from scipy.interpolate import interp1d
    hg = cfg.get("hug")
    if hg:  # the room every ride needs through the demo clips (sweep), grown by the clearance
        rides = {}
        for pl in cfg["plates"]:
            for lm in pl.get("lames", ()):
                for h in ((1, -1) if pl.get("mirror", True) else (1,)):
                    rides[ride_key(lm["ride"], h)] = side_ride(lm["ride"], h)
        Esw, ys_, ths_ = sweep(rides, hg.get("under", ["kit_brief"]), z0)
        Eroom = {k: dilate(Esw[k], ys_, ths_, hg["need"]) for k in rides}
        skin_rho = wrap.field(wrap.rho)
        ride_out, built = [], {}
    for pl in cfg["plates"]:
        if hg and pl.get("lames"):
            hs = (1, -1) if pl.get("mirror", True) else (1,)
            rooms = lap_rooms(pl, hs, built, Eroom, ys_, ths_, z0, hg.get("lap_gap", 0.0015), pt_th + rim["h"])
            for h in hs:
                hug_plate(pl, h, cfg, bl, belt_pt, wrap, rooms[h], skin_rho, rigid, ride_out, M, rim, pt_th, edge_off, z0,
                          built)
            continue
        for h in ((1, -1) if pl.get("mirror", True) else (1,)):
            nm = pl["name"] + ("" if not pl.get("mirror", True) else ("_l" if h > 0 else "_r"))
            a0, a1 = pl["th"]
            ths = np.linspace(a0, a1, pl["cols"]) * h
            if not pl.get("mirror", True):
                ths = np.linspace(-a1, a1, pl["cols"])
            y_top = belt_line(ths, bl) - hw + pl["tuck"]
            rho_t = np.array([np.linalg.norm((belt_pt(yy, t, 0.0010)[0][0] - [0, yy, z0])[[0, 2]]) for yy, t in zip(y_top, ths)])
            u = (np.abs(ths) - min(abs(a0), abs(a1))) / max(abs(a1 - a0), 1e-6) if pl.get("mirror", True) else np.abs(ths) / a1
            Lk = np.array(pl["len"])
            length = interp1d(np.linspace(0, 1, len(Lk)), Lk, kind="quadratic" if len(Lk) > 2 else "linear")(np.clip(u, 0, 1))
            nd = pl["need"]
            G, Nn, tilt = hang(ref, wrap, nm, ths, y_top, rho_t, length, pl["tilt"],
                               lambda f, nd=nd: nd[0] + (nd[1] - nd[0]) * f, rows=pl["rows"], a_max=pl.get("tilt_max"))
            ex = None
            if pl.get("keel"):
                k_ = pl["keel"]
                xs = np.linalg.norm(G - G[:, [len(ths) // 2]], axis=-1)
                ex = k_["h"] * np.clip(1 - xs / (k_["w"] / 2), 0, 1) ** 1.0
            # two hinged lames (the sheet's): the upper rides her pelvis (short, above the hip joint), the lower hangs
            # OUTSIDE its bottom edge by `lap` and rides her thigh (its own node: its own blend, the mean of her
            # weights over it), so it swings with the thigh and slides under nothing; a plate without "split" is one.
            R_, C_ = G.shape[:2]
            if pl.get("split"):
                k_ = int(round(pl["split"] * (R_ - 1)))
                sp = pl.get("lap_rows", 2)
                lo = slice(max(k_ - sp, 0), R_)
                lames = [("_up", slice(0, k_ + 1), slice(0, C_), 0.0, False, "lbr")]
                if pl.get("halves"):  # (the lower lame cut at the centre column: each half its own node on its own thigh,
                    # no rim on the seam (the keel's ridge line), so at rest the two read as one V)
                    c_ = C_ // 2
                    lames += [("_lo_l", lo, slice(c_, C_), pl.get("lap", 0.004), True, "br"),
                              ("_lo_r", lo, slice(0, c_ + 1), pl.get("lap", 0.004), True, "lb")]
                else:
                    lames.append(("_lo", lo, slice(0, C_), pl.get("lap", 0.004), True, "lbr"))
            else:
                lames = [("", slice(0, R_), slice(0, C_), 0.0, True, "lbr")]
            for sfx, rs, cs, push, band_on, sides in lames:
                Gl, Nl = G[rs, cs] + Nn[rs, cs] * push, Nn[rs, cs]
                exl = None if ex is None else ex[rs, cs]
                plate_p = kb.slab(nm + sfx + "_rigid", M["plate"], Gl, Nl, pt_th, extra=exl)
                plate_p.name = nm + sfx + "_rigid"
                rigid.append(plate_p)
                # its rim (all but the top, which is under the belt or the lame above; `sides` l/b/r: the left column,
                # bottom row, right column): one rigid gold part with the band
                E = np.vstack(([Gl[:, 0]] if "l" in sides else []) + ([Gl[-1, (1 if "l" in sides else 0):]] if "b" in sides else [])
                              + ([Gl[::-1, -1][1:]] if "r" in sides else []))
                gold = [kb.bead(Normals(Gl.reshape(-1, 3), Nl.reshape(-1, 3)), nm + sfx + "_rim", M["trim"], E, rim, edge_off,
                                False, relax_it=1)]
                if pl.get("band") and band_on:
                    b_ = pl["band"]
                    Gs = Gl + Nl * (pt_th + (0 if exl is None else exl[..., None]))
                    gold += interlace(Gs, Nl, 1.2, Gl.shape[1] - 2.2, b_["v"][0], b_["v"][1], b_["wl"], nm + sfx + "_band",
                                      M["trim"], 0.0, [dict(rim, w=b_["border_w"], h=b_["border_h"], below=0.0003),
                                                       dict(rim, w=b_["w"], h=b_["h"], below=0.0003)])
                # (the SAME node name as its plate: the importer reads them as one source part (`<name>_rigid`, `.001`),
                # whose parts ride ONE common blend (piece_blender by_src), so the gold never drifts off its steel)
                rigid.append(Part.join(nm + sfx + "_rigid", M["trim"], gold))
                rd = pl.get("rides", {}).get(sfx)
                if rd is not None and hg:  # (its own single-bone ride: a skinned plate that pivots whole, params.rigid_ride)
                    ride_out.append({"match": nm + sfx, "weights": side_ride(rd, h) if pl.get("mirror", True) else dict(rd), "mix": 1.0})
            print(nm, "tilt", np.round(tilt.min(), 1), np.round(tilt.max(), 1), "len", np.round(length.max(), 3))
    if hg:  # each lame's ride, into the piece's install params (pin_shipped params.rigid_ride; first match wins)
        if rg.get("ride"):  # (opt-in: the keeper rings ride one blend of their own ({bone: w}, her left; mirrored),
            # e.g. {"tasset_hinge": 1}: they swing out with the V over the leading thigh instead of the mean of her
            # skin under them, which the brief's leg line rises through in the leap)
            ride_out += [{"match": f"ring_{s}_rigid", "weights": side_ride(rg["ride"], h), "mix": 1.0}
                         for h, s in ((1, "l"), (-1, "r"))]
        pid = cfg["piece"]["id"]
        cfg["piece"]["params"] = {"file": f"{pid}.glb", **cfg["piece"].get("params", {}), "rigid_ride": ride_out}
    unweld_rigid(rigid)
    return plate, trim, straps, rigid


def unweld_rigid(parts, tol=2e-6, step=5e-5):
    """No two rigid nodes share a point (armor-D hipv-2, 16 Nov): pin_shipped welds every point to the micron and a
    rigid shell is a welded component of ONE weight set, so the hip plate's top corner on the front hip plate's
    (y 1.1335, th ~68) merged both into one two-set component: neither was rigid, both steels bent with her skin
    (exact.json rigid_blends 284-615) while their gold rode the hinge. A later node's shared points move `step` in."""
    from scipy.spatial import cKDTree
    seen, moved = [], 0
    for pt in parts:
        for nm_, P_ in seen:
            if nm_ == pt.name or not len(P_) or not len(pt.P):
                continue
            d, _ = cKDTree(P_).query(pt.P, distance_upper_bound=tol)
            hit = np.isfinite(d)
            if hit.any():
                pt.P[hit] -= pt.N[hit] * step
                moved += int(hit.sum())
        seen.append((pt.name, pt.P.copy()))
    print(f"unweld_rigid: {moved} shared points moved {step * 1000:.2f} mm")


def side_ride(ride, h):
    """A ride written for her left ({bone: w}, *_l bones) on side h (1 left, -1 right)."""
    return {(b[:-2] + ("_l" if h > 0 else "_r") if b.endswith(("_l", "_r")) else b): w for b, w in ride.items()}


def ride_key(ride, h):
    return wkey(side_ride(ride, h))


def wkey(w):
    return ",".join(f"{b}:{v:g}" for b, v in sorted(w.items()))


def dense(G, f=6):
    """A plate grid (R, C, 3) resampled f times finer each way (bilinear): points every ~2 mm for a room."""
    from scipy.ndimage import zoom
    return np.stack([zoom(G[..., i], f, order=1) for i in range(3)], -1).reshape(-1, 3)


def bin_room(X, ys, ths, z0):
    """Points (n, 3) binned as sweep() bins them: the outermost radius per (y, theta) cell (nan: none)."""
    iy = np.round((X[:, 1] - ys[0]) / (ys[1] - ys[0])).astype(int)
    th = np.degrees(np.arctan2(X[:, 0], X[:, 2] - z0))
    it = np.round((th + 180.0) / (ths[1] - ths[0])).astype(int) % len(ths)
    ok = (iy >= 0) & (iy < len(ys))
    flat = np.full(len(ys) * len(ths), -1.0)
    np.maximum.at(flat, iy[ok] * len(ths) + it[ok], np.hypot(X[ok, 0], X[ok, 2] - z0))
    flat = flat.reshape(len(ys), len(ths))
    return np.where(flat > 0, flat, np.nan)


def lap_rooms(pl, hs, built, Eroom, ys, ths, z0, gap, up):
    """Per side h, {ride key: room} for a plate (its ride's room, dilated): raised, for a plate that laps over others
    (plates[].over, built before it), over each one's outer face and rim (`up` over its inner face) wherever that
    plate stands in this plate's ride frame through the demo clips: where it rests if it rides the same blend, else
    swept (sweep extra); grown by `gap`. So a lap clears the lame under it in every frame (rigid on both)."""
    out, stat, extra, ride_w = {}, {}, {}, {}
    for h in hs:
        out[h] = {k: room_fn(Eroom[k], ys, ths) for k in Eroom}
        for lm in pl["lames"]:
            k, w = ride_key(lm["ride"], h), side_ride(lm["ride"], h)
            for o in pl.get("over", ()):
                for G, N, wo in built.get(o + ("_l" if h > 0 else "_r"), built.get(o, [])):
                    P = dense(G + N * up)
                    if wkey(wo) == k:
                        stat[(h, k)] = np.fmax(stat.get((h, k), np.full(Eroom[k].shape, np.nan)), bin_room(P, ys, ths, z0))
                    else:
                        extra.setdefault(f"{k}|{h}", []).append((P, wo))
                        ride_w[f"{k}|{h}"] = w
    Ex = sweep(ride_w, [], z0, extra=extra)[0] if extra else {}
    for h in hs:
        for lm in pl["lames"]:
            k = ride_key(lm["ride"], h)
            L = np.fmax(stat.get((h, k), np.full(Eroom[k].shape, np.nan)), Ex.get(f"{k}|{h}", np.nan))
            if np.isfinite(L).any():
                out[h][k] = room_fn(np.fmax(Eroom[k], dilate(L, ys, ths, gap)), ys, ths)
    return out


def hug_plate(pl, h, cfg, bl, belt_pt, wrap, rooms, skin_rho, rigid, ride_out, M, rim, pt_th, edge_off, z0, built=None):
    """A plate of hugging lames (build.json plates[].lames, top to bottom): each its own rigid node riding its own
    blend (lames[].ride), its columns the least outward-bowing curve over that ride's room through the demo clips
    (sweep, dilate), the first hung from under the belt, each next from the one above (`ov` up under it, `lap` out)."""
    from scipy.interpolate import interp1d
    nm = pl["name"] + ("" if not pl.get("mirror", True) else ("_l" if h > 0 else "_r"))
    a0, a1 = pl["th"]
    ths = np.linspace(a0, a1, pl["cols"]) * h if pl.get("mirror", True) else np.linspace(-a1, a1, pl["cols"])
    u = (np.abs(ths) - min(abs(a0), abs(a1))) / max(abs(a1 - a0), 1e-6) if pl.get("mirror", True) else np.abs(ths) / a1
    hw = bl["w"] / 2
    y_top = belt_line(ths, bl) - hw + pl["tuck"]
    r_top = np.array([np.linalg.norm((belt_pt(yy, t, 0.0010)[0][0] - [0, yy, z0])[[0, 2]]) for yy, t in zip(y_top, ths)])
    s0, prev = np.zeros(len(ths)), None
    for k, lm in enumerate(pl["lames"]):
        Lk = np.array(lm["len"])
        s1 = interp1d(np.linspace(0, 1, len(Lk)), Lk, kind="quadratic" if len(Lk) > 2 else "linear")(np.clip(u, 0, 1))
        room = rooms[ride_key(lm["ride"], h)]
        if prev is not None and ride_key(lm["ride"], h) != prev[4]:
            # (a lame on another ride than the one above it (hipv-2 r5: the front plate's lower lame on hiptasset_hinge
            # under a top lame on thigh_hinge): its room also clears that lame's outer face and rim, posed through the
            # demo clips into this lame's ride frame (sweep extra), as lap_rooms does for plates[].over)
            kx = f"{ride_key(lm['ride'], h)}|{h}|{nm}{k}"
            Ex, ys_, ths_ = sweep({kx: side_ride(lm["ride"], h)}, [], z0,
                                  extra={kx: [(dense(prev[3][0] + prev[3][1] * (pt_th + rim["h"])), prev[3][2])]})
            fx = room_fn(dilate(Ex[kx], ys_, ths_, cfg.get("hug", {}).get("lap_gap", 0.0015)), ys_, ths_)
            room = (lambda y, th, a=room, b=fx: np.fmax(a(y, th), b(y, th)))
        if prev is None:
            r0, floors = r_top, None
            s1 = s1 + 0.0
        else:
            ov, lap = lm.get("ov", 0.008), lm.get("lap", 0.004)
            s0 = prev[0][-1] - ov
            r0 = np.array([prev[2][j](s0[j]) + lap for j in range(len(ths))])
            s1 = s0 + ov + s1
            floors = [lambda s, f=prev[2][j], e=prev[0][-1, j]: np.where(s <= e + 0.002, f(s) + lap, np.nan)
                      for j in range(len(ths))]
        Sg, Rg, fns = hug_lame(room, skin_rho, ths, y_top, s0, r0, s1, lm.get("rows", 8), lm.get("a_in", 6.0),
                               lm.get("smax", 0.03), floors, sig=lm.get("sig", 1.0), min_len=lm.get("min_len", 0.012))
        G = wrap.pt(y_top[None] - Sg, ths[None], Rg)
        du, dv = np.gradient(G, axis=1), np.gradient(G, axis=0)
        Nl = U(np.cross(dv, du))
        o = wrap.dirs(ths)
        Nl = np.where(((Nl * o[None]).sum(-1) < 0)[..., None], -Nl, Nl)
        ex = None
        if pl.get("keel"):
            k_ = pl["keel"]
            xs = np.linalg.norm(G - G[:, [len(ths) // 2]], axis=-1)
            ex = k_["h"] * np.clip(1 - xs / (k_["w"] / 2), 0, 1)
        node = nm + lm.get("sfx", "") + "_rigid"
        rigid.append(kb.slab(node, M["plate"], G, Nl, pt_th, extra=ex))
        rigid[-1].name = node
        E = np.vstack([G[:, 0], G[-1, 1:], G[::-1, -1][1:]])
        gold = [kb.bead(Normals(G.reshape(-1, 3), Nl.reshape(-1, 3)), node[:-6] + "_rim", M["trim"], E, rim, edge_off,
                        False, relax_it=1)]
        b_ = pl.get("band")
        if b_ and lm.get("band", True) and float(np.median(Sg[-1] - Sg[0])) > b_.get("min_len", 0.03):
            Gs = G + Nl * (pt_th + (0 if ex is None else ex[..., None]))
            bv = lm.get("band_v", b_["v"])
            gold += interlace(Gs, Nl, 1.2, len(ths) - 2.2, bv[0], bv[1], b_["wl"], node[:-6] + "_band",
                              M["trim"], 0.0, [dict(rim, w=b_["border_w"], h=b_["border_h"], below=0.0003),
                                               dict(rim, w=b_["w"], h=b_["h"], below=0.0003)])
        rigid.append(Part.join(node, M["trim"], gold))
        ride_out.append({"match": node[:-6], "weights": side_ride(lm["ride"], h) if pl.get("mirror", True) else dict(lm["ride"]),
                         "mix": 1.0})
        if built is not None:  # (its inner face, for a plate built later that laps over it: lap_rooms)
            built.setdefault(nm, []).append((G, Nl, side_ride(lm["ride"], h) if pl.get("mirror", True) else dict(lm["ride"])))
        st = Rg - skin_rho(y_top[None] - Sg, np.broadcast_to(ths[None], Sg.shape))
        print(f"{node}: len {np.round((Sg[-1] - Sg[0]).min() * 1000)}-{np.round((Sg[-1] - Sg[0]).max() * 1000)} mm, "
              f"bottom y {np.round((y_top - Sg[-1]).min(), 3)}-{np.round((y_top - Sg[-1]).max(), 3)}, stand-off off her "
              f"skin mm: top {np.round(st[1].min() * 1000)}-{np.round(st[1].max() * 1000)}, bottom "
              f"{np.round(st[-1].min() * 1000)}-{np.round(st[-1].max() * 1000)}, max {np.round(st.max() * 1000)}")
        if prev is not None and ride_key(lm["ride"], h) != prev[4]:
            # (the lap through the clips: the lame above's bottom edge posed into this lame's frame, its highest per
            # column vs this lame's top: > 0 = they overlap in every frame of the demo clips)
            kx = f"{ride_key(lm['ride'], h)}|{h}|{nm}{k}edge"
            Ee, ys_, ths_ = sweep({kx: side_ride(lm["ride"], h)}, [], z0, extra={kx: [(prev[3][0][-1], prev[3][2])]}, verbose=False)
            it_ = np.round((ths + 180.0) / (ths_[1] - ths_[0])).astype(int) % len(ths_)
            fin = np.isfinite(Ee[kx][:, it_])
            ytop = np.where(fin.any(0), ys_[np.where(fin, np.arange(len(ys_))[:, None], 0).max(0)], np.nan)
            olap = (y_top - Sg[0]) - ytop
            print(f"{node} lap: overlap with the lame above through the demo clips, mm: min {np.round(np.nanmin(olap) * 1000, 1)} "
                  f"(rest {np.round((prev[0][-1] - Sg[0]).min() * 1000, 1)}), per column {np.round(olap * 1000).tolist()}")
        prev = (Sg, Rg, fns, (G, Nl, side_ride(lm["ride"], h) if pl.get("mirror", True) else dict(lm["ride"])),
                ride_key(lm["ride"], h))


RECIPES = {"brief": brief, "belt": belt}
