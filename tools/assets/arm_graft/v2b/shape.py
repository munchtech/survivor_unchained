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
         NARROW=0.0, DOME=0.0, ELLO=-25.0, ELHI=60.0, CAPTOP=0.0, BELLY=0.0)   # step 8 (narrower shoulders, Body 3 B-narrow): both 0 = off, B rebuilds unchanged
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
if K["NARROW"] or K["DOME"] or K["CAPTOP"] or K["BELLY"]:
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
        moved8 |= (dx > 1e-6) | (dr > 1e-6)
    prof8 = profile(V[vid], T, F, armkeep(W[vid], "r")); show_profile(prof8, "R narrowed")
    moved0 = moved0 | moved8
# every weld group shares one position and one weight row (reports what was left to close)
spread = np.linalg.norm(gmean(V, WG) - V, axis=1); wsp = np.abs(gmean(W, WG) - W).max(1)  # (all groups)
print("weld check: position off group mean max %.4f mm, weight max %.5f" % (spread.max() * 1e3, wsp.max()))
tch = np.bincount(WG, weights=((reg > 0) | moved0).astype(float), minlength=WG.max() + 1)[WG] > 0   # groups this script touched
V[tch] = gmean(V[tch], WG[tch]); W[tch] = gmean(W[tch], WG[tch]).astype(np.float32)
reg_out = np.where(reg > 0, reg, 3 * moved0)
np.savez(out, **{**D, "V": V, "W": W, "uv": UV, "region": reg_out})
print("WROTE", out)
