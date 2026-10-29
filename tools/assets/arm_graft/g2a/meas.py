# G2a acceptance numbers, both sides (the left by mirrored poses). m(b) -> dict; also prints.
import numpy as np
from collections import defaultdict
from common import regions
MX = np.diag([-1., 1, 1, 1])


def prep(b):
    key = np.round(b.P / 1e-5).astype(np.int64)
    _, b.wid = np.unique(key, axis=0, return_inverse=True); b.wid = b.wid.ravel()
    Tw = b.wid[b.T]; ok = (Tw[:, 0] != Tw[:, 1]) & (Tw[:, 1] != Tw[:, 2]) & (Tw[:, 0] != Tw[:, 2]); b.Tw = Tw[ok]; b.nW = b.wid.max() + 1
    ef = defaultdict(list)
    for i, (a, c, e) in enumerate(b.Tw):
        for x, y in ((a, c), (c, e), (e, a)):
            ef[(min(x, y), max(x, y))].append(i)
    b.EP = np.array([k for k, v in ef.items() if len(v) == 2]); b.EF = np.array([ef[tuple(k)] for k in b.EP])
    t1 = b.Tw[b.EF[:, 1]]
    far = t1[:, 0].copy(); mm = (far == b.EP[:, 0]) | (far == b.EP[:, 1]); far[mm] = t1[mm, 1]
    mm = (far == b.EP[:, 0]) | (far == b.EP[:, 1]); far[mm] = t1[mm, 2]; b.far = far
    sw = []
    for i, n in enumerate(b.sk.names):
        o = n[:-2] + ("_l" if n.endswith("_r") else "_r") if n[-2:] in ("_l", "_r") else n
        sw.append(b.sk.index.get(o, i))
    b.swap = np.array(sw)
    b.rep = np.zeros(b.nW, int); b.rep[b.wid] = np.arange(len(b.wid))


def weld(b, V):
    Pw = np.zeros((b.nW, 3)); Pw[b.wid] = V; return Pw


def fn(b, Pw):
    T = b.Tw; n = np.cross(Pw[T[:, 1]] - Pw[T[:, 0]], Pw[T[:, 2]] - Pw[T[:, 0]]); a = np.linalg.norm(n, axis=1)
    return n / np.maximum(a[:, None], 1e-12), a / 2


def crease(b, Pw, n):
    c = np.degrees(np.arccos(np.clip((n[b.EF[:, 0]] * n[b.EF[:, 1]]).sum(1), -1, 1)))
    sgn = np.sign(((Pw[b.far] - Pw[b.EP[:, 0]]) * n[b.EF[:, 0]]).sum(1)); return np.where(sgn > 0, -c, c)


def mirrorG(b, G):
    R = b.rest; Ri = b.rest_inv; out = np.empty_like(G)
    for j in range(len(G)):
        out[b.swap[j]] = MX @ G[j] @ Ri[j] @ MX @ R[b.swap[j]]
    return out


def wmask(b, msk):
    w = np.zeros(b.nW, bool); w[b.wid[msk]] = True; return w


def slice_area(Pw, Tw, H, u, t, L, armw):
    o = H + u * t * L; s = (Pw - o) @ u; tm = armw[Tw].all(1); tt = Tw[tm]; ss = s[tt]; pts = []
    for k in range(3):
        a, c = tt[:, k], tt[:, (k + 1) % 3]; sa, sc = ss[:, k], ss[:, (k + 1) % 3]; x = (sa * sc < 0)
        w = sa[x] / (sa[x] - sc[x]); pts.append(Pw[a[x]] + (Pw[c[x]] - Pw[a[x]]) * w[:, None])
    p = np.concatenate(pts)
    if len(p) < 6:
        return np.nan
    d = p - o; r = np.linalg.norm(d, axis=1); p = p[r < 0.08]; d = p - o
    e1 = np.cross(u, [0, 0, 1.]); e1 /= np.linalg.norm(e1); e2 = np.cross(u, e1)
    x, y = d @ e1, d @ e2; ang = np.arctan2(y - y.mean(), x - x.mean()); o2 = np.argsort(ang); x, y = x[o2], y[o2]
    return 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1))) * 1e4


O = np.array([0, 1.9285036, 25.80094]); CX = np.array([1, 0, 0.]); CY = np.array([0, 0.9986295, -0.05233624]); CZ = np.array([0, 0.05233624, 0.9986295])
FPX = 540 / np.tan(np.radians(12))


def project(V):
    Vw = V * 1.04 + [0, 0.182, 23.0]; d = Vw - O; z = -(d @ CZ); return Vw, FPX * (d @ CX) / z + 960, 540 - FPX * (d @ CY) / z


