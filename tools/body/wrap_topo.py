"""P1 C: her forms on OUR topology. Her slider values, stance and residual, solved against the posed A (her_target.py),
written as data build_topo.py reads (specs/her_topo.json; forms/her_topo_{close,play}.npz). Authoring only: the build
never runs this. Numpy/scipy, no Blender, no MakeHuman data: the model is build_topo.py's own stages 1-2 (OurSliders
on our topology, the stance, the neck ring snapped onto her head), the skeleton ours (landmarks.json), the regions
our topology's part and ring ids. The commands (wrap.py's topo-* subcommands, one per step):

    python tools/body/wrap.py topo-target   <slider-stage body.glb> <target.npz>           (`target`, her head's world rest)
    python tools/body/wrap.py topo-sliders  <spec_in> <target.npz> <spec_out> [<forms_{tier}.npz>]
    python tools/body/wrap.py topo-residual <spec> <target.npz> <forms_close.npz>
    python tools/body/wrap.py topo-carry    <forms_close.npz> <forms_play.npz> [<spec> <target.npz>]
    python tools/body/wrap.py topo-chain    <spec_start> <spec_out> <forms_pattern> <work_dir>   (all of them, in order)
her_topo: python tools/body/wrap.py topo-chain tools/body/specs/her.json tools/body/specs/her_topo.json
          tools/body/forms/her_topo_{tier}.npz tools/body/out/her_topo_fit   (~6 min)

topo-sliders:  Gauss-Newton on the slider values + the stance (pitch, y, z), correspondences held each round
               (region-matched closest points on her: point-to-plane plus a tenth point-to-point), our skeleton's
               shoulder, elbow, wrist, hip and knee onto hers, the sole onto her ground; the model is the build
               itself (stage_base + stage_place), Jacobians by finite differences.
topo-residual: R per our vertex (glTF m, added after the ring snap: build_topo stage 2b), by zone:
               TIGHT (neck under the hold, trunk, breast, crotch, thighs, knees, shins): non-rigid ICP (point-to-plane
               + 0.1 point-to-point + lam |L R|^2 on our quads' graph Laplacian, lam stepped down, stiffer x5 at the
               crotch), mirror-averaged each round (eased out within 10 cm of her asymmetric head ring);
               LOOSE arms (shoulder's outer rings to the wrist): her girth over ours at 23 stations, a smooth radial
               scale about our section middles (our loops keep their flow, only their size changes);
               hands: no residual (the template; the sliders give her size); feet: one move per side (the ankle
               band's mean TIGHT move, its height so the sole stands on her ground), the template's shape kept;
               hold: 0 on the head's ring, full 8 mm under SPLIT (the seam is the head's, her neck under it hers);
               relax: the TIGHT points slid along the fitted skin back to the slider stage's spacing (`relax`);
               seam: the rows between the ring and 15 mm under it: R lerped ring -> anchor, onto her skin (`restrip`).
topo-carry:    the play tier's R = close's R at each play vertex's closest point on close's reference surface
               (barycentric on close's triangles, the two tiers' rest surfaces are the same reference's, topo_corr):
               one shape for both tiers (no LOD pop), no second fit; mirror-averaged, 0 on the ring;
               play's own seam rows re-laid (`restrip`, with the spec and target).
Derivation: (a) the game's need (her approved sculpt as data on our base); (b) the named reference A
(godot/art/people/heroine.glb, Mesh_0 "Heroine"), posed by her own game stack; (c) the method inherited from wrap.py
(its v1 fit on hm08, TIGHT p95 ~1.7 mm), every MakeHuman id replaced by our topology's labels.
"""
import json
import os
import sys
import time

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import build_topo as bt  # noqa: E402
import headbake          # noqa: E402
import skeleton as skm   # noqa: E402
import stages            # noqa: E402
import wrap              # noqa: E402
from gl import Glb       # noqa: E402

REGIONS = wrap.REGIONS          # neck chest hips thigh calf arm hand foot
TIGHT = wrap.TIGHT
HOLD_ZERO_M, HOLD_FULL_M = 0.0, 0.008     # 0 on the ring, full by its second row (our neck rows are 5 mm apart; v1's
                                          # 12..30 mm was MakeHuman's coarse rows, and left her neck 17 mm off there)
FOOT_EASE_M = 0.05              # the foot's move eased out up the shin over 5 cm above the template's top
HIP_UP_M = 0.09                 # "hips": the trunk under 9 cm above the hip joints (MakeHuman's pelvis weight's reach)
s01 = wrap.smooth01


def pidx(z, name):
    return list(map(str, z["parts"])).index(name)


