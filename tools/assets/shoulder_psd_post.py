"""Her shoulders and armpits as an arm rises: pose-space correctives (armor 17 C1, 22 October 2026).

The max judge (AJ1) at the close-up camera: with an arm raised past level, linear skinning leaves a hard corner on top
of the shoulder (no deltoid cap: "the arm looks plugged into the chest"), and the armpit a pinched, creased seam where
the breast's outer edge runs into the arm; overhead the traps buckle. A bone can't make these: they are pose-space
shapes.

Shapes (morph targets on heroine.glb's body, per side _l/_r; the left authored, the right its mirror):
  shoulder_abd110, shoulder_abd140  arm out to the side (abduction), A = 110 and 140 degrees
  shoulder_flex110, shoulder_flex140  arm forward (flexion), A = 110 and 140
  shoulder_up175  arm overhead (either way), A = 175
A is the angle between the upper arm and her torso's down axis (neck_01 to pelvis): 90 is level with the shoulder, 180
overhead. Each shape is authored at its sample pose: her rest with only that upper arm turned there (the shortest
turn from rest), her helpers driven as HerJoints drives them, her breast lifted as HerRaise lifts it and her
axilla_fold/raise_crease morphs at HerRaise's weight. The target there is the posed skinned mesh made smooth and
volume-keeping in the shoulder and armpit region, delta-mush style: the posed mesh smoothed, then the rest mesh's
detail (rest minus its smoothing, in each point's local frame) put back on it, so the corner, the pinch and the crease
(skinning's) go and the deltoid, the pec and lat folds (the sculpt's) come back. The move wanted there is carried back
to her bind shape through the inverse of each point's blended skin matrix, so at the sample it is exactly that target
and between samples it rides with the skin. Plus a soft armpit HOLLOW between the folds (deeper as the arm rises).

HerRaise drives them in game per side from the upper arm's direction in her torso frame (Play/ShoulderPsd.cs: A
eased in from EASE_FROM, between the samples linearly, the azimuth blending side to front), so at rest and with the arms
down every weight is 0: she is bit-identical there.

Each outfit's tops and pauldrons carry the same morphs, moved as the skin under them (axilla_fold_post.follow).

Idempotent: done-mark shoulder_psd on the glb and on each outfit file.

    python tools/assets/shoulder_psd_post.py [art dir, default godot/art/people] [--dry] [--report]
"""
import json
import math
import os
import struct
import sys

import numpy as np
from scipy.sparse import coo_matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "anim"))
from heroine_neck import _Gl  # noqa: E402
from wrap_post import skin_union  # noqa: E402
from worn_reaver_post import _sparse, _vn, _ss  # noqa: E402

# (way, A, shrug): the samples, in the order of SHAPES. The shrugged ones (her clavicle raised SHRUG degrees above its
# rest, as the clips raise it overhead: cast_raise about 15-19, leap 55-60) carry the trap's fold the clavicle makes
SHRUG = 30.0
# (C2: the first samples at A 117, where the close-range clips live, was 110; each plain sample with HerShrug's
# clavicle lift (helpers.shrug), its twin SHRUG degrees past it)
FIRST = 117.0
SAMPLES = [("abd", FIRST, 0.0), ("abd", 140.0, 0.0), ("flex", FIRST, 0.0), ("flex", 140.0, 0.0), ("up", 175.0, 0.0),
           ("abd", 140.0, SHRUG), ("flex", 140.0, SHRUG), ("up", 175.0, SHRUG)]
SHAPES = ["shoulder_abd117", "shoulder_abd140", "shoulder_flex117", "shoulder_flex140", "shoulder_up175",
          "shoulder_abd140s", "shoulder_flex140s", "shoulder_up175s"]
