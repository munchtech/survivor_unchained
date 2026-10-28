"""Body 23 r1a: in-camera measures of a candidate vs A (outline moves per asked region, Look width, knot checks) and
1:1 clay sheets. Regions are welded-vertex sets per side (rest charts), the outline pixel's triangle decides."""
import os, sys, json
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
import k
import chart as c
import harness as h
sys.path.insert(0, k.B22 + r"\shoulder")
import sh  # noqa  (clay renders)

LOOPMAP = k.B23 + r"\loops\loop_map.json"
# judged frames: (frame, side, regions asked there)
JUDGED = [("w_p45", "r", ("cap", "delt", "fold")), ("w_m45", "l", ("cap", "delt", "fold")),
          ("w_m80", "l", ("cap", "delt", "elbow", "crease")), ("s_p45", "r", ("elbow", "crease", "cap")),
          ("rL90_m45", "l", ("cap", "delt", "fold", "elbow")), ("look_f", "r", ("cap", "delt", "fold")),
          ("look_f", "l", ("cap", "elbow"))]
OTHER = [("r132_p45", "r"), ("r132_p45", "l"), ("r132_m45", "l"), ("r132_m45", "r"), ("w_p80", "l"), ("w_p80", "r")]


def _loop_ids(feat, sd):
    m = json.load(open(LOOPMAP))
    bs = k.base()
    ids = set()

    def walk(o):
        if isinstance(o, list):
            if len(o) == 2 and all(isinstance(x, int) for x in o):
                pr, v = o
                kk = bs.kidx[pr] if pr < len(bs.kidx) else None
                ids.add(int(bs.wid[bs.offs[pr] + v]))
            else:
                for x in o:
                    walk(x)
        elif isinstance(o, dict):
            for kk, x in o.items():
                if not kk.startswith("_"):
                    walk(x)
    walk(m[sd][feat])
    return np.array(sorted(ids))


_REG = {}


def regions(sd):
    """{name: bool mask over welded vertices} for one side (rest charts)"""
    if sd in _REG:
        return _REG[sd]
    bs = k.base()
    U = bs.U
    sg = 1 if sd == "l" else -1
    FU = c.rest_frame(sd, "U")
    FF = c.rest_frame(sd, "F")
    s, phi, r = c.coords(U, FU)
    s2, phi2, r2 = c.coords(U, FF)
    side = U[:, 0] * sg > 0.03
    L = FU["L"]
    out = {}
    # cap: the shoulder's top and outer cap, above ~28% of the humerus, near the joint (torso's shoulder top too)
    dj = np.linalg.norm(U - FU["O"], axis=1) * 1000
    out["cap"] = side & (dj < 95) & (s < 0.30 * L) & (s > -80) & (np.abs((phi - 90 + 180) % 360 - 180) < 125)
    out["delt"] = side & (s >= 0.30 * L) & (s < 0.66 * L) & (r < 75) & (np.abs((phi - 90 + 180) % 360 - 180) < 100)
    fold = _loop_ids("front_fold", sd)
    if len(fold):
        from scipy.spatial import cKDTree
        d, _ = cKDTree(U[fold]).query(U)
        out["fold"] = side & (d < 0.030)
    else:
        out["fold"] = np.zeros(len(U), bool)
    # elbow: +-45 mm about the elbow joint along the arm; the point (back) and crease (front)
    E = FF["O"]
    de = np.linalg.norm(U - E, axis=1) * 1000
    arm = bs.b.arm_w(sd) > 0.5
    out["elbow"] = side & arm & (de < 60) & (np.abs((phi2 - 180 + 180) % 360 - 180) < 100)
    out["crease"] = side & arm & (de < 55) & (np.abs(phi2) < 80)
    _REG[sd] = out
    return out


