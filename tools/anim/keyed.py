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
               "thumb": (x, y, z) instead of blade and knuckles: the wrist
                      left straight, the forearm rolled so the thumb side
                      faces as near this way as it can (a carried weapon),
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

import bisect
import copy
import math

import numpy as np

from rig import (Clip, Skeleton, qaxis, qbetween, qeuler, qfrom_basis, qinv, qmul, qnorm, qrot, two_bone_ik,
                 qslerp)

SPINE = (("spine_01", 0.22), ("spine_02", 0.33), ("spine_03", 0.45))
FINGERS = ("index", "middle", "ring", "pinky")


class Rig:
    """Her skeleton, ready to be posed by controls. `body`: whose ("her",
    or "him": the hero, who stands with his feet further apart, FEET_OUT,
    and runs with his own carriage, gait.MANLY)."""

    FEET_OUT = {"her": 0.0, "him": 0.045}

    def __init__(self, sk: Skeleton, body="her", grips=True):
        self.sk = sk
        self.body = body
        # Whether weapons sit in a diagonal grip (GRIP): her and the hero;
        # not the folk, who also play the library's clips, held square.
        self.grips = grips
        self.feet_out = self.FEET_OUT.get(body, 0.0)
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
        # The elbows' and knees' hinges at rest, in her space: an elbow bends
        # the forearm forward (about the axis across the upper arm and her
        # front), a knee the shin back. The IK turns the upper arm and the
        # thigh about their own length until these hinges lie across the
        # bend, so a joint only ever bends the way it can.
        fwd = np.array([0.0, 0.0, 1.0])
        self.hinge = {}
        for side in "lr":
            for kind, top, mid, way in (("arm", "upperarm", "lowerarm", fwd), ("leg", "thigh", "calf", -fwd)):
                u = self.prest[self.I[f"{mid}_{side}"]] - self.prest[self.I[f"{top}_{side}"]]
                u = u / np.linalg.norm(u)
                h = np.cross(u, way)
                self.hinge[(kind, side)] = h / np.linalg.norm(h)
        # The swivel each arm last needed (degrees about shoulder-to-wrist from
        # the keyed elbow), so a strained wrist is eased the same way frame to frame.
        self.swivel = {}
        # How far a held weapon's shaft leans in each fist (degrees; GRIP),
        # for the clip being solved.
        self.grip = {}

    # Anatomy, degrees: how far the forearm turns about its length from the
    # hand's rest (pronation and supination, about neutral either way), and how
    # far the wrist bends: a long way toward the palm and back (flexion,
    # extension), little to either side (toward the thumb, radial; toward the
    # little finger, ulnar). A hand keyed past these is brought back within
    # them, first by swinging the elbow round, then by letting the hand fall
    # short. (A wrist bent 60 degrees sideways reads as broken: the old single
    # limit of 80 let it, and runs flapped the sword hand from one side to the
    # other every stride.)
    TWIST_LIMIT = 95.0
    FLEX, EXT, RADIAL, ULNAR = 75.0, 65.0, 22.0, 38.0

    def _bend(self, kind, side, top, mid, end, d_top, d_mid, S, E, W, pole):
        """The upper and lower bones' turns (character-space deltas) that put
        the joint at E and the end at W, the upper bone turned about its length
        so the joint's hinge lies across the bend (no sideways elbow or knee)."""
        rest_u = self.prest[mid] - self.prest[top]
        rest_u = rest_u / np.linalg.norm(rest_u)
        rest_f = self.prest[end] - self.prest[mid]
        rest_f = rest_f / np.linalg.norm(rest_f)
        r1 = qbetween(qrot(d_top, rest_u), E - S)
        d_top, d_mid = qmul(r1, d_top), qmul(r1, d_mid)
        u = (E - S) / np.linalg.norm(E - S)
        f = W - E
        # The bend's own axis; as the limb straightens it fades into the
        # pole's, so a straight limb still knows which way it would bend.
        n = np.cross(E - S, f) / (np.linalg.norm(E - S) * np.linalg.norm(f) + 1e-9)
        np_ = np.cross(pole, W - S)
        if np.linalg.norm(np_) > 1e-9:
            n = n + 0.05 * np_ / np.linalg.norm(np_)
        # A limb all but straight has no bend to read its hinge from: keep the
        # way it was bending last frame, so the arm does not roll over as it
        # passes straight (a flung arm, a hanging one).
        sinb = float(np.linalg.norm(np.cross(E - S, f)) / (np.linalg.norm(E - S) * np.linalg.norm(f) + 1e-9))
        last = getattr(self, "bend_last", {}).get((kind, side))
        forced = (getattr(self, "bend_force", None) or {}).get((kind, side))
        if forced is not None and sinb < 0.35:
            # Through a straight stretch, the hinge turned evenly from how it
            # bent going in to how it bends coming out (solve_frames).
            n = np.asarray(forced, float)
        elif last is not None and sinb < 0.35:
            k = sinb / 0.35
            nn_ = n / max(np.linalg.norm(n), 1e-9)
            if float(np.dot(nn_, last)) < 0 and k < 0.5:
                nn_ = -nn_
            n = nn_ * k + last * (1 - k)
        if not hasattr(self, "bend_last"):
            self.bend_last = {}
        if np.linalg.norm(n) > 1e-9:
            self.bend_last[(kind, side)] = n / np.linalg.norm(n)
        h = qrot(d_top, self.hinge[(kind, side)])
        hp, nn = h - u * np.dot(h, u), n - u * np.dot(n, u)
        if np.linalg.norm(hp) > 1e-6 and np.linalg.norm(nn) > 1e-6:
            ang = math.atan2(np.dot(np.cross(hp, nn), u), np.dot(hp, nn))
            w = qaxis(u, math.degrees(ang))
            d_top, d_mid = qmul(w, d_top), qmul(w, d_mid)
        r2 = qbetween(qrot(d_mid, rest_f), f)
        return d_top, qmul(r2, d_mid)

    def _strain(self, d_la, want, ha, fa, side):
        """How a hand keyed to `want` sits on its forearm: the turn about the
        forearm (degrees, signed) and the wrist's bend (degrees), the two as
        rotations (twist, swing), and the bend as the wrist's own flexion and
        deviation (Rig._wrist_split)."""
        cur = qmul(d_la, self.grest[ha])
        rel = qmul(want, qinv(cur))
        tw = _twist(rel, fa)
        if tw[3] < 0:
            tw = -tw
        tw_deg = math.degrees(2 * math.atan2(np.dot(tw[:3], fa), tw[3]))
        sw = qnorm(qmul(rel, qinv(tw)))
        if sw[3] < 0:
            sw = -sw
        sw_deg = math.degrees(2 * math.acos(min(1.0, sw[3])))
        axis = sw[:3] / max(np.linalg.norm(sw[:3]), 1e-9)
        phi, dev = self._wrist_split(axis, sw_deg, qmul(tw, cur), side)
        return tw_deg, sw_deg, tw, sw, phi, dev

    def _wrist_split(self, axis, deg, hand_t, side):
        """A wrist bend (a turn of `deg` about `axis`, in her space, laid on
        the hand `hand_t`) as flexion (+ toward the palm) and deviation (+
        toward the thumb), degrees, about the hand's own axes: +Z the thumb
        side, +X across the back (her right hand) or the palm (her left)."""
        if deg < 1e-6:
            return 0.0, 0.0
        z, x = qrot(hand_t, [0, 0, 1.0]), qrot(hand_t, [1.0, 0, 0])
        s = 1.0 if side == "r" else -1.0
        return deg * float(np.dot(axis, z)) * s, deg * float(np.dot(axis, x))

    def _wrist_join(self, phi, dev, hand_t, side):
        """The bend _wrist_split read, as a turn in her space."""
        z, x = qrot(hand_t, [0, 0, 1.0]), qrot(hand_t, [1.0, 0, 0])
        s = 1.0 if side == "r" else -1.0
        v = phi * s * z + dev * x
        a = float(np.linalg.norm(v))
        return qaxis(v / a, a) if a > 1e-6 else np.array([0, 0, 0, 1.0])

    def _wrist_over(self, phi, dev):
        """How far past its range a wrist is bent (0 within it; 1 is twice as
        far as it goes), on a squared-off ellipse: a wrist bends a long way
        toward the palm while bent a little sideways, not as far as either alone."""
        lp = self.FLEX if phi > 0 else self.EXT
        ld = self.RADIAL if dev > 0 else self.ULNAR
        e = ((phi / lp) ** 4 + (dev / ld) ** 4) ** 0.25
        return max(0.0, e - 1.0)

    def _wrist_clamp(self, phi, dev):
        """A wrist bend brought within its range, the way it was bending."""
        lp = self.FLEX if phi > 0 else self.EXT
        ld = self.RADIAL if dev > 0 else self.ULNAR
        e = ((phi / lp) ** 4 + (dev / ld) ** 4) ** 0.25
        if e <= 1.0:
            return phi, dev
        # Each within its own range first (so a bend that is only too far
        # sideways keeps its flexion), then the two together.
        phi = max(-self.EXT, min(self.FLEX, phi))
        dev = max(-self.ULNAR, min(self.RADIAL, dev))
        e = ((phi / lp) ** 4 + (dev / ld) ** 4) ** 0.25
        if e > 1.0:
            phi, dev = phi / e, dev / e
        return phi, dev

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
            arc_t = pos_t = None
            if "arc" in spec:
                az, el, r = spec["arc"]
                d = np.array([math.sin(math.radians(az)) * math.cos(math.radians(el)), math.sin(math.radians(el)),
                              math.cos(math.radians(az)) * math.cos(math.radians(el))])
                arc_t = sh + qrot(chest, d) * r
            if "pos" in spec:
                # A point in her space (a hand on a knee, behind her ear): in
                # her character's space, whatever frame the hand's aim uses.
                pos_t = np.array(spec["pos"], float)
            if arc_t is not None and pos_t is not None:
                target = arc_t + (pos_t - arc_t) * spec.get("mix", 1.0)
            elif arc_t is not None:
                target = arc_t
            elif pos_t is not None:
                target = pos_t
            else:
                target = gpos[ha]
            s = 1 if side == "l" else -1
            pole = np.array(spec.get("pole", (s * 0.6, -0.3, -1.0)), float)
            pole = qrot(frame, pole) if spec.get("frame") == "chest" else pole
            S = gpos[ua].copy()
            elbow_at = getattr(self, "elbow_force", None)
            if elbow_at is not None and side in elbow_at:
                # Where the elbow goes, settled over the whole clip (solve_frames):
                # bent toward it, whatever the pole would say this frame.
                eb, wr = two_bone_ik(gpos[ua], gpos[la], gpos[ha], target, S + elbow_at[side])
            else:
                eb, wr = two_bone_ik(gpos[ua], gpos[la], gpos[ha], target, gpos[la] + pole)
            aimed = "blade" in spec or "knuckles" in spec or "thumb" in spec
            # A weapon is held in a diagonal grip: its shaft crosses the palm
            # from the root of the forefinger to the heel of the hand, so it
            # leans from square to the fingers toward them (Rig.grip, from the
            # clip's weapon; the game mounts it so, Arms.Hold). The blade and
            # knuckles keyed are the grip's; the hand is turned back from it.
            lean = self.grip.get(side, 0.0) if "blade" in spec else 0.0
            lq = qaxis([1.0, 0, 0], -lean) if lean else None

            def want_for(d_la):
                """The hand's wanted turn in her space (blade and knuckles; what
                is not given is kept from the hand riding the forearm)."""
                if "thumb" in spec and "blade" not in spec and "knuckles" not in spec:
                    # The wrist left straight and the forearm rolled until the
                    # thumb side faces as near this way as it can: a carried
                    # weapon goes where the arm takes it, in the grip's lean
                    # from the forearm, as a relaxed hand holds one.
                    cur = qmul(d_la, self.grest[ha])
                    fa_ = qrot(d_la, self.prest[ha] - self.prest[la])
                    fa_ = fa_ / np.linalg.norm(fa_)
                    t = np.array(spec["thumb"], float)
                    t = qrot(frame, t) if spec.get("frame") == "chest" else t
                    z = qrot(cur, [0, 0, 1.0])
                    zp, tp = z - fa_ * np.dot(z, fa_), t - fa_ * np.dot(t, fa_)
                    if np.linalg.norm(zp) < 1e-6 or np.linalg.norm(tp) < 1e-6:
                        return cur
                    ang = math.degrees(math.atan2(float(np.dot(np.cross(zp, tp), fa_)), float(np.dot(zp, tp))))
                    return qmul(qaxis(fa_, ang), cur)
                want = _want_grip(qmul(qmul(d_la, self.grest[ha]), lq) if lq is not None else qmul(d_la, self.grest[ha]))
                return qmul(want, qinv(lq)) if lq is not None else want

            def _want_grip(cur):
                z, y = qrot(cur, [0, 0, 1]), qrot(cur, [0, 1, 0])
                if "blade" in spec:
                    z = np.array(spec["blade"], float)
                    z = qrot(frame, z) if spec.get("frame") == "chest" else z
                if "knuckles" in spec:
                    y = np.array(spec["knuckles"], float)
                    y = qrot(frame, y) if spec.get("frame") == "chest" else y
                if "blade" in spec and "knuckles" in spec:
                    z = z / np.linalg.norm(z)
                    y = y - z * np.dot(y, z)
                    y = y / np.linalg.norm(y)
                    want = qfrom_basis(np.cross(y, z), y, z)
                elif "blade" in spec:
                    # Only the blade's way given: the hand turned the least way
                    # from how it rides the forearm (never spun about it).
                    want = qmul(qbetween(qrot(cur, [0, 0, 1]), z), cur)
                else:
                    want = qmul(qbetween(qrot(cur, [0, 1, 0]), y), cur)
                # "aim" 0..1: how much the hand is aimed at all (0: it rides the
                # forearm as it would hang), so a hand can let go of its aim.
                a = spec.get("aim", 1.0)
                return want if a >= 1.0 else qslerp(cur, want, max(0.0, a))

            def config(phi):
                """The arm with its elbow swung phi degrees about shoulder to wrist."""
                axis = (wr - S) / np.linalg.norm(wr - S)
                spin = qaxis(axis, phi)
                E = S + qrot(spin, eb - S)
                d_ua, d_la = self._bend("arm", side, ua, la, ha, delta[ua], delta[la], S, E, wr, qrot(spin, pole))
                return d_ua, d_la

            d_ua, d_la = config(0.0)
            phi = 0.0
            force = getattr(self, "swivel_force", None)
            if force is not None and side in force:
                # The swivel already settled for this frame (solve_frames).
                phi = force[side]
                if phi:
                    d_ua, d_la = config(phi)
            elif "blade" in spec or "knuckles" in spec:
                # A wrist keyed past what it can do: swing the elbow round (as
                # little, and as like the last frame, as will do) until it can.
                # (Not for a thumb's way alone: the wrist is straight, and the
                # roll simply goes as far as the forearm turns.)
                fa = (wr - eb) / np.linalg.norm(wr - eb)
                tw_deg, sw_deg, _, _, wp, wd = self._strain(d_la, want_for(d_la), ha, fa, side)
                if abs(tw_deg) > self.TWIST_LIMIT or self._wrist_over(wp, wd) > 0:
                    prev = self.swivel.get(side, 0.0)
                    best = None
                    for cand in range(-42, 43, 6):
                        c_ua, c_la = config(float(cand))
                        E = S + qrot(qaxis((wr - S) / np.linalg.norm(wr - S), cand), eb - S)
                        cfa = (wr - E) / np.linalg.norm(wr - E)
                        t, _, _, _, cp, cd = self._strain(c_la, want_for(c_la), ha, cfa, side)
                        cost = (max(0.0, abs(t) - self.TWIST_LIMIT) ** 2 + 2 * (40 * self._wrist_over(cp, cd)) ** 2
                                + 0.08 * cand * cand + 0.8 * (cand - prev) ** 2)
                        if best is None or cost < best[0]:
                            best = (cost, float(cand), c_ua, c_la)
                    _, phi, d_ua, d_la = best
            self.swivel[side] = phi
            delta[ua], delta[la] = d_ua, d_la
            # Where this elbow went, from the shoulder (for solve_frames).
            if not hasattr(self, "elbow_seen"):
                self.elbow_seen = {}
            self.elbow_seen[side] = qrot(d_ua, self.prest[la] - self.prest[ua])
            refresh()
            # The hand: aimed by blade and knuckles if given, else it rides
            # the forearm.
            if aimed:
                fa = gpos[ha] - gpos[la]
                fa = fa / np.linalg.norm(fa)
                want = want_for(delta[la])
                tw_deg, sw_deg, tw, sw, _, _ = self._strain(delta[la], want, ha, fa, side)
                # The turn about the forearm taken the way nearest last
                # frame's (a hand keyed past half a turn would otherwise flip
                # from one side to the other between two frames).
                last = getattr(self, "twist_last", {}).get(side)
                if last is not None:
                    tw_deg += 360.0 * round((last - tw_deg) / 360.0)
                    # A hand keyed nearly back along its forearm has no
                    # meaningful turn about it (the split is singular there):
                    # hold the turn it had rather than follow the noise.
                    if sw_deg > 120:
                        tw_deg = last + max(-8.0, min(8.0, tw_deg - last))
                if not hasattr(self, "twist_last"):
                    self.twist_last = {}
                self.twist_last[side] = tw_deg
                # Within what a forearm and a wrist can do.
                tw_c = max(-self.TWIST_LIMIT, min(self.TWIST_LIMIT, tw_deg))
                # The wrist bent toward the wanted hand, the short way round
                # unless the hand is keyed nearly back along the forearm; then
                # the way it bent last frame (either way is as near, and
                # choosing afresh each frame flips it).
                axis = sw[:3] / max(np.linalg.norm(sw[:3]), 1e-9)
                prev = getattr(self, "swing_last", {}).get(side)
                if prev is not None and sw_deg > 120 and float(np.dot(axis, prev)) < 0:
                    axis, sw_deg = -axis, 360.0 - sw_deg
                if prev is not None and sw_deg > 120:
                    # Near the singular split the bend's axis wheels round
                    # from frame to frame: let it drift, not jump.
                    axis = prev * 0.8 + axis * 0.2
                    axis = axis / max(np.linalg.norm(axis), 1e-9)
                if not hasattr(self, "swing_last"):
                    self.swing_last = {}
                if sw_deg > 1:
                    self.swing_last[side] = axis
                # Then within the wrist's own range: far toward the palm and
                # back, little to either side.
                cur = qmul(delta[la], self.grest[ha])
                hand_t = qmul(qaxis(fa, tw_c), cur)
                wp, wd = self._wrist_split(axis, sw_deg, hand_t, side)
                wp, wd = self._wrist_clamp(wp, wd)
                sw = self._wrist_join(wp, wd, hand_t, side)
                want = qmul(sw, hand_t)
                hd = qmul(want, qinv(self.grest[ha]))
                # The forearm takes its share of the turn about its length (the
                # radius rolling over the ulna), so the wrist does not wring.
                # (At least half: a wrist has no roll of its own, and with no
                # twist bones half at the elbow and half at the wrist spreads it.)
                share = max(0.5, spec.get("twist", 0.5))
                if share > 0:
                    delta[la] = qmul(qaxis(fa, share * tw_c), delta[la])
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
            s = 1 if side == "l" else -1
            p = np.array(spec.get("pos", (rest_ankle[0], 0, rest_ankle[2])), float)
            # A body that stands wider sets each keyed foot further out.
            target = np.array([p[0] + s * self.feet_out * ("pos" in spec), rest_ankle[1] + p[1], p[2]])
            pole = np.array(spec.get("pole", (s * 0.15, 0, 1.0)), float)
            kb, an = two_bone_ik(gpos[th], gpos[ca], gpos[fo], target, gpos[ca] + pole)
            # The thigh turned about its length so the knee bends straight
            # over the shin, never out to the side.
            delta[th], delta[ca] = self._bend("leg", side, th, ca, fo, delta[th], delta[ca], gpos[th].copy(), kb, an, pole)
            refresh()
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
            # The thumb swung in across the palm before it bends ("oppose", 0..1),
            # so a fist closes over the fingers instead of thumbing a lift.
            oppose = spec.get("oppose", 0) if isinstance(spec, dict) else 0
            if oppose:
                j = I[f"thumb_01_{side}"]
                along = qrot(qinv(self.grest[j]), qrot(self.grest[I[f"hand_{side}"]], [0, 1.0, 0]))
                local[j] = qmul(local[j], qaxis(along / np.linalg.norm(along), oppose * 55 * (1 if side == "l" else -1)))
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