EASE_FROM = 90.0
UP_AZ = 0.0  # the overhead sample's azimuth (0: sideways); overhead the two ways meet
# HerRaise's knobs (its defaults)
RAISE = dict(start=-10.0, full=70.0, pitch=20.0, yaw=12.0, up=0.034, out=0.010, back=0.006, sup=0.22, sside=0.03)
# the region: around her left shoulder joint (rest), metres
REGION_IN, REGION_OUT = 0.09, 0.19
ARM_KEEP = 0.17   # along the upper arm past the shoulder joint: kept to here, fading over FADE
FADE = 0.05
BREAST_KEEP = 0.45  # how much of the smoothing her breast (its bone's weight) still takes
DM_ITERS = int(os.environ.get("PSD_DM", 30))
HOLLOW_D, HOLLOW_R = float(os.environ.get("PSD_HOLLOW", 0.016)), 0.032
FILL, FILL_ITERS = float(os.environ.get("PSD_FILL", 1.0)), int(os.environ.get("PSD_FILL_IT", 60))   # the armpit hollow at full (A 175); scaled by (A - 90) / 85
SMOOTH = 3
# C2's sculpt (posed space, at each sample; CJ1: "smoothed targets can soften a notch but can't add shape"):
#   the deltoid cap: an ellipsoid round the humeral head along the arm (CAP_ALONG long, the arm's own top radius plus
#     CAP_BULGE across, centred CAP_AT along the arm and CAP_UP above its line), her skin pushed out onto it where it
#     dips under (a soft max: no corner where the trap meets the arm), on the top and outer side only;
#   the armpit: in the pit's frame (b out of the pit, the bisector of her side's and the arm's underside's outward
#     directions; t forward), the front (pec) and back (lat) folds as webs across the pit FOLD_H above its apex, at
#     FOLD_F in front of it and FOLD_B behind (FOLD_W wide), her skin lifted onto them along b (fill only); between
#     them the hollow, its middle pressed in HOLLOW_D (her centre sits higher than the creases either side). Each grows with the raise (full from A 117).
CAP_ALONG, CAP_AT, CAP_UP = float(os.environ.get("PSD_CAP_ALONG", 0.075)), 0.02, float(os.environ.get("PSD_CAP_UP", 0.004))
CAP_BULGE, CAP_K = float(os.environ.get("PSD_CAP", 0.008)), 0.012
FOLD_H, FOLD_F, FOLD_B, FOLD_W = float(os.environ.get("PSD_FOLD", 0.03)), 0.045, 0.045, 0.016
FOLD_K = 0.006
NECK_KEEP = 0.25   # how much of the region her neck (neck_01's weight) still takes (C1: none past 0.8; the trap spike)
# the outfit pieces over her shoulders and armpits that carry the shapes (every calling, the warden's steel too: its
# pauldrons and top ride the skin under them like everything else skinned there)
FOLLOW_PARTS = (".top.", ".cloak.", ".collar.")
PAULDRON_NEAR, PAULDRON_FAR = 0.11, 0.15
# (pauldrons stand well off her shoulder: whole to 6 cm, none past 10)
FOLLOW_NEAR, FOLLOW_FAR = 0.06, 0.10


