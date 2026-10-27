# Body 2 A step 3: the RIGHT arm's shape (the left is mirrored from it by mirror_a.py) and both shoulder tops.
#   python shape_a.py <work dir> <start P.npy> <out P.npy>       (Z up, front -Y, metres; dump order of ar.npz)
# 1. Shoulder top (each side, its own contour): the top line from the side neck point (x NSP_X) to the acromion made
#    straight (no dent at x 12 cm) with the acromion LOWER_CM lower; the move fades to 0 at the NSP and with depth under
#    the ridge (full to 1.5 cm, none by 6 cm), and down the cap's outside.
# 2. Right arm sections: per station an affine scale in the section plane about the bone (top = front-view width,
#    front = side-view depth) to the target table (d_c's front/side widths, S 1654), applied to the low-pass surface
#    (Taubin) with the relief (the residual) added back unscaled; upper/forearm fields blended across the elbow plane.
#    AMT scales every change (1 = the targets).
# 3. Authored form along the normal: deltoid (cap to the V at t .46, standing ~10 mm proud in front), triceps long
#    head (+4 mm over the chord at t .40, back), collarbone ridge with the hollows above and below.
# Only graft-owned vertices of the arm move in 2-3 (the torso ring and the hand ring stay); 1 moves kept skin too.
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from lib import load, fan, edges, adjacency, armframe, joints, ss, bump, vnormals
import scipy.sparse as sp
WK, PIN, POUT = sys.argv[1:4]; J = lambda f: os.path.join(WK, f)
E_ = lambda k, d: float(os.environ.get(k, d))
AMT = E_("AMT", "1"); LOWER = E_("LOWER_CM", "1.0") / 100; NSP_X = E_("NSP_X", "0.08")
a = load(J("ar.npz")); P0 = np.load(PIN).astype(float); P = P0.copy(); W8 = np.load(J("wts.npz")); VG = W8["VG"].astype(float); own = W8["own"]
names = a["names"]; ix = {n: i for i, n in enumerate(names)}
T, _, _ = fan(a["ls"], a["lt"], a["lv"]); E = edges(a["ls"], a["lt"], a["lv"]); A = adjacency(len(P), E)
deg = np.asarray(A.sum(1)).ravel(); Wn = sp.diags(1 / np.maximum(deg, 1)) @ A
log = []

# ---------------- 1. shoulder tops
def acromion(s, X):
    j = joints(a, s); sg = -1 if s == "r" else 1
    col = (np.abs(X[:, 0] - j["A"][0]) < 0.01) & (np.abs(X[:, 1] - j["A"][1]) < 0.025) & (np.sign(X[:, 0]) == sg)
    k = np.where(col)[0][np.argmax(X[col, 2])]; return X[k].copy()
def contour(X, sg, xs, ymid, half=0.05):
    """top line in front view: max z per x bin (|y - ymid| < half)"""
    x = X[:, 0] * sg; out = []
    for x0 in xs:
        m = (np.abs(x - x0) < 0.004) & (np.abs(X[:, 1] - ymid) < half) & (X[:, 2] > 1.2)
        out.append(X[m, 2].max() if m.any() else np.nan)
    return np.array(out)
for s in "rl":
    sg = -1 if s == "r" else 1; j = joints(a, s); ac = acromion(s, P); xa = ac[0] * sg
    xs = np.arange(NSP_X, xa + 1e-4, 0.005); zc = contour(P, sg, xs, ac[1])
    # the line lowered by LOWER at the acromion, ramping from 0 at the NSP, then made smooth (a cubic through it: the
    # dent at x 12 filled, the trap's own concave fall from the neck kept; a straight NSP-acromion line would RAISE the
    # inner trap 8-11 mm and bulk it)
    ramp = ss((xs - xs[0]) / (xs[-1] - xs[0]))
    tgt = zc - LOWER * AMT * ramp; c3 = np.polyfit(xs - xs[0], tgt, 3); lin = np.polyval(c3, xs - xs[0])
    lin[0] = zc[0]; lin = np.minimum(lin, np.maximum(zc, tgt + 0.0))
    dz_x = lin - zc                                  # per x: wanted move of the ridge
    x = P[:, 0] * sg
    dzx = np.interp(x, xs, dz_x, left=0, right=dz_x[-1])
    zr = np.interp(x, xs, zc, left=np.nan, right=zc[-1])
    depth = zr - P[:, 2]                             # under the ridge
    wd = 1 - ss((depth - 0.015) / 0.045)
    # past the acromion: down the cap's outside the drop fades with height under the acromion (none 6 cm under)
    wo = np.where(x > xa, 1 - ss(((ac[2] - P[:, 2]) - 0.01) / 0.05), 1.0)
    wn = ss((x - NSP_X) / 0.02)                      # nothing at the NSP, full 2 cm out
    wy = 1 - ss((np.abs(P[:, 1] - ac[1]) - 0.06) / 0.04)
    side = np.sign(P[:, 0]) == sg
    dz = np.where(side & np.isfinite(zr), dzx * wd * wo * wn * wy, 0)
    dz = np.where(np.abs(dz) > 1e-6, dz, 0)
    P[:, 2] += dz
    log.append("shoulder %s: acromion x %.1f cm; ridge move mm (x 8..) %s; max raise %.1f mm at x %.1f cm; moved %d (kept %d)" % (
        s, xa * 100, " ".join("%.1f" % v for v in dz_x[::2] * 1e3), dz_x.max() * 1e3, xs[np.argmax(dz_x)] * 100, int((np.abs(dz) > 1e-4).sum()), int(((np.abs(dz) > 1e-4) & ~own).sum())))