def labels(z, V0, ends):
    """Per vertex of our topology (fixed attributes, from the reference rest V0 and its skeleton): the fit's region
    (index into REGIONS, -1 the ring's band), the formcheck region (formcheck.REG), and the zones (arm, foot, hold,
    tight; 0..1)."""
    part = z["part"]
    P = {n: part == pidx(z, n) for n in map(str, z["parts"])}
    dep = bt.split_depth(V0)
    y = V0[:, 1]
    hip_y, knee_y = ends["thigh_l"][0][1], ends["calf_l"][0][1]
    sh = np.clip((z["ring"] - 1) / 7.0, 0, 1) * P["shoulder"]       # shoulder rings 1 (trunk) .. 8 (arm root)
    w_arm = np.where(P["arm"] | P["elbow"] | P["forearm"] | P["hand"], 1.0, s01((sh - 0.2) / 0.8) * P["shoulder"])
    y_ft = y[P["foot"]].max()
    w_foot = np.where(P["foot"], 1.0, (1 - s01((y - y_ft) / FOOT_EASE_M)) * P["shin"])
    hold = s01((dep - HOLD_ZERO_M) / (HOLD_FULL_M - HOLD_ZERO_M))
    hold[bt.boundary_ring(z["Q"], len(V0))] = 0.0
    R = REGIONS.index
    reg = np.full(len(V0), R("chest"))
    reg[(P["trunk"] & (y < hip_y + HIP_UP_M)) | P["crotch"]] = R("hips")
    reg[P["thigh"] | (P["knee"] & (y >= knee_y))] = R("thigh")
    reg[P["shin"] | (P["knee"] & (y < knee_y))] = R("calf")
    reg[P["arm"] | P["elbow"] | P["forearm"] | (P["shoulder"] & (sh >= 0.5))] = R("arm")
    reg[P["hand"]] = R("hand")
    reg[P["foot"]] = R("foot")
    reg[(dep < 0.10) & (reg == R("chest"))] = R("neck")
    reg[dep < 0.002] = -1
    import formcheck as fc
    F = fc.REG.index
    names = {"neck": "neck", "chest": "torso", "hips": "hips", "thigh": "thigh", "calf": "calf", "arm": "arm",
             "hand": "hand", "foot": "foot"}
    freg = np.array([F(names[REGIONS[r]]) if r >= 0 else -1 for r in reg])
    freg[P["breast"] & (reg == R("chest"))] = F("bust")
    freg[P["shoulder"] | (P["shin"] & (w_foot > 0.05))] = F("band")
    freg[dep < 0.0] = -1
    return {"reg": reg, "freg": freg, "arm": w_arm, "foot": w_foot, "hold": hold,
            "tight": (1 - w_arm) * (1 - w_foot)}


def tier_labels(tier):
    """labels() for a tier from its files alone (formcheck.py's topology mode): (z, labels)."""
    z = bt.load_tier(tier)[0]
    with open(os.path.join(HERE, "skeleton.json")) as f:
        skel = json.load(f)
    with open(os.path.join(HERE, "base", "landmarks.json")) as f:
        table = json.load(f)["tiers"][tier]
    V0 = z["V"].astype(np.float64)
    return z, labels(z, V0, skm.place_skeleton_ours(skel, V0, table)[3])


def mirror_pairs(z):
    """Each vertex's mirror partner (both ways; the midline its own), from the topology's mirror_of."""
    n = len(z["V"])
    pr = np.arange(n)
    mo = z["mirror_of"]
    r = np.where(mo >= 0)[0]
    pr[r] = mo[r]
    pr[mo[r]] = r
    return pr


def symmetrize(D, pr, w=None):
    """D mirror-averaged (w: per point, 1 = fully, 0 = left as is)."""
    Dm = 0.5 * (D + D[pr] * np.array([-1.0, 1, 1]))
    return Dm if w is None else D + w[:, None] * (Dm - D)


DATA_FROM_M = 0.0                       # the ICP's data from this depth under SPLIT (above: the Laplacian alone)
SYM_FREE_M, SYM_FULL_M = 0.03, 0.10     # her head (and its ring) is not symmetric: R mirror-averaged in full from
                                        # 10 cm under SPLIT, free within 3 cm (the neck meets her ring as she does)


