"""Her arms' rest contour: a slim, toned, feminine athletic arm instead of a tube (Body 19, 27 Oct 2026; the owner on a
town close-up of her bent right arm: "that bend still just dosn't look feminine OR athletic - it just looks clunky", and
on a front 3/4 frame, arm hanging: "armpit problems there too, and elbow").

What it fixes (Body 19's measure, tools/anim/elbow_sweep frames, arm hung straight, t = humerus lengths from the shoulder
joint): no deltoid cap (the lateral outline 35 mm off the humerus line at t .1-.25 but 40 at t .4-.6: the shoulder
narrower than the mid arm, cap -3.6 mm), the front edge flat 54-55 mm from t .2 to .7 (no biceps belly), a bulky inner
arm (medial 54-60 mm at t .2-.5), the back running straight into the elbow (no triceps line, no olecranon), a 27.3 cm
forearm tube; and the front of the pit a flat web from the breast's side to the arm (no anterior axillary fold).

The step, in bind space, left-canonical and mirrored (her right is her left's mirror by construction: heroine_arm_tone's
charts, s mm down her upper arm's own axis from her shoulder joint's level, t = s / humerus, phi deg round it: 0 front,
90 out, 180 back, -90 in; the forearm's chart likewise from her elbow):
  1. UP: soft radial bumps on the upper arm (biweight windows in t and phi, mm out (+) or in (-) from the arm's axis):
     the deltoid as a rounded cap (middle, front and rear heads) easing into its insertion, the inner arm slimmer, the
     biceps' belly, the triceps' heads and their flat tendon above the elbow, the olecranon and the two epicondyles;
  2. FORE: the same on the forearm: the brachioradialis / extensor and flexor masses just below the elbow, the forearm
     slimmer toward a slim wrist;
  3. FOLD: the anterior axillary fold, a soft ridge along her surface normal from the breast's upper-outer side to the
     front of the arm under the deltoid (the pec's lower border), with the pit's hollow behind it;
  each taken by her arm's share of the skinning (upperarm/delt/lowerarm/hand of that side), so her torso keeps its shape
  (the fold's own mask aside), then the move smoothed over her surface (no mask seams).
Positions and normals (her stored normal + the surface's geometric change). Her shoulder pose-space shapes (shoulder_*,
shoulder_psd_post, sparse) are kept COMPATIBLE: inside each shape's support the move is taken back out of its delta (by
smoothstep(|delta| / PSD_KEEP)), so at its sample raise the round-13 shoulder is exactly as approved, and the new
contour fades out as the raise eases in (the shapes' weights sum to at most 1). elbow_point_{l,r} and worn_reaver are
left as they are (deltas: they add on the new shape).

    python tools/assets/arm_contour_post.py <in heroine.glb> <out heroine.glb> [--report]
Idempotent: done-mark arm_contour (a marked body is copied unchanged). Bare body only: outfits and armor follow later
(their chain's body_follow_post carries BODY' minus BASE).
"""
import json
import os
import shutil
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import heroine_arm_tone as tone  # noqa: E402

MARK = "arm_contour"
_E = os.environ.get
AMT = float(_E("CONTOUR_AMT", "1.0"))
# upper arm: (t0, phi0, half-length in t, half-width deg, mm)
UP = (
    (0.15, 95, 0.28, 70, 10.0),      # deltoid, middle head: the cap
    (0.10, 35, 0.25, 40, 4.0),      # deltoid, front head
    (0.12, 155, 0.25, 40, 3.5),     # deltoid, rear head
    (0.55, 90, 0.18, 50, -4.5),     # below the insertion: the outer arm slimmer
    (0.40, -95, 0.30, 60, -9.0),    # inner arm slimmer
    (0.64, -10, 0.24, 55, 5.5),     # biceps' belly
    (0.32, -5, 0.10, 45, -1.5),     # front: deltoid to biceps
    (0.42, -155, 0.24, 45, 5.5),    # triceps, long head
    (0.42, 140, 0.20, 35, 3.5),     # triceps, lateral head
    (0.80, 180, 0.10, 50, -1.5),    # triceps' flat tendon
    (1.02, 180, 0.07, 40, 3.5),     # olecranon
    (0.97, -95, 0.06, 30, 2.5),     # medial epicondyle
    (0.97, 95, 0.06, 30, 1.5),      # lateral epicondyle
)
# forearm: (t0 from the elbow in forearm lengths, phi0, half-length, half-width deg (>= 180: all round), mm)
FORE = (
    (0.25, 45, 0.30, 40, 2.0),      # brachioradialis
    (0.25, -100, 0.30, 60, 1.5),    # flexors
    (0.25, 110, 0.28, 45, 1.0),     # extensors
    (0.35, 0, 0.40, 180, -3.5),     # forearm slimmer
    (0.75, 0, 0.25, 180, -1.5),     # toward a slim wrist
)
# the fold: arm end in the upper arm's chart (t, phi), chest end as an offset from the pit's apex (m), ridge height and
# half-width (mm), the hollow behind it (mm, its offset back along the pit (mm))
FOLD = dict(arm=(0.30, -40.0), chest=(-0.030, -0.075, 0.060), h=3.5, w=14.0, hollow=-1.5, back=14.0)
SMOOTH = int(_E("CONTOUR_SMOOTH", "4"))
PSD_KEEP = 1.5   # mm: a shape's delta from which the move is taken back out of it whole