# ---------------- 2. right arm sections
s = "r"; F = armframe(a, s, P); u, f = F["u"], F["f"]; side = F["side"]
arm = VG[:, [ix["upperarm_r"], ix["lowerarm_r"], ix["hand_r"]]].sum(1)
# low-pass surface (Taubin, 20 it) for the scaled part; the residual (her relief) is added back unscaled
Ps = P.copy()
for _ in range(20):
    Ps = Ps + 0.5 * (Wn @ Ps - Ps); Ps = Ps - 0.53 * (Wn @ Ps - Ps)
def widths(g, t, sel):
    m = sel & (np.abs(g["t"] - t) * g["L"] < 0.006) & (g["r"] < 0.08)
    d = Ps[m] - g["o"]; x = d @ g["top"]; y = d @ g["fr"]
    return x.max() - x.min(), y.max() - y.min()
sel = side & (arm > 0.5)
# targets (mm): top width (front view), front-back depth (side view)
TU = [(0.30, None, None), (0.46, 79, 87), (0.55, 78, 86), (0.65, 77, 84), (0.75, 75, 80), (0.85, 72, 74), (0.95, 70, 69)]
TF = [(0.0, 69, 67), (0.05, 71, 67), (0.15, 77, 69), (0.25, 76, 69), (0.40, 70, 66), (0.50, 64, 64), (0.60, 57, 62), (0.75, 49, 59),
      (0.85, 46, 58), (0.90, 44, 58), (0.95, 47, 60), (0.98, None, None)]
# (the wrist: the hand ring is 50 thick x 62 at tf .98 and stays; 42 x 57 at .9 would pinch a waist above the hand: 44 x 58)
def kfield(g, tab):
    ts = []; kt = []; kf = []
    for t, wt, wf in tab:
        cw, cf = widths(g, max(t, 0.02) if g is f else min(t, 0.97), sel)
        ts.append(t); kt.append(1.0 if wt is None else wt / 1e3 / cw); kf.append(1.0 if wf is None else wf / 1e3 / cf)
        log.append("  %s%.2f now %.0f x %.0f -> k %.3f %.3f" % ("u" if g is u else "f", t, cw * 1e3, cf * 1e3, kt[-1], kf[-1]))
    return np.array(ts), np.array(kt), np.array(kf)
tu, ktu, kfu = kfield(u, TU); tf_, ktf, kff = kfield(f, TF)
def disp(g, ts, kt, kf):
    t = g["t"]; a_t = 1 + AMT * (np.interp(t, ts, kt) - 1); a_f = 1 + AMT * (np.interp(t, ts, kf) - 1)
    d = Ps - g["o"]; x = d @ g["top"]; y = d @ g["fr"]
    return np.outer((a_t - 1) * x, g["top"]) + np.outer((a_f - 1) * y, g["fr"])
Du = disp(u, tu, ktu, kfu); Df = disp(f, tf_, ktf, kff)
# the elbow plane (bisector): upper field on the shoulder side, forearm field past it, blended over 6 cm
nb = u["n"] + f["n"]; nb /= np.linalg.norm(nb); sb = (P - f["o"]) @ nb; beta = ss((sb + 0.03) / 0.06)
D = (1 - beta[:, None]) * Du + beta[:, None] * Df
# where: the right arm's graft-owned skin, upper part from t .30 (the field is 1 there), not past the hand ring
# (the graft ends at tf ~.92: her kept wrist skin from tf .6 to the hand (tf 1) takes the field too; it is 1 by tf .98)
wrist_k = (~own) & (beta > 0.5) & (f["t"] > 0.6) & (f["t"] < 1.0)
wm = side & (own | wrist_k) & (((1 - beta) * u["r"] + beta * f["r"]) < 0.10)
wm = wm & ~((f["t"] > 1.0) & (beta > 0.5))
D[~wm] = 0
P = P + D
log.append("sections: moved %d, max %.1f mm" % (int((np.linalg.norm(D, axis=1) > 1e-4).sum()), np.linalg.norm(D, axis=1).max() * 1e3))