def _slerp_vec(a, b, u):
    """Unit directions turned from a to b along the arc between them."""
    d = max(-1.0, min(1.0, float(np.dot(a, b))))
    w = math.acos(d)
    if w < 1e-4:
        v = a + (b - a) * u
    elif w > math.pi - 1e-3:
        # Opposite: round through any direction square to them.
        side = np.cross(a, [0.0, 1.0, 0.0])
        if np.linalg.norm(side) < 1e-6:
            side = np.cross(a, [1.0, 0.0, 0.0])
        side = side / np.linalg.norm(side)
        v = a * math.cos(math.pi * u) + side * math.sin(math.pi * u)
    else:
        v = (math.sin((1 - u) * w) * a + math.sin(u * w) * b) / math.sin(w)
    return v / np.linalg.norm(v)


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
    i = min(bisect.bisect_right(ts, t) - 1, n - 2)
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


# A blow thrown from the ground up: the feet and hips a frame and a half
# ahead of the hands, the back nearly a frame, the shoulders a little.
STRIKE = {"hips": 1.5, "foot_": 1.5, "spine": 0.8, "clav_": 0.4}


def smoothstep_(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def _zero_default(n):
    head = n.split("#")[0]
    return head.startswith(("hips.", "spine", "neck", "head", "clav_")) or head.endswith((".rot", ".toe"))


class Track:
    """Keys [(frame, pose, ease), ...] as a pose at any frame."""

    def __init__(self, keys):
        self.keys = sorted(keys, key=lambda k: k[0])
        self.flats = [_flatten(k[1]) for k in self.keys]
        self.names = set()
        for f in self.flats:
            self.names |= set(f)
        # A turn or offset a key leaves out is none at that key (so a key
        # without "spine" stands straight); a hand or foot a key leaves out
        # is wherever the keys either side put it.
        for f in self.flats:
            for n in self.names:
                if n not in f and _zero_default(n):
                    f[n] = 0.0
        self.frames = int(round(self.keys[-1][0])) + 1
        # Each control's own keys, gathered once (a clip keyed every frame
        # would otherwise gather them again for every control at every frame).
        self.have = {n: [(k[0], f[n], k[2] if len(k) > 2 else "auto") for k, f in zip(self.keys, self.flats) if n in f]
                     for n in self.names}
        self.vectors = sorted({n[:-2] for n in self.names if n.endswith("#0") and n.split("#")[0].split(".")[-1]
                               in ("blade", "knuckles", "pole", "thumb") and all(f"{n[:-2]}#{i}" in self.names for i in (1, 2))
                               and len(self.have[n]) == len(self.have[n[:-2] + "#1"]) == len(self.have[n[:-2] + "#2"])})

    def __call__(self, fr, lead=None):
        """The pose at frame fr. `lead`: frames ahead each part of her runs
        ({"hips": 1.5, "spine": 0.8}): the body leading the hands, so a blow
        is thrown from the hips with the blade's own timing kept."""
        flat = {}
        for n in self.names:
            have = self.have[n]
            if not have:
                continue
            t = fr
            if lead:
                for part, ahead in lead.items():
                    if n.startswith(part):
                        t = min(fr + ahead, have[-1][0])
                        break
            if isinstance(have[0][1], float):
                flat[n] = _hermite([h[0] for h in have], [h[1] for h in have], [h[2] for h in have], t)
            else:
                # Presets switch at the key nearest in time.
                flat[n] = min(have, key=lambda h: abs(h[0] - fr))[1]
        # A direction (a blade's, the knuckles', an elbow's way) is turned
        # round the sphere from key to key, not drawn through it: two keys a
        # long way apart would otherwise pass near nothing between them and
        # the hand would spin over in a frame.
        for vec in self.vectors:
            names = [f"{vec}#{i}" for i in range(3)]
            have = self.have[names[0]]
            t = fr
            if len(have) < 2 or t <= have[0][0] or t >= have[-1][0]:
                continue
            i = min(bisect.bisect_right([h[0] for h in have], t) - 1, len(have) - 2)
            a = np.array([self.have[n][i][1] for n in names])
            b = np.array([self.have[n][i + 1][1] for n in names])
            na, nb = np.linalg.norm(a), np.linalg.norm(b)
            if na < 1e-6 or nb < 1e-6:
                continue
            ang = math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(a, b) / (na * nb))))))
            if ang < 60:
                continue
            # How far through the segment the components went (the eased
            # parameter), applied along the arc between the two keys.
            t0, t1 = have[i][0], have[i + 1][0]
            e0, e1 = have[i][2], have[i + 1][2]
            # (A strike's "fast" key whips the fist, not the hand's roll: a
            # hand turned over in a frame reads as a flip, so it turns evenly.)
            ease = {"auto": "ease", "fast": "linear"}
            u = _hermite([t0, t1], [0.0, 1.0], [ease.get(e0, e0), ease.get(e1, e1)], t)
            arc = _slerp_vec(a / na, b / nb, u) * (na + (nb - na) * u)
            lin = np.array([flat[n] for n in names])
            w = min(1.0, (ang - 60) / 40.0)
            v = lin * (1 - w) + arc * w
            for k, n in enumerate(names):
                flat[n] = float(v[k])
        # A hand placed on an arc in one key and at a point in the next: the
        # two targets cross-faded between them (each held from its own keys).
        for side in "lr":
            h = f"hand_{side}"
            modes = [(k[0], "pos" if f"{h}.pos#0" in f else "arc") for k, f in zip(self.keys, self.flats)
                     if f"{h}.pos#0" in f or f"{h}.arc#0" in f]
            if not modes:
                continue
            before = [m for m in modes if m[0] <= fr] or modes[:1]
            after = [m for m in modes if m[0] > fr] or modes[-1:]
            (t0, m0), (t1, m1) = before[-1], after[0]
            if m0 == m1 or t1 <= t0:
                drop = "arc" if m0 == "pos" else "pos"
                for i in range(3):
                    flat.pop(f"{h}.{drop}#{i}", None)
                continue
            u = float(smoothstep_((fr - t0) / (t1 - t0)))
            flat[f"{h}.mix"] = u if m1 == "pos" else 1 - u
        return _unflatten(flat)