def view_box(fr, sd, pad=40):
    """a box round her side's arm (shoulder to wrist) on screen"""
    P = np.array([k.joint(fr, n + "_" + sd) for n in ("clavicle", "upperarm", "lowerarm", "hand")])
    q = h.project(fr.Pm, P)
    x0, y0 = q.min(0) - [110, 110]
    x1, y1 = q.max(0) + [110, 90]
    return (int(max(x0, 0)), int(max(y0, 0)), int(min(x1, 1920)), int(min(y1, 1080)))


def raster(fr, g, box):
    ids = h.raster(g["xy"], g["z"], g["I"], g["front"], box, h.SS)
    zt = g["z"][g["I"]].mean(1)
    return ids, h.edges(ids, zt)


def tri_u(fr, g):
    """per triangle of g: its 3 welded vertex ids (-1 none)"""
    d2u = fr.d2u
    return d2u[g["I"]]


def moves(fr, sd, gA, gB, regs, box=None):
    """per region: A's outline pixels (whose triangle has a region vertex) -> distance to B's outline (px, 1x),
    signed + out where B's body covers the A pixel (silhouette edges); and max/mean |move|"""
    box = box or view_box(fr, sd)
    idsA, EA = raster(fr, gA, box)
    idsB, EB = raster(fr, gB, box)
    dist = distance_transform_edt(~EB) / h.SS
    distA = distance_transform_edt(~EA) / h.SS
    TU = tri_u(fr, gA)
    R = regions(sd)
    out = {}
    yy, xx = np.nonzero(EA)
    t = idsA[yy, xx]
    covB = idsB[yy, xx] >= 0
    silA = np.zeros(len(t), bool)
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        y2, x2 = np.clip(yy + dy, 0, EA.shape[0] - 1), np.clip(xx + dx, 0, EA.shape[1] - 1)
        silA |= idsA[y2, x2] < 0
    # B's outline pixels -> A distance (the other way: B's new outline where A had none)
    yb, xb = np.nonzero(EB)
    tb = idsB[yb, xb]
    for rn in regs:
        reg = R[rn]
        inA = (TU[t] >= 0).all(1) & reg[np.maximum(TU[t], 0)].any(1)
        inB = (TU[tb] >= 0).all(1) & reg[np.maximum(TU[tb], 0)].any(1)
        if inA.sum() < 4:
            out[rn] = None
            continue
        v = dist[yy[inA], xx[inA]]
        vb = distA[yb[inB], xb[inB]] if inB.any() else np.zeros(1)
        sgn = np.where(covB[inA], 1.0, -1.0)
        sv = v[silA[inA]] * sgn[silA[inA]]
        both = np.r_[v, vb]
        out[rn] = dict(n=int(inA.sum() / h.SS), max=round(float(both.max()), 1), mean=round(float(both.mean()), 1),
                       p90=round(float(np.percentile(both, 90)), 1),
                       sil_med=round(float(np.median(sv)), 1) if len(sv) else None,
                       sil_min=round(float(sv.min()), 1) if len(sv) else None,
                       sil_max=round(float(sv.max()), 1) if len(sv) else None)
    return out, (box, idsA, EA, idsB, EB)


def look_width(gA, gB, fr):
    """Look: her shoulders' screen width (px) in a band about the shoulder joints' height, A and B"""
    q = h.project(fr.Pm, np.array([k.joint(fr, "upperarm_l"), k.joint(fr, "upperarm_r")]))
    ym = q[:, 1].mean()
    box = (int(q[:, 0].min() - 200), int(ym - 120), int(q[:, 0].max() + 200), int(ym + 80))
    res = []
    for g in (gA, gB):
        ids = h.raster(g["xy"], g["z"], g["I"], g["front"], box, h.SS)
        fg = ids >= 0
        rows = np.nonzero(fg.any(1))[0]
        w = []
        for y in range(fg.shape[0]):
            xs = np.nonzero(fg[y])[0]
            w.append((xs.max() - xs.min()) / h.SS if len(xs) else 0)
        res.append(np.array(w))
    # width at the shoulders: the max over the band from the shoulder top to 60 px below the joints
    wA, wB = res
    return round(float(wA.max()), 1), round(float(wB.max()), 1), round(float(wB.max() - wA.max()), 1)


