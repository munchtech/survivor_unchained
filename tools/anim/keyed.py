"""Clips keyed by hand, in code: key poses as an animator thinks of them,
timed, and solved onto her skeleton.

A pose is a dict of controls, all in her character space (she stands at the
origin facing +Z, her left at +X, up +Y; metres and degrees):

    hips      {"pos": (x, y, z) from where they rest, "rot": (yaw, pitch, roll)}
    spine     (yaw, pitch, roll) for the whole back, shared out over spine_01..03
    neck      (yaw, pitch, roll) and head (yaw, pitch, roll), after the back
    clav_l/r  (raise, forward): the shoulder shrugged and drawn forward
    hand_l/r  {"pos": (x, y, z) wrist in character space, or
               "arc": (azimuth, elevation, reach) about the shoulder, in the
                      chest's frame (azimuth + toward her left, 0 straight
                      ahead; elevation + up; reach in metres),
               "blade": (x, y, z) the way a held shaft leaves the fist (the
                      thumb side: the hand's +Z), "knuckles": (x, y, z) the
                      way the fingers point when flat (the hand's +Y),
               "pole": (x, y, z) the way the elbow points,
               "frame": "char" | "chest" (which space blade/knuckles/pos use)}
    foot_l/r  {"pos": (x, y, z) the ankle (y 0 = flat on the ground),
               "rot": (yaw, pitch, roll), "pole": (x, y, z) the knee's way,
               "toe": degrees the toes bend up}
    fingers_l/r  a preset ("relaxed", "grip", "fist", "open", "claw",
               "point", "spread") or {"curl": 0..1, "thumb": 0..1, "spread": deg}

Anything left out stays as it was at rest: an empty pose is her rest, which
is her A-pose. `Stance` presets give a neutral standing pose to build on.

Keys are (time in frames, pose, ease). Each control is interpolated on its
own curve (cubic Hermite through the keys; "ease" flattens the tangent at a
key, "linear" keeps it straight, "hold" steps), so arcs come from the arc
control rather than from straight lines between wrists.
"""
from __future__ import annotations

import copy
import math

import numpy as np

from rig import (Clip, Skeleton, qaxis, qbetween, qeuler, qfrom_basis, qinv, qmul, qnorm, qrot, two_bone_ik,
                 qslerp)

SPINE = (("spine_01", 0.22), ("spine_02", 0.33), ("spine_03", 0.45))
FINGERS = ("index", "middle", "ring", "pinky")


