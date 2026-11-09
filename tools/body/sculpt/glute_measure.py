# Glute + hourglass numbers for a spec (formview stages 1-2, close tier, rest A-pose; formrules "glutes").
# python tools/body/sculpt/glute_measure.py SPEC[,SPEC..] [--json OUT]
import sys, os, json, math
import numpy as np
WT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, WT + "/tools/body")
import formview as fv, ray, topo_check as tc
from scipy.spatial import ConvexHull

LM = json.load(open(WT + "/tools/body/base/landmarks.json"))["tiers"]
K_HIP = json.dumps({"cube": "joint-l-upper-leg"}, separators=(",", ":"))
K_PEL = json.dumps({"cube": "joint-pelvis"}, separators=(",", ":"))


def lm(V, key, tier="close"):
    e = LM[tier][key]
    return (V[e["ids"]] * np.asarray(e["w"], float)[:, None]).sum(0)


class FakeSk:
    def __init__(self, J):
        self.names = list(J)
        self.rest = np.stack([np.block([[np.eye(3), np.asarray(J[n], float)[:, None]], [np.zeros((1, 3)), np.ones((1, 1))]]) for n in self.names])


def tris(Q, qm):
    Qs = Q[qm]
    return np.concatenate([Qs[:, [0, 1, 2]], Qs[:, [0, 2, 3]]])


def cast(s, org, d):
    pid, tf = ray.hits(s, org, np.broadcast_to(np.asarray(d, float), org.shape).copy())
    return np.where(pid >= 0, tf, np.nan)


def section(V, T, y):
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    pts = []
    for p, q in ((a, b), (b, c), (c, a)):
        dp, dq = p[:, 1] - y, q[:, 1] - y
        m = (dp * dq) < 0
        t = dp[m] / (dp[m] - dq[m])
        pts.append(p[m] + t[:, None] * (q[m] - p[m]))
    P = np.concatenate(pts)
    return P[:, [0, 2]]


def hull_dev(yv, bv):
    pts = np.stack([yv, bv], 1)
    h = ConvexHull(np.concatenate([pts, [[yv[0], bv.min() - 1], [yv[-1], bv.min() - 1]]]))
    hv = pts[[i for i in h.vertices if i < len(pts)]]
    hv = hv[np.argsort(hv[:, 0])]
    hb = np.interp(yv, hv[:, 0], hv[:, 1])
    return hb - bv


def fin(a):
    return [None if not np.isfinite(v) else round(float(v), 5) for v in a]