def _q2m(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def _axis(a, deg):
    a = np.asarray(a, float) / np.linalg.norm(a)
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    x, y, z = a
    return np.array([[c + x * x * (1 - c), x * y * (1 - c) - z * s, x * z * (1 - c) + y * s],
                     [y * x * (1 - c) + z * s, c + y * y * (1 - c), y * z * (1 - c) - x * s],
                     [z * x * (1 - c) - y * s, z * y * (1 - c) + x * s, c + z * z * (1 - c)]])


def _between(a, b):
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    v = np.cross(a, b)
    s, c = np.linalg.norm(v), float(a @ b)
    if s < 1e-9:
        return np.eye(3)
    return _axis(v / s, math.degrees(math.atan2(s, c)))


class Rig:
    """Her skeleton from the glb's joints (local rest TRS), skeleton space as Godot's (the root joint's turn in)."""

    def __init__(s, G):
        g = G.g
        joints = g["skins"][0]["joints"]
        s.names = [g["nodes"][j].get("name") for j in joints]
        s.index = {n: i for i, n in enumerate(s.names)}
        pos = {j: i for i, j in enumerate(joints)}
        s.parent = [-1] * len(joints)
        for i, j in enumerate(joints):
            for c in g["nodes"][j].get("children", []):
                if c in pos:
                    s.parent[pos[c]] = i
        s.rest_rot = np.array([g["nodes"][j].get("rotation", [0, 0, 0, 1.0]) for j in joints], float)
        s.rest_pos = np.array([g["nodes"][j].get("translation", [0, 0, 0.0]) for j in joints], float)
        s.rest_scl = np.array([g["nodes"][j].get("scale", [1, 1, 1.0]) for j in joints], float)
        s.ibm = G.get(g["skins"][0]["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
        assert all(s.parent[i] < i for i in range(len(joints)) if s.parent[i] >= 0), "joints not parent-first"

    def fk(s, rot, pos, scl):
        """Bone globals (4x4) from local quaternions, positions and scales (T R S, Godot's bone pose)."""
        M = np.zeros((len(s.names), 4, 4))
        for j, p in enumerate(s.parent):
            L = np.eye(4)
            L[:3, :3] = _q2m(rot[j]) * scl[j][None, :]
            L[:3, 3] = pos[j]
            M[j] = L if p < 0 else M[p] @ L
        return M


def _mq(R):
    """A rotation matrix's quaternion (x, y, z, w)."""
    from rig import qfrom_matrix
    return np.asarray(qfrom_matrix(R), float)


def _ix(rig):
    return rig if isinstance(rig, dict) else rig.index


def torso_frame(Mg, rig, side):
    """(down, lateral, forward) of her torso in skeleton space: down neck_01 to pelvis, lateral spine_03's X (her
    left; flipped for the right) made square to it, forward their cross (+Z at rest). As Play/ShoulderPsd does."""
    I = _ix(rig)
    down = Mg[I["pelvis"], :3, 3] - Mg[I["neck_01"], :3, 3]
    down /= np.linalg.norm(down)
    left = Mg[I["spine_03"], :3, 0]
    left = left - (left @ down) * down
    left /= np.linalg.norm(left)
    fwd = np.cross(down, left)
    return down, left * (1.0 if side == "l" else -1.0), fwd


def arm_angles(Mg, rig, side):
    """(A, azimuth) of an upper arm: A from her torso's down axis, azimuth 0 sideways, 90 forward, -90 back."""
    I = _ix(rig)
    d = Mg[I["lowerarm_" + side], :3, 3] - Mg[I["upperarm_" + side], :3, 3]
    d /= np.linalg.norm(d)
    down, lat, fwd = torso_frame(Mg, rig, side)
    A = math.degrees(math.acos(np.clip(d @ down, -1, 1)))
    az = math.degrees(math.atan2(d @ fwd, d @ lat))
    return A, az


def clavicle_rise(Mg, M0, rig, side):
    """Degrees her clavicle is raised above its rest, in her torso frame (its line's elevation, now minus at rest)."""
    I = _ix(rig)
    def el(M):
        v = M[I["upperarm_" + side], :3, 3] - M[I["clavicle_" + side], :3, 3]
        down = torso_frame(M, rig, side)[0]
        return math.degrees(math.asin(np.clip(-(v @ down) / np.linalg.norm(v), -1, 1)))
    return el(Mg) - el(M0)


def sample_pose(rig, side, way, A, shrug=0.0):
    """Local (rot, pos, scl) and globals for her rest with one upper arm turned to (way, A), helpers driven as
    HerJoints does and the breast lifted as HerRaise does; and HerRaise's weight there."""
    import helpers as hp
    from rig import Skeleton
    I = rig.index
    rot, pos, scl = rig.rest_rot.copy(), rig.rest_pos.copy(), rig.rest_scl.copy()
    M0 = rig.fk(rot, pos, scl)
    down, lat, fwd = torso_frame(M0, rig, side)
    # her clavicle raised as HerShrug raises it at this A (helpers.shrug: its outer end up, rolled forward a little),
    # the twins SHRUG past that; the arm then aimed as wanted (and helpers.drive's lift finds nothing left to add)
    import helpers as hp
    lift = hp.shrug_target(A) + shrug
    if lift:
        c = I["clavicle_" + side]
        up_ax = np.cross(down, lat)
        roll_ax = np.cross(lat, fwd)
        Rg = _axis(roll_ax, hp.SHRUG_ROLL * lift) @ _axis(up_ax, lift) @ M0[c, :3, :3]
        rot[c] = _mq(M0[rig.parent[c], :3, :3].T @ Rg)
        M0 = rig.fk(rot, pos, scl)
    az = UP_AZ if way == "up" else (0.0 if way == "abd" else 90.0)
    a, z = math.radians(A), math.radians(az)
    want = math.cos(a) * down + math.sin(a) * (math.cos(z) * lat + math.sin(z) * fwd)
    u, lo = I["upperarm_" + side], I["lowerarm_" + side]
    have = M0[lo, :3, 3] - M0[u, :3, 3]
    Rg = _between(have, want) @ M0[u, :3, :3]
    rot[u] = _mq(M0[rig.parent[u], :3, :3].T @ Rg)
    # her helpers, as HerJoints drives them (helpers.drive: the game's twin)
    sk = Skeleton(names=rig.names, parent=rig.parent, rest_rot=rig.rest_rot.copy(), rest_pos=rig.rest_pos.copy())
    sk.index = dict(I)
    hscale, hshift = np.ones((len(rig.names), 3)), np.zeros((len(rig.names), 3))
    rot = hp.drive(sk, rot, hscale, hshift)
    for j in range(len(rig.names)):
        if np.any(hscale[j] != 1) or np.any(hshift[j] != 0):
            scl[j] = scl[j] * hscale[j]
            pos[j] = pos[j] + _q2m(rot[j]) @ hshift[j]
    M = rig.fk(rot, pos, scl)
    # HerRaise: each breast lifted by its arm's elevation in spine_03's frame
    w = {}
    for i, s in enumerate("lr"):
        C = np.linalg.inv(M[I["spine_03"]])
        dd = (C[:3, :3] @ (M[I["lowerarm_" + s], :3, 3] - M[I["upperarm_" + s], :3, 3]))
        dd /= np.linalg.norm(dd)
        el = math.degrees(math.asin(np.clip(dd[1], -1, 1)))
        t = np.clip((el - RAISE["start"]) / (RAISE["full"] - RAISE["start"]), 0, 1)
        w[s] = t * t * (3 - 2 * t)
        if w[s] <= 0:
            continue
        sd = 1.0 if s == "l" else -1.0
        b = I["breast_" + s]
        turn = _axis([0, 1, 0], RAISE["yaw"] * sd * w[s]) @ _axis([1, 0, 0], -RAISE["pitch"] * w[s])
        pos[b] = pos[b] + np.array([RAISE["out"] * sd, RAISE["up"], -RAISE["back"]]) * w[s]
        rot[b] = _mq(turn @ _q2m(rot[b]))
        uu, ss = 1 + w[s] * RAISE["sup"], 1 + w[s] * RAISE["sside"]
        scl[b] = scl[b] * np.array([ss, 1 / (uu * ss), uu])
    M = rig.fk(rot, pos, scl)
    return M, w


def psd_weights(A, az, rise=0.0):
    """{shape: weight} for an upper arm at (A, azimuth) (arm_angles): 0 to EASE_FROM, eased in to the first samples,
    then linear between samples (they sum to the ease); the azimuth blends side (<= 0) to front (>= 90).
    The game's twin: godot/logic/Play/ShoulderPsd.cs."""
    def ramp(x, a, b):
        return float(np.clip((x - a) / (b - a), 0, 1))
    import helpers as hp
    e = ramp(A, EASE_FROM, FIRST)
    e = e * e * (3 - 2 * e)
    t110 = e * (1 - ramp(A, FIRST, 140.0))
    t140 = ramp(A, FIRST, 140.0) * (1 - ramp(A, 140.0, 175.0))
    t175 = ramp(A, 140.0, 175.0)
    wf = math.sin(math.radians(float(np.clip(az, 0.0, 90.0)))) ** 2
    wa = 1 - wf
    # her clavicle's rise (degrees above rest) hands the 140 and 175 samples over to their shrugged twins
    # (read past HerShrug's own lift, helpers.shrug_target)
    r = float(np.clip((rise - hp.shrug_target(A)) / SHRUG, 0, 1))
    return {"shoulder_abd117": wa * t110, "shoulder_abd140": wa * t140 * (1 - r), "shoulder_flex117": wf * t110,
            "shoulder_flex140": wf * t140 * (1 - r), "shoulder_up175": t175 * (1 - r),
            "shoulder_abd140s": wa * t140 * r, "shoulder_flex140s": wf * t140 * r, "shoulder_up175s": t175 * r}


def weights_from_globals(Mg, index, M0):
    """{shape_side: weight} for bone globals Mg [J, 4, 4] (her skeleton's index; M0 her rest globals): as HerRaise
    sets them."""
    out = {}
    for s in "lr":
        A, az = arm_angles(Mg, index, s)
        for k, w in psd_weights(A, az, clavicle_rise(Mg, M0, index, s)).items():
            out[k + "_" + s] = w
    return out


def _blend(J, W, M):
    B = np.zeros((len(J), 4, 4))
    for k in range(J.shape[1]):
        B += W[:, k, None, None] * M[J[:, k]]
    return B


def _adj(F, n):
    r = np.concatenate([F[:, 0], F[:, 1], F[:, 2], F[:, 1], F[:, 2], F[:, 0]])
    c = np.concatenate([F[:, 1], F[:, 2], F[:, 0], F[:, 0], F[:, 1], F[:, 2]])
    A = coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n)).tocsr()
    A.data[:] = 1
    return A, np.maximum(np.asarray(A.sum(1)).ravel(), 1)


def _smooth(X, A, deg, k, mask=None):
    for _ in range(k):
        Y = 0.5 * X + 0.5 * (A @ X) / deg[:, None]
        X = Y if mask is None else np.where(mask[:, None], Y, X)
    return X


def _frames(X, N, nb):
    """Each point's frame (t, b, n): n its normal, t toward its first neighbour, b across."""
    e = X[nb] - X
    t = e - (e * N).sum(1)[:, None] * N
    t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-12)
    b = np.cross(N, t)
    return np.stack([t, b, N], 1)


