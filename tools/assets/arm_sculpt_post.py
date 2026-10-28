"""Her arms' rest sculpt, round 2: broad forms in the geometry, the fine ones baked in her skin's relief (Body 19,
27 Oct 2026). Round 1 (arm_contour_post) failed a max judge: 1-4 mm contour nudges don't read at the town close-up
(1 mm ~ 0.9 px) and its 2.6 mm pit-fold ridge read as a seam. The owner: "not toned or sexy", "armpit problems ...
and elbow" (a tube plugged into the torso, a flat front pit, a weak deltoid). So every form here is 5-10 mm and broad
(30 mm and up), and the shading carries it.

GEOMETRY (left-canonical, mirrored; heroine_arm_tone's charts: t = s / humerus down her upper arm's axis from her
shoulder joint's level, phi deg round it: 0 front, 90 out, 180 back, -90 in):
  DELT   the deltoid as one mass of three heads (front, middle, rear domes) cut by a soft V: its lower edge inserts on
         the outer arm at DELT_V[0] of the humerus, rising to DELT_V[1] at its front and back borders (a band of
         DELT_BAND either side, so the edge is a soft slope, never a ring); none over her shoulder's top (DELT_TOP), so
         the cap stands proud of the arm below it, not out past her shoulders;
  UP     broad radial bumps: the outer arm slimmer below the insertion (so the cap reads), the biceps' belly forward,
         the inner arm slimmer (no added girth), the triceps' upper back, the flat tendon plane above the olecranon;
  FORE   the forearm round its own centre line (per-slice centroids: tone's straight forearm axis drifts ~20 mm off her
         wrist), along her surface normal: the brachioradialis/extensor and flexor masses high on it, the lower half
         flattened front and back to a flat wrist;
  WEDGE  the front of her armpit: the pectoral tendon as a broad mass (Gaussian WEDGE["sig"] mm, so ~2.4x that across
         at half height) from her breast's upper-outer side into the front of her arm under the deltoid, and the pit's
         hollow behind it as broad (no ridge line: round 1's 14 mm biweight ridge + hollow pair is gone);
  each taken by her arm's share of the skinning (the wedge by its own window), smoothed over her surface; positions and
  normals; her shoulder PSDs kept valid as round 1 kept them (arm_contour_post.psd_keep).
RELIEF (her body's and her graft's normal maps, heroine_arm_tone's bake): the grooves and planes of 2-3 mm that her
  ~4.7 mm mesh shows only as shading: the deltopectoral groove, the deltoid's rear border, the groove between biceps and
  triceps on the outer arm, the triceps' tendon plane, the brachioradialis' edge; each broad (Gaussian sigma >= 8 mm:
  20-25 mm across), never a line (the owner's "weird vein looking things", heroine_arm_lines). The old tone is taken out
  of both maps (her body's had nothing else; her graft's collar relief is kept) and this relief laid instead.

    python tools/assets/arm_sculpt_post.py <in heroine.glb> <out heroine.glb> [--no-relief] [--png DIR]
Idempotent: done-mark arm_sculpt (a marked body is copied unchanged). Bare body only: outfits follow later.
"""
import io
import json
import os
import shutil
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import heroine_arm_tone as tone  # noqa: E402
import arm_contour_post as ac  # noqa: E402

