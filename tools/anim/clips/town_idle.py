"""Her town idles, one per calling (animation 48; the owner, 20-21 Oct: "I adore the idle sway ... a lot of the looks
are rigid even when safe", then "having their own is probably better than all the same"). The warden keeps her
WiggleHips sway (idle.py, idle_warden_town). Each other calling gets its own way of standing at ease: a captured
take (100STYLE, CC BY 4.0) for the breath and the small life, set into a relaxed stance by `contra` (the weight on
one hip, the free knee soft, the shoulders tilted against the hips, a slow settle across the loop) and, for the
stalker, `look` (her head's slow look to one side and back).

The 100STYLE idle takes stand square and still: of 29 measured (scratch anim/town meas.py), 23 keep her pelvis within
1 cm, her weight within 0.3 of the middle of her feet and her hips level within 2 deg: "weight even on both feet",
the owner's anxious stance. So the stance is made here, the take kept for what it moves.
"""
from __future__ import annotations

import math

import numpy as np

from rig import Clip


def _env(T, amp, phase):
    """A periodic envelope over the loop (first and last frames meet): 1 + amp * sin(2 pi t + phase)."""
    t = np.arange(T) / max(T - 1, 1)
    return 1.0 + amp * np.sin(2 * math.pi * t + phase)


def contra(rig, clip: Clip, side="l", shift=0.06, roll=6.0, yaw=0.0, counter=0.5, knee=4.0, settle=0.25, phase=0.0,
           free_out=0.0, free_fwd=0.0, free_turn=0.0, free_knee_in=0.0, chest_yaw=0.0, width=None, free_knee=None,
           turn_in=False, stand_back=0.0, feet_shift=0.0, roll_floor=None) -> Clip:
    """`clip` stood with her weight on one leg (contrapposto). side: the standing leg ("l"/"r"); shift: her pelvis
    carried that far toward it (m); roll: the hips tilted, the standing hip up (deg); yaw: the free hip brought forward
    (deg); counter: the shoulders tilted back against the hips (a share of roll, through the spine); knee: the
    standing knee's mean bend (deg; the free one bends as it must to reach its foot); settle: the shift and tilt
    swelling and easing once over the loop (a share), from `phase`. The free foot: moved out (m, away from the
    standing one) and forward (m), turned out (deg), its knee drawn in toward the other (m on the knee's aim).
    chest_yaw: the chest's turn left at the top of the spine (deg). width: her ankles set that far apart (m) first.
    free_knee: the free knee's mean bend (deg), made by drawing the free foot in under its hip (toward the standing
    leg) as far as it takes (or out, for less): a soft free knee is what reads as the weight off it.
    turn_in: the free thigh turned about its own length so its knee's hinge lies across the bend free_knee_in drew in
    (the kneecap turned in toward the other leg, as a hip turned in carries it, not a knee bent sideways).
    feet_shift: both feet set that far (m) toward the free side, her hips' path kept: for a stand that sways (the
    warden's WiggleHips), so the sway rides on her standing leg, from a little on it to fully on it, not across the
    middle; roll_floor: the hips' roll (deg, with the take's own) held above it, so they never come level.
    stand_back: the standing foot set back (m), so the free one leads it without its thigh reaching far forward (a
    thigh reaching forward lifts its knee: the free knee reads lower only while its thigh stays near upright).
    Her head keeps the take's own carriage (the neck takes back the spine's turn)."""
    from rig import qaxis, qbetween, qinv, qmul, qrot, two_bone_ik
    sk = rig.sk
    rot, pos = clip.rot.copy(), clip.pos.copy()
    T = rot.shape[0]
    pel, root = sk.i("pelvis"), sk.i("root")
    spine = [sk.i("spine_01"), sk.i("spine_02"), sk.i("spine_03")]
    neck = sk.i("neck_01")
    g, p = sk.fk(rot, pos)
    ank = {s: p[:, sk.i(f"foot_{s}")].copy() for s in "lr"}
    ball = {s: p[:, sk.i(f"ball_{s}")] for s in "lr"}
    foot_g = {s: g[:, sk.i(f"foot_{s}")].copy() for s in "lr"}
    bend0 = {s: p[:, sk.i(f"calf_{s}")] - (p[:, sk.i(f"thigh_{s}")] + ank[s]) / 2 for s in "lr"}
    fwd = sum(ball[s] - ank[s] for s in "lr").mean(axis=0)
    fwd[1] = 0
    fwd /= np.linalg.norm(fwd)
    up = np.array([0.0, 1.0, 0.0])
    left = np.cross(up, fwd)
    sgn = 1.0 if side == "l" else -1.0          # toward the standing leg, along `left`
    free = "r" if side == "l" else "l"
    if width:
        apart = np.mean(np.abs(np.sum((ank["l"] - ank["r"]) * left, axis=1)))
        for s, k in (("l", 1.0), ("r", -1.0)):
            ank[s] = ank[s] + left * k * (width - apart) / 2
    # The free foot set out, forward and turned out (fixed offsets: planted stays planted).
    ank[free] = ank[free] - left * sgn * free_out + fwd * free_fwd
    ank[side] = ank[side] - fwd * stand_back
    for s_ in "lr":
        ank[s_] = ank[s_] - left * sgn * feet_shift
    if free_turn:
        tq = qaxis(up, -sgn * free_turn)     # its toes turned away from the standing leg
        foot_g[free] = qmul(np.broadcast_to(tq, foot_g[free].shape), foot_g[free])
    a = _env(T, settle, phase)
    shiftv = (left * sgn)[None, :] * (shift * a)[:, None]
    # The pelvis: the standing hip up (a turn about her forward axis), the free hip forward (about up).
    rr = sgn * roll * a
    if roll_floor is not None:
        # Her hips never come level: the take's own roll (+ the standing hip up) with ours, held softly above the floor.
        hl = p[:, sk.i("thigh_l")] - p[:, sk.i("thigh_r")]
        r0 = sgn * np.degrees(np.arctan2(hl[:, 1], np.hypot(hl @ left, hl @ fwd)))
        k = 1.5
        tot = r0 + roll * a
        rr = sgn * (roll_floor + k * np.logaddexp(0.0, (tot - roll_floor) / k) - r0)
    Tp = np.array([qmul(qaxis(up, sgn * yaw * a[f]), qaxis(fwd, rr[f])) for f in range(T)])
    gp_new = qmul(Tp, g[:, pel])
    rot[:, pel] = qmul(qinv(g[:, root]), gp_new)
    # The spine takes the tilt and the hips' turn back, a third a joint, to `counter` the other way at the chest.
    par = gp_new
    for k, j in enumerate(spine, 1):
        r_k = rr * (1 - (1 + counter) * k / 3)
        y_k = sgn * yaw * a * (1 - k / 3) + chest_yaw * k / 3
        Tk = np.array([qmul(qaxis(up, y_k[f]), qaxis(fwd, r_k[f])) for f in range(T)])
        gj = qmul(Tk, g[:, j])
        rot[:, j] = qmul(qinv(par), gj)
        par = gj
    # The neck back to its own carriage (the head as the take held it).
    rot[:, neck] = qmul(qinv(par), g[:, neck])

    knee_in = {free: free_knee_in, side: 0.0}
    h0 = _rest_hinges(sk) if turn_in else None

    def legs(dy):
        r, q = rot.copy(), pos.copy()
        d = shiftv + up[None, :] * dy
        q[:, pel] = q[:, pel] + qrot(qinv(g[:, root]), d)
        gl, gp = sk.fk(r, q)
        bends = {}
        for s in "lr":
            th, ca, fo = sk.i(f"thigh_{s}"), sk.i(f"calf_{s}"), sk.i(f"foot_{s}")
            bb = []
            for t in range(T):
                A, B, C = gp[t, th], gp[t, ca], gp[t, fo]
                kk = bend0[s][t] / max(np.linalg.norm(bend0[s][t]), 1e-6)
                # (the free knee drawn in toward the standing leg)
                kk = kk + left * sgn * knee_in[s] * 10
                kk /= np.linalg.norm(kk)
                nb, nc = two_bone_ik(A, B, C, ank[s][t], (A + ank[s][t]) / 2 + kk)
                r1 = qbetween(B - A, nb - A)
                if turn_in and s == free:
                    r1 = qmul(_hinge_twist(gl[t, th], r1, nb - A, nc - nb, h0[s]), r1)
                gth = qmul(r1, gl[t, th])
                c2 = nb + qrot(r1, C - B)
                gca = qmul(qbetween(c2 - nb, nc - nb), qmul(r1, gl[t, ca]))
                r[t, th] = qmul(qinv(gl[t, sk.parent[th]]), gth)
                r[t, ca] = qmul(qinv(gth), gca)
                r[t, fo] = qmul(qinv(gca), foot_g[s][t])
                u, v = nb - A, nc - nb
                bb.append(math.degrees(math.acos(np.clip(np.dot(u, v) / np.linalg.norm(u) / np.linalg.norm(v), -1, 1))))
            bends[s] = float(np.mean(bb))
        return r, q, bends

    lo, hi = -0.15, 0.10
    for _ in range(16):
        dy = (lo + hi) / 2
        _, _, b = legs(dy)
        lo, hi = (dy, hi) if b[side] > knee else (lo, dy)
    dy = (lo + hi) / 2
    tuck = 0.0
    if free_knee is not None:
        # (The standing leg's knee does not depend on the free foot: the height found above holds.)
        ank0 = ank[free].copy()
        lo, hi = -0.06, 0.12
        for _ in range(16):
            tuck = (lo + hi) / 2
            ank[free] = ank0 + left * sgn * tuck
            _, _, b = legs(dy)
            lo, hi = (lo, tuck) if b[free] > free_knee else (tuck, hi)
        tuck = (lo + hi) / 2
        ank[free] = ank0 + left * sgn * tuck
    r, q, b = legs(dy)
    meta = {**clip.meta, "changes": clip.meta.get("changes", "") +
            f"; her weight on the {'left' if side == 'l' else 'right'} leg (hips {roll:.0f} deg, carried {shift * 100:.0f} cm,"
            f" knees {b['l']:.0f}/{b['r']:.0f} deg, the free foot {tuck * 100:+.1f} cm in, a settle of {settle:.0%})"}
    return Clip(clip.name, clip.fps, r, q, loop=clip.loop, meta=meta)


