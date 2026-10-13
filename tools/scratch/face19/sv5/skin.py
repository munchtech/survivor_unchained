"""skin.py: her hair's vertices as drawn, offline: bones fitted from a HAIRDUMP frame's balls and head, linear blend skinning,
then the shader (chain swing, card turn). verts(d, x, style, turnfn) -> world positions of the moving vertices."""
import json, numpy as np
from mesh import load as mload, ART
from turn import turns, rot
def kabsch(A, B):
    """R (3x3) with R @ A[i] ~ B[i] (unit-free directions)."""
    H = np.array(A).T @ np.array(B); U, S, Vt = np.linalg.svd(H); D = np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ U.T))])
    return Vt.T @ D @ U.T
class Hair:
    def __init__(s, style, prim="hair"):
        prims, joints = mload(style); p = [q for q in prims if q["mat"] == prim][0]
        m = p["UV2"][:, 1] > 0
        s.P, s.UV2, s.J, s.W = p["P"][m].astype(float), p["UV2"][m].astype(float), p["J"][m], p["W"][m].astype(float)
        s.joints = joints
        ch = json.load(open(ART + "heroine_hair_%s.chain.json" % style))
        s.balls = [(b["bone"], np.array(b["at"])) for b in ch["spheres"]]; s.rest = np.array(ch["points"]); s.bone = ch["bone"]
        g = json.load(open(ART + "heroine_hair_%s.gltf" % style)); sk = g["skins"][0]
        a = g["accessors"][sk["inverseBindMatrices"]]; bv = g["bufferViews"][a["bufferView"]]
        buf = open(ART + g["buffers"][0]["uri"], "rb").read()
        ibm = np.frombuffer(buf, np.float32, 16 * a["count"], bv.get("byteOffset", 0) + a.get("byteOffset", 0)).reshape(-1, 4, 4).transpose(0, 2, 1)
        s.ibm = {joints[k]: ibm[k].astype(float) for k in range(len(joints))}
    def bones(s, d):
        """name -> 4x4 world transform of (pose * rest^-1), i.e. skeleton rest space -> world."""
        T = {}
        def mk(R, sc, At, at):
            M = np.eye(4); M[:3, :3] = R * sc; M[:3, 3] = at - (R * sc) @ At; return M
        for name in ("spine_03", "spine_02", "spine_01"):
            idx = [k for k, (b, _) in enumerate(s.balls) if b == name]
            k = idx[0]; ac = d["across"][k]; sc = np.linalg.norm(ac) / 0.06
            R = kabsch([[1, 0, 0], [0, 0, -1]], [ac / np.linalg.norm(ac), d["back"][k]])
            T[name] = mk(R, sc, s.balls[k][1], d["at"][k])
        sc = T["spine_03"][:3, :3].dot([1, 0, 0]); sc = np.linalg.norm(sc)
        idx = [k for k, (b, _) in enumerate(s.balls) if b == "neck_01"]
        a1, a2 = s.balls[idx[0]][1], s.balls[idx[1]][1]; w1, w2 = d["at"][idx[0]], d["at"][idx[1]]
        u = (a2 - a1) / np.linalg.norm(a2 - a1); v = (w2 - w1) / np.linalg.norm(w2 - w1)
        R = kabsch([u, [0, 0, -1]], [v, d["back"][idx[0]]]); T["neck_01"] = mk(R, sc, a1, w1)
        h = d["head"]; P = np.eye(4); P[:3, 0], P[:3, 1], P[:3, 2], P[:3, 3] = h[1], h[2], h[3], h[0]
        T["Head"] = P @ s.ibm["Head"]
        T["pelvis"] = T["spine_01"]; T["root"] = T["spine_01"]
        return T
    def skinned(s, d):
        T = s.bones(d); out = np.zeros_like(s.P); ph = np.c_[s.P, np.ones(len(s.P))]
        for k in range(4):
            for j in np.unique(s.J[:, k]):
                m = (s.J[:, k] == j) & (s.W[:, k] > 0)
                if not m.any(): continue
                Tj = T.get(s.joints[j], T["spine_03"])
                out[m] += s.W[m, k, None] * (ph[m] @ Tj.T)[:, :3]
        return out
    def drawn(s, d, x, qs=None, offs=None):
        """the shader: VERTEX += (swing + R o - o) * w; qs: per point quaternions (None: no turn); offs(o, dlt, i, f): edit R o - o."""
        v = s.skinned(d); tg = d["target"]
        sv = np.clip(s.UV2[:, 0], 0, 1) * 7; i = np.minimum(np.floor(sv).astype(int), 6); f = sv - i
        sw = (x - tg)[i] * (1 - f[:, None]) + (x - tg)[i + 1] * f[:, None]
        o = v - (tg[i] * (1 - f[:, None]) + tg[i + 1] * f[:, None])
        dl = np.zeros_like(v)
        if qs is not None:
            q0, q1 = qs[i], qs[i + 1]; sg = np.sign(np.sum(q0 * q1, 1)); sg[sg == 0] = 1
            q = q0 * (1 - f[:, None]) + q1 * sg[:, None] * f[:, None]; q /= np.linalg.norm(q, axis=1)[:, None]
            u = q[:, 1:]; w = q[:, :1]
            ro = o + 2 * np.cross(u, np.cross(u, o) + w * o)
            dl = ro - o
            if offs is not None: dl = offs(o, dl, i, f)
        return v + (sw + dl) * s.UV2[:, 1:2], v
