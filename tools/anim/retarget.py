"""Motion capture onto her skeleton.

The source's every joint turns in the world as it did in the take; each of
her bones takes the same turn, measured from a calibration pose: her own
rest, each bone swung (never twisted) to lie along the source's rest line,
so her bones keep their own frames and the take lands on her as it was
performed. Then the clean-up a capture needs:

- the pelvis's height and travel scaled by leg length (hers to the
  performer's), her feet set where the performer's were (scaled the same,
  their stance drawn in toward her narrower hips) by two-bone IK, the knee
  bent the way the take bends it;
- feet locked where the take plants them (a planted foot holds still while
  planted, however the capture jittered);
- resampled to the game's 30 frames a second;
- for loops: the stretch whose ends match best, the seam spread over the
  whole loop;
- root motion measured (the game moves her) and taken out.

100STYLE (CC BY 4.0) is the source here: tools/anim/clips/mocap.py.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np

import bvh as bvhlib
from rig import Clip, Skeleton, qbetween, qinv, qmul, qnorm, qrot, qslerp, two_bone_ik

MOCAP = Path(r"C:\Users\munch\Tools\mocap")

# Her bones from 100STYLE's joints (and where each one's line runs to, in
# both skeletons, for the calibration).
MAP_100STYLE = {
    "pelvis": ("Hips", "spine_01", "Chest"),
    "spine_01": ("Chest", "spine_02", "Chest2"),
    "spine_02": ("Chest2", "spine_03", "Chest3"),
    "spine_03": ("Chest4", "neck_01", "Neck"),
    "neck_01": ("Neck", "Head", "Head"),
    "Head": ("Head", None, "Head:end"),
    "clavicle_l": ("LeftCollar", "upperarm_l", "LeftShoulder"),
    "upperarm_l": ("LeftShoulder", "lowerarm_l", "LeftElbow"),
    "lowerarm_l": ("LeftElbow", "hand_l", "LeftWrist"),
    "hand_l": ("LeftWrist", "middle_01_l", "LeftWrist:end"),
    "clavicle_r": ("RightCollar", "upperarm_r", "RightShoulder"),
    "upperarm_r": ("RightShoulder", "lowerarm_r", "RightElbow"),
    "lowerarm_r": ("RightElbow", "hand_r", "RightWrist"),
    "hand_r": ("RightWrist", "middle_01_r", "RightWrist:end"),
    "thigh_l": ("LeftHip", "calf_l", "LeftKnee"),
    "calf_l": ("LeftKnee", "foot_l", "LeftAnkle"),
    "foot_l": ("LeftAnkle", "ball_l", "LeftToe"),
    "ball_l": ("LeftToe", "ball_leaf_l", "LeftToe:end"),
    "thigh_r": ("RightHip", "calf_r", "RightKnee"),
    "calf_r": ("RightKnee", "foot_r", "RightAnkle"),
    "foot_r": ("RightAnkle", "ball_r", "RightToe"),
    "ball_r": ("RightToe", "ball_leaf_r", "RightToe:end"),
}


def _fingers(side, src_side, names):
    """Her three finger joints per finger on a source's (names: the
    source's per-finger joint names, 1 to 3, and the joint after 3)."""
    out = {}
    for f, sf in (("index", "Index"), ("middle", "Middle"), ("ring", "Ring"), ("pinky", "Pinky"), ("thumb", "Thumb")):
        js = names(src_side, sf)
        for k in range(3):
            child = f"{f}_0{k + 2}_{side}" if k < 2 else f"{f}_04_leaf_{side}"
            out[f"{f}_0{k + 1}_{side}"] = (js[k], child, js[k + 1])
    return out