# ---------------- 3. authored form (along the normal), right arm
N = vnormals(P, T); F = armframe(a, s, P); u, f = F["u"], F["f"]
def outline_excess(t_list):
    """lateral (top+) extent at t minus the line fit through t .55-.85 (front-view outline)"""
    ts = np.arange(0.10, 0.90, 0.025); ex = []
    for t in ts:
        m = sel & (np.abs(u["t"] - t) * u["L"] < 0.005) & (u["r"] < 0.08)
        ex.append(((P[m] - u["o"]) @ u["top"]).max())
    ex = np.array(ex); k = (ts >= 0.55) & (ts <= 0.85); c = np.polyfit(ts[k], ex[k], 1)
    return np.interp(t_list, ts, ex - np.polyval(c, ts))
# deltoid: the outline at t .25-.46 to EX_D (10 mm) proud, ending at the V (t .46 -> 0 by .56); its width round the arm
# narrows from 80 deg (half) at the cap to 25 at the V; front/back heads keep their own (window soft)
tt = np.array([0.20, 0.25, 0.30, 0.38, 0.46, 0.51, 0.56]); want = np.array([np.nan, 13, 12, 11, E_("EX_D", "10"), 5, 0])
now = outline_excess(tt); add = np.nan_to_num(np.clip(want - now * 1e3, 0, None)) / 1e3 * AMT
amp = np.interp(u["t"], tt, add, left=0, right=0)
half = np.interp(u["t"], [0.2, 0.46, 0.56], [80, 25, 18])
wphi = bump(u["phi"], 0, half)
dd = amp * wphi * (side & own & (u["r"] < 0.09) & (beta < 0.5))
P = P + N * dd[:, None]
log.append("deltoid: outline excess now %s mm, added peak %.1f mm" % (np.round(now * 1e3, 1).tolist(), dd.max() * 1e3))
# triceps long head: +TRI mm over the chord at t .40 on the back (phi -100), soft
def back_line():
    ts = np.arange(0.15, 0.90, 0.025); ex = []
    for t in ts:
        m = sel & (np.abs(u["t"] - t) * u["L"] < 0.005) & (u["r"] < 0.08)
        ex.append(-((P[m] - u["o"]) @ u["fr"]).min())
    return ts, np.array(ex)
ts, bl = back_line(); ch = np.interp(ts, [0.2, 0.85], np.interp([0.2, 0.85], ts, bl)); over = (bl - ch) * 1e3
tri_add = max(0.0, E_("TRI", "4") - float(np.interp(0.40, ts, over))) / 1e3 * AMT
dt = tri_add * bump(u["t"], 0.40, 0.22) * bump(u["phi"], -100, 60) * (side & own & (u["r"] < 0.09) & (beta < 0.5))
P = P + N * dt[:, None]
log.append("triceps: over chord at .40 was %.1f mm, added %.1f" % (np.interp(0.40, ts, over), tri_add * 1e3))
# collarbone: ridge along the clavicle (sternal end x 3 cm -> acromion end), front-top skin, both sides
for sd in "rl":
    sg = -1 if sd == "r" else 1; jc = joints(a, sd); ac = acromion(sd, P)
    p0 = np.array([0.03 * sg, jc["C"][1] - 0.02, jc["C"][2] + 0.005]); p1 = np.array([ac[0] - 0.025 * sg, ac[1] - 0.02, ac[2] - 0.02])
    ax = p1 - p0; L = np.linalg.norm(ax); ax /= L
    rel = P - p0; tl = np.clip(rel @ ax / L, 0, 1); q = p0 + np.outer(tl * L, ax); dv = P - q
    up = np.array([0, 0, 1.0]) - ax[2] * ax; up /= np.linalg.norm(up); h = dv @ up; dist = np.linalg.norm(dv - np.outer(dv @ np.array([0, -1, 0]), [0, -1, 0]) * 0, axis=1)
    front = (-N[:, 1] > 0.25) & (np.sign(P[:, 0]) == sg) & (np.abs(P[:, 1] - q[:, 1]) < 0.05)
    along = ss(((rel @ ax) / L - 0.0) / 0.15) * (1 - ss(((rel @ ax) / L - 0.85) / 0.15))
    rid = E_("CLAV", "1.6") / 1e3 * np.exp(-0.5 * (h / 0.007) ** 2) - 1.2e-3 * np.exp(-0.5 * ((h - 0.017) / 0.008) ** 2) * ss((np.abs(P[:, 0]) - 0.06) / 0.02) \
          - 0.6e-3 * np.exp(-0.5 * ((h + 0.016) / 0.008) ** 2)
    dc = rid * along * front * AMT
    P = P + N * dc[:, None]
    log.append("collarbone %s: moved %d, ridge max %.1f mm, hollow min %.1f mm" % (sd, int((np.abs(dc) > 1e-4).sum()), dc.max() * 1e3, dc.min() * 1e3))
np.save(POUT, P)
print("\n".join(log)); print("SHAPED", POUT, "max move %.1f mm" % (np.linalg.norm(P - P0, axis=1).max() * 1e3))