def _read_sparse(G, ai):
    """A (sparse) accessor as a dense array."""
    a = G.g["accessors"][ai]
    out = np.zeros((a["count"], 3))
    if "bufferView" in a:
        out[:] = G.get(ai)
    sp = a.get("sparse")
    if sp:
        def view(v, dt, n):
            bv = G.g["bufferViews"][v["bufferView"]]
            o = G.b0 + bv.get("byteOffset", 0) + v.get("byteOffset", 0)
            return np.frombuffer(bytes(G.buf[o:o + np.dtype(dt).itemsize * n]), dt)
        idt = {5121: "<u1", 5123: "<u2", 5125: "<u4"}[sp["indices"]["componentType"]]
        idx = view(sp["indices"], idt, sp["count"]).astype(int)
        val = view(sp["values"], "<f4", sp["count"] * 3).reshape(-1, 3)
        out[idx] = val
    return out


def body_morphs(G, wid, nU):
    """{name: union-indexed rest delta} of the body's morphs."""
    g = G.g
    mesh = g["meshes"][[n for n in g["nodes"] if n.get("name") == "Heroine"][0]["mesh"]]
    names = (mesh.get("extras") or {}).get("targetNames", [])
    prims = [p for p in mesh["primitives"] if g["materials"][p["material"]].get("name") != "skin_head"]
    out = {n: np.zeros((nU, 3)) for n in names}
    o = 0
    for p in prims:
        cnt = g["accessors"][p["attributes"]["POSITION"]]["count"]
        for k, n in enumerate(names):
            if k < len(p.get("targets", [])):
                out[n][wid[o:o + cnt]] = _read_sparse(G, p["targets"][k]["POSITION"])
        o += cnt
    return out