# Kimodo's SOMA skeleton (its BVH: tools/anim/kimodo_bvh.py).
MAP_SOMA = {
    "pelvis": ("Hips", "spine_01", "Spine1"),
    "spine_01": ("Spine1", "spine_02", "Spine2"),
    "spine_02": ("Spine2", "spine_03", "Chest"),
    "spine_03": ("Chest", "neck_01", "Neck1"),
    "neck_01": ("Neck2", "Head", "Head"),
    "Head": ("Head", None, "HeadEnd"),
}
for _s, _S in (("l", "Left"), ("r", "Right")):
    MAP_SOMA.update({
        f"clavicle_{_s}": (f"{_S}Shoulder", f"upperarm_{_s}", f"{_S}Arm"),
        f"upperarm_{_s}": (f"{_S}Arm", f"lowerarm_{_s}", f"{_S}ForeArm"),
        f"lowerarm_{_s}": (f"{_S}ForeArm", f"hand_{_s}", f"{_S}Hand"),
        f"hand_{_s}": (f"{_S}Hand", f"middle_01_{_s}", f"{_S}HandMiddle1"),
        f"thigh_{_s}": (f"{_S}Leg", f"calf_{_s}", f"{_S}Shin"),
        f"calf_{_s}": (f"{_S}Shin", f"foot_{_s}", f"{_S}Foot"),
        f"foot_{_s}": (f"{_S}Foot", f"ball_{_s}", f"{_S}ToeBase"),
        f"ball_{_s}": (f"{_S}ToeBase", f"ball_leaf_{_s}", f"{_S}ToeEnd"),
    })
    MAP_SOMA.update(_fingers(_s, _S, lambda S, F: [f"{S}Hand{F}{i}" for i in (1, 2, 3)] +
                             [f"{S}Hand{F}{'End' if F == 'Thumb' else 4}"]))

# Mixamo's skeleton (an FBX made BVH by tools/anim/fbx_bvh.py; "mixamorig:" taken off).
MAP_MIXAMO = {
    "pelvis": ("Hips", "spine_01", "Spine"),
    "spine_01": ("Spine", "spine_02", "Spine1"),
    "spine_02": ("Spine1", "spine_03", "Spine2"),
    "spine_03": ("Spine2", "neck_01", "Neck"),
    "neck_01": ("Neck", "Head", "Head"),
    "Head": ("Head", None, "HeadTop_End"),
}
for _s, _S in (("l", "Left"), ("r", "Right")):
    MAP_MIXAMO.update({
        f"clavicle_{_s}": (f"{_S}Shoulder", f"upperarm_{_s}", f"{_S}Arm"),
        f"upperarm_{_s}": (f"{_S}Arm", f"lowerarm_{_s}", f"{_S}ForeArm"),
        f"lowerarm_{_s}": (f"{_S}ForeArm", f"hand_{_s}", f"{_S}Hand"),
        f"hand_{_s}": (f"{_S}Hand", f"middle_01_{_s}", f"{_S}HandMiddle1"),
        f"thigh_{_s}": (f"{_S}UpLeg", f"calf_{_s}", f"{_S}Leg"),
        f"calf_{_s}": (f"{_S}Leg", f"foot_{_s}", f"{_S}Foot"),
        f"foot_{_s}": (f"{_S}Foot", f"ball_{_s}", f"{_S}ToeBase"),
        f"ball_{_s}": (f"{_S}ToeBase", f"ball_leaf_{_s}", f"{_S}Toe_End"),
    })
    MAP_MIXAMO.update(_fingers(_s, _S, lambda S, F: [f"{S}Hand{F}{i}" for i in (1, 2, 3, 4)]))


# Each source's skeleton: the mapping, the joints the clean-up reads, and
# whether its standing is measured against 100STYLE's neutral take.
PROFILES = {
    "100style": {"map": MAP_100STYLE, "hips": "Hips", "hip": ("LeftHip", "RightHip"), "knee": ("LeftKnee", "RightKnee"),
                 "ankle": ("LeftAnkle", "RightAnkle"), "toe": ("LeftToe", "RightToe"), "neutral": True},
    "soma": {"map": MAP_SOMA, "hips": "Hips", "hip": ("LeftLeg", "RightLeg"), "knee": ("LeftShin", "RightShin"),
             "ankle": ("LeftFoot", "RightFoot"), "toe": ("LeftToeBase", "RightToeBase"), "neutral": False},
    "mixamo": {"map": MAP_MIXAMO, "hips": "Hips", "hip": ("LeftUpLeg", "RightUpLeg"), "knee": ("LeftLeg", "RightLeg"),
               "ankle": ("LeftFoot", "RightFoot"), "toe": ("LeftToeBase", "RightToeBase"), "neutral": False},
}



