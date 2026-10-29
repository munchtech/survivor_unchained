"""Her scapula helpers built into a posted body (Body 6 S1; tools/anim/helpers.py SPEC "scap"), and her shoulder's
weights rewritten for them:

    python tools/assets/scap_rig_post.py <in heroine.glb> <out heroine.glb> [--report]

Run on the body after post_run.py (the neck graft and the other post steps write her weights after Blender's export,
so a weight change in the blend would be overwritten) and without the shoulder/axilla corrective shapes (the rig
replaces them; tools: body5's strip). Adds per side scap_{s}: a child of spine_03, no global rest turn, at the pivot
(her left; the right mirrored), appended to the skin's joints (her other meshes, sharing the skin, untouched). Then her
body's weights ("Heroine", every primitive), per side, in her rest space (x out from her midline):

1. Her trapezius' top (within `band` below the top of her silhouette, out to `out`): the arm's weight a smoothstep
   over arm_ramp (the clavicle-to-upper-arm blend over 60 mm, was 30), the clavicle's share of the rest a smoothstep
   from x0 to x1 (was 0 at x 0.10 to 0.67 at 0.14: a step that lifted the outer trapezius rigidly into a corner), the
   torso's what remains; each group's bones in the proportions she had (the twist chain's kept).
2. Her scapula's blade (behind blade_z, over blade_x/blade_y, eased over blade_fade): up to blade_max of the non-arm
   weight (clavicle and torso alike) to scap_{s}.
3. Four bones a point: the smallest folded into its own group's largest (each group's total kept), made whole.
Without SCAP_RIG=1 in the environment it copies the body unchanged (the build's gate, as TWIST_CHAIN)."""
import json
import os
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "anim"))
import helpers as hp  # noqa: E402