def _aims(keys):
    """A hand aimed (blade or knuckles) in some keys and not in others: the
    keys without an aim let go of it ("aim" 0: the hand rides the forearm),
    rather than holding the last key's aim on a hand that has gone
    elsewhere (a hand pushed into the hair would stay turned that way as
    the arm came down to hang)."""
    out = list(keys)
    for side in "lr":
        h = f"hand_{side}"
        aimed = [isinstance(k[1].get(h), dict) and any(v in k[1][h] for v in ("blade", "knuckles", "thumb")) for k in keys]
        held = [isinstance(k[1].get(h), dict) for k in keys]
        if not any(aimed) or all(a for a, hh in zip(aimed, held) if hh):
            continue
        for i, k in enumerate(out):
            spec = k[1].get(h)
            if not isinstance(spec, dict) or "aim" in spec:
                continue
            pose = dict(k[1])
            pose[h] = dict(spec, aim=1.0 if aimed[i] else 0.0)
            out[i] = (k[0], pose) + tuple(k[2:])
    return out


def _whole_aims(rig: Rig, keys, base=None):
    """A hand given its blade in some keys and only its knuckles (or the
    reverse) in others: each key's missing half filled with what that key
    alone makes of it. A control a key leaves out is otherwise held from
    the nearest key that has it, so a blade keyed only at the end would
    turn the hand from the very first frame, and jump where it first
    appears."""
    out = list(keys)
    for side in "lr":
        h = f"hand_{side}"
        specs = [k[1].get(h) if isinstance(k[1].get(h), dict) else None for k in keys]
        has_b = [s is not None and "blade" in s for s in specs]
        has_k = [s is not None and "knuckles" in s for s in specs]
        # (A thumb's way alone, beside keys that aim the hand outright, is
        # filled the same way: the aimed keys' blade would otherwise be held
        # over it.)
        has_t = [s is not None and "thumb" in s and not b and not kk for s, b, kk in zip(specs, has_b, has_k)]
        aimed = [b or kk or t for b, kk, t in zip(has_b, has_k, has_t)]
        if not any(aimed):
            continue
        mixed = len({(b, kk) for b, kk, a in zip(has_b, has_k, aimed) if a}) > 1
        if not mixed:
            continue
        # The blade and knuckles filled in are the grip's (Rig.grip), as keyed ones are.
        lean = rig.grip.get(side, 0.0)
        lq = qaxis([1.0, 0, 0], -lean)
        for i, k in enumerate(out):
            spec = specs[i]
            if spec is None or not aimed[i] or (has_b[i] and has_k[i]):
                continue
            fr = int(round(k[0]))
            b = None if base is None else (base.rot[min(fr, base.frames - 1)], base.pos[min(fr, base.frames - 1)])
            rig.swivel_force = {}
            local, pos = rig.solve(k[1], base=b)
            rig.swivel_force = None
            g, _ = rig.globals(local, pos)
            q = qmul(g[0, rig.I[h]], lq)
            spec = {kk: v for kk, v in spec.items() if kk != "thumb"}
            spec = dict(spec, frame="char", blade=tuple(float(x) for x in qrot(q, [0, 0, 1.0])),
                        knuckles=tuple(float(x) for x in qrot(q, [0, 1.0, 0])))
            if "pole" in specs[i] and specs[i].get("frame") == "chest":
                # (The pole was in the chest's frame: carry it into hers too.)
                chest = qmul(g[0, rig.I["spine_03"]], qinv(rig.grest[rig.I["spine_03"]]))
                spec["pole"] = tuple(float(x) for x in qrot(chest, np.array(specs[i]["pole"], float)))
            pose = dict(k[1])
            pose[h] = spec
            out[i] = (k[0], pose) + tuple(k[2:])
    return out