class Rig:
    """Her skeleton, ready to be posed by controls."""

    def __init__(self, sk: Skeleton):
        self.sk = sk
        grot, gpos = sk.rest_globals()
        self.grest = grot[0]
        self.prest = gpos[0]
        self.I = sk.index
        # The hand's own axes at rest, in character space: +Y along the
        # fingers, +Z out of the thumb side (People/Arms mount weapons so).
        self.finger_axis = {}
        for side in "lr":
            h = self.I[f"hand_{side}"]
            # Each finger joint bends about the axis across the hand.
            for f in FINGERS + ("thumb",):
                for k in (1, 2, 3):
                    j = self.I[f"{f}_0{k}_{side}"]
                    self.finger_axis[j] = self._bend_axis(j, side)

    def _bend_axis(self, j, side):
        """The axis (in the bone's own frame) a finger joint curls about,
        signed so a positive turn closes it toward the palm."""
        sk = self.sk
        h = self.I[f"hand_{side}"]
        g = self.grest
        fing = qrot(g[h], [0, 1, 0])
        thumb = qrot(g[h], [0, 0, 1])
        palm = np.cross(fing, thumb) * (1 if side == "l" else -1)
        name = sk.names[j]
        d = qrot(g[j], [0, 1, 0])  # the bone's direction
        if name.startswith("thumb"):
            # The thumb folds across the palm toward the little finger.
            across = -qrot(g[h], [0, 0, 1])
            axis_w = np.cross(d, palm * 0.6 + across * 0.8)
        else:
            axis_w = np.cross(d, palm)
        axis_w = axis_w / np.linalg.norm(axis_w)
        return qrot(qinv(g[j]), axis_w)

    # ------------------------------------------------------------- solve --
    def solve(self, pose: dict, base=None):
        """Local rotations [J, 4] and positions [J, 3] for one pose. With a
        base ((local, pos) of a frame of another clip, a capture say), the
        controls are laid over it: turns add to its turns, and hands and feet
        given are solved afresh while the rest of it stands."""
        sk, I = self.sk, self.I
        J = len(sk)
        pel = I["pelvis"]
        if base is None:
            delta = np.tile(np.array([0, 0, 0, 1.0]), (J, 1))  # character-space turn from rest, per bone
            hp = np.zeros(3)
        else:
            bg, bp = sk.fk(base[0][None], base[1][None])
            delta = qmul(bg[0], qinv(self.grest))
            hp = bp[0, pel] - self.prest[pel]
        gpos = self.prest.copy()
        grot = self.grest.copy()

        def turn(j, inc):
            """Bone j (and all under it) turned by inc, in j's own turned frame."""
            w = qmul(qmul(delta[j], inc), qinv(delta[j]))
            for k in [j] + self._below(j):
                delta[k] = qmul(w, delta[k])

        # Hips.
        hips = pose.get("hips", {})
        turn(pel, qeuler(*hips.get("rot", (0, 0, 0))))
        hp = hp + np.array(hips.get("pos", (0, 0, 0)), float)
        # Spine, neck, head: each turned on top of the one below.
        sp = pose.get("spine", (0, 0, 0))
        for name, w in SPINE:
            turn(I[name], qeuler(sp[0] * w, sp[1] * w, sp[2] * w))
        turn(I["neck_01"], qeuler(*pose.get("neck", (0, 0, 0))))
        turn(I["Head"], qeuler(*pose.get("head", (0, 0, 0))))
        for side in "lr":
            c = I[f"clavicle_{side}"]
            raise_, fwd = pose.get(f"clav_{side}", (0, 0))
            s = 1 if side == "l" else -1
            # Raise: the shoulder's tip up, about the forward axis; forward:
            # about up. (Her left clavicle runs toward +X, her right toward -X.)
            turn(c, qmul(qaxis([0, 0, 1], raise_ * s), qaxis([0, 1, 0], -fwd * s)))
        # Globals from the deltas: rotation turned, positions by FK.
        def refresh():
            for j in range(J):
                grot[j] = qmul(delta[j], self.grest[j])
            for j in range(J):
                p = sk.parent[j]
                if p < 0:
                    continue
                if j == pel:
                    gpos[j] = self.prest[j] + hp
                else:
                    lp = qrot(qinv(self.grest[p]), self.prest[j] - self.prest[p])  # rest offset in parent frame
                    gpos[j] = gpos[p] + qrot(grot[p], lp)
        refresh()
        chest = delta[I["spine_03"]]

        # Arms.
        for side in "lr":
            spec = pose.get(f"hand_{side}")
            if not spec:
                continue
            ua, la, ha = I[f"upperarm_{side}"], I[f"lowerarm_{side}"], I[f"hand_{side}"]
            frame = chest if spec.get("frame", "char") == "chest" else np.array([0, 0, 0, 1.0])
            sh = gpos[ua]
            if "arc" in spec:
                az, el, r = spec["arc"]
                d = np.array([math.sin(math.radians(az)) * math.cos(math.radians(el)), math.sin(math.radians(el)),
                              math.cos(math.radians(az)) * math.cos(math.radians(el))])
                target = sh + qrot(chest, d) * r
            elif "pos" in spec:
                target = qrot(frame, np.array(spec["pos"], float)) if spec.get("frame") == "chest" else np.array(spec["pos"], float)
                if spec.get("frame") == "chest":
                    target = target + gpos[I["spine_03"]]
            else:
                target = gpos[ha]
            s = 1 if side == "l" else -1
            pole = np.array(spec.get("pole", (s * 0.6, -0.3, -1.0)), float)
            pole = qrot(frame, pole) if spec.get("frame") == "chest" else pole
            eb, wr = two_bone_ik(gpos[ua], gpos[la], gpos[ha], target, gpos[la] + pole)
            # Upper arm: turned from where it points now onto the elbow.
            r1 = qbetween(gpos[la] - gpos[ua], eb - gpos[ua])
            delta[ua] = qmul(r1, delta[ua])
            delta[la] = qmul(r1, delta[la])
            refresh()
            r2 = qbetween(gpos[ha] - gpos[la], wr - gpos[la])
            delta[la] = qmul(r2, delta[la])
            refresh()
            # The hand: aimed by blade and knuckles if given, else it rides
            # the forearm.
            if "blade" in spec or "knuckles" in spec:
                cur = qmul(delta[la], self.grest[ha])
                z = qrot(cur, [0, 0, 1])
                y = qrot(cur, [0, 1, 0])
                if "blade" in spec:
                    z = np.array(spec["blade"], float)
                    z = qrot(frame, z) if spec.get("frame") == "chest" else z
                if "knuckles" in spec:
                    y = np.array(spec["knuckles"], float)
                    y = qrot(frame, y) if spec.get("frame") == "chest" else y
                z = z / np.linalg.norm(z)
                if "blade" in spec:
                    y = y - z * np.dot(y, z)
                    y = y / np.linalg.norm(y)
                else:
                    y = y / np.linalg.norm(y)
                    z = z - y * np.dot(z, y)
                    z = z / np.linalg.norm(z)
                x = np.cross(y, z)
                want = qfrom_basis(x, y, z)
                hd = qmul(want, qinv(self.grest[ha]))
                # Share the hand's twist about the forearm with the forearm,
                # so the wrist does not wring like a sweet wrapper.
                share = spec.get("twist", 0.45)
                if share > 0:
                    fa = gpos[ha] - gpos[la]
                    fa = fa / np.linalg.norm(fa)
                    rel = qmul(hd, qinv(delta[la]))  # the hand's turn on top of the forearm's
                    tw = _twist(rel, fa)
                    part = qslerp(np.array([0, 0, 0, 1.0]), tw, share)
                    delta[la] = qmul(part, delta[la])
                delta[ha] = hd
                for j in self._below(ha):
                    delta[j] = hd
                refresh()
            else:
                for j in [ha] + self._below(ha):
                    delta[j] = delta[la]
                refresh()

        # Legs.
        for side in "lr":
            spec = pose.get(f"foot_{side}", {})
            if base is not None and not spec:
                continue
            th, ca, fo = I[f"thigh_{side}"], I[f"calf_{side}"], I[f"foot_{side}"]
            rest_ankle = self.prest[fo]
            p = np.array(spec.get("pos", (rest_ankle[0], 0, rest_ankle[2])), float)
            target = np.array([p[0], rest_ankle[1] + p[1], p[2]])
            s = 1 if side == "l" else -1
            pole = np.array(spec.get("pole", (s * 0.15, 0, 1.0)), float)
            kb, an = two_bone_ik(gpos[th], gpos[ca], gpos[fo], target, gpos[ca] + pole)
            r1 = qbetween(gpos[ca] - gpos[th], kb - gpos[th])
            delta[th] = qmul(r1, delta[th])
            delta[ca] = qmul(r1, delta[ca])
            refresh()
            r2 = qbetween(gpos[fo] - gpos[ca], an - gpos[ca])
            delta[ca] = qmul(r2, delta[ca])
            # The foot keeps its own turn in the world, whatever the leg does.
            fq = qeuler(*spec.get("rot", (0, 0, 0)))
            delta[fo] = fq
            toe = spec.get("toe", 0)
            b = I[f"ball_{side}"]
            # Toes bend about the foot's across axis.
            delta[b] = qmul(qmul(fq, qaxis([1, 0, 0], -toe)), np.array([0, 0, 0, 1.0]))
            for j in self._below(b):
                delta[j] = delta[b]
            refresh()

        # Hands' fingers.
        local = np.empty((J, 4))
        for j in range(J):
            p = sk.parent[j]
            local[j] = grot[j] if p < 0 else qmul(qinv(grot[p]), grot[j])
        for side in "lr":
            spec = pose.get(f"fingers_{side}", "relaxed")
            curl = finger_curl(spec)
            for name, angles in curl.items():
                for k, a in enumerate(angles):
                    j = I[f"{name}_0{k + 1}_{side}"]
                    if a:
                        local[j] = qmul(local[j], qaxis(self.finger_axis[j], a))
            sp_ = spec.get("spread", 0) if isinstance(spec, dict) else FINGER_PRESETS.get(spec, {}).get("spread", 0)
            if sp_:
                # Fanned about the palm's normal (across the bend axis and
                # the finger's own line).
                for f, w in (("index", 1), ("middle", 0.3), ("ring", -0.4), ("pinky", -1)):
                    j = I[f"{f}_01_{side}"]
                    local[j] = qmul(local[j], qaxis(np.cross([0, 1, 0], self.finger_axis[j]), sp_ * w))
        pos = self.sk.rest_pos.copy()
        pos[pel] = qrot(qinv(self.grest[sk.parent[pel]]), self.prest[pel] + hp - self.prest[sk.parent[pel]])
        return local, pos

    def _below(self, j):
        if not hasattr(self, "_below_cache"):
            self._below_cache = {}
        if j not in self._below_cache:
            out = []
            stack = list(self.sk.children(j))
            while stack:
                k = stack.pop()
                out.append(k)
                stack.extend(self.sk.children(k))
            self._below_cache[j] = out
        return self._below_cache[j]

    def globals(self, local, pos):
        return self.sk.fk(local[None], pos[None])


