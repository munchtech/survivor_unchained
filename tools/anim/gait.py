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
    fingers: str = "relaxed"
    head_up: float = 0.0         # chin raised (+) beyond level
    shoulders: tuple = (0, 0)    # clavicles (raise, forward)
    arms: dict = field(default_factory=dict)  # per side overrides: {"r": callable(phase, pose)->hand spec}


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
        y += 0.10 * max(0.0, (u - 0.6) / 0.4) ** 2
        return np.array([0.0, y, z]), pitch, 0.0
    s = (ph - g.duty) / (1 - g.duty)
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
        "fingers_l": g.fingers, "fingers_r": g.fingers,
    }
    for side, off in (("l", 0.0), ("r", 0.5)):
        s = 1 if side == "l" else -1
        a, pitch, toe = foot(g, ph - off)
        rest = rig.prest[rig.I[f"foot_{side}"]]
        pose[f"foot_{side}"] = {"pos": (s * g.width + a[0], a[1], a[2]), "rot": (s * 4, -pitch, 0), "toe": toe,
                                "pole": (s * 0.1, 0, 1)}
        # Arms against the legs: the left fist forward as the right foot lands.
        k = 0.5 - 0.5 * math.cos(2 * math.pi * (ph - off - 0.5))  # 1: this arm fully forward
        fwd = np.array(g.arm_fwd) * [s * -1, 1, 1]
        back = np.array(g.arm_back) * [s * 1, 1, 1]
        # The fist swings on an arc about the shoulder, the arm's reach
        # changing only as the elbow opens and closes (a straight line from
        # behind to in front would fold the arm up through the shoulder and
        # spin the forearm), a touch higher through the middle.
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
    return pose


def _ease(k):
    return k * k * (3 - 2 * k)


def run_cycle(name, rig: Rig, g: Gait, meta=None) -> Clip:
    from keyed import solve_frames
    n = g.frames
    rot, pos = solve_frames(rig, [pose_at(g, rig, f / n) for f in range(n + 1)], loop=True)
    m = {"layer": "full", "speed": g.speed, "cycle": n / 30.0, "steps": 2,
         "source": "keyed (tools/anim/gait.py)", "licence": "own work"}
    m.update(meta or {})
    return Clip(name, 30, rot, pos, loop=True, meta=m)