def _rest_hinges(sk):
    """Each knee's hinge (audit.hinge_off's: across the thigh, square to her forward) in its thigh's own frame."""
    from rig import qinv, qrot
    rg, rp = (a[0] for a in sk.rest_globals())
    out = {}
    for s in "lr":
        th, ca = sk.i(f"thigh_{s}"), sk.i(f"calf_{s}")
        u0 = rp[ca] - rp[th]
        h = np.cross(u0 / np.linalg.norm(u0), np.array([0.0, 0.0, -1.0]))
        out[s] = qrot(qinv(rg[th]), h / np.linalg.norm(h))
    return out


def _hinge_twist(g_th, r1, u, v, h_local):
    """The turn about the thigh's length (u) that brings its knee hinge (h_local, the thigh's frame; the thigh at
    r1 * g_th) onto the bend the leg makes (thigh u, shin v)."""
    from rig import qaxis, qmul, qrot
    a = u / np.linalg.norm(u)
    h = qrot(qmul(r1, g_th), h_local)
    n = np.cross(u, v)
    if np.linalg.norm(n) < 1e-6 * np.linalg.norm(u) * np.linalg.norm(v):
        return np.array([0.0, 0.0, 0.0, 1.0])
    h, n = h - a * (h @ a), n - a * (n @ a)
    # (All but straight, the bend's plane says nothing: the turn eases in from 3 to 12 deg of bend.)
    bend = math.degrees(math.acos(np.clip(u @ v / np.linalg.norm(u) / np.linalg.norm(v), -1, 1)))
    w = min(1.0, max(0.0, (bend - 3.0) / 9.0))
    return qaxis(a, w * w * (3 - 2 * w) * math.degrees(math.atan2(float(a @ np.cross(h, n)), float(h @ n))))


