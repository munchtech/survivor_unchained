"""g3meas.py: the G3 chain's numbers (Body 12).
  targets <glb>                  her body's morph names
  marks <glb>                    her body's done-marks
  same <a.glb> <b.glb>           are two bodies the same (per primitive positions/weights)
  zone <base.glb> <body.glb> <art root>   what the follow must carry: rest moves, the new helpers' weights, the
                                 shoulder shapes; outfit/armor points over each; tuck records stale vs the body
  wc <base wc dir> <wc dir>      wearcheck per outfit/piece: OUT>2 and worst, baseline -> now; the pairs that got worse
"""
import glob
import json
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

W = os.environ.get("W", r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\armor-7")
sys.path.insert(0, os.path.join(W, "tools", "assets"))
from heroine_neck import _Gl  # noqa: E402
from shoulder_psd_post import _read_sparse  # noqa: E402


def body(path):
    G = _Gl(path)
    g = G.g
    ni = [n for n in g["nodes"] if n.get("name") == "Heroine"][0]
    m = g["meshes"][ni["mesh"]]
    skin = g["skins"][ni["skin"]]
    jn = [g["nodes"][j]["name"] for j in skin["joints"]]
    P, Wn, prims = [], [], []
    for p in m["primitives"]:
        if g["materials"][p["material"]].get("name") == "skin_head":
            continue
        a = p["attributes"]
        X = G.get(a["POSITION"]).astype(float)
        wn = np.zeros((len(X), len(jn)))
        for jk, wk in (("JOINTS_0", "WEIGHTS_0"), ("JOINTS_1", "WEIGHTS_1")):
            if jk in a:
                J = G.get(a[jk]).astype(int)
                Wt = G.get(a[wk]).astype(float)
                if Wt.max() > 1.5:
                    Wt = Wt / 255.0
                for k in range(J.shape[1]):
                    np.add.at(wn, (np.arange(len(X)), J[:, k]), Wt[:, k])
        P.append(X)
        Wn.append(wn)
        prims.append(p)
    names = m.get("extras", {}).get("targetNames", [])
    marks = sorted(((g.get("asset") or {}).get("extras") or {}).keys())
    return dict(G=G, g=g, m=m, P=np.concatenate(P), W=np.concatenate(Wn), jn=jn, names=names, marks=marks, prims=prims)


def shape(b, name):
    k = b["names"].index(name)
    out = []
    for p in b["prims"]:
        n = b["g"]["accessors"][p["attributes"]["POSITION"]]["count"]
        t = p.get("targets", [])
        out.append(_read_sparse(b["G"], t[k]["POSITION"]) if k < len(t) and "POSITION" in t[k] else np.zeros((n, 3)))
    return np.concatenate(out)


def pieces(root):
    fs = sorted(glob.glob(os.path.join(root, "people", "heroine_outfit_*.gltf")))
    fs = [f for f in fs if not f.endswith("_lod.gltf")] + sorted(glob.glob(os.path.join(root, "armor", "*.gltf")))
    fs += sorted(glob.glob(os.path.join(root, "people", "heroine_hair_*.gltf")))
    for f in fs:
        G = _Gl(f)
        X = []
        for m in G.g["meshes"]:
            for p in m["primitives"]:
                X.append(G.get(p["attributes"]["POSITION"]).astype(float))
        yield os.path.basename(f).replace(".gltf", "").replace("heroine_outfit_", ""), np.concatenate(X) if X else np.zeros((0, 3))


def key(P):
    return np.round(P.astype(np.float32).astype(np.float64) * 1e5).astype(np.int64)


def records(path):
    b = open(path, "rb").read()
    n = int(np.frombuffer(b[:4], "<u4")[0])
    return np.frombuffer(b, np.dtype([("k", "<i4", 3), ("v", "<f4")]), n, 4)


def zone(a, bb, root):
    A, B = body(a), body(bb)
    print("G3 zone body: base %d pts, new %d pts; bones base %d new %d (+%s)" % (
        len(A["P"]), len(B["P"]), len(A["jn"]), len(B["jn"]), ",".join(sorted(set(B["jn"]) - set(A["jn"])))))
    tB = cKDTree(B["P"])
    d, _ = tB.query(A["P"])
    tA = cKDTree(A["P"])
    dB, jA = tA.query(B["P"])
    mv = d > 0.0005
    print("G3 zone rest: %d base points moved > 0.5 mm (max %.1f mm), %d > 2 mm; %d new points (no base point within 0.5 mm)"
          % (mv.sum(), d.max() * 1000, (d > 0.002).sum(), (dB > 0.0005).sum()))
    new_b = sorted(set(B["jn"]) - set(A["jn"]))
    hw = B["W"][:, [B["jn"].index(n) for n in new_b]].sum(1) if new_b else np.zeros(len(B["P"]))
    # weights changed: per new point, the change against its nearest base point on the shared bones
    common = [n for n in A["jn"] if n in B["jn"]]
    dw = np.abs(B["W"][:, [B["jn"].index(n) for n in common]] - A["W"][jA][:, [A["jn"].index(n) for n in common]]).sum(1) / 2 + hw
    wz = dw > 0.05
    print("G3 zone weights: %d body points with > 0.05 of their weight moved (%d on the new helper bones > 0.05)" % (wz.sum(), (hw > 0.05).sum()))
    sh = [n for n in B["names"] if n.startswith("shoulder_")]
    S = np.zeros(len(B["P"]))
    for n in sh:
        S = np.maximum(S, np.linalg.norm(shape(B, n), axis=1))
    sz = S > 0.0005
    print("G3 zone shapes: %d shoulder shapes; %d body points move > 0.5 mm in one (max %.1f mm)" % (len(sh), sz.sum(), S.max() * 1000))
    zr = cKDTree(A["P"][mv]) if mv.any() else None
    zw = cKDTree(B["P"][wz]) if wz.any() else None
    zs = cKDTree(B["P"][sz]) if sz.any() else None
    print("G3 zone per file: points within 45 mm of moved rest skin | within 15 mm of reweighted skin | within 45 mm of shaped skin")
    for nm, X in pieces(root):
        c = [int((z.query(X, distance_upper_bound=r)[0] < r).sum()) if z is not None and len(X) else 0 for z, r in ((zr, 0.045), (zw, 0.015), (zs, 0.045))]
        if any(c):
            print("G3 zone   %-28s %7d pts: rest %6d  weights %6d  shapes %6d" % (nm, len(X), *c))
    kB = {tuple(k) for k in key(B["P"])}
    kA = {tuple(k) for k in key(A["P"])}
    tot_s = tot_n = 0
    for f in sorted(glob.glob(os.path.join(root, "people", "armor_tuck", "*.bin")) + glob.glob(os.path.join(root, "armor", "armor_tuck", "*.bin"))):
        r = records(f)
        if not len(r):
            continue
        ks = [tuple(k) for k in r["k"]]
        stale = sum(1 for k in ks if k not in kB)
        stale_base = sum(1 for k in ks if k not in kA)
        # the new body's points with no record whose nearest base point had one (> 0)
        rk = {k: v for k, v in zip(ks, r["v"])}
        hasA = np.array([rk.get(tuple(k), 0) > 0 for k in key(A["P"])])
        newpts = np.array([tuple(k) not in rk for k in key(B["P"])])
        miss = int((newpts & hasA[jA]).sum())
        tot_s += stale
        tot_n += miss
        if stale or miss:
            print("G3 tuck   %-40s %6d records: stale vs new body %5d (vs base %d); new-body points left unrecorded %5d"
                  % (os.path.relpath(f, root), len(r), stale, stale_base, miss))
    print("G3 tuck total: %d stale records, %d new-body points unrecorded" % (tot_s, tot_n))


def wc(a, b):
    def load(d):
        return json.load(open(os.path.join(d, "matrix.json")))["pairs"]
    A, B = load(a), load(b)
    kA = {(e["A"], e["B"]): e for e in A}

    def grp(e):
        return (e["B"].split(".")[0] if "." in e["B"] else e["B"])
    agg = {}
    for lab, L in (("base", A), ("now", B)):
        for e in L:
            r = agg.setdefault(grp(e), {"base": [0, 0.0], "now": [0, 0.0]})[lab]
            r[0] += e["out_n_over_2"]
            r[1] = max(r[1], e["worst_mm"] or 0)
    print("G3 wc per outfit/piece (B side): OUT>2 base -> now, worst mm base -> now")
    for k in sorted(agg, key=lambda k: -(agg[k]["now"][0] - agg[k]["base"][0])):
        r = agg[k]
        print("G3 wc   %-26s %6d -> %6d   %5.1f -> %5.1f" % (k, r["base"][0], r["now"][0], r["base"][1], r["now"][1]))
    print("G3 wc total OUT>2: %d -> %d" % (sum(e["out_n_over_2"] for e in A), sum(e["out_n_over_2"] for e in B)))
    worse = []
    for e in B:
        o = kA.get((e["A"], e["B"]))
        base = o["out_n_over_2"] if o else 0
        if e["out_n_over_2"] - base > 50 or ((e["worst_mm"] or 0) - ((o or {}).get("worst_mm") or 0) > 3):
            worse.append((e["out_n_over_2"] - base, e, base, o))
    print("G3 wc worse than baseline (OUT>2 +50 or worst +3 mm): %d pairs" % len(worse))
    for dd, e, base, o in sorted(worse, key=lambda x: -x[0])[:25]:
        print("G3 wc   %-20s under %-24s OUT>2 %5d -> %5d  worst %5.1f -> %5.1f mm at %s@%s (%s)" % (
            e["A"], e["B"], base, e["out_n_over_2"], (o or {}).get("worst_mm") or 0, e["worst_mm"] or 0,
            e["worst_clip"], e["worst_frame"], e["worst_bone"]))


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "targets":
        print("\n".join(body(sys.argv[2])["names"]))
    elif c == "marks":
        print(",".join(body(sys.argv[2])["marks"]))
    elif c == "same":
        A, B = body(sys.argv[2]), body(sys.argv[3])
        if A["P"].shape != B["P"].shape:
            print("G3 same: NO, points %d vs %d" % (len(A["P"]), len(B["P"])))
        else:
            print("G3 same: positions max %.3f mm, weights max %.4f, targets %s, marks %s" % (
                np.abs(A["P"] - B["P"]).max() * 1000, np.abs(A["W"] - B["W"]).max() if A["W"].shape == B["W"].shape else -1,
                A["names"] == B["names"], A["marks"] == B["marks"]))
    elif c == "zone":
        zone(*sys.argv[2:5])
    elif c == "wc":
        wc(*sys.argv[2:4])
