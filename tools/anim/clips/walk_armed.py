"""Her armed walks (Animation 53): walk_<calling> for each calling's own weapon and walk_<calling>_<kind> for each kind
with its own run (run.RUNS), the names OwnClips.Walk asks for drawn (Sheath.Names, sheathed false). Without them the
game blended her armed idle into her armed run slowed to 0.55x, a slow-motion run.

Each is her calling's town walk (walk_town.make_walk: the same legs, pelvis, trunk and head, the reaver's swagger, the
same loop from the left heel strike and the same speed, so Stride keeps walk and run in one phase) with the arms that
hold something laid over it: solved afresh frame by frame (keyed.solve_frames, the town walk as the base) to a hand
keyed in the chest's frame, as the armed idles and runs key theirs. A walk's carriage is calmer than the run's: the
weapon hand rides near where her armed idle holds it, swinging a few centimetres with the stride, in step with the free
arm's swing (half a cycle from it: `k` below is the town walk's own swing on that side, 1 fully forward); a shield arm
stays braced at her side; a two-handed carry rides low and steady. A free arm keeps the town walk's swing.
"""
from __future__ import annotations

import math

import numpy as np

from gait import arc_of
from rig import Clip, qrot

from clips import walk_town as wt


def _n(v):
    v = np.asarray(v, float)
    return tuple(v / np.linalg.norm(v))


def _at(rest, swing, k, lift=0.0):
    """A hand (chest frame, from the shoulder) `rest` carried `swing` (m, fore and aft, the hand's whole travel) with the
    stride, k 1 fully forward, rising `lift` (m) through the middle of the swing as a pendulum's hand does."""
    r = np.array(rest, float)
    r[2] += swing * (k - 0.5)
    r[1] += lift * (1.0 - (2.0 * k - 1.0) ** 2)
    return r


# ---------------------------------------------------------------- carriages --
# Each: (k, frame) -> the hand's spec (keyed.Rig.solve), k the town walk's swing on that side.

def sword(k, f):
    """The sword low at her right, as her armed idle holds it (idle.warden: the point 34 deg below level ahead, the
    thumb forward, the elbow swung out over the hilt), the fist swinging a little with the stride."""
    return {"arc": arc_of(_at((-0.12, -0.45, 0.04), 0.08, k, 0.01)), "pole": (-0.744, 0.09, -0.662), "frame": "chest",
            "blade": _n((-0.30, -0.52, 0.80)), "knuckles": _n((0.123, -0.828, -0.548)), "twist": 0.5}


def shield(k, f):
    """The shield at rest at her left side, off her body (idle.warden's hand_l), braced, riding the step a little."""
    return {"arc": arc_of(_at((0.0817, -0.3796, 0.1299), 0.02, k)), "pole": (0.3281, -0.4168, -0.8477), "frame": "chest",
            "thumb": (-0.1498, 0.7455, 0.6495), "twist": 1.0}


def axe(side):
    """An axe in the hand at her side, the arm near hanging and swinging a little, the head ahead and down, out from
    her leg."""
    sg = 1.0 if side == "l" else -1.0

    def f(k, fr):
        return {"arc": arc_of(_at((sg * 0.10, -0.46, 0.05), 0.08, k, 0.01)), "pole": (sg * 0.5, -0.2, -1.0),
                "frame": "chest", "blade": _n((sg * 0.25, -0.45, 0.86)), "twist": 0.5}
    return f


def staff(k, f):
    """The staff upright in her right fist at her side, tipped forward (run.staff_hold), the arm barely swinging."""
    return {"arc": arc_of(_at((-0.10, -0.40, 0.10), 0.03, k)), "pole": (-0.3, -0.1, -1.0),
            "blade": (0.05, 0.94, 0.33), "knuckles": (0.0, -0.33, 0.94), "frame": "chest", "twist": 0.5}


def wand(k, f):
    """The wand in her right fist, the arm near hanging and swinging a little, the wand pointing ahead and down."""
    return {"arc": arc_of(_at((-0.10, -0.46, 0.06), 0.10, k, 0.01)), "pole": (-0.5, -0.2, -1.0), "frame": "chest",
            "blade": _n((-0.15, -0.35, 0.92)), "twist": 0.5}


def crossbow_r(k, f):
    """The crossbow low ahead of her in both hands (idle.stalker's carry), steady, the right fist on its grip."""
    from clips.idle import STALKER_HAND_R
    h = dict(STALKER_HAND_R["hand_r"])
    return h


def crossbow_l(k, f):
    from clips.idle import STALKER_HAND_L
    return dict(STALKER_HAND_L["hand_l"])


def dagger(side):
    """A dagger in each fist, the arms near hanging and swinging with the stride, the blade rising ahead and out."""
    sg = 1.0 if side == "l" else -1.0

    def f(k, fr):
        return {"arc": arc_of(_at((sg * 0.10, -0.45, 0.07), 0.12, k, 0.01)), "pole": (sg * 0.5, -0.2, -1.0),
                "frame": "chest", "thumb": _n((sg * 0.25, 0.55, 0.8)), "twist": 0.5}
    return f