def soften(rig, clip: Clip, knee=10.0, roll=3.5, chest=1.5, reach=0.04, roll_max=6.0) -> Clip:
    """A swaying stand (the warden's WiggleHips) never on two locked knees: as her hips swing over one foot the other
    knee softens `knee` deg (toward it as they come back through the middle, half each), and the pelvis rolls down
    on that side, about its own centre (the sway's path kept), solved per frame so each knee takes its bend: the
    roll sought near `roll` deg (at most roll_max), the pelvis's height for the loaded knee. The chest leans `chest`
    deg back against the roll through the spine; the head keeps its carriage. reach: how far (m) the hips swing off
    the middle of her feet before the weight is wholly on one foot (tanh)."""
    from rig import qaxis, qbetween, qinv, qmul, qrot, two_bone_ik
    sk = rig.sk
    rot, pos = clip.rot.copy(), clip.pos.copy()
    T = rot.shape[0]
    pel, root = sk.i("pelvis"), sk.i("root")
    spine = [sk.i("spine_01"), sk.i("spine_02"), sk.i("spine_03")]
    neck = sk.i("neck_01")
    g, p = sk.fk(rot, pos)
    J = {s: (sk.i(f"thigh_{s}"), sk.i(f"calf_{s}"), sk.i(f"foot_{s}")) for s in "lr"}
    ank = {s: p[:, J[s][2]].copy() for s in "lr"}
    foot_g = {s: g[:, J[s][2]].copy() for s in "lr"}
    fwd = sum(p[:, sk.i(f"ball_{s}")] - ank[s] for s in "lr").mean(axis=0)
    fwd[1] = 0
    fwd /= np.linalg.norm(fwd)
    up = np.array([0.0, 1.0, 0.0])
    left = np.cross(up, fwd)

    def bend(A, B, C):
        u, v = B - A, C - B
        return math.degrees(math.acos(np.clip(np.dot(u, v) / np.linalg.norm(u) / np.linalg.norm(v), -1, 1)))
    k0 = {s: np.array([bend(*(p[t, j] for j in J[s])) for t in range(T)]) for s in "lr"}
    w = np.tanh(((p[:, pel] - (ank["l"] + ank["r"]) / 2) @ left) / reach)   # + her hips over her left foot
    unl = {"l": (1 - w) / 2, "r": (1 + w) / 2}                              # each leg's share unloaded
    want = {s: k0[s] + knee * unl[s] for s in "lr"}
    rolls = np.zeros(T)

    def frame(t, rl, dy):
        """Frame t with the pelvis rolled rl deg (+ her left hip up) and lowered dy: (rot row, pos row, bends)."""
        r, q = rot[t].copy(), pos[t].copy()
        Tp = qaxis(fwd, rl)
        gp_new = qmul(Tp, g[t, pel])
        r[pel] = qmul(qinv(g[t, root]), gp_new)
        q[pel] = q[pel] + qrot(qinv(g[t, root]), up * dy)
        par = gp_new
        for k, j in enumerate(spine, 1):
            r_k = rl * (1 - k / 3) - (chest * np.sign(rl) * min(1.0, abs(rl) / max(roll, 1e-6))) * k / 3
            gj = qmul(qaxis(fwd, r_k), g[t, j])
            r[j] = qmul(qinv(par), gj)
            par = gj
        r[neck] = qmul(qinv(par), g[t, neck])
        gl, gpos = sk.fk(r[None], q[None])
        gl, gpos = gl[0], gpos[0]
        out = {}
        for s in "lr":
            th, ca, fo = J[s]
            A, B, C = gpos[th], gpos[ca], gpos[fo]
            kk = p[t, ca] - (p[t, th] + ank[s][t]) / 2
            kk = kk / max(np.linalg.norm(kk), 1e-6)
            nb, nc = two_bone_ik(A, B, C, ank[s][t], (A + ank[s][t]) / 2 + kk)
            r1 = qbetween(B - A, nb - A)
            gth = qmul(r1, gl[th])
            c2 = nb + qrot(r1, C - B)
            gca = qmul(qbetween(c2 - nb, nc - nb), qmul(r1, gl[ca]))
            r[th] = qmul(qinv(gl[sk.parent[th]]), gth)
            r[ca] = qmul(qinv(gth), gca)
            r[fo] = qmul(qinv(gca), foot_g[s][t])
            out[s] = bend(A, nb, nc)
        return r, q, out

    for t in range(T):
        un = "r" if w[t] >= 0 else "l"        # the leg coming unloaded
        ld = "l" if un == "r" else "r"
        sg = 1.0 if un == "r" else -1.0       # its hip down: + roll raises her left
        def height(rl):
            lo, hi = -0.06, 0.03
            for _ in range(14):
                dy = (lo + hi) / 2
                _, _, b = frame(t, rl, dy)
                lo, hi = (dy, hi) if b[ld] > want[ld][t] else (lo, dy)
            return (lo + hi) / 2
        lo, hi = 0.0, roll_max
        for _ in range(12):
            a = (lo + hi) / 2
            _, _, b = frame(t, sg * a, height(sg * a))
            lo, hi = (lo, a) if b[un] > want[un][t] else (a, hi)
        a = (lo + hi) / 2
        rolls[t] = sg * a
        rot[t], pos[t], _ = frame(t, sg * a, height(sg * a))
    meta = {**clip.meta, "changes": clip.meta.get("changes", "") +
            f"; softened: the unloading knee +{knee:.0f} deg, the hips rolled down on its side (|roll| mean {np.abs(rolls).mean():.1f},"
            f" max {np.abs(rolls).max():.1f} deg), the chest {chest:.1f} against"}
    return Clip(clip.name, clip.fps, rot, pos, loop=clip.loop, meta=meta)


