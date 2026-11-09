"""Her fit: her slider values and her residual, solved against the posed A (her_target.py), written as data the build
reads (specs/her.json, forms/her_v1.npz). Authoring only: the build never runs this. Pure numpy/scipy.

    python tools/body/wrap.py target <base.glb> <target.npz>
    python tools/body/wrap.py sliders <stage_dir> <samples.npz> <target.npz> <spec_in> <spec_out>
    python tools/body/wrap.py residual <stage_dir> <target.npz> <spec> <forms_out.npz>
    python tools/body/wrap.py topo-target|topo-sliders|topo-residual|topo-carry ...   (OUR topology: wrap_topo.py)
<stage_dir>: a build's stage/ (base.npz: the head's human V and, with sliders, the slider body Vs); <samples.npz>:
fit_sample.py's; <target.npz>: the posed A (`target`, posed to <base.glb>'s rest).

sliders:  the catalogue's sliders that best lay the base on her, by MPFB's own samples of each slider (V0 and each
          slider alone at a few values: the fit's model is their piecewise-linear sum; the build then evaluates the
          solved values exactly through MPFB, macros as its nonlinear blends), the region-weighted distance both
          ways between the close tier (as the build joins it under the head) and the posed A;
residual: per base point, in MakeHuman space (forms.py adds it before the subdivision; the helpers get their skin's
          so the skeleton follows), by region (see `residual`).
"""
import json
import os
import sys
import time

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import forms             # noqa: E402
import headmatch as hm   # noqa: E402
import pipeline          # noqa: E402
import stages            # noqa: E402
from gl import Glb       # noqa: E402

A_PATH = os.path.join(REPO, "godot", "art", "people", "heroine.glb")
MH_HAND = ("wrist", "metacarpal", "finger")
MH_FOOT = ("foot", "toe")
MH_ARM = ("upperarm", "lowerarm")
MH_SETS = {"hand": MH_HAND, "foot": MH_FOOT, "arm": MH_ARM, "thigh": ("upperleg",), "calf": ("lowerleg",),
           "pelvis": ("pelvis", "root"), "breast": ("breast",)}
A_HAND = ("hand_", "index_", "middle_", "ring_", "pinky_", "thumb_")
A_FOOT = ("foot_", "ball_")
A_ARM = ("upperarm", "lowerarm")
A_SETS = {"hand": A_HAND, "foot": A_FOOT, "arm": A_ARM + ("delt_",), "thigh": ("thigh_",), "calf": ("calf_",),
          "hips": ("pelvis", "glute_", "root"),
          "chest": ("spine_", "neck_", "breast_", "pec_", "lat_", "scap_", "clavicle_", "trap_", "panel_")}
# a base region's points match her points of these sets (her weight on them at least 0.2)
MATCH = {"neck": ("chest",), "chest": ("chest", "arm", "hips"), "hips": ("hips", "thigh", "chest"),
         "thigh": ("thigh", "hips", "calf"), "calf": ("calf", "thigh", "foot"), "arm": ("arm", "chest", "hand"),
         "hand": ("hand", "arm"), "foot": ("foot", "calf")}


def load_stage(stage_dir):
    z = np.load(os.path.join(stage_dir, "base.npz"))
    b = {k: z[k] for k in z.files if not k.startswith("g:")}
    b["groups"] = {k[2:]: z[k] for k in z.files if k.startswith("g:")}
    return b


def mh_groups(n):
    """Per base point: MakeHuman's weight on each set's bones (MH_SETS, both sides)."""
    w = stages.load_mh("weights.default.json")["weights"]
    out = {k: np.zeros(n) for k in MH_SETS}
    for bone, lst in w.items():
        stem = bone.split(".")[0]
        for k, pre in MH_SETS.items():
            if stem.startswith(pre):
                for i, x in lst:
                    out[k][int(i)] += float(x)
    return {k: np.clip(v, 0, 1) for k, v in out.items()}


def a_groups(body):
    """Per A point: her own skin weights on her hand, foot and arm bones."""
    names = body.sk.names
    out = {}
    nj = int(body.Jv.max()) + 1
    for k, pre in A_SETS.items():
        m = np.array([n.startswith(pre) for n in names] + [False] * max(0, nj - len(names)))
        out[k] = (body.W * m[body.Jv]).sum(1)
    return out


