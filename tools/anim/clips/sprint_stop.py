"""Faster than her run, and stopping out of it.

- sprint_<calling>[_<weapon>]: each run's own carriage pushed: a longer, lower stride,
  more lean, the arms driving harder. The same number of frames as her run,
  in step with it (the left foot lands at the start of both), so the game
  can blend the two by speed without the legs fighting.
- stop_<calling>_l / _r: out of the run onto the front foot (the left or
  the right, whichever was coming down), the body carried on over it and
  braking back, the back foot brought through beside it, a rebound, and the
  weight settling, the arms in the calling's hold throughout.
"""
from __future__ import annotations

from dataclasses import replace

import numpy as np

from clips import idle
from clips.run import RUNS, SPRINT_ARMS
from gait import arc_of, run_cycle
from keyed import build

CALLINGS = {"warden": "run_warden", "arcanist": "run_arcanist", "reaver": "run_reaver", "stalker": "run_stalker",
            "warden_town": "run_warden_town"}


def sprint(rig, run):
    """The sprint for one of her runs (run_<calling>[_<weapon>])."""
    g, arms, weapon = RUNS[run]
    arms = {**arms, **SPRINT_ARMS.get(run, {})}
    # The arms drive further, but the elbow stays bent, as a sprinter's does:
    # an arm flung out straight behind her has no hinge to read, and the
    # forearm rolled over as it bent again.
    I = rig.I
    reach = 0.85 * sum(float(np.linalg.norm(rig.prest[I[b]] - rig.prest[I[a]]))
                       for a, b in (("upperarm_r", "lowerarm_r"), ("lowerarm_r", "hand_r")))

    def held(v):
        v = np.array(v, float)
        n = float(np.linalg.norm(v))
        return tuple(v * min(1.0, reach / n))

    s = replace(g, arms=arms, speed=g.speed * 1.45, duty=g.duty - 0.05, lean=g.lean + 8, kick=g.kick + 0.06,
                knee=g.knee + 0.06, reach=g.reach + 0.08, bob=g.bob + 0.01,
                arm_fwd=held(np.array(g.arm_fwd) * [1, 0.8, 1.2]), arm_back=held(np.array(g.arm_back) * [1, 1.1, 1.25]))
    return run_cycle("sprint" + run[3:], rig, s, {"weapon": weapon})


# The stops' left fingers closed onto her hip frame by frame (deg; idle.hip_layer's `curl`): with the hand kept on her
# pelvis they stood 4-10 mm off as her legs braked under them, the little finger 2.9 mm in at stop_l f4 (judge
# l31-hip). Fitted from the gaps (atan((gap - 1.8 mm) / finger length), 3-frame smoothed, neighbours within 3 deg).
ARC_STOP_CURL = {
    "l": {
        "index": [4.0, 4.2, 4.5, 4.8, 4.7, 4.7, 4.5, 4.3, 4.2, 3.9, 3.7, 3.5, 3.3, 2.9, 2.6, 2.2, 2.0, 1.9, 1.8, 1.7, 1.7, 1.7, 1.7, 1.7, 1.7],
        "middle": [4.7, 5.0, 5.5, 5.7, 6.0, 5.9, 5.5, 5.2, 5.0, 4.8, 4.5, 4.3, 4.0, 3.7, 3.4, 3.2, 3.0, 2.8, 2.7, 2.6, 2.6, 2.6, 2.6, 2.6, 2.6],
        "ring": [5.4, 6.0, 6.6, 6.5, 6.6, 6.6, 6.2, 5.7, 5.6, 5.2, 4.8, 4.5, 4.1, 3.5, 3.1, 2.6, 2.4, 2.1, 2.0, 2.0, 2.0, 1.9, 1.9, 1.9, 1.9],
        "pinky": [3.4, 5.0, 7.1, 7.0, 7.1, 7.1, 5.2, 4.7, 2.7, 0.7, 2.6, 4.9, 7.4, 8.0, 8.0, 8.0, 7.4, 7.1, 6.8, 6.7, 6.6, 6.5, 6.6, 6.6, 6.6],
    },
    "r": {
        "index": [-1.4, -1.1, -0.5, 0.2, 0.8, 1.7, 2.3, 2.8, 2.7, 2.6, 2.3, 2.1, 2.0, 1.8, 1.6, 1.4, 1.2, 1.1, 1.0, 0.9, 0.9, 0.8, 0.8, 0.8, 0.8],
        "middle": [-0.7, -0.4, 0.1, 0.8, 1.6, 2.4, 2.9, 3.3, 3.4, 3.4, 3.3, 3.1, 2.9, 2.7, 2.4, 2.2, 2.0, 1.9, 1.7, 1.6, 1.6, 1.5, 1.5, 1.5, 1.5],
        "ring": [-1.1, -1.0, -0.7, -0.2, 0.5, 1.6, 2.5, 3.1, 3.1, 3.0, 2.8, 2.7, 2.5, 2.3, 2.1, 1.8, 1.5, 1.2, 1.0, 0.8, 0.7, 0.6, 0.6, 0.6, 0.6],
        "pinky": [-0.7, -0.7, 0.2, 1.5, 3.7, 5.8, 8.0, 8.0, 8.0, 8.0, 8.0, 8.0, 7.5, 7.1, 6.4, 5.8, 5.3, 4.9, 4.6, 4.2, 3.9, 3.6, 3.6, 3.6, 3.6],
    },
}