def posed_normals(g, fr):
    X, I = g["X"], g["I"]
    Ns = np.vstack([sf["A"][:, 3:6] for sf in fr.dump["surfs"]])
    e1, e2 = X[I[:, 1]] - X[I[:, 0]], X[I[:, 2]] - X[I[:, 0]]
    n = np.cross(e1, e2)
    sgn = np.sign((n * Ns[I].sum(1)).sum(1))
    n = n * sgn[:, None]
    return n


def knots(fr, g, sd, regs=("fold", "elbow", "crease", "cap")):
    """per region (posed): the faces' dihedral angle with neighbours (deg p99, max) and folded faces vs a smoothed
    surface; a bright-nub proxy: the p99 of the posed mean curvature (1/mm) over the region"""
    bs = k.base()
    R = regions(sd)
    TU = tri_u(fr, g)
    ok = (TU >= 0).all(1)
    X = g["X"]
    n = posed_normals(g, fr)
    nn = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-15)
    # welded posed positions and faces
    Xu = np.full((bs.nU, 3), np.nan)
    Xu[fr.d2u[fr.d2u >= 0]] = X[fr.d2u >= 0]
    out = {}
    F = bs.F
    good = np.isfinite(Xu).all(1)
    Ff = F[good[F].all(1)]
    q = np.cross(Xu[Ff[:, 1]] - Xu[Ff[:, 0]], Xu[Ff[:, 2]] - Xu[Ff[:, 0]])
    area = np.linalg.norm(q, axis=1)
    fn = q / np.maximum(area[:, None], 1e-18)
    # edges -> faces
    E = np.r_[Ff[:, [0, 1]], Ff[:, [1, 2]], Ff[:, [2, 0]]]
    fi = np.r_[np.arange(len(Ff))] .repeat(1)
    fi = np.r_[np.arange(len(Ff)), np.arange(len(Ff)), np.arange(len(Ff))]
    key = np.sort(E, 1)
    kk = key[:, 0].astype(np.int64) * 10_000_000 + key[:, 1]
    o = np.argsort(kk)
    kk, fi2 = kk[o], fi[o]
    same = kk[1:] == kk[:-1]
    fa, fb = fi2[:-1][same], fi2[1:][same]
    dih = np.degrees(np.arccos(np.clip((fn[fa] * fn[fb]).sum(1), -1, 1)))
    # mean curvature proxy at vertices: |lap(X) . n| / (mean edge^2) in 1/mm
    Xg = np.where(good[:, None], Xu, 0)
    Nv = np.zeros_like(Xg)
    for j in range(3):
        np.add.at(Nv, Ff[:, j], q)
    Nv /= np.maximum(np.linalg.norm(Nv, axis=1, keepdims=True), 1e-15)
    A = bs.b.A
    lap = (A @ Xg) / bs.b.deg[:, None] - Xg
    el = 0.0
    Hc = (lap * Nv).sum(1)
    # mean squared edge length per vertex
    ev = np.linalg.norm(Xg[E[:, 0]] - Xg[E[:, 1]], axis=1) ** 2
    s2 = np.zeros(bs.nU); cnt = np.zeros(bs.nU)
    np.add.at(s2, E[:, 0], ev); np.add.at(cnt, E[:, 0], 1)
    s2 = s2 / np.maximum(cnt, 1)
    Hk = 4 * Hc / np.maximum(s2, 1e-12) / 1000.0     # ~ 2H in 1/mm
    for rn in regs:
        reg = R[rn]
        fm = reg[Ff].all(1)
        em = fm[fa] & fm[fb]
        vm = reg & good
        if em.sum() == 0:
            continue
        out[rn] = dict(dih_p99=round(float(np.percentile(dih[em], 99)), 1), dih_max=round(float(dih[em].max()), 1),
                       H_p99=round(float(np.percentile(np.abs(Hk[vm]), 99)), 3), H_conv_max=round(float(Hk[vm].max()), 3))
    return out