def shoulders(rig, clip: Clip, drop_l=0.0, drop_r=0.0) -> Clip:
    """Her shoulders let down: each clavicle turned drop deg down about her forward axis (the shoulder's tip lower,
    the neck longer), in the chest's frame; the arms solved after hang from there."""
    from rig import qaxis, qinv, qmul
    sk = rig.sk
    rot = clip.rot.copy()
    g, _ = sk.fk(clip.rot, clip.pos)
    fwd = np.array([0.0, 0.0, 1.0])
    for s, d, sg in (("l", drop_l, -1.0), ("r", drop_r, 1.0)):
        if not d:
            continue
        c = sk.i(f"clavicle_{s}")
        for t in range(clip.frames):
            ax = qrot_(g[t, sk.i("spine_03")], fwd)
            gc = qmul(qaxis(ax, sg * d), g[t, c])
            rot[t, c] = qmul(qinv(g[t, sk.parent[c]]), gc)
    meta = {**clip.meta, "changes": clip.meta.get("changes", "") + f"; shoulders let down {drop_l:.0f}/{drop_r:.0f} deg"}
    return Clip(clip.name, clip.fps, rot, clip.pos, loop=clip.loop, meta=meta)


def qrot_(q, v):
    from rig import qrot
    return qrot(q, np.asarray(v, float))