def _twist(qr, axis):
    """The part of rotation qr that turns about axis (swing-twist split)."""
    v = qr[:3]
    p = axis * np.dot(v, axis)
    t = np.array([p[0], p[1], p[2], qr[3]])
    n = np.linalg.norm(t)
    return t / n if n > 1e-9 else np.array([0, 0, 0, 1.0])


# ------------------------------------------------------------------ fingers --
# Degrees each finger's three joints close by (index, middle, ring, pinky,
# thumb), and how far they fan.
FINGER_PRESETS = {
    "rest": {"curl": 0, "thumb": 0},
    "relaxed": {"curl": 0.28, "thumb": 0.15, "cascade": 0.25},
    "open": {"curl": 0.05, "thumb": 0.0, "spread": 4},
    "spread": {"curl": 0.0, "thumb": -0.1, "spread": 10},
    "claw": {"curl": 0.45, "thumb": 0.2, "spread": 9, "tip": 0.6},
    "grip": {"curl": 0.9, "thumb": 0.65, "cascade": 0.08},
    "fist": {"curl": 1.0, "thumb": 0.8, "cascade": 0.05},
    "point": {"curl": 0.95, "thumb": 0.6, "index": 0.05},
}


def finger_curl(spec):
    p = dict(FINGER_PRESETS.get(spec, {})) if isinstance(spec, str) else dict(spec)
    c = p.get("curl", 0.3)
    th = p.get("thumb", 0.2)
    cascade = p.get("cascade", 0.15)
    tip = p.get("tip", 1.0)
    out = {}
    for i, f in enumerate(FINGERS):
        ci = c * (1 + cascade * i)
        if f == "index" and "index" in p:
            ci = p["index"]
        out[f] = [ci * 80, ci * 95 * (0.8 + 0.2 * tip), ci * 65 * tip]
    out["thumb"] = [th * 25, th * 35, th * 40]
    return out


