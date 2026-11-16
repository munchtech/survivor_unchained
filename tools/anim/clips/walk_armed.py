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


def _pitch(v, deg):
    """v turned `deg` about the chest's x (her left): + tips its forward part up."""
    a = math.radians(deg)
    x, y, z = v
    return (x, y * math.cos(a) + z * math.sin(a), -y * math.sin(a) + z * math.cos(a))


# Each side's swing velocity (-1..1, + coming forward) and its swing `LAG` frames late, per frame (set by make()).
_CTX = {}
LAG = 2.5


# ---------------------------------------------------------------- carriages --
# Each: (k, frame) -> the hand's spec (keyed.Rig.solve), k the town walk's swing on that side.

def _arc_v(arc):
    az, el, r = arc
    a, e = math.radians(az), math.radians(el)
    return r * np.array([math.sin(a) * math.cos(e), math.sin(e), math.cos(a) * math.cos(e)])


# Prowl's hands (prowl.end_keys frame 0, chest frame; set by make() when her idle is Prowl): the walk carries the sword
# as Prowl holds it, the elbow soft, the arm live: the fist swings PROWL_SWING m with the stride from the shoulder, the
# point trailing the fist PROWL_LAG deg as it comes through (the owner, 15 Nov: "held rigid not moving at all").
_PROWL = {}
PROWL_SWING = 9.0  # deg either way about the shoulder (the reach kept: the elbow stays at Prowl's bend)
PROWL_LAG = 7.0


def _prowl_hand(side, k, f, swing, lag):
    """Prowl's hand swung `swing` deg about the shoulder's left-right line with the stride (the whole arm and the blade
    turning with it), the point trailing a further `lag` deg as the fist comes through."""
    h = {kk: v for kk, v in _PROWL[side].items()}
    a = swing * (2.0 * k - 1.0)
    h["arc"] = arc_of(np.array(_pitch(_arc_v(h["arc"]), a)))
    d = -lag * float(_CTX[side][0][f]) if lag else 0.0
    for kk in ("blade", "knuckles", "pole"):
        if kk in h:
            h[kk] = _pitch(h[kk], a + (d if kk != "pole" else 0.0))
    return h


def _trail_hand(k, f):
    """(solver 3a, 15 Nov; prowl.TRAIL) Prowl's trailing sword arm by its joints (prowl.TRAIL_ARM, chest frame): the
    upper arm swung PROWL_SWING deg about the shoulder with the stride, the elbow bending 33-41 (more as the fist comes
    forward), the fist's grip (prowl.TRAIL_GRIP) turned with the forearm so the wrist keeps Prowl's set, the point
    trailing a further PROWL_LAG deg as the fist comes through."""
    from clips import prowl
    from gait import arm_joints
    from rig import qaxis, qbetween, qmul
    th, out, el, turn = prowl.TRAIL_ARM
    lu, lf = _CTX["arm"]
    m = np.array([-1.0, 1, 1])
    E0, H0 = arm_joints(th, out, el, turn, lu, lf)
    E, H = arm_joints(th + PROWL_SWING * (2.0 * k - 1.0), out, el - 8.0 * k, turn, lu, lf)
    # (solver 4a) where her mesh needs the fist let out (_solve's push, m), the whole arm swung that much further out
    # from her side about the shoulder (the reach and the elbow's bend kept; the push laid on the wrist as a longer
    # reach straightened the elbow to 4 deg and turned the wrist past armroll's caps)
    p = float(_CTX.get("push_r", np.zeros(f + 1))[f])
    if p > 0:
        E, H = arm_joints(th + PROWL_SWING * (2.0 * k - 1.0), out + math.degrees(p / max(float(np.hypot(H[0], H[1])), 0.2)),
                          el - 8.0 * k, turn, lu, lf)
    E0, H0, E, H = E0 * m, H0 * m, E * m, H * m
    # the forearm's turn from Prowl's (its line, then its hinge's way: the elbow's side of the arm)
    q = qbetween(H0 - E0, H - E)
    n0, n = np.cross(E0, H0 - E0), np.cross(E, H - E)
    a = math.degrees(math.atan2(np.dot(np.cross(qrot(q, n0), n), _n(H - E)), np.dot(qrot(q, n0), n)))
    q = qmul(qaxis(_n(H - E), a), q)
    lag = qaxis([1.0, 0, 0], -PROWL_LAG * float(_CTX["r"][0][f]))
    b, kn = (qrot(q, np.array(v, float)) for v in prowl.TRAIL_GRIP)
    return {"arc": arc_of(H), "pole": _n(E), "pole_at": "shoulder", "frame": "chest",
            "blade": tuple(qrot(lag, b)), "knuckles": tuple(qrot(lag, kn))}