def _bw(x):
    x = np.clip(1 - x * x, 0, None)
    return x * x


def _bumps(t, phi, table):
    d = np.zeros_like(t)
    for t0, p0, ht, hp, mm in table:
        w = _bw((t - t0) / ht)
        if hp < 180:
            w = w * _bw(tone._wrap(phi - p0) / hp)
        d += mm * w
    return d


def _armw(b, side, names=("upperarm", "delt", "lowerarm", "hand")):
    return b.Wd[:, [i for i, n in enumerate(b.names) if n.endswith("_" + side) and n.split("_")[0] in names]].sum(1)


def _radial(Q, O, ax):
    q = (Q - O) - ((Q - O) @ ax)[:, None] * ax
    return q / np.maximum(np.linalg.norm(q, axis=1, keepdims=True), 1e-9)


def fields(b, FR=None, up=UP, fore=FORE, fold=FOLD, grids=None, smooth=SMOOTH):
    """The rest move (n, 3) m and a per-side info dict. grids: optional {side: (dR_up(s, phi) on tone.RG_S x RG_P,
    mm)} added to the up field (an outside source, e.g. MakeHuman's muscle delta, by the same chart)."""
    import pit_hollow_post as ph
    FR = FR or tone.frames(b)
    J = {n: np.linalg.inv(b.ibm[i])[:3, 3] for i, n in enumerate(b.names)}
    Nv = tone._vn(b.U, b.F)
    dU = np.zeros_like(b.U)
    info = {}
    for side, fr in FR.items():
        mir, off = fr["mir"], fr["off"]
        Q = b.U * mir + off
        O, ax, f, l = fr["up"]
        O2, ax2, f2, l2 = fr["fore"]
        E = J["lowerarm_" + side] * mir + off
        H = J["hand_" + side] * mir + off
        L = float((E - O) @ ax)
        L2 = float(np.linalg.norm(H - E))
        s, phi, r = tone._chart(Q, O, ax, f, l)
        t = s / (L * 1000)
        s2, phi2, r2 = tone._chart(Q, O2, ax2, f2, l2)
        t2 = s2 / (L2 * 1000)
        from scipy.ndimage import map_coordinates
        R = map_coordinates(fr["Rg"], [(np.clip(s, tone.RG_S[0], tone.RG_S[-1]) - tone.RG_S[0]) / 5,
                                       (phi - tone.RG_P[0]) / 5], order=1, mode="nearest")
        wa = _armw(b, side)
        wu = _armw(b, side, ("upperarm", "delt"))
        wf = _armw(b, side, ("lowerarm", "hand"))
        on = tone._step(18.0, 6.0, r - R) * tone._step(0.08, 0.4, wa)
        # upper arm (its bumps end by t 1.1; none on the hand)
        du = _bumps(t, phi, up) * tone._step(1.12, 1.06, t)
        if grids is not None and side in grids:
            du = du + map_coordinates(grids[side]["up"], [(np.clip(s, tone.RG_S[0], tone.RG_S[-1]) - tone.RG_S[0]) / 5,
                                                    (phi - tone.RG_P[0]) / 5], order=1, mode="nearest") * tone._step(1.12, 1.06, t)
        du = du * on * tone._step(-0.25, -0.12, t)
        # forearm, from the elbow to the wrist
        df = _bumps(t2, phi2, fore)
        if grids is not None and side in grids and "fore" in grids[side]:
            gf, tg2, pg = grids[side]["fore"]
            df = df + map_coordinates(gf, [(np.clip(t2, tg2[0], tg2[-1]) - tg2[0]) / (tg2[1] - tg2[0]),
                                           (phi2 - pg[0]) / (pg[1] - pg[0])], order=1, mode="nearest")
        df = df * tone._step(-0.02, 0.06, t2) * tone._step(1.0, 0.9, t2)
        df = df * tone._step(0.1, 0.4, wf) * tone._step(70, 55, r2)
        mv = du[:, None] * _radial(Q, O, ax) + df[:, None] * _radial(Q, O2, ax2)
        # the fold, along her surface normal
        fo = np.zeros(len(Q))
        if fold and fold.get("h"):
            ap = Q[ph.apex(b, b.U, side)]
            ta, pa = fold["arm"]
            Ra = map_coordinates(fr["Rg"], [[(ta * L * 1000 - tone.RG_S[0]) / 5], [(pa - tone.RG_P[0]) / 5]], order=1)[0]
            pr = np.radians(pa)
            A_end = O + ax * ta * L + (np.cos(pr) * f + np.sin(pr) * l) * Ra / 1000
            C_end = ap + np.array(fold["chest"])
            C_end = Q[np.argmin(np.linalg.norm(Q - C_end, axis=1))]
            from scipy.spatial import cKDTree
            tree = cKDTree(Q)
            us = np.linspace(0, 1, 41)
            path = Q[tree.query(C_end[None] + us[:, None] * (A_end - C_end)[None])[1]]
            dd, k = cKDTree(path).query(Q)
            u = us[k]
            dist = dd * 1000
            seg = A_end - C_end
            env = (4 * u * (1 - u)) ** 0.6
            Nq = Nv * mir
            fo = fold["h"] * _bw(dist / fold["w"]) * env
            if fold.get("hollow"):
                # the hollow behind the fold: toward the pit's apex, below the ridge
                sh_ = (ap - path[20]) / max(np.linalg.norm(ap - path[20]), 1e-6) * fold["back"] / 1000
                back = cKDTree(Q[tree.query(path + sh_[None])[1]]).query(Q)[0] * 1000
                fo = fo + fold["hollow"] * _bw(back / fold["w"]) * env
            near = tone._step(0.16, 0.10, np.linalg.norm(Q - ap, axis=1))
            fo = fo * near
            mv = mv + fo[:, None] * Nq
            info[side + "_fold"] = dict(arm=A_end.round(4).tolist(), chest=C_end.round(4).tolist())
        dU += mv * 1e-3 * mir * AMT
        info[side] = dict(L=L, L2=L2, up_mm=[float(du.min()), float(du.max())], fore_mm=[float(df.min()), float(df.max())],
                          fold_mm=[float(fo.min()), float(fo.max())])
    # smoothed over her surface: the moved region only (mask seams out), the rest held
    if smooth:
        mov = np.linalg.norm(dU, axis=1) > 1e-6
        reg = (b.A @ mov.astype(float)) > 0
        reg = reg | mov
        for _ in range(smooth):
            dU[reg] = dU[reg] + 0.5 * b.lap(dU)[reg]
    return dU, info