def _srelu(x, k):
    """max(x, 0) with its corner rounded over k (0 at and below 0)."""
    x = np.asarray(x, float)
    return np.where(x <= 0, 0.0, np.where(x < k, x * x / (2 * k), x - k / 2))


def folded(Y, F, A, deg, grow, reg):
    """The region's faces folded over: their normal against the heavily smoothed surface's there."""
    Ys = _smooth(Y, A, deg, 12, grow)
    q = np.cross(Y[F[:, 1]] - Y[F[:, 0]], Y[F[:, 2]] - Y[F[:, 0]])
    qs = np.cross(Ys[F[:, 1]] - Ys[F[:, 0]], Ys[F[:, 2]] - Ys[F[:, 0]])
    c = (q * qs).sum(1) / np.maximum(np.linalg.norm(q, axis=1) * np.linalg.norm(qs, axis=1), 1e-18)
    return (c < 0.2) & (reg[F].min(1) > 0.05)


def untangle(X, Dp, F, A, deg, grow, reg, rounds=40):
    """Dp with the region's folded faces relaxed out (posed space): (Dp, folds before, folds after)."""
    Y = X + Dp
    bad = folded(Y, F, A, deg, grow, reg)
    n0 = int(bad.sum())
    for _ in range(rounds):
        if not bad.any():
            break
        m = np.zeros(len(Y), bool)
        m[F[bad].ravel()] = True
        for _ in range(2):
            m = m | (A @ m.astype(float) > 0)
        Y = np.where(m[:, None], 0.4 * Y + 0.6 * (A @ Y) / deg[:, None], Y)
        bad = folded(Y, F, A, deg, grow, reg)
    D = Y - X
    return Dp + (D - Dp) * np.clip(reg * 4, 0, 1)[:, None], n0, int(bad.sum())


def pit_soft(pit, A, deg):
    """The pit's mask made soft at its edge (a few rings)."""
    return np.clip(_smooth(pit[:, None].astype(float), A, deg, 4)[:, 0] * 1.6, 0, 1)