def sword(k, f):
    """The sword low at her right, as her armed idle holds it (idle.warden: the point 34 deg below level ahead, the
    thumb forward, the elbow swung out over the hilt), the fist swinging a little with the stride."""
    if "r" in _PROWL and _CTX.get("trail"):
        return _trail_hand(k, f)
    if "r" in _PROWL:
        return _prowl_hand("r", k, f, PROWL_SWING, PROWL_LAG)
    return {"arc": arc_of(_at((-0.12, -0.45, 0.04), 0.08, k, 0.01)), "pole": (-0.744, 0.09, -0.662), "frame": "chest",
            "blade": _n((-0.30, -0.52, 0.80)), "knuckles": _n((0.123, -0.828, -0.548)), "twist": 0.5}


def shield(k, f):
    """The shield at rest at her left side, off her body (idle.warden's hand_l), braced, riding the step a little."""
    if "l" in _PROWL:
        return _prowl_hand("l", k, f, 3.0, 0.0)
    return {"arc": arc_of(_at((0.0817, -0.3796, 0.1299), 0.02, k)), "pole": (0.3281, -0.4168, -0.8477), "frame": "chest",
            "thumb": (-0.1498, 0.7455, 0.6495), "twist": 1.0}


def axe(side):
    """An axe in the hand at her side, the arm near hanging and swinging a little, the head ahead and down, out from
    her leg."""
    sg = 1.0 if side == "l" else -1.0

    # (Round 2, the judge: the left read near level at her belt, its head before her left knee at the right heel
    # strike; the left hand let 3 cm further out and its haft dropped toward 45 deg forward and down.)
    out, blade = (0.10, (sg * 0.25, -0.45, 0.86)) if side == "r" else (0.13, (sg * 0.32, -0.62, 0.72))

    def f(k, fr):
        return {"arc": arc_of(_at((sg * out, -0.46, 0.05), 0.08, k, 0.01)), "pole": (sg * 0.5, -0.2, -1.0),
                "frame": "chest", "blade": _n(blade), "twist": 0.5}
    return f


def staff(k, f):
    """The staff upright in her right fist at her side, tipped forward (run.staff_hold), the arm barely swinging."""
    # (Round 2: the staff's head trails the stride, its pitch swinging STAFF_PITCH deg, LAG frames behind the arm.)
    d = STAFF_PITCH * (2.0 * _CTX["r"][1][f] - 1.0)
    return {"arc": arc_of(_at((-0.10, -0.40, 0.10), 0.03, k)), "pole": (-0.3, -0.1, -1.0),
            "blade": _pitch((0.05, 0.94, 0.33), d), "knuckles": _pitch((0.0, -0.33, 0.94), d), "frame": "chest",
            "twist": 0.5}


STAFF_PITCH = 2.0  # deg either way: 4 in all


def wand(k, f):
    """The wand in her right fist, the arm near hanging and swinging a little, the wand pointing ahead and down."""
    return {"arc": arc_of(_at((-0.10, -0.46, 0.06), 0.10, k, 0.01)), "pole": (-0.5, -0.2, -1.0), "frame": "chest",
            "blade": _n((-0.15, -0.35, 0.92)), "twist": 0.5}


def crossbow(k, f):
    """The crossbow in her right fist on its pistol grip as her run carries it (run.crossbow_low: the stock level and
    ahead, the forearm level from an elbow by her ribs, the fist at her waist 10 cm out), steadier. (Both hands on it as
    her idle holds it, the left on the fore-stock, put her upper arms 30-49 mm into her breasts and sides at the walk's
    chest: her idle stands wider, the crossbow further ahead.)"""
    # Round 2 (the judge: forearm level at the waist and the bow 20 deg up read as presenting a pistol): the front
    # end down CROSSBOW_DOWN deg at the wrist, the elbow opened, the fist lower, at her hip.
    return {"arc": arc_of(_at(CROSSBOW_HAND, 0.03, k)), "pole": (-0.2, -0.3, -1.0),
            "knuckles": _pitch((0.0, 0.64, 0.77), -CROSSBOW_DOWN), "blade": _pitch((0.0, 0.77, -0.64), -CROSSBOW_DOWN),
            "frame": "chest", "twist": 0.5}


CROSSBOW_HAND = (-0.12, -0.30, 0.24)
CROSSBOW_DOWN = 33.0


def dagger(side):
    """A dagger in each fist, the arms near hanging and swinging with the stride, the blade rising ahead and out."""
    sg = 1.0 if side == "l" else -1.0

    # Round 2 (the judge: elbows bent and out, the points level ahead, the camp stance's "arms held out, fists clenched,
    # stiff"): the arm near straight (25-30 deg of bend), the elbow in by her side, swung as the town walk's free arm;
    # the point tipped forward and down; the wrist trailing each swing DAGGER_LAG deg; the forearm's turn out easing
    # toward neutral on the backswing.
    def f(k, fr):
        v = _CTX[side][0][fr]
        th = DAGGER_THUMB + DAGGER_LAG * v  # (forward: the knuckles trail, the point tips up)
        h = _at((sg * 0.075, -0.505, 0.05), 0.17, k, 0.012)
        h *= DAGGER_REACH / np.linalg.norm(h)  # (one reach: the elbow's bend held at 25-30 through the swing)
        return {"arc": arc_of(h), "pole": (sg * 0.15, -0.2, -1.0),
                "frame": "chest", "blade": _n((sg * (0.05 + 0.15 * k), math.tan(math.radians(th)), 1.0)), "twist": 0.5}
    return f