class Model:
    """build_topo.py's stages 1, 2 and 2b for any sliders, stance and residual; our skeleton on the result."""

    def __init__(self, spec, tier="close"):
        self.spec = {k: v for k, v in spec.items() if k not in ("forms", "forms_topo")}
        self.tier = tier
        self.pre = bt.load_tier(tier)
        self.z = self.pre[0]
        self.V0 = self.z["V"].astype(np.float64)
        self.n = len(self.V0)
        self.Q = self.z["Q"]
        self.T = np.concatenate([self.Q[:, [0, 1, 2]], self.Q[:, [0, 2, 3]]])
        self.A = Glb(os.path.join(REPO, spec["ref"]))
        self.baked = headbake.bake(self.A, ["HeroineHead"])
        with open(os.path.join(HERE, "skeleton.json")) as f:
            self.skel = json.load(f)
        with open(os.path.join(HERE, "base", "landmarks.json")) as f:
            self.table = json.load(f)["tiers"][tier]
        self.ring = bt.boundary_ring(self.Q, self.n)
        self.lab = labels(self.z, self.V0, self.ends(self.V0))
        self.pr = mirror_pairs(self.z)
        self.L = stages.laplacian(self.Q, self.n)
        self.dep = bt.split_depth(self.V0)
        self.symw = s01((bt.split_depth(self.V0) - SYM_FREE_M) / (SYM_FULL_M - SYM_FREE_M))

    def body(self, sliders, stance, R=None):
        spec = dict(self.spec, sliders=sliders, stance=stance)
        rep = {}
        z, V = bt.stage_base(spec, self.tier, rep, pre=self.pre)
        V, _, _ = bt.stage_place(spec, z, V, self.A, self.baked, rep)
        return V if R is None else V + R

    def ends(self, V):
        return skm.place_skeleton_ours(self.skel, V, self.table)[3]

    def normals(self, V):
        return stages.vertex_normals(V, self.T)


# --------------------------------------------------------------------------------------------- the sliders --
def fit_sliders(md, tgt, names, x0, rounds=14, sub=2, log=print, R=None, mp=None, Rp=None):
    """wrap.fit_sliders' Gauss-Newton on our build: x = slider values + (pitch rad, y m, z m). R: a residual held
    fixed on top (the second pass: the sliders see the skeleton and surface the forms give). mp (and Rp): the play
    tier's Model (and residual): its arm segments weigh as close's (one spec builds both tiers; their landmark
    tables place the shoulder up to 2 mm apart)."""
    from scipy.optimize import lsq_linear
    mt = wrap.Matcher(tgt)
    sl = md.pre[1]
    ns = len(names)
    x = np.asarray(x0, float)
    lo = np.array([sl.knots[n][0] for n in names] + [-0.3, -0.15, -0.15])
    hi = np.array([sl.knots[n][-1] for n in names] + [0.3, 0.15, 0.15])
    REGW = {"neck": 0.0, "chest": 1.0, "hips": 1.0, "thigh": 1.0, "calf": 1.0, "arm": 1.0, "hand": 0.3, "foot": 0.6}
    JOINTS = [f"{b}_{sd}" for sd in "lr" for b in ("upperarm", "lowerarm", "hand", "thigh", "calf")]
    aj = np.array([tgt.bones[n][0] for n in JOINTS])
    # the arm's two segments joint to joint (shoulder-elbow, elbow-wrist): their lengths weigh most (the joints'
    # places differ by convention, ours placed by landmarks.json, hers by her rig; the lengths are what animation reads)
    SEG = [(JOINTS.index(f"upperarm_{sd}"), JOINTS.index(f"lowerarm_{sd}")) for sd in "lr"] +           [(JOINTS.index(f"lowerarm_{sd}"), JOINTS.index(f"hand_{sd}")) for sd in "lr"]
    la = np.array([np.linalg.norm(aj[j] - aj[i]) for i, j in SEG])
    wl = np.sqrt(30000.0)

    def seglen(bj):
        return np.array([np.linalg.norm(bj[j] - bj[i]) for i, j in SEG])
    low_a = np.sort(tgt.P[:, 1])[:30].mean() - tgt.P[:, 1].min() + tgt.ground

    def stance(p):
        return {"pitch_deg": float(np.degrees(p[0])), "move_m": [0.0, float(p[1]), float(p[2])]}

    def feats(x):
        sx, tx = dict(zip(names, x[:ns])), stance(x[ns:])
        V = md.body(sx, tx, R)
        e = md.ends(V)
        bj = np.array([e[n][0] for n in JOINTS])
        L = seglen(bj)
        if mp is not None:
            ep = mp.ends(mp.body(sx, tx, Rp))
            L = np.concatenate([L, seglen(np.array([ep[n][0] for n in JOINTS]))])
        return V, bj, np.sort(V[:, 1])[:30].mean(), L

    reg = md.lab["reg"]
    idx = np.where(reg >= 0)[0][::sub]
    w = np.array([REGW[REGIONS[r]] for r in reg[idx]])
    wj = np.repeat(np.sqrt([3000.0 if n.startswith(("lowerarm", "hand")) else 300.0 for n in JOINTS]), 3)
    ws = np.sqrt(2000.0)
    h = 0.05
    if mp is not None:
        la = np.concatenate([la, la])
    V, bj, low, Lb = feats(x)
    for it in range(rounds):
        t0 = time.time()
        q, nq, d = mt.closest(V[idx], reg[idx])
        good = w * (np.einsum("ij,ij->i", nq, nq) > 0)
        J = np.zeros((len(idx), 3, len(x)))
        Jj = np.zeros((len(JOINTS), 3, len(x)))
        Js = np.zeros(len(x))
        Jl = np.zeros((len(la), len(x)))
        for c in range(len(x)):
            xc = x.copy()
            hc = h if c < ns else 0.01
            xc[c] = x[c] + hc if x[c] + hc <= hi[c] else x[c] - hc
            Vc, bjc, lowc, Lc = feats(xc)
            dx = xc[c] - x[c]
            J[:, :, c] = (Vc[idx] - V[idx]) / dx
            Jj[:, :, c] = (bjc - bj) / dx
            Js[c] = (lowc - low) / dx
            Jl[:, c] = (Lc - Lb) / dx
        r0 = V[idx] - q
        Jn = np.einsum("ij,ijc->ic", nq, J)
        rn = np.einsum("ij,ij->i", nq, r0)
        Am = np.concatenate([good[:, None] * Jn, 0.3 * (good[:, None, None] * J).reshape(-1, len(x)),
                             wj[:, None] * Jj.reshape(-1, len(x)), ws * Js[None], wl * Jl,
                             0.02 * np.sqrt(len(idx)) * np.eye(len(x))])
        bm = np.concatenate([-good * rn, -0.3 * (good[:, None] * r0).ravel(), -wj * (bj - aj).ravel(),
                             [-ws * (low - low_a)], -wl * (Lb - la), np.zeros(len(x))])
        st = lsq_linear(Am, bm, bounds=(lo - x - 1e-12, hi - x + 1e-12))
        x = np.clip(x + st.x, lo, hi)
        V, bj, low, Lb = feats(x)
        log(f"round {it}: p50 {np.percentile(d, 50) * 1000:.2f} p95 {np.percentile(d, 95) * 1000:.2f} mm, joints "
            f"{np.linalg.norm(bj - aj, axis=1).max() * 1000:.1f} mm max, arm segments "
            f"{np.abs(Lb - la).max() * 1000:.1f} mm max, sole {(low - low_a) * 1000:+.1f} mm, step "
            f"{np.abs(st.x).max():.3f} ({time.time() - t0:.0f} s)")
        if np.abs(st.x).max() < 0.005:
            break
    p = x[ns:]
    return (dict(zip(names, [round(float(v), 4) for v in x[:ns]])),
            {"pitch_deg": round(float(np.degrees(p[0])), 3), "move_m": [0.0, round(float(p[1]), 5), round(float(p[2]), 5)]})


