"""Her shoulder's muscle helpers built into a posted body (Body 6 S2; tools/anim/helpers.py SPEC "shoulder"), and their
weights:

    SHOULDER_RIG=1 python tools/assets/shoulder_rig_post.py <in heroine.glb> <out heroine.glb>

Run after scap_rig_post.py (SCAP_RIG=1). Adds per side delt_{s}, trap_{s}, pec_{s}, lat_{s} (helpers.shoulder_rest:
each at its pivot, its Y toward its aim), each a child of the one bone whose weight it takes (SPEC parent: twist_02,
the clavicle, spine_03, spine_03), appended to the skin's joints. Then her body's weights ("Heroine", every
primitive): per side and helper, its mask (smoothstep bands, SPEC "weights") of its parent's weight moves to it. Below
SPEC A[0] each helper moves exactly as its parent, so the move changes nothing there (her idles and the Look); her
other bones' weights are untouched. Four bones a point: the smallest folded into its own group's largest (a helper in
its parent's group). Without SHOULDER_RIG=1 in the environment it copies the body unchanged (the build's gate)."""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "anim"))
sys.path.insert(0, HERE)
import helpers as hp  # noqa: E402
from scap_rig_post import Glb, _quat, _S, top4  # noqa: E402

ARM = ("upperarm", "lowerarm", "hand", "thumb", "index", "middle", "ring", "pinky")


def _band(v, a, b, c, d):
    return _S((v - a) / (b - a)) * (1 - _S((v - c) / (d - c)))