def silhouette(b, Pw, n, mask, mirror):
    V = Pw * [-1, 1, 1] if mirror else Pw
    nn = -(n * [-1, 1, 1]) if mirror else n
    Vw, sx, sy = project(V); T = b.Tw; cen = (Vw[T[:, 0]] + Vw[T[:, 1]] + Vw[T[:, 2]]) / 3; front = ((O - cen) * nn).sum(1) > 0
    sil = front[b.EF[:, 0]] != front[b.EF[:, 1]]; k = sil & mask[b.EP].all(1); e = b.EP[k]
    ff = np.where(front[b.EF[k, 0]], b.EF[k, 0], b.EF[k, 1])
    if len(e) < 3:
        return None
    S = np.c_[sx, -sy]
    L = np.linalg.norm(S[e[:, 0]] - S[e[:, 1]], axis=1)
    adj = defaultdict(list)
    for i, (p, q) in enumerate(e):
        adj[p].append(i); adj[q].append(i)
    turns = []
    for v, l in adj.items():
        if len(l) == 2:
            i, j = l; a = e[i][0] if e[i][1] == v else e[i][1]; c = e[j][0] if e[j][1] == v else e[j][1]
            v1 = S[v] - S[a]; v2 = S[c] - S[v]
            if np.linalg.norm(v1) > 0.5 and np.linalg.norm(v2) > 0.5:
                turns.append(np.degrees(np.arccos(np.clip(v1 @ v2 / np.linalg.norm(v1) / np.linalg.norm(v2), -1, 1))))
    turns = np.array(turns) if turns else np.zeros(1)
    cs = (S[T[ff, 0]] + S[T[ff, 1]] + S[T[ff, 2]]) / 3
    def cr2(a, c):
        return a[0] * c[1] - a[1] * c[0]
    oe = [(p, q) if cr2(S[q] - S[p], c - S[p]) > 0 else (q, p) for (p, q), c in zip(e, cs)]
    nxt = {p: q for p, q in oe}; prv = {q: p for p, q in oe}
    seen = set(); chains = []
    for p, q in oe:
        if p in seen:
            continue
        s = p; guard = 0
        while s in prv and prv[s] != p and guard < 10000:
            s = prv[s]; guard += 1
            if s in seen:
                break
        ch = [s]; seen.add(s)
        while ch[-1] in nxt and nxt[ch[-1]] not in seen:
            ch.append(nxt[ch[-1]]); seen.add(ch[-1])
        chains.append(ch)
    ch = max(chains, key=lambda c: np.linalg.norm(np.diff(S[c], axis=0), axis=1).sum() if len(c) > 1 else 0)
    return dict(seg=np.median(L), seg90=np.percentile(L, 90), turn=np.median(turns), turn90=np.percentile(turns, 90), n=len(e), chain=S[ch], V=V[ch])


def curvature(pts, step=9.4):
    """the outline resampled every `step` px (~1 cm at the close-up); signed turn per step (deg, + convex)."""
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    if d[-1] < 3 * step:
        return None
    s = np.arange(0, d[-1], step); q = np.c_[np.interp(s, d, pts[:, 0]), np.interp(s, d, pts[:, 1])]
    v = np.diff(q, axis=0); a = np.degrees(np.arctan2(v[:, 1], v[:, 0])); tr = (np.diff(a) + 180) % 360 - 180
    return dict(q=q, len_cm=d[-1] / 9.4, total=tr.sum(), turns=tr, min=tr.min(), flat=np.mean(np.abs(tr) < 1.0), conc=np.mean(tr < -0.5))


