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
           free_out=0.0, free_fwd=0.0, free_turn=0.0, free_knee_in=0.0, chest_yaw=0.0, width=None) -> Clip:
    """`clip` stood with her weight on one leg (contrapposto). side: the standing leg ("l"/"r"); shift: her pelvis
    carried that far toward it (m); roll: the hips tilted, the standing hip up (deg); yaw: the free hip brought forward
    (deg); counter: the shoulders tilted back against the hips (a share of roll, through the spine); knee: the
    standing knee's mean bend (deg; the free one bends as it must to reach its foot); settle: the shift and tilt
    swelling and easing once over the loop (a share), from `phase`. The free foot: moved out (m, away from the
    standing one) and forward (m), turned out (deg), its knee drawn in toward the other (m on the knee's aim).
    chest_yaw: the chest's turn left at the top of the spine (deg). width: her ankles set that far apart (m) first.
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
    if free_turn:
        tq = qaxis(up, -sgn * free_turn)     # its toes turned away from the standing leg
        foot_g[free] = qmul(np.broadcast_to(tq, foot_g[free].shape), foot_g[free])
    a = _env(T, settle, phase)
    shiftv = (left * sgn)[None, :] * (shift * a)[:, None]
    # The pelvis: the standing hip up (a turn about her forward axis), the free hip forward (about up).
    Tp = np.array([qmul(qaxis(up, sgn * yaw * a[f]), qaxis(fwd, sgn * roll * a[f])) for f in range(T)])
    gp_new = qmul(Tp, g[:, pel])
    rot[:, pel] = qmul(qinv(g[:, root]), gp_new)
    # The spine takes the tilt and the hips' turn back, a third a joint, to `counter` the other way at the chest.
    par = gp_new
    for k, j in enumerate(spine, 1):
        r_k = sgn * roll * a * (1 - (1 + counter) * k / 3)
        y_k = sgn * yaw * a * (1 - k / 3) + chest_yaw * k / 3
        Tk = np.array([qmul(qaxis(up, y_k[f]), qaxis(fwd, r_k[f])) for f in range(T)])
        gj = qmul(Tk, g[:, j])
        rot[:, j] = qmul(qinv(par), gj)
        par = gj
    # The neck back to its own carriage (the head as the take held it).
    rot[:, neck] = qmul(qinv(par), g[:, neck])

    knee_in = {free: free_knee_in, side: 0.0}

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
    r, q, b = legs((lo + hi) / 2)
    meta = {**clip.meta, "changes": clip.meta.get("changes", "") +
            f"; her weight on the {'left' if side == 'l' else 'right'} leg (hips {roll:.0f} deg, carried {shift * 100:.0f} cm,"
            f" knees {b['l']:.0f}/{b['r']:.0f} deg, a settle of {settle:.0%})"}
    return Clip(clip.name, clip.fps, r, q, loop=clip.loop, meta=meta)


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
        W = p[f, pel] + qrot(dp, np.array(pos) - prest[pel])
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
                                        free_turn=10), None),
    # Poised: the GracefulArms take, the weight on her back (right) leg, the left foot 8 cm ahead and turned out.
    "arcanist_town": ("GracefulArms", (3, 11), dict(side="r", shift=0.05, roll=5, yaw=4, width=0.20, knee=5, settle=0.2,
                                                    counter=0.4, free_fwd=0.08, free_turn=20), None),
    # Loose but watchful: the HandsInPockets take, the weight on her left leg, a slow look to her right and back.
    "stalker_town": ("HandsInPockets", (0, 8), dict(side="l", shift=0.05, roll=5, yaw=4, width=0.24, knee=9, settle=0.4,
                                                    counter=0.5, free_turn=10), dict(deg=-28.0, start=0.2, hold=0.3, ease=0.17)),
}


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
_RV_K, _RV_B = _hand((0.105, -0.654, 0.657), (-0.95, -0.277, 0.0))
REAVER_HIP_L = dict(pos=(0.2155, 1.095, 0.0), pole=_pole(53.0), knuckles=_RV_K, blade=_RV_B, curl=0.06)
# The arcanist: her left wrist resting on the side of her hip bone at the seam (contact 17 cm out, 1.08 m up at rest),
# the hand hanging soft beside it (the fingers down, the palm back: the back of the hand to the camera, the thumb side
# of the wrist on her hip), the elbow out 20 cm, open to 86. (The palm turned out, the wrist's very back on her hip,
# was fitted and dropped: the forearm wrung 156 deg from rest, audit's limit 120, the elbow's flesh kept 38 %.)
_AR_K, _AR_B = _hand((0.1, -0.97, -0.1), (math.cos(math.radians(-75.0)), 0.0, math.sin(math.radians(-75.0))))
ARC_WRIST_L = dict(pos=(0.203, 1.20, 0.015), pole=_pole(30.0), knuckles=_AR_K, blade=_AR_B, curl=0.10)


def on_hip(spec, free):
    """Arms for a town stand: `free` (idle.free_arms) with the left hand as `spec` keeps it on her pelvis. Returns
    make(rig, base) -> over(t, f) (the hand rides the base's pelvis)."""
    def make(rig, base):
        return pelvis_hand(rig, base, free, "l", spec["pos"], spec["pole"], _relaxed(spec["curl"]),
                           knuckles=spec["knuckles"], blade=spec["blade"], twist=0.5)
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
    D = p[f, I[f"thigh_{side}"]] + qrot(dp, np.array((sgn * spec["out"], 0.0, fwd)))
    sh = p[f, ua]
    h = D - sh
    h[1] = 0.0
    hh = float(np.linalg.norm(h))
    if hh > 0.95 * r:
        h *= 0.95 * r / hh
        hh = 0.95 * r
    W = sh + h + np.array((0.0, -math.sqrt(r * r - hh * hh), 0.0))
    return {"arc": arc_of(qrot(ic, W - sh)), "pole": _mirror(spec["pole"], side), "frame": "chest",
            "thumb": tuple(qrot(ic, qrot(dp, np.array(_mirror(spec["thumb"], side), float) / np.linalg.norm(spec["thumb"])))),
            "twist": 1.0}


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
