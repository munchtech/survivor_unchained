# Body 2 B step 2: the right arm resculpted (authored fields, never smoothing), its weights fixed, then the right's
# shape and weights mirrored onto the left (the left moves its own vertices along their normals onto the mirrored
# right, keeps its own UVs). Every moved region is relaxed tangentially with its corner UVs re-sampled by exact point
# location on the moved surface (seams and the region border locked).
#   python shape.py <dense.npz> <out.npz>      knobs: env (see K below)
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import numpy as np
import scipy.sparse as sp
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree
from lib import Frame, ss, win, profile, show_profile, vnormals
from remesh import islands, Ref, Work
from geo import Surf

K = dict(SLIM=1.0, DELT=9.0, TRI=3.5, LOWER=10.0, CAPW=0.12, PIT_IT=60, RELAX=10, WSM=10, FLAT=1.0, MIRROR=1, SIG=0.008, CLAV=0.0,
         NARROW=0.0, DOME=0.0, ELLO=-25.0, ELHI=60.0, CAPTOP=0.0, BELLY=0.0, VEE=0.0, NOTCH=0.0, VPHI=-15.0, NPHI=-45.0, VT=0.36,
         COLLAR=0.0, CHOL=1.5, CNOT=1.0, CHEAD=1.2, CSR=7.0, CSR2=6.0, CSH=7.0, CSH2=14.0, CVH=16.0, CSN=8.0, CNZ=1.545, CX0=0.018, CX1=0.175, CZ0=1.533, CZ1=1.525, CS=2.0, UNFOLD=0.0, UMINA=4.0, UDEL=2.0, UIT=20)   # step 8 (narrower shoulders, Body 3 B-narrow): both 0 = off, B rebuilds unchanged; step 9 (collarbones): COLLAR 0 = off
for k in K: K[k] = float(os.environ.get(k, K[k]))
print("K", K)
D = dict(np.load(sys.argv[1])); out = sys.argv[2]
V = D["V"].copy(); W = D["W"].copy(); fl = D["fl"]; fv = D["fv"]; UV = D["uv"].copy(); reg = D["region"]
names = [str(x) for x in D["names"]]; d = dict(bn=[str(x) for x in D["bn"]], bh=D["bh"], bt=D["bt"])
ls = np.r_[0, np.cumsum(fl)[:-1]]
ni = {n: i for i, n in enumerate(names)}
# her skin has split vertices (two indices at one position, e.g. along the forearm). Every graph operation below runs on
# the WELDED topology and every per-vertex field is equal across a weld group, so the two sides of a split never part
# (they did: one-sided border fades, normals and Laplacians opened slits on the forearms).
from scipy.sparse.csgraph import connected_components
_pr = cKDTree(D["V"]).query_pairs(2e-5, output_type="ndarray")
_, WG = connected_components(sp.coo_matrix((np.ones(len(_pr)), (_pr[:, 0], _pr[:, 1])), shape=(len(D["V"]),) * 2), directed=False)
WN = np.bincount(WG); print("weld groups (split vertices): %d groups, %d vertices" % ((WN > 1).sum(), WN[WN > 1].sum()))


def gmean(A, g):
    """rows of A averaged over the weld groups g (ids per row)."""
    _, gi = np.unique(g, return_inverse=True); gi = gi.ravel(); n = np.bincount(gi).astype(float)
    S_ = np.zeros((len(n),) + A.shape[1:]); np.add.at(S_, gi, A)
    return (S_ / n.reshape((-1,) + (1,) * (A.ndim - 1)))[gi]


def sub(flag):
    f = np.nonzero(fl == 3)[0]
    T3 = fv[ls[f][:, None] + np.arange(3)]
    m = (reg[T3] == flag).all(1); f = f[m]; Tg = T3[m]
    vid = np.unique(Tg); loc = -np.ones(len(V), int); loc[vid] = np.arange(len(vid))
    inreg = np.zeros(len(fl), bool); inreg[f] = True
    outside = np.zeros(len(V), bool)
    for k in np.nonzero(~inreg)[0]: outside[fv[ls[k]:ls[k] + fl[k]]] = True
    cidx = ls[f][:, None] + np.arange(3)
    outside = np.bincount(WG, weights=outside, minlength=WG.max() + 1)[WG] > 0   # a split vertex whose twin is outside
    return dict(f=f, T=loc[Tg], vid=vid, border=outside[vid], cidx=cidx, g=WG[vid])


def weld_pairs(g):
    o = np.argsort(g, kind="stable"); gs = g[o]; same = gs[1:] == gs[:-1]
    return np.c_[o[:-1][same], o[1:][same]]


