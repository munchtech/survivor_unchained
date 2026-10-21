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