CT = {5126: np.float32, 5123: np.uint16, 5121: np.uint8, 5125: np.uint32}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def _S(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


class Glb:
    def __init__(s, path):
        d = open(path, "rb").read()
        jl = struct.unpack("<I", d[12:16])[0]
        s.g = json.loads(d[20:20 + jl])
        b0 = 20 + jl + 8
        s.bin = bytearray(d[b0:b0 + s.g["buffers"][0]["byteLength"]])

    def _at(s, ai):
        a = s.g["accessors"][ai]
        bv = s.g["bufferViews"][a["bufferView"]]
        dt, n = np.dtype(CT[a["componentType"]]), NC[a["type"]]
        assert bv.get("byteStride") in (None, dt.itemsize * n), "interleaved"
        return bv.get("byteOffset", 0) + a.get("byteOffset", 0), dt, n, a["count"]

    def get(s, ai):
        off, dt, n, c = s._at(ai)
        return np.frombuffer(bytes(s.bin[off:off + dt.itemsize * n * c]), dt).reshape(c, n).copy()

    def put(s, ai, x):
        off, dt, n, c = s._at(ai)
        b = np.ascontiguousarray(x, dtype=dt).tobytes()
        assert len(b) == dt.itemsize * n * c
        s.bin[off:off + len(b)] = b

    def append(s, arr, ctype, typ):
        """A new accessor (and buffer view) at the buffer's end; returns its index."""
        while len(s.bin) % 4:
            s.bin.append(0)
        b = np.ascontiguousarray(arr, dtype=CT[ctype]).tobytes()
        s.g["bufferViews"].append({"buffer": 0, "byteOffset": len(s.bin), "byteLength": len(b)})
        s.bin += b
        s.g["accessors"].append({"bufferView": len(s.g["bufferViews"]) - 1, "componentType": ctype,
                                 "count": int(len(arr)), "type": typ})
        s.g["buffers"][0]["byteLength"] = len(s.bin)
        return len(s.g["accessors"]) - 1

    def save(s, path):
        while len(s.bin) % 4:
            s.bin.append(0)
        s.g["buffers"][0]["byteLength"] = len(s.bin)
        js = json.dumps(s.g, separators=(",", ":")).encode()
        js += b" " * ((4 - len(js) % 4) % 4)
        body = struct.pack("<I", len(js)) + b"JSON" + js + struct.pack("<I", len(s.bin)) + b"BIN\x00" + bytes(s.bin)
        open(path, "wb").write(b"glTF" + struct.pack("<II", 2, 12 + len(body)) + body)


def _quat(m):
    """A rotation matrix's quaternion (x, y, z, w)."""
    t = np.trace(m)
    if t > 0:
        r = np.sqrt(1 + t) * 2
        return np.array([(m[2, 1] - m[1, 2]) / r, (m[0, 2] - m[2, 0]) / r, (m[1, 0] - m[0, 1]) / r, r / 4])
    i = int(np.argmax(np.diag(m)))
    j, k = (i + 1) % 3, (i + 2) % 3
    r = np.sqrt(1 + m[i, i] - m[j, j] - m[k, k]) * 2
    q = np.zeros(4)
    q[i] = r / 4
    q[j] = (m[j, i] + m[i, j]) / r
    q[k] = (m[k, i] + m[i, k]) / r
    q[3] = (m[k, j] - m[j, k]) / r
    return q


def add_bones(G):
    """scap_l/_r into the glb (nodes, the skin's joints, its inverse binds). Returns their joint indices."""
    g = G.g
    c = hp.SPEC["scap"]
    skin = g["skins"][0]
    names = [g["nodes"][j].get("name") for j in skin["joints"]]
    ibm = G.get(skin["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)   # (column-major in the file)
    pj = names.index(c["parent"])
    pn = skin["joints"][pj]
    Gp = np.linalg.inv(ibm[pj])
    out = {}
    for s in "lr":
        n = c["bone"].replace("{s}", s)
        if n in names:
            out[s] = names.index(n)
            continue
        Gs = np.eye(4)
        Gs[:3, 3] = hp.scap_pivot(s)
        L = np.linalg.inv(Gp) @ Gs
        R = L[:3, :3] / np.linalg.norm(L[:3, :3], axis=0)
        g["nodes"].append({"name": n, "rotation": [float(v) for v in _quat(R)], "translation": [float(v) for v in L[:3, 3]]})
        ni = len(g["nodes"]) - 1
        g["nodes"][pn].setdefault("children", []).append(ni)
        skin["joints"].append(ni)
        names.append(n)
        ibm = np.concatenate([ibm, np.linalg.inv(Gs)[None]])
        out[s] = len(names) - 1
    skin["inverseBindMatrices"] = G.append(ibm.transpose(0, 2, 1).reshape(-1, 16), 5126, "MAT4")
    return out, names


def reweight(P, W, names, report=None, Pall=None):
    """Her shoulder's weights (the module's 1-2) on dense weights W [V, J] at rest points P [V, 3] (Pall: all her
    body's points, for the top of her silhouette; P if None)."""
    Pall = P if Pall is None else Pall
    c = dict(hp.SPEC["scap"]["weights"])
    for k in ("band", "arm_ramp", "out"):    # (env overrides for trials: SCAP_BAND="0.015,0.05")
        if os.environ.get("SCAP_" + k.upper()):
            c[k] = [float(v) for v in os.environ["SCAP_" + k.upper()].split(",")]
    I = {n: i for i, n in enumerate(names)}
    W = W.copy()
    for s, sg in (("l", 1.0), ("r", -1.0)):
        x = P[:, 0] * sg
        xa = Pall[:, 0] * sg
        arm = np.array([n.startswith(("upperarm_", "lowerarm_", "hand_")) and n.endswith("_" + s) for n in names])
        arm |= np.array([n.split("_")[0] in ("thumb", "index", "middle", "ring", "pinky") and n.endswith("_" + s) for n in names])
        cl, sc = I["clavicle_" + s], I["scap_" + s]
        torso = ~arm
        torso[[cl, sc]] = False
        # the top of her silhouette (front view) by x: the highest point per 5 mm, her head left out
        bins = np.arange(0.03, 0.30, 0.005)
        near = (Pall[:, 1] < 1.63) & (np.abs(Pall[:, 2] + 0.03) < 0.07)
        top = np.array([Pall[near & (np.abs(xa - b) < 0.0025), 1].max() if (near & (np.abs(xa - b) < 0.0025)).any() else np.nan for b in bins])
        ok = ~np.isnan(top)
        h = np.interp(x, bins[ok], top[ok])
        d = h - P[:, 1]
        b0, b1 = c["band"]
        o0, o1 = c["out"]
        m = (1 - _S((d - b0) / (b1 - b0))) * (1 - _S((x - o0) / (o1 - o0))) * (x > 0.0)
        a_t = _S((x - c["arm_ramp"][0]) / (c["arm_ramp"][1] - c["arm_ramp"][0]))
        g_t = (1 - a_t) * _S((x - c["x0"]) / (c["x1"] - c["x0"]))
        t_t = 1 - a_t - g_t
        k = m > 1e-6
        Wk = W[k]
        A_old, T_old = Wk[:, arm].sum(1), Wk[:, torso].sum(1)
        tgt = np.zeros_like(Wk)
        # the arm's bones as she had them (where she had none: the share and the first twist, as at the joint)
        ap = np.where(A_old[:, None] > 1e-3, Wk[:, arm] / np.maximum(A_old[:, None], 1e-12), 0)
        ref = np.zeros(arm.sum())
        an = [n for n, a in zip(names, arm) if a]
        ref[an.index("upperarm_share_" + s)] = 0.6
        ref[an.index("upperarm_twist_01_" + s)] = 0.4
        ap[A_old <= 1e-3] = ref
        tgt[:, arm] = ap * a_t[k, None]
        # the torso's: her own bones' weights kept (cut back alike where there is less to share), what's added
        # going to spine_03, so her neck and head (the graft's) gain none here (a head turn would drag her shoulder)
        tw = Wk[:, torso] * np.minimum(1.0, t_t[k] / np.maximum(T_old, 1e-12))[:, None]
        tw[:, list(np.nonzero(torso)[0]).index(I["spine_03"])] += t_t[k] - tw.sum(1)
        tgt[:, torso] = tw
        tgt[:, cl] = g_t[k]
        W[k] = (1 - m[k, None]) * Wk + m[k, None] * tgt
        # the blade
        f0 = c["blade_fade"]
        fx = 1 - _S((np.maximum(c["blade_x"][0] - x, x - c["blade_x"][1])) / f0)
        fy = 1 - _S((np.maximum(c["blade_y"][0] - P[:, 1], P[:, 1] - c["blade_y"][1])) / f0)
        fz = _S((c["blade_z"] - P[:, 2]) / f0)
        f = c["blade_max"] * fx * fy * fz * (x > 0.0)
        na = ~arm
        na[sc] = False
        mv = W[:, na] * f[:, None]
        W[:, na] -= mv
        W[:, sc] += mv.sum(1)
        if report is not None:
            report[s] = dict(band=int((m > 0.01).sum()), blade=int((f > 0.01).sum()))
    return W


def merge_cap(W, names, cap=4):
    """Points with more than `cap` bones: the smallest folded into the largest bone of its own group (each side's
    arm, the torso; the clavicles and scapulae alone), so each group's total, the smooth ramps above, is kept."""
    grp = []
    for n in names:
        s = n[-2:] if n.endswith(("_l", "_r")) else ""
        if n.startswith(("clavicle_", "scap_")):
            grp.append(n)
        elif s and n.split("_")[0] in ("upperarm", "lowerarm", "hand", "thumb", "index", "middle", "ring", "pinky"):
            grp.append("arm" + s)
        else:
            grp.append("torso")
    gid = np.array([sorted(set(grp)).index(x) for x in grp])
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


def top4(W):
    top = np.argsort(-W, 1)[:, :4]
    tw = np.clip(np.take_along_axis(W, top, 1), 0, None)
    tw[tw < 1e-5] = 0
    tw /= tw.sum(1, keepdims=True)
    return top, tw


def run(src, dst):
    G = Glb(src)
    g = G.g
    js, names = add_bones(G)
    hn = [n for n in g["nodes"] if n.get("name") == "Heroine"][0]
    rep = {}
    prims = g["meshes"][hn["mesh"]]["primitives"]
    Pall = np.concatenate([G.get(p["attributes"]["POSITION"]).astype(float) for p in prims])
    for p in prims:
        at = p["attributes"]
        assert "JOINTS_1" not in at
        P = G.get(at["POSITION"]).astype(float)
        J, Wt = G.get(at["JOINTS_0"]).astype(int), G.get(at["WEIGHTS_0"]).astype(float)
        D = np.zeros((len(P), len(names)))
        np.add.at(D, (np.repeat(np.arange(len(P)), J.shape[1]), J.ravel()), Wt.ravel())
        D2 = merge_cap(reweight(P, D, names, rep, Pall), names)
        Jn, Wn = top4(D2)
        Jn[Wn == 0] = 0
        G.put(at["JOINTS_0"], Jn)
        G.put(at["WEIGHTS_0"], Wn.astype(np.float32))
        print("SCAP primitive", len(P), "points;", int((np.abs(D2 - D).max(1) > 1e-4).sum()), "reweighted", rep)
    g["asset"].setdefault("extras", {})["scap_rig"] = "body6 S1"
    G.save(dst)
    print("SCAP bones", js, "->", dst)


if __name__ == "__main__":
    if os.environ.get("SCAP_RIG", "0") != "1":
        import shutil
        shutil.copyfile(sys.argv[1], sys.argv[2])
        print("SCAP off (SCAP_RIG=1 builds it): copied")
    else:
        run(sys.argv[1], sys.argv[2])