def _mhr_positions():
    """SAM 3D Body's Momentum Human Rig, as BuildPoseFile writes it (joints
    named joint_NNN): which joint stands where on her. Read from a take
    against the body (the eyes say which way she faces, so which leg and arm
    is the left)."""
    J = lambda n: f"joint_{n:03d}"
    pts = {
        "pelvis": "Hips", "spine_01": J(35), "spine_02": J(36), "spine_03": J(37), "neck_01": J(110),
        "Head": J(113), "head_top": J(126), "eye_l": J(124), "eye_r": J(122),
    }
    for s, (cl, sh, el, wr, idx, mid, ring, pnk, th, hip, kn, an, ball, toe) in {
            "l": (74, 75, 76, 78, 80, 84, 88, 92, 97, 2, 3, 4, 7, 8),
            "r": (38, 39, 40, 42, 44, 48, 52, 56, 61, 18, 19, 20, 23, 24)}.items():
        pts.update({f"clavicle_{s}": J(cl), f"upperarm_{s}": J(sh), f"lowerarm_{s}": J(el), f"hand_{s}": J(wr),
                    f"thigh_{s}": J(hip), f"calf_{s}": J(kn), f"foot_{s}": J(an), f"ball_{s}": J(ball),
                    f"ball_leaf_{s}": J(toe)})
        for f, base in (("index", idx), ("middle", mid), ("ring", ring), ("pinky", pnk), ("thumb", th)):
            for k in range(4):
                pts[f"{f}_0{k + 1}_{s}" if k < 3 else f"{f}_04_leaf_{s}"] = J(base + k)
    return pts


def _aims():
    """Each bone: where it points (its own joint to the next) and the second
    line that fixes its roll; both measured the same way on her rest and on
    the take. Second lines: a pair of points (from, to), or "fwd" (the way
    the head looks), or a bend ("bend", a, b, c, default)."""
    aims = {
        "pelvis": ("pelvis", "spine_01", ("thigh_r", "thigh_l")),
        "spine_01": ("spine_01", "spine_02", ("thigh_r", "thigh_l")),
        "spine_02": ("spine_02", "spine_03", ("upperarm_r", "upperarm_l")),
        "spine_03": ("spine_03", "neck_01", ("upperarm_r", "upperarm_l")),
        "neck_01": ("neck_01", "Head", ("upperarm_r", "upperarm_l")),
        "Head": ("Head", "head_top", ("eye_r", "eye_l")),
    }
    for s in "lr":
        aims.update({
            f"clavicle_{s}": (f"clavicle_{s}", f"upperarm_{s}", ("spine_03", "neck_01")),
            f"upperarm_{s}": (f"upperarm_{s}", f"lowerarm_{s}", ("bend", f"upperarm_{s}", f"lowerarm_{s}", f"hand_{s}", "arm")),
            f"lowerarm_{s}": (f"lowerarm_{s}", f"hand_{s}", (f"pinky_01_{s}", f"index_01_{s}")),
            f"hand_{s}": (f"hand_{s}", f"middle_01_{s}", (f"pinky_01_{s}", f"index_01_{s}")),
            f"thigh_{s}": (f"thigh_{s}", f"calf_{s}", ("bend", f"thigh_{s}", f"calf_{s}", f"foot_{s}", "leg")),
            f"calf_{s}": (f"calf_{s}", f"foot_{s}", ("bend", f"thigh_{s}", f"calf_{s}", f"foot_{s}", "leg")),
            f"foot_{s}": (f"foot_{s}", f"ball_{s}", ("thigh_r", "thigh_l")),
            f"ball_{s}": (f"ball_{s}", f"ball_leaf_{s}", ("thigh_r", "thigh_l")),
        })
        for f in ("index", "middle", "ring", "pinky", "thumb"):
            for k in range(3):
                nxt = f"{f}_0{k + 2}_{s}" if k < 2 else f"{f}_04_leaf_{s}"
                aims[f"{f}_0{k + 1}_{s}"] = (f"{f}_0{k + 1}_{s}", nxt, (f"pinky_01_{s}", f"index_01_{s}"))
    return aims


AIMS = _aims()


def _frame(d, s):
    """An orthonormal frame from a pointing line and a second line (made
    square to it)."""
    d = d / np.linalg.norm(d, axis=-1, keepdims=True)
    s = s - d * np.sum(s * d, axis=-1, keepdims=True)
    s = s / np.maximum(np.linalg.norm(s, axis=-1, keepdims=True), 1e-9)
    t = np.cross(d, s)
    return np.stack([d, s, t], axis=-1)