MARK = "arm_sculpt"
_E = os.environ.get
AMT = float(_E("SCULPT_AMT", "1.35"))   # (round 2: 1.0 read too faint at 0.9 px/mm in clay)
RELIEF_K = float(_E("SCULPT_RELIEF", "1.6"))   # the relief's slopes x this (tone's was 1.75)
# deltoid: heads (t0, phi0, half-length t, half-width deg, mm); its V edge (t at phi 90, t at its borders), band (t)
# (the middle head kept low: it is her shoulder line seen from the front (2.7 head widths, approved); the cap stands
# proud in the side view through the front and rear heads)
DELT_HEADS = ((0.14, 28, 0.26, 48, 6.0), (0.17, 90, 0.30, 62, 1.5), (0.14, 152, 0.26, 48, 5.5))
DELT_V = (0.46, 0.24)
DELT_BAND = 0.07
DELT_TOP = (-0.14, -0.02)   # t: none above the first, whole below the second
DELT_PHI = (-25, 205)       # its front and back borders (deg), 20 deg soft
UP = (
    (0.68, 95, 0.22, 55, -5.0),     # outer arm below the insertion: slimmer, so the cap stands proud
    (0.60, -5, 0.24, 52, 5.0),      # biceps' belly, forward, easing into the crease
    (0.42, -100, 0.26, 45, -4.5),   # inner arm slimmer (no added girth)
    (0.33, 170, 0.22, 50, 4.0),     # triceps, upper back third
    (0.86, 180, 0.09, 50, -2.5),    # triceps' flat tendon plane above the olecranon
)
# forearm, round its centre line: (t2 from the elbow in forearm lengths, phi0, half-length, half-width deg (>= 180: all
# round), mm along her normal)
FORE = (
    (0.24, 40, 0.20, 50, 3.0),      # brachioradialis / extensors, high on the outer front
    (0.26, -85, 0.20, 50, 2.5),     # flexors, high on the inner side
    (0.74, 0, 0.24, 45, -2.5),      # lower half flattened, front
    (0.74, 180, 0.24, 45, -2.5),    # and back: a flat wrist
    (0.62, 0, 0.30, 180, -1.0),     # the lower half slimmer all round
)
# the front of her pit: the arm end (t, phi) on her arm, the chest end as an offset from the pit's apex (m), the mass
# (mm, Gaussian sigma mm), the hollow behind it (mm, sigma mm, its offset toward the apex mm)
WEDGE = dict(arm=(0.30, -38.0), chest=(-0.030, -0.075, 0.060), h=6.0, sig=13.0, hollow=-3.0, hsig=16.0, back=24.0)
# relief paths: ((t0, phi0), (t1, phi1), chart, mm, sigma mm, end fades (share of the length))
GROOVES = (
    ((-0.10, 8), (0.42, 78), "up", -2.5, 9.0, (0.15, 0.35)),     # deltopectoral groove into the insertion
    ((-0.05, 172), (0.42, 102), "up", -1.5, 9.0, (0.2, 0.35)),   # the deltoid's rear border
    ((0.48, 92), (0.98, 102), "up", -2.5, 8.0, (0.25, 0.25)),    # biceps / triceps on the outer arm
    ((0.05, 15), (0.55, 30), "fore", -1.5, 8.0, (0.25, 0.3)),    # the brachioradialis' inner edge
)
PLANES = (
    (0.86, 180, 0.08, 55, -2.0),    # the triceps' tendon plane (relief)
    (0.60, -5, 0.20, 45, 1.5),      # the biceps' belly (relief)
    (0.16, 90, 0.20, 50, 1.5),      # the deltoid's middle head (relief)
)
SMOOTH = int(_E("SCULPT_SMOOTH", "4"))
ON_ARM = (5.0, 28.0)        # the relief: whole within the first mm outside her arm's radius, none past the second (tone's
                            # 5-14 read as a 50 deg step at the shoulder's top on her graft: a seam)
MAX_TILT = float(_E("SCULPT_MAX_TILT", "22"))   # deg: the relief's slope capped (a mask edge never draws a line)


def _bw(x):
    x = np.clip(1 - x * x, 0, None)
    return x * x


def delt_field(t, phi):
    """the deltoid's height (mm) on the upper-arm chart"""
    d = np.zeros_like(t)
    for t0, p0, ht, hp, mm in DELT_HEADS:
        d += mm * _bw((t - t0) / ht) * _bw(tone._wrap(phi - p0) / hp)
    a = np.clip(np.abs(tone._wrap(phi - 90)) / 62.0, 0, 1)
    tb = DELT_V[0] + (DELT_V[1] - DELT_V[0]) * a * a * (3 - 2 * a)
    m = tone._step(tb + DELT_BAND, tb - DELT_BAND, t) * tone._step(DELT_TOP[0], DELT_TOP[1], t)
    pw = ((phi + 90) % 360) - 90          # -90 .. 270, continuous over the back
    m = m * tone._step(DELT_PHI[0] - 20, DELT_PHI[0], pw) * tone._step(DELT_PHI[1] + 20, DELT_PHI[1], pw)
    return d * m


def up_grid(L, up=UP, delt=True):
    """the upper arm's move (mm) on tone's (s, phi) grid (delt: with the deltoid's heads)"""
    S, P = np.meshgrid(tone.RG_S, tone.RG_P, indexing="ij")
    t = S / (L * 1000)
    return (delt_field(t, P) if delt else 0.0) + ac._bumps(t, P, up)