class Ctx:
    """The base's build up to the close tier (stages 2 and 3), for any V."""

    def __init__(self, stage_dir, spec):
        self.base = load_stage(stage_dir)
        self.spec = spec
        self.A = Glb(A_PATH)
        b0 = dict(self.base)
        b0.pop("Vs", None)
        self.pl = pipeline.stage_place(b0, self.A, {})
        self.V0 = self.base["V"]
        self.n = len(self.V0)
        self.mh = mh_groups(self.n)
        self.Sub = self.pl["Sub"]
        ti = self.close(self.V0)
        self.BF, self.inbody, self.ring = ti["BF"], ti["inbody"], ti["ring"]

    def close(self, V, E=None):
        b = dict(self.base, V=V)
        if E is not None:
            b["E"] = E
        return stages.stage_tiers(b, self.pl, self.spec, {})

    def points(self, V, E=None):
        """The close tier's points (glTF)."""
        return hm.to_gltf(self.close(V, E)["P2"])


class Target:
    def __init__(self, npz):
        z = np.load(npz)
        self.P, self.T, self.N = z["P"], z["T"], z["N"]
        self.g = {k: z["g_" + k] for k in A_SETS}
        self.tree = cKDTree(self.P)
        self.ground = float(z["ground"])
        self.bones = {k[2:]: z[k] for k in z.files if k.startswith("b_")}


def make_target(base_glb, out, world=False):
    import her_target as ht
    d = ht.target(base_glb, world=world)
    import skin   # (her_target put tools/anim on the path)
    from rig import Skeleton
    sk = Skeleton.load(skin.SKELETONS / "heroine_skeleton.json")
    body = skin.Body(sk, [(A_PATH, lambda n: n == "Heroine", "skin")], None, label="her", helpers=True)
    first, _ = ht.weld(body.P)
    g = a_groups(body)
    ground = float(body.P[:, 1].min())      # (her feet are not on Head: stored = world)
    np.savez(out, P=d["P"], T=d["T"], N=d["N"], ground=ground, **{"g_" + k: v[first] for k, v in g.items()},
             **{"b_" + k: np.stack(v) for k, v in d["bones"].items()})
    return d["turns"]


class SliderModel:
    def __init__(self, npz):
        z = np.load(npz)
        self.V0 = z["V0"]
        self.s = {}
        for k in z.files:
            if "@" in k:
                n, x = k.split("@")
                self.s.setdefault(n, []).append((float(x), z[k] - self.V0))
        for n in self.s:
            self.s[n] = sorted(self.s[n] + [(0.0, np.zeros_like(self.V0))], key=lambda t: t[0])

    def __call__(self, x):
        V = self.V0.copy()
        for n, v in x.items():
            xs = [a for a, _ in self.s[n]]
            v = float(np.clip(v, xs[0], xs[-1]))
            i = int(np.clip(np.searchsorted(xs, v) - 1, 0, len(xs) - 2))
            t = (v - xs[i]) / (xs[i + 1] - xs[i])
            V = V + (1 - t) * self.s[n][i][1] + t * self.s[n][i + 1][1]
        return V


def close_groups(ctx):
    return {k: np.asarray(ctx.Sub @ v) for k, v in ctx.mh.items()}


class Matcher:
    """Closest points on her surface for the base's points, region by region (MATCH): a base region's points look
    only at her triangles whose corners carry her weight on its sets, so a calf never takes her knee's front."""

    def __init__(self, tgt):
        import surfdist
        self.tgt = tgt
        self.S = {}
        for k, sets in MATCH.items():
            ok = np.zeros(len(tgt.P), bool)
            for st in sets:
                ok |= tgt.g[st] >= 0.2
            T = tgt.T[ok[tgt.T].all(1)]
            self.S[k] = surfdist.Surface(tgt.P, T)

    def closest(self, P, reg):
        q = np.zeros_like(P)
        n = np.zeros_like(P)
        d = np.full(len(P), np.inf)
        for i, k in enumerate(REGIONS):
            m = reg == i
            if m.any():
                q[m], n[m], _, d[m] = self.S[k].closest(P[m])
        return q, n, d


