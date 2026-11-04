"""Stage 4: tools/body/skeleton.json placed on a MakeHuman body (any slider body: the landmarks are MakeHuman's).

    place_skeleton(skel_json, base, mh_rig, mh_weights, to_world) -> (names, parents, worlds [B,4,4] glTF, ends {name: (head, tail)}, info)
base: stage 1's arrays (MakeHuman space); mh_rig: MPFB's rigs/standard/rig.default.json (its head/tail rules);
mh_weights: weights.default.json "weights"; to_world(P_mh) -> glTF points (the placement, stage 2/3).
Only the left side is placed; the right is its true mirror (x -> -x; Y and Z mirrored, X = Y x Z), and the middle's
bones sit on x = 0 exactly.
"""
import numpy as np

UP, FRONT, LEFT = np.array([0.0, 1, 0]), np.array([0.0, 0, 1]), np.array([1.0, 0, 0])     # glTF: y up, front +z
MH_DIR = {"lateral": np.array([1.0, 0, 0]), "up": np.array([0.0, 0, 1]), "front": np.array([0.0, -1, 0]),
          "back": np.array([0.0, 1, 0])}                                                     # MakeHuman (z up, front -y), her left


def unit(v):
    v = np.asarray(v, float)
    return v / max(np.linalg.norm(v), 1e-12)


def perp(v, n):
    return unit(v - n * (v @ n))


def expand(x, s, S, X):
    if isinstance(x, str):
        return x.replace("{s}", s).replace("{S}", S).replace("{X}", X)
    if isinstance(x, list):
        return [expand(y, s, S, X) for y in x]
    if isinstance(x, dict):
        return {k: expand(v, s, S, X) for k, v in x.items()}
    return x


class Landmarks:
    """Points in MakeHuman space by skeleton.json's rules."""

    def __init__(self, base, mh_rig, mh_weights):
        self.V, self.g, self.rig, self.w = base["V"], base["groups"], mh_rig, mh_weights
        self.skin = self.V[base["inbody"]]

    def mh_end(self, bone, end):
        r = self.rig[bone][end]
        st = r["strategy"]
        if st == "CUBE":
            return self.cube(r["cube_name"])
        if st == "MEAN":
            return self.V[r["vertex_indices"]].mean(0)
        if st == "VERTEX":
            return self.V[r["vertex_index"]]
        raise ValueError(st)

    def cube(self, name):
        return self.V[self.g[name]].mean(0)

    def point(self, p):
        if "cube" in p:
            return self.cube(p["cube"])
        if "mh" in p:
            return self.mh_end(p["mh"], p["end"])
        if "mean" in p:
            return np.mean([self.point(q) for q in p["mean"]], 0)
        if "lerp" in p:
            a, b, t = p["lerp"]
            return (1 - t) * self.point(a) + t * self.point(b)
        if "origin" in p:
            return None
        if "skin_out" in p:
            q, way = p["skin_out"]
            o = self.point(q)
            d = MH_DIR[way].copy()
            if way == "lateral" and o[0] < 0:
                d = -d
            rel = self.skin - o
            along = rel @ d
            off = np.linalg.norm(rel - along[:, None] * d, axis=1)
            m = (off < 0.02) & (along > 0)
            return o + d * along[m].max()
        if "weights_base" in p:
            ww = dict((int(i), float(x)) for i, x in self.w[p["weights_base"]])
            idx = np.array([i for i, x in ww.items() if 0.05 < x < 0.35])
            return self.V[idx].mean(0)
        raise ValueError(p)