def _centres(Q, O2, ax2, L2, wf):
    """the forearm's centre line: per 2% slice of t2, the centroid of its arm-carried points (smoothed)"""
    s2 = (Q - O2) @ ax2 / L2
    ts = np.arange(-0.1, 1.11, 0.02)
    C = []
    for t0 in ts:
        m = (np.abs(s2 - t0) < 0.012) & (wf > 0.5)
        C.append(Q[m].mean(0) if m.sum() > 8 else np.full(3, np.nan))
    C = np.array(C)
    ok = ~np.isnan(C[:, 0])
    for k in range(3):
        C[:, k] = np.interp(ts, ts[ok], C[ok, k])
    from scipy.ndimage import gaussian_filter1d
    return ts, gaussian_filter1d(C, 1.5, axis=0, mode="nearest")


def fore_chart(Q, fr, L2, cl):
    """(t2, phi, r mm) round the forearm's centre line cl = _centres(her rest points, ...)"""
    O2, ax2, f2, l2 = fr["fore"]
    ts, C = cl
    t2 = (Q - O2) @ ax2 / L2
    c = np.stack([np.interp(t2, ts, C[:, k]) for k in range(3)], 1)
    q = Q - c
    q -= (q @ ax2)[:, None] * ax2
    return t2, np.degrees(np.arctan2(q @ l2, q @ f2)), np.linalg.norm(q, axis=1) * 1000


def moves(b, FR=None, up=UP, fore=FORE, wedge=WEDGE, grids=None, amt=AMT, smooth=SMOOTH, delt=True):
    """(dU (n, 3) m, info): the upper arm radial (via arm_contour_post.fields on a grid), the forearm and the wedge
    along her normals; smoothed over her surface. (delt=False: no deltoid; arm_carve_post's tables alone)"""
    import pit_hollow_post as ph
    from scipy.ndimage import map_coordinates  # noqa: F401
    from scipy.spatial import cKDTree
    FR = FR or tone.frames(b)
    J = {n: np.linalg.inv(b.ibm[i])[:3, 3] for i, n in enumerate(b.names)}
    g = {}
    for side, fr in FR.items():
        O, ax = fr["up"][0], fr["up"][1]
        L = float((J["lowerarm_" + side] * fr["mir"] + fr["off"] - O) @ ax)
        G = up_grid(L, up, delt)
        if grids is not None and side in grids:
            G = G + grids[side]["up"]
        g[side] = {"up": G}
    dU, info = ac.fields(b, FR, up=(), fore=(), fold={}, grids=g, smooth=0)
    Nv = tone._vn(b.U, b.F)
    for side, fr in FR.items():
        mir, off = fr["mir"], fr["off"]
        Q = b.U * mir + off
        E = J["lowerarm_" + side] * mir + off
        H = J["hand_" + side] * mir + off
        L2 = float(np.linalg.norm(H - E))
        wf = ac._armw(b, side, ("lowerarm", "hand"))
        t2, p2, r2 = fore_chart(Q, fr, L2, _centres(Q, fr["fore"][0], fr["fore"][1], L2, wf))
        df = ac._bumps(t2, p2, fore) * tone._step(-0.04, 0.08, t2) * tone._step(1.04, 0.96, t2)
        df = df * tone._step(0.1, 0.4, wf) * tone._step(70, 55, r2)
        mv = df[:, None] * Nv
        # the wedge, along her normal
        fo = np.zeros(len(Q))
        if wedge and wedge.get("h"):
            ap = Q[ph.apex(b, b.U, side)]
            O, ax, f, l = fr["up"]
            Lu = float((E - O) @ ax)
            ta, pa = wedge["arm"]
            Ra = map_coordinates(fr["Rg"], [[(ta * Lu * 1000 - tone.RG_S[0]) / 5], [(pa - tone.RG_P[0]) / 5]], order=1)[0]
            pr = np.radians(pa)
            A_end = O + ax * ta * Lu + (np.cos(pr) * f + np.sin(pr) * l) * Ra / 1000
            tree = cKDTree(Q)
            C_end = Q[tree.query(ap + np.array(wedge["chest"]))[1]]
            us = np.linspace(0, 1, 41)
            path = Q[tree.query(C_end[None] + us[:, None] * (A_end - C_end)[None])[1]]
            dd, k = cKDTree(path).query(Q)
            u = us[k]
            env = np.sin(np.pi * np.clip(u, 0, 1)) ** 0.5
            fo = wedge["h"] * np.exp(-0.5 * (dd * 1000 / wedge["sig"]) ** 2) * env
            if wedge.get("hollow"):
                sh_ = (ap - path[20]) / max(np.linalg.norm(ap - path[20]), 1e-6) * wedge["back"] / 1000
                back = cKDTree(Q[tree.query(path + sh_[None])[1]]).query(Q)[0] * 1000
                fo = fo + wedge["hollow"] * np.exp(-0.5 * (back / wedge["hsig"]) ** 2) * env
            fo = fo * tone._step(0.17, 0.11, np.linalg.norm(Q - ap, axis=1))
            mv = mv + fo[:, None] * Nv
            info[side + "_wedge"] = dict(arm=A_end.round(4).tolist(), chest=C_end.round(4).tolist())
        dU += mv * 1e-3 * mir
        info[side].update(fore_mm=[float(df.min()), float(df.max())], wedge_mm=[float(fo.min()), float(fo.max())])
    dU *= amt
    if smooth:
        mov = np.linalg.norm(dU, axis=1) > 1e-6
        reg = ((b.A @ mov.astype(float)) > 0) | mov
        for _ in range(smooth):
            dU[reg] = dU[reg] + 0.5 * b.lap(dU)[reg]
    return dU, info


