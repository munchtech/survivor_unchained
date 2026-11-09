"""The rig's drivers and correctives: the reference implementation the game ports to C# (rig.json "poser":
"tools.body.rig_drive"). Pure functions of the ANIMATED bones (clips key the core bones; helpers are never keyed),
each law a small formula driven by rig.json data, so the check, the build and the game evaluate them identically.

    drive(poser, G, rig) -> (G, {shape: weight})
    poser: names, index, parent, rest [B,4,4] (bone rest worlds), subtree(j);  G [B,4,4] the posed bone worlds.

Order (rig.json "helpers" rows run in list order, after "girdle"):
  girdle        per side, the scapulohumeral rhythm from the arm's elevation A (the humerus' angle from the torso's
                down axis, deg) and its forward reach f (its direction . the torso's front), by tables (monotone C1
                cubics, flat past the ends), all relative to the rest (A0 ~43, f0): the clavicle's elevation and
                retraction (scaled by the plane, retract_plane: by forward reach above 95-120 deg of elevation;
                less a protraction per unit of reach) about its head, the scapula's upward rotation and
                posterior tilt about its head and its forward glide; the upper arm keeps its world turn (the clip's
                aim), riding the moved clavicle. girdle() has the formulas.
  unroll        the bone's own roll about its line (beyond its parent's) handed to its child: forearm (ulna on a
                hinge) and calf; the child keeps its world turn.
  counter_twist the follow bone's roll about the helper's line (beyond its parent's), undone by `amount`
                (upper arm chain 0.5 (1 - t): half at the shoulder, none at the elbow; thigh 0.7 (1 - t)).
  twist         the follow bone's roll about the helper's line, taken by `amount` (the forearm's 0.4 / 0.8 of the
                hand's roll as the radius rolls; the calf's of the foot's).
  share         `amount` of the follow bone's turn beyond its parent, about a PIVOT `pivot` m toward the crease
                (the follow bone's rest Z times `crease`), stretched across the bend (along the crease axis) by
                k = min(1 + bulge (1 - cos(b / 2)), bulge_max), b the bend from rest (deg). With "below"
                {"amount", "band"} the amount follows the girdle's arm elevation A (share_amount): `amount` above the
                rest A0, below.amount under it, smoothstep over A0 -+ band (the hanging cap rides the girdle).
  point         a share whose result is pushed away from the crease by push * smoothstep((F - from) / (to - from)),
                F the joint's absolute flexion (deg, the angle between the bones): the olecranon, the patella.
  aim           a muscle helper (delt, trap, pec, lat, glute): g = smoothstep over `A` of the `on` bone's
                elevation; turned `turn` of the way the aim point (on's head + aim_m along on) swung from rest,
                about the helper's head; scaled 1 + sp g across and 1 + sa g along its Y; moved off g (m, world,
                turned with its parent). Neutral at and below A[0].
  hand_clear    (rig.json "hand_clear", tools/body/hand_clear.py; after the girdle, before the rows; absent on the
                ref body) per side, the arm opened by the least turn at its head so the hand keeps its place against
                the thigh surface where this body's stands further out than the ref body's, by the hand's proximity.
                hand_clear() has the formulas.
Correctives (rig.json "correctives"; shapes are rest-space deltas added before skinning):
  "law": "flex"  the joint's absolute flexion F (deg, proximal head->joint vs joint->distal head); sorted keys
                 k_0 < ... < k_n with a shape each (null at the rest angle: no shape); between k_i and k_i+1,
                 t = smoothstep((F - k_i) / (k_i+1 - k_i)) gives k_i 1 - t and k_i+1 t; held past either end:
                 a partition of one, exact at each key, smooth in-betweens.
  "law": "rbf"   the bone's direction d in its parent's frame; keys k_j (unit, k_0 the rest direction, no shape);
                 phi(d) = exp(-(angle(d, k_j) / sigma)^2); w = clip(phi(d) @ M, 0, 1), M = Phi^-1 (Phi_jk =
                 phi(k_j, k_k)) times the key-to-shape table: exact at the keys (1 on its own, 0 on the others);
                 w < 1e-5 is 0 (the rest exactly unchanged).
  "law": "arc"   the "rbf" law's direction d; keys k_0 (the rest, no shape) .. k_n along ONE swing (the hip's flexion
                 arc, keyed every 15 deg): d's angle in the keys' plane (axis k_0 x k_n) from k_0 through the "flex"
                 smoothstep hats over the keys' angles (exact at each key, a partition of one, held past the last:
                 dense keys never ring as the Gaussian rbf's do: 5 keys 15 deg apart summed to 2.0 at 45 deg), times
                 a gate on d's angle out of that plane (1 within gate_deg[0], 0 past gate_deg[1], smoothstep).
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
def table(x, T):
    """A table's monotone C1 curve at x: T [[x_k, y_k], ...] (x_k rising); Hermite cubics with Fritsch-Butland slopes
    (0 where the neighbouring secants differ in sign: no overshoot), 0 slope at both end nodes and held flat past them
    (C1 everywhere)."""
    xs = [float(r[0]) for r in T]
    ys = [float(r[1]) for r in T]
    n = len(xs)
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    h = [xs[k + 1] - xs[k] for k in range(n - 1)]
    dl = [(ys[k + 1] - ys[k]) / h[k] for k in range(n - 1)]
    m = [0.0] * n
    for k in range(1, n - 1):
        if dl[k - 1] * dl[k] > 0:
            w1, w2 = 2 * h[k] + h[k - 1], h[k] + 2 * h[k - 1]
            m[k] = (w1 + w2) / (w1 / dl[k - 1] + w2 / dl[k])
    i = 0
    while x > xs[i + 1]:
        i += 1
    t = (x - xs[i]) / h[i]
    t2, t3 = t * t, t * t * t
    return ((2 * t3 - 3 * t2 + 1) * ys[i] + (t3 - 2 * t2 + t) * h[i] * m[i] + (-2 * t3 + 3 * t2) * ys[i + 1]
            + (t3 - t2) * h[i] * m[i + 1])


def retract_plane(A, reach, gd):
    """The retraction table's scale by the arm's elevation plane (gd "retract_plane", absent: 1): its forward reach
    beyond the rest (reach = d . front - d0 . front, the torso's frame; 0 in the frontal plane, abduction; ~0.5-0.7
    in flexion; up to ~0.4 at 135 in the scapular plane) read by the table "by_reach" [[reach, scale]] (monotone C1,
    flat ends), faded in over the arm's elevation A in "fade" [from, to] (smoothstep; under `from` the scale is 1:
    the hanging arm and the rest, where the plane is undefined, and flexion to 90, which keeps the full table). An
    azimuth (atan2 of forward and lateral) cannot serve: the check's flexion 135 from her A-pose sits at azimuth 35,
    the scapular plane, and its 90 at 47; the swing axis d0 x d reads 25 and 45."""
    rp = gd.get("retract_plane")
    if not rp:
        return 1.0
    g = smooth((A - rp["fade"][0]) / (rp["fade"][1] - rp["fade"][0]))
    if g <= 0:
        return 1.0
    return 1.0 + g * (table(reach, rp["by_reach"]) - 1.0)


def share_amount(h, A, A0):
    """A share's amount by the arm's elevation (h "below": {"amount", "band"}, absent: h "amount"): `amount` above the
    rest elevation A0, below["amount"] under it, smoothstep-blended over A0 -+ band (deg): no pop through the rest."""
    a = float(h.get("amount", 0.0))
    b = h.get("below")
    if not b or A is None:
        return a
    t = smooth((A - (A0 - b["band"])) / (2.0 * b["band"]))
    return float(b["amount"]) + t * (a - float(b["amount"]))


def girdle(poser, G, rig, s):
    """The scapulohumeral rhythm (rig.json "girdle", base_drive.json has the tables and their sources): per side, from
    the arm's elevation A and its forward reach f = d . front (d the upper arm's direction, front the torso's), all
    relative to the rest (A0, f0: the rest is exactly neutral):
      clavicle  elevation e = clav_elev(A) - clav_elev(A0)                    about the torso's front (per-side sign)
                retraction r = k (clav_retract(A) - clav_retract(A0)) - protract_per_reach (f - f0)  about its up (+ back),
                k = retract_plane(A, f - f0) (1 without "retract_plane")
                (both about the clavicle's head); the upper arm then keeps its world turn (the clip's aim)
      scapula   upward rotation u = scap_up(A) - scap_up(A0)                  about scap_axis (mirrored per side)
                posterior tilt p = scap_tilt(A) - scap_tilt(A0)               about the torso's side (+ top back)
                (both about the scapula's head, after the clavicle carried it); glide glide_m (f - f0) forward."""
    gd = rig["girdle"]
    I = poser.index
    sg = 1.0 if s == "l" else -1.0
    cl, sc, arm = (I[gd[k].replace("{s}", s)] for k in ("clavicle", "scap", "arm"))
    end = I[gd["arm_end"].replace("{s}", s)]
    A = elevation(poser, G, s, rig)
    A0 = elevation(poser, poser.rest, s, rig)
    Rt = _turn(G, poser.rest, I[gd["torso"]])
    front = Rt @ np.asarray(gd["front"], float)
    up = Rt @ np.asarray(gd["up"], float)
    side = Rt @ np.asarray(gd["side"], float)
    d = _n(head(G, end) - head(G, arm))
    d0 = _n(head(poser.rest, end) - head(poser.rest, arm))
    reach = float(d @ front - (Rt @ d0) @ front)
    th_e = table(A, gd["clav_elev"]) - table(A0, gd["clav_elev"])
    th_r = (retract_plane(A, reach, gd) * (table(A, gd["clav_retract"]) - table(A0, gd["clav_retract"]))
            - gd["protract_per_reach"] * reach)
    arm_old = G[arm].copy()
    if gd.get("clavicle_by") == "shrug":     # (P1 R1 arm chain: the clavicle is the clip's, lifted by A's HerShrug at runtime)
        th_e = th_r = 0.0
    if abs(th_e) > 1e-9 or abs(th_r) > 1e-9:
        Rc = _expm(up * sg * math.radians(th_r)) @ _expm(front * sg * math.radians(th_e))
        _apply(poser, G, cl, _about(head(G, cl), Rc))
        # the upper arm keeps its world turn (the clip's aim), riding the moved clavicle
        new = arm_old.copy()
        new[:3, 3] = G[arm][:3, 3]
        _apply(poser, G, arm, new @ np.linalg.inv(G[arm]))
    if gd.get("clavicle_roll") == "neutral":  # (P1 R1 arm chain round 27: the clips key A's clavicle, so the game's blends
        # and A's HerShrug run as A's; its roll about its own line beyond its neutral goes to the upper arm, which keeps
        # its world, so B's clavicle skin never takes A's roll. P1Rig.ClavicleRollNeutral)
        y = _unit(G[cl])[:, 1]
        ang = _roll(_turn(G, poser.rest, cl) @ _turn(G, poser.rest, poser.parent[cl]).T, y)
        if abs(ang) >= 1e-12:
            keep = {k: G[k].copy() for k in poser.subtree(arm)}
            # (P1 R1 round 30) "clavicle_roll_keep": helpers under the clavicle that keep the clip's roll (their world
            # kept): the trapezius (A's top of the shoulder rides A's clavicle roll; weights_topo.a_shoulder_top)
            for nm in gd.get("clavicle_roll_keep", []):
                j = I.get(nm.replace("{s}", s))
                if j is not None:
                    keep[j] = G[j].copy()
            _apply(poser, G, cl, _about(head(G, cl), _expm(-y * ang)))
            for k, M in keep.items():
                G[k] = M
    th_u =table(A, gd["scap_up"]) - table(A0, gd["scap_up"])
    th_p = table(A, gd["scap_tilt"]) - table(A0, gd["scap_tilt"])
    if abs(th_u) > 1e-9 or abs(th_p) > 1e-9:
        n = Rt @ _n(np.asarray(gd["scap_axis"], float) * np.array([sg, 1.0, 1.0]))
        Rs = _expm(-side * math.radians(th_p)) @ _expm(n * sg * math.radians(th_u))
        _apply(poser, G, sc, _about(head(G, sc), Rs))
    glide = gd["glide_m"] * reach
    if abs(glide) > 1e-12:
        T = np.eye(4)
        T[:3, 3] = front * glide
        _apply(poser, G, sc, T)
    return {"A": A, "A0": A0, "clav_elev_deg": th_e, "clav_retract_deg": th_r, "scap_up_deg": th_u, "scap_tilt_deg": th_p}


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
    a = share_amount(h, info.get(("A", s)), info.get(("A0", s))) if "below" in h else float(h.get("amount", 0.0))
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


def arc_weights(d, K, gate_deg):
    """The "arc" law: keys K [n+1, 3] (unit, K[0] the rest direction, no shape) along one swing (their plane's axis
    a = K[0] x K[n]); d's angle theta in that plane from K[0] (deg) through flex_weights' smoothstep hats over the
    keys' own angles (exact at each key, a partition of one along the arc, held past the last), times a gate on d's
    angle beta out of the plane: 1 within gate_deg[0], 0 past gate_deg[1], smoothstep between."""
    K = np.asarray(K, float)
    a = _n(np.cross(K[0], K[-1]))
    e1 = _n(K[0] - (K[0] @ a) * a)
    e2 = np.cross(a, e1)
    th = lambda v: math.degrees(math.atan2(float(v @ e2), float(v @ e1)))
    tk = [th(k) for k in K]
    tk[0] = 0.0
    w = flex_weights(th(d), tk)[1:]
    beta = abs(math.degrees(math.asin(float(np.clip(d @ a, -1, 1)))))
    g0, g1 = gate_deg
    return w * (1.0 - smooth((beta - g0) / (g1 - g0)))


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
            elif law == "arc":
                if sub(c["bone"]) not in poser.index:
                    continue
                d = direction(poser, G, sub(c["bone"]), sub(c["end"]), sub(c["frame"]))
                w = arc_weights(d, c["keys"][s or "l"], c["gate_deg"])
                w = np.where(w < 1e-5, 0.0, w)
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


# ---------------------------------------------------------------- hand clearance --
def grid_at(D, t, th, t0, dt):
    """A [t][theta] table at (t, theta): bilinear, t rows at t0 + i dt (held at the ends), theta bins centred at
    -pi + (j + 0.5) 2 pi / n (periodic)."""
    nt, nth = len(D), len(D[0])
    x = min(max((t - t0) / dt, 0.0), nt - 1.0)
    i = min(int(math.floor(x)), nt - 2)
    fx = x - i
    y = (th + math.pi) / (2 * math.pi) * nth - 0.5
    j = int(math.floor(y))
    fy = y - j
    j0, j1 = j % nth, (j + 1) % nth
    return ((1 - fx) * ((1 - fy) * D[i][j0] + fy * D[i][j1]) + fx * ((1 - fy) * D[i + 1][j0] + fy * D[i + 1][j1]))


def hand_clear(poser, G, rig, s):
    """rig.json "hand_clear" (tools/body/hand_clear.py; absent on the ref body: no change). The clips are A's on every
    body, so where this body's thigh and hip stand further out than the ref body's (dr, read against the same side's
    shoulder) a hand by them goes into the skin by that much. Each hand point p (its "points" heads, and the palm: the
    mean of the "palm" heads) in the thigh's frame (q = its posed world's turn undone, from its head): t = q . axis /
    length, rho = q across the axis, d = |rho|, theta = atan2(rho . e2, rho . e1); its gap to the ref body's surface
    g = d - (r - dr) (grid_at). g's soft minimum (g_min - soft ln sum exp(-(g - g_min) / soft)) gives the proximity
    k = 1 - smoothstep((g - near) / (far - near)); the change dr and the outward direction (rho's, world) are the
    points' means by exp(-(g - g_min) / soft). The arm (its subtree) takes the least turn about its head that moves the
    palm by k dr along that direction: the hand keeps its place against the thigh surface the clip was made on."""
    hc = rig["hand_clear"]
    sd = hc["sides"].get(s)
    if not sd:
        return
    I = poser.index
    th, arm = I[hc["thigh"].replace("{s}", s)], I[hc["arm"].replace("{s}", s)]
    R, o = _unit(G[th]), G[th][:3, 3]
    ax, e1, e2 = (np.asarray(sd[k], float) for k in ("axis", "e1", "e2"))
    L, t0, dt = float(sd["length_m"]), float(hc["t0"]), float(hc["dt"])
    palm_b = [I[n.replace("{s}", s)] for n in hc["palm"] if n.replace("{s}", s) in I]
    if not palm_b:
        return
    palm = sum(head(G, k) for k in palm_b) / len(palm_b)
    P = [head(G, I[n.replace("{s}", s)]) for n in hc["points"] if n.replace("{s}", s) in I] + [palm]
    gs, drs, dirs = [], [], []
    for p in P:
        q = R.T @ (p - o)
        rho = q - (q @ ax) * ax
        d = float(np.linalg.norm(rho))
        if d < 1e-9:
            continue
        t, ang = float(q @ ax) / L, math.atan2(float(rho @ e2), float(rho @ e1))
        dr = grid_at(sd["dr"], t, ang, t0, dt)
        gs.append(d - (grid_at(sd["r"], t, ang, t0, dt) - dr))
        drs.append(dr)
        dirs.append(R @ (rho / d))
    if not gs:
        return
    soft = float(hc["soft_m"])
    gm = min(gs)
    w = [math.exp(-(g - gm) / soft) for g in gs]
    sw = sum(w)
    g = gm - soft * math.log(sw)
    k = 1.0 - smooth((g - float(hc["near_m"])) / (float(hc["far_m"]) - float(hc["near_m"])))
    if k <= 0.0:
        return
    dr = sum(wi * x for wi, x in zip(w, drs)) / sw
    v = _n(sum(wi * x for wi, x in zip(w, dirs))) * (k * dr)
    if float(np.linalg.norm(v)) < 1e-9:
        return
    c = head(G, arm)
    a = palm - c
    _apply(poser, G, arm, _about(c, _arc(_n(a), _n(a + v))))


# --------------------------------------------------------------------- drive --
def drive_helpers(poser, G, rig):
    G = G.copy()
    info = {}
    if "girdle" in rig:
        for s in ("l", "r"):
            r = girdle(poser, G, rig, s)
            info[("A", s)] = r["A"]
            info[("A0", s)] = r["A0"]
    if "hand_clear" in rig:      # (P1 R1 sliders: after the girdle, before the helper rows; absent on the ref body)
        for s in ("l", "r"):
            hand_clear(poser, G, rig, s)
    for h in rig.get("helpers", []):
        for s in (("l", "r") if "{s}" in h["name"] else ("",)):
            helper(poser, G, h, s, info)
    return G, info


def drive(poser, G, rig):
    G, _ = drive_helpers(poser, G, rig)
    return G, corrective_weights(poser, G, rig)