# ------------------------------------------------------------------ glb plumbing --
def _sparse(G, ai):
    """(indices, values array, (value offset, dtype)) of a sparse accessor (no bufferView)"""
    a = G.g["accessors"][ai]
    sp = a["sparse"]
    iv, vv = G.g["bufferViews"][sp["indices"]["bufferView"]], G.g["bufferViews"][sp["values"]["bufferView"]]
    idt = np.dtype({5121: "u1", 5123: "<u2", 5125: "<u4"}[sp["indices"]["componentType"]])
    io = G.b0 + iv.get("byteOffset", 0) + sp["indices"].get("byteOffset", 0)
    vo = G.b0 + vv.get("byteOffset", 0) + sp["values"].get("byteOffset", 0)
    n = sp["count"]
    idx = np.frombuffer(bytes(G.buf[io:io + idt.itemsize * n]), idt).astype(np.int64)
    val = np.frombuffer(bytes(G.buf[vo:vo + 12 * n]), "<f4").reshape(n, 3).astype(float)
    return idx, val, vo


def _put_sparse(G, ai, vo, val):
    b = np.ascontiguousarray(val, "<f4").tobytes()
    G.buf[vo:vo + len(b)] = b
    a = G.g["accessors"][ai]
    if "min" in a:
        a["min"] = np.minimum(val.min(0), 0).astype(np.float32).tolist()
        a["max"] = np.maximum(val.max(0), 0).astype(np.float32).tolist()