def _matrix_quat(m):
    from rig import qfrom_matrix
    return np.array([qfrom_matrix(x) for x in m])


def globals_from_positions(sk: Skeleton, src: "Source", spec):
    """Her bones' rotations in the world for each frame from where the
    source's joints are: each bone turned so its line runs where the take's
    does, its roll set by a second line measured alike on her and the take
    (the hips' line, the shoulders', the bend of a limb, the knuckles')."""
    pts_map = spec["points"]
    grest, prest = sk.rest_globals()
    grest, prest = grest[0], prest[0]
    T = src.pos.shape[0]

    # Her own points at rest.
    def hers(name):
        if name == "head_top":
            return prest[sk.i("Head")] + qrot(grest[sk.i("Head")], [0, 0.14, 0])
        if name in ("eye_l", "eye_r"):
            h = prest[sk.i("Head")]
            return h + np.array([0.032 if name == "eye_l" else -0.032, 0.07, 0.09])
        return prest[sk.i(name)]

    def theirs(name):
        return src.pos[:, src.joint(pts_map[name])]

    def second(sec, P, rest):
        if sec[0] == "bend":
            _, a, b, c, kind = sec
            A, B, C = P(a), P(b), P(c)
            n = np.cross(B - A, C - B)
            # A straight limb's bend is no guide: lean on the way it would
            # bend (an elbow forward, a knee back) as it straightens.
            fwd = np.array([0, 0, 1.0]) if kind == "arm" else np.array([0, 0, -1.0])
            if not rest:
                left = P("thigh_l") - P("thigh_r")
                left = left / np.linalg.norm(left, axis=-1, keepdims=True)
                up = np.broadcast_to([0, 1.0, 0], left.shape)
                face = np.cross(left, up)
                fwd = face if kind == "arm" else -face
            dflt = np.cross(B - A, fwd)
            w = np.linalg.norm(n, axis=-1, keepdims=True) / np.maximum(
                np.linalg.norm(B - A, axis=-1, keepdims=True) * np.linalg.norm(C - B, axis=-1, keepdims=True), 1e-9)
            k = np.clip(w / 0.35, 0, 1)
            nn = n / np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-9)
            dd = dflt / np.maximum(np.linalg.norm(dflt, axis=-1, keepdims=True), 1e-9)
            return nn * k + dd * (1 - k)
        return P(sec[1]) - P(sec[0])

    g = np.tile(grest, (T, 1, 1))
    for bone, (a, b, sec) in AIMS.items():
        if bone not in sk.index or a not in pts_map or b not in pts_map:
            continue
        jb = sk.i(bone)
        d0 = hers(b) - hers(a)
        s0 = second(sec, hers, True)
        d1 = theirs(b) - theirs(a)
        s1 = second(sec, theirs, False)
        F0 = _frame(d0[None], np.asarray(s0, float)[None])[0]
        F1 = _frame(d1, s1)
        R = np.einsum("tij,kj->tik", F1, F0)  # F1 @ F0^T
        g[:, jb] = qmul(_matrix_quat(R), grest[jb])
    return g


_MHR = _mhr_positions()
PROFILES["mhr"] = {"map": {}, "hips": "Hips", "hip": (_MHR["thigh_l"], _MHR["thigh_r"]),
                   "knee": (_MHR["calf_l"], _MHR["calf_r"]), "ankle": (_MHR["foot_l"], _MHR["foot_r"]),
                   "toe": (_MHR["ball_l"], _MHR["ball_r"]), "neutral": False, "ground": True,
                   "positions": {"points": _MHR, "bones": {b: None for b in AIMS}}}

