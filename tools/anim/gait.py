"""Her run, keyed as a function of the stride rather than pose by pose.

A run cycle is two steps. Each foot spends `duty` of the cycle planted,
travelling back under her at exactly the ground's speed (so in the game,
where she moves at that speed, it holds still on the ground), and the rest
swinging through: off the toe, the heel kicked up behind, the knee driven
through, the foot reaching and settling onto the ground ahead. The pelvis
falls into each plant and rises into flight, turns with the swinging leg,
tips and shifts over the standing one; the chest turns against it, the arms
swing against the legs, the head holds steady. A Gait is the numbers that
make one woman's run different from another's: the calling's carriage.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, replace

import numpy as np

from keyed import Rig
from rig import Clip


@dataclass
class Gait:
    frames: int = 20             # one cycle (two steps) at 30 fps
    speed: float = 5.1           # metres a second of her skeleton (the world's is 1.04 times)
    duty: float = 0.31           # of the cycle a foot is planted
    drop: float = 0.07           # pelvis lower than standing, on average
    bob: float = 0.07            # pelvis rise and fall per step
    lean: float = 18.0           # the whole body tipped forward from the ankles
    spine_lean: float = 4.0      # the back's own forward bend
    hip_yaw: float = 9.0         # pelvis turning with the swinging leg
    hip_roll: float = 4.0        # the free hip dropping (more: a woman's sway)
    hip_shift: float = 0.025     # pelvis over the standing foot
    chest_yaw: float = 10.0      # shoulders turning against the hips
    width: float = 0.06          # each foot's line from the middle (less: steps on one line)
    reach: float = 0.36          # how far ahead of the pelvis a foot lands
    kick: float = 0.42           # how high the heel comes up behind
    knee: float = 0.30           # foot height as the knee drives through
    toe_off: float = 35.0        # foot pitch leaving the ground
    arm_fwd: tuple = (0.0, -0.17, 0.29)     # fist ahead, from the shoulder in the chest's frame (toward the middle +)
    arm_back: tuple = (0.02, -0.30, -0.26)  # fist behind
    elbow_out: float = 0.35      # elbows away from the body
    # The arm keyed by its joints (chest frame), forward and back: (upper arm forward of hanging, out from her
    # side, elbow's inside angle, the upper arm turned in), eased between on the step. Set, it replaces
    # arm_fwd/arm_back/elbow_out: their pole was an offset from her rest elbow, out at her side, so every run's
    # elbows flared out 35-55 degrees and the fists pumped up high (the owner, 17 October: "chicken wing").
    # Measured on a real run (100STYLE Neutral_FR): out 15-18, the elbow 65-95, the fist ahead of the
    # shoulder through the whole swing, a little in toward the middle in front, the upper arm 16 degrees
    # each way at a jog (1.5 m/s); hers is a run (5.3 m/s), so the upper arm swings about 42.
    swing: tuple = None
    # The right arm's own swing where it carries a heavy piece (the Reaver's axe: closer in, half the swing).
    swing_r: tuple = None
    fingers: str = "relaxed"
    # The right hand's own, where it holds a piece the other hand doesn't ("grip": the piece's fitted fist, keyed.wrap_of):
    # the arcanist's run keyed both hands "open", so her staff hand stood open, the pads 24-79 mm off the shaft.
    fingers_r: str = ""
    head_up: float = 0.0         # chin raised (+) beyond level
    shoulders: tuple = (0, 0)    # clavicles (raise, forward)
    arms: dict = field(default_factory=dict)  # per side overrides: {"r": callable(phase, pose)->hand spec}
    # The foot's swing path: "" the spline (every run before A1 L21); "v2" (A1 L21, the armed warden run): the heel
    # folded up fast off the toe, the foot under the driving knee, then reached and clawed back so it comes down
    # steeply with `land` of the ground's speed already under it (no skate on the ground before the plant), the
    # heel peeling `peel` m up at toe-off.
    path: str = ""
    land: float = 0.65
    peel: float = 0.10
    # v2's last reach key (s, metres past the landing spot, height) and the foot's fall at the plant (height per unit
    # of the swing's s). The game samples the clip between its keys, so a foot that keeps moving over the ground in the
    # frame before the plant reads as a skate there even if the keyed frames don't (A1 L21: see facts_run.md).
    reach_key: tuple = (0.85, 0.12, 0.12)
    fall: float = 0.9
    # A1 L22, the off-travel runs: her body (chest, head, arms) faces the aim while the legs run `travel` degrees off it
    # in her local frame (Move2D.Local's way round: 0 forward, 90 to her right, 180 back, 270 to her left), at `speed`
    # along that travel and on the same phase (the left foot plants at 0). 0 leaves every run as it was, byte for byte.
    # 180, the backpedal: the feet path mirrored (landing behind her hips, pushed off ahead of them), on the forefoot
    # (`back_toe` degrees heel-up at the landing, the ball held on the ground through the stance), the trunk `lean`
    # (pelvis `hip_tilt`), the arms' swing turned over (each arm goes with the opposite leg). 90/270, the strafes: the
    # pelvis turned `side_hips` toward travel, the chest counter-turned to the aim, the feet on lines `width` either
    # side of travel (the trail foot's line ahead of the lead's: neither crosses the other's), the lead foot toed out
    # `toe_lead` of the pelvis's turn and the trail `toe_trail`, the body tipped `side_lean` toward travel.
    travel: float = 0.0
    # v2's foot leaving the ground: its speed along the ground (of the ground's: -1 holds it on its spot) and its rise.
    lift: tuple = (-0.35, 0.6)
    back_toe: float = 14.0
    hip_tilt: float = 0.0
    chest_lean: float = 0.0
    side_hips: float = 45.0
    side_lean: float = 6.0
    toe_lead: float = 1.35
    toe_trail: float = 0.8
    # The arms' swing about its middle (1 as keyed; less: the arms held in guard, riding the step).
    arm_amp: float = 1.0


def _spline(points, s):
    """Catmull-Rom through points [(s, value...)] at s (values as arrays)."""
    ss = [p[0] for p in points]
    vs = [np.array(p[1:], float) for p in points]
    if s <= ss[0]:
        return vs[0]
    if s >= ss[-1]:
        return vs[-1]
    i = max(k for k in range(len(ss) - 1) if ss[k] <= s)
    p0 = vs[max(i - 1, 0)]
    p1, p2 = vs[i], vs[i + 1]
    p3 = vs[min(i + 2, len(vs) - 1)]
    u = (s - ss[i]) / (ss[i + 1] - ss[i])
    return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)


def foot(g: Gait, phase):
    """A foot's ankle (x out from its line, y up, z forward of the pelvis's
    mean) and its pitch (+ toes up), for a foot whose plant starts at
    phase 0."""
    T = g.frames / 30.0
    travel = g.speed * T * g.duty
    z_land = g.reach
    z_off = g.reach - travel
    ph = phase % 1.0
    if ph < g.duty:
        u = ph / g.duty
        z = z_land - travel * u
        # Rolls from heel (toes a little up) through flat to the toe.
        pitch = 6 * (1 - u) ** 3 - g.toe_off * max(0.0, (u - 0.55) / 0.45) ** 2
        y = 0.0
        # On the toe at the end: the ankle rises as the heel peels.
        y += g.peel * max(0.0, (u - 0.6) / 0.4) ** 2
        return np.array([0.0, y, z]), pitch, 0.0
    s = (ph - g.duty) / (1 - g.duty)
    if g.path == "v2":
        V = g.speed * T * (1 - g.duty)  # the ground's travel under her over the swing (m per unit s)
        rs, rz, ry = g.reach_key
        keys = [(0.0, z_off, g.peel), (0.28, z_off * 0.55, g.kick), (0.58, z_land * 0.55, g.knee + 0.05),
                (rs, z_land + rz, ry), (1.0, z_land, 0.0)]
        d0, d1 = np.array([g.lift[0] * V, g.lift[1]]), np.array([-g.land * V, -g.fall])
        i = max(k for k in range(len(keys) - 1) if keys[k][0] <= s) if s < 1.0 else len(keys) - 2

        def der(k):
            if k == 0:
                return d0
            if k == len(keys) - 1:
                return d1
            return (np.array(keys[k + 1][1:]) - np.array(keys[k - 1][1:])) / (keys[k + 1][0] - keys[k - 1][0])
        s0, s1 = keys[i][0], keys[i + 1][0]
        h = s1 - s0
        t = (s - s0) / h
        p0, p1 = np.array(keys[i][1:]), np.array(keys[i + 1][1:])
        p = ((2 * t ** 3 - 3 * t ** 2 + 1) * p0 + (t ** 3 - 2 * t ** 2 + t) * h * der(i)
             + (-2 * t ** 3 + 3 * t ** 2) * p1 + (t ** 3 - t ** 2) * h * der(i + 1))
        pitch = float(_spline([(0.0, -g.toe_off), (0.25, -g.toe_off * 1.2), (0.55, -15), (0.8, 8), (1.0, 6)], s)[0])
        toe = float(_spline([(0.0, 30), (0.2, 10), (0.4, 0), (1.0, 0)], s)[0])
        return np.array([0.0, max(0.0, p[1]), p[0]]), pitch, toe
    # Off the toe, the heel kicked up, the knee driven through, the reach.
    p = _spline([
        (0.0, z_off, 0.10),
        (0.22, z_off * 0.75, g.kick * 0.8),
        (0.42, z_off * 0.25, g.kick),
        (0.62, z_land * 0.45, g.knee + 0.04),
        (0.82, z_land + 0.1, 0.12),
        (1.0, z_land, 0.0),
    ], s)
    pitch = float(_spline([(0.0, -g.toe_off), (0.25, -g.toe_off * 1.2), (0.55, -15), (0.8, 8), (1.0, 6)], s)[0])
    toe = float(_spline([(0.0, 30), (0.2, 10), (0.4, 0), (1.0, 0)], s)[0])
    return np.array([0.0, p[1], p[0]]), pitch, toe


def arc_of(v):
    """Shoulder-relative vector (x toward her left, y up, z forward) as the
    solver's arc (azimuth, elevation, reach)."""
    v = np.asarray(v, float)
    r = float(np.linalg.norm(v))
    el = math.degrees(math.asin(max(-1.0, min(1.0, v[1] / r))))
    az = math.degrees(math.atan2(v[0], v[2]))
    return (az, el, r)