# -------------------------------------------------------------------------------------------- the residual --
LAMBDAS = [30.0, 10.0, 3.0, 1.0, 0.3, 0.1, 0.03, 0.01, 0.01, 0.01]


def icp_round(md, mt, V, Ut, lam, crotch, mu=0.1, max_d=0.08, min_dot=0.5):
    """One non-rigid ICP step on the TIGHT field Ut (applied as tight * hold * Ut): correspondences held, the step U
    minimising point-to-plane + mu point-to-point + lam |Lw (Ut + U)|^2 (Lw: the graph Laplacian, x5 at the crotch)."""
    lab = md.lab
    wt = lab["tight"] * lab["hold"]
    unk = np.where(wt > 1e-3)[0]
    reg = lab["reg"]
    idx = np.where(np.isin(reg, [REGIONS.index(k) for k in TIGHT]) & (wt > 0.3) & (md.dep >= DATA_FROM_M))[0]
    q, n, d = mt.closest(V[idx], reg[idx])
    Nb = md.normals(V)[idx]
    ok = (d < max_d) & (np.einsum("ij,ij->i", Nb, n) > min_dot)
    idx, q, n, d = idx[ok], q[ok], n[ok], d[ok]
    col = -np.ones(md.n, np.int64)
    col[unk] = np.arange(len(unk))
    k = len(unk)
    S_ = sp.csr_matrix((wt[idx], (np.arange(len(idx)), col[idx])), shape=(len(idx), k))
    w = np.sqrt(wt[idx])
    r0 = V[idx] - q
    A1 = sp.hstack([sp.diags(w * n[:, c]) @ S_ for c in range(3)])
    b1 = -w * np.einsum("ij,ij->i", n, r0)
    A2 = np.sqrt(mu) * sp.block_diag([sp.diags(w) @ S_] * 3)
    b2 = -np.sqrt(mu) * (w[:, None] * r0).T.ravel()
    L = md.L[unk][:, unk]
    Lw = sp.diags(1 + 4 * crotch[unk]) @ L
    Dg = Ut[unk]
    A3 = np.sqrt(lam) * sp.block_diag([Lw] * 3)
    b3 = -np.sqrt(lam) * np.concatenate([Lw @ Dg[:, c] for c in range(3)])
    A = sp.vstack([A1, A2, A3]).tocsc()
    b = np.concatenate([b1, b2, b3])
    u = spl.spsolve((A.T @ A + 1e-9 * sp.eye(3 * k)).tocsc(), A.T @ b)
    U = np.zeros((md.n, 3))
    U[unk] = u.reshape(3, k).T
    return Ut + U, {"pairs": int(len(idx)), "p50_mm": round(float(np.percentile(d, 50)) * 1000, 2),
                    "p95_mm": round(float(np.percentile(d, 95)) * 1000, 2)}


