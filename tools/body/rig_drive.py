"""The lbs poser's default driver: the rig.json "correctives" table, nothing else.

A rig build replaces this by naming its own module in rig.json ("poser": "tools.body.<module>") with the same entry
point:  drive(poser, G, rig) -> (G, {shape name: weight}).  G [B,4,4] are the posed bone worlds (the poser's bone
order, poser.names); a driver may move helper bones (twists, shares) in G and return the shapes' weights.

A corrective row (as godot/art/people/rig_helpers.json "correctives"):
  {"name": "elbow_fix_{s}", "bone": "lowerarm_{s}", "from": 90, "to": 145}            smoothstep from..to
  {"name": "elbow_psd90_{s}", "bone": "lowerarm_{s}", "keys": [45, 90, 135]}          0 at lo, 1 at at, 0 at hi
  "on": "swing" (default: the bone's swing off its rest, its turn about its own line left out), "flex" (its rest
  line seen along its own X, toward +Z), or "angle" (the whole rotation's angle). "{s}" expands to l and r.
  "smoothstep": false makes the from..to ramp linear.
"""
from __future__ import annotations

import math

import numpy as np


def _local(poser, G, j):
    p = poser.parent[j]
    return G[j] if p < 0 else np.linalg.inv(G[p]) @ G[j]


def _unit(M):
    M = M[:3, :3]
    return M / np.linalg.norm(M, axis=0)


def angle_of(poser, G, j, on="swing"):
    R0 = _unit(_local(poser, poser.rest, j))
    R1 = _unit(_local(poser, G, j))
    d = R0.T @ R1                     # the turn in the bone's rest frame
    if on == "angle":
        return math.degrees(math.acos(max(-1.0, min(1.0, (np.trace(d) - 1) / 2))))
    y = d[:, 1]
    if on == "flex":
        return math.degrees(math.atan2(y[2], y[1]))
    return math.degrees(math.acos(max(-1.0, min(1.0, y[1]))))


def weight(c, deg):
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


def drive(poser, G, rig):
    out = {}
    for c in rig.get("correctives", []):
        for s in ("l", "r") if "{s}" in c["bone"] else ("",):
            b = c["bone"].replace("{s}", s)
            j = poser.index.get(b)
            if j is None:
                continue
            out[c["name"].replace("{s}", s)] = weight(c, angle_of(poser, G, j, c.get("on", "swing")))
    return G, out