def look(rig, clip: Clip, deg=28.0, start=0.2, hold=0.35, ease=0.18, pitch=0.0, neck_share=0.4) -> Clip:
    """Her head turned `deg` to her left (negative: right) and back once a loop: from `start` (a share of the loop),
    `ease` to turn, held `hold`, `ease` back; the turn shared by the neck (neck_share) and the head, about up, with a
    little chin `pitch` (deg, + down) at the look."""
    from rig import qaxis, qinv, qmul
    sk = rig.sk
    T = clip.frames
    nk, hd = sk.i("neck_01"), sk.i("Head")
    g, _ = sk.fk(clip.rot, clip.pos)
    t = np.arange(T) / max(T - 1, 1)

    def s(u):
        u = np.clip(u, 0.0, 1.0)
        return u * u * (3 - 2 * u)
    w = s((t - start) / ease) - s((t - start - ease - hold) / ease)
    rot = clip.rot.copy()
    up = np.array([0.0, 1.0, 0.0])
    for f in range(T):
        lx = np.array([1.0, 0.0, 0.0])
        tn = qmul(qaxis(up, deg * w[f] * neck_share), qaxis(lx, pitch * w[f] * neck_share))
        th = qmul(qaxis(up, deg * w[f]), qaxis(lx, pitch * w[f]))
        gn = qmul(tn, g[f, nk])
        gh = qmul(th, g[f, hd])
        rot[f, nk] = qmul(qinv(g[f, sk.parent[nk]]), gn)
        rot[f, hd] = qmul(qinv(gn), gh)
    meta = {**clip.meta, "changes": clip.meta.get("changes", "") + f"; a slow look {abs(deg):.0f} deg to her {'left' if deg > 0 else 'right'} and back"}
    return Clip(clip.name, clip.fps, rot, clip.pos, loop=clip.loop, meta=meta)


def pelvis_hand(rig, base, arms, side, pos, pole, fingers, knuckles=None, blade=None, thumb=None, twist=1.0):
    """`arms` with one hand (side "l"/"r") kept on her pelvis frame by frame (idle._on_hip's way, either hand): `pos`
    the wrist in character space at rest, the hand's way (`knuckles`/`blade`, or `thumb`) in the pelvis's frame at
    rest, the elbow's `pole` in the chest's frame."""
    from gait import arc_of
    from rig import qinv, qmul, qrot
    I = rig.I
    grest, prest = (a[0] for a in rig.sk.rest_globals())
    pel, s3, ua = I["pelvis"], I["spine_03"], I[f"upperarm_{side}"]
    g, p = rig.sk.fk(base.rot, base.pos)
    n = lambda v: tuple(np.asarray(v, float) / np.linalg.norm(v))

    def over(t, f):
        d = dict(arms(t, f))
        dp = qmul(g[f, pel], qinv(grest[pel]))
        ic = qinv(qmul(g[f, s3], qinv(grest[s3])))
        # (`pos` may be a function of the loop time, t -> the wrist at rest: a hand kept on a waist that bends under it.)
        W = p[f, pel] + qrot(dp, np.array(pos(t) if callable(pos) else pos) - prest[pel])
        h = {"arc": arc_of(qrot(ic, W - p[f, ua])), "pole": pole, "frame": "chest", "twist": twist}
        for k, v in (("knuckles", knuckles), ("blade", blade), ("thumb", thumb)):
            if v is not None:
                h[k] = tuple(qrot(ic, qrot(dp, np.array(n(v)))))
        d[f"hand_{side}"] = h
        d[f"fingers_{side}"] = fingers(t) if callable(fingers) else fingers
        return d
    return over


def _hand(fingers, palm):
    """(knuckles, blade) for a LEFT hand from the way its fingers point and its palm faces (the palm made square to
    the fingers): the hand's +Y the fingers, +X the palm, +Z (the thumb side) X x Y."""
    k = np.asarray(fingers, float)
    k = k / np.linalg.norm(k)
    p = np.asarray(palm, float)
    p = p - k * float(p @ k)
    p = p / np.linalg.norm(p)
    return tuple(k), tuple(np.cross(p, k))


def _hand_r(fingers, palm):
    """_hand for a RIGHT hand (its fingers' and palm's ways in her space): the left's, mirrored."""
    m = np.array([-1.0, 1.0, 1.0])
    k, b = _hand(tuple(np.asarray(fingers, float) * m), tuple(np.asarray(palm, float) * m))
    return tuple(np.asarray(k) * m), tuple(np.asarray(b) * m)


def _pole(back):
    """An elbow pole out to her left side, swung `back` degrees behind it (the chest's frame)."""
    a = math.radians(back)
    return (math.cos(a), 0.0, -math.sin(a))


def _relaxed(curl):
    from keyed import FINGER_PRESETS
    return dict(FINGER_PRESETS["relaxed"], curl=curl)


