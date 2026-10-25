"""Her raised-arm shoulder join SCULPTED at the key poses, replacing the skinned surface there (Body 9, 24 Oct 2026).

Five rounds of small correctives on the skinned join (bumps, hollows, folds, the 8-weight helper rig, the reweight) left
every judge saying the raised arm looks PLUGGED IN: the deltoid a ball on the torso's corner with a notch under it,
the pec not tenting into the arm, the arm's underside one sausage into a pinched pit crease. The fault is big form, so
this pass doesn't nudge the skinned surface: at each key pose Godot dumped (tools/assets/shoulder_sculpt_poses.json)
her body is skinned with all 8 weights (NO shoulder shapes) and the arm-chest-shoulder region is RE-SOLVED as a new
surface in her chest's frame, then carried back to the bind shape through the inverse of each point's blended skin
matrix (pit_hollow_post's machinery), so at the key it lands exactly and between keys it rides with the skin.

The construction (per side, at each key; m in her rest unless said):
  region  within 0.10-0.135 of the shoulder joint (eased), the breast's core, the sternum side (x < 0.07-0.11) and
          the neck kept; plus (round 2) the BREAST PANEL: her front chest on that side from the sternum (and the other
          breast's inner edge) out to x 0.19-0.23, y 1.18-1.53; those and everything outside are the boundary, three
          rings of it held (tangent continuity)
  solve   least squares on the uniform Laplacian: each point's Laplacian made her REST one turned into the pose
          (min |L X - R dU|^2), so the skin keeps its own curvature and spacing but not the skinning's ball, notch,
          slot and crumples; the turn R is the skin's own (polar of the blended matrix) blended toward the humerus'
          turn on the cap and arm (arm-ness 0 at 0.08 medial of the joint plane, 1 at 0.04 down the arm), so the
          deltoid's mass moves with the arm instead of sitting on the torso's corner; on the breast none (her rest)
  flat    in the pit and the front crease (the under side about the humerus, and its front-under side out from
          0.035 medial of the joint plane, inside 0.115 of the joint) her rest curvature is dropped (the A-pose's
          closed pit valley isn't carried up): a thin-plate fill there; at the pit's core the spacing too
  lift    (round 2) the breast rises with the arm: its core (smoothed breast weight > 0.45) is her REST breast moved
          LIFT x (A - 70) / 80 up (along the chest wall: a quarter back, a fifth out toward the arm; 27 mm at A 150,
          ~13 at A 114), its upper pole drawn in FLAT (the pole flattens as the pec pulls it), held hard; the panel
          solved round it, so the breast keeps its round rest shape (never a disc) and the skin above and below it
          (and HerRaise's crumpled upper pole at A 150) is her rest skin stretched, never crumpled
  pull    the breast's upper-outer edge drawn along her skin toward the front fold's arm end (PULL), so the fold
          runs into the breast
  folds   anchors on the filled surface: the back fold (BACK, from the lat's edge to the arm's back-inner side), the
          pit pushed in as one elliptic dome along its own axis (DOME, 50 x 38 mm, long along the arm), the deltoid's
          front and middle heads one teardrop on the arm's top-outer side (DELT, peak ~0.04 down the humerus), the
          old soft front ridge (RIDGE, off by default since round 2: the lip replaces it); re-solved once
  relax   the pit's core relaxed (RELAX, 15 Laplacian passes): the fold's leftover nick under the arm's root
  detail  (round 2) offsets along the normal, eased: the PEC'S LOWER BORDER one rounded lip from the breast's
          upper-outer edge into the arm's front (LIP mm proud on the spine, falling 22 mm wide over the chest and
          9 mm into the pit: a ~15-20 mm edge radius), the BICEPS/TRICEPS GROOVE up the arm's inner face into the
          pit (GROOVE deep, 9 mm wide, 0.04-0.21 down the humerus), the DELTOID'S INSERTION a soft V on the arm's
          outer side closing ~45% down the humerus (INS proud inside the V)
  scale   the anatomy (folds, dome, delt, pull, details) eased in with A: 0 at A 60, whole from A 114
Keys and slots: the reaver_show key (right A 113.5, az 23) and the cast key (l A 117 az 70, r A 114 az 61) give the
A 117 slots: per point the abd117 and flex117 shapes solved so Play/ShoulderPsd's weights at each key give back that
key's sculpt exactly (the left's show key is the right's mirrored); the old overhead cast (l A 148, r A 155) gives
the 140 and 175 slots and their shrug twins (shared accessors); (round 2) the lowered swing (right A 75 az 40) gives
the LEVEL slot shoulder_lvl80 (ShoulderPsd: eased in from A 60, whole at 80, handed to the 117 slots by 117; its
share subtracted at the other keys first; whole at 80, not 90, so the key (0.85 there) isn't doubled at A 85-95,
where a level slot whole at 90 buckled the fold). So nothing up to A 60 (the Look and the idles move 0.00 mm).
pit_hollow_post's shapes in those slots are REPLACED (they were authored on the pre-reweight weights and are the old
nudges): run on its output, this pass takes them off first. The hero and NPCs carry no such shapes: untouched.

    SHOULDER_SCULPT=1 python tools/assets/shoulder_sculpt_post.py <src.glb> <dst.glb>
Run after shoulder_reweight_post.py (weights read and kept). Without SHOULDER_SCULPT=1 it copies unchanged.
"""
import json
import os
import shutil
import struct
import sys