# ------------------------------------------------------------------ relief --
def _path_field(t, phi, p0, p1, R, mm, sig, fades):
    """a groove/ridge along a straight path in the (s mm, arc mm) plane of a chart, Gaussian across, faded at its ends"""
    (t0, a0), (t1, a1) = p0, p1
    k = R * np.pi / 180
    x0, y0, x1, y1 = t0, tone._wrap(a0) * k, t1, tone._wrap(a1) * k
    x, y = t, tone._wrap(phi) * k
    ex, ey = x1 - x0, y1 - y0
    u = ((x - x0) * ex + (y - y0) * ey) / (ex * ex + ey * ey)
    uc = np.clip(u, 0, 1)
    d = np.hypot(x - x0 - uc * ex, y - y0 - uc * ey)
    env = tone._step(-0.05, fades[0], u) * tone._step(1.05, 1 - fades[1], u)
    return mm * np.exp(-0.5 * (d / sig) ** 2) * env


def relief_side(Q, fr, L, L2, wf, cl):
    s, phi, r = tone._chart(Q, *fr["up"])
    R = tone.map_coordinates(fr["Rg"], [(np.clip(s, tone.RG_S[0], tone.RG_S[-1]) - tone.RG_S[0]) / 5,
                                        (phi - tone.RG_P[0]) / 5], order=1, mode="nearest")
    on = tone._step(ON_ARM[1], ON_ARM[0], r - R) * tone._step(270, 240, s)
    t = s / (L * 1000)
    t2, p2, r2 = fore_chart(Q, fr, L2, cl)
    hu = np.zeros(len(Q))
    hf = np.zeros(len(Q))
    for p0, p1, ch, mm, sig, fades in GROOVES:
        if ch == "up":
            # (t scaled to mm along the arm: the path works in (s mm, arc mm))
            hu += _path_field(s, phi, (p0[0] * L * 1000, p0[1]), (p1[0] * L * 1000, p1[1]), 45.0, mm, sig, fades)
        else:
            hf += _path_field(t2 * L2 * 1000, p2, (p0[0] * L2 * 1000, p0[1]), (p1[0] * L2 * 1000, p1[1]), 38.0, mm, sig, fades)
    hu += ac._bumps(t, phi, PLANES)
    hu *= on * tone._step(-0.25, -0.12, t) * tone._step(1.12, 1.04, t)
    hf *= tone._step(-0.02, 0.06, t2) * tone._step(1.0, 0.9, t2) * tone._step(0.1, 0.4, wf) * tone._step(70, 55, r2)
    return (hu + hf) * 1e-3 * RELIEF_K