# Her stances (round 1, the max judge: R_A, A_A, S_B pass; the staff hold rides A_A's): the take, its window (seconds),
# contra()'s and look()'s arguments.
STANCES = {
    # Heavy and swaggering: the Proud take (a broad chest leaned back, chin level), the weight sunk into her left hip.
    "reaver_town": ("Proud", None, dict(side="l", shift=0.07, roll=7, yaw=5, width=0.32, knee=5, settle=0.3, counter=0.5,
                                        free_turn=15, free_fwd=0.06, free_knee=16), None),
    # Poised: the GracefulArms take, the weight on her back (right) leg, the left foot 8 cm ahead and turned out.
    # (Animation 51, the judge: "from the front" the weight must show: the free knee 1.3 cm below the standing one and
    # turned in 12 deg (turn_in), the free foot out and ahead of a standing foot set back; the hips 10 deg, the chest 3
    # against. The knee turned in no more than 15 deg against its foot's turn out: no twist bones at her ankle.)
    "arcanist_town": ("GracefulArms", (3, 11), dict(side="r", shift=0.05, roll=12, yaw=4, width=0.20, knee=5, settle=0.1,
                                                    counter=0.3, free_out=0.06, free_fwd=0.005, stand_back=0.03, free_turn=15,
                                                    free_knee_in=-0.009, turn_in=True), None),
    # Loose but watchful: the HandsInPockets take, the weight on her left leg, a slow look to her right and back.
    # (Animation 51: the free foot 8 cm ahead (a standing foot set back) and turned out 12, its knee 1.2 cm lower (the
    # hips 11 deg), the kneecap over the toes within 15 deg; the shoulders 2.5 deg against the hips.)
    "stalker_town": ("HandsInPockets", (0, 8), dict(side="l", shift=0.05, roll=11, yaw=4, width=0.24, knee=5, settle=0.1,
                                                    counter=0.25, free_turn=0, free_fwd=0.07, stand_back=0.05, free_knee=18,
                                                    free_knee_in=0.0, turn_in=True), dict(deg=-28.0, start=0.2, hold=0.3, ease=0.17)),
    # The warden's WiggleHips (the owner loves its sway: its path and timing kept exactly, her hips' roll with it) set
    # on her right leg (animation 51, the judge: "never passes level"): her left foot set 6 cm further out, so the
    # sway rides 3 cm further over her right foot than the take's (from about level over her feet to fully on her right
    # hip), its far end no further past her right ankle than round 2's; the hips 4.5 deg more on that side and never
    # under 3.5; her left foot 10 cm ahead (the right set back) and turned out 12 more, its knee soft and turned in 8
    # (the kneecap over the toes within 15 deg).
    "warden_town": ("WiggleHips", None, dict(side="r", shift=0.0, roll=4.5, roll_floor=3.5, yaw=0.0, counter=0.5, settle=0.0,
                                             knee=5, feet_shift=-0.005, free_fwd=0.0, stand_back=0.08, free_turn=12,
                                             free_knee=14, free_knee_in=-0.007, turn_in=True), None),
}


# Animation 50, round 2 (the max judge: "the stance underneath doesn't yet": square, both knees locked). A swaying
# stand softened (soften), and the shoulders let down where the take holds them above her walk_tired's (shoulders:
# (left, right) deg).
# (Animation 51: the warden's stand now made by contra (STANCES), its sway kept: soften() stays for a stand that
# sways across its middle. The judge: the warden's left clavicle down too, the stalker's both a further 3.5.)
SWAYS = {}
SHOULDERS = {"arcanist_town": (5.0, 5.0), "stalker_town": (7.0, 8.5), "warden_town": (3.5, 4.0)}


def town_base(rig, calling):
    """A calling's town standing: its take looped, stood with her weight on one hip (contra), the head's look."""
    from clips.mocap import idle_loop
    take, window, ck, lk = STANCES[calling]
    b = contra(rig, idle_loop(f"idle_{calling}_base", rig, take, seconds=(5.0, 8.0), window=window), **ck)
    return look(rig, b, **lk) if lk else b


# Round 2 (the max judge: every hand on the hip read "a stomach-ache", on the front of her lower belly). The hands now
# rest on the SIDE of her pelvis, over the hip bone at the side seam (pelvis_hand: on it frame by frame). Fitted on her
# body and outfit (scratch anim/town2 opt.py: 0 mm into her, the resting part 0-3 mm off).
# The reaver: the heel of her left hand on the side of her hip at the belt (contact 17 cm out of her middle, 1 cm ahead
# of the side seam, 1.10 m up at rest), the palm in, the fingers down and forward over the hip, the wrist bent back 40,
# the elbow out 11 cm and well behind her side (the forearm along her flank), open to 83 (95 would put the hand on her
# thigh: the hip bone sits 30 cm under her shoulder and her arm is 52 cm).
# (Round 2 of animation 50, the judge: the hand floated 15 mm off her outfit, "from 30 deg it floats off the hip":
# the heel planted, 13 mm in, the wrist bent back 6 less, the elbow drawn back 12.)
_RV_K, _RV_B = _hand((0.01, -0.69, 0.724), (-0.95, -0.277, 0.0))
REAVER_HIP_L = dict(pos=(0.2175, 1.095, 0.0), pole=_pole(57.0), knuckles=_RV_K, blade=_RV_B, curl=0.06)
# The arcanist: her left wrist resting on the side of her hip bone at the seam (contact 17 cm out, 1.08 m up at rest),
# the hand hanging soft beside it (the fingers down, the palm back: the back of the hand to the camera, the thumb side
# of the wrist on her hip), the elbow out 20 cm, open to 86. (The palm turned out, the wrist's very back on her hip,
# was fitted and dropped: the forearm wrung 156 deg from rest, audit's limit 120, the elbow's flesh kept 38 %.)
# (Was: knuckles (0.1, -0.97, -0.1), the palm 75 deg back, the wrist at (0.203, 1.20, 0.015), pole 30, curl 0.10.)
# Round 2 of animation 50 (the judge: "a balled fist with a high teapot elbow"): the hand open, the fingers together
# in a loose half-curl, the back of the wrist on her hip (2 mm off her outfit) and the hand bent forward off it so the
# fingers trail back and down, resting on the side of her hip (2 mm off); the elbow lowered 13 deg (out 37). Fitted
# on frame 0 (scratch anim50/tools/fit_arc.py). The wrist takes 53 deg of that bend: at 35-45 the fingers go 3-16 mm
# into her hip, and the elbow drawn back instead flips the arm (the elbow behind her, the fingers pointing ahead).
_AR_K, _AR_B = _hand((0.231, -0.811, -0.537), (math.cos(math.radians(-25.0)), 0.0, math.sin(math.radians(-25.0))))
ARC_WRIST_L = dict(pos=(0.1736, 1.17, 0.015), pole=_pole(8.0), knuckles=_AR_K, blade=_AR_B, curl=0.20)
# (Animation 51, round 3b, tried and dropped: the wrist 3.7 cm back and 2 cm down, the hand rolled palm-down so the
# fingers trail down and back, took the elbow back to the shoulder line (out 6 cm, 32 deg behind) but wrung the
# forearm 155 deg from rest (audit's limit 120) every frame. Between that and this the swivel has no rest.)