def place_skeleton(skel, base, mh_rig, mh_weights, to_world):
    lm = Landmarks(base, mh_rig, mh_weights)
    defs = skel["bones"]
    # the left side (and the middle), in MakeHuman space
    ends = {}
    for d in defs:
        e = expand(d, "l", "l", "L")
        if d.get("leaf"):
            continue
        ends[e["name"]] = [lm.point(e["head"]), lm.point(e["tail"])]
    # to the world (glTF)
    W = {}
    for n, (h, t) in ends.items():
        hw = np.zeros(3) if h is None else to_world(h[None])[0]
        tw = to_world(t[None])[0]
        if not n.endswith("_l"):
            hw[0] = 0.0
            tw[0] = 0.0
        W[n] = [hw, tw]
    for d in defs:
        if d.get("leaf"):
            e = expand(d, "l", "l", "L")
            ph, pt = W[e["parent"]]
            W[e["name"]] = [pt, pt + (pt - ph) / 3.0]
    # frames
    ya = unit(W["upperarm_l"][1] - W["upperarm_l"][0])
    yb = unit(W["lowerarm_l"][1] - W["lowerarm_l"][0])
    hinge = unit(np.cross(yb, -ya))                 # flexion (+X) takes the forearm toward the upper arm
    bend = float(np.degrees(np.arccos(np.clip(ya @ yb, -1, 1))))
    hand_y = unit(W["hand_l"][1] - W["hand_l"][0])

    def curl(chain):
        """The direction a finger's rest curl turns it (toward the palm)."""
        v = []
        for a, b in zip(chain, chain[1:]):
            y1, y2 = unit(W[a][1] - W[a][0]), unit(W[b][1] - W[b][0])
            v.append(y2 - y1 * (y1 @ y2))
        return unit(np.sum(v, 0))
    palm = unit(np.sum([curl([f"{f}_01_l", f"{f}_02_l", f"{f}_03_l"]) for f in ("index", "middle", "ring", "pinky")], 0))
    thumb = curl(["thumb_01_l", "thumb_02_l", "thumb_03_l"])

    def frame(d, Y):
        kind = d["frame"]
        if kind == "elbow_upper":
            X = perp(hinge, Y)
            return X, np.cross(X, Y)
        if kind == "elbow_lower":
            X = perp(hinge, Y)
            return X, np.cross(X, Y)
        if kind == "hand":
            X = perp(hinge, Y)
            return X, np.cross(X, Y)
        if kind == "knee":
            Z = perp(-FRONT, Y)
        elif kind == "palm":
            Z = perp(palm, Y)
        elif kind == "thumb":
            Z = perp(thumb if np.linalg.norm(thumb) > 0.5 else palm, Y)
        elif kind == "up":
            Z = perp(UP, Y) if abs(Y @ UP) < 0.7 else perp(FRONT, Y)
        else:
            Z = perp(FRONT, Y) if abs(Y @ FRONT) < 0.7 else perp(UP, Y)
        return np.cross(Y, Z), Z
    names, parents, worlds, ends_out = [], [], [], {}
    M = np.diag([-1.0, 1, 1])
    for d in defs:
        sides = ("l", "r") if "{s}" in d["name"] else ("",)
        for s in sides:
            e = expand(d, s or "l", s or "l", "L" if s != "r" else "R")
            nl = expand(d["name"], "l", "l", "L")
            h, t = W[nl]
            ends_out[e["name"]] = (M @ h, M @ t) if s == "r" else (h.copy(), t.copy())
            Y = unit(t - h)
            X, Z = frame(d, Y)
            G = np.eye(4)
            if s == "r":
                Y, Z, h = M @ Y, M @ Z, M @ h
                X = np.cross(Y, Z)
            G[:3, 0], G[:3, 1], G[:3, 2], G[:3, 3] = X, Y, Z, h
            names.append(e["name"])
            parents.append(e["parent"])
            worlds.append(G)
    idx = {n: i for i, n in enumerate(names)}
    par = [idx[p] if p else -1 for p in parents]
    info = {"bones": len(names), "elbow_rest_bend_deg": round(bend, 2), "hinge_l": [round(float(x), 4) for x in hinge],
            "palm_l": [round(float(x), 3) for x in palm]}
    return names, par, np.stack(worlds), ends_out, info