# ---------------------------------------------------------------- stances --
def stance(width=0.17, back=0.0, toe_out=8, **over):
    """Her standing: feet a little apart and turned out, the rest of her as
    the keys say."""
    pose = {
        "foot_l": {"pos": (width, 0, -back), "rot": (toe_out, 0, 0)},
        "foot_r": {"pos": (-width, 0, back), "rot": (-toe_out, 0, 0)},
        "hand_l": {"arc": (80, -72, 0.44), "pole": (0.3, 0, -1)},
        "hand_r": {"arc": (-80, -72, 0.44), "pole": (-0.3, 0, -1)},
        "fingers_l": "relaxed", "fingers_r": "relaxed",
    }
    pose.update(over)
    return pose


def merge(base: dict, **over) -> dict:
    """A pose with some controls replaced (dicts merged one level deep)."""
    out = copy.deepcopy(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = {**out[k], **v}
        else:
            out[k] = v
    return out


# ------------------------------------------------------------------ timing --
def _flatten(pose, prefix=""):
    """A pose as named scalars and named non-scalars (presets)."""
    out = {}
    for k, v in pose.items():
        name = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(_flatten(v, name + "."))
        elif isinstance(v, (tuple, list)) and all(isinstance(x, (int, float)) for x in v):
            for i, x in enumerate(v):
                out[f"{name}#{i}"] = float(x)
        elif isinstance(v, (int, float)):
            out[name] = float(v)
        else:
            out[name] = v
    return out


def _unflatten(flat):
    pose = {}
    for k, v in flat.items():
        path, _, idx = k.partition("#")
        parts = path.split(".")
        d = pose
        for p in parts[:-1]:
            d = d.setdefault(p, {})
        leaf = parts[-1]
        if idx:
            arr = d.setdefault(leaf, [])
            i = int(idx)
            while len(arr) <= i:
                arr.append(0.0)
            arr[i] = v
        else:
            d[leaf] = v
    return pose


def _hermite(ts, vs, eases, t):
    """Cubic through (ts, vs); a key's ease flattens its tangent ("ease"),
    keeps the line ("linear"), steps ("hold"), or "fast" (sharper into it)."""
    n = len(ts)
    if t <= ts[0]:
        return vs[0]
    if t >= ts[-1]:
        return vs[-1]
    i = max(k for k in range(n - 1) if ts[k] <= t)
    t0, t1 = ts[i], ts[i + 1]
    v0, v1 = vs[i], vs[i + 1]
    if eases[i] == "hold":
        return v0
    u = (t - t0) / (t1 - t0)

    def tangent(k):
        e = eases[k]
        if e == "ease" or k == 0 or k == n - 1:
            return 0.0
        m = ((vs[k + 1] - vs[k]) / (ts[k + 1] - ts[k]) + (vs[k] - vs[k - 1]) / (ts[k] - ts[k - 1])) / 2
        # No overshoot between keys where the curve turns back.
        if (vs[k + 1] - vs[k]) * (vs[k] - vs[k - 1]) <= 0:
            return 0.0
        return m

    if eases[i] == "linear" and eases[i + 1] in ("linear", "hold"):
        return v0 + (v1 - v0) * u
    m0 = tangent(i) * (t1 - t0)
    m1 = tangent(i + 1) * (t1 - t0)
    if eases[i] == "fast":
        # Leaves the key fast and arrives slowing (a strike's whip).
        m0 = (v1 - v0) * 2.2
    if eases[i + 1] == "fast":
        m1 = (v1 - v0) * 0.2
    h00 = 2 * u ** 3 - 3 * u ** 2 + 1
    h10 = u ** 3 - 2 * u ** 2 + u
    h01 = -2 * u ** 3 + 3 * u ** 2
    h11 = u ** 3 - u ** 2
    return h00 * v0 + h10 * m0 + h01 * v1 + h11 * m1


def _zero_default(n):
    head = n.split("#")[0]
    return head.startswith(("hips.", "spine", "neck", "head", "clav_")) or head.endswith((".rot", ".toe"))


def build(name, rig: Rig, keys, fps=30, loop=False, meta=None, post=None) -> Clip:
    """A clip from keys [(frame, pose, ease), ...]. For a loop, the last key
    should be the first again."""
    keys = sorted(keys, key=lambda k: k[0])
    flats = [_flatten(k[1]) for k in keys]
    names = set()
    for f in flats:
        names |= set(f)
    frames = int(round(keys[-1][0])) + 1
    rot = np.empty((frames, len(rig.sk), 4))
    pos = np.empty((frames, len(rig.sk), 3))
    # A turn or offset a key leaves out is none at that key (so a key without
    # "spine" stands straight); a hand or foot a key leaves out is wherever
    # the keys either side put it.
    for f in flats:
        for n in names:
            if n not in f and _zero_default(n):
                f[n] = 0.0
    for fr in range(frames):
        flat = {}
        for n in names:
            have = [(k[0], f[n], k[2] if len(k) > 2 else "auto") for k, f in zip(keys, flats) if n in f]
            if not have:
                continue
            if isinstance(have[0][1], float):
                flat[n] = _hermite([h[0] for h in have], [h[1] for h in have], [h[2] for h in have], fr)
            else:
                # Presets switch at the key nearest in time.
                flat[n] = min(have, key=lambda h: abs(h[0] - fr))[1]
        pose = _unflatten(flat)
        if post:
            pose = post(fr, pose)
        rot[fr], pos[fr] = rig.solve(pose)
    m = {"source": "keyed (tools/anim)", "licence": "own work"}
    m.update(meta or {})
    return Clip(name, fps, rot, pos, loop=loop, meta=m)