import numpy as np
import scipy.sparse as sps
from scipy.sparse.csgraph import dijkstra
from scipy.sparse.linalg import splu
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "anim"))
from heroine_neck import _Gl  # noqa: E402
from worn_reaver_post import _sparse  # noqa: E402
import pit_hollow_post as ph  # noqa: E402
import shoulder_psd_post as sp  # noqa: E402

POSES = os.path.join(HERE, "shoulder_sculpt_poses.json")
_E = os.environ.get
P = dict(ridge=float(_E("SCULPT_RIDGE", 0.0)), back=float(_E("SCULPT_BACK", 0.003)), dome=float(_E("SCULPT_DOME", 0.011)),
         dRu=0.05, dRv=0.038, pull=float(_E("SCULPT_PULL", 0.008)), delt=float(_E("SCULPT_DELT", 0.005)),
         cr=0.2, cd=0.02, cl=0.05, aw=(0.08, 0.12), sf=(0.15, 0.035),
         relax=float(_E("SCULPT_RELAX", 1.0)), relaxIt=int(_E("SCULPT_RELAX_IT", 15)),
         lift=float(_E("SCULPT_LIFT", 0.027)), liftA=(70.0, 150.0), lback=0.25, llat=0.2,
         flat=float(_E("SCULPT_FLAT", 0.003)), cb=30.0,
         lip=float(_E("SCULPT_LIP", 0.007)), lipF=0.022, lipP=0.009,
         groove=float(_E("SCULPT_GROOVE", 0.002)), grooveW=0.009, ins=float(_E("SCULPT_INS", 0.002)), insT=0.45,
         fair=float(_E("SCULPT_FAIR", 1.0)), fairIt=int(_E("SCULPT_FAIR_IT", 12)), kA=(60.0, 114.0))
SLOTS117 = ("shoulder_abd117", "shoulder_flex117")
SLOTS150 = ("shoulder_abd140", "shoulder_flex140", "shoulder_up175", "shoulder_abd140s", "shoulder_flex140s", "shoulder_up175s")
LVL = "shoulder_lvl80"
KEYS = (("show", "r"), ("cast", "l"), ("cast", "r"), ("cast150", "l"), ("cast150", "r"), ("low", "r"))