class Source:
    """A take, its globals in metres at 30 frames a second. `profile` names
    its skeleton (PROFILES): 100style, soma (Kimodo) or mixamo."""

    def __init__(self, path, start=0, stop=None, fps=30, units=0.01, profile="100style"):
        self.profile = PROFILES[profile]
        self.b = bvhlib.load(path)
        # (Mixamo's joints carry its rig's prefix.)
        self.b.names = [n.split(":")[-1] for n in self.b.names]
        g, p = self.b.globals(start, stop)
        step = self.b.fps / fps
        idx = np.arange(0, g.shape[0] - 1e-6, step)
        lo = np.floor(idx).astype(int)
        hi = np.minimum(lo + 1, g.shape[0] - 1)
        f = (idx - lo)[:, None]
        self.pos = (p[lo] * (1 - f[..., None]) + p[hi] * f[..., None]) * units
        rot = np.empty((len(idx), g.shape[1], 4))
        for j in range(g.shape[1]):
            for k, (a, c, w) in enumerate(zip(lo, hi, f[:, 0])):
                rot[k, j] = qslerp(g[a, j], g[c, j], w)
        self.rot = rot
        self.fps = fps
        self.units = units
        rest = self.b.rest_positions() * units
        self.rest = rest
        self.names = self.b.names

    def joint(self, name):
        return self.names.index(name)

    def direction(self, spec):
        """A joint's rest line: to a named child, or to its end site."""
        if spec.endswith(":end"):
            j = self.joint(spec[:-4])
            return self.b.end_sites[j] * self.units
        j = self.joint(spec)
        return self.b.offset[j] * self.units


