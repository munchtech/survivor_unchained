# Body 2 A step 1: HER weights on the graft (d_b: her weights take 2/3 of the graft's extra pit shear away), then the
# shoulder rules (target 1/4: no upper-arm weight on the trap inside the acromion, at most CAP_TOP on the shoulder
# top, the rest to the clavicle; at least CAP_CL clavicle on the cap). Right side only matters (the left is mirrored
# from it later), both are written.
#   python carry.py <work dir>      reads her.npz, ar.npz, graft_data.npz; writes <work>/wts.npz (VG dump order, own mask)
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from scipy.spatial import cKDTree
import scipy.sparse as sp
from scipy.sparse.linalg import spsolve
from lib import load, fan, edges, adjacency, armframe, joints, ss
from geo import Surf

WK = sys.argv[1]; J = lambda f: os.path.join(WK, f)
h = load(J("her.npz")); a = load(J("ar.npz")); D = np.load(J("graft_data.npz"))
P0 = D["V"]; names = a["names"]; ix = {n: i for i, n in enumerate(names)}
CAP_TOP = float(os.environ.get("CAP_TOP", "0.25")); CAP_CL = float(os.environ.get("CAP_CL", "0.05"))

# --- her rows by surface correspondence (kept vertices: their own row)
dd, jj = cKDTree(h["P"]).query(P0); same = dd < 1e-7; own = dd > 1e-6
Th, _, _ = fan(h["ls"], h["lt"], h["lv"]); S = Surf(h["P"], Th)
VGh = h["VG"].astype(float); VG = np.zeros((len(P0), len(names)))
VG[same] = VGh[jj[same]]
q, dist, fi, bar = S.query(P0[~same]); Wc = (VGh[Th[fi]] * bar[:, :, None]).sum(1)
top = np.argsort(-Wc, 1)[:, :4]; r = np.arange(len(Wc))[:, None]; W4 = np.zeros_like(Wc); W4[r, top] = Wc[r, top]; W4[W4 < 1e-4] = 0
VG[~same] = W4 / np.maximum(W4.sum(1, keepdims=True), 1e-9)
print("carried: kept rows %d, interpolated %d, her surface distance mm p50 %.2f p95 %.2f max %.2f" % (
    same.sum(), (~same).sum(), np.median(dist) * 1e3, np.percentile(dist, 95) * 1e3, dist.max() * 1e3))

# --- CARRY=idw: on the arm proper (each side: past the shoulder joint, r < 7 cm upper arm / 6 cm forearm), her rows
# from her own ARM vertices in the same region, k=IDW_K inverse-distance (d_b m6's swap, which took the pit shear at A 82
# from 4.6 / 4.4 to 3.0 / 3.6 deg/cm on the graft). Outside it the exact surface carry above stays.
if os.environ.get("CARRY", "idw") == "idw":
    K = int(os.environ.get("IDW_K", "4"))
    def armreg(d, P, s):
        F = armframe(d, s, P); u, f = F["u"], F["f"]
        return F["side"] & (((u["t"] >= 0) & (u["t"] < 1) & (u["r"] < 0.07)) | ((f["t"] >= 0) & (f["t"] < 1) & (f["r"] < 0.06)))
    for s in "lr":
        mh = armreg(h, h["P"], s); mg = armreg(a, P0, s) & own
        dk, ik = cKDTree(h["P"][mh]).query(P0[mg], k=K); wk = 1 / np.maximum(dk, 1e-5); wk /= wk.sum(1, keepdims=True)
        VG[mg] = (VGh[mh][ik] * wk[..., None]).sum(1)
        print("idw", s, "vertices", int(mg.sum()), "from", int(mh.sum()))
# --- the wrist's hand/lowerarm split made harmonic on graft-owned forearm vertices (post.py g3: her carried rows can
# be non-monotone along the arm and fold the inner wrist under a bent hand)
E = edges(a["ls"], a["lt"], a["lv"]); Ad = adjacency(len(P0), E)
for s in ("lr" if int(os.environ.get("WRIST", "1")) else ""):
    F = armframe(a, s, P0); ih, i2 = ix["hand_" + s], ix["lowerarm_" + s]
    su = VG[:, ih] + VG[:, i2]; x = np.where(su > 1e-6, VG[:, ih] / np.maximum(su, 1e-9), 0)
    hb = x > 0.005
    for _ in range(2): hb = hb | ((Ad @ hb.astype(float)) > 0)
    I = np.where(F["side"] & hb & (F["f"]["t"] > 0.25 * F["u"]["L"] / F["f"]["L"]) & own & (su > 0.2))[0]
    if len(I):
        Bm = np.ones(len(P0), bool); Bm[I] = False
        AII = Ad[I][:, I]; deg = np.asarray(Ad[I].sum(1)).ravel(); rhs = Ad[I][:, Bm] @ x[Bm]
        xi = np.clip(spsolve(sp.diags(deg) - AII, rhs), 0, 1); dx = np.abs(xi - x[I]); x[I] = xi
        VG[I, ih] = su[I] * x[I]; VG[I, i2] = su[I] * (1 - x[I])
        print("wrist split", s, "vertices", len(I), "hand share change mean %.3f max %.3f" % (dx.mean(), dx.max()))