def _one_frame(rig: Rig, keys, base=None):
    """Keys whose hand is aimed in the chest's frame in some keys and in her
    space in others, all put in her space (each by its own key's chest), so
    the aim is never read in the wrong frame between them."""
    keys = _whole_aims(rig, _aims(keys), base)
    out = list(keys)
    s3 = rig.I["spine_03"]
    for side in "lr":
        h = f"hand_{side}"
        frames = {k[1][h].get("frame", "char") for k in keys if isinstance(k[1].get(h), dict)
                  and any(v in k[1][h] for v in ("blade", "knuckles", "pole", "thumb"))}
        if len(frames) < 2:
            continue
        for i, k in enumerate(out):
            spec = k[1].get(h)
            if not isinstance(spec, dict) or spec.get("frame", "char") != "chest":
                continue
            fr = int(round(k[0]))
            b = None if base is None else (base.rot[min(fr, base.frames - 1)], base.pos[min(fr, base.frames - 1)])
            rig.swivel_force = {}
            local, pos = rig.solve(k[1], base=b)
            rig.swivel_force = None
            g, _ = rig.globals(local, pos)
            chest = qmul(g[0, s3], qinv(rig.grest[s3]))
            spec = dict(spec, frame="char")
            for v in ("blade", "knuckles", "pole", "thumb"):
                if v in spec:
                    spec[v] = tuple(float(x) for x in qrot(chest, np.array(spec[v], float)))
            pose = dict(k[1])
            pose[h] = spec
            out[i] = (k[0], pose) + tuple(k[2:])
    return out