def on_hip(spec, free):
    """Arms for a town stand: `free` (idle.free_arms) with the left hand (or spec["side"]'s) as `spec` keeps it on her
    pelvis (a right hand's spec in its own terms: _hand_r). Returns
    make(rig, base) -> over(t, f) (the hand rides the base's pelvis)."""
    def make(rig, base):
        return pelvis_hand(rig, base, free, spec.get("side", "l"), spec["pos"], spec["pole"],
                           spec.get("fingers") or _relaxed(spec["curl"]), knuckles=spec["knuckles"], blade=spec["blade"],
                           twist=spec.get("twist", 0.5))
    make.needs_base = True
    return make


# A hanging arm (animation 50; the owner, 26 Oct, of her free arms held out from her sides: "nobody stands like that").
# The arms had been aimed at a fixed point in her CHEST's frame, so the hips swaying or cocked under them had to be
# cleared by holding the hands out 27-32 cm beyond the hip (17-25 deg out, the elbows 26-39). A hanging hand rides the
# HIP instead: its place beside the outer thigh (out from the hip joint and ahead of it, in the pelvis's frame, swung
# a little fore and aft) is followed frame by frame across the floor, and the wrist hangs at a set reach from the
# shoulder straight above that place, so the elbow stays as soft as asked whatever the hips and the breath do. Any
# stand can use it (hang_arms), one hand or both.
HANG = dict(out=0.21, fwd=0.0, elbow=18.0, elbow_life=1.5, pole=(0.0, -0.2, -1.0), thumb=(-0.15, -0.1, 1.0),
            swing=0.010, swing_phase=0.0, fingers="relaxed")


def loop_wave(mean, *harmonics):
    """A smooth looping value of the loop time t (0..1): mean + sum of a_k cos(2 pi k t) + b_k sin(2 pi k t) for
    harmonics ((a_1, b_1), (a_2, b_2), ...). (A hanging hand's `out` that follows her skirt as the hip sways.)"""
    def wave(t):
        return mean + sum(a * math.cos(2 * math.pi * k * t) + b * math.sin(2 * math.pi * k * t)
                          for k, (a, b) in enumerate(harmonics, 1))
    return wave


# A hanging hand's fingers together in a loose half-curl (20-30 deg a joint; "relaxed" is about 12).
HALF_CURL = _relaxed(0.2)


def graded(knuckle=(15.0, 30.0), middle=(20.0, 45.0), tip=(10.0, 20.0), spreads=None):
    """A soft hand with its curl graded from the forefinger to the little finger (each joint's bend, deg, index ->
    little, evenly between), the fingers together (the relaxed preset's fan closing, its judged spreads) and the relaxed thumb laid alongside the
    forefinger. (Animation 51, the judge: HALF_CURL's cascade put the little finger's knuckle at 68 and read as a
    knuckle clump or a claw.)"""
    from keyed import FINGER_PRESETS, finger_curl
    r = FINGER_PRESETS["relaxed"]
    bends = {f: [a + (b - a) * i / 3 for a, b in (knuckle, middle, tip)] for i, f in enumerate(("index", "middle", "ring", "pinky"))}
    bends["thumb"] = finger_curl("relaxed")["thumb"]
    return dict(r, bends=bends, spreads=dict(spreads if spreads is not None else r["spreads"]))