def _ss(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def _ramp(x, a, c):
    return float(np.clip((x - a) / (c - a), 0, 1))


def _unit(v):
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def _polar(Bm):
    U_, _, Vt = np.linalg.svd(Bm)
    R = U_ @ Vt
    neg = np.linalg.det(R) < 0
    if neg.any():
        U_[neg, :, 2] *= -1
        R[neg] = U_[neg] @ Vt[neg]
    return R


class Her:
    """the welded body (pit_hollow_post.Body), its uniform Laplacian, rest Laplacian coordinates, edge graph"""

    def __init__(s, G):
        b = s.b = ph.Body(G)
        n = len(b.U)
        s.L = (sps.diags(1.0 / b.deg) @ b.A - sps.identity(n)).tocsr()
        s.dU = s.L @ b.U
        s.M0 = np.linalg.inv(b.ibm)
        s.NU = ph.vn(b.U, b.F)
        E = np.unique(np.sort(np.r_[b.F[:, [0, 1]], b.F[:, [1, 2]], b.F[:, [2, 0]]], axis=1), axis=0)
        el = np.linalg.norm(b.U[E[:, 0]] - b.U[E[:, 1]], axis=1)
        s.GR = sps.coo_matrix((np.r_[el, el], (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(n, n)).tocsr()

    def rings(s, m, k):
        out = m.copy()
        for _ in range(k):
            out = out | (s.b.A @ out.astype(float) > 0)
        return out

    def smooth(s, f, k):
        for _ in range(k):
            f = 0.5 * f + 0.5 * (s.b.A @ f) / (s.b.deg if f.ndim == 1 else s.b.deg[:, None])
        return f

    def path(s, a, c):
        _, pred = dijkstra(s.GR, indices=a, return_predecessors=True)
        p = [c]
        while p[-1] != a:
            p.append(pred[p[-1]])
        return np.array(p[::-1])


class Side:
    """one side's rest fields: the region, the flat sector, arm-ness, the fold anchors and spines, the pit's apex,
    the breast panel and core, the arm's rest frame"""

    def __init__(s, H, side, p=P):
        b, U = H.b, H.b.U
        sg = 1 if side == "l" else -1
        J0 = H.M0[b.I["upperarm_" + side]][:3, 3]
        h0 = _unit(H.M0[b.I["lowerarm_" + side]][:3, 3] - J0)
        v = U - J0
        t0 = v @ h0
        rj = np.linalg.norm(v, axis=1)
        s.aw = b.arm_w(side)
        s.bw = b.Wd[:, b.I["breast_" + side]]
        x = U[:, 0] * sg
        up = _unit(np.array([0, 1.0, 0]) - h0[1] * h0)
        fr = _unit(np.array([0, 0, 1.0]) - h0[2] * h0 - (np.array([0, 0, 1.0]) @ up) * up)
        c = np.cross(h0, fr)
        med = c if c[0] * sg < 0 else -c
        rr = v - t0[:, None] * h0
        rn = np.maximum(np.linalg.norm(rr, axis=1), 1e-9)
        cosu, cosf = (rr @ up) / rn, (rr @ fr) / rn
        phi = _ss((0.135 - rj) / 0.035) * (1 - _ss((s.bw - 0.35) / 0.3)) * _ss((x - 0.07) / 0.04)
        phi *= 1 - _ss((U[:, 1] - 1.53) / 0.03) * _ss((0.13 - x) / 0.04)
        s.phi = phi * (x > 0.02)
        sect = np.maximum(_ss((-0.1 - cosu) / 0.5),
                          _ss((p["sf"][0] - cosu) / 0.35) * _ss((cosf - 0.15) / 0.4) * _ss((t0 + p["sf"][1]) / 0.03))
        s.kap = 1 - sect * _ss((0.115 - rj) / 0.035) * (1 - _ss((t0 - 0.06) / 0.05))
        s.arm = _ss((t0 + p["aw"][0]) / p["aw"][1])
        s.core = _ss((-0.3 - cosu) / 0.4) * _ss((0.09 - rj) / 0.03)

        def arm_pt(t, d):
            i = np.nonzero((s.aw > 0.8) & (np.abs(t0 - t) < 0.006))[0]
            return int(i[np.argmax(H.NU[i] @ d)])
        s.a_fa = arm_pt(0.095, _unit(0.75 * fr + 0.66 * med))
        s.a_ba = arm_pt(0.090, _unit(-0.75 * fr + 0.66 * med))
        Bm = s.bw > 0.3
        Bc = (U[Bm] * s.bw[Bm, None]).sum(0) / s.bw[Bm].sum()
        # (round 2: the fold's chest end where the breast's upper-outer edge meets her chest wall, ~45 mm over the
        # nipple; round 1's was on the breast's upper pole, so its fold crossed the breast)
        i = np.nonzero((s.bw > 0.06) & (s.bw < 0.2) & (U[:, 2] > 0.05) & (U[:, 1] > 1.36))[0]
        s.a_fc = int(i[np.argmax(U[i] @ np.array([0.9 * sg, 0.44, 0.0]))])
        d = np.linalg.norm(U - np.array([0.125 * sg, 1.31, -0.085]), axis=1)
        s.a_bc = int(np.argmin(np.where(s.aw < 0.2, d, 9)))
        s.faf, s.baf = H.path(s.a_fc, s.a_fa), H.path(s.a_bc, s.a_ba)
        s.apex = ph.apex(b, U, side)
        # the breast panel (her front chest this side; the sternum and the other breast's inner edge free too, its
        # core held), the breast's core and its nipple
        bo = b.Wd[:, b.I["breast_" + ("r" if side == "l" else "l")]]
        y, z = U[:, 1], U[:, 2]
        s.phib = (_ss((x + 0.03) / 0.04) * (1 - _ss((bo - 0.15) / 0.2)) * _ss((y - 1.18) / 0.06)
                  * (1 - _ss((y - 1.50) / 0.03)) * _ss(z / 0.04) * (1 - _ss((x - 0.19) / 0.04)))
        # and her side under the pit (the lat's front edge, the serratus: the skinning's streaks there)
        side_ = (_ss((x - 0.11) / 0.03) * (1 - _ss((x - 0.24) / 0.03)) * _ss((y - 1.20) / 0.05)
                 * (1 - _ss((y - 1.42) / 0.04)) * _ss((z + 0.10) / 0.03) * (s.aw < 0.3))
        s.phib = np.maximum(s.phib, side_)
        s.bsm = H.smooth(s.bw, 6)
        s.kb = _ss((s.bsm - 0.2) / 0.3)
        s.bcore = np.nonzero(s.bsm > 0.45)[0]
        s.bcw = _ss((s.bsm[s.bcore] - 0.45) / 0.15)
        i = np.nonzero(s.bw > 0.5)[0]
        s.nip = int(i[np.argmax(U[i, 2])])
        # the arm's rest frame square to the humerus: out (the deltoid's side) and front
        lat0 = np.array([sg * 1.0, 0, 0])
        s.lat0 = _unit(lat0 - (lat0 @ h0) * h0)
        f0 = np.array([0, 0, 1.0])
        s.fr0 = _unit(f0 - (f0 @ h0) * h0 - (f0 @ s.lat0) * s.lat0)


def _solve(H, Pin, phi, delta, anchors=None, c_core=1e-7, c_fix=1e2):
    """min sum |(L X)_i - delta_i|^2 + c_i |X_i - Pin_i|^2 (+ anchors' |X_i - target_i|^2 w) over phi's points and
    three rings beyond; c from phi (held where phi is 0)"""
    act = H.rings(phi > 1e-4, 3)
    ia, io = np.nonzero(act)[0], np.nonzero(~act)[0]
    ir = np.nonzero(H.rings(act, 1))[0]
    Lr = H.L[ir]
    LA, LO = Lr[:, ia], Lr[:, io]
    c = c_core + c_fix * (1 - phi[ia]) ** 2
    cw, tgt = np.zeros(len(Pin)), Pin.copy()
    for idx, T, w in anchors or []:
        cw[idx] += w
        tgt[idx] = T
    lu = splu((LA.T @ LA + sps.diags(c + cw[ia])).tocsc())
    rhs = LA.T @ (delta[ir] - LO @ Pin[io]) + c[:, None] * Pin[ia] + cw[ia, None] * tgt[ia]
    X = Pin.copy()
    X[ia] = np.stack([lu.solve(rhs[:, k]) for k in range(3)], 1)
    return X


def _angles(H, d, side):
    """bone globals [J, 4, 4] from a dump entry and the side's (A, azimuth)"""
    b = H.b
    Mg = np.stack([np.eye(4)] * len(b.names))
    for i, n in enumerate(b.names):
        v = d[n]
        Mg[i, :3, 0], Mg[i, :3, 1], Mg[i, :3, 2], Mg[i, :3, 3] = v[0:3], v[3:6], v[6:9], v[9:12]
    A, az = sp.arm_angles(Mg, b.I, side)
    return Mg, A, az


def _folds(H, X, live):
    """faces more than ~78 degrees off the surface smoothed (15 passes): folded over or about to"""
    F = H.b.F
    Xs = H.smooth(X, 15)
    q = np.cross(X[F[:, 1]] - X[F[:, 0]], X[F[:, 2]] - X[F[:, 0]])
    q /= np.maximum(np.linalg.norm(q, axis=1, keepdims=True), 1e-15)
    return np.nonzero(((q * ph.vn(Xs, F)[F].mean(1)).sum(1) < 0.2) & live[F].all(1))[0]


def _untangle(H, X, live, rounds=8, its=6):
    b = H.b
    n0 = None
    for _ in range(rounds):
        fl = _folds(H, X, live)
        n0 = len(fl) if n0 is None else n0
        if not len(fl):
            break
        m = np.zeros(len(X), bool)
        m[b.F[fl].ravel()] = True
        m = H.rings(m, 2) & live
        for _ in range(its):
            X = X + 0.5 * m[:, None] * b.lap(X)
            X = X - 0.53 * m[:, None] * b.lap(X)
    return X, (n0, len(_folds(H, X, live)))


def author(H, S, d, side, p=P, info=None, **_):
    """(D the posed move in her chest frame, B blended chest-frame matrices) for one side at one key"""
    b = H.b
    F, U = b.F, b.U
    M, T, X0, B = b.pose(d)
    _, A, _ = _angles(H, d, side)
    kA, kL = _ramp(A, *p["kA"]), _ramp(A, *p["liftA"])
    sg = 1 if side == "l" else -1
    J = (T @ M["upperarm_" + side])[:3, 3]
    Eb = (T @ M["lowerarm_" + side])[:3, 3]
    h = _unit(Eb - J)
    Lh = np.linalg.norm(Eb - J)
    Sa = T @ M["upperarm_" + side] @ b.ibm[b.I["upperarm_" + side]]
    Ra = _polar(Sa[None, :3, :3])[0]
    ra = _polar((1 - S.arm)[:, None, None] * np.eye(3)[None] + S.arm[:, None, None] * Ra[None])
    w = S.phi[:, None, None]
    R = _polar((1 - w) * _polar(B[:, :3, :3]) + w * ra)
    kb = S.kb[:, None, None]
    R = _polar((1 - kb) * R + kb * np.eye(3)[None])
    dR = np.einsum("nab,nb->na", R, H.dU)
    phi = np.maximum(S.phi, S.phib)
    out = phi < 1e-4
    # the breast lifted: its core her rest breast moved up the chest wall (a little out toward the arm), the upper
    # pole drawn in; held hard
    ldir = _unit(np.array([sg * p["llat"], 1.0, -p["lback"]]))
    tc = (U[S.bcore] + p["lift"] * kL * ldir
          - (p["flat"] * kL * _ss((U[S.bcore, 1] - U[S.nip, 1]) / 0.05))[:, None] * H.NU[S.bcore])
    abr = [(S.bcore, tc, p["cb"] * S.bcw)]

    def fill(Pin, anchors, its=2):
        X = Pin.copy()
        for _ in range(its):
            N = ph.vn(X, F)
            dn = (dR * N).sum(1, keepdims=True) * N
            delta = (dR - (1 - S.kap[:, None]) * dn) * (1 - S.core[:, None])
            delta[out] = (H.L @ Pin)[out]
            X = _solve(H, Pin, phi, delta, anchors)
        return X
    Xf = fill(X0, abr)
    Nf = ph.vn(Xf, F)
    anc = list(abr)
    # the breast's upper-outer edge drawn along her skin toward the front fold's arm end
    m = S.bw > 0.3
    Bc = (Xf[m] * S.bw[m, None]).sum(0) / S.bw[m].sum()
    du = _unit(Xf[S.a_fa] - Bc)
    rb = np.linalg.norm(Xf - Bc, axis=1)
    k = H.smooth(H.smooth(S.bw, 20) * _ss(((Xf - Bc) @ du) / 0.08) * _ss((rb - 0.03) / 0.04), 10)
    k = k / max(k.max(), 1e-9)
    ip = np.nonzero((k > 0.02) & (phi > 0.5))[0]
    ip = ip[~np.isin(ip, S.bcore)]
    if p["pull"] > 0:
        anc.append((ip, Xf[ip] + (p["pull"] * kA * k[ip])[:, None] * (du[None, :] - (Nf[ip] @ du)[:, None] * Nf[ip]), p["cr"]))
    for pth, amp in ((S.faf, p["ridge"]), (S.baf, p["back"])):
        if amp > 0:
            sl = np.linspace(0, 1, len(pth))
            a = kA * amp * np.sin(np.pi * np.clip(sl * 1.15 - 0.05, 0, 1)) ** 0.7
            anc.append((pth, Xf[pth] + a[:, None] * Nf[pth], p["cr"]))
    C = Xf[S.apex]
    ax = _unit(Nf[np.linalg.norm(Xf - C, axis=1) < 0.02].mean(0))
    hu = _unit(h - (h @ ax) * ax)
    q = Xf - C
    rho = np.sqrt(((q @ hu) / p["dRu"]) ** 2 + ((q - (q @ hu)[:, None] * hu - (q @ ax)[:, None] * ax) ** 2).sum(1) / p["dRv"] ** 2)
    core = np.nonzero((rho < 1.0) & (S.phi > 0.5))[0]
    anc.append((core, Xf[core] - (kA * p["dome"] * (1 - rho[core] ** 2) ** 2)[:, None] * ax, p["cd"]))
    up = _unit(np.array([0, 1.0, 0]) - h[1] * h)
    c = np.cross(up, h)
    dt = _unit(np.cos(np.radians(25)) * up + np.sin(np.radians(25)) * (c if c[2] > 0 else -c))
    v = Xf - J
    ta = v @ h
    rr = v - ta[:, None] * h
    ca = (rr @ dt) / np.maximum(np.linalg.norm(rr, axis=1), 1e-9)
    wdl = _ss((ta + 0.015) / 0.04) * (1 - _ss((ta - 0.06) / 0.065)) * _ss(ca / 0.6) * (S.aw > 0.3) * (S.phi > 0.05)
    dl = np.nonzero(wdl > 0.02)[0]
    if p["delt"] > 0:
        anc.append((dl, Xf[dl] + (kA * p["delt"] * wdl[dl])[:, None] * Nf[dl], p["cl"]))
    X = fill(Xf, anc, its=1)
    # the pit's core relaxed (plain passes: Taubin left it): the A-pose fold's leftover nick where the arm's underside
    # meets the torso wall eased out
    wr = p["relax"] * H.smooth(np.minimum(S.core * 1.5, 1) * S.phi, 6)
    for _ in range(p["relaxIt"]):
        X = X + 0.5 * wr[:, None] * b.lap(X)
    # faired: each point moved along its normal till its ring's curvature is her rest's (none in the flat sector);
    # the solve's rotated rest Laplacian leaves 1-1.5 mm single-point dips where its turn and the surface's disagree
    # (odd valence points on the chest's front by the fold: a dark nick in Godot)
    Xr = X.copy()
    wf = p["fair"] * H.smooth(phi, 4) * (phi > 1e-4)
    k0 = S.kap * (H.dU * H.NU).sum(1)
    for _ in range(p["fairIt"]):
        N = ph.vn(X, F)
        X = X + (0.5 * wf * ((b.lap(X) * N).sum(1) - k0))[:, None] * N
    Xa = X.copy()
    # detail along the normal: the pec's lower border a rounded lip, the biceps/triceps groove, the deltoid's insertion
    N = ph.vn(X, F)
    off = np.zeros(len(X))
    if p["lip"] > 0:
        # its spine: the fold's edge path (zigzag along edges) smoothed and resampled
        Xs = X[S.faf].copy()
        for _ in range(30):
            Xs[1:-1] = 0.5 * Xs[1:-1] + 0.25 * (Xs[:-2] + Xs[2:])
        cum = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Xs, axis=0), axis=1))]
        ns = 240
        Xs = np.stack([np.interp(np.linspace(0, cum[-1], ns), cum, Xs[:, k]) for k in range(3)], 1)
        tg = _unit(np.gradient(Xs, axis=0))
        bn = _unit(np.cross(tg, N[cKDTree(X).query(Xs)[1]]))
        mid = slice(ns // 3, 2 * ns // 3)
        if ((X[S.apex] - Xs[mid]) * bn[mid]).sum() > 0:
            bn = -bn                                          # + over the chest, - into the pit
        dist, qq = cKDTree(Xs).query(X)
        nr = np.nonzero((dist < 0.06) & (phi > 0.05))[0]
        qq = qq[nr]
        vv = X[nr] - Xs[qq]
        sx, al = (vv * bn[qq]).sum(1), (vv * tg[qq]).sum(1)
        sl = qq / (ns - 1.0)
        env = np.sin(np.pi * np.clip(sl * 1.15 - 0.05, 0, 1)) ** 0.7
        env *= np.where((qq == 0) | (qq == ns - 1), _ss(1 - np.abs(al) / 0.02), 1.0)
        prof = np.where(sx >= 0, np.exp(-(sx / p["lipF"]) ** 2), np.exp(-(sx / p["lipP"]) ** 2))
        off[nr] += p["lip"] * kA * env * prof
    lat, fr = Ra @ S.lat0, Ra @ S.fr0
    v = X - J
    ta = v @ h
    rr = v - ta[:, None] * h
    rn = np.maximum(np.linalg.norm(rr, axis=1), 1e-9)
    ang = np.arctan2(rr @ fr, rr @ lat)                       # 0 out (the deltoid), +90 front, 180 in
    armm = _ss((S.aw - 0.5) / 0.3)
    if p["groove"] > 0:
        arc = np.angle(np.exp(1j * (ang - np.radians(160)))) * rn
        envg = _ss((ta - 0.04) / 0.03) * (1 - _ss((ta - 0.19) / 0.04))
        off -= p["groove"] * kA * envg * np.exp(-(arc / p["grooveW"]) ** 2) * armm
    if p["ins"] > 0:
        ti = p["insT"] * Lh
        hw = np.radians(80) * np.clip((ti - ta) / (ti - 0.03), 0, 1)
        dv = np.abs(np.angle(np.exp(1j * (ang - np.radians(10)))))
        off += p["ins"] * kA * _ss((hw - dv) / np.radians(14)) * _ss((ta - 0.035) / 0.03) * armm
    off = H.smooth(off, 3)
    X = X + off[:, None] * N
    # untangled: where the bend packs the skin past what her rest shape fits (the join's front-top, the fold's chest
    # end) the solve buckles a few triangles over (dark nicks in Godot): those and two rings round them smoothed
    # (Taubin, no shrink) till none is left
    X, nfold = _untangle(H, X, H.rings(phi > 1e-4, 1))
    if info is not None:
        info.update(X0=X0, Xf=Xf, Xr=Xr, Xa=Xa, X=X)
        info["num"] = "A %.1f kA %.2f kL %.2f: nipple rise %.1f mm (skinned %.1f), detail offset %.1f/%.1f mm, folds %d -> %d" % (
            A, kA, kL, 1000 * (X[S.nip, 1] - U[S.nip, 1]), 1000 * (X0[S.nip, 1] - U[S.nip, 1]), 1000 * off.min(), 1000 * off.max(), *nfold)
    return X - X0, B


def _rest(B, D):
    return np.einsum("nab,nb->na", np.linalg.inv(B[:, :3, :3]), D)


def build(G, log=print):
    """{group_side: rest delta} and {group_side: rest normal delta}"""
    H = Her(G)
    b = H.b
    poses = json.load(open(POSES))
    S = {s: Side(H, s) for s in "lr"}
    samp = {}
    for key, side in KEYS:
        D, B = author(H, S[side], poses[key], side)
        _, _, X0, _ = b.pose(poses[key])
        Mg, A, az = _angles(H, poses[key], side)
        wts = sp.psd_weights(A, az, sp.clavicle_rise(Mg, H.M0, b.I, side))
        samp[key + "_" + side] = (_rest(B, D), wts, (ph.vn(X0, b.F), ph.vn(X0 + D, b.F), B[:, :3, :3], np.linalg.norm(D, axis=1) > 1e-6))
        log("SCULPT %s %s: A %.1f az %.1f, posed move max %.1f mm, %d points" % (
            key, side, A, az, 1000 * np.linalg.norm(D, axis=1).max(), int((np.linalg.norm(D, axis=1) > 1e-4).sum())))
    # normals: the posed normal turned as the sculpt turned it, back to rest through the same matrix
    nU = ph.vn(b.U, b.F)
    dN = {}
    for k, (_, _, (N0, N1, L, moved)) in samp.items():
        g0 = _unit(np.einsum("nab,nb->na", L, nU))
        nr = _unit(np.einsum("nab,nb->na", np.linalg.inv(L), ph._rot(N0, N1, g0)))
        dN[k] = np.where(moved[:, None], nr - nU, 0)
    for key in ("show", "low"):
        samp[key + "_l"] = (ph.mirror(b, samp[key + "_r"][0]), samp[key + "_r"][1], None)
        dN[key + "_l"] = ph.mirror(b, dN[key + "_r"])
    rest, nrm = {}, {}
    for side in "lr":
        # the level slot alone at the lowered key; its share taken off the other keys
        Dl, wl, _ = samp["low_" + side]
        rest["lvl80_" + side] = Dl / max(wl[LVL], 1e-6)
        nrm["lvl80_" + side] = dN["low_" + side] / max(wl[LVL], 1e-6)
        log("SCULPT lvl80 %s: key weight %.2f" % (side, wl[LVL]))

        def less(key):
            D, wk, _ = samp[key + "_" + side]
            return D - wk[LVL] * rest["lvl80_" + side], dN[key + "_" + side] - wk[LVL] * nrm["lvl80_" + side], wk
        # the A 117 pair: per point abd/flex so each key's weights give back its sculpt (2 x 2, the same for all points)
        (Ds, nDs, ws), (Dc, nDc, wc) = less("show"), less("cast")
        Wm = np.array([[ws["shoulder_abd117"], ws["shoulder_flex117"]], [wc["shoulder_abd117"], wc["shoulder_flex117"]]])
        Wi = np.linalg.inv(Wm)
        rest["abd117_" + side] = Wi[0, 0] * Ds + Wi[0, 1] * Dc
        rest["flex117_" + side] = Wi[1, 0] * Ds + Wi[1, 1] * Dc
        nrm["abd117_" + side] = Wi[0, 0] * nDs + Wi[0, 1] * nDc
        nrm["flex117_" + side] = Wi[1, 0] * nDs + Wi[1, 1] * nDc
        log("SCULPT 117 %s: key weights abd/flex show %.2f/%.2f cast %.2f/%.2f (level %.2f/%.2f)" % (
            side, *Wm.ravel(), ws[LVL], wc[LVL]))
        D150, nD150, w150 = less("cast150")
        tot = sum(w150[k] for k in SLOTS150)
        rest["150_" + side] = D150 / max(tot, 1e-6)
        nrm["150_" + side] = nD150 / max(tot, 1e-6)
    return b, rest, nrm


def run(src, dst):
    G = _Gl(src)
    g = G.g
    mesh = g["meshes"][[n for n in g["nodes"] if n.get("name") == "Heroine"][0]["mesh"]]
    names0 = list((mesh.get("extras") or {}).get("targetNames", []))
    prims = [p for p in mesh["primitives"] if g["materials"][p["material"]].get("name") != "skin_head"]
    assert len(prims) == len(mesh["primitives"])
    # pit_hollow_post's shapes in these slots off first (the sculpt replaces them; accessors left unreferenced)
    keep = [i for i, n in enumerate(names0) if not n.startswith("shoulder_")]
    if len(keep) < len(names0):
        print("SCULPT: replacing", len(names0) - len(keep), "shoulder shapes")
    for p in prims:
        p["targets"] = [p["targets"][i] for i in keep] if p.get("targets") else []
    w0 = list(mesh.get("weights", [0] * len(names0)))
    names = [names0[i] for i in keep]
    weights = [w0[i] for i in keep]
    b, rest, nrm = build(G)
    binb = bytearray(G.buf[G.b0:G.b0 + g["buffers"][0]["byteLength"]])
    acc = {}
    for key, d in rest.items():
        o = 0
        acc[key] = []
        for p in prims:
            n = g["accessors"][p["attributes"]["POSITION"]]["count"]
            w = b.wid[o:o + n]
            o += n
            Dp, dn = d[w], nrm[key][w]
            Ns = G.get(p["attributes"]["NORMAL"]).astype(float)
            Nn = Ns + dn
            Nn /= np.maximum(np.linalg.norm(Nn, axis=1, keepdims=True), 1e-12)
            dNp = np.where((np.abs(dn).max(1) > 1e-6)[:, None], Nn - Ns, 0)
            ip = np.nonzero(np.abs(Dp).max(1) > 1e-7)[0]
            inn = np.nonzero(np.abs(dNp).max(1) > 1e-6)[0]
            acc[key].append((_sparse(g, binb, n, ip, Dp[ip]), _sparse(g, binb, n, inn, dNp[inn])))
    added = []
    for nm, grp in [(n, n.replace("shoulder_", "")) for n in SLOTS117] + [(n, "150") for n in SLOTS150] + [(LVL, "lvl80")]:
        for side in "lr":
            for pi, p in enumerate(prims):
                pa, na = acc[grp + "_" + side][pi]
                p.setdefault("targets", []).append({"POSITION": pa, "NORMAL": na})
            added.append(nm + "_" + side)
    for p in prims:
        assert len(p["targets"]) == len(names) + len(added)
    mesh.setdefault("extras", {})["targetNames"] = names + added
    mesh["weights"] = weights + [0] * len(added)
    g["asset"].setdefault("extras", {}).pop("pit_hollow", None)
    g["asset"]["extras"]["shoulder_sculpt"] = {"keys": [k + " " + s for k, s in KEYS],
                                               "params": {k: v for k, v in P.items()}}
    while len(binb) % 4:
        binb.append(0)
    g["buffers"][0]["byteLength"] = len(binb)
    js = json.dumps(g, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    body = struct.pack("<I", len(js)) + b"JSON" + js + struct.pack("<I", len(binb)) + b"BIN\x00" + bytes(binb)
    open(dst, "wb").write(b"glTF" + struct.pack("<II", 2, 12 + len(body)) + body)
    print("SCULPT shapes", len(added), "->", dst)


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if os.environ.get("SHOULDER_SCULPT", "0") != "1":
        shutil.copyfile(a[0], a[1])
        print("SCULPT off (SHOULDER_SCULPT=1 builds it): copied")
    else:
        run(a[0], a[1])
