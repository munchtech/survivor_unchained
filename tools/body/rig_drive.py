"""The rig's drivers and correctives: the reference implementation the game ports to C# (rig.json "poser":
"tools.body.rig_drive"). Pure functions of the ANIMATED bones (clips key the core bones; helpers are never keyed),
each law a small formula driven by rig.json data, so the check, the build and the game evaluate them identically.

    drive(poser, G, rig) -> (G, {shape: weight})
    poser: names, index, parent, rest [B,4,4] (bone rest worlds), subtree(j);  G [B,4,4] the posed bone worlds.

Order (rig.json "helpers" rows run in list order, after "girdle"):
  girdle        per side, from the arm's elevation A (the humerus' angle from the torso's down axis, deg):
                  clavicle elevation  c_max * (S(A) - S(A_rest)),  S a smoothstep over [a0, a1]   (about her front)
                  scapula upward rot  k * (r(A) - r(A_rest)), r(A) = A - a0 eased (quadratic over `ease`), <= max
                                      (about the scapular plane's normal, at the scap's head)
                  scap glide          glide_m * (d . front)  (protraction forward as the arm flexes)
                the upper arm keeps its world turn (the clip's aim), riding the lifted clavicle.
  unroll        the bone's own roll about its line (beyond its parent's) handed to its child: forearm (ulna on a
                hinge) and calf; the child keeps its world turn.
  counter_twist the follow bone's roll about the helper's line (beyond its parent's), undone by `amount`
                (upper arm chain 0.5 (1 - t): half at the shoulder, none at the elbow; thigh 0.7 (1 - t)).
  twist         the follow bone's roll about the helper's line, taken by `amount` (the forearm's 0.4 / 0.8 of the
                hand's roll as the radius rolls; the calf's of the foot's).
  share         `amount` of the follow bone's turn beyond its parent, about a PIVOT `pivot` m toward the crease
                (the follow bone's rest Z times `crease`), stretched across the bend (along the crease axis) by
                k = min(1 + bulge (1 - cos(b / 2)), bulge_max), b the bend from rest (deg).
  point         a share whose result is pushed away from the crease by push * smoothstep((F - from) / (to - from)),
                F the joint's absolute flexion (deg, the angle between the bones): the olecranon, the patella.
  aim           a muscle helper (delt, trap, pec, lat, glute): g = smoothstep over `A` of the `on` bone's
                elevation; turned `turn` of the way the aim point (on's head + aim_m along on) swung from rest,
                about the helper's head; scaled 1 + sp g across and 1 + sa g along its Y; moved off g (m, world,
                turned with its parent). Neutral at and below A[0].
Correctives (rig.json "correctives"; shapes are rest-space deltas added before skinning):
  "law": "flex"  the joint's absolute flexion F (deg, proximal head->joint vs joint->distal head); sorted keys
                 k_0 < ... < k_n with a shape each (null at the rest angle: no shape); between k_i and k_i+1,
                 t = smoothstep((F - k_i) / (k_i+1 - k_i)) gives k_i 1 - t and k_i+1 t; held past either end:
                 a partition of one, exact at each key, smooth in-betweens.
  "law": "rbf"   the bone's direction d in its parent's frame; keys k_j (unit, k_0 the rest direction, no shape);
                 phi(d) = exp(-(angle(d, k_j) / sigma)^2); w = clip(phi(d) @ M, 0, 1), M = Phi^-1 (Phi_jk =
                 phi(k_j, k_k)) times the key-to-shape table: exact at the keys (1 on its own, 0 on the others);
                 w < 1e-5 is 0 (the rest exactly unchanged).
  legacy rows    ({"bone", "keys": [lo, at, hi]} or {"from", "to"}): as before (godot/art/people/rig_helpers.json).
"""
from __future__ import annotations

import math

import numpy as np


# ------------------------------------------------------------------ algebra --
def _unit(M):
    M = M[:3, :3]
    return M / np.linalg.norm(M, axis=0)