DAGGER_THUMB = -31.0  # the point's way, deg above level ahead
DAGGER_LAG = 9.0
DAGGER_REACH = 0.500  # m, shoulder to wrist


# name: (calling, {side: carriage}, {side: fingers}, weapon (keyed.grip_of))
WALKS = {
    "walk_warden": ("warden", {"r": sword, "l": shield},
                    {"r": "grip", "l": {"curl": 0.95, "cascade": 0.05, "thumb": 1.6, "oppose": 0.9}}, "sword+shield"),
    "walk_reaver": ("reaver", {"r": axe("r")}, {"r": "grip"}, "axe"),
    "walk_reaver_axes": ("reaver", {"r": axe("r"), "l": axe("l")}, {"r": "grip", "l": "grip"}, "axes"),
    "walk_arcanist": ("arcanist", {"r": staff}, {"r": "grip"}, "staff"),
    "walk_arcanist_wand": ("arcanist", {"r": wand}, {"r": "grip"}, "wand"),
    "walk_stalker": ("stalker", {"r": crossbow}, {"r": "grip"}, "crossbow"),
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
PUSH = {"walk_stalker": {"r": (-0.6, 0.0, 0.8)}}
LINKED = set()
OUTFIT = {"warden": "warden", "reaver": "reaver", "arcanist": "arcanist", "stalker": "ranger"}
_LAST = {}  # per clip: the hands' push (m, per side per frame) and the arms' clearance after it (read by the checks)


def _tilt(name):
    """(solver 6a) The grip tilt the walk holds: the warden's Prowl walk the idle's (prowl.GRIP_TILT), else none."""
    if name == "walk_warden" and "r" in _PROWL:
        from clips import prowl
        return prowl.GRIP_TILT
    return 0.0


def _solve(rig, name, town, k, push):
    from keyed import solve_frames
    calling, arms, fingers, weapon = WALKS[name]
    rot, pos = town.rot.copy(), town.pos.copy()
    n = len(rot) - 1  # the closing frame is the first again
    way = PUSH.get(name, OUT)
    # (solver 4a) the trailing sword arm takes its push as more out at the shoulder (walk_armed._trail_hand)
    joints = name == "walk_warden" and "r" in _PROWL and bool(_CTX.get("trail"))
    _CTX["push_r"] = push["r"] if joints else np.zeros(n)
    specs = []
    for f in range(n):
        sp = {}
        for s, carry in arms.items():
            h = dict(carry(float(k[s][f]), f))
            if push[s][f] > 0 and not (joints and s == "r"):
                from gait import arc_of as _arc
                az, el, r = h["arc"]
                a, e = math.radians(az), math.radians(el)
                v = r * np.array([math.sin(a) * math.cos(e), math.sin(e), math.cos(a) * math.cos(e)])
                h["arc"] = _arc(v + push[s][f] * np.array(way[s], float))
            sp[f"hand_{s}"] = h
            sp[f"fingers_{s}"] = fingers[s]
        specs.append(sp)
    bases = [(rot[f], pos[f]) for f in range(n)]
    srot, _ = solve_frames(rig, specs, bases, loop=True, weapon=weapon, tilt=_tilt(name))
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
    _PROWL.clear()
    if name == "walk_warden":
        from clips.sword import prowl_end
        end = prowl_end(rig)
        if end is not None:
            from clips import prowl
            # (solver 6a) the walk holds at the idle's grip tilt (prowl.GRIP_TILT), so its keys are the idle's own
            end = prowl.end_keys(rig, fingers_l=end["fingers_l"])
            _PROWL.update({s: end[f"hand_{s}"] for s in "lr"})
            ap = rig.sk.rest_globals()[1][0]
            I = rig.I
            _CTX["trail"] = prowl.TRAIL
            _CTX["arm"] = (float(np.linalg.norm(ap[I["lowerarm_r"]] - ap[I["upperarm_r"]])),
                           float(np.linalg.norm(ap[I["hand_r"]] - ap[I["lowerarm_r"]])))
            fingers = dict(fingers, l=end["fingers_l"])
            WALKS[name] = (calling, arms, fingers, weapon)
    if calling not in _TOWN:
        _TOWN[calling] = wt.make_walk(rig, calling)
    town = _TOWN[calling]
    n = len(town.rot) - 1
    k = _swing_k(rig, town)
    for s in "lr":
        vel = np.gradient(np.concatenate([k[s][-3:-1], k[s][:n], k[s][:2]]))[2:-2]
        _CTX[s] = (vel / max(np.abs(vel).max(), 1e-6), wt._shift(k[s][:n], LAG))
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
    if _tilt(name):
        meta["grip_tilt"] = _tilt(name)
    return Clip(name, 30, rot, pos, loop=True, meta=meta)


def clips(rig, want):
    return [make(rig, name) for name in WALKS if not want or any(x in name for x in want)]