def crotch_weight(V, ends):
    """1 at her crotch (the middle under the hip joints), eased out (wrap.crotch_weight's rule)."""
    hy = 0.5 * (ends["thigh_l"][0][1] + ends["thigh_r"][0][1])
    return (1 - s01((np.abs(V[:, 0]) - 0.03) / 0.04)) * (1 - s01((V[:, 1] - hy) / 0.05)) * s01((V[:, 1] - (hy - 0.16)) / 0.04)


def arm_field(md, V, ends, tgt):
    """LOOSE (wrap.arm_field's rule): per arm a smooth radial scale k(s), her girth over ours at 23 stations, low-passed,
    eased to 1 at the shoulder cap and over the hand, about our section middles; weighted by the arm zone."""
    lab = md.lab
    D = np.zeros((md.n, 3))
    info = {}
    S = wrap.ARM_S
    for side in "lr":
        sgn = 1 if side == "l" else -1
        jb = [ends[f"{b}_{side}"][0] for b in ("upperarm", "lowerarm", "hand")]
        ja = [tgt.bones[f"{b}_{side}"][0] for b in ("upperarm", "lowerarm", "hand")]
        mb = (lab["arm"] > 0.3) & (V[:, 0] * sgn > 0)
        gb, cb = wrap.section_perims(V, md.T[mb[md.T].all(1)], None, jb, S)
        ma = ((tgt.g["arm"] + tgt.g["hand"]) > 0.3) & (tgt.P[:, 0] * sgn > 0)
        ga, _ = wrap.section_perims(tgt.P, tgt.T[ma[tgt.T].all(1)], None, ja, S)
        ok = np.isfinite(gb) & np.isfinite(ga)
        ratio = ga[ok] / gb[ok]
        rs = np.convolve(np.pad(ratio, 1, mode="edge"), [0.25, 0.5, 0.25], "valid")
        idx = np.where((lab["arm"] > 0) & (V[:, 0] * sgn > 0))[0]
        X = V[idx]
        sx = wrap.arm_param(X, *jb)
        kk = np.interp(sx, S[ok], rs)
        ease = s01(sx / 0.12) * (1 - s01((sx - 2.0) / 0.25))
        kk = 1 + (kk - 1) * ease
        dax, _ = wrap.arm_axis(np.clip(sx, 0, 2), *jb)
        mid = np.stack([np.interp(np.clip(sx, S[ok][0], S[ok][-1]), S[ok], cb[ok][:, j]) for j in range(3)], 1)
        rel = X - mid
        rel -= dax * np.einsum("ij,ij->i", rel, dax)[:, None]
        D[idx] = (kk - 1)[:, None] * rel * lab["arm"][idx, None]
        info[side] = {"ratio_min": round(float(ratio.min()), 4), "ratio_max": round(float(ratio.max()), 4)}
    return D, info


def residual(md, tgt, sliders, stance, lambdas=LAMBDAS, arm_passes=4, log=print):
    lab = md.lab
    Vc = md.body(sliders, stance)
    mt = wrap.Matcher(tgt)
    import surfdist
    mt.S_all = surfdist.Surface(tgt.P, tgt.T)
    wt = lab["tight"] * lab["hold"]
    side = np.where(md.V0[:, 0] >= 0, "l", "r")
    band = (lab["foot"] > 0.3) & (lab["foot"] < 0.7)
    fw = lab["foot"] * lab["hold"]
    Ut = np.zeros((md.n, 3))
    Darm = np.zeros((md.n, 3))
    tf = {"l": np.zeros(3), "r": np.zeros(3)}

    def R_of(Ut, Darm, tf):
        R = Ut * wt[:, None] + Darm
        for sd in "lr":
            m = side == sd
            R[m] += tf[sd][None] * fw[m, None]
        R = symmetrize(R, md.pr, md.symw)
        R[md.ring] = 0.0
        return R

    crotch = crotch_weight(Vc, md.ends(Vc))
    hist = []
    for it, lam in enumerate(lambdas):
        t0 = time.time()
        V = Vc + R_of(Ut, Darm, tf)
        Ut, st = icp_round(md, mt, V, Ut, lam, crotch)
        Ut = symmetrize(Ut, md.pr, md.symw)
        for sd in "lr":
            m = band & (side == sd)
            tf[sd] = (Ut[m] * wt[m, None]).sum(0) / max(wt[m].sum(), 1e-9)
        V = Vc + R_of(Ut, Darm, tf)
        for sd in "lr":
            m = V[:, 0] * (1 if sd == "l" else -1) > 0.02
            tf[sd][1] += tgt.ground - V[m, 1].min()
        hist.append(dict(lam=lam, **st))
        log(f"icp {it} lam {lam}: {st} ({time.time() - t0:.1f} s)")
    for ap in range(arm_passes):
        V = Vc + R_of(Ut, Darm, tf)
        dA, info = arm_field(md, V, md.ends(V), tgt)
        Darm = Darm + dA
        log(f"arm pass {ap}: {info}")
    R = R_of(Ut, Darm, tf)
    R = relax(md, Vc, R)
    X, seam = restrip(md, mt.S_all, Vc, Vc + R)
    R = X - Vc
    R[md.ring] = 0.0
    return R, {"seam": seam, "icp": hist, "feet_move_m": {k: [round(float(x), 5) for x in v] for k, v in tf.items()}}