# (Animation 51, the judge of the arcanist's on-hip hand: "a knuckle clump, a fist": its curl graded and open.)
ARC_WRIST_L["fingers"] = graded((15.0, 20.0), (20.0, 30.0), (8.0, 12.0))
# (Animation 51, the judge: the stalker's right thumb hooked over her belt at the front of the right hip, the elbow
# ~80, that hand 12-15 cm above the left; the other fingers together, lying on the hip.) The wrist 1.145 m up at rest
# (15 cm above the hanging left), the fingers down and a little in and ahead along the front of her hip and thigh, the
# palm to her; the thumb's pad on the belt 1.4 mm off the ranger outfit, the fingers 2 mm off; the elbow open to 81.
# (Fitted on frame 0, scratch anim51/s3b/fit_stk.py.)
_ST_K, _ST_B = _hand_r((0.1891, -0.9456, 0.2648), (0.6312, -0.0895, -0.7705))
STALKER_THUMB_R = dict(side="r", pos=(-0.1499, 1.145, 0.1096), pole=(-math.cos(math.radians(30.0)), 0.0, -math.sin(math.radians(30.0))),
                       knuckles=_ST_K, blade=_ST_B, curl=0.2, fingers=graded((5.0, 12.0), (8.0, 18.0), (4.0, 10.0)))


def _mirror(v, side):
    """A left hand's vector (her character's space) for `side`: x turned over for the right."""
    return v if side == "l" else (-v[0], v[1], v[2])


def hang_target(rig, g, p, f, side, spec, t):
    """The hanging hand's key at frame f (globals g, positions p of the base) and loop time t: {"arc", "pole",
    "frame": "chest", "thumb", "twist"} (spec: HANG's keys, given for a LEFT hand; the right's mirrored)."""
    from gait import arc_of
    from rig import qinv, qmul, qrot
    I = rig.I
    grest, prest = (a[0] for a in rig.sk.rest_globals())
    pel, s3 = I["pelvis"], I["spine_03"]
    ua, la, ha = I[f"upperarm_{side}"], I[f"lowerarm_{side}"], I[f"hand_{side}"]
    a = float(np.linalg.norm(prest[la] - prest[ua]))
    b = float(np.linalg.norm(prest[ha] - prest[la]))
    e = math.radians(spec["elbow"] + spec["elbow_life"] * math.sin(2 * math.pi * t + spec["swing_phase"]))
    r = math.sqrt(a * a + b * b + 2 * a * b * math.cos(e))
    dp = qmul(g[f, pel], qinv(grest[pel]))
    ic = qinv(qmul(g[f, s3], qinv(grest[s3])))
    sgn = 1.0 if side == "l" else -1.0
    fwd = spec["fwd"] + sgn * spec["swing"] * math.sin(2 * math.pi * t * 2 + spec["swing_phase"])
    # Out from her hip joint and ahead of it, in the pelvis's frame (her +X her left, +Z ahead).
    # (`out` may be a function of the loop time, t -> m: a hand kept on a skirt whose hip sways out and back under it.)
    out = spec["out"](t) if callable(spec["out"]) else spec["out"]
    D = p[f, I[f"thigh_{side}"]] + qrot(dp, np.array((sgn * out, 0.0, fwd)))
    sh = p[f, ua]
    h = D - sh
    h[1] = 0.0
    hh = float(np.linalg.norm(h))
    if hh > 0.95 * r:
        h *= 0.95 * r / hh
        hh = 0.95 * r
    W = sh + h + np.array((0.0, -math.sqrt(r * r - hh * hh), 0.0))
    key = {"arc": arc_of(qrot(ic, W - sh)), "pole": _mirror(spec["pole"], side), "frame": "chest",
           "thumb": tuple(qrot(ic, qrot(dp, np.array(_mirror(spec["thumb"], side), float) / np.linalg.norm(spec["thumb"])))),
           "twist": 1.0}
    if spec.get("flex"):
        # The fingers laid in toward her thigh at the wrist (deg; a function of t, or a number).
        key["flex"] = spec["flex"](t) if callable(spec["flex"]) else spec["flex"]
    return key


def hang_arms(arms=None, **hands):
    """Arms for a stand with hanging hands: `arms` (over(t, f), or a make(rig, base) as on_hip returns, or None) with
    each hand named (l=..., r=...: HANG's keys to change, for a LEFT hand; the right's mirrored; {} for HANG's own)
    hung from her shoulder beside her thigh (hang_target). Returns make(rig, base) -> over(t, f)."""
    specs = {s: dict(HANG, **(v or {})) for s, v in hands.items()}

    def make(rig, base):
        under = arms(rig, base) if getattr(arms, "needs_base", False) else arms
        g, p = rig.sk.fk(base.rot, base.pos)

        def over(t, f):
            d = dict(under(t, f)) if under else {}
            for s, sp in specs.items():
                d[f"hand_{s}"] = hang_target(rig, g, p, f, s, sp, t)
                d[f"fingers_{s}"] = sp["fingers"]
            return d
        return over
    make.needs_base = True
    return make