# --- the arm root's weights diffused on the mesh (implicit heat flow, edge weights 1/len^2, t = SM_SIG^2/2) on graft-owned
# vertices of the upper arm's root (t_u < SM_T1, fading over 0.15; the trap/shoulder top included), each side; every other
# row fixed. Why: her rows carried exactly (piecewise linear over her coarse triangles) show, on the dense graft, the
# within-triangle shear her coarse mesh hid: at A 82 the pit band turned 4.6 / 4.4 deg/cm vs 3.0 / 3.6 with the same rows
# averaged over ~1 cm (d_b's IDW). SM_SIG=0 skips.
SIG = float(os.environ.get("SM_SIG", "0")) / 100; ST1 = float(os.environ.get("SM_T1", "0.55"))
if SIG > 0:
    Le = np.linalg.norm(P0[E[:, 0]] - P0[E[:, 1]], axis=1); c = 1 / np.maximum(Le, 1e-4) ** 2
    Lc = sp.coo_matrix((np.r_[c, c], (np.r_[E[:, 0], E[:, 1]], np.r_[E[:, 1], E[:, 0]])), shape=(len(P0),) * 2).tocsr()
    Lap = sp.diags(np.asarray(Lc.sum(1)).ravel()) - Lc
    msk = np.zeros(len(P0))
    for s in "lr":
        F = armframe(a, s, P0); msk = np.maximum(msk, F["side"] * ss((ST1 - F["u"]["t"]) / 0.15) * ss((F["u"]["t"] + 0.6) / 0.15))
    msk *= own
    I = np.where(msk > 1e-3)[0]; Bm = np.ones(len(P0), bool); Bm[I] = False
    M = (sp.identity(len(I)) + (SIG ** 2 / 2) * Lap[I][:, I]).tocsc(); rhs = VG[I] - (SIG ** 2 / 2) * (Lap[I][:, Bm] @ VG[Bm])
    from scipy.sparse.linalg import splu
    lu = splu(M); Ws = lu.solve(rhs.astype(float))
    Ws = np.clip(Ws, 0, None); Ws /= np.maximum(Ws.sum(1, keepdims=True), 1e-9)
    dW = np.abs(Ws - VG[I]).sum(1) / 2
    VG[I] = msk[I, None] * Ws + (1 - msk[I, None]) * VG[I]
    print("diffused: vertices %d sigma %.1f cm, weight moved mean %.3f p95 %.3f" % (len(I), SIG * 100, dW.mean(), np.percentile(dW, 95)))
# --- shoulder rules (bind, blend coords): sx = distance out from the midline, the acromion from her skin top over
# the upper-arm head
def acromion(s):
    j = joints(a, s); sg = -1 if s == "r" else 1; X = P0
    col = (np.abs(X[:, 0] - j["A"][0]) < 0.01) & (np.abs(X[:, 1] - j["A"][1]) < 0.025) & (np.sign(X[:, 0]) == sg)
    k = np.where(col)[0][np.argmax(X[col, 2])]; return X[k]
stat = {}
for s in ("rl" if int(os.environ.get("RULES", "1")) else ""):
    j = joints(a, s); sg = -1 if s == "r" else 1; acr = acromion(s); x = P0[:, 0] * sg; ax = acr[0] * sg
    iu, ic = ix["upperarm_" + s], ix["clavicle_" + s]
    up = P0[:, 2] - j["A"][2]
    side = np.sign(P0[:, 0]) == sg
    # the shoulder's upper skin: above the joint by more than 2.5 cm (fading in from 1.5), front to back
    hz = ss((up - 0.015) / 0.02) * side
    # (a) trap inside the acromion (from 1 cm in): upper-arm weight to none, to the clavicle; fades out over the last cm
    trap = hz * ss((ax - 0.01 - x) / 0.012) * ss((x - 0.06) / 0.01)
    # (b) shoulder top (acromion +- 3 cm, the cap's top): upper arm at most CAP_TOP
    capt = hz * (1 - ss((ax - 0.01 - x) / 0.012))
    u0 = VG[:, iu].copy()
    lim = np.where(trap > 0, u0 * (1 - trap), u0)
    lim = np.minimum(lim, np.where(capt > 0, u0 * (1 - capt) + np.minimum(u0, CAP_TOP) * capt, lim))
    mv = u0 - lim; VG[:, iu] = lim; VG[:, ic] += mv
    # (c) the cap (outer side, down to the pit's level): at least CAP_CL clavicle, taken from the upper arm
    F = armframe(a, s, P0); u = F["u"]
    cap = side * ss((0.32 - u["t"]) / 0.10) * ss((u["t"] + 0.12) / 0.08) * ss((90 - np.abs(u["phi"])) / 40) * ss((0.08 - u["r"]) / 0.01)
    need = np.clip(CAP_CL * cap - VG[:, ic], 0, None); take = np.minimum(need, VG[:, iu]); VG[:, iu] -= take; VG[:, ic] += take
    stat[s] = dict(trap=float(mv[trap > 0.5].mean()) if (trap > 0.5).any() else 0, ntrap=int((trap > 0.5).sum()),
                   ncap=int((capt > 0.5).sum()), capmove=float(mv[capt > 0.5].mean()) if (capt > 0.5).any() else 0, ncl=int((take > 1e-4).sum()))
print("shoulder rules", stat)
VG = VG / np.maximum(VG.sum(1, keepdims=True), 1e-9)
OUTN = os.environ.get("OUT", "wts")
np.save(J(OUTN + "_VG.npy"), VG.astype(np.float32))
np.savez(J(OUTN + ".npz"), VG=VG.astype(np.float32), own=own, names=np.array(names))
print("WTS", J(OUTN + ".npz"))