RELAX_ITERS, RELAX_STEP = 30, 0.5


def relax(md, Vc, R, iters=RELAX_ITERS, alpha=RELAX_STEP):
    """Our loops after the fit: the TIGHT points slid along the fitted skin (projected back onto it each step) toward
    the slider stage's own spacing (its graph-Laplacian coordinates' tangential part), so her shape stays and our
    rows and columns keep their designed spacing (the ICP pinches them where she is narrower: her cleavage, her
    throat). Weighted by tight * hold; the ring fixed; the move mirror-averaged."""
    import surfdist
    Vf = Vc + R
    S = surfdist.Surface(Vf, md.T)
    w = md.lab["tight"] * md.lab["hold"]
    free = w > 0.5
    free[md.ring] = False
    deg = md.L.diagonal()[:, None]
    Lb = md.L @ Vc
    V = Vf.copy()
    for _ in range(iters):
        N = md.normals(V)
        dl = (md.L @ V - Lb) / deg
        m = -alpha * (dl - (dl * N).sum(1)[:, None] * N)
        V[free] += m[free] * w[free, None]
        V[free] = S.closest(V[free])[0]
        V = Vf + symmetrize(V - Vf, md.pr, md.symw)
        V[md.ring] = Vf[md.ring]
    return V - Vc


SEAM_M = 0.015


def restrip(md, S, Vc, V, seam_m=SEAM_M):
    """The seam rows: between the head's ring and the first neck row at least `seam_m` under SPLIT (the anchor),
    each column's residual laid again: R lerped from the ring's (0) to the anchor's at the slider stage's own
    arc-length fractions down the column, then the points onto her skin (S). P1 N: the topology now meets the baked
    ring by construction (topo.neck_carry), so the slider stage's seam rows are clean (folds 0, aspect max 3.6);
    pulled point by point by the ICP her top rows still cross (fit with no seam rule: 6 neck folds over 60 deg), and
    C's old rule (the points re-laid along the chord ring -> anchor, then projected) now folds 14 (179 deg: the chord
    cuts under her neck's curve and the projection lands rows out of order). Lerping R keeps the rows' order from
    the slider stage: 0 neck folds (her close fit on spec3, folds over the body: C's rule 27, none 19, this 13)."""
    z = md.z
    m = z["part"] == pidx(z, "neck")
    rows = z["ring"]
    rr = sorted(set(rows[m].tolist()))
    top = rr[-1]
    anchor = max(r for r in rr if md.dep[m & (rows == r)].mean() >= seam_m)
    key = z["side"] * 1000 + z["col"]
    cols = np.unique(key[m & (rows == top)])
    band = list(range(top, anchor - 1, -1))
    C = np.full((len(band), len(cols)), -1)
    for i, r in enumerate(band):
        sel = np.where(m & (rows == r))[0]
        C[i, np.searchsorted(cols, key[sel])] = sel
    assert (C >= 0).all(), "the neck's seam rows are not whole columns"
    seg = np.linalg.norm(np.diff(Vc[C], axis=0), axis=2)
    t = np.concatenate([np.zeros((1, len(cols))), np.cumsum(seg, 0)]) / seg.sum(0)
    R = V - Vc
    X = V.copy()
    for i in range(1, len(band) - 1):
        X[C[i]] = Vc[C[i]] + t[i][:, None] * R[C[-1]]       # the ring's R is 0 (the head's, kept): never the ICP's
    inner = C[1:-1].ravel()
    X[inner] = S.closest(X[inner])[0]
    return X, {"rows": [int(band[1]), int(band[-2])], "anchor_row": int(anchor), "points": int(len(inner))}