def stop(rig, calling, side):
    """Planting the `side` foot out of the run."""
    arms = idle.IDLES[f"idle_{calling}"][1](0, 0)
    if calling == "arcanist":
        # The staff's head leant out past her hat's brim: braking, her head and hat pitch over the fist (13 Oct, with
        # the staff seated in the fist's hollow, the idle's lean put the head 1 mm into the brim).
        arms["hand_r"] = {**arms["hand_r"], "blade": idle._n((-0.10, 1.0, 0.04))}
    s = 1 if side == "l" else -1
    front, back = f"foot_{side}", f"foot_{'r' if side == 'l' else 'l'}"
    w = 0.09 if calling == "warden" else 0.05

    def p(fz, bz, by, btoe, hy, hz, lean, roll=0.0, brot=-25, out=0.0):
        a = arms
        if out and calling == "warden":
            # The sword hand carried 15 mm out from her right thigh through the stop (14 Oct: with the hilt seated in
            # the fist's hollow, 12 mm nearer the palm, it came 7-12 mm from the thigh, inside the skirt, as she
            # landed, braked and settled with her hips forward; the game blends the stop's ends with the run and idle).
            a = {**arms, "hand_r": {**arms["hand_r"], "arc": arc_of(np.add(idle.WARDEN_HAND_R, (-out, 0.0, 0.0)))}}
        return {**a,
                front: {"pos": (s * w, 0, fz), "rot": (s * 6, 0, 0)},
                back: {"pos": (-s * (w + 0.06), by, bz), "rot": (-s * 10, brot, 0), "toe": btoe},
                "hips": {"pos": (s * 0.02, hy, hz), "rot": (s * 4, lean * 0.4, roll)},
                "spine": (0, lean * 0.6, -roll), "head": (0, -lean * 0.5, 0)}

    keys = [
        # Coming down on the front foot, the back leg still behind.
        (0, p(0.34, -0.48, 0.12, 25, -0.08, 0.04, 16, out=0.015), "auto"),
        # Over it and braking: the body carried on, the back foot coming through.
        (5, p(0.30, -0.12, 0.10, 10, -0.13, 0.12, 4, roll=2, out=0.015), "auto"),
        # Down beside it, the weight back on the heels, the lean thrown back.
        (9, p(0.26, 0.10, 0.0, 0, -0.12, 0.10, -7, brot=0, out=0.015), "auto"),
        # The rebound and the settle.
        (15, p(0.20, 0.06, 0.0, 0, -0.05, 0.06, 4, brot=0, out=0.015), "auto"),
        (24, p(0.16, 0.00, 0.0, 0, -0.04, 0.03, 1, brot=0, out=0.015), "ease"),
    ]
    clip = build(f"stop_{calling}_{side}", rig, keys, meta={"layer": "full", "weapon": idle.IDLES[f"idle_{calling}"][2]})
    if calling == "arcanist":
        # Her left hand kept on her hip as the hips brake and rock under her (it floated 10-17 mm off in the chest's frame).
        clip = idle.hip_layer(rig, clip, lambda f: 1.0, curl=ARC_STOP_CURL[side])
    return clip


def clips(rig, want):
    out = []
    for run in RUNS:
        name = "sprint" + run[3:]
        if not want or any(w in name for w in want):
            out.append(sprint(rig, run))
    for c in CALLINGS:
        for side in "lr":
            name = f"stop_{c}_{side}"
            if not want or any(w in name for w in want):
                out.append(stop(rig, c, side))
    return out