def relief_field_fn(b, FR):
    J = {n: np.linalg.inv(b.ibm[i])[:3, 3] for i, n in enumerate(b.names)}
    Ls = {}
    for side, fr in FR.items():
        O, ax = fr["up"][0], fr["up"][1]
        E = J["lowerarm_" + side] * fr["mir"] + fr["off"]
        H = J["hand_" + side] * fr["mir"] + fr["off"]
        Ls[side] = (float((E - O) @ ax), float(np.linalg.norm(H - E)))
    # the forearm weight per point is needed at bake samples: nearest rest vertex's
    from scipy.spatial import cKDTree
    tree = cKDTree(b.U)
    WF = {s: ac._armw(b, s, ("lowerarm", "hand")) for s in FR}
    CL = {}
    for s, fr in FR.items():
        Qv = b.U * fr["mir"] + fr["off"]
        CL[s] = _centres(Qv, fr["fore"][0], fr["fore"][1], Ls[s][1], WF[s])

    def field(P, FR_=None):
        h = np.zeros(len(P))
        idx = tree.query(P)[1]
        for side, fr in FR.items():
            Q = P * fr["mir"] + fr["off"]
            on = Q[:, 0] > 0.06
            if on.any():
                h[on] += relief_side(Q[on], fr, *Ls[side], WF[side][idx[on]], CL[side])
        return h
    return field


def _old_tone_slopes(G, b, k, size):
    """the tone as heroine_arm_lines last laid it (its soft field at the tone's record), for prim k"""
    import importlib
    rec = G.g["asset"]["extras"]["heroine_arm_tone"]
    os.environ["TONE_DELT_W"], os.environ["TONE_SPLIT"] = repr(rec["delt_w"]), repr(rec["split"])
    T = importlib.reload(tone)
    T.STRENGTH = float(rec["strength"])
    import heroine_arm_lines as al
    FR = T.frames(b)
    T.field, _ = al.soft_field(T, FR)
    name, sx, sy = T.bake(G, b, FR, k, size)
    importlib.reload(tone)
    return name, sx, sy


def _decode(img):
    n = img[..., :3].astype(float) / 255 * 2 - 1
    z = np.maximum(n[..., 2], 0.2)
    return n[..., 0] / z, n[..., 1] / z