def manly(g: Gait) -> Gait:
    """A calling's run as the hero runs it: the same carriage, a man's
    weight. The hips held square (a fraction of her roll and shift, none
    of her line-walking), the shoulders turning more against them, the
    elbows out and the shoulders up, a deeper drop and a longer contact as
    the weight lands."""
    return replace(g, hip_roll=g.hip_roll * 0.3, hip_shift=g.hip_shift * 0.4, hip_yaw=g.hip_yaw * 0.8,
                   chest_yaw=g.chest_yaw * 1.3, width=max(g.width, 0.065), drop=g.drop + 0.015, bob=g.bob * 0.9,
                   duty=min(0.4, g.duty + 0.02), elbow_out=g.elbow_out + 0.12,
                   swing=None if g.swing is None else tuple((a[0], a[1] + 5, a[2], a[3]) for a in g.swing),
                   swing_r=None if g.swing_r is None else tuple((a[0], a[1] + 5, a[2], a[3]) for a in g.swing_r),
                   shoulders=(g.shoulders[0] + 2, g.shoulders[1] + 3))


def pose_at(g: Gait, rig: Rig, ph):
    """Her pose at a phase of the cycle (0 = left foot lands); his, as he runs it (manly)."""
    if getattr(rig, "body", "her") == "him":
        g = manly(g)
    c = math.cos(2 * math.pi * ph)
    d2 = g.duty / 2
    # Pelvis: lowest in the middle of each plant, highest in flight.
    y = -g.drop - g.bob / 2 * math.cos(4 * math.pi * (ph - d2))
    x = g.hip_shift * math.cos(2 * math.pi * (ph - d2))
    yaw = -g.hip_yaw * c
    roll = g.hip_roll * math.cos(2 * math.pi * (ph - d2))
    # The body tipped forward over the feet: the pelvis carried forward a
    # little with it.
    pose = {
        "hips": {"pos": (x, y, 0.04), "rot": (yaw, g.lean * 0.35, roll)},
        "spine": (g.chest_yaw * c - yaw, g.lean * 0.65 + g.spine_lean + 2 * math.cos(4 * math.pi * (ph - d2)), -roll * 0.85),
        "neck": (0, -(g.lean + g.spine_lean) * 0.35, 0),
        "head": (-g.chest_yaw * c * 0.8, -(g.lean + g.spine_lean) * 0.45 - g.head_up, 0),
        "clav_l": g.shoulders, "clav_r": g.shoulders,
        "fingers_l": g.fingers, "fingers_r": g.fingers_r or g.fingers,
    }
    for side, off in (("l", 0.0), ("r", 0.5)):
        s = 1 if side == "l" else -1
        a, pitch, toe = foot(g, ph - off)
        rest = rig.prest[rig.I[f"foot_{side}"]]
        pose[f"foot_{side}"] = {"pos": (s * g.width + a[0], a[1], a[2]), "rot": (s * 4, -pitch, 0), "toe": toe,
                                "pole": (s * 0.1, 0, 1)}
        # Arms against the legs: the left fist forward as the right foot lands.
        k = 0.5 - 0.5 * math.cos(2 * math.pi * (ph - off - 0.5))  # 1: this arm fully forward
        if g.travel or g.arm_amp != 1.0:
            # Off travel: backpedalling, the right foot lands behind her, so the left fist goes back with it.
            if abs(((g.travel + 180) % 360) - 180) > 135:
                k = 1.0 - k
            k = 0.5 + (k - 0.5) * g.arm_amp
        fwd = np.array(g.arm_fwd) * [s * -1, 1, 1]
        back = np.array(g.arm_back) * [s * 1, 1, 1]
        # The fist swings on an arc about the shoulder, the arm's reach
        # changing only as the elbow opens and closes (a straight line from
        # behind to in front would fold the arm up through the shoulder and
        # spin the forearm), a touch higher through the middle.
        if g.swing is not None:
            hand = _swung(g.swing_r if side == "r" and g.swing_r is not None else g.swing, rig, side, k)
            if side in g.arms:
                hand = g.arms[side](ph, k, hand)
            pose[f"hand_{side}"] = hand
            pose[f"clav_{side}"] = (g.shoulders[0] + 2.5 * (1 - k), g.shoulders[1] + 9 * (k - 0.5))
            continue
        e = _ease(k)
        nb, nf = np.linalg.norm(back), np.linalg.norm(fwd)
        db, df = back / nb, fwd / nf
        ang = math.acos(max(-1.0, min(1.0, float(np.dot(db, df)))))
        if ang > 1e-4:
            d = (math.sin((1 - e) * ang) * db + math.sin(e * ang) * df) / math.sin(ang)
        else:
            d = db
        v = d * (nb + (nf - nb) * e)
        v[1] += 0.04 * math.sin(math.pi * k)
        hand = {"arc": arc_of(v), "pole": (s * g.elbow_out, -0.2, -1.0)}
        if side in g.arms:
            hand = g.arms[side](ph, k, hand)
        pose[f"hand_{side}"] = hand
        # The shoulder goes with its arm: forward as the arm drives through,
        # drawn back and a touch higher behind.
        pose[f"clav_{side}"] = (g.shoulders[0] + 2.5 * (1 - k), g.shoulders[1] + 9 * (k - 0.5))
    if g.travel:
        _off_travel(g, rig, ph, pose)
    return pose