def _n(v):
    return v / max(np.linalg.norm(v), 1e-12)


def _rotvec(R):
    c = np.clip((np.trace(R) - 1) / 2, -1, 1)
    a = np.arccos(c)
    if a < 1e-9:
        return np.zeros(3)
    v = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]])
    n = np.linalg.norm(v)
    if n < 1e-9:
        w, U = np.linalg.eigh((R + np.eye(3)) / 2)
        return U[:, -1] * a
    return v / n * a


def _expm(v):
    a = np.linalg.norm(v)
    if a < 1e-12:
        return np.eye(3)
    k = v / a
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K


def _arc(a, b):
    """The shortest turn taking unit a to unit b."""
    v = np.cross(a, b)
    s = np.linalg.norm(v)
    c = float(np.clip(a @ b, -1, 1))
    if s < 1e-12:
        return np.eye(3)
    return _expm(v / s * math.atan2(s, c))


def _roll(Rd, y):
    """The twist of rotation Rd about axis y (swing-twist), radians."""
    v = _rotvec(Rd)
    a = np.linalg.norm(v)
    if a < 1e-12:
        return 0.0
    q = np.concatenate([np.sin(a / 2) * v / a, [np.cos(a / 2)]])
    return 2 * np.arctan2(q[:3] @ y, q[3])