# How far each weapon's shaft leans in a diagonal grip, from square to the
# fingers toward them (degrees): a sword's grip runs from the root of the
# forefinger to the heel of the hand, so with the wrist straight the blade
# rises at about 55 degrees from the forearm's line and a little ulnar bend
# puts it nearly in line. An axe's haft is gripped nearer square, a staff and
# a crossbow square (mid-shaft; pistol fashion). Only her and the hero
# (Rig.grips): the folk also play the Universal Animation Library, held
# square. Must match the game's mounts (Arms.Spec.Lean).
GRIP = {"sword": 35.0, "axe": 30.0, "daggers": 30.0, "wand": 30.0}


def grip_of(weapon):
    """Each fist's lean for a clip that holds `weapon` (its meta's "weapon":
    "sword+shield", "axe", "axes", "daggers", "wand", "staff", "crossbow")."""
    if not weapon:
        return {}
    main = weapon.split("+")[0]
    if main == "axes":
        return {"r": GRIP["axe"], "l": GRIP["axe"]}
    if main == "daggers":
        return {"r": GRIP["daggers"], "l": GRIP["daggers"]}
    return {"r": GRIP[main]} if main in GRIP else {}


def solve_frames(rig: Rig, poses, bases=None, loop=False, sigma=2.0, weapon=""):
    """Every frame's pose solved, where each elbow goes settled over the
    whole clip first: solved frame by frame (the pole's way, swung round
    where a keyed wrist needs it), then smoothed in time, so an elbow eases
    round instead of whipping between frames as the hand passes near the
    shoulder or the wrist's strain tips it from one side to the other.
    `weapon`: what the clip holds (grip_of)."""
    rig.grip = grip_of(weapon) if rig.grips else {}
    n = len(poses)
    J = len(rig.sk)
    rot = np.empty((n, J, 4))
    pos = np.empty((n, J, 3))
    rig.swivel, rig.swivel_force, rig.twist_last, rig.swing_last, rig.bend_last = {}, None, {}, {}, {}
    rig.elbow_force = None
    seen = {"l": np.full((n, 3), np.nan), "r": np.full((n, 3), np.nan)}
    rig.bend_force = None
    for fr, pose in enumerate(poses):
        b = None if bases is None else bases[fr]
        rig.elbow_seen = {}
        rot[fr], pos[fr] = rig.solve(pose, base=b)
        for s in "lr":
            if s in rig.elbow_seen:
                seen[s][fr] = rig.elbow_seen[s]
    # Straight stretches of each limb: the hinge's way there turned evenly
    # from the bend going in to the bend coming out (a limb is free to roll
    # while it is straight, and does so then, not in the frame it bends).
    g1, p1 = rig.sk.fk(rot, pos)
    I = rig.I
    bend_force = [dict() for _ in range(n)]
    for kind, top, mid, end in (("arm", "upperarm", "lowerarm", "hand"), ("leg", "thigh", "calf", "foot")):
        for s in "lr":
            S, E, W = p1[:, I[f"{top}_{s}"]], p1[:, I[f"{mid}_{s}"]], p1[:, I[f"{end}_{s}"]]
            c = np.cross(E - S, W - E)
            sinb = np.linalg.norm(c, axis=1) / (np.linalg.norm(E - S, axis=1) * np.linalg.norm(W - E, axis=1) + 1e-9)
            nrm = c / np.maximum(np.linalg.norm(c, axis=1, keepdims=True), 1e-9)
            bent = sinb >= 0.35
            fr = 0
            while fr < n:
                if bent[fr]:
                    fr += 1
                    continue
                a = fr
                while fr < n and not bent[fr]:
                    fr += 1
                b0 = fr  # first bent frame after the stretch (or n)
                na = nrm[a - 1] if a > 0 else (nrm[b0] if b0 < n else None)
                nb = nrm[b0] if b0 < n else na
                if na is None:
                    continue
                for t in range(a, b0):
                    u = (t - a + 1) / (b0 - a + 1)
                    u = u * u * (3 - 2 * u)
                    bend_force[t][(kind, s)] = _slerp_vec(na, nb, u)
    rig.twist_last, rig.swing_last, rig.bend_last = {}, {}, {}
    rig.bend_force = None
    k = np.exp(-0.5 * (np.arange(-int(3 * sigma), int(3 * sigma) + 1) / sigma) ** 2)
    pad = len(k) // 2
    smooth = {}
    for s in "lr":
        x = seen[s]
        have = ~np.isnan(x[:, 0])
        if not have.any():
            continue
        out = np.full((n, 3), np.nan)
        for fr in np.nonzero(have)[0]:
            idx = np.arange(fr - pad, fr + pad + 1)
            if loop:
                idx = idx % max(1, n - 1)
            ok = (idx >= 0) & (idx < n)
            idx, w = idx[ok], k[ok]
            ok = have[idx]
            idx, w = idx[ok], w[ok]
            v = (x[idx] * w[:, None]).sum(0) / w.sum()
            out[fr] = v
        smooth[s] = out
    rig.twist_last, rig.swing_last, rig.bend_last = {}, {}, {}
    for fr, pose in enumerate(poses):
        b = None if bases is None else bases[fr]
        force = {s: smooth[s][fr] for s in smooth if not np.isnan(smooth[s][fr, 0])}
        rig.elbow_force = force
        rig.swivel_force = {s: 0.0 for s in force}
        rig.bend_force = bend_force[fr]
        rot[fr], pos[fr] = rig.solve(pose, base=b)
    rig.swivel_force = rig.elbow_force = rig.bend_force = None
    return rot, pos


def build(name, rig: Rig, keys, fps=30, loop=False, meta=None, post=None, base=None, lead=None) -> Clip:
    """A clip from keys [(frame, pose, ease), ...]. For a loop, the last key
    should be the first again. With a base clip, the keys are laid over its
    frames (Rig.solve's base): turns add to its turns, hands and feet given
    are solved afresh. `lead`: see Track. A weapon in the meta ("weapon")
    sits in the fist's diagonal grip (GRIP)."""
    rig.grip = grip_of((meta or {}).get("weapon")) if rig.grips else {}
    keys = _one_frame(rig, keys, base)
    track = Track(keys)
    frames = track.frames
    poses = []
    for fr in range(frames):
        pose = track(fr, lead)
        poses.append(post(fr, pose) if post else pose)
    bases = None if base is None else [(base.rot[min(fr, base.frames - 1)], base.pos[min(fr, base.frames - 1)])
                                       for fr in range(frames)]
    rot, pos = solve_frames(rig, poses, bases, loop=loop, weapon=(meta or {}).get("weapon", ""))
    m = {"source": "keyed (tools/anim)", "licence": "own work"}
    m.update(meta or {})
    return Clip(name, fps, rot, pos, loop=loop, meta=m)