# name: (calling, {side: carriage}, {side: fingers}, weapon (keyed.grip_of))
WALKS = {
    "walk_warden": ("warden", {"r": sword, "l": shield},
                    {"r": "grip", "l": {"curl": 0.95, "cascade": 0.05, "thumb": 1.6, "oppose": 0.9}}, "sword+shield"),
    "walk_reaver": ("reaver", {"r": axe("r")}, {"r": "grip"}, "axe"),
    "walk_reaver_axes": ("reaver", {"r": axe("r"), "l": axe("l")}, {"r": "grip", "l": "grip"}, "axes"),
    "walk_arcanist": ("arcanist", {"r": staff}, {"r": "grip"}, "staff"),
    "walk_arcanist_wand": ("arcanist", {"r": wand}, {"r": "grip"}, "wand"),
    "walk_stalker": ("stalker", {"r": crossbow_r, "l": crossbow_l}, {"r": "grip", "l": "relaxed"}, "crossbow"),
    "walk_stalker_daggers": ("stalker", {"r": dagger("r"), "l": dagger("l")}, {"r": "grip", "l": "grip"}, "daggers"),
}
_TOWN = {}


def _swing_k(rig, clip):
    """Each side's swing on the town walk, 0 fully back .. 1 fully forward, per frame."""
    g, p = rig.sk.fk(clip.rot, clip.pos)
    out = {}
    for s in "lr":
        sw, _, _ = wt._arm_angles(g, p, rig.I, s)
        out[s] = (sw - sw.min()) / max(np.ptp(sw), 1e-6)
    return out


# Which way each carriage's hand is let out where her forearm or hand comes too near her or her own outfit (chest
# frame; x toward her left): out from her side, the crossbow's two hands together and ahead (LINKED: one piece).
OUT = {"r": (-1.0, 0.0, 0.0), "l": (1.0, 0.0, 0.0)}
PUSH = {"walk_stalker": {"r": (0.0, 0.0, 1.0), "l": (0.0, 0.0, 1.0)}}
LINKED = {"walk_stalker"}
OUTFIT = {"warden": "warden", "reaver": "reaver", "arcanist": "arcanist", "stalker": "ranger"}
_LAST = {}  # per clip: the hands' push (m, per side per frame) and the arms' clearance after it (read by the checks)


def _solve(rig, name, town, k, push):
    from keyed import solve_frames
    calling, arms, fingers, weapon = WALKS[name]
    rot, pos = town.rot.copy(), town.pos.copy()
    n = len(rot) - 1  # the closing frame is the first again
    way = PUSH.get(name, OUT)
    specs = []
    for f in range(n):
        sp = {}
        for s, carry in arms.items():
            h = dict(carry(float(k[s][f]), f))
            if push[s][f] > 0:
                from gait import arc_of as _arc
                az, el, r = h["arc"]
                a, e = math.radians(az), math.radians(el)
                v = r * np.array([math.sin(a) * math.cos(e), math.sin(e), math.cos(a) * math.cos(e)])
                h["arc"] = _arc(v + push[s][f] * np.array(way[s], float))
            sp[f"hand_{s}"] = h
            sp[f"fingers_{s}"] = fingers[s]
        specs.append(sp)
    srot, _ = solve_frames(rig, specs, [(rot[f], pos[f]) for f in range(n)], loop=True, weapon=weapon)
    I = rig.I
    for s in arms:
        chain = [I[f"upperarm_{s}"]]
        for j in chain:
            chain += [c for c, q in enumerate(rig.sk.parent) if q == j and c not in chain]
        for f in range(n):
            rot[f, chain] = srot[f, chain]
    rot[n] = rot[0]
    return rot, pos


def make(rig, name, rounds=6):
    calling, arms, fingers, weapon = WALKS[name]
    if calling not in _TOWN:
        _TOWN[calling] = wt.make_walk(rig, calling)
    town = _TOWN[calling]
    n = len(town.rot) - 1
    k = _swing_k(rig, town)
    push = {s: np.zeros(n) for s in "lr"}
    c = {"outfit": OUTFIT[calling]}
    # The hands let out where (and as much as) her real mesh needs: the forearm and hand wt.NEAR clear of her and her
    # own outfit (walk_town._clear's measure), eased over the frames around.
    for _ in range(rounds):
        rot, pos = _solve(rig, name, town, k, push)
        near = wt._near(wt.Walk(rig, rot[:n], pos[:n], town.meta["speed"]), c)
        need = {s: np.maximum(wt.NEAR + 0.002 - near[s], 0.0) if s in arms else np.zeros(n) for s in "lr"}
        if name in LINKED:
            both = np.maximum(need["l"], need["r"])
            need = {"l": both, "r": both}
        if max(need[s].max() for s in arms) < 0.0005:
            break
        for s in arms:
            add = need[s].copy()
            for _k in range(6):
                add = np.maximum(wt._smooth(add, 1.0), need[s])
            push[s] = push[s] + add
    _LAST[name] = dict(push=push, near=near)
    meta = dict(town.meta)
    meta.update({"weapon": weapon,
                 "changes": town.meta["changes"] + "; the weapon arms keyed to an armed carriage (tools/anim/clips/walk_armed.py)",
                 "note": f"her armed walk, {calling} ({weapon}); her town walk's gait; loop starts at the left heel strike"})
    return Clip(name, 30, rot, pos, loop=True, meta=meta)


def clips(rig, want):
    return [make(rig, name) for name in WALKS if not want or any(x in name for x in want)]