# ---------------------------------------------------------------------------------------- topology quality --
def quality(V, Q, z=None):
    """Our loops' health on a body, by the topology's own gate (topo_gates.mesh_quality, the hand and foot templates
    apart): fold edges over 60 deg (and the worst), quads with aspect over 4, edges under 2 mm."""
    import topo_gates as G
    z = z if z is not None else bt.load_tier("close" if len(V) > 20000 else "play")[0]
    parts = list(map(str, z["parts"]))
    q = G.mesh_quality(V, Q, np.isin(z["qpart"], [parts.index("hand"), parts.index("foot")]))
    return {"fold_over_60": q["fold_edges_over_60"], "fold_max_deg": q["fold_deg_p99_max_body"][1],
            "aspect_over_4": q["aspect_over_4"], "edges_under_2mm": q["edges_under_2mm"],
            "edge_min_mm": q["edge_min_mm_body"]}


def write_forms(path, z, R, tier, about):
    np.savez_compressed(path, R=R.astype(np.float32), tier=np.array(tier), topology=np.array(bt.topo_sha(z)),
                        about=np.array(about))


def carry(close_npz, play_npz, spec_path=None, tnpz=None):
    """topo-carry: close's R onto play's vertices through close's reference surface (barycentric); with the spec and
    the target, play's own seam rows laid again on her skin (restrip)."""
    import surfdist
    rc = np.load(close_npz)
    zc, _ = bt.load_tier("close")
    zp, _ = bt.load_tier("play")
    assert str(rc["topology"]) == bt.topo_sha(zc)
    Vc, Vp = zc["V"].astype(np.float64), zp["V"].astype(np.float64)
    Tc = np.concatenate([zc["Q"][:, [0, 1, 2]], zc["Q"][:, [0, 2, 3]]])
    S = surfdist.Surface(Vc, Tc)
    q, _, ti, d = S.closest(Vp)
    tri = Tc[ti]
    a, b, c = Vc[tri[:, 0]], Vc[tri[:, 1]], Vc[tri[:, 2]]
    v0, v1, v2 = b - a, c - a, q - a
    d00, d01, d11 = (v0 * v0).sum(1), (v0 * v1).sum(1), (v1 * v1).sum(1)
    d20, d21 = (v2 * v0).sum(1), (v2 * v1).sum(1)
    den = d00 * d11 - d01 * d01
    bv = (d11 * d20 - d01 * d21) / den
    bw = (d00 * d21 - d01 * d20) / den
    bu = 1 - bv - bw
    R = rc["R"].astype(np.float64)
    Rp = bu[:, None] * R[tri[:, 0]] + bv[:, None] * R[tri[:, 1]] + bw[:, None] * R[tri[:, 2]]
    Rp = symmetrize(Rp, mirror_pairs(zp), s01((bt.split_depth(Vp) - SYM_FREE_M) / (SYM_FULL_M - SYM_FREE_M)))
    info = {}
    if spec_path:
        import surfdist
        from sliders import load_spec
        mp = Model(load_spec(spec_path), "play")
        tg = wrap.Target(tnpz)
        Vc = mp.body(load_spec(spec_path)["sliders"], load_spec(spec_path)["stance"])
        X, info = restrip(mp, surfdist.Surface(tg.P, tg.T), Vc, Vc + Rp)
        Rp = X - Vc
    Rp[bt.boundary_ring(zp["Q"], len(Vp))] = 0.0
    write_forms(play_npz, zp, Rp, "play", "tools/body/wrap.py topo-carry: her residual R per our play vertex (glTF m), "
                "close's carried through close's reference surface; build_topo.py stage 2b adds it after the ring snap")
    return {"seam": info, "play_to_close_ref_mm": [round(float(np.percentile(d, 50)) * 1e3, 2), round(float(np.percentile(d, 95)) * 1e3, 2),
                                     round(float(d.max()) * 1e3, 2)]}