def fit_sliders(ctx, model, tgt, names, x0=None, rounds=8, sub=2):
    """Gauss-Newton on the slider values and the stance (forms.stance) with correspondences held each round (Matcher, point-to-plane plus a
    tenth point-to-point; the skeleton's shoulder, elbow, wrist, hip and knee onto hers; the sole onto her ground),
    bounded by the samples' range, damped toward the round's start."""
    from scipy.optimize import lsq_linear
    mt = Matcher(tgt)
    x = np.zeros(len(names) + 3) if x0 is None else np.asarray(x0, float)
    lo = np.array([model.s[n][0][0] for n in names] + [-0.3, -0.15, -0.15])     # + stance: pitch (rad), y, z (m)
    hi = np.array([model.s[n][-1][0] for n in names] + [0.3, 0.15, 0.15])
    REGW = {"neck": 0.0, "chest": 1.0, "hips": 1.0, "thigh": 1.0, "calf": 1.0, "arm": 1.0, "hand": 0.3, "foot": 0.6}

    ns = len(names)

    JOINTS = [f"{b}_{sd}" for sd in "lr" for b in ("upperarm", "lowerarm", "hand", "thigh", "calf")]
    aj = np.array([tgt.bones[n][0] for n in JOINTS])
    low_a = np.sort(tgt.P[:, 1])[:30].mean() - tgt.P[:, 1].min() + tgt.ground

    def feats(x):
        """The close tier's points, the skeleton's joints (placed as the build places them) and the sole's height."""
        V, _ = forms.join(ctx.V0, model(dict(zip(names, x[:ns]))), ctx.base["inbody"], ctx.pl)
        V = forms.stance(V, ctx.V0, ctx.base["inbody"], ctx.pl, stance_of(x[ns:]))
        ti = ctx.close(V)
        P = hm.to_gltf(ti["P2"])
        ends = stages.stage_skeleton(dict(ctx.base, V=V), ti, {})["ends"]
        bj = np.array([ends[n][0] for n in JOINTS])
        return P, bj, np.sort(P[ctx.inbody, 1])[:30].mean()
    P, bj, low = feats(x)
    reg = regions(ctx, P)
    idx = np.where(reg >= 0)[0][::sub]
    w = np.array([REGW[REGIONS[r]] for r in reg[idx]])
    # (the arm's joints weigh most: the arm takes its length from the sliders alone, LOOSE)
    wj = np.repeat(np.sqrt([3000.0 if n.startswith(("lowerarm", "hand")) else 300.0 for n in JOINTS]), 3)
    ws = np.sqrt(2000.0)
    h = 0.05
    for it in range(rounds):
        t0 = time.time()
        q, n, d = mt.closest(P[idx], reg[idx])
        good = w * (np.einsum("ij,ij->i", n, n) > 0)
        J = np.zeros((len(idx), 3, len(x)))
        Jj = np.zeros((len(JOINTS), 3, len(x)))
        Js = np.zeros(len(x))
        for c in range(len(x)):
            xc = x.copy()
            hc = h if c < ns else 0.01
            xc[c] = x[c] + hc if x[c] + hc <= hi[c] else x[c] - hc
            Pc, bjc, lowc = feats(xc)
            dx = xc[c] - x[c]
            J[:, :, c] = (Pc[idx] - P[idx]) / dx
            Jj[:, :, c] = (bjc - bj) / dx
            Js[c] = (lowc - low) / dx
        r0 = P[idx] - q
        Jn = np.einsum("ij,ijc->ic", n, J)
        rn = np.einsum("ij,ij->i", n, r0)
        Am = np.concatenate([good[:, None] * Jn, 0.3 * (good[:, None, None] * J).reshape(-1, len(x)),
                             wj[:, None] * Jj.reshape(-1, len(x)), ws * Js[None],
                             0.02 * np.sqrt(len(idx)) * np.eye(len(x))])
        bm = np.concatenate([-good * rn, -0.3 * (good[:, None] * r0).ravel(), -wj * (bj - aj).ravel(),
                             [-ws * (low - low_a)], np.zeros(len(x))])
        st = lsq_linear(Am, bm, bounds=(lo - x - 1e-12, hi - x + 1e-12))
        x = np.clip(x + st.x, lo, hi)
        P, bj, low = feats(x)
        print(f"round {it}: p50 {np.percentile(d, 50) * 1000:.2f} p95 {np.percentile(d, 95) * 1000:.2f} mm, joints "
              f"{np.linalg.norm(bj - aj, axis=1).max() * 1000:.1f} mm max, sole {(low - low_a) * 1000:+.1f} mm, step "
              f"{np.abs(st.x).max():.3f} ({time.time() - t0:.0f} s)", flush=True)
        if np.abs(st.x).max() < 0.005:
            break
    return dict(zip(names, [round(float(v), 4) for v in x[:ns]])), stance_of(x[ns:])


def stance_of(p):
    return {"pitch_deg": round(float(np.degrees(p[0])), 3), "move_m": [0.0, round(float(p[1]), 5), round(float(p[2]), 5)]}


