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
SAMPLES = [("abd", 110.0, 0.0), ("abd", 140.0, 0.0), ("flex", 110.0, 0.0), ("flex", 140.0, 0.0), ("up", 175.0, 0.0),
           ("abd", 140.0, SHRUG), ("flex", 140.0, SHRUG), ("up", 175.0, SHRUG)]
SHAPES = ["shoulder_abd110", "shoulder_abd140", "shoulder_flex110", "shoulder_flex140", "shoulder_up175",
          "shoulder_abd140s", "shoulder_flex140s", "shoulder_up175s"]
EASE_FROM = 90.0
UP_AZ = 0.0  # the overhead sample's azimuth (0: sideways); overhead the two ways meet
# HerRaise's knobs (its defaults)
RAISE = dict(start=-10.0, full=70.0, pitch=20.0, yaw=12.0, up=0.034, out=0.010, back=0.006, sup=0.22, sside=0.03)
# the region: around her left shoulder joint (rest), metres
REGION_IN, REGION_OUT = 0.08, 0.17
ARM_KEEP = 0.17   # along the upper arm past the shoulder joint: kept to here, fading over FADE
FADE = 0.05
BREAST_KEEP = 0.45  # how much of the smoothing her breast (its bone's weight) still takes
DM_ITERS = int(os.environ.get("PSD_DM", 30))
HOLLOW_D, HOLLOW_R = float(os.environ.get("PSD_HOLLOW", 0.010)), 0.035
FILL, FILL_ITERS = float(os.environ.get("PSD_FILL", 1.0)), int(os.environ.get("PSD_FILL_IT", 60))   # the armpit hollow at full (A 175); scaled by (A - 90) / 85
SMOOTH = 3
# the outfit pieces over her shoulders and armpits that carry the shapes (every calling, the warden's steel too: its
# pauldrons and top ride the skin under them like everything else skinned there)
FOLLOW_PARTS = (".top.", ".pauldrons.", ".cloak.", ".collar.")
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
    if shrug:
        # her clavicle raised about her forward axis (its outer end up), the arm then aimed as wanted
        c = I["clavicle_" + side]
        Rg = _axis(fwd, shrug * (1.0 if side == "l" else -1.0)) @ M0[c, :3, :3]
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
    e = ramp(A, EASE_FROM, 110.0)
    e = e * e * (3 - 2 * e)
    t110 = e * (1 - ramp(A, 110.0, 140.0))
    t140 = ramp(A, 110.0, 140.0) * (1 - ramp(A, 140.0, 175.0))
    t175 = ramp(A, 140.0, 175.0)
    wf = math.sin(math.radians(float(np.clip(az, 0.0, 90.0)))) ** 2
    wa = 1 - wf
    # her clavicle's rise (degrees above rest) hands the 140 and 175 samples over to their shrugged twins
    r = float(np.clip(rise / SHRUG, 0, 1))
    return {"shoulder_abd110": wa * t110, "shoulder_abd140": wa * t140 * (1 - r), "shoulder_flex110": wf * t110,
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
    neck = wsum(["neck_01", "Head"])
    distal = wsum(["lowerarm_l", "hand_l", "lowerarm_twist_01_l", "lowerarm_twist_02_l", "lowerarm_share_l",
                   "lowerarm_point_l"])
    wbr = wsum(["breast_l"])
    reg = (1 - _ss((dist - REGION_IN) / (REGION_OUT - REGION_IN))) * (1 - _ss((along - ARM_KEEP) / FADE))
    reg *= (1 - _ss(neck / 0.8)) * (1 - _ss(distal / 0.3)) * (1 - (1 - BREAST_KEEP) * _ss(wbr / 0.6)) * left
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
        # FILL: on top of the shoulder and the trap (posed normal up or out), the creases and the corner filled out
        # toward a heavily smoothed surface (outward only: the deltoid's cap and the trap's slope made round, nothing
        # pressed in), as the arm rises past level
        down, lat, fwd = torso_frame(M, rig, "l")
        Y = X + Dp
        Yh = _smooth(Y, A, deg, FILL_ITERS, grow)
        Ny = _vn(Y, F)
        out_ = np.maximum(((Yh - Y) * Ny).sum(1), 0.0)
        top = _ss((-(Ny @ down) + 0.15) / 0.5)
        k = FILL * float(np.clip((Asmp - 90) / 50, 0, 1))
        Dp = Dp + Ny * (k * out_ * top * reg)[:, None]
        # the armpit hollow: the deepest point of her posed armpit (the region's point nearest the torso's side,
        # under the shoulder), pressed in along the posed normal
        Np = _vn(X + Dp, F)
        shp = M[I["upperarm_l"], :3, 3]
        rel = X - shp
        score = rel @ down * 1.0 - np.abs(rel @ fwd) * 2.0 - np.abs(rel @ lat - 0.0) * 1.0
        cand = np.nonzero(active & (reg > 0.5) & ((rel @ down) > 0.02) & ((Np @ down) > 0.2))[0]
        if len(cand):
            hc = X[cand[np.argmax(score[cand])]]
            dh = np.linalg.norm(X - hc, axis=1)
            depth = HOLLOW_D * float(np.clip((Asmp - 90) / 85, 0, 1))
            Dp = Dp - Np * (depth * np.cos(np.clip(dh / HOLLOW_R, 0, 1) * np.pi / 2) ** 2 * reg)[:, None]
        Dp = _smooth(Dp, A, deg, SMOOTH)
        Dp[~left] = 0
        Db = np.einsum("nij,nj->ni", np.linalg.inv(Bm[:, :3, :3]), Dp)
        Db[np.linalg.norm(Db, axis=1) < 1e-6] = 0
        dn = (Dp * _vn(X, F)).sum(1)
        log("SHOULDER_PSD %s (A %.1f az %.1f, raise w %.2f): %d points, most %.1f mm, out %.1f in %.1f mm" % (
            name, Ar, az, w["l"], int((np.abs(Db).max(1) > 0).sum()), 1000 * np.linalg.norm(Dp, axis=1).max(),
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
        "samples": SAMPLES, "dm_iters": DM_ITERS, "hollow_mm": HOLLOW_D * 1000}
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