def author(G, log=print):
    """The left side's bind-space shapes {name: (Db [n,3], posed delta)} and the context (U, F, ...)."""
    U, F, J, W, wid = skin_union(G)
    rig = Rig(G)
    I = rig.index
    M0 = rig.fk(rig.rest_rot, rig.rest_pos, rig.rest_scl)
    E = np.abs(M0 @ rig.ibm - np.eye(4)).max((1, 2))
    # (Head: the neck cut moved its bind, not its joint; it lies outside the region, so it is posed from its rest)
    for j in np.nonzero(E > 1e-3)[0]:
        log("SHOULDER_PSD: %s's rest is %.3g off its bind; posed relative to its rest" % (rig.names[j], E[j]))
        assert rig.names[j] in ("Head",), "the glb's joints don't match its bind"
        rig.ibm[j] = np.linalg.inv(M0[j])
    mor = body_morphs(G, wid, len(U))
    A, deg = _adj(F, len(U))
    nb = A.indices[A.indptr[:-1]]
    left = U[:, 0] > 0.005
    # the region (rest): round her left shoulder joint, not down the arm, not up the neck
    sh = M0[I["upperarm_l"], :3, 3]
    el = M0[I["lowerarm_l"], :3, 3]
    ax = (el - sh) / np.linalg.norm(el - sh)
    # (from the line of her clavicle, its inner end to the shoulder joint: the trap's slope is in)
    ch = M0[I["clavicle_l"], :3, 3]
    tt = np.clip((U - ch) @ (sh - ch) / ((sh - ch) @ (sh - ch)), 0, 1)
    dist = np.linalg.norm(U - (ch + tt[:, None] * (sh - ch)), axis=1)
    along = (U - sh) @ ax
    wsum = lambda names: sum((W * (J == I[n])).sum(1) for n in names if n in I)  # noqa: E731
    neck, head = wsum(["neck_01"]), wsum(["Head"])
    distal = wsum(["lowerarm_l", "hand_l", "lowerarm_twist_01_l", "lowerarm_twist_02_l", "lowerarm_share_l",
                   "lowerarm_point_l"])
    wbr = wsum(["breast_l"])
    reg = (1 - _ss((dist - REGION_IN) / (REGION_OUT - REGION_IN))) * (1 - _ss((along - ARM_KEEP) / FADE))
    reg *= (1 - (1 - NECK_KEEP) * _ss(neck / 0.6)) * (1 - _ss(head / 0.15)) * (1 - _ss(distal / 0.3))
    reg *= (1 - (1 - BREAST_KEEP) * _ss(wbr / 0.6)) * left
    # the arm's own top radius round its line at the deltoid (rest), for the cap
    rr = U - sh
    ra = rr @ ax
    rp = rr - ra[:, None] * ax
    zone = (ra > 0.03) & (ra < 0.07) & (wsum(["upperarm_l", "upperarm_twist_01_l", "upperarm_share_l"]) > 0.5) & left
    upr = -(M0[I["pelvis"], :3, 3] - M0[I["neck_01"], :3, 3])
    upr = upr - (upr @ ax) * ax
    upr /= np.linalg.norm(upr)
    topz = zone & ((rp @ upr) > 0.5 * np.linalg.norm(rp, axis=1))
    r_arm = float(np.percentile(np.linalg.norm(rp[topz], axis=1), 90)) if topz.any() else 0.045
    log("SHOULDER_PSD: her arm's top radius at the deltoid %.1f mm (%d points)" % (1000 * r_arm, int(topz.sum())))
    reg = _smooth(reg[:, None], A, deg, 4)[:, 0] * left * _ss((U[:, 0] - 0.01) / 0.04)  # (none at her midline)
    active = reg > 1e-3
    grow = _smooth(active[:, None].astype(float), A, deg, DM_ITERS + 4)[:, 0] > 0  # the smoothing's reach
    out = {}
    for (way, Asmp, shr), name in zip(SAMPLES, SHAPES):
        M, w = sample_pose(rig, "l", way, Asmp, shr)
        Ar, az = arm_angles(M, rig, "l")
        Ur = U + w["l"] * (mor.get("axilla_fold_l", 0) + mor.get("raise_crease_l", 0))
        Bm = _blend(J, W, M @ rig.ibm)
        X = np.einsum("nij,nj->ni", Bm, np.c_[Ur, np.ones(len(U))])[:, :3]
        # delta mush on the region's reach: the rest's detail onto the smoothed posed shape
        Us = _smooth(Ur, A, deg, DM_ITERS, grow)
        Xs = _smooth(X, A, deg, DM_ITERS, grow)
        Fr = _frames(Us, _vn(Us, F), nb)
        Fp = _frames(Xs, _vn(Xs, F), nb)
        loc = np.einsum("nij,nj->ni", Fr, Ur - Us)
        T = Xs + np.einsum("nji,nj->ni", Fp, loc)
        Dp = (T - X) * reg[:, None]
        down, lat, fwd = torso_frame(M, rig, "l")
        Sp, Ep = M[I["upperarm_l"], :3, 3], M[I["lowerarm_l"], :3, 3]
        ap = (Ep - Sp) / np.linalg.norm(Ep - Sp)
        grow_k = float(np.clip((Ar - 90) / (FIRST - 90), 0, 1))
        # the deltoid cap: her skin on the top and outer side pushed out onto an ellipsoid round the humeral head
        Y = X + Dp
        up = -down + 0.6 * lat               # (the arm's top: up and out; overhead, its outer side)
        up = up - (up @ ap) * ap
        up /= max(np.linalg.norm(up), 1e-9)
        Cc = Sp + CAP_AT * ap + CAP_UP * up
        q = Y - Cc
        qa = q @ ap
        qp = q - qa[:, None] * ap
        qpn = np.linalg.norm(qp, axis=1)
        Rp = r_arm + CAP_BULGE
        rho = np.sqrt((qa / CAP_ALONG) ** 2 + (qpn / Rp) ** 2)
        kk = CAP_K / Rp
        rho_t = rho + _srelu(1 - rho, kk)                                  # a soft max(rho, 1)
        side = (qp @ up) / np.maximum(qpn, 1e-9)                         # 1 on top, 0 at the sides, -1 under
        wcap = _ss((side + 0.35) / 0.7) * (1 - _ss((qa - 0.06) / 0.05)) * grow_k
        Dcap = q * (rho_t / np.maximum(rho, 1e-9) - 1)[:, None] * (wcap * reg)[:, None]
        Dp = Dp + Dcap
        # FILL (C1): on top of the shoulder and the trap (posed normal up or out), what creases are left filled out
        # toward a heavily smoothed surface (outward only)
        Y = X + Dp
        Yh = _smooth(Y, A, deg, FILL_ITERS, grow)
        Ny = _vn(Y, F)
        out_ = np.maximum(((Yh - Y) * Ny).sum(1), 0.0)
        top = _ss((-(Ny @ down) + 0.15) / 0.5)
        k = FILL * float(np.clip((Asmp - 90) / 50, 0, 1))
        Dp = Dp + Ny * (k * out_ * top * reg)[:, None]
        # the armpit: its frame, its apex, the pec and lat folds as webs across it, the hollow between
        Y = X + Dp
        Ny = _vn(Y, F)
        na = down - (down @ ap) * ap
        na /= np.linalg.norm(na)
        # (the torso's face under the arm: the way the arm points, level; out to the side overhead)
        tn = ap - (ap @ down) * down
        tn = tn / np.linalg.norm(tn) if np.linalg.norm(tn) > 0.25 else lat
        bp = tn + na
        bp /= np.linalg.norm(bp)
        tp = np.cross(down, tn)          # along the pit: forward when the arm is out to the side (the pec fold ahead)
        tp = tp - (tp @ bp) * bp
        tp /= np.linalg.norm(tp)
        rel = Y - Sp
        # (under the arm's line and below the shoulder: not the trap, whose normals face out of the pit too)
        # (and across the pit no further than its walls: the crease's breast side faces forward, so it is in)
        up_ = np.cross(bp, tp)
        pit = active & (reg > 0.3) & ((Ny @ bp) > -0.35) & (np.linalg.norm(rel, axis=1) < 0.16) & ((rel @ na) > 0.0)
        pit &= ((rel @ down) > -0.01)
        cand = np.nonzero(pit & (np.abs(rel @ tp) < 0.015) & ((Ny @ bp) > 0.2))[0]
        Dpit = np.zeros_like(Dp)
        if len(cand) and grow_k > 0:
            o = Y[cand[np.argmin(rel[cand] @ bp)]]
            h = (Y - o) @ bp
            tc = (Y - o) @ tp
            pit &= np.abs((Y - o) @ up_) < 0.08
            # (her torso is round: the pit's crease drops away in front and behind, so each fold is a web FOLD_H over
            # the crease's own depth in its slice; slices 1 cm, the crease a low percentile, smoothed along t)
            edges = np.arange(-0.12, 0.1201, 0.01)
            mid = 0.5 * (edges[1:] + edges[:-1])
            lowh = np.full(len(mid), np.nan)
            for i_ in range(len(mid)):
                m_ = pit & (np.abs(tc - mid[i_]) < 0.01)
                if m_.sum() >= 5:
                    lowh[i_] = np.percentile(h[m_], 5)
            ok_ = ~np.isnan(lowh)
            lowh = np.interp(mid, mid[ok_], lowh[ok_]) if ok_.any() else np.zeros(len(mid))
            lowh = np.convolve(np.pad(lowh, 2, mode="edge"), np.ones(5) / 5, mode="valid")
            # (overhead the folds stretch flatter: half height at A 175)
            fold_k = grow_k * (1 - 0.5 * float(np.clip((Ar - 130) / 45, 0, 1)))
            web = np.interp(tc, mid, lowh) + FOLD_H * fold_k * (
                np.exp(-0.5 * ((tc - FOLD_F) / FOLD_W) ** 2) + np.exp(-0.5 * ((tc + FOLD_B) / FOLD_W) ** 2))
            facing = _ss(((Ny @ bp) + 0.35) / 0.5)
            reach = 1 - _ss((np.linalg.norm(Y - o, axis=1) - 0.09) / 0.05)
            lift = _srelu(web - h, FOLD_K)                                       # (a soft max(h, web))
            lift = 1.4 * FOLD_H * np.tanh(lift / (1.4 * FOLD_H))                  # (no deeper fill than the folds')
            Dpit += bp[None] * (lift * facing * reach * pit)[:, None]
            # the hollow: the middle between the folds pressed in along the pit's axis
            dh = np.sqrt(tc ** 2 + ((Y - o) @ up_) ** 2)
            depth = HOLLOW_D * grow_k
            Dpit -= bp[None] * (depth * np.cos(np.clip(dh / HOLLOW_R, 0, 1) * np.pi / 2) ** 2 * facing)[:, None]
            Dpit = _smooth(Dpit * pit_soft(pit, A, deg)[:, None], A, deg, 8, grow)   # (no ridge sharper than its rings)
            Dp = Dp + Dpit * reg[:, None]
            log("  pit: %d points, apex at S %+.0f down %+.0f lat %+.0f fwd%.0f mm; lift most %.1f mm, %d over 5 mm" % (
                int(pit.sum()), 1000 * ((o - Sp) @ down), 1000 * ((o - Sp) @ lat), 1000 * ((o - Sp) @ fwd), 0,
                1000 * np.linalg.norm(Dpit, axis=1).max(), int((np.linalg.norm(Dpit, axis=1) > 0.005).sum())))
            if os.environ.get("PSD_DEBUG"):
                np.savez(os.environ["PSD_DEBUG"] + "_" + name + ".npz", pit=pit, Dpit=Dpit, Dcap=Dcap, h=h, tc=tc, o=o, X=X)
        Dp = _smooth(Dp, A, deg, SMOOTH)
        # untangle: faces folded over (their normal against the heavily smoothed surface's) in the region, and two rings
        # round them, relaxed until none is left (the dark fleck in the armpit is such a fold)
        Dp, nf0, nf1 = untangle(X, Dp, F, A, deg, grow, reg)
        Dp[~left] = 0
        Db = np.einsum("nij,nj->ni", np.linalg.inv(Bm[:, :3, :3]), Dp)
        Db[np.linalg.norm(Db, axis=1) < 1e-6] = 0
        dn = (Dp * _vn(X, F)).sum(1)
        log("SHOULDER_PSD %s (A %.1f az %.1f, raise w %.2f): folds %d -> %d; %d points, most %.1f mm, out %.1f in %.1f mm" % (
            name, Ar, az, w["l"], nf0, nf1, int((np.abs(Db).max(1) > 0).sum()), 1000 * np.linalg.norm(Dp, axis=1).max(),
            1000 * dn.max(), -1000 * dn.min()))
        out[name] = (Db, Dp)
    return out, (U, F, J, W, wid, rig)