def smooth(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def _about(c, M3):
    """The 4x4 that applies M3 (3x3) about the point c."""
    A = np.eye(4)
    A[:3, :3] = M3
    A[:3, 3] = c - M3 @ c
    return A


def _apply(poser, G, j, A):
    """A (world 4x4) applied to bone j and its subtree."""
    for k in poser.subtree(j):
        G[k] = A @ G[k]


def _turn(G, R0, j):
    """Bone j's world turn from its rest (3x3)."""
    return _unit(G[j]) @ _unit(R0[j]).T


def _carried(poser, G, j):
    """Bone j's world as its parent carries it (no own motion)."""
    p = poser.parent[j]
    return G[p] @ np.linalg.inv(poser.rest[p]) @ poser.rest[j]


def head(G, j):
    return G[j][:3, 3]


def _child_head(poser, G, j, child):
    return G[poser.index[child]][:3, 3] if child else G[j][:3, 3] + _unit(G[j])[:, 1] * 0.1


# ------------------------------------------------------------------ readings --
def elevation(poser, G, s, rig):
    """The upper arm's angle (deg) from the torso's down axis (spine_05's turn applied to her rest down)."""
    gd = rig["girdle"]
    I = poser.index
    j, c = I[gd["arm"].replace("{s}", s)], I[gd["arm_end"].replace("{s}", s)]
    down = _turn(G, poser.rest, I[gd["torso"]]) @ np.asarray(gd["down"], float)
    d = _n(head(G, c) - head(G, j))
    return math.degrees(math.acos(float(np.clip(d @ down, -1, 1))))


def flexion(poser, G, prox, joint, dist):
    """A joint's absolute flexion (deg): proximal head -> joint head against joint head -> distal head."""
    I = poser.index
    u = _n(head(G, I[joint]) - head(G, I[prox]))
    d = _n(head(G, I[dist]) - head(G, I[joint]))
    return math.degrees(math.acos(float(np.clip(u @ d, -1, 1))))


def direction(poser, G, bone, end, frame):
    """Bone's direction (head -> end's head) in `frame`'s rest-aligned frame: frame's world turn from rest undone."""
    I = poser.index
    d = _n(head(G, I[end]) - head(G, I[bone]))
    return _turn(G, poser.rest, I[frame]).T @ d


# ------------------------------------------------------------------- helpers --
def _ramp(x, a0, ease):
    x = x - a0
    if x <= 0:
        return 0.0
    return x * x / (2 * ease) if x < ease else x - ease / 2


def girdle(poser, G, rig, s):
    gd = rig["girdle"]
    I = poser.index
    sg = 1.0 if s == "l" else -1.0
    cl, sc, arm = (I[gd[k].replace("{s}", s)] for k in ("clavicle", "scap", "arm"))
    A = elevation(poser, G, s, rig)
    A0 = elevation(poser, poser.rest, s, rig)
    Rt = _turn(G, poser.rest, I[gd["torso"]])
    front = Rt @ np.asarray(gd["front"], float)
    a0, a1 = gd["clav_A"]
    S = lambda a: smooth((a - a0) / (a1 - a0))
    th_c = gd["clav_max"] * (S(A) - S(A0))
    arm_old = G[arm].copy()
    if abs(th_c) > 1e-9:
        _apply(poser, G, cl, _about(head(G, cl), _expm(front * sg * math.radians(th_c))))
        # the upper arm keeps its world turn (the clip's aim), riding the lifted clavicle
        new = arm_old.copy()
        new[:3, 3] = G[arm][:3, 3]
        _apply(poser, G, arm, new @ np.linalg.inv(G[arm]))
    k, b0, ease, mx = gd["scap_per_deg"], gd["scap_from"], gd["scap_ease"], gd["scap_max"]
    th_s = k * (min(_ramp(A, b0, ease), mx / k) - min(_ramp(A0, b0, ease), mx / k))
    n = np.asarray(gd["scap_axis"], float) * np.array([sg, 1.0, 1.0])
    n = Rt @ _n(n)
    if abs(th_s) > 1e-9:
        _apply(poser, G, sc, _about(head(G, sc), _expm(n * sg * math.radians(th_s))))
    d = _n(head(G, I[gd["arm_end"].replace("{s}", s)]) - head(G, arm))
    d0 = _n(head(poser.rest, I[gd["arm_end"].replace("{s}", s)]) - head(poser.rest, arm))
    glide = gd["glide_m"] * (d @ front - (Rt @ d0) @ front)
    if abs(glide) > 1e-12:
        T = np.eye(4)
        T[:3, 3] = front * glide
        _apply(poser, G, sc, T)
    return {"A": A, "clav_deg": th_c, "scap_deg": th_s}


def _rel(G, R0, j, p):
    return _turn(G, R0, p).T @ _turn(G, R0, j)       # j's turn beyond its parent's (rest-aligned)


def helper(poser, G, h, s, info):
    I = poser.index
    R0 = poser.rest
    nm = h["name"].replace("{s}", s)
    j = I.get(nm)
    if j is None:
        return
    kind = h["kind"]
    if kind == "unroll":                               # j's own roll handed to its child (the child keeps its turn)
        ch = I[h["child"].replace("{s}", s)]
        p = poser.parent[j]
        y = _unit(G[j])[:, 1]
        ang = _roll(_turn(G, R0, j) @ _turn(G, R0, p).T, y)
        if abs(ang) < 1e-12:
            return
        keep = {k: G[k].copy() for k in poser.subtree(ch)}
        _apply(poser, G, j, _about(head(G, j), _expm(-y * ang)))
        for k, M in keep.items():
            G[k] = M
        return
    if kind == "aim":
        p = poser.parent[j]
        on = I[h["on"].replace("{s}", s)]
        A = info.get(("A", s))
        if h.get("read") == "hip":
            A = flexion_from_down(poser, G, on, h, s)
        g = smooth((A - h["A"][0]) / (h["A"][1] - h["A"][0])) if A is not None else 0.0
        if g <= 0:
            return
        Gc = G[j].copy()
        hj = head(G, j)
        end = _child_head(poser, G, on, h.get("on_end", "").replace("{s}", s) or None)
        aim = head(G, on) + float(h.get("aim_m", 0.0)) * _n(end - head(G, on))
        # the same aim at rest, carried by the helper's parent: its swing since rest
        end0 = _child_head(poser, R0, on, h.get("on_end", "").replace("{s}", s) or None)
        aim0 = head(R0, on) + float(h.get("aim_m", 0.0)) * _n(end0 - head(R0, on))
        Cp = G[p] @ np.linalg.inv(R0[p])
        aim0w = (Cp @ np.append(aim0, 1.0))[:3]
        Rsw = _arc(_n(aim0w - hj), _n(aim - hj))
        R = _expm(g * float(h.get("turn", 0.0)) * _rotvec(Rsw))
        y = R @ _unit(Gc)[:, 1]
        Sc = (1 + g * float(h.get("sp", 0.0))) * np.eye(3) + g * (float(h.get("sa", 0.0)) - float(h.get("sp", 0.0))) * np.outer(y, y)
        M = _about(hj, Sc @ R)
        M[:3, 3] += Cp[:3, :3] @ (g * np.asarray(h.get("off", [0, 0, 0]), float) * np.array([1.0 if s == "l" else -1.0, 1, 1]))
        G[j] = M @ Gc
        return
    f = I[h["follow"].replace("{s}", s)]
    p = poser.parent[j]
    a = float(h.get("amount", 0.0))
    if kind in ("counter_twist", "twist"):
        y = _unit(G[j])[:, 1]
        if kind == "counter_twist":
            pf = poser.parent[f]
            ang = -a * _roll(_turn(G, R0, f) @ _turn(G, R0, pf).T, y)
        else:
            ang = a * _roll(_turn(G, R0, f) @ _turn(G, R0, p).T, y)
        if abs(ang) > 1e-12:
            _apply(poser, G, j, _about(head(G, j), _expm(y * ang)))
        return
    if kind in ("share", "point"):
        Gc = _carried(poser, G, j)                    # the share as its parent carries it
        G[j] = Gc
        Rp = _turn(G, R0, p)
        Rrel = _rel(G, R0, f, p)
        rv = _rotvec(Rrel)
        Rh = Rp @ _expm(a * rv) @ Rp.T                 # the half turn, in the world
        z = Rp @ (_unit(R0[f])[:, 2] * float(h.get("crease", 1.0)))
        c = head(G, j) + float(h.get("pivot", 0.0)) * z
        b = math.degrees(np.linalg.norm(rv))
        k = min(1.0 + float(h.get("bulge", 0.0)) * (1.0 - math.cos(math.radians(min(b, 180.0)) / 2)),
                float(h.get("bulge_max", 1.0)))
        zz = Rh @ z
        Sw = np.eye(3) + (k - 1.0) * np.outer(zz, zz)
        tp = head(G, j) + float(h.get("turn_pivot", 0.0)) * z      # the turn's centre (0: the joint's head)
        M = _about(c, Sw) @ _about(tp, Rh)                          # turned about tp, stretched about the pivot
        if kind == "point":
            F = flexion(poser, G, *[x.replace("{s}", s) for x in h["flex"]])
            push = float(h["push"]) * smooth((F - h["from"]) / (h["to"] - h["from"]))
            M[:3, 3] -= push * zz
        G[j] = M @ Gc
        return
    raise ValueError(f"unknown helper kind {kind}")


def flexion_from_down(poser, G, on, h, s):
    """The thigh's angle (deg) from the pelvis' rest down axis, carried by the pelvis (hip flexion, any plane)."""
    I = poser.index
    p = I[h["torso"]]
    down = _turn(G, poser.rest, p) @ np.asarray(h["down"], float)
    end = I[h["on_end"].replace("{s}", s)]
    d = _n(head(G, end) - head(G, on))
    return math.degrees(math.acos(float(np.clip(d @ down, -1, 1))))


# --------------------------------------------------------------- correctives --
def flex_weights(F, keys):
    """Smoothstep hats over the sorted keys: [w per key], a partition of one (held at either end)."""
    w = np.zeros(len(keys))
    if F <= keys[0]:
        w[0] = 1.0
    elif F >= keys[-1]:
        w[-1] = 1.0
    else:
        i = int(np.searchsorted(keys, F, side="right")) - 1
        t = smooth((F - keys[i]) / (keys[i + 1] - keys[i]))
        w[i], w[i + 1] = 1.0 - t, t
    return w


def rbf_phi(d, K, sigma_deg):
    ang = np.degrees(np.arccos(np.clip(np.asarray(K) @ d, -1, 1)))
    return np.exp(-(ang / sigma_deg) ** 2)


def rbf_solve(K, sigma_deg):
    """M [n_keys, n_shapes]: key 0 the rest (no shape), key j>0 shape j-1."""
    K = np.asarray(K, float)
    Phi = np.stack([rbf_phi(k, K, sigma_deg) for k in K])
    Y = np.zeros((len(K), len(K) - 1))
    Y[1:] = np.eye(len(K) - 1)
    return np.linalg.solve(Phi, Y)


def corrective_weights(poser, G, rig):
    out = {}
    for c in rig.get("correctives", []):
        law = c.get("law")
        sides = ("l", "r") if "{s}" in json_dump(c) else ("",)
        for s in sides:
            sub = lambda x: x.replace("{s}", s)
            if law == "flex":
                if any(sub(b) not in poser.index for b in c["bones"]):
                    continue
                F = flexion(poser, G, *[sub(b) for b in c["bones"]])
                w = flex_weights(F, c["keys"])
                for nm, x in zip(c["shapes"], w):
                    if nm:
                        out[sub(nm)] = float(x)
            elif law == "rbf":
                if sub(c["bone"]) not in poser.index:
                    continue
                d = direction(poser, G, sub(c["bone"]), sub(c["end"]), sub(c["frame"]))
                K = np.asarray(c["keys"][s or "l"], float)
                w = np.clip(rbf_phi(d, K, c["sigma_deg"]) @ np.asarray(c["M"][s or "l"], float), 0.0, 1.0)
                w = np.where(w < 1e-5, 0.0, w)      # exactly 0 at the rest key (the solve leaves ~1e-7)
                for nm, x in zip(c["shapes"], w):
                    out[sub(nm)] = float(x)
            else:
                b = sub(c["bone"])
                j = poser.index.get(b)
                if j is not None:
                    out[sub(c["name"])] = legacy_weight(c, angle_of(poser, G, j, c.get("on", "swing")))
    return out


def json_dump(c):
    import json
    return json.dumps(c)


# legacy table rows (godot/art/people/rig_helpers.json "correctives")
def _local(poser, G, j):
    p = poser.parent[j]
    return G[j] if p < 0 else np.linalg.inv(G[p]) @ G[j]


def angle_of(poser, G, j, on="swing"):
    R0 = _unit(_local(poser, poser.rest, j))
    R1 = _unit(_local(poser, G, j))
    d = R0.T @ R1
    if on == "angle":
        return math.degrees(math.acos(max(-1.0, min(1.0, (np.trace(d) - 1) / 2))))
    y = d[:, 1]
    if on == "flex":
        return math.degrees(math.atan2(y[2], y[1]))
    return math.degrees(math.acos(max(-1.0, min(1.0, y[1]))))


def legacy_weight(c, deg):
    if "keys" in c:
        lo, at, hi = (float(x) for x in c["keys"])
        if deg <= lo:
            return 0.0
        if deg < at:
            return (deg - lo) / (at - lo)
        if hi <= at:
            return 1.0
        return max(0.0, 1.0 - (deg - at) / (hi - at))
    t = min(max((deg - c["from"]) / (c["to"] - c["from"]), 0.0), 1.0)
    return t * t * (3 - 2 * t) if c.get("smoothstep", True) else t


weight = legacy_weight


# --------------------------------------------------------------------- drive --
def drive_helpers(poser, G, rig):
    G = G.copy()
    info = {}
    if "girdle" in rig:
        for s in ("l", "r"):
            r = girdle(poser, G, rig, s)
            info[("A", s)] = r["A"]
    for h in rig.get("helpers", []):
        for s in (("l", "r") if "{s}" in h["name"] else ("",)):
            helper(poser, G, h, s, info)
    return G, info


def drive(poser, G, rig):
    G, _ = drive_helpers(poser, G, rig)
    return G, corrective_weights(poser, G, rig)