def _q2e(q):
    """rig.qeuler's (yaw, pitch, roll) of a quaternion (R = yaw . pitch . roll)."""
    from rig import qmatrix
    R = np.asarray(qmatrix(q), float)[:3, :3]
    pitch = math.degrees(math.asin(max(-1.0, min(1.0, -R[1, 2]))))
    yaw = math.degrees(math.atan2(R[0, 2], R[2, 2]))
    roll = math.degrees(math.atan2(R[1, 0], R[1, 1]))
    return yaw, pitch, roll


def _off_travel(g: Gait, rig: Rig, ph, pose):
    """pose_at's legs, pelvis, spine and head for a run `g.travel` off her facing (the arms are pose_at's, in the
    chest's frame): the feet and pelvis on the travel, the chest and head turned back to the aim (see Gait.travel)."""
    from rig import qeuler, qinv, qmul
    tr = g.travel % 360
    back = abs(tr - 180) < 45
    psi = -((tr + 180) % 360 - 180)          # the travel's yaw in her frame (+ to her left)
    c = math.cos(2 * math.pi * ph)
    d2 = g.duty / 2
    y = -g.drop - g.bob / 2 * math.cos(4 * math.pi * (ph - d2))
    x = g.hip_shift * math.cos(2 * math.pi * (ph - d2))
    roll_sw = g.hip_roll * math.cos(2 * math.pi * (ph - d2))
    I = rig.I
    if back:
        # The pelvis turns with the swinging leg, which now swings back: the other way round.
        p_yaw = g.hip_yaw * c
        pel = qeuler(p_yaw, g.hip_tilt, roll_sw)
        chest = qeuler(-g.chest_yaw * c, g.chest_lean, 0.0)
        hp = (x, y, 0.0)
    else:
        turn = psi * g.side_hips / 90.0
        rel = math.radians(psi - turn)       # travel's yaw from the pelvis's forward
        p_yaw = turn - g.hip_yaw * c
        pel = qeuler(p_yaw, g.hip_tilt * math.cos(rel), -g.hip_tilt * math.sin(rel) + roll_sw)
        side = -math.copysign(1.0, psi)      # + travelling to her right (roll + tips her right)
        chest = qeuler(g.chest_yaw * c, g.chest_lean, side * g.side_lean)
        pr = math.radians(psi)               # over the standing foot: across the travel, not across her
        hp = (x * math.cos(pr), y, -x * math.sin(pr))
    sp = _q2e(qmul(qinv(pel), chest))
    pose["hips"] = {"pos": hp, "rot": _q2e(pel)}
    pose["spine"] = sp
    cy, cp, cr = _q2e(chest)
    pose["neck"] = (0, -cp * 0.4, -cr * 0.4)
    pose["head"] = (-cy * 0.8, -cp * 0.5 - g.head_up, -cr * 0.5)
    rest = {s: rig.prest[I[f"foot_{s}"]] for s in "lr"}
    ball = {s: rig.prest[I[f"ball_{s}"]] - rig.prest[I[f"foot_{s}"]] for s in "lr"}
    for side, off in (("l", 0.0), ("r", 0.5)):
        s = 1 if side == "l" else -1
        a, pitch, toe = foot(g, ph - off)
        if back:
            u = (ph - off) % 1.0
            if u < g.duty:
                v = u / g.duty
                pitch = -g.back_toe * (1 - v) ** 2 - 4 * math.sin(math.pi * v) - (g.back_toe + 4) * max(0.0, (v - 0.5) / 0.5) ** 2
                pitch = min(pitch, -2.0)
                toe = -pitch
            else:
                v = (u - g.duty) / (1 - g.duty)
                pitch = float(_spline([(0.0, -g.back_toe - 4), (0.3, -g.back_toe - 14), (0.7, -g.back_toe - 6),
                                       (1.0, -g.back_toe)], v)[0])
                toe = float(_spline([(0.0, g.back_toe + 4), (0.35, 0.0), (0.75, 0.0), (1.0, g.back_toe)], v)[0])
            # Heel up on the forefoot: the ankle raised and moved so the ball holds its place (its rest offset turned).
            b = math.radians(-pitch)
            bl = ball[side]
            dy = bl[1] * (1 - math.cos(b)) + bl[2] * math.sin(b)
            dz = bl[2] * (1 - math.cos(b)) - bl[1] * math.sin(b)
            fx, fy, fz = s * g.width + a[0], a[1] + max(0.0, dy), -a[2] + dz
            yaw_f = s * 4
            pole = (s * 0.1, 0, 1)
        else:
            lead = (s < 0) == (psi < 0)      # the foot on the side she travels toward
            # The travel frame's (out, forward) turned to her frame by psi (+ yaw: forward toward her left).
            # Each foot's path follows its own hip socket along the travel (the turned pelvis puts the trail hip
            # behind: on the run's shared spot its leg reached across her, landing locked straight).
            sx = float(rig.prest[I[f"thigh_{side}"]][0])
            ox, oz = s * g.width + a[0], a[2] + sx * math.sin(math.radians(psi - turn))
            pr = math.radians(psi)
            fx = ox * math.cos(pr) + oz * math.sin(pr)
            fz = -ox * math.sin(pr) + oz * math.cos(pr)
            fy = a[1]
            yaw_f = turn * (g.toe_lead if lead else g.toe_trail)
            yr = math.radians(yaw_f)
            pole = (math.sin(yr) + s * 0.1 * math.cos(yr), 0, math.cos(yr) - s * 0.1 * math.sin(yr))
        pose[f"foot_{side}"] = {"pos": (fx, fy, fz), "rot": (yaw_f, -pitch, 0), "toe": toe, "pole": pole}
    return pose