def chain(spec_start, spec_out, forms_out, work):
    """topo-chain: every step above in order, each run as its own command (the log says which), intermediates in
    `work` (git-ignored): the slider stage built from the start values, A posed into it, the sliders; once more from
    the fitted sliders' stage (that target is THE target: work/target.npz, formcheck's --target); the residual; the
    sliders again with that residual held (the arm's segments as the final skeleton reads them); the residual again;
    the play tier carried. spec_out = base + sliders + stance + "forms_topo" (forms_out, a pattern with {tier})."""
    import subprocess
    os.makedirs(work, exist_ok=True)
    py = [sys.executable]
    W = lambda *x: py + [os.path.join(HERE, "wrap.py"), *x]       # noqa: E731
    B = lambda *x: py + [os.path.join(HERE, "build_topo.py"), *x]  # noqa: E731
    j = lambda n: os.path.join(work, n)                            # noqa: E731
    start = json.load(open(spec_start))
    s0 = {"base": "tools/body/specs/base_woman.json", "sliders": start.get("sliders", {}), "stance": start.get("stance", {})}
    json.dump(s0, open(j("spec0.json"), "w"), indent=1)
    fc = forms_out.format(tier="close")
    steps = [B(j("spec0.json"), j("s0"), "--tiers", "close"), W("topo-target", j("s0/body.glb"), j("target0.npz")),
             W("topo-sliders", j("spec0.json"), j("target0.npz"), j("spec1.json")),
             B(j("spec1.json"), j("s1"), "--tiers", "close"), W("topo-target", j("s1/body.glb"), j("target.npz")),
             W("topo-sliders", j("spec1.json"), j("target.npz"), j("spec2.json")),
             W("topo-residual", j("spec2.json"), j("target.npz"), j("forms2_close.npz")),
             W("topo-carry", j("forms2_close.npz"), j("forms2_play.npz"), j("spec2.json"), j("target.npz")),
             W("topo-sliders", j("spec2.json"), j("target.npz"), j("spec3.json"), j("forms2_{tier}.npz")),
             W("topo-residual", j("spec3.json"), j("target.npz"), fc),
             W("topo-carry", fc, forms_out.format(tier="play"), j("spec3.json"), j("target.npz"))]
    for c in steps:
        print("STEP", " ".join(os.path.relpath(x, REPO) if os.path.isabs(x) and x.startswith(REPO) else x for x in c[1:]), flush=True)
        r = subprocess.run(c, cwd=REPO, capture_output=True, text=True)
        assert r.returncode == 0, r.stderr[-3000:]
        print("   ", r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "", flush=True)
    s3 = json.load(open(j("spec3.json")))
    out = {"about": "Her body on OUR topology (P1 C): base_woman + her slider values + stance + her residual per our vertex, "
                    "solved against A (godot/art/people/heroine.glb) posed into the slider stage's rest (her_target.py, "
                    "her head's world rest). Made by: python tools/body/wrap.py topo-chain " + " ".join(
                        os.path.relpath(os.path.abspath(x), REPO).replace("\\", "/") for x in (spec_start, spec_out)) +
                    f" {forms_out} {os.path.relpath(os.path.abspath(work), REPO)}".replace("\\", "/") +
                    ". Rebuild: python tools/body/build_topo.py " + os.path.relpath(os.path.abspath(spec_out), REPO).replace("\\", "/") + " <out>.",
           "base": "tools/body/specs/base_woman.json", "sliders": s3["sliders"], "stance": s3["stance"],
           "forms_topo": forms_out}
    json.dump(out, open(spec_out, "w"), indent=1)


def main(a):
    from sliders import load_spec
    if a[0] == "topo-sliders":
        spec_in, tnpz, spec_out = a[1:4]
        R = Rp = None
        if len(a) > 4:      # <forms pattern with {tier}>
            R = np.load(a[4].format(tier="close"))["R"].astype(np.float64)
            Rp = np.load(a[4].format(tier="play"))["R"].astype(np.float64)
        spec = load_spec(spec_in)
        md = Model(spec)
        names = [n for n in md.pre[1].names if n not in ("male", "heavy", "arm_length")]   # (v1's set: arm_length = the two segments')
        st0 = spec.get("stance", {})
        x0 = [spec.get("sliders", {}).get(n, 0.0) for n in names] + \
             [np.radians(st0.get("pitch_deg", 0.0))] + list(st0.get("move_m", [0, 0, 0]))[1:]
        x, stn = fit_sliders(md, wrap.Target(tnpz), names, x0, R=R, mp=Model(spec, "play"), Rp=Rp)
        out = json.load(open(spec_in))
        out.update(sliders=x, stance=stn)
        json.dump(out, open(spec_out, "w"), indent=1)
    elif a[0] == "topo-residual":
        spec_path, tnpz, out = a[1:4]
        spec = load_spec(spec_path)
        md = Model(spec)
        tgt = wrap.Target(tnpz)
        Vb = md.body(spec["sliders"], spec["stance"])
        R, info = residual(md, tgt, spec["sliders"], spec["stance"])
        write_forms(out, md.z, R, "close", "tools/body/wrap.py topo-residual: her residual R per our close vertex (glTF m); "
                    "build_topo.py stage 2b adds it after the ring snap")
        print(json.dumps({"feet_move_m": info["feet_move_m"], "icp_last": info["icp"][-1],
                          "seam": info["seam"], "quality_before": quality(Vb, md.Q, md.z), "quality_after": quality(Vb + R, md.Q, md.z)}))
    elif a[0] == "topo-chain":
        chain(*a[1:5])
    elif a[0] == "topo-carry":
        print(json.dumps(carry(*a[1:5])))
    elif a[0] == "topo-target":
        print(wrap.make_target(a[1], a[2], world=True))


if __name__ == "__main__":
    main(sys.argv[1:])