POSTURE = ("pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "Head")


def heading_free(rot, hips):
    """Rotations with the hips' heading (yaw) taken off each frame."""
    f = qrot(rot[:, hips], [0, 0, 1])
    yaw = np.arctan2(f[:, 0], f[:, 2])
    h = np.stack([np.zeros_like(yaw), np.sin(-yaw / 2), np.zeros_like(yaw), np.cos(-yaw / 2)], axis=1)
    return qmul(h[:, None, :], rot)


def mean_rotation(qs):
    qs = np.array(qs, float)
    ref = qs[0]
    qs = np.where((qs @ ref)[:, None] < 0, -qs, qs)
    m = qs.mean(axis=0)
    return m / np.linalg.norm(m)


_neutral = {}


def neutral_posture(src_like: "Source"):
    """The performer's own way of standing (their Neutral idle), joint by
    joint, heading taken off: what her rest is matched to for the back,
    neck and head, so a performer's habit (100STYLE's looks at the floor)
    is not carried over and a style's posture is measured from it."""
    key = str(src_like.b.names)
    if key not in _neutral:
        from clips.mocap import take
        path, start, stop = take("Neutral", "ID")
        n = Source(path, start, stop)
        hf = heading_free(n.rot, n.joint("Hips"))
        _neutral[key] = {name: mean_rotation(hf[:, n.joint(name)]) for name in n.names}
    return _neutral[key]


def retarget(sk: Skeleton, src: Source, mapping=None, stance=0.8, lock=True, posture=None):
    """Her local rotations [T, J, 4] and positions [T, J, 3] for the take,
    root motion still in (see in_place)."""
    pr = src.profile
    mapping = mapping or pr["map"]
    posture = pr["neutral"] if posture is None else posture
    HIPS = pr["hips"]
    (LHIP, RHIP), (LKNEE, _), (LANK, RANK), (LTOE, RTOE) = pr["hip"], pr["knee"], pr["ankle"], pr["toe"]
    grest, prest = sk.rest_globals()
    grest, prest = grest[0], prest[0]
    T = src.rot.shape[0]
    J = len(sk)
    if "positions" in pr:
        # A source whose rest is no pose at all (SAM 3D Body's rig lies
        # along its bones' axes): her bones aimed from the joints' places.
        g = globals_from_positions(sk, src, pr["positions"])
        mapping = pr["positions"]["bones"]
    else:
        # Calibration: her limbs swung onto the source's rest lines; her
        # back, neck and head matched to the performer's neutral standing.
        cal = {}
        neutral = neutral_posture(src) if posture else None
        for b, (s, tchild, schild) in mapping.items():
            jb = sk.i(b)
            if neutral is not None and b in POSTURE:
                cal[b] = qmul(qinv(neutral[s]), grest[jb])
                continue
            if tchild is None:
                dt = qrot(grest[jb], [0, 1, 0])
            else:
                dt = prest[sk.i(tchild)] - prest[jb]
            ds = src.direction(schild)
            cal[b] = qmul(qbetween(dt, ds), grest[jb])
        g = np.tile(grest, (T, 1, 1))
        for b, (s, _, _) in mapping.items():
            g[:, sk.i(b)] = qmul(src.rot[:, src.joint(s)], cal[b])
    # Bones with no source keep their rest turn on their parent.
    for j in range(J):
        if sk.names[j] in mapping or sk.parent[j] < 0:
            continue
        p = sk.parent[j]
        g[:, j] = qmul(g[:, p], qmul(qinv(grest[p]), grest[j]))
    # Scale: her leg length to the performer's.
    leg_t = np.linalg.norm(prest[sk.i("calf_l")] - prest[sk.i("thigh_l")]) + np.linalg.norm(prest[sk.i("foot_l")] - prest[sk.i("calf_l")])
    leg_s = np.linalg.norm(src.rest[src.joint(LKNEE)] - src.rest[src.joint(LHIP)]) + \
        np.linalg.norm(src.rest[src.joint(LANK)] - src.rest[src.joint(LKNEE)])
    k = leg_t / leg_s
    hips = src.pos[:, src.joint(HIPS)] * k
    # Heights from the ground: the performer standing straight has the hips
    # a leg's drop above a planted ankle; hers stand where her rest does.
    ground_s = np.percentile(src.pos[:, src.joint(LANK), 1], 5)
    # (Measured down the leg's own length, whatever pose the source's rest is.)
    stand_s = src.rest[src.joint(HIPS)][1] - src.rest[src.joint(LHIP)][1] + leg_s + ground_s
    pel_off = np.array([0.0, prest[sk.i("pelvis")][1] - k * stand_s, 0.0])
    pelvis = hips + pel_off
    # Locals by FK order.
    local = np.empty((T, J, 4))
    for j in range(J):
        p = sk.parent[j]
        local[:, j] = g[:, j] if p < 0 else qmul(qinv(g[:, p]), g[:, j])
    pos = np.tile(sk.rest_pos, (T, 1, 1))
    root = sk.i("root")
    pos[:, sk.i("pelvis")] = qrot(qinv(sk.rest_rot[root]), pelvis - prest[root])
    # Feet: where the performer's were, scaled, stance drawn toward hers.
    hipw_t = abs(prest[sk.i("thigh_l")][0] - prest[sk.i("thigh_r")][0]) / 2
    hipw_s = abs(src.rest[src.joint(LHIP)][0] - src.rest[src.joint(RHIP)][0]) / 2 * k
    lateral = stance + (1 - stance) * (hipw_t / hipw_s)
    ankles = {}
    for side, sj in (("l", LANK), ("r", RANK)):
        a = src.pos[:, src.joint(sj)] * k
        # Draw the stance in about the pelvis's line, in the hips' own frame.
        hip_fwd = qrot(src.rot[:, src.joint(HIPS)], [0, 0, 1])
        hip_fwd[:, 1] = 0
        hip_fwd /= np.linalg.norm(hip_fwd, axis=1, keepdims=True)
        hip_left = np.cross([0, 1, 0], hip_fwd)
        rel = a - pelvis
        side_amt = np.sum(rel * hip_left, axis=1, keepdims=True)
        a = a - hip_left * side_amt * (1 - lateral)
        # A planted ankle at her own ankle's height.
        a[:, 1] += prest[sk.i(f"foot_{side}")][1] - k * ground_s
        ankles[side] = a
    if pr.get("ground"):
        # Height from one camera is the least sure thing it gives: the lower
        # foot is put on the ground every frame, the body with it (smoothed,
        # so it settles rather than jitters).
        # ("exact": no smoothing, for a jump the game flies itself.)
        rest_ank = prest[sk.i("foot_l")][1]
        low = np.minimum(ankles["l"][:, 1], ankles["r"][:, 1]) - rest_ank
        if pr["ground"] == "exact":
            off = low
        else:
            kern = np.exp(-0.5 * (np.arange(-6, 7) / 3.0) ** 2)
            kern /= kern.sum()
            off = np.convolve(np.pad(low, 6, mode="edge"), kern, mode="valid")
        for side in "lr":
            ankles[side][:, 1] -= off
        pel = sk.i("pelvis")
        world = qrot(sk.rest_rot[root], pos[:, pel]) + prest[root]
        world[:, 1] -= off
        pos[:, pel] = qrot(qinv(sk.rest_rot[root]), world - prest[root])
    contacts = {}
    if lock:
        for side, sj, tj in (("l", LANK, LTOE), ("r", RANK, RTOE)):
            c = foot_contacts(src, sj, tj)
            contacts[side] = c
            ankles[side] = lock_feet(ankles[side], c)
    # Legs reach for the ankles.
    gl, gp = sk.fk(local, pos)
    for side in "lr":
        th, ca, fo = sk.i(f"thigh_{side}"), sk.i(f"calf_{side}"), sk.i(f"foot_{side}")
        for t in range(T):
            a, b_, c_ = gp[t, th], gp[t, ca], gp[t, fo]
            # The knee bends the way the take bends it; a straight leg's
            # knee points the way its foot does.
            kd = b_ - (a + c_) / 2
            toe = gp[t, sk.i(f"ball_{side}")] - c_
            toe[1] = 0
            toe = toe / max(np.linalg.norm(toe), 1e-6)
            pole = kd / max(np.linalg.norm(kd), 1e-6) * min(1.0, np.linalg.norm(kd) / 0.03) + toe * 0.3
            nb, nc = two_bone_ik(a, b_, c_, ankles[side][t], b_ + pole)
            r1 = qbetween(b_ - a, nb - a)
            gth = qmul(r1, gl[t, th])
            gca0 = qmul(r1, gl[t, ca])
            b2 = a + (nb - a)
            c2 = b2 + qrot(r1, c_ - b_)
            r2 = qbetween(c2 - b2, nc - b2)
            gca = qmul(r2, gca0)
            pth = gl[t, sk.parent[th]]
            local[t, th] = qmul(qinv(pth), gth)
            local[t, ca] = qmul(qinv(gth), gca)
            # The foot keeps its turn in the world.
            local[t, fo] = qmul(qinv(gca), gl[t, fo])
    return local, pos, {"scale": k, "contacts": contacts}


def foot_contacts(src: Source, ankle, toe, h_ankle=None, v_max=0.35):
    """Frames a foot is planted: low and still (heel or toe), with short
    gaps closed and short contacts dropped."""
    a = src.pos[:, src.joint(ankle)]
    t = src.pos[:, src.joint(toe)]
    va = np.linalg.norm(np.gradient(a, axis=0), axis=1) * src.fps
    vt = np.linalg.norm(np.gradient(t, axis=0), axis=1) * src.fps
    ha = a[:, 1] - np.percentile(a[:, 1], 5)
    ht = t[:, 1] - np.percentile(t[:, 1], 5)
    c = ((ha < 0.03) & (va < v_max)) | ((ht < 0.025) & (vt < v_max))
    return _clean(c, 2)


def _clean(c, n):
    c = c.copy()
    # Close gaps of up to n frames, then drop runs shorter than n.
    for val, length in ((False, n), (True, n)):
        i = 0
        while i < len(c):
            if c[i] == val:
                j = i
                while j < len(c) and c[j] == val:
                    j += 1
                if j - i <= length and i > 0 and j < len(c):
                    c[i:j] = not val
                i = j
            else:
                i += 1
    return c


def lock_feet(a, contact, blend=3):
    """Hold a planted foot where it lands (the mean of its plant), easing in
    and out over a few frames so the lock never pops."""
    a = a.copy()
    T = len(a)
    i = 0
    out = a.copy()
    while i < T:
        if contact[i]:
            j = i
            while j < T and contact[j]:
                j += 1
            hold = a[i:j].mean(axis=0)
            hold[1] = min(a[i:j, 1].min(), hold[1])
            for t in range(max(0, i - blend), min(T, j + blend)):
                if i <= t < j:
                    w = 1.0
                elif t < i:
                    w = 1 - (i - t) / (blend + 1)
                else:
                    w = 1 - (t - j + 1) / (blend + 1)
                out[t] = a[t] * (1 - w) + hold * w
            i = j
        else:
            i += 1
    return out


def best_loop(local, pos, sk: Skeleton, min_len, max_len, weights=None):
    """The frames [a, b] whose poses match best (b - a between min and max),
    for a loop: rotations of the big bones, and the pelvis's height."""
    T = local.shape[0]
    big = [sk.i(n) for n in ("pelvis", "spine_03", "Head", "upperarm_l", "upperarm_r", "lowerarm_l", "lowerarm_r",
                              "thigh_l", "thigh_r", "calf_l", "calf_r", "foot_l", "foot_r")]
    feats = np.concatenate([local[:, big].reshape(T, -1), pos[:, sk.i("pelvis")] * 3], axis=1)
    vel = np.gradient(feats, axis=0)
    best = (1e9, 0, min_len)
    for a in range(0, T - min_len):
        for b in range(a + min_len, min(T, a + max_len + 1)):
            d = np.sum((feats[a] - feats[b]) ** 2) + 0.5 * np.sum((vel[a] - vel[b]) ** 2)
            if d < best[0]:
                best = (d, a, b)
    return best


def make_loop(local, pos, a, b):
    """Frames a..b as a closed loop: the difference between the ends spread
    across the clip, so the seam vanishes."""
    L = local[a:b + 1].copy()
    P = pos[a:b + 1].copy()
    n = L.shape[0]
    for j in range(L.shape[1]):
        dq = qmul(L[0, j], qinv(L[-1, j]))
        for t in range(n):
            w = t / (n - 1)
            L[t, j] = qmul(qslerp(np.array([0, 0, 0, 1.0]), dq, w), L[t, j])
    dp = P[0] - P[-1]
    for t in range(n):
        P[t] += dp * (t / (n - 1))
    L[-1] = L[0]
    P[-1] = P[0]
    return L, P


def in_place(sk: Skeleton, pos, keep_height=True):
    """Root motion out: the pelvis's straight-line travel removed (its sway
    about that line kept). Returns the positions and the travel speed (m/s of
    her skeleton at 30 fps) and heading."""
    pel = sk.i("pelvis")
    root = sk.i("root")
    world = qrot(sk.rest_rot[root], pos[:, pel])
    T = len(world)
    start, end = world[0].copy(), world[-1].copy()
    d = end - start
    d[1] = 0
    out = world.copy()
    for t in range(T):
        out[t] -= d * (t / (T - 1))
    # Centre the sway about her rest line.
    mean = out.mean(axis=0)
    out[:, 0] -= mean[0]
    out[:, 2] -= mean[2]
    p = pos.copy()
    p[:, pel] = qrot(qinv(sk.rest_rot[root]), out)
    return p, np.linalg.norm(d) / ((T - 1) / 30.0), math.degrees(math.atan2(d[0], d[2])) if np.linalg.norm(d) > 1e-6 else 0.0


def face_forward(sk: Skeleton, local, pos):
    """The whole take turned about the vertical so her hips face +Z on
    average (a take captured facing elsewhere)."""
    pel = sk.i("pelvis")
    g, _ = sk.fk(local, pos)
    fwd = qrot(g[:, pel], qrot(qinv(sk.rest_globals()[0][0, pel]), [0, 0, 1]))
    fwd = fwd.mean(axis=0)
    yaw = math.atan2(fwd[0], fwd[2])
    turn = np.array([0, math.sin(-yaw / 2), 0, math.cos(-yaw / 2)])
    root = sk.i("root")
    L = local.copy()
    P = pos.copy()
    # Turn the pelvis about the world's up (in the root's frame) and carry
    # its position round with it.
    rr = sk.rest_rot[root]
    turn_root = qmul(qinv(rr), qmul(turn, rr))
    L[:, pel] = qmul(turn_root, L[:, pel])
    P[:, pel] = qrot(turn_root, P[:, pel])
    return L, P


# The hero's neck leans further forward at rest than any performer's: laid
# along the performer's lines, a take throws his head back by about this
# much (the library's clips, made for yet another body, need People.HisNeckPitch).
NECK_PITCH = {"him": 10.0}


def lean_neck(rig, local):
    """A take's neck bowed forward about the chest's own left-right axis,
    every frame, by the body's NECK_PITCH (none for her)."""
    deg = NECK_PITCH.get(getattr(rig, "body", "her"), 0.0)
    if not deg:
        return local
    sk = rig.sk
    neck, chest = sk.i("neck_01"), sk.i("spine_03")
    axis = qrot(qinv(sk.rest_globals()[0][0, chest]), [1.0, 0, 0])
    half = math.radians(deg) / 2
    bow = np.array([*(axis / np.linalg.norm(axis) * math.sin(half)), math.cos(half)])
    L = local.copy()
    L[:, neck] = qmul(bow, L[:, neck])
    return L


def clip_from(name, sk, local, pos, loop=False, meta=None):
    return Clip(name, 30, local, pos, loop=loop, meta=meta or {})