def clay_sheet(cands, out, cols=None, half=False):
    """1:1 clay crops per judged frame/side: rows = candidates [(name, Body)], outlines of A (red) on later rows"""
    cols = cols or [(f, s) for f, s, _ in JUDGED]
    rows = []
    A = None
    for name, body in cands:
        ims = []
        for f, sd in cols:
            fr = k.frame(f)
            g = k.geom(fr, body)
            box = view_box(fr, sd)
            rgb, ids = sh.clay(fr, g, box)
            if A is None or name == "A":
                pass
            ims.append(Image.fromarray(rgb))
        rows.append(ims)
    W = sum(im.width for im in rows[0]) + 4 * (len(rows[0]) - 1)
    H = sum(max(im.height for im in r) for r in rows) + 4 * (len(rows) - 1)
    S = Image.new("RGB", (W, H), (255, 0, 255))
    y = 0
    for r in rows:
        x = 0
        for im in r:
            S.paste(im, (x, y)); x += im.width + 4
        y += max(im.height for im in r) + 4
    if half:
        S = S.resize((S.width // 2, S.height // 2), Image.LANCZOS)
    S.save(out)
    return S.size


def report(body, name="B", frames=JUDGED, other=True, log=print):
    A = k.Body()
    res = {}
    for f, sd, regs in frames:
        fr = k.frame(f)
        gA, gB = k.geom(fr, A), k.geom(fr, body)
        mv, _ = moves(fr, sd, gA, gB, regs)
        kn = knots(fr, gB, sd, [r for r in regs if r in ("fold", "elbow", "crease", "cap")])
        knA = knots(fr, gA, sd, [r for r in regs if r in ("fold", "elbow", "crease", "cap")])
        res[(f, sd)] = (mv, kn, knA)
        line = "%-9s %s " % (f, sd)
        for rn in regs:
            v = mv.get(rn)
            line += " %s[max %s mean %s sil %s..%s]" % (rn, v["max"], v["mean"], v["sil_min"], v["sil_max"]) if v else " %s[-]" % rn
        log(line)
        line = "            knots B/A:"
        for rn, v in kn.items():
            a = knA.get(rn, {})
            line += " %s dih99 %s/%s Hp99 %s/%s Hmax %s/%s;" % (rn, v["dih_p99"], a.get("dih_p99"), v["H_p99"], a.get("H_p99"),
                                                               v["H_conv_max"], a.get("H_conv_max"))
        log(line)
        if f == "look_f" and sd == "r":
            wa, wb, dw = look_width(gA, gB, fr)
            log("            look_f shoulder width A %s B %s delta %+.1f px" % (wa, wb, dw))
            res["look_w"] = dw
    if other:
        for f, sd in OTHER:
            fr = k.frame(f)
            gA, gB = k.geom(fr, A), k.geom(fr, body)
            mv, _ = moves(fr, sd, gA, gB, ("cap", "delt", "fold", "elbow"))
            kn = knots(fr, gB, sd, ("fold", "elbow", "cap"))
            knA = knots(fr, gA, sd, ("fold", "elbow", "cap"))
            line = "%-9s %s (other)" % (f, sd)
            for rn, v in mv.items():
                line += " %s[max %s mean %s]" % (rn, v["max"], v["mean"]) if v else ""
            line += " | dih99 " + " ".join("%s %s/%s" % (rn, v["dih_p99"], knA.get(rn, {}).get("dih_p99")) for rn, v in kn.items())
            log(line)
            res[(f, sd)] = (mv, kn, knA)
    return res