def rest_globals(G):
    skin = G.g["skins"][0]
    names = [G.g["nodes"][j].get("name") for j in skin["joints"]]
    ibm = G.get(skin["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
    return names, ibm, {n: np.linalg.inv(ibm[i]) for i, n in enumerate(names)}


def add_bones(G):
    """The helpers into the glb (nodes, the skin's joints, inverse binds). Returns (frames, names)."""
    g = G.g
    skin = g["skins"][0]
    names, ibm, Grest = rest_globals(G)
    frames = hp.shoulder_rest(Grest)
    for n, f in frames.items():
        if n in names:
            continue
        pj = names.index(f["parent"])
        L = np.linalg.inv(Grest[f["parent"]]) @ f["G0"]
        R = L[:3, :3] / np.linalg.norm(L[:3, :3], axis=0)
        g["nodes"].append({"name": n, "rotation": [float(v) for v in _quat(R)], "translation": [float(v) for v in L[:3, 3]]})
        ni = len(g["nodes"]) - 1
        g["nodes"][skin["joints"][pj]].setdefault("children", []).append(ni)
        skin["joints"].append(ni)
        names.append(n)
        ibm = np.concatenate([ibm, np.linalg.inv(f["G0"])[None]])
    skin["inverseBindMatrices"] = G.append(ibm.transpose(0, 2, 1).reshape(-1, 16), 5126, "MAT4")
    return frames, names, Grest


def masks(P, Pall, Grest, s):
    """{helper kind: mask [V]} for side s at rest points P (Pall: all her body's points, for her silhouette's top)."""
    c = hp.SPEC["shoulder"]["weights"]
    sg = 1.0 if s == "l" else -1.0
    x, y, z = P[:, 0] * sg, P[:, 1], P[:, 2]
    J, E = Grest["upperarm_" + s][:3, 3], Grest["lowerarm_" + s][:3, 3]
    h = (E - J) / np.linalg.norm(E - J)
    top = np.array([abs(h[1]) * sg, abs(h[0]), 0.0])          # square to the humerus, up and out
    v = P - J
    t = v @ h
    r = v - t[:, None] * h
    rn = np.maximum(np.linalg.norm(r, axis=1), 1e-9)
    cc = (r @ top) / rn
    m = {}
    d = c["delt"]
    m["delt"] = _band(t, *d["t"]) * _S((cc - d["c"][0]) / (d["c"][1] - d["c"][0])) * (rn < d["r"])
    xa = Pall[:, 0] * sg
    bins = np.arange(0.03, 0.30, 0.005)
    near = (Pall[:, 1] < 1.63) & (np.abs(Pall[:, 2] + 0.03) < 0.07)
    tops = np.array([Pall[near & (np.abs(xa - b) < 0.0025), 1].max() if (near & (np.abs(xa - b) < 0.0025)).any() else np.nan for b in bins])
    ok = ~np.isnan(tops)
    dd = np.interp(x, bins[ok], tops[ok]) - y
    tp = c["trap"]
    m["trap"] = _band(x, *tp["x"]) * (1 - _S((dd - tp["d"][0]) / (tp["d"][1] - tp["d"][0])))
    p = c["pec"]
    m["pec"] = _S((x - p["x"][0]) / (p["x"][1] - p["x"][0])) * _band(y, *p["y"]) * _S((z - p["z"][0]) / (p["z"][1] - p["z"][0]))
    lt = c["lat"]
    m["lat"] = (_S((x - lt["x"][0]) / (lt["x"][1] - lt["x"][0])) * _band(y, *lt["y"])
                * (1 - _S((z - lt["z"][0]) / (lt["z"][1] - lt["z"][0]))) * _S((z - lt["z"][2]) / (lt["z"][3] - lt["z"][2])))
    return m


def reweight(P, W, names, Grest, frames, Pall):
    """Dense weights W [V, J] with each helper's share of its parent's weight moved to it."""
    W = W.copy()
    I = {n: i for i, n in enumerate(names)}
    for s in "lr":
        m = masks(P, Pall, Grest, s)
        m["pec"] = m["pec"] * (1 - hp.SPEC["shoulder"]["weights"]["pec"]["bre"] * _S(W[:, I["breast_" + s]] / 0.3))
        tot = m["pec"] + m["lat"]                  # (both from spine_03: never more than all of it)
        k = tot > 1
        m["pec"][k] /= tot[k]
        m["lat"][k] /= tot[k]
        for kind in hp.SPEC["shoulder"]["bones"]:
            n = f"{kind}_{s}"
            p = I[frames[n]["parent"]]
            mv = W[:, p] * m[kind]
            W[:, p] -= mv
            W[:, I[n]] += mv
    return W


def merge_cap(W, names, frames, cap=4):
    """Points with more than `cap` bones: the smallest folded into the largest of its own group (each side's arm, the
    torso, each clavicle and scapula alone; a helper in its parent's group), each group's total kept."""
    def grp(n):
        if n in frames:
            n = frames[n]["parent"]
        s = n[-2:] if n.endswith(("_l", "_r")) else ""
        if n.startswith(("clavicle_", "scap_")):
            return n
        if s and n.split("_")[0] in ARM:
            return "arm" + s
        return "torso"
    gs = [grp(n) for n in names]
    gid = np.array([sorted(set(gs)).index(x) for x in gs])
    W = W.copy()
    for v in np.nonzero((W > 1e-5).sum(1) > cap)[0]:
        w = W[v]
        while (w > 1e-5).sum() > cap:
            nz = np.nonzero(w > 1e-5)[0]
            k = nz[np.argmin(w[nz])]
            same = nz[(gid[nz] == gid[k]) & (nz != k)]
            if len(same):
                w[same[np.argmax(w[same])]] += w[k]
            w[k] = 0
    return W


def run(src, dst):
    G = Glb(src)
    g = G.g
    frames, names, Grest = add_bones(G)
    hn = [n for n in g["nodes"] if n.get("name") == "Heroine"][0]
    prims = g["meshes"][hn["mesh"]]["primitives"]
    Pall = np.concatenate([G.get(p["attributes"]["POSITION"]).astype(float) for p in prims])
    for p in prims:
        at = p["attributes"]
        assert "JOINTS_1" not in at
        P = G.get(at["POSITION"]).astype(float)
        J, Wt = G.get(at["JOINTS_0"]).astype(int), G.get(at["WEIGHTS_0"]).astype(float)
        D = np.zeros((len(P), len(names)))
        np.add.at(D, (np.repeat(np.arange(len(P)), J.shape[1]), J.ravel()), Wt.ravel())
        D2 = merge_cap(reweight(P, D, names, Grest, frames, Pall), names, frames)
        Jn, Wn = top4(D2)
        Jn[Wn == 0] = 0
        G.put(at["JOINTS_0"], Jn)
        G.put(at["WEIGHTS_0"], Wn.astype(np.float32))
        moved = {n: int((D2[:, names.index(n)] > 0.01).sum()) for n in frames}
        print("SHOULDER primitive", len(P), "points;", moved)
    g["asset"].setdefault("extras", {})["shoulder_rig"] = "body6 S2"
    G.save(dst)
    print("SHOULDER bones", [n for n in frames], "->", dst)


if __name__ == "__main__":
    if os.environ.get("SHOULDER_RIG", "0") != "1":
        import shutil
        shutil.copyfile(sys.argv[1], sys.argv[2])
        print("SHOULDER off (SHOULDER_RIG=1 builds it): copied")
    else:
        run(sys.argv[1], sys.argv[2])