REGIONS = ["neck", "chest", "hips", "thigh", "calf", "arm", "hand", "foot"]
TIGHT = ["neck", "chest", "hips", "thigh", "calf"]


def regions(ctx, P):
    """Each close point's region (index into REGIONS; -1 the head and the ring's band) by MakeHuman's weights."""
    g = close_groups(ctx)
    dep = -hm.s_split(hm.to_blender(P))
    r = np.full(len(P), REGIONS.index("chest"))
    r[g["pelvis"] > 0.4] = REGIONS.index("hips")
    for k in ("thigh", "calf", "arm", "hand", "foot"):
        r[g[k] > 0.5] = REGIONS.index(k)
    r[(dep < 0.10) & (r == REGIONS.index("chest"))] = REGIONS.index("neck")
    r[(dep < 0.005) | ~ctx.inbody] = -1
    return r


def report(P, reg, S, inbody):
    """Per region: B's points to the target surface S, p50/p95/max mm."""
    q, n, _, d = S.closest(P[inbody])
    rr = reg[inbody]
    out = {}
    for i, k in enumerate(REGIONS):
        m = rr == i
        if m.any():
            out[k] = [round(float(np.percentile(d[m], 50)) * 1000, 2), round(float(np.percentile(d[m], 95)) * 1000, 2),
                      round(float(d[m].max()) * 1000, 2)]
    return out