def m(b, tag="", verbose=True, curv_print=False):
    if not hasattr(b, "Tw"):
        prep(b)
    I = b.sk.index; out = {}
    Pr = weld(b, b.P); nr, ar = fn(b, Pr); cr0 = crease(b, Pr, nr)
    if not hasattr(b, "_cl"):
        b._cl = {k: b.clip(k) for k in ("idle_reaver_town", "reaver_show", "flask_drink", "catch_breath")}
    cl = b._cl

    def Aof(G, s):
        H = G[I[f"upperarm_{s}"]][:3, 3]; Eb = G[I[f"lowerarm_{s}"]][:3, 3]; u = (Eb - H) / np.linalg.norm(Eb - H)
        ax = G[I["neck_01"]][:3, 3] - G[I["pelvis"]][:3, 3]; ax /= np.linalg.norm(ax); return np.degrees(np.arccos(u @ -ax))
    f58 = min(range(0, 25), key=lambda f: abs(Aof(b.globals(cl["reaver_show"], f), "r") - 58))
    # (clip, frame, the arm it is authored for)
    poses = {"idle": (cl["idle_reaver_town"], 0, None), "A58": (cl["reaver_show"], f58, "r"), "A82": (cl["reaver_show"], 24, "r"),
             "flask": (cl["flask_drink"], 126, "r"), "catch": (cl["catch_breath"], 97, "l")}
    lines = []
    for s in "rl":
        reg, info = regions(b, s)
        armw = wmask(b, (b.piece == "Heroine") & (info["rad"] < 0.075) & (info["t"] > -0.05) & ((b.P[:, 0] < 0) if s == "r" else (b.P[:, 0] > 0)))
        pit = wmask(b, reg["pit"]); em = pit[b.EP].all(1); ie = wmask(b, reg["inner_elbow"]); tie = ie[b.Tw].all(1)
        r = dict(pit_rest=-cr0[em].min())
        for pn, (clip, f, arm) in poses.items():
            G = b.globals(clip, f)
            mir = arm is not None and arm != s
            if mir:
                G = mirrorG(b, G)
            Pw = weld(b, b.pose(G)); n, a = fn(b, Pw); cr = crease(b, Pw, n)
            H = G[I[f"upperarm_{s}"]][:3, 3]; Eb = G[I[f"lowerarm_{s}"]][:3, 3]; u = (Eb - H) / np.linalg.norm(Eb - H)
            r[pn + "_sec"] = [slice_area(Pw, b.Tw, H, u, t, info["L"], armw) / slice_area(Pr, b.Tw, info["H"], info["u"], t, info["L"], armw) for t in (0.15, 0.3, 0.5)]
            r[pn + "_A"] = Aof(G, s)
            Hd = G[I[f"hand_{s}"]][:3, 3]; r[pn + "_bend"] = np.degrees(np.arccos(np.clip(u @ ((Hd - Eb) / np.linalg.norm(Hd - Eb)), -1, 1)))
            r[pn + "_pitcr"] = -cr[em].min(); r[pn + "_pit30"] = int((cr[em] < -30).sum())
            ratio = a[tie] / np.maximum(ar[tie], 1e-12); r[pn + "_elb"] = np.mean(ratio < 0.5)
            if pn == "A82":
                for rn in ("deltoid", "shoulder_top", "bicep", "pit"):
                    r["sil_" + rn] = silhouette(b, Pw, n, wmask(b, reg[rn]), mir)
                sl = silhouette(b, Pw, n, wmask(b, reg["shoulder_top"] | reg["deltoid"]), mir)
                r["curv"] = curvature(sl["chain"]) if sl else None; r["curv_chain"] = sl
                r["A82_P"] = Pw
                r["top"] = outline_top(b, Pw, G, s, mir, show=getattr(b, "_show", None) and b._show % s)
                t_ = r["top"]
                if t_ and "wv" in t_:
                    # g2c: the window's end crosses onto the arm's front (phi > 65 past t 0.1): the top outline ends there
                    tt, pp = info["t"][b.rep[t_["wv"]]], np.abs(info["phi"][b.rep[t_["wv"]]])
                    cut = np.nonzero((tt > 0.1) & (pp > 65))[0]; k = cut[0] if len(cut) else len(tt)
                    t_["turns_top"] = list(t_["turns"][:k]); t_["min_top"] = float(np.min(t_["turns"][:k])) if k else 0.0
            if pn == "idle":
                r["idle_P"] = Pw
        out[s] = r
        if verbose:
            c = r["curv"]
            lines.append(f"{tag} [{s}] pit rest {r['pit_rest']:.0f} | A82 pit>30 {r['A82_pit30']} cr {r['A82_pitcr']:.0f} | flask pit {r['flask_pitcr']:.0f} (A{r['flask_A']:.0f}) | catch pit {r['catch_pitcr']:.0f}"
                         f" | elbow<0.5 A82 {r['A82_elb']:.0%} (bend {r['A82_bend']:.0f}) flask {r['flask_elb']:.0%} ({r['flask_bend']:.0f}) catch {r['catch_elb']:.0%} ({r['catch_bend']:.0f})")
            lines.append("      sec idle " + "/".join(f"{x:.2f}" for x in r["idle_sec"]) + "  A58 " + "/".join(f"{x:.2f}" for x in r["A58_sec"]) + f"(A{r['A58_A']:.0f})  A82 " + "/".join(f"{x:.2f}" for x in r["A82_sec"])
                         + "  | sil " + " ".join(f"{k[4:]} {v['seg']:.1f}/{v['seg90']:.1f}px {v['turn']:.0f}/{v['turn90']:.0f}d" for k, v in r.items() if k.startswith("sil_") and v)
                         + (f" | curv {c['len_cm']:.1f}cm total {c['total']:.0f}d min {c['min']:.1f} flat {c['flat']:.0%} concave {c['conc']:.0%}" if c else " | curv -"))
            t_ = r["top"]
            if t_:
                lines.append(f"      top outline {t_['len_cm']:.1f}cm total {t_['total']:.0f}d min {t_['min']:.1f} d/cm, flat {t_['flat']:.0%}, longest flat run {t_['flat_run']}cm, concave {t_['conc']:.0%}: " + " ".join(f"{x:.0f}" for x in t_["turns"]))
                if "turns_top" in t_:
                    lines.append(f"      top outline on the shoulder (to phi 65): min {t_['min_top']:.1f} d/cm, {len(t_['turns_top'])} of {len(t_['turns'])} samples")
                lines.append("        at t,phi " + " ".join(f"{info['t'][b.rep[v]]:.2f},{info['phi'][b.rep[v]]:.0f}" for v in t_["wv"]))
            if curv_print and c:
                lines.append("      turns/cm " + " ".join(f"{x:.0f}" for x in c["turns"]))
    if verbose:
        print("\n".join(lines))
    return out