def psd_keep(G, prims, wid, dU, dN, report=None):
    """the move taken back out of each shoulder_* shape inside its support, so its sample stays as approved"""
    g = G.g
    mesh = g["meshes"][[n for n in g["nodes"] if n.get("name") == "Heroine"][0]["mesh"]]
    names = mesh.get("extras", {}).get("targetNames", [])
    done = set()   # shapes may share their sparse data (the 140/175 samples do): each block is moved once
    o = 0
    for p in prims:
        n = g["accessors"][p["attributes"]["POSITION"]]["count"]
        w = wid[o:o + n]
        o += n
        for k, tn in enumerate(names):
            if not tn.startswith("shoulder_"):
                continue
            tg = p["targets"][k]
            ai = tg["POSITION"]
            if "sparse" not in g["accessors"][ai]:
                sys.exit("ARM_CONTOUR: %s is not sparse; this step writes sparse shapes in place only" % tn)
            idx, val, vo = _sparse(G, ai)
            if vo in done:
                continue
            done.add(vo)
            m = tone._ss(np.linalg.norm(val, axis=1) * 1000 / PSD_KEEP)
            val2 = val - dU[w[idx]] * m[:, None]
            _put_sparse(G, ai, vo, val2)
            if "NORMAL" in tg and "sparse" in g["accessors"][tg["NORMAL"]]:
                nidx, nval, nvo = _sparse(G, tg["NORMAL"])
                if nvo in done:
                    continue
                done.add(nvo)
                pos = {int(i): j for j, i in enumerate(idx)}
                mm = np.array([m[pos[int(i)]] if int(i) in pos else 0.0 for i in nidx])
                _put_sparse(G, tg["NORMAL"], nvo, nval - dN[w[nidx]] * mm[:, None])
            if report is not None:
                kept = np.linalg.norm(dU[w[idx]], axis=1) * m
                report.setdefault(tn, [0, 0.0])
                report[tn][0] += int((kept > 1e-4).sum())
                report[tn][1] = max(report[tn][1], float(kept.max() * 1000) if len(kept) else 0.0)


def run(src, dst, grids=None, up=UP, fore=FORE, fold=FOLD, quiet=False):
    from heroine_neck import _Gl
    import pit_hollow_post as ph
    if os.path.abspath(src) != os.path.abspath(dst):
        shutil.copyfile(src, dst)
    G = _Gl(dst)
    ex = G.g.setdefault("asset", {}).setdefault("extras", {})
    if ex.get(MARK):
        print("ARM_CONTOUR: %s has had it" % dst)
        return None
    b = ph.Body(G)
    dU, info = fields(b, up=up, fore=fore, fold=fold, grids=grids)
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
    psd_keep(G, prims, b.wid, dU, n1 - n0, rep)
    mv = np.linalg.norm(dU, axis=1) * 1000
    ex[MARK] = {"up": [list(x) for x in up], "fore": [list(x) for x in fore], "fold": fold, "smooth": SMOOTH,
                "amt": AMT, "psd_keep_mm": PSD_KEEP, "max_mm": round(float(mv.max()), 2),
                "grids": bool(grids)}
    js = json.dumps(g, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    binb = bytes(G.buf[G.b0:G.b0 + g["buffers"][0]["byteLength"]])
    body = struct.pack("<I", len(js)) + b"JSON" + js + struct.pack("<I", len(binb)) + b"BIN\x00" + binb
    open(dst, "wb").write(b"glTF" + struct.pack("<II", 2, 12 + len(body)) + body)
    if not quiet:
        print("ARM_CONTOUR: %d points moved > 0.5 mm, max %.1f mm -> %s" % ((mv > 0.5).sum(), mv.max(), dst))
        for k, v in info.items():
            print("  %s %s" % (k, json.dumps(v)))
        print("  psd kept (points, max mm taken back): " + ", ".join("%s %d/%.1f" % (k, v[0], v[1]) for k, v in rep.items()))
    return info


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    run(a[0], a[1])