def edges_w(X, T, g=None):
    e = np.r_[T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]; e.sort(1); e = np.unique(e, axis=0)
    L = np.linalg.norm(X[e[:, 0]] - X[e[:, 1]], axis=1)
    if g is not None:   # weld groups joined at ~0 length
        wp = weld_pairs(g); e = np.r_[e, wp]; L = np.r_[L, np.full(len(wp), 1e-9)]
    n = len(X)
    return e, sp.coo_matrix((np.r_[L, L], (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(n, n)).tocsr()


def border_fade(X, T, border, r0=0.004, r1=0.025, g=None):
    e, G = edges_w(X, T, g)
    dist = dijkstra(G, indices=np.nonzero(border)[0], min_only=True, limit=0.2)
    return ss((dist - r0) / (r1 - r0))


def gsmooth(X, Dv, sigma):
    tr = cKDTree(X); M = tr.sparse_distance_matrix(tr, 3 * sigma, output_type="coo_matrix")
    w = np.exp(-0.5 * (M.data / sigma) ** 2)
    A = sp.coo_matrix((w, (M.row, M.col)), shape=(len(X), len(X))).tocsr()
    den = np.asarray(A.sum(1)).ravel()
    return (A @ Dv) / den[:, None]


def umb(T, n, g=None):
    """umbrella operator; with weld groups g it is the welded one (neighbours of the group, equal on every member)."""
    if g is None: g = np.arange(n)
    _, gi = np.unique(g, return_inverse=True); gi = gi.ravel(); m = gi.max() + 1
    e = gi[np.r_[T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]]; e.sort(1); e = np.unique(e[e[:, 0] != e[:, 1]], axis=0)
    A = sp.coo_matrix((np.ones(2 * len(e)), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(m, m)).tocsr()
    Ug = sp.diags(1 / np.maximum(np.asarray(A.sum(1)).ravel(), 1)) @ A
    cnt = np.bincount(gi, minlength=m).astype(float)
    Pe = sp.coo_matrix((np.ones(n), (np.arange(n), gi)), shape=(n, m)).tocsr()     # group -> member
    Pa = sp.coo_matrix((1 / cnt[gi], (gi, np.arange(n))), shape=(m, n)).tocsr()    # members -> group mean
    return Pe @ Ug @ Pa


def relax_resample(S, X, Wloc, iters):
    """tangential relax of the moved surface X (UVs as carried), corner UVs and vertex weights re-sampled there."""
    T = S["T"]; UVc = UV[S["cidx"]]
    FI = islands(T, UVc)
    ref = Ref(X, T, UVc, FI)
    w = Work(X, T, FI, S["border"], ref)
    if iters: w.relax(int(iters), lam=0.4)
    cuv, cd = w.corner_uv(); fi, bar, dist = w.vertex_anchor()
    Wn = gmean((Wloc[T[fi]] * bar[:, :, None]).sum(1), S["g"])
    Vn = gmean(w.V, S["g"])
    print("  relax: weld groups spread before mean %.4f mm" % (np.linalg.norm(Vn - w.V, axis=1).max() * 1e3))
    w.V = Vn
    mv = np.linalg.norm(w.V - X, axis=1)
    print("  relax: moved p95 %.2f max %.2f mm, locate max %.4f mm" % (np.percentile(mv, 95) * 1e3, mv.max() * 1e3, max(cd.max(), dist.max()) * 1e3))
    return w.V, cuv, Wn


def armkeep(Wv, sd):
    return Wv[:, ni["upperarm_" + sd]] + Wv[:, ni["lowerarm_" + sd]] + Wv[:, ni["hand_" + sd]] > 0.5


# ---------------- 0. shoulder tops lowered at rest, every vertex both sides (the trap and shoulder top are on the
# neck graft's skin): 0 at the side neck point (|x| 8 cm), a straight ramp to the acromion (|x| 19 cm), kept over the
# cap and faded out down the arm and below the collarbone / scapula line
F = Frame(d, "r")
xa = np.abs(V[:, 0]); zr0 = V[:, 2] - F.A[2]
ramp = np.clip((xa - 0.08) / 0.11, 0, 1)
ramp = np.where(xa < 0.085, ss((xa - 0.08) / 0.01) * ramp, ramp)
tt = np.minimum(F.coords(V)["t"], Frame(d, "l").coords(V)["t"])
glow = K["LOWER"] * 1e-3 * ramp * ss((zr0 + 0.02) / 0.04) * ss((0.30 - tt) / 0.25) * (xa > 0.075)
moved0 = glow > 1e-6
V[:, 2] -= glow
print("lowering: %d vertices, max %.1f mm" % (moved0.sum(), glow.max() * 1e3))
S = sub(1); vid = S["vid"]; T = S["T"]; X0 = V[vid].copy(); W0 = W[vid].copy()
keepr = armkeep(W0, "r")
prof0 = profile(X0, T, F, keepr); show_profile(prof0, "R before")
c = F.coords(X0); t, u, phi, r, e = c["t"], c["u"], c["phi"], c["r"], c["e"]
Dv = np.zeros_like(X0)
# 1. slimming: per-station girth targets (mm), the cut spread round the arm by g(u, phi)
st_u = np.array([0.15, 0.30, 0.46, 0.50, 0.60, 0.75, 0.90, 1.0, 1.1, 1.2, 1.3, 1.5, 1.7, 1.85, 1.9, 1.95])
tgt = np.array([np.nan, 300, 274, 268, 256, 244, 232, 226, 238, 246, 242, 218, 188, 175, 172, 176])
cur = np.array([p[2] for p in prof0])
k_st = np.where(np.isnan(tgt), 1.0, tgt / cur)
k_st = 1 - K["SLIM"] * (1 - k_st)
k = np.interp(u, st_u, k_st)
k = 1 - (1 - k) * ss((t - 0.18) / 0.14)  # no cut on the cap / pit root
gbar = np.interp(u, st_u, cur) / (2 * np.pi) / 1e3   # mean radius
cp = np.cos(np.radians(phi)); sp_ = np.sin(np.radians(phi))
# g: upper arm keeps the outer (deltoid) line, cuts the inner and front; elbow and forearm cut the sides (front-view width)
g_up = 1.0 - 0.55 * cp + 0.1 * sp_            # lateral 0.45, medial 1.55, front 1.1, back 0.9
g_el = 1.0 + 0.30 * cp * cp - 0.15 * sp_ * sp_   # sides 1.3, front/back 0.85
wu = ss((u - 0.75) / 0.25)
g = (1 - wu) * g_up + wu * g_el
g /= (1 - wu) * 1.0 + wu * (1.0 + 0.15 - 0.075)       # mean over phi of each
arm_t = ss((u + 0.05) / 0.25) * ss((2.0 - u) / 0.05)
Dv += -((1 - k) * gbar * g * arm_t)[:, None] * e
# 2. deltoid: the cap carried down to the V at t 0.46, narrowing round the arm, then a soft drop by 0.55
pw = 1.5 + 6 * ss((t - 0.25) / 0.25)
ang = ((1 + np.cos(np.radians(phi - 12))) / 2) ** pw
delt = K["DELT"] * 1e-3 * win(t, 0.12, 0.30, 0.47, 0.56) * ang
Dv += delt[:, None] * e
# 3. triceps: the long head's soft bulge at the back (t 0.35-0.45), flat plate from 0.65
angb = ((1 + np.cos(np.radians(phi + 100))) / 2) ** 2
tri = K["TRI"] * 1e-3 * (np.exp(-0.5 * ((t - 0.40) / 0.11) ** 2) - 0.35 * win(t, 0.62, 0.72, 0.88, 0.97))
Dv += (tri * angb * (u < 1.02))[:, None] * e
# 4. wrist: flatter (width:depth ~1.4); in the bind (palms down) the thin side faces the front camera (top axis)
wf = K["FLAT"] * win(u, 1.62, 1.80, 1.92, 1.985)
Dv += (-(4.5e-3) * wf * cp * cp + 1.5e-3 * wf * sp_ * sp_)[:, None] * e
# 6. collarbone hint (off by default)
fade = border_fade(X0, T, S["border"], g=S["g"])
Dv = gmean(gsmooth(X0, Dv, K["SIG"]), S["g"]) * fade[:, None]
X1 = X0 + Dv
# 7. pit fairing (as g2c post.py: edit.pit_mask, Taubin), on the moved surface
pm = win(t, -0.30, -0.18, 0.22, 0.36) * ss((np.abs(phi) - 110) / 30) * ss((0.11 - r) / 0.025) * fade
Wn = umb(T, len(X1), S["g"]); m_ = pm[:, None]
for _ in range(int(K["PIT_IT"])):
    X1 = X1 + 0.5 * m_ * (Wn @ X1 - X1); X1 = X1 + (-0.53) * m_ * (Wn @ X1 - X1)
mv = np.linalg.norm(X1 - X0, axis=1); print("R shape: moved p95 %.1f max %.1f mm, pit verts %d" % (np.percentile(mv, 95) * 1e3, mv.max() * 1e3, (pm > 0.05).sum()))
X2, cuv, W2 = relax_resample(S, X1, W0, K["RELAX"])
# ---------------- right arm: weights ----------------
c2 = F.coords(X2); t2, phi2 = c2["t"], c2["phi"]
iu, il, ic, ih = ni["upperarm_r"], ni["lowerarm_r"], ni["clavicle_r"], ni["hand_r"]
fade2 = border_fade(X2, T, S["border"], 0.0, 0.015, g=S["g"])
# a. the twist hand-off (t 0.15-0.6): Laplacian smoothing of the rows
Um = umb(T, len(X2), S["g"]); mw = (win(t2, 0.05, 0.15, 0.60, 0.72) * fade2)[:, None]
for _ in range(int(K["WSM"])): W2 = W2 + 0.5 * mw * (Um @ W2 - W2)
dlt = np.zeros(1)
# c. ~0.05 clavicle on the cap (so ClavicleLift moves it)
capz = win(t2, -0.25, -0.1, 0.25, 0.4) * ss((90 - np.abs(phi2)) / 40) * (W2[:, iu] > 0.2)
need = np.clip(0.05 - W2[:, ic], 0, None) * capz
W2[:, iu] -= need; W2[:, ic] += need
W2 = np.clip(W2, 0, None); W2 /= W2.sum(1, keepdims=True)
print("R weights: trap zone moved %.1f (sum), cap clav added %.1f" % (dlt.sum(), need.sum()))
prof1 = profile(X2, T, F, armkeep(W2, "r")); show_profile(prof1, "R after")
V[vid] = X2; W[vid] = W2.astype(np.float32); UV[S["cidx"]] = cuv
# ---------------- left: the right's shape and weights, mirrored ----------------
if K["MIRROR"]:
    FL = Frame(d, "l")
    SL = sub(2); vl = SL["vid"]; TL = SL["T"]; Y0 = V[vl].copy(); WL0 = W[vl].copy()
    # target: the right half of the body (region + 4 cm of torso), mirrored, with the skeleton's own L/R offset
    f3 = np.nonzero(fl == 3)[0]; allT = []
    for k_ in range(len(fl)):
        pass
    tri_all = []
    for k_ in range(len(fl)):
        p = fv[ls[k_]:ls[k_] + fl[k_]]
        for j in range(1, len(p) - 1): tri_all.append((p[0], p[j], p[j + 1]))
    tri_all = np.array(tri_all)
    cen = V[tri_all].mean(1); near = (cen[:, 0] < 0.002) & (cKDTree(V[vid]).query(cen)[0] < 0.04)
    TR = tri_all[near]; vr = np.unique(TR); lr = -np.ones(len(V), int); lr[vr] = np.arange(len(vr)); TRl = lr[TR]
    Q = V[vr].copy(); Q[:, 0] *= -1
    cq = F.coords(V[vr]); uq = cq["u"]
    mE = F.E * [-1, 1, 1]; mW = F.Wr * [-1, 1, 1]
    offE = FL.E - mE; offW = FL.Wr - mW
    a1 = ss((uq - 0.3) / 0.7)[:, None]; a2 = np.clip(uq - 1.0, 0, 1)[:, None]
    Q = Q + a1 * ((1 - a2) * offE + a2 * offW)
    TRl = TRl[:, ::-1]   # mirror flips the winding
    SR = Surf(Q, TRl, k=32)
    nL = gmean(vnormals(Y0, TL), SL["g"]); nL /= np.linalg.norm(nL, axis=1)[:, None]   # welded normals
    Y = Y0.copy()
    for _ in range(4):
        q, dd, fi, bar = SR.query(Y)
        Y = Y + ((q - Y) * nL).sum(1)[:, None] * nL
    q, dd, fi, bar = SR.query(Y)
    fadeL = border_fade(Y0, TL, SL["border"], g=SL["g"])
    move = (Y - Y0) * fadeL[:, None]
    print("L onto mirrored R: along-normal move p50 %.1f p95 %.1f max %.1f mm; residual to target p95 %.2f mm"
          % tuple(np.r_[np.percentile(np.linalg.norm(Y - Y0, axis=1), [50, 95]) * 1e3, np.linalg.norm(Y - Y0, axis=1).max() * 1e3, np.percentile(dd, 95) * 1e3]))
    Y1 = Y0 + move
    # weights: the right's at the mirrored location, names swapped, blended by the same fade
    WR = W[vr]
    Wm = (WR[TRl[fi]] * bar[:, :, None]).sum(1)
    sw = np.arange(len(names))
    for i, n in enumerate(names):
        if n.endswith("_r") and n[:-2] + "_l" in ni: sw[i] = ni[n[:-2] + "_l"]
        elif n.endswith("_l") and n[:-2] + "_r" in ni: sw[i] = ni[n[:-2] + "_r"]
    Wm2 = np.zeros_like(Wm); Wm2[:, sw] = Wm
    WL1 = WL0 * (1 - fadeL[:, None]) + Wm2 * fadeL[:, None]
    Y2, cuvL, WL2 = relax_resample(SL, Y1, WL1, K["RELAX"])
    V[vl] = Y2; W[vl] = WL2.astype(np.float32); UV[SL["cidx"]] = cuvL
    profL = profile(Y2, TL, FL, armkeep(WL2, "l")); show_profile(profL, "L after")
# trap and shoulder top, both sides, every vertex: no upper arm inside the acromion, <= 0.25 on the cap's top
for sd in "lr":
    Fs = Frame(d, sd); iu, ic = ni["upperarm_" + sd], ni["clavicle_" + sd]
    xs = V[:, 0] * Fs.sx; zr2 = V[:, 2] - Fs.A[2]
    zone = ss((xs - 0.06) / 0.015) * ss((0.215 - xs) / 0.015) * ss((zr2 - 0.025) / 0.015)
    cap = K["CAPW"] * ss((xs - 0.17) / 0.02)
    ua = W[:, iu]; dl = (ua - np.minimum(ua, cap)) * zone
    W[:, iu] -= dl; W[:, ic] += dl
    print("trap rule %s: %d vertices, %.1f weight moved to the clavicle" % (sd, (dl > 1e-4).sum(), dl.sum()))
# 8. narrower shoulders (off by default), both sides, every vertex, after the arm shape and the mirror; a smooth function
# of rest position only, so a weld group's members move alike and nothing is relaxed or re-sampled.
#   NARROW (mm): a medial x move, full on the cap's outer face (arm-frame phi 0 = lateral at rest) for t <= 0.2, gone by
#     t 0.45 down the arm, toward the neck by |x| 14 cm, and over the front/back (((1 + cos phi) / 2)^2: 0.25 at the
#     front and back, 0 underneath, so the pit does not move), and off the shoulder's top (elevation from the joint).
#   DOME (0-1): the outer cap's bulge above the chord of its lateral profile r(t) (phi within 30 deg of lateral, chord
#     from t -0.25 to 0.45) taken in by that fraction, radially, with the same phi falloff: less ball, no facet.
moved8 = np.zeros(len(V), bool)
if K["NARROW"] or K["DOME"] or K["CAPTOP"] or K["BELLY"] or K["VEE"] or K["NOTCH"]:
    V8 = V.copy()
    for sd in "rl":
        Fs = Frame(d, sd); xs = V8[:, 0] * Fs.sx; on = xs > 0.02
        c8 = Fs.coords(V8); t8, phi8, r8, e8 = c8["t"], c8["phi"], c8["r"], c8["e"]
        a8 = ((1 + np.cos(np.radians(phi8))) / 2) ** 2
        wt = ss((0.45 - t8) / 0.25) * ss((t8 + 0.6) / 0.2)
        # not on the shoulder's top (it would slide the top outline in and drop it, steepening the slope): fade by the
        # elevation of the point seen from the joint, full at ELLO deg and below, gone by ELHI
        el = np.degrees(np.arctan2(V8[:, 2] - Fs.A[2], xs - Fs.A[0] * Fs.sx))
        dx = K["NARROW"] * 1e-3 * ss((xs - 0.14) / 0.045) * wt * a8 * ss((K["ELHI"] - el) / (K["ELHI"] - K["ELLO"])) * on
        # the outer profile R(t): binned max r near phi 0, smoothed; bulge = R - chord, zero at both chord ends
        tb = np.arange(-0.35, 0.551, 0.01); R = np.full(len(tb), np.nan)
        lat = on & (np.abs(phi8) < 30) & (r8 < 0.10)
        for i, tc in enumerate(tb):
            m = lat & (np.abs(t8 - tc) < 0.015)
            if m.any(): R[i] = r8[m].max()
        R = np.interp(tb, tb[~np.isnan(R)], R[~np.isnan(R)])
        ker = np.exp(-0.5 * (np.arange(-8, 9) * 0.01 / 0.03) ** 2); ker /= ker.sum()
        Rs = np.convolve(np.r_[np.full(8, R[0]), R, np.full(8, R[-1])], ker, "valid")
        ta, tb_ = -0.25, 0.45; Ca = np.interp(ta, tb, Rs); Cb = np.interp(tb_, tb, Rs)
        bul = np.clip(Rs - (Ca + (Cb - Ca) * (tb - ta) / (tb_ - ta)), 0, None) * ss((tb - ta) / 0.08) * ss((tb_ - tb) / 0.08)
        dr = K["DOME"] * np.interp(t8, tb, bul) * a8 * ss((xs - 0.12) / 0.04) * on * (r8 < 0.10)
        print("narrow %s: dx max %.1f mm on %d verts; dome bulge max %.1f mm at t %.2f, move max %.1f mm on %d verts"
              % (sd, dx.max() * 1e3, (dx > 1e-5).sum(), bul.max() * 1e3, tb[np.argmax(bul)], dr.max() * 1e3, (dr > 1e-5).sum()))
        # CAPTOP (mm, Body 4): the cap's top-outer arc taken in toward the joint, so the outline from the acromion runs
        #   down-out into the deltoid's belly instead of rounding over a ball centred on the joint. Frontal-plane angle
        #   seen from the joint (0 = straight out, 90 = up): full 25-55 deg, gone by 0 and 80; out of that plane it fades
        #   as cos^2 (gone by 70 deg front/back); only within 75 mm of the joint (full inside 55).
        q8 = V8 - Fs.A; X8 = q8[:, 0] * Fs.sx; Z8 = q8[:, 2]; hd = np.hypot(X8, Z8)
        th8 = np.degrees(np.arctan2(Z8, X8)); ps8 = np.degrees(np.arctan2(np.abs(q8[:, 1]), np.maximum(hd, 1e-9)))
        dcap = (K["CAPTOP"] * 1e-3 * ss(th8 / 25) * ss((80 - th8) / 25) * np.cos(np.radians(np.clip(ps8 * 90 / 70, 0, 90))) ** 2
                * ss((0.075 - np.linalg.norm(q8, axis=1)) / 0.02) * on)
        ucap = q8 / np.maximum(np.linalg.norm(q8, axis=1), 1e-9)[:, None]
        # BELLY (mm, Body 4): the deltoid's upper belly (t 0.08-0.46, full 0.20-0.33) moved medially (x), lateral face
        #   only (phi falloff as NARROW), all elevations: the breadth line at t 0.30 comes in, the V (t 0.46) stays.
        dxb = K["BELLY"] * 1e-3 * win(t8, 0.08, 0.20, 0.33, 0.46) * a8 * ss((xs - 0.14) / 0.045) * on * (r8 < 0.10)
        print("captop %s: max %.1f mm on %d verts; belly max %.1f mm on %d verts" % (sd, dcap.max() * 1e3, (dcap > 1e-5).sum(), dxb.max() * 1e3, (dxb > 1e-5).sum()))
        V[:, 0] -= Fs.sx * (dx + dxb)
        V -= dr[:, None] * e8 + dcap[:, None] * ucap
        moved8 |= (dcap > 1e-6) | (dxb > 1e-6)
        # teardrop cap (Body 5), radial (out from the humerus axis), on the deltoid's outer half (phi centred VPHI deg,
        #   0 = lateral at rest, -90 = back), so the cap tapers into the arm instead of a dome sitting on a tube:
        #   NOTCH (mm, the largest move): within +-90 deg of NPHI (cos^2), the concave dip between the cap and the arm filled toward the upper hull of each
        #     sector's profile r(t) (t -0.10..0.50, sectors every 10 deg, smoothed in t and phi), fill proportional to
        #     the dip, so a straight-ish run replaces the notch and nothing convex grows.
        #   VEE (mm): the deltoid's lower V raised: full t VT +-0.06, gone by VT +-0.20 (VT 0.36: 0.16-0.56); its sector narrows down the
        #     arm (half-width 85 deg at t 0.2 -> 35 at 0.5, cos^2) so the outline runs to a point at the insertion.
        if K["VEE"] or K["NOTCH"]:
            dph = (phi8 - K["VPHI"] + 180) % 360 - 180
            hw = np.interp(t8, [0.2, 0.5], [85.0, 35.0])
            dv = (K["VEE"] * 1e-3 * win(t8, K["VT"] - 0.20, K["VT"] - 0.06, K["VT"] + 0.06, K["VT"] + 0.20) * np.cos(np.radians(np.clip(np.abs(dph) / hw * 90, 0, 90))) ** 2
                  * ss((xs - 0.12) / 0.04) * on * (r8 < 0.10))
            dn = np.zeros(len(V8))
            if K["NOTCH"]:
                th_ = np.arange(-0.15, 0.601, 0.01); pb = np.arange(-180, 180, 10.0); Dg = np.zeros((len(th_), len(pb)))
                kt = np.exp(-0.5 * (np.arange(-6, 7) * 0.01 / 0.02) ** 2); kt /= kt.sum()
                for j, pc in enumerate(pb):
                    m0 = on & (np.abs((phi8 - pc + 180) % 360 - 180) < 10) & (r8 < 0.10) & (xs > 0.08)
                    Rj = np.full(len(th_), np.nan)
                    for i, tc in enumerate(th_):
                        m = m0 & (np.abs(t8 - tc) < 0.012)
                        if m.sum() > 1: Rj[i] = r8[m].max()
                    if np.isfinite(Rj).sum() < 10: continue
                    Rj = np.interp(th_, th_[np.isfinite(Rj)], Rj[np.isfinite(Rj)])
                    Rj = np.convolve(np.r_[np.full(6, Rj[0]), Rj, np.full(6, Rj[-1])], kt, "valid")
                    sel = np.where((th_ >= -0.10) & (th_ <= 0.50))[0]; hull = [sel[0]]
                    for i in sel[1:]:   # upper hull (monotone chain)
                        while len(hull) > 1 and ((th_[hull[-1]] - th_[hull[-2]]) * (Rj[i] - Rj[hull[-2]])
                                                 - (Rj[hull[-1]] - Rj[hull[-2]]) * (th_[i] - th_[hull[-2]])) >= 0: hull.pop()
                        hull.append(i)
                    Hj = np.interp(th_, th_[hull], Rj[hull]); Dg[:, j] = np.where((th_ >= -0.10) & (th_ <= 0.50), np.clip(Hj - Rj, 0, None), 0)
                kp = np.exp(-0.5 * (np.arange(-3, 4) * 10 / 15.0) ** 2); kp /= kp.sum()
                Dg = np.stack([np.convolve(np.r_[Dg[i, -3:], Dg[i], Dg[i, :3]], kp, "valid") for i in range(len(th_))])
                Dg = np.stack([np.convolve(np.r_[np.full(6, Dg[0, j]), Dg[:, j], np.full(6, Dg[-1, j])], kt, "valid") for j in range(len(pb))], 1)
                Dg *= (ss((th_ - 0.0) / 0.08) * ss((0.48 - th_) / 0.08))[:, None]
                # bilinear lookup (phi periodic)
                fi = np.clip((t8 - th_[0]) / 0.01, 0, len(th_) - 1.001); i0 = fi.astype(int); ft = fi - i0
                fj = ((phi8 + 180) % 360) / 10.0; j0 = fj.astype(int) % len(pb); j1 = (j0 + 1) % len(pb); fp = fj - np.floor(fj)
                dg = ((1 - ft) * ((1 - fp) * Dg[i0, j0] + fp * Dg[i0, j1]) + ft * ((1 - fp) * Dg[i0 + 1, j0] + fp * Dg[i0 + 1, j1]))
                dpn = (phi8 - K["NPHI"] + 180) % 360 - 180   # the notch's sector: cos^2 over +-90 deg about NPHI (back of the cap)
                wn = np.cos(np.radians(np.clip(np.abs(dpn), 0, 90))) ** 2 * ss((xs - 0.12) / 0.04) * on * (r8 < 0.10)
                if os.environ.get("NDBG"):
                    for j in range(0, len(pb), 3): print("  dip phi %4.0f: " % pb[j] + " ".join("%4.1f" % (x * 1e3) for x in Dg[5:66:5, j]))
                dg = dg * wn; dn = K["NOTCH"] * 1e-3 * dg / max(dg.max(), 1e-9)
                print("notch %s: hull dip max %.1f mm at t %.2f phi %.0f" % (sd, dg.max() * 1e3, t8[np.argmax(dg)], phi8[np.argmax(dg)]))
            print("vee %s: max %.1f mm on %d verts; notch max %.1f mm on %d verts" % (sd, dv.max() * 1e3, (dv > 1e-5).sum(), dn.max() * 1e3, (dn > 1e-5).sum()))
            V += (dv + dn)[:, None] * e8
            moved8 |= (dv > 1e-6) | (dn > 1e-6)
        moved8 |= (dx > 1e-6) | (dr > 1e-6)
    prof8 = profile(V[vid], T, F, armkeep(W[vid], "r")); show_profile(prof8, "R narrowed")
    moved0 = moved0 | moved8
# 9. collarbones (Body 5, off by default): her clavicles, the hollow above their outer two-thirds and the sternal notch,
#   along each vertex's welded normal, a smooth compactly supported function of rest position (a weld group moves as one;
#   nothing relaxed, weights untouched). The bone's line, per side: from |x| CX0 (off the notch) to CX1 (the acromion),
#   height CZ0 -> CZ1 with a gentle S (CS mm: the inner half up, the outer down), laid on her front surface (a plane fitted
#   to the skin every 5 mm, smoothed). Each vertex is measured from it in the surface's up-the-yoke direction (v, + up).
#   COLLAR (mm): the ridge's height (gaussian in v, sigma CSR mm below the crest, CSR2 above; full s 0.08-0.80 of the line, the inner head CHEAD x as
#     proud, gone past the acromion); the hollow CHOL x COLLAR deep (sigma CSH mm below, CSH2 above: a steep wall under the bone's top, a long one up to the trapezius; centred CVH mm above the crest, over
#     s 0.25-1.0: the outer two-thirds); the notch CNOT x COLLAR deep at the midline (height CNZ; sigma CSN mm wide, 7 tall).
#   Kept off Face's neck graft seam (the open edge under her head: zero within 45 mm of it, full by 60) and off the
#   graft/body paint seam (zero within 8 mm, full by 18), so neither seam's vertices move.
moved9 = np.zeros(len(V), bool)
if K["COLLAR"]:
    Tq = np.concatenate([fv[ls[np.where(fl == n)[0]][:, None] + np.array([0, k, k + 1])] for n in np.unique(fl) for k in range(1, n - 1)])
    fn9 = np.cross(V[Tq[:, 1]] - V[Tq[:, 0]], V[Tq[:, 2]] - V[Tq[:, 0]]); N9 = np.zeros_like(V)
    for k in range(3): np.add.at(N9, Tq[:, k], fn9)
    N9 = gmean(N9, WG); N9 /= np.maximum(np.linalg.norm(N9, axis=1), 1e-12)[:, None]   # welded normals
    E9 = np.sort(np.r_[Tq[:, [0, 1]], Tq[:, [1, 2]], Tq[:, [2, 0]]], 1); E9 = WG[E9]; E9.sort(1)
    eu, ec = np.unique(E9[E9[:, 0] != E9[:, 1]], axis=0, return_counts=True)
    bnd = np.isin(WG, eu[ec == 1].ravel()) & (V[:, 2] > 1.55)                              # the open edge under her head
    gr9 = D["graft"] > 0; gseam = np.zeros(len(V), bool)
    for n in np.unique(fl):   # graft/body seam: vertices of faces that mix graft and body vertices
        idx = fv[ls[np.where(fl == n)[0]][:, None] + np.arange(n)]; mx = gr9[idx].any(1) & ~gr9[idx].all(1); gseam[idx[mx].ravel()] = True
    dH = cKDTree(V[bnd]).query(V)[0]; dG = cKDTree(V[gseam]).query(V)[0]
    keep9 = ss((dH - 0.045) / 0.015) * ss((dG - 0.008) / 0.010)
    fr = (V[:, 1] < 0.04) & (V[:, 2] > 1.40) & (V[:, 2] < 1.62)
    tot = np.zeros(len(V)); rid = np.zeros(len(V)); hol = np.zeros(len(V))
    def gau(u, s, s2=None):   # gaussian, compact (gone by 3 sigma); s2: its sigma above (u > 0)
        s = np.where(u > 0, s if s2 is None else s2, s); return np.exp(-0.5 * (u / s) ** 2) * ss((3 * s - np.abs(u)) / s)
    def surf(xc, zc):   # front skin at (x, z): a plane y = a + b dx + c dz over a 7 mm box; returns y and its outward normal
        for bx in (0.007, 0.011, 0.016):
            i = np.where(fr & (np.abs(V[:, 0] - xc) < bx) & (np.abs(V[:, 2] - zc) < bx))[0]
            if len(i) >= 6: break
        i = i[V[i, 1] < V[i, 1].min() + 0.008]
        A = np.c_[np.ones(len(i)), V[i, 0] - xc, V[i, 2] - zc]; a, b, c = np.linalg.lstsq(A, V[i, 1], rcond=None)[0]
        n = np.array([b, -1.0, c]); return a, n / np.linalg.norm(n)
    for sg in (1.0, -1.0):
        xs = np.arange(0.0, K["CX1"] + 0.03, 0.005); s9 = (xs - K["CX0"]) / (K["CX1"] - K["CX0"])
        zc = K["CZ0"] + (K["CZ1"] - K["CZ0"]) * np.clip(s9, 0, 1) + K["CS"] * 1e-3 * np.sin(2 * np.pi * np.clip(s9, 0, 1))
        sf = [surf(sg * x, z) for x, z in zip(xs, zc)]; yc = np.array([q[0] for q in sf]); nc = np.array([q[1] for q in sf])
        ker = np.array([1, 2, 3, 2, 1.0]); ker /= ker.sum(); sm = lambda a: np.convolve(np.r_[a[:2][::-1], a, a[-2:][::-1]], ker, "valid")
        yc = sm(yc); nc = np.stack([sm(nc[:, k]) for k in range(3)], 1); nc /= np.linalg.norm(nc, axis=1)[:, None]
        on = (V[:, 0] * sg > -0.004) & fr
        x9 = np.clip(V[:, 0] * sg, 0, xs[-1]); jf = x9 / 0.005; j0 = np.minimum(jf.astype(int), len(xs) - 2); fj = jf - j0
        L = lambda a: a[j0] * (1 - fj) + a[j0 + 1] * fj if a.ndim == 1 else a[j0] * (1 - fj)[:, None] + a[j0 + 1] * fj[:, None]
        C = np.c_[V[:, 0], L(yc), L(zc)]; nC = L(nc); nC[:, 0] *= sg
        tu = np.c_[np.zeros(len(V)), nC[:, 2], -nC[:, 1]]; tu /= np.linalg.norm(tu, axis=1)[:, None]    # up the yoke (up and back)
        dd = V - C; v = (dd * tu).sum(1); h = (dd * nC).sum(1); sv = (x9 - K["CX0"]) / (K["CX1"] - K["CX0"])
        sheet = ss((0.030 - np.abs(h)) / 0.010) * on
        ar = win(sv, -0.08, 0.08, 0.80, 1.05) * (1 + (K["CHEAD"] - 1) * win(sv, -0.08, 0.0, 0.10, 0.30))
        r_ = K["COLLAR"] * 1e-3 * ar * gau(v, K["CSR"] * 1e-3, K["CSR2"] * 1e-3) * sheet
        hl = K["CHOL"] * K["COLLAR"] * 1e-3 * win(sv, 0.15, 0.35, 0.85, 1.05) * gau(v - K["CVH"] * 1e-3, K["CSH"] * 1e-3, K["CSH2"] * 1e-3) * sheet
        rid += r_; hol += hl; tot += r_ - hl
    # the notch: at the midline, between the bones' inner heads
    yN, nN = surf(0.0, K["CNZ"]); tN = np.array([0, nN[2], -nN[1]]) / np.hypot(nN[1], nN[2]); dN = V - np.array([0, yN, K["CNZ"]])
    nt = K["CNOT"] * K["COLLAR"] * 1e-3 * gau(V[:, 0], K["CSN"] * 1e-3) * gau(dN @ tN, 0.007) * ss((0.012 - np.abs(dN @ nN)) / 0.006) * fr
    tot = (tot - nt) * keep9
    V += tot[:, None] * N9
    moved9 = np.abs(tot) > 1e-7
    print("collar: ridge max %.2f mm, hollow max %.2f mm, notch max %.2f mm; %d vertices moved (max |d| %.2f mm); neck seam %d verts, "
          "max move within 45 mm of it %.4f mm; graft seam %d verts, max move on it %.4f mm"
          % (rid.max() * 1e3, hol.max() * 1e3, nt.max() * 1e3, moved9.sum(), np.abs(tot).max() * 1e3, bnd.sum(),
             np.abs(tot[dH < 0.045]).max() * 1e3, gseam.sum(), np.abs(tot[gseam]).max() * 1e3))
    moved0 = moved0 | moved9
# every weld group shares one position and one weight row (reports what was left to close)
spread = np.linalg.norm(gmean(V, WG) - V, axis=1); wsp = np.abs(gmean(W, WG) - W).max(1)  # (all groups)
print("weld check: position off group mean max %.4f mm, weight max %.5f" % (spread.max() * 1e3, wsp.max()))
tch = np.bincount(WG, weights=((reg > 0) | moved0).astype(float), minlength=WG.max() + 1)[WG] > 0   # groups this script touched
V[tch] = gmean(V[tch], WG[tch]); W[tch] = gmean(W[tch], WG[tch]).astype(np.float32)
# 10. unfold (Body 5, off by default): her source mesh has needle triangles (one at the front of her left upper arm, 24 mm
#   long and 0.7 mm high, its own UV island where three others meet); dense.py splits them into a zero-width strip of
#   slivers that the left's mirror move then folds (dihedral 144 deg at t 0.21 phi 93), and their auto normals, angle-
#   weighted, turn the strip's points up to 70 deg off the skin: light and dark nicks at 1:1. Here every point of a sliver
#   (a face with an angle under UMINA deg, both sides, the region only) is laid onto the skin round it (a quadratic height
#   field fitted to the points within 8 mm that are not on slivers, gaussian 4 mm) and relaxed in that surface (UIT
#   uniform umbrella steps, tangential, at most UDEL mm from where it was), so the strip opens into proper triangles and
#   lies flush; nothing else moves. Each moved corner's UV is re-sampled on its own UV island at the new point; weights
#   stay (they change little over 2 mm). A weld group moves as one.
if K["UNFOLD"]:
    tri, tcor = [], []
    for k_ in range(len(fl)):
        for j in range(1, fl[k_] - 1):
            tri.append((fv[ls[k_]], fv[ls[k_] + j], fv[ls[k_] + j + 1])); tcor.append((ls[k_], ls[k_] + j, ls[k_] + j + 1))
    tri = np.array(tri); tcor = np.array(tcor); TWu = WG[tri]

    def _angles(X):
        out = []
        for i in range(3):
            u_ = X[tri[:, (i + 1) % 3]] - X[tri[:, i]]; v_ = X[tri[:, (i + 2) % 3]] - X[tri[:, i]]
            out.append(np.degrees(np.arctan2(np.linalg.norm(np.cross(u_, v_), axis=1), (u_ * v_).sum(1))))
        return np.stack(out, 1)
    zt = (reg[tri] > 0).all(1)
    slv = (_angles(V).min(1) < K["UMINA"]) & zt
    sv = np.unique(TWu[slv]); isv = np.zeros(WG.max() + 1, bool); isv[sv] = True
    ng = WG.max() + 1; Vg = np.zeros((ng, 3)); np.add.at(Vg, WG, V); Vg /= np.bincount(WG, minlength=ng)[:, None]
    fnu = np.cross(V[tri[:, 1]] - V[tri[:, 0]], V[tri[:, 2]] - V[tri[:, 0]]); fcu = V[tri].mean(1)
    gfi = np.nonzero(~slv)[0]; gtr = cKDTree(fcu[gfi]); vtr = cKDTree(Vg)
    eu = np.r_[TWu[:, [0, 1]], TWu[:, [1, 2]], TWu[:, [2, 0]]]; eu = eu[eu[:, 0] != eu[:, 1]]
    ring = {g: set() for g in sv.tolist()}
    for a_, b_ in eu.tolist():
        if isv[a_]: ring[a_].add(b_)
        if isv[b_]: ring[b_].add(a_)
    fit = {}
    for g in sv.tolist():
        p_ = Vg[g]; n_ = fnu[gfi[gtr.query_ball_point(p_, 0.008)]].sum(0); n_ /= np.linalg.norm(n_)
        t1 = np.cross(n_, [0, 0, 1.0]) if abs(n_[2]) < 0.9 else np.cross(n_, [1.0, 0, 0]); t1 /= np.linalg.norm(t1); t2 = np.cross(n_, t1)
        nb = [h for h in vtr.query_ball_point(p_, 0.008) if not isv[h]]; Q_ = Vg[nb] - p_
        x_, y_, z_ = Q_ @ t1, Q_ @ t2, Q_ @ n_; w_ = np.exp(-0.5 * (x_ * x_ + y_ * y_) / 0.004 ** 2)
        c_ = np.linalg.lstsq(np.c_[np.ones_like(x_), x_, y_, x_ * x_, x_ * y_, y_ * y_] * w_[:, None], z_ * w_, rcond=None)[0] if len(nb) >= 8 else None
        fit[g] = (p_.copy(), n_, t1, t2, c_)

    def _onskin(g, q_):
        p_, n_, t1, t2, c_ = fit[g]
        if c_ is None: return q_
        d_ = q_ - p_; x_, y_ = d_ @ t1, d_ @ t2
        return p_ + x_ * t1 + y_ * t2 + np.clip(c_ @ [1, x_, y_, x_ * x_, x_ * y_, y_ * y_], -0.001, 0.001) * n_
    X_ = Vg.copy(); dmax = K["UDEL"] * 1e-3
    for g in sv.tolist(): X_[g] = _onskin(g, X_[g])
    for _ in range(int(K["UIT"])):
        Xn_ = X_.copy()
        for g in sv.tolist():
            p_, n_ = fit[g][:2]; dl_ = X_[list(ring[g])].mean(0) - X_[g]; dl_ -= (dl_ @ n_) * n_
            q_ = X_[g] + 0.5 * dl_; off = q_ - p_; off -= (off @ n_) * n_; lo = np.linalg.norm(off)
            if lo > dmax: q_ = q_ - off * (1 - dmax / lo)
            Xn_[g] = _onskin(g, q_)
        X_ = Xn_
    mvv = np.isin(WG, sv); Vnew = X_[WG]
    # corner UVs re-sampled on their own island, near the moved points only
    loc = np.nonzero((cKDTree(V[mvv]).query(fcu)[0] < 0.015) | mvv[tri].any(1))[0]
    UVc = UV[tcor[loc]]; FIu = islands(tri[loc], UVc); refu = Ref(V, tri[loc], UVc, FIu)
    cm = np.isin(fv, np.nonzero(mvv)[0]); cidx = np.nonzero(cm)[0]
    # each corner's island: the island of a local triangle that holds this corner
    cisl = -np.ones(len(fv), int); cisl[tcor[loc].ravel()] = np.repeat(FIu, 3)
    _, fi_, bar_, dist_ = refu.locate(Vnew[fv[cidx]], cisl[cidx])
    UV[cidx] = refu.uv(fi_, bar_)
    mv_ = np.linalg.norm(Vnew[mvv] - V[mvv], axis=1); V[mvv] = Vnew[mvv]
    a2_ = _angles(V)
    print("unfold: %d slivers (%d left, %d right), %d points moved p50 %.2f max %.2f mm; corner UVs re-sampled %d (locate max %.3f mm); "
          "slivers left %d, their min angle p50 %.1f deg" % (slv.sum(), (slv & (V[tri[:, 0], 0] > 0)).sum(), (slv & (V[tri[:, 0], 0] < 0)).sum(),
          mvv.sum(), np.median(mv_) * 1e3, mv_.max() * 1e3, len(cidx), dist_.max() * 1e3, ((a2_.min(1) < K["UMINA"]) & zt).sum(), np.median(a2_[slv].min(1))))
reg_out = np.where(reg > 0, reg, 3 * moved0)
np.savez(out, **{**D, "V": V, "W": W, "uv": UV, "region": reg_out})
print("WROTE", out)