def main(a):
    from axilla_fold_post import mirror, follow
    import axilla_fold_post as afp
    art = next((x for x in a if not x.startswith("--")), "godot/art/people")
    path = os.path.join(art, "heroine.glb")
    G = _Gl(path)
    g = G.g
    mesh = g["meshes"][[n for n in g["nodes"] if n.get("name") == "Heroine"][0]["mesh"]]
    prims = [p for p in mesh["primitives"] if g["materials"][p["material"]].get("name") != "skin_head"]
    out, (U, F, J, W, wid, rig) = author(G)
    shapes = []
    for key, (Dl, _) in out.items():
        shapes += [(key + "_l", Dl), (key + "_r", mirror(U, Dl))]
    if "--dry" in a:
        np.savez_compressed(os.path.join(art, "..", "..", ".shots", "shoulder_psd_dry.npz"),
                            **{n: D for n, D in shapes})
        return
    # the outfits' tops and pauldrons carry them (axilla_fold_post.follow, with this file's done-mark)
    for o in ("warden",) + tuple(afp.OUTFITS):
        op = os.path.join(art, f"heroine_outfit_{o}.gltf")
        if os.path.exists(op):
            gg = json.load(open(op))
            if "shoulder_psd" in ((gg.get("asset") or {}).get("extras") or {}):
                print("SHOULDER_PSD: %s follows already" % o)
                continue
            follow(op, U, shapes, mark="shoulder_psd", parts=FOLLOW_PARTS, near=FOLLOW_NEAR, far=FOLLOW_FAR)
            # (C2: the rigid pauldrons ride the whole of the shoulder's fill and cap, out to PAULDRON_FAR: C1's fill
            # pressed her shoulder into them, warden 860 -> 891 points through, ranger 42 -> 81)
            follow(op, U, shapes, mark="shoulder_psd_pauldrons", parts=(".pauldrons.",), near=PAULDRON_NEAR,
                   far=PAULDRON_FAR)
    if "shoulder_abd110_l" in (mesh.get("extras") or {}).get("targetNames", []):
        print("SHOULDER_PSD: the morphs are on the glb already")
        return
    binb = bytearray(G.buf[G.b0:G.b0 + g["buffers"][0]["byteLength"]])
    for name, D in shapes:
        dN = _vn(U + D, F) - _vn(U, F)
        o = 0
        for p in prims:
            n = g["accessors"][p["attributes"]["POSITION"]]["count"]
            w = wid[o:o + n]
            Dp = D[w]
            Ns = G.get(p["attributes"]["NORMAL"]).astype(float)
            Nn = Ns + dN[w]
            Nn /= np.maximum(np.linalg.norm(Nn, axis=1, keepdims=True), 1e-12)
            dNp = np.where((np.abs(dN[w]).max(1) > 1e-5)[:, None], Nn - Ns, 0)
            ip = np.nonzero(np.abs(Dp).max(1) > 0)[0]
            inn = np.nonzero(np.abs(dNp).max(1) > 0)[0]
            p.setdefault("targets", []).append({
                "POSITION": _sparse(g, binb, n, ip, Dp[ip]),
                "NORMAL": _sparse(g, binb, n, inn, dNp[inn])})
            o += n
        mesh.setdefault("extras", {}).setdefault("targetNames", []).append(name)
        mesh["weights"] = list(mesh.get("weights", [])) + [0]
    g.setdefault("asset", {}).setdefault("extras", {})["shoulder_psd"] = {
        "samples": SAMPLES, "dm_iters": DM_ITERS, "hollow_mm": HOLLOW_D * 1000, "fold_mm": FOLD_H * 1000,
        "cap_bulge_mm": CAP_BULGE * 1000, "sculpt": "C2"}
    while len(binb) % 4:
        binb.append(0)
    g["buffers"][0]["byteLength"] = len(binb)
    js = json.dumps(g, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    body = struct.pack("<I", len(js)) + b"JSON" + js + struct.pack("<I", len(binb)) + b"BIN\x00" + bytes(binb)
    open(path, "wb").write(b"glTF" + struct.pack("<II", 2, 12 + len(body)) + body)
    print("SHOULDER_PSD: written", path)


if __name__ == "__main__":
    main(sys.argv[1:])