# ------------------------------------------------------------------------------------------------ the residual --
def smooth01(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def smooth_on(F, n, x, iters):
    """Neighbour averaging over the base mesh's edges, `iters` times (points off the skin untouched)."""
    L = stages.laplacian(F, n)
    deg = L.diagonal()
    Adj = sp.diags(deg) - L
    for _ in range(iters):
        x = np.where(deg > 0, (Adj @ x + x) / (deg + 1), x)
    return x


def zones(ctx):
    """Per base point (0..1): arm (LOOSE, from the shoulder cap to the hand), foot, tight (the rest), and hold (0 at
    the head's ring and its neighbours, 1 from HOLD_FULL_M under SPLIT: the residual eased in under the ring)."""
    F, n = ctx.base["F"], ctx.n
    a = smooth_on(F, n, np.clip(ctx.mh["arm"] + ctx.mh["hand"], 0, 1), 4)
    w_arm = smooth01((a - 0.2) / 0.6)
    f = smooth_on(F, n, ctx.mh["foot"], 2)
    w_foot = smooth01((f - 0.2) / 0.6)
    dep = forms.split_depth(ctx.V0, ctx.pl)
    hold = smooth01((dep - HOLD_ZERO_M) / (HOLD_FULL_M - HOLD_ZERO_M))
    return {"arm": w_arm, "foot": w_foot, "tight": (1 - w_arm) * (1 - w_foot), "hold": hold}


HOLD_ZERO_M = 0.012
HOLD_FULL_M = 0.03


def close_normals(ctx, P):
    BF = ctx.BF
    T = np.concatenate([BF[:, [0, 1, 2]], BF[:, [0, 2, 3]]])
    return stages.vertex_normals(P, T)


def base_rows(ctx):
    """The close tier's row of each base point it keeps (the subdivision keeps the used points first, in order)."""
    used = np.unique(ctx.base["F"])
    row = -np.ones(ctx.n, np.int64)
    row[used] = np.arange(len(used))
    return row


def icp_round(ctx, mt, P, reg, Ut, zn, lam, mu=0.1, crotch=None, max_d=0.08, min_dot=0.5):
    """One non-rigid ICP step on the TIGHT residual Ut (glTF metres, per base point, applied as tight * hold * Ut):
    correspondences held, the step U minimising point-to-plane + mu point-to-point + lam |L (Ut + U)|^2.
    Returns Ut + U."""
    s = ctx.pl["sim"][0]
    wt_b = zn["tight"] * zn["hold"]
    unk = np.where(ctx.base["inbody"] & (zn["hold"] > 0) & (wt_b > 1e-3))[0]
    wt_c = np.asarray(ctx.Sub @ wt_b)
    idx = np.where(np.isin(reg, [REGIONS.index(k) for k in TIGHT]) & (wt_c > 0.3))[0]
    q, n, d = mt.closest(P[idx], reg[idx])
    Nb = close_normals(ctx, P)[idx]
    ok = (d < max_d) & (np.einsum("ij,ij->i", Nb, n) > min_dot)
    idx, q, n, d = idx[ok], q[ok], n[ok], d[ok]
    w = np.sqrt(wt_c[idx])
    S_ = (ctx.Sub[idx][:, unk] @ sp.diags(wt_b[unk])).tocsr()
    k = len(unk)
    r0 = P[idx] - q
    A1 = sp.hstack([sp.diags(w * n[:, c]) @ S_ for c in range(3)])
    b1 = -w * np.einsum("ij,ij->i", n, r0)
    A2 = np.sqrt(mu) * sp.block_diag([sp.diags(w) @ S_] * 3)
    b2 = -np.sqrt(mu) * (w[:, None] * r0).T.ravel()
    L = stages.laplacian(ctx.base["F"], ctx.n)[unk][:, unk]
    lw = np.ones(k) if crotch is None else 1 + 4 * crotch[unk]
    Lw = sp.diags(lw) @ L
    Dg = Ut[unk]
    A3 = np.sqrt(lam) * sp.block_diag([Lw] * 3)
    b3 = -np.sqrt(lam) * np.concatenate([Lw @ Dg[:, c] for c in range(3)])
    A = sp.vstack([A1, A2, A3]).tocsc()
    b = np.concatenate([b1, b2, b3])
    M = (A.T @ A + 1e-9 * sp.eye(3 * k)).tocsc()
    u = spl.spsolve(M, A.T @ b)
    U = np.zeros((ctx.n, 3))
    U[unk] = u.reshape(3, k).T
    stats = {"pairs": int(len(idx)), "p50_mm": round(float(np.percentile(d, 50)) * 1000, 2),
             "p95_mm": round(float(np.percentile(d, 95)) * 1000, 2)}
    return Ut + U, stats


ARM_S = np.linspace(0.18, 1.94, 23)     # stations along the arm: 0 shoulder, 1 elbow, 2 wrist


def arm_param(X, sh, el, wr):
    """Each point's place along the arm (0 shoulder, 1 elbow, 2 wrist, beyond: the hand), the nearer segment's."""
    def seg(a, b):
        d = b - a
        t = (X - a) @ d / (d @ d)
        tc = np.clip(t, 0, 1)
        return t, np.linalg.norm(X - (a + tc[:, None] * d), axis=1)
    t1, d1 = seg(sh, el)
    t2, d2 = seg(el, wr)
    return np.where((d2 < d1) | (t2 > 1), 1 + t2, t1)


def arm_axis(s, sh, el, wr):
    """The bone's direction and line point at each place s."""
    up = s < 1
    a = np.where(up[:, None], sh, el)
    b = np.where(up[:, None], el, wr)
    t = np.where(up, s, s - 1)
    d = (b - a) / np.linalg.norm(b - a, axis=1, keepdims=True)
    return d, a + t[:, None] * (b - a)


def plane_cut(X, T, o, d):
    """Where the edges of triangles T (on points X) cross the plane through o with normal d."""
    h = (X - o) @ d
    E = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    a, b = h[E[:, 0]], h[E[:, 1]]
    m = (a * b) < 0
    t = a[m] / (a[m] - b[m])
    return X[E[m, 0]] + t[:, None] * (X[E[m, 1]] - X[E[m, 0]])


def section_perims(X, T, sx, js, stations, reach=0.06):
    """At each station: the mesh's cut by the plane across the bone there (its triangles within `reach` of the
    station's line point), its convex-hull perimeter and middle."""
    from scipy.spatial import ConvexHull
    out, mids = [], []
    for st in stations:
        d, p = arm_axis(np.array([st]), *js)
        d, p = d[0], p[0]
        near = np.linalg.norm(X - p, axis=1) < reach * 2
        tt = T[near[T].all(1)]
        C = plane_cut(X, tt, p, d)
        C = C[np.linalg.norm(C - p, axis=1) < reach * 1.6] if len(C) else C
        if len(C) < 8:
            out.append(np.nan)
            mids.append(np.full(3, np.nan))
            continue
        e1 = np.cross(d, [0, 0, 1.0])
        e1 /= np.linalg.norm(e1)
        e2 = np.cross(d, e1)
        Q = np.stack([(C - p) @ e1, (C - p) @ e2], 1)
        h = ConvexHull(Q)
        out.append(h.area)
        c2 = Q[h.vertices].mean(0)
        mids.append(p + c2[0] * e1 + c2[1] * e2)
    return np.array(out), np.array(mids)


def arm_profiles(ctx, P, ends, tgt, side, stations=ARM_S):
    """B's and her girth (hull perimeter) at the stations along one arm, and B's section middles."""
    jb = [ends[f"{b}_{side}"][0] for b in ("upperarm", "lowerarm", "hand")]
    ja = [tgt.bones[f"{b}_{side}"][0] for b in ("upperarm", "lowerarm", "hand")]
    g = close_groups(ctx)
    sgn = 1 if side == "l" else -1
    mb = ((g["arm"] + g["hand"]) > 0.3) & ctx.inbody & (P[:, 0] * sgn > 0)      # (the same rule as hers)
    BT = np.concatenate([ctx.BF[:, [0, 1, 2]], ctx.BF[:, [0, 2, 3]]])
    gb, cb = section_perims(P, BT[mb[BT].all(1)], None, jb, stations)
    ma = ((tgt.g["arm"] + tgt.g["hand"]) > 0.3) & (tgt.P[:, 0] * sgn > 0)
    ga, _ = section_perims(tgt.P, tgt.T[ma[tgt.T].all(1)], None, ja, stations)
    return gb, ga, cb, jb


def arm_field(ctx, P, ends, tgt, Vc, zn, rows, prev=None):
    """LOOSE: per arm, a smooth radial scale k(s) (her girth over B's at 23 stations 8 cm apart, low-passed, linear
    between), eased to 1 at the shoulder cap and over the hand) about B's section middles; the move per base
    point (MakeHuman space), weighted by the arm zone."""
    s_sim = ctx.pl["sim"][0]
    D = np.zeros((ctx.n, 3))
    info = {}
    used = rows >= 0
    for side in "lr":
        gb, ga, cb, jb = arm_profiles(ctx, P, ends, tgt, side)
        ok = np.isfinite(gb) & np.isfinite(ga)
        ratio = ga[ok] / gb[ok]
        so = ARM_S[ok]
        rs = np.convolve(np.pad(ratio, 1, mode="edge"), [0.25, 0.5, 0.25], "valid")     # (low-pass: 8 cm)
        sgn = 1 if side == "l" else -1
        Xb = P[rows[used]]
        idx = np.where(used)[0]
        m = (zn["arm"][idx] > 0) & (Xb[:, 0] * sgn > 0)
        idx, X = idx[m], Xb[m]
        sx = arm_param(X, *jb)
        k = np.interp(sx, so, rs)
        ease = smooth01((sx - 0.0) / 0.12) * (1 - smooth01((sx - 2.0) / 0.25))
        k = 1 + (k - 1) * ease
        dax, pax = arm_axis(np.clip(sx, 0, 2), *jb)
        mid = np.stack([np.interp(np.clip(sx, ARM_S[ok][0], ARM_S[ok][-1]), ARM_S[ok], cb[ok][:, j]) for j in range(3)], 1)
        rel = X - mid
        rel -= dax * np.einsum("ij,ij->i", rel, dax)[:, None]
        U = (k - 1)[:, None] * rel
        D[idx] = hm.to_blender(U) / s_sim * zn["arm"][idx, None]
        info[side] = {"stations": [round(float(x), 3) for x in ARM_S[ok]], "ratio": [round(float(x), 4) for x in ratio],
                      "smoothed": [round(float(x), 4) for x in rs]}
    return D, info


def helpers_follow(V0, inbody, D, k=16):
    """The helpers' (joint cubes', off the skin) move: the inverse-square mean of their k nearest skin points'."""
    skin = np.where(inbody)[0]
    d, j = cKDTree(V0[skin]).query(V0[~inbody], k=k)
    w = 1 / np.maximum(d, 1e-4) ** 2
    out = D.copy()
    out[~inbody] = np.einsum("ik,ikc->ic", w, D[skin[j]]) / w.sum(1, keepdims=True)
    return out


def crotch_weight(ctx, P, rows, ends):
    """1 at her crotch (the middle under the hip joints), eased out: the residual is stiffer there (a smooth form)."""
    hy = 0.5 * (ends["thigh_l"][0][1] + ends["thigh_r"][0][1])
    X = np.zeros((ctx.n, 3))
    X[rows >= 0] = P[rows[rows >= 0]]
    w = (1 - smooth01((np.abs(X[:, 0]) - 0.03) / 0.04)) * (1 - smooth01((X[:, 1] - hy) / 0.05)) * \
        smooth01((X[:, 1] - (hy - 0.16)) / 0.04)
    return w * (rows >= 0)


LAMBDAS = [30.0, 10.0, 3.0, 1.0, 0.3, 0.1, 0.03, 0.01, 0.01, 0.01]


def residual(ctx, tgt, Vc, lambdas=LAMBDAS, arm_passes=4, log=print):
    """Her residual D (per base point, MakeHuman space) on the composed body Vc (sliders and stance in)."""
    s = ctx.pl["sim"][0]
    zn = zones(ctx)
    mt = Matcher(tgt)
    rows = base_rows(ctx)
    pairs = forms.mirror_pairs(ctx.V0)
    inb = ctx.base["inbody"]
    wt_b = zn["tight"] * zn["hold"]
    Ut = np.zeros((ctx.n, 3))
    Darm = np.zeros((ctx.n, 3))
    tf = {"l": np.zeros(3), "r": np.zeros(3)}
    side_b = np.where(ctx.V0[:, 0] >= 0, "l", "r")
    band = inb & (zn["foot"] > 0.3) & (zn["foot"] < 0.7)

    def D_of(Ut, Darm, tf):
        D = hm.to_blender(Ut * wt_b[:, None]) / s + Darm
        for sd in "lr":
            m = side_b == sd
            D[m] += hm.to_blender(tf[sd][None])[0] / s * (zn["foot"][m] * zn["hold"][m])[:, None]
        D = helpers_follow(ctx.V0, inb, D)
        return forms.symmetrize(D, pairs)

    def mirror_gltf(U):
        out = U.copy()
        ok = pairs >= 0
        out[ok] = 0.5 * (U[ok] + U[pairs[ok]] * np.array([-1.0, 1, 1]))
        return out

    def feet(Ut):
        """The feet's one move each: the tight field's mean over the ankle band, its height set so the sole stands
        on her ground."""
        out = {}
        for sd in "lr":
            m = band & (side_b == sd)
            out[sd] = (Ut[m] * wt_b[m, None]).sum(0) / max(wt_b[m].sum(), 1e-9)
        return out

    crotch = None
    hist = []
    for it, lam in enumerate(lambdas):
        t0 = time.time()
        D = D_of(Ut, Darm, tf)
        ti = ctx.close(Vc + D)
        P = hm.to_gltf(ti["P2"])
        if crotch is None:
            ends = stages.stage_skeleton(dict(ctx.base, V=Vc + D), ti, {})["ends"]
            crotch = crotch_weight(ctx, P, rows, ends)
        reg = regions(ctx, P)
        Ut, st = icp_round(ctx, mt, P, reg, Ut, zn, lam, crotch=crotch)
        Ut = mirror_gltf(Ut)
        tf = feet(Ut)
        # the sole on her ground: the lowest points of each foot
        P = ctx.points(Vc + D_of(Ut, Darm, tf))
        for sd in "lr":
            m = ctx.inbody & (P[:, 0] * (1 if sd == "l" else -1) > 0.02)
            tf[sd][1] += tgt.ground - P[m, 1].min()
        hist.append(dict(lam=lam, **st))
        log(f"icp {it} lam {lam}: {st} ({time.time() - t0:.0f} s)")
    for ap in range(arm_passes):
        D = D_of(Ut, Darm, tf)
        ti = ctx.close(Vc + D)
        P = hm.to_gltf(ti["P2"])
        ends = stages.stage_skeleton(dict(ctx.base, V=Vc + D), ti, {})["ends"]
        dA, info = arm_field(ctx, P, ends, tgt, Vc, zn, rows)
        Darm = Darm + dA
        log(f"arm pass {ap}: ratio l {min(info['l']['ratio']):.3f}..{max(info['l']['ratio']):.3f}")
    D = D_of(Ut, Darm, tf)
    return D, {"icp": hist, "feet_move_m": {k: [round(float(x), 5) for x in v] for k, v in tf.items()}}



DETAIL_LAMBDAS = [0.3, 0.1, 0.03, 0.01, 0.01]


def detail(ctx, tgt, V, lambdas=DETAIL_LAMBDAS, mu=0.1, pin=10.0, log=print, max_d=0.05, min_dot=0.5):
    """Her residual's detail E per close point (Blender axes, placed; forms.py): non-rigid ICP on the close tier over
    TIGHT (to the head's ring, which stays put), a Laplacian of E on the close mesh as the stiffness, E held to 0 in
    the LOOSE arms, the hands and the feet; mirror-averaged each round."""
    zn = zones(ctx)
    mt = Matcher(tgt)
    wt_c = np.clip(np.asarray(ctx.Sub @ zn["tight"]), 0, 1)
    n2 = len(wt_c)
    ring = np.zeros(n2, bool)
    ring[ctx.ring] = True
    unk = np.where(ctx.inbody & ~ring)[0]
    k = len(unk)
    L = stages.laplacian(ctx.BF, n2)[unk][:, unk]
    E = np.zeros((n2, 3))
    P = ctx.points(V)
    pr = forms.mirror_pairs(P, 1e-5)
    hist = []
    for it, lam in enumerate(lambdas):
        P = ctx.points(V, E)
        reg = regions(ctx, P)
        idx = np.where(np.isin(reg, [REGIONS.index(r) for r in TIGHT]) & (wt_c > 0.3) & ~ring)[0]
        q, n, d = mt.closest(P[idx], reg[idx])
        Nb = close_normals(ctx, P)[idx]
        ok = (d < max_d) & (np.einsum("ij,ij->i", Nb, n) > min_dot)
        idx, q, n, d = idx[ok], q[ok], n[ok], d[ok]
        col = -np.ones(n2, np.int64)
        col[unk] = np.arange(k)
        Ssel = sp.csr_matrix((np.ones(len(idx)), (np.arange(len(idx)), col[idx])), shape=(len(idx), k))
        w = np.sqrt(wt_c[idx])
        r0 = P[idx] - q
        A1 = sp.hstack([sp.diags(w * n[:, c]) @ Ssel for c in range(3)])
        b1 = -w * np.einsum("ij,ij->i", n, r0)
        A2 = np.sqrt(mu) * sp.block_diag([sp.diags(w) @ Ssel] * 3)
        b2 = -np.sqrt(mu) * (w[:, None] * r0).T.ravel()
        Eg = hm.to_gltf(E)[unk]
        A3 = np.sqrt(lam) * sp.block_diag([L] * 3)
        b3 = -np.sqrt(lam) * np.concatenate([L @ Eg[:, c] for c in range(3)])
        pw = np.sqrt(pin) * (1 - wt_c[unk])
        A4 = sp.block_diag([sp.diags(pw)] * 3)
        b4 = -np.concatenate([pw * Eg[:, c] for c in range(3)])
        A = sp.vstack([A1, A2, A3, A4]).tocsc()
        b = np.concatenate([b1, b2, b3, b4])
        u = spl.spsolve((A.T @ A + 1e-10 * sp.eye(3 * k)).tocsc(), A.T @ b)
        Eg = Eg + u.reshape(3, k).T
        Eb = np.zeros((n2, 3))
        Eb[unk] = hm.to_blender(Eg)
        ok2 = (pr >= 0) & ctx.inbody
        Em = Eb.copy()
        Em[ok2] = 0.5 * (Eb[ok2] + Eb[pr[ok2]] * np.array([-1.0, 1, 1]))
        Em[ring] = 0.0
        E = Em
        st = {"lam": lam, "pairs": int(len(idx)), "p50_mm": round(float(np.percentile(d, 50)) * 1000, 2),
              "p95_mm": round(float(np.percentile(d, 95)) * 1000, 2)}
        hist.append(st)
        log(f"detail {it}: {st}")
    return E, hist


def main():
    a = sys.argv[1:]
    if a[0].startswith("topo-"):
        import wrap_topo          # her forms on OUR topology (P1 C): wrap_topo.py's docstring
        return wrap_topo.main(a)
    if a[0] == "target":
        print(make_target(a[1], a[2]))
    elif a[0] == "sliders":
        import sliders
        stage, samples, tnpz, spec_in, spec_out = a[1:6]
        spec = sliders.load_spec(spec_in)
        ctx = Ctx(stage, spec)
        model = SliderModel(samples)
        names = list(model.s)
        x, stn = fit_sliders(ctx, model, Target(tnpz), names, rounds=14)
        out = json.load(open(spec_in))
        out.update(sliders=x, stance=stn)
        json.dump(out, open(spec_out, "w"), indent=1)
    elif a[0] == "residual":
        import sliders
        stage, tnpz, spec_path, out = a[1:5]
        spec = sliders.load_spec(spec_path)
        spec.pop("forms", None)
        ctx = Ctx(stage, spec)
        tgt = Target(tnpz)
        Vc = forms.compose(ctx.base, ctx.pl, spec, {})["V"]
        D, info = residual(ctx, tgt, Vc)
        E, hist = detail(ctx, tgt, Vc + D)
        np.savez_compressed(out, D=D.astype(np.float32), E=E.astype(np.float32),
                            about=np.array("tools/body/wrap.py residual: D per base point (MakeHuman space), E per "
                                           "close point (placed, Blender axes); forms.py applies them"))
        print(json.dumps({"feet_move_m": info["feet_move_m"], "detail": hist[-1]}))


if __name__ == "__main__":
    main()