def measure(spec, V=None, z=None, skel_glb=None):
    if V is None:
        V, T, H, HT, z, rep = fv.body(spec)
    Q, parts = z["Q"], [str(p) for p in z["parts"]]
    qp = z["qpart"]
    noarm = ~np.isin(qp, [parts.index(p) for p in ("arm", "elbow", "forearm", "hand")])
    Tb = tris(Q, noarm)
    Tall = tris(Q, np.ones(len(Q), bool))
    s = ray.scene(V, Tb)
    hipL = lm(V, K_HIP)
    pel = lm(V, K_PEL)
    out = {"hip_joint_mm": [round(float(x) * 1e3) for x in hipL]}
    xs = np.arange(0.0, 0.20, 0.002)
    ys = np.arange(0.70, 1.36, 0.002)
    X, Y = np.meshgrid(xs, ys)
    org = np.stack([X.ravel(), Y.ravel(), np.full(X.size, -1.0)], 1)
    zb = (-1.0 + cast(s, org, [0, 0, 1])).reshape(X.shape)
    band = (Y > hipL[1] - 0.20) & (Y < hipL[1] + 0.12) & (X > 0.02) & (X < 0.16)
    zz = np.where(band & np.isfinite(zb), zb, np.inf)
    i, j = np.unravel_index(np.argmin(zz), zz.shape)
    xa = xs[j]
    out["apex_x_mm"] = round(xa * 1e3)
    prof = zb[:, j]
    ya, za = ys[i], prof[i]
    out["apex_y_mm"], out["apex_z_mm"] = round(ya * 1e3), round(za * 1e3)
    out["apex_minus_hip_mm"] = round((ya - hipL[1]) * 1e3)
    up = (ys > ya + 0.04) & (ys < ya + 0.30) & np.isfinite(prof)
    k = np.argmax(np.where(up, prof, -np.inf))
    out["lumbar_y_mm"], out["proj_back_mm"] = round(ys[k] * 1e3), round((prof[k] - za) * 1e3, 1)
    yt = hipL[1] - 0.18
    out["proj_thigh_mm"] = round((np.interp(yt, ys, prof) - za) * 1e3, 1)
    sil = np.nanmin(np.where(np.isfinite(zb), zb, np.nan), 1)
    ia = np.argmin(np.where((ys > hipL[1] - 0.2) & (ys < hipL[1] + 0.12) & np.isfinite(sil), sil, np.inf))
    k2 = np.argmax(np.where((ys > ys[ia] + 0.04) & (ys < ys[ia] + 0.30) & np.isfinite(sil), sil, -np.inf))
    out["sil_apex_y_mm"], out["sil_proj_back_mm"] = round(ys[ia] * 1e3), round((sil[k2] - sil[ia]) * 1e3, 1)
    lo = (ys >= hipL[1] - 0.30) & (ys <= ya) & np.isfinite(prof)
    d = hull_dev(ys[lo], -prof[lo])
    kd = np.argmax(d)
    out["fold_depth_mm"], out["fold_y_mm"] = round(float(d[kd]) * 1e3, 1), round(float(ys[lo][kd]) * 1e3)
    b = -prof[lo]
    yy = ys[lo]
    bs = np.convolve(np.pad(b, 1, mode="edge"), np.ones(3) / 3, "valid")
    b1 = np.gradient(bs, yy)
    b2 = np.gradient(b1, yy)
    kap = b2 / (1 + b1 ** 2) ** 1.5
    out["fold_min_radius_mm"] = round(1e3 / max(float(kap.max()), 1e-6), 1)
    zmid = zb[:, 0]
    out["cleft_depth_at_apex_mm"] = round((zmid[i] - za) * 1e3, 1)
    yw = np.arange(0.75, 1.36, 0.002)
    xw = np.arange(-0.30, 0.30, 0.0015)
    XW, YW = np.meshgrid(xw, yw)
    orgf = np.stack([XW.ravel(), YW.ravel(), np.full(XW.size, 1.0)], 1)
    hitf = np.isfinite(cast(s, orgf, [0, 0, -1])).reshape(XW.shape)
    width = np.array([(xw[r].max() - xw[r].min()) if r.any() else np.nan for r in hitf])
    zs = np.arange(-0.30, 0.30, 0.0015)
    YS, ZS = np.meshgrid(yw, zs, indexing="ij")
    orgs = np.stack([np.full(YS.size, -1.0), YS.ravel(), ZS.ravel()], 1)
    hits = np.isfinite(cast(s, orgs, [1, 0, 0])).reshape(YS.shape)
    depth = np.array([(zs[r].max() - zs[r].min()) if r.any() else np.nan for r in hits])
    wb = (yw > 1.08) & (yw < 1.34)
    iw = np.argmin(np.where(wb & np.isfinite(width), width, np.inf))
    hb = (yw > 0.86) & (yw < 1.12)
    ih = np.argmax(np.where(hb & np.isfinite(width), width, -np.inf))

    def circ(y):
        P = section(V, Tb, y)
        P = P[np.abs(P[:, 0]) < 0.30]
        return ConvexHull(P).area
    cs = [(circ(y), y) for y in np.arange(1.10, 1.32, 0.01)]
    cmin = min(cs)
    chs = [(circ(y), y) for y in np.arange(0.92, 1.10, 0.01)]
    cmax = max(chs)
    out.update({"waist_y_mm": round(yw[iw] * 1e3), "waist_w_mm": round(width[iw] * 1e3), "waist_d_mm": round(depth[iw] * 1e3),
                "waist_circmin_y_mm": round(cmin[1] * 1e3), "waist_circ_mm": round(cmin[0] * 1e3),
                "hip_y_mm": round(yw[ih] * 1e3), "hip_w_mm": round(width[ih] * 1e3), "hip_d_mm": round(depth[ih] * 1e3),
                "hip_circmax_y_mm": round(cmax[1] * 1e3), "hip_circ_mm": round(cmax[0] * 1e3),
                "whr_w": round(width[iw] / width[ih], 3), "whr_circ": round(cmin[0] / cmax[0], 3)})
    out["hip_widest_vs_joint_mm"] = round(out["hip_y_mm"] - out["hip_joint_mm"][1])
    below = (yw <= yw[ih]) & np.isfinite(width)
    wd = width[below][::-1] * 1e3  # from the widest-hip height downward
    out["saddle_mm"] = round(float(np.max(wd - np.minimum.accumulate(wd))), 1) if len(wd) else 0.0
    out["w_at_hipjoint_mm"] = round(float(np.interp(hipL[1], yw, width)) * 1e3)
    orgn = np.stack([np.zeros(len(yw)), yw, np.full(len(yw), 1.0)], 1)
    zf = 1.0 - cast(s, orgn, [0, 0, -1])
    m = (yw > 0.98) & (yw < 1.22) & np.isfinite(zf)
    sm = np.convolve(np.pad(zf, 15, mode="edge"), np.ones(31) / 31, "valid")
    kn = np.argmin(np.where(m, zf - sm, np.inf))
    out["navel_y_mm"] = round(yw[kn] * 1e3)
    from gl import Glb
    sk = Glb(skel_glb or WT + "/tools/body/out/her_r1/body.glb").skeleton()
    sk.rest = sk.rest.copy()
    sk.rest[sk.names.index("pelvis")][:3, 3] = pel
    sk.rest[sk.names.index("thigh_l")][:3, 3] = hipL
    t = tc.measure(V, z, sk)
    out["fold_over_60"], out["aspect_over_4"], out["edges_under_2mm"] = t["fold_over_60"], t["aspect_over_4"], t["edges_under_2mm"]
    out["cleft_floor"] = t["floors"]["gluteal_cleft"]
    out["cleft_floor_over_60"] = t["floors"]["gluteal_cleft"]["over_60"]
    out["cleft_floor_max_deg"] = t["floors"]["gluteal_cleft"]["max_deg"]
    out["cleavage_floor_over60"] = t["floors"]["cleavage"]["over_60"] if "cleavage" in t["floors"] else None
    out["fold_below_hip_mm"] = round(out["hip_joint_mm"][1] - out["fold_y_mm"])
    out["waist_over_pelvis_mm"] = round(out["waist_y_mm"] - pel[1] * 1e3)
    # P1 R1 round 9 (the butt from behind): the numbers that say two round lobes and a long soft cleft, on the back's
    # own height map (2 mm grid, zb). cleft_narrow_mm: how far the midline sits forward of the column 26 mm out (a
    # wide shallow V doesn't read as a cleft, a narrow one does); the cleft's top is where that falls under 8 mm going
    # up from the apex; the lobe runs from the under-fold to the small of the back
    j26 = int(round(0.026 / 0.002))
    nar = (zmid - zb[:, j26]) * 1e3
    top = i
    while top + 1 < len(ys) and np.isfinite(nar[top + 1]) and nar[top + 1] >= 8.0:
        top += 1
    out["cleft_top_over_hip_mm"] = round((ys[top] - hipL[1]) * 1e3)
    out["cleft_over_lobe"] = round(float((ys[top] - out["fold_y_mm"] / 1e3) / (out["lumbar_y_mm"] / 1e3 - out["fold_y_mm"] / 1e3)), 3)
    imid = int(np.argmin(np.abs(ys - (hipL[1] + 0.06))))
    out["cleft_narrow_at_60_mm"] = round(float(nar[imid]), 1)
    # the low back's turn at the crest's column: the height span over which the slope falls from 75% to 25% of its
    # steepest on the way up to the small of the back (a short span is the straight edge the judge saw from behind)
    def turn(jc):
        pr = np.array([np.nan if not np.isfinite(v) else v for v in zb[:, jc]])
        k1 = (ys > hipL[1] + 0.05) & (ys < hipL[1] + 0.30) & np.isfinite(pr)
        yy, zz2 = ys[k1], np.convolve(np.pad(pr[k1], 5, mode="edge"), np.ones(11) / 11, "valid")
        sl = np.gradient(zz2, yy)
        ks = int(np.argmax(sl))
        hi = next((q for q in range(ks, len(sl)) if sl[q] <= 0.25 * sl[ks]), len(sl) - 1)
        lo = next((q for q in range(ks, len(sl)) if sl[q] <= 0.75 * sl[ks]), ks)
        return (yy[hi] - yy[lo]) * 1e3, (yy[lo] + yy[hi]) / 2 * 1e3
    tb = [turn(int(round(xc / 0.002))) for xc in (0.03, 0.06, 0.09, 0.12)]
    out["low_back_blend_mm"] = round(min(t0[0] for t0 in tb[:3]), 1)
    out["low_back_line_drop_mm"] = round(tb[0][1] - tb[3][1], 1)
    # the under-curve toward the outer hip: how much higher the fold sits at |x| 120 than at |x| 60 (a smile with no lift
    # reads as one slab over a crease)
    def fold_at(xc):
        pr = zb[:, int(round(xc / 0.002))]
        k1 = (ys >= hipL[1] - 0.30) & (ys <= ya) & np.isfinite(pr)
        dd = hull_dev(ys[k1], -pr[k1])
        return ys[k1][int(np.argmax(dd))] * 1e3, float(dd.max()) * 1e3
    f60, f120 = fold_at(0.06), fold_at(0.12)
    out["fold_outer_lift_mm"] = round(f120[0] - f60[0], 1)
    out["fold_outer_depth_mm"] = round(f120[1], 1)
    # mid-band relief across the cheek: what the eye reads as vertical ripples (the Gaussian band 4-16 mm in x, the
    # lobes' columns |x| 25-140 mm, apex-60 to apex+90 mm, on the 2 mm grid)
    from scipy.ndimage import gaussian_filter1d
    xok = (xs >= 0.0) & (xs < 0.17)
    band2 = (ys > ya - 0.06) & (ys < ya + 0.09)
    Zb = np.where(np.isfinite(zb), zb, -0.03)[np.ix_(band2, xok)]
    Zf = np.concatenate([Zb[:, ::-1], Zb], 1)
    hp = gaussian_filter1d(Zf, 2.0, axis=1) - gaussian_filter1d(Zf, 8.0, axis=1)
    hp = hp[:, Zb.shape[1]:]
    xk = (xs[xok] >= 0.05) & (xs[xok] <= 0.11)
    # the second x-derivative of a smooth lobe is not a ripple: take off a cubic in x per row
    resid = []
    for r0, r1 in zip(Zb, hp):
        c0 = np.polyfit(xs[xok][xk], r1[xk], 3)
        resid.append(r1[xk] - np.polyval(c0, xs[xok][xk]))
    out["cheek_ripple_mm"] = round(float(np.abs(np.array(resid)).max()) * 1e3, 2)
    sa = ray.scene(V, Tall)
    reg = (V[:, 1] > 0.75) & (V[:, 1] < 1.30) & (V[:, 2] < 0.0) & (np.abs(V[:, 0]) < 0.22)
    Nv = fv.vnormals(V, Tall)
    out["inside_glute_region"] = int(ray.inside(sa, V[reg] + 3e-4 * Nv[reg]).sum())
    out["inside_glute_region_in"] = int(ray.inside(sa, V[reg] - 3e-4 * Nv[reg]).sum())
    out["_prof"] = {"x": float(xa), "ys": ys.tolist(), "z": fin(prof), "sil": fin(sil), "mid": fin(zmid)}
    out["_w"] = {"y": yw.tolist(), "w": fin(width), "d": fin(depth), "zf": fin(zf)}
    return out


if __name__ == "__main__":
    res = {}
    for sp in sys.argv[1].split(","):
        r = measure(sp)
        res[os.path.basename(sp)] = r
        print(os.path.basename(sp), json.dumps({k: v for k, v in r.items() if not k.startswith("_")}))
    if "--json" in sys.argv:
        json.dump(res, open(sys.argv[sys.argv.index("--json") + 1], "w"))
