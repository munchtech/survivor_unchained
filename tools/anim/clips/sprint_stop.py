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
from clips.run import RUNS
from gait import run_cycle
from keyed import build

CALLINGS = {"warden": "run_warden", "arcanist": "run_arcanist", "reaver": "run_reaver", "stalker": "run_stalker"}


def sprint(rig, run):
    """The sprint for one of her runs (run_<calling>[_<weapon>])."""
    g, arms, weapon = RUNS[run]
    s = replace(g, arms=arms, speed=g.speed * 1.45, duty=g.duty - 0.05, lean=g.lean + 8, kick=g.kick + 0.06,
                knee=g.knee + 0.06, reach=g.reach + 0.08, bob=g.bob + 0.01,
                arm_fwd=tuple(np.array(g.arm_fwd) * [1, 0.8, 1.2]), arm_back=tuple(np.array(g.arm_back) * [1, 1.1, 1.25]))
    return run_cycle("sprint" + run[3:], rig, s, {"weapon": weapon})


def stop(rig, calling, side):
    """Planting the `side` foot out of the run."""
    arms = idle.IDLES[f"idle_{calling}"][1](0, 0)
    s = 1 if side == "l" else -1
    front, back = f"foot_{side}", f"foot_{'r' if side == 'l' else 'l'}"
    w = 0.09 if calling == "warden" else 0.05

    def p(fz, bz, by, btoe, hy, hz, lean, roll=0.0, brot=-25):
        return {**arms,
                front: {"pos": (s * w, 0, fz), "rot": (s * 6, 0, 0)},
                back: {"pos": (-s * (w + 0.06), by, bz), "rot": (-s * 10, brot, 0), "toe": btoe},
                "hips": {"pos": (s * 0.02, hy, hz), "rot": (s * 4, lean * 0.4, roll)},
                "spine": (0, lean * 0.6, -roll), "head": (0, -lean * 0.5, 0)}

    keys = [
        # Coming down on the front foot, the back leg still behind.
        (0, p(0.34, -0.48, 0.12, 25, -0.08, 0.04, 16), "auto"),
        # Over it and braking: the body carried on, the back foot coming through.
        (5, p(0.30, -0.12, 0.10, 10, -0.13, 0.12, 4, roll=2), "auto"),
        # Down beside it, the weight back on the heels, the lean thrown back.
        (9, p(0.26, 0.10, 0.0, 0, -0.12, 0.10, -7, brot=0), "auto"),
        # The rebound and the settle.
        (15, p(0.20, 0.06, 0.0, 0, -0.05, 0.06, 4, brot=0), "auto"),
        (24, p(0.16, 0.00, 0.0, 0, -0.04, 0.03, 1, brot=0), "ease"),
    ]
    return build(f"stop_{calling}_{side}", rig, keys, meta={"layer": "full"})


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