def _rotv(v, axis, deg):
    a = np.asarray(axis, float)
    a = a / np.linalg.norm(a)
    t = math.radians(deg)
    return v * math.cos(t) + np.cross(a, v) * math.sin(t) + a * float(np.dot(a, v)) * (1 - math.cos(t))


def arm_joints(th, out, el, turn, lu, lf):
    """Her left arm by its joints, in the chest's frame from the shoulder (x out to her left, y up, z
    forward): the upper arm `th` degrees forward of hanging and `out` from her side, the elbow's inside
    angle `el`, the upper arm turned in by `turn` (the forearm swung toward her middle). (elbow, hand)."""
    u = _rotv(_rotv(np.array([0.0, -1.0, 0.0]), [1, 0, 0], -th), [0, 0, 1], out)
    hinge = _rotv(_rotv(_rotv(np.array([1.0, 0, 0]), [1, 0, 0], -th), [0, 0, 1], out), u, turn)
    f = _rotv(u, hinge, -(180 - el))
    return u * lu, u * lu + f * lf


def _swung(swing, rig, side, k):
    """The hand spec for an arm keyed by its joints (Gait.swing), k 1 fully forward: the hand where those
    joints put it, the elbow's way from the shoulder as the pole (exactly where it goes)."""
    fw, bk = np.array(swing[0], float), np.array(swing[1], float)
    th, out, el, turn = bk + (fw - bk) * k
    I = rig.I
    lu = float(np.linalg.norm(rig.prest[I[f"lowerarm_{side}"]] - rig.prest[I[f"upperarm_{side}"]]))
    lf = float(np.linalg.norm(rig.prest[I[f"hand_{side}"]] - rig.prest[I[f"lowerarm_{side}"]]))
    E, H = arm_joints(th, out, el, turn, lu, lf)
    m = np.array([1.0 if side == "l" else -1.0, 1, 1])
    E, H = E * m, H * m
    return {"arc": arc_of(H), "pole": tuple(E / np.linalg.norm(E)), "pole_at": "shoulder", "frame": "chest"}


def _ease(k):
    return k * k * (3 - 2 * k)


def run_cycle(name, rig: Rig, g: Gait, meta=None) -> Clip:
    from keyed import solve_frames
    n = g.frames
    # (A meta "grip_slide" / "grip_slide_l": the piece slid in her fist; "grip_tilt" / "grip_tilt_l" (animation 58): turned
    # in it about the palm's normal, keyed.solve_frames; 0 solves as before.)
    mt = meta or {}
    rot, pos = solve_frames(rig, [pose_at(g, rig, f / n) for f in range(n + 1)], loop=True,
                            weapon=mt.get("weapon", ""), slide=float(mt.get("grip_slide", 0.0)),
                            slide_l=float(mt.get("grip_slide_l", 0.0)), tilt=float(mt.get("grip_tilt", 0.0)),
                            tilt_l=float(mt.get("grip_tilt_l", 0.0)))
    m = {"layer": "full", "speed": g.speed, "cycle": n / 30.0, "steps": 2,
         "source": "keyed (tools/anim/gait.py)", "licence": "own work"}
    m.update(meta or {})
    return Clip(name, 30, rot, pos, loop=True, meta=m)