def outline_top(b, Pw, G, s, mirror, ss=4, show=None):
    """The upper outline at the close-up from the trap over the deltoid to the upper arm (raster, ss x supersampled):
    curvature per cm (deg, + convex) along it."""
    from PIL import Image, ImageDraw
    I = b.sk.index
    V = Pw * [-1, 1, 1] if mirror else Pw
    _, sx, sy = project(V)
    jp = lambda n: project((G[I[n]][:3, 3] * ([-1, 1, 1] if mirror else 1))[None])
    _, nx, ny = jp("neck_01"); _, ux, uy = jp(f"upperarm_{'l' if (mirror and s == 'r') or (not mirror and s == 'l') else 'r'}" if False else f"upperarm_{s}")
    _, lx, ly = jp(f"lowerarm_{s}")
    x0 = float(nx[0] + (ux[0] - nx[0]) * 0.45); x1 = float(ux[0] + (lx[0] - ux[0]) * 0.40)
    lo, hi = min(x0, x1) - 5, max(x0, x1) + 5; ytop = min(ny[0], uy[0]) - 260; ybot = max(ny[0], uy[0]) + 60
    T = b.Tw; tx = sx[T]; ty = sy[T]
    hb = np.zeros(b.nW, bool); hb[b.wid[b.piece == 'Heroine']] = True
    keep = hb[T].all(1) & (tx.max(1) > lo) & (tx.min(1) < hi) & (ty.max(1) > ytop) & (ty.min(1) < ybot)
    W_, H_ = int((hi - lo) * ss) + 1, int((ybot - ytop) * ss) + 1
    im = Image.new("L", (W_, H_), 0); dr = ImageDraw.Draw(im)
    for a, c in zip(tx[keep], ty[keep]):
        dr.polygon([((a[k] - lo) * ss, (c[k] - ytop) * ss) for k in range(3)], fill=255)
    M = np.array(im) > 127
    if show:
        im.save(show)
    cols = np.arange(int((min(x0, x1) - lo) * ss), int((max(x0, x1) - lo) * ss))
    top = np.array([np.argmax(M[:, c]) if M[:, c].any() else -1 for c in cols], float)
    ok = top >= 0
    xs = cols[ok] / ss + lo; ys = -(top[ok] / ss + ytop)   # y up
    if x1 < x0:
        xs, ys = xs[::-1], ys[::-1]
    # (the curve walked from the trap toward the arm; convex = turning clockwise there, as the outline bends down over the cap)
    pts = np.c_[xs, ys]
    k = 9
    pts = np.c_[np.convolve(pts[:, 0], np.ones(k) / k, "valid"), np.convolve(pts[:, 1], np.ones(k) / k, "valid")]
    c = curvature(pts)
    if c:
        from scipy.spatial import cKDTree
        hv = np.nonzero(hb)[0]
        d_, k_ = cKDTree(np.c_[sx[hv], -sy[hv]]).query(c["q"][1:-1])
        c["wv"] = hv[k_]
        # the longest run (cm) turning less than 1.5 deg per cm
        run = best = 0
        for t in c["turns"]:
            run = run + 1 if abs(t) < 1.5 else 0; best = max(best, run)
        c["flat_run"] = best
        c["pts"] = pts
    return c