def relay_relief(path, old, b_new, png_dir=None):
    """her two normal maps: the old tone out (old: {k: (name, sx, sy)} from _old_tone_slopes on the body before the
    move; her graft's collar relief kept), this relief in"""
    from heroine_neck import _Gl
    from PIL import Image
    g, binc = tone._read(path)
    FRn = tone.frames(b_new)
    field = relief_field_fn(b_new, FRn)
    orig = tone.field
    rep = {}
    for k in (0, 1):
        size = tone.BODY_SIZE if k == 0 else tone.GRAFT_SIZE
        name, osx, osy = old[k]
        tone.field = field
        G1 = _Gl(path)
        _, sx, sy = tone.bake(G1, b_new, FRn, k, size)
        tone.field = orig
        mag = np.hypot(sx, sy)
        steep = int((mag > np.tan(np.radians(MAX_TILT))).sum())
        cap = np.minimum(1.0, np.tan(np.radians(MAX_TILT)) / np.maximum(mag, 1e-12))
        sx, sy = sx * cap, sy * cap
        mat = [m for m in g["materials"] if m.get("name") == name][0]
        cur = mat.get("normalTexture", {}).get("index")
        if cur is not None:
            bx, by = _decode(tone._image(g, binc, cur))
            bx, by = bx - osx, by - osy          # the old tone out
            if k == 0:
                bx, by = bx * 0, by * 0          # (her body's map was the tone alone)
        else:
            bx, by = np.zeros_like(sx), np.zeros_like(sy)
        n = np.stack([sx + bx, sy + by, np.ones_like(sx)], -1)
        n /= np.linalg.norm(n, axis=-1, keepdims=True)
        img = np.clip(np.round((n * 0.5 + 0.5) * 255), 0, 255).astype(np.uint8)
        buf = io.BytesIO()
        Image.fromarray(img).save(buf, "PNG", optimize=True)
        png = buf.getvalue()
        if png_dir:
            os.makedirs(png_dir, exist_ok=True)
            open(os.path.join(png_dir, "arm_sculpt_%s.png" % name), "wb").write(png)
        while len(binc) % 4:
            binc.append(0)
        o = len(binc)
        binc += png
        g["bufferViews"].append({"buffer": 0, "byteOffset": o, "byteLength": len(png)})
        g["images"].append({"name": "heroine_arm_sculpt_" + name, "mimeType": "image/png",
                            "bufferView": len(g["bufferViews"]) - 1})
        g["textures"].append({"sampler": 0, "source": len(g["images"]) - 1})
        mat["normalTexture"] = {"index": len(g["textures"]) - 1}
        rep[name] = dict(steepest_deg=round(float(np.degrees(np.arctan(mag.max()))), 1), capped_texels=steep,
                         texels=int((np.hypot(sx, sy) > 0.01).sum()),
                         old_out_max=round(float(np.hypot(osx, osy).max()), 3), kb=len(png) // 1024)
    import heroine_arm_lines as al
    al._drop_unused(g)
    ex = g["asset"]["extras"]
    ex["heroine_arm_tone"] = dict(ex["heroine_arm_tone"], replaced_by=MARK)
    tone._write(path, g, binc)
    return rep


def run(src, dst, grids=None, relief=True, png_dir=None, quiet=False):
    from heroine_neck import _Gl
    import pit_hollow_post as ph
    if os.path.abspath(src) != os.path.abspath(dst):
        shutil.copyfile(src, dst)
    G = _Gl(dst)
    ex = G.g.setdefault("asset", {}).setdefault("extras", {})
    if ex.get(MARK):
        print("ARM_SCULPT: %s has had it" % dst)
        return None
    b = ph.Body(G)
    old = {k: _old_tone_slopes(G, b, k, tone.BODY_SIZE if k == 0 else tone.GRAFT_SIZE) for k in (0, 1)} if relief else None
    dU, info = moves(b, grids=grids)
    n0 = ph.vn(b.U, b.F)
    n1 = ph.vn(b.U + dU, b.F)
    g = G.g
    mesh = g["meshes"][[n for n in g["nodes"] if n.get("name") == "Heroine"][0]["mesh"]]
    prims = [p for p in mesh["primitives"] if g["materials"][p["material"]].get("name") != "skin_head"]
    o = 0
    for p in prims:
        ai, ni = p["attributes"]["POSITION"], p["attributes"]["NORMAL"]
        X = G.get(ai).astype(float)
        w = b.wid[o:o + len(X)]
        o += len(X)
        X = X + dU[w]
        N = G.get(ni).astype(float) + (n1 - n0)[w]
        N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
        G.put(ai, X.astype(np.float32))
        G.put(ni, N.astype(np.float32))
        g["accessors"][ai]["min"] = X.min(0).astype(np.float32).tolist()
        g["accessors"][ai]["max"] = X.max(0).astype(np.float32).tolist()
    rep = {}
    ac.psd_keep(G, prims, b.wid, dU, n1 - n0, rep)
    mv = np.linalg.norm(dU, axis=1) * 1000
    ex[MARK] = {"delt": [list(x) for x in DELT_HEADS], "delt_v": DELT_V, "up": [list(x) for x in UP],
                "fore": [list(x) for x in FORE], "wedge": WEDGE, "amt": AMT, "smooth": SMOOTH,
                "max_mm": round(float(mv.max()), 2), "grids": bool(grids), "relief": relief, "relief_k": RELIEF_K}
    js = json.dumps(g, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    binb = bytes(G.buf[G.b0:G.b0 + g["buffers"][0]["byteLength"]])
    body = struct.pack("<I", len(js)) + b"JSON" + js + struct.pack("<I", len(binb)) + b"BIN\x00" + binb
    open(dst, "wb").write(b"glTF" + struct.pack("<II", 2, 12 + len(body)) + body)
    rrep = None
    if relief:
        b_new = ph.Body(_Gl(dst))
        rrep = relay_relief(dst, old, b_new, png_dir)
    if not quiet:
        print("ARM_SCULPT: %d points moved > 0.5 mm, max %.1f mm -> %s" % ((mv > 0.5).sum(), mv.max(), dst))
        for k, v in info.items():
            print("  %s %s" % (k, json.dumps(v)))
        print("  psd kept (points, max mm taken back): " + ", ".join("%s %d/%.1f" % (k, v[0], v[1]) for k, v in rep.items()))
        if rrep:
            print("  relief: %s" % json.dumps(rrep))
    return info


if __name__ == "__main__":
    a = sys.argv[1:]
    png = a[a.index("--png") + 1] if "--png" in a else None
    files = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or a[i - 1] != "--png")]
    run(files[0], files[1], relief="--no-relief" not in a, png_dir=png)
