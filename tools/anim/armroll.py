"""Her arms re-solved where a clip wrings them: a pass at pack time (build.pack), after clavhold.

The owner (24 Oct, the raised arm at reaver_show and the Warden cast): "still twisting like a towel, even the
wrist angle is bizarre". The twist chain (helpers SPEC "twist_chain") spreads the upper arm's roll evenly down
the humerus, but a roll of 75-110 deg still reads as a wrung towel under linear skinning, and her keyed IK left
the wrist bent 45-57 deg to the side (a real wrist: under ~20 deg of deviation, ~45 deg of extension).

The fix is the pose, not the skin; per frame and side, three steps, each eased over the frames (a Viterbi path on
a grid, loops closed on themselves, then a light Gaussian):
1. A raised arm's elbow swivels about its shoulder-to-wrist line (the wrist and the hand's global turn kept): only
   from arm angle 70-90 up, at most 45 deg, near the clip's own elbow, the elbow kept clear of her head, trunk and
   the floor; kept for a side only if it cuts its worst roll by GAIN_MIN deg (or that roll is past ROLL_BIG). At
   the owner's frames (a goalpost arm, the elbow out) it buys little: the hinge fixes that roll.
2. A near-straight arm's roll is traded into the forearm (rho; the forearm and hand don't move; a bent elbow pays
   as the forearm leaving its hinge), never past the forearm's own range.
3. The wrist (the main fix): the hand turned the least way into a comfortable bend (`_comfort`), read in the hand's
   own frame after the forearm's pronation (keyed.Rig._wrist_split's convention). A raised fist sits square on its
   forearm (deviation <= W_DEV, extension <= W_EXT_HIGH; the owner's targets, 24 Oct), a hanging hand keeps a
   relaxed set (W_DEV_LOW, W_EXT). A flexion/extension fix turns the hand about its +Z, the shaft (a round haft
   reads the same); the turn is capped at TURN_CAP. Not where both hands hold one weapon (the grip kept), nor a
   planted hand (the floor, a thigh, her trunk, her face).
The hand's turn carries the weapon it holds. Body 6's chain bones get twist_01's track (chain_tracks).

Off with ARM_ROLL=0. Report: `python tools/anim/armroll.py <clip.json> ...` (max roll, dev, ext, flex, pron
before -> after per side; the swivel, rho, the hand's turn and its shaft's tilt).
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path

import numpy as np

from rig import Skeleton, qaxis, qcontinuous, qinv, qmul, qnorm, qrot

# The swivel (deg): the upper arm's roll from rest past ROLL_OK costs (per ROLL_SCALE); a swivel costs (per STAY)
# so the clip's own elbow is kept unless the roll pays for it; capped at SPAN. A side's swivel is kept only where it
# buys a real cut: at least GAIN_MIN deg off its worst roll, or the clip's roll past ROLL_BIG.
ROLL_OK, ROLL_SCALE = float(os.environ.get("ARM_ROLL_OK", "35")), 15.0
STAY = 22.0
STEP = 3
SPAN = 45
GAIN_MIN, ROLL_BIG = 20.0, 120.0
JERK = 3.0           # deg per frame of swivel change that costs one unit (Viterbi's smoothness)
SIGMA = 1.5          # frames: the chosen path's final smoothing
# The swivel's wrist terms (so it never makes the hand's turn worse than it need be).
FLEX_OK, FLEX_SCALE = 45.0, 10.0
DEV_OK, DEV_SCALE = 20.0, 8.0
PRO_OK, PRO_SCALE = 80.0, 10.0
# The wrist's comfortable range (deg), the hand turned into it: deviation either way, extension (back of the hand
# toward the forearm), flexion (toward the palm), the forearm's pronation/supination.
# Deviation: the owner's targets (24 Oct) put a raised fist square on its forearm (0-10); a hanging hand keeps a
# relaxed hand's natural sideways set (up to W_DEV_LOW): W_DEV from arm angle W_DEV_A[1] up, W_DEV_LOW under W_DEV_A[0].
W_DEV = float(os.environ.get("ARM_WRIST_DEV", "8"))
W_DEV_LOW = float(os.environ.get("ARM_WRIST_DEV_LOW", "20"))
W_DEV_A = (45.0, 75.0)
W_EXT = float(os.environ.get("ARM_WRIST_EXT", "45"))
W_EXT_HIGH = float(os.environ.get("ARM_WRIST_EXT_HIGH", "25"))   # a raised fist (the same ramp as deviation)
W_FLEX = float(os.environ.get("ARM_WRIST_FLEX", "60"))
W_PRO = float(os.environ.get("ARM_WRIST_PRO", "80"))
TURN_CAP = float(os.environ.get("ARM_TURN_CAP", "40"))     # the hand's turn, at most (deg)
TURN_SIGMA = 1.0                                          # frames: the turn's easing
# Two hands on one weapon (the wrists this close, m): the hand is not turned (the grip kept; the swivel only).
TWO_HAND = (0.35, 0.45)
# A planted hand bears weight, its wrist's extension natural (a palm on the floor, a hand braced on a thigh): not
# turned. Wrist height over the floor (m), wrist to either thigh's line (m): planted under the first, free past the second.
PLANT_FLOOR = (0.25, 0.40)
PLANT_THIGH = (0.12, 0.20)
PLANT_TRUNK = (0.18, 0.26)     # a hand on her hip or chest (wrist to the pelvis-neck_01 line)
PLANT_HEAD = (0.22, 0.30)      # a hand at her face (a flask at her lips): wrist to her head's centre
# The swivel is for a raised arm (the towel): allowed in full from arm angle SWIVEL_A[1], none under SWIVEL_A[0];
# the elbow never goes nearer the floor than ELBOW_FLOOR (m) or the clip's own.
SWIVEL_A = (70.0, 90.0)
ELBOW_FLOOR = 0.10
# The roll traded into the forearm (from arm_roll_fix, 24 Oct): the upper arm turned about its own line by rho, the
# forearm's global kept, so the roll the twist chain reads moves into the forearm's pronation. Free on a straight
# elbow; a bent one pays for it as the forearm leaving the elbow's hinge (HINGE_OK deg, then steeply).
RHO_SPAN, RHO_STEP, RHO_STAY = 60, 5, 40.0
HINGE_OK, HINGE_SCALE = 2.0, 1.0
HINGE = {"l": (0.985, 0.0, -0.17), "r": (0.985, 0.0, 0.16)}   # the elbow's axis in the upper arm (keyed.Rig's bend)
# Clearance (m): the elbow from her head's centre and from her trunk's line (pelvis to neck_01), the forearm
# (elbow to wrist) from her head's centre. Under it the cost climbs steeply (per CLEAR_SCALE m), unless the
# clip's own arm was already that close (never worse than the clip).
ELBOW_HEAD, ELBOW_TRUNK, FORE_HEAD, CLEAR_SCALE = 0.17, 0.15, 0.12, 0.015
HEAD_UP = 0.09       # her head's centre above the Head bone (m)
CHAIN = ("upperarm_twist_02", "upperarm_twist_03", "upperarm_twist_04")


def on():
    return os.environ.get("ARM_ROLL", "1") != "0"


def twist_y(d):
    """Twist angle (deg) of local rotation(s) d [..., 4] about the bone's own +Y."""
    return np.degrees(2 * np.arctan2(d[..., 1], d[..., 3]))


def _wrap(a):
    return (a + 180.0) % 360.0 - 180.0


def _hinge(x, ok, scale):
    return (np.maximum(0.0, np.abs(x) - ok) / scale) ** 2


def _twist_swing(dh):
    """dh [..., 4] = tw * sw: tw about the bone's own +Y (the forearm's pronation, applied first, nearer the
    elbow), sw a swing about an axis in the hand's own X-Z plane (the wrist's bend, in the hand's frame)."""
    tw = np.zeros_like(dh)
    tw[..., 1], tw[..., 3] = dh[..., 1], dh[..., 3]
    tw = tw / np.maximum(np.linalg.norm(tw, axis=-1, keepdims=True), 1e-12)
    sw = qmul(qinv(tw), dh)
    sw = np.where(sw[..., 3:4] < 0, -sw, sw)
    return tw, sw


def _rotvec(q):
    q = np.where(q[..., 3:4] < 0, -q, q)
    v = q[..., :3]
    n = np.linalg.norm(v, axis=-1)
    ang = 2 * np.arctan2(n, q[..., 3])
    return v / np.maximum(n, 1e-12)[..., None] * ang[..., None]


def _qexp(v):
    a = np.linalg.norm(v, axis=-1)
    ax = v / np.maximum(a, 1e-12)[..., None]
    return np.concatenate([ax * np.sin(a / 2)[..., None], np.cos(a / 2)[..., None]], axis=-1)


def _hand_dh(sk: Skeleton, lo_rot, h_rot, s):
    """The hand's turn from its rest, in its rest frame, with the forearm's own roll handed down to it (as the
    game does, helpers SPEC "unroll")."""
    I = sk.index
    l, h = I[f"lowerarm_{s}"], I[f"hand_{s}"]
    rl, rh = sk.rest_rot[l], sk.rest_rot[h]
    dl = qmul(qinv(rl), lo_rot)
    t = np.zeros_like(dl)
    t[..., 1], t[..., 3] = dl[..., 1], dl[..., 3]
    t = t / np.maximum(np.linalg.norm(t, axis=-1, keepdims=True), 1e-12)
    A = qmul(qinv(rl), qmul(t, rl))
    return qmul(qinv(rh), qmul(A, h_rot))


def wrist(sk: Skeleton, lo_rot, h_rot, s):
    """Forearm pronation, wrist flexion (+ toward the palm, - extension) and deviation (+ toward the thumb), deg,
    from the forearm's and hand's local rotations [..., 4]. The pronation is the hand's twist about its own +Y
    (the forearm's roll handed down); the bend is read about the hand's own axes after it (keyed.Rig._wrist_split's
    convention: +Z the thumb side, +X across the back of her right hand, the palm of her left)."""
    dh = _hand_dh(sk, lo_rot, h_rot, s)
    tw, sw = _twist_swing(dh)
    pro = twist_y(tw)
    v = np.degrees(_rotvec(sw))
    sgn = 1.0 if s == "r" else -1.0
    return _wrap(pro), sgn * v[..., 2], v[..., 0]


def _comfort(sk: Skeleton, lo_rot, h_rot, s, dev_lim, ext_lim):
    """The least turn r (in the hand's own frame: h_rot * r) that brings its bend into the comfortable range.
    A flexion/extension fix is a turn about the hand's +Z (the shaft: a round shaft reads the same)."""
    dh = _hand_dh(sk, lo_rot, h_rot, s)
    tw, sw = _twist_swing(dh)
    pro = np.radians(_wrap(twist_y(tw)))
    lim = math.radians(W_PRO)
    pro2 = np.clip(pro, -lim, lim)
    tw2 = np.zeros_like(tw)
    tw2[..., 1], tw2[..., 3] = np.sin(pro2 / 2), np.cos(pro2 / 2)
    v = _rotvec(sw)
    sgn = 1.0 if s == "r" else -1.0
    v2 = v.copy()
    v2[..., 1] = 0.0
    dl = np.radians(dev_lim)
    v2[..., 0] = np.clip(v[..., 0], -dl, dl)
    fl = np.clip(sgn * v[..., 2], -np.radians(ext_lim), math.radians(W_FLEX))
    v2[..., 2] = sgn * fl
    dh2 = qmul(tw2, _qexp(v2))
    return qnorm(qmul(qinv(dh), dh2))


def _seg_dist(p, a, b):
    ab = b - a
    t = np.clip(np.einsum("...i,...i", p - a, ab) / np.maximum(np.einsum("...i,...i", ab, ab), 1e-12), 0, 1)
    return np.linalg.norm(p - (a + t[..., None] * ab), axis=-1)


def measure(sk: Skeleton, rot, pos=None):
    """Per side, per frame: roll, pro, flex, dev, A (deg) of a clip's local rotations [T, J, 4]."""
    I = sk.index
    grot, gpos = sk.fk(rot, pos)
    down = gpos[:, I["pelvis"]] - gpos[:, I["neck_01"]]
    down /= np.linalg.norm(down, axis=-1, keepdims=True)
    out = {}
    for s in "lr":
        u, lo, h = I[f"upperarm_{s}"], I[f"lowerarm_{s}"], I[f"hand_{s}"]
        roll = _wrap(twist_y(qmul(qinv(sk.rest_rot[u]), rot[:, u])))
        pro, fl, dv = wrist(sk, rot[:, lo], rot[:, h], s)
        arm = gpos[:, lo] - gpos[:, u]
        A = np.degrees(np.arccos(np.clip(np.einsum("ti,ti->t", arm / np.linalg.norm(arm, axis=-1, keepdims=True), down), -1, 1)))
        out[s] = dict(roll=roll, pro=pro, flex=fl, dev=dv, A=A)
    return out


def _smooth(x, sigma, loop):
    """Gaussian along axis 0 (a loop's last frame is its first again)."""
    x = np.asarray(x, float)
    if sigma < 0.3 or len(x) < 3:
        return x.copy()
    r = max(1, int(3 * sigma))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    if loop:
        body = x[:-1]
        idx = np.arange(-r, len(body) + r) % len(body)
    else:
        body = x
        idx = np.clip(np.arange(-r, len(x) + r), 0, len(x) - 1)
    xs = body[idx]
    n = len(xs) - 2 * r
    out = sum(k[i] * xs[i:i + n] for i in range(2 * r + 1))
    if loop:
        out = np.concatenate([out, out[:1]])
    return out


def _viterbi(cost, grid, loop):
    """cost [T, K]: the path of grid indices minimising sum cost + ((d swivel)/JERK)^2. A loop's path is found on
    three laps and the middle one kept, so it closes on itself."""
    T, K = cost.shape
    if loop and T > 2:
        body = cost[:-1]
        n = len(body)
        p = _viterbi(np.concatenate([body, body, body]), grid, False)
        mid = p[n:2 * n]
        return np.append(mid, mid[0])
    tr = ((grid[:, None] - grid[None, :]) / JERK) ** 2
    acc = cost[0].copy()
    back = np.zeros((T, K), int)
    for t in range(1, T):
        m = acc[:, None] + tr
        back[t] = np.argmin(m, axis=0)
        acc = m[back[t], np.arange(K)] + cost[t]
    path = np.zeros(T, int)
    path[-1] = int(np.argmin(acc))
    for t in range(T - 1, 0, -1):
        path[t - 1] = back[t, path[t]]
    return path


def _stats(m, frame=None):
    out = {}
    for s in "lr":
        d = m[s]
        sl = slice(None) if frame is None else slice(frame, frame + 1)
        fl = d["flex"][sl]
        out[s] = dict(roll=float(np.max(np.abs(d["roll"][sl]))), dev=float(np.max(np.abs(d["dev"][sl]))),
                      ext=float(max(0.0, -np.min(fl))), flex=float(max(0.0, np.max(fl))),
                      pro=float(np.max(np.abs(d["pro"][sl]))), A=float(np.max(d["A"][sl])))
    return out


def solve_rot(sk: Skeleton, rot, pos, fps, loop, report=None):
    """rot [T, J, 4] local rotations (a changed copy returned), pos [T, J, 3]. report (a dict) gets, per side:
    before/after maxima, the swivel's max, the hand's turn max and its shaft's tilt max (deg)."""
    I = sk.index
    if "upperarm_l" not in I or "Head" not in I:
        return rot
    rot0 = rot
    rot = rot.copy()
    T = rot.shape[0]
    grot, gpos = sk.fk(rot, pos)
    head = gpos[:, I["Head"]] + qrot(grot[:, I["Head"]], np.broadcast_to([0, HEAD_UP, 0], (T, 3)))
    pel, nk = gpos[:, I["pelvis"]], gpos[:, I["neck_01"]]
    down = (pel - nk) / np.linalg.norm(pel - nk, axis=-1, keepdims=True)
    grid = np.arange(-SPAN, SPAN + 1, STEP, dtype=float)
    j0 = int(np.argmin(np.abs(grid)))
    swiv = {}
    # ---- 1. the swivel about shoulder-to-wrist (the wrist and the hand's global turn kept)
    for s in "lr":
        c, u, lo, h = (I[f"{b}_{s}"] for b in ("clavicle", "upperarm", "lowerarm", "hand"))
        S, E, H = gpos[:, u], gpos[:, lo], gpos[:, h]
        ax = H - S
        ax /= np.maximum(np.linalg.norm(ax, axis=-1, keepdims=True), 1e-12)
        q = np.stack([np.stack([qaxis(ax[f], g) for g in grid]) for f in range(T)])          # [T, K, 4]
        Ug = qmul(q, grot[:, None, u])
        Lg = qmul(q, grot[:, None, lo])
        Ul = qmul(qinv(grot[:, None, c]), Ug)
        Hl = qmul(qinv(Lg), grot[:, None, h])
        Ll = np.broadcast_to(rot[:, None, lo], Hl.shape)
        roll = _wrap(twist_y(qmul(qinv(sk.rest_rot[u]), Ul)))
        pro, fl, dv = wrist(sk, Ll, Hl, s)
        E2 = S[:, None] + qrot(q, (E - S)[:, None])
        e_head = np.linalg.norm(E2 - head[:, None], axis=-1)
        e_trunk = _seg_dist(E2, pel[:, None], nk[:, None])
        f_head = _seg_dist(head[:, None], E2, np.broadcast_to(H[:, None], E2.shape))
        Aa = np.degrees(np.arccos(np.clip(np.einsum("ti,ti->t", (E - S) / np.linalg.norm(E - S, axis=-1, keepdims=True),
                                                          down), -1, 1)))
        xa = np.clip((Aa - SWIVEL_A[0]) / (SWIVEL_A[1] - SWIVEL_A[0]), 0, 1)
        wa = np.maximum(xa * xa * (3 - 2 * xa), 0.02)[:, None]
        cost = (_hinge(roll, ROLL_OK, ROLL_SCALE) + _hinge(fl, FLEX_OK, FLEX_SCALE) + _hinge(dv, DEV_OK, DEV_SCALE)
                + _hinge(pro, PRO_OK, PRO_SCALE) + (grid[None] / (STAY * wa)) ** 2)
        fl_lim = np.minimum(ELBOW_FLOOR, E2[:, j0, 1])[:, None]
        cost = cost + 50.0 * (np.maximum(0.0, fl_lim - E2[..., 1]) / CLEAR_SCALE) ** 2
        for d, lim in ((e_head, ELBOW_HEAD), (e_trunk, ELBOW_TRUNK), (f_head, FORE_HEAD)):
            lim_f = np.minimum(lim, d[:, j0])[:, None]      # never worse than the clip's own arm
            cost = cost + 50.0 * (np.maximum(0.0, lim_f - d) / CLEAR_SCALE) ** 2
        path = _viterbi(cost, grid, loop)
        sw = np.clip(_smooth(grid[path], SIGMA, loop), -SPAN, SPAN)
        r0 = np.abs(roll[:, j0])
        x = (sw + SPAN) / STEP                                   # the roll at the smoothed swivel
        i0 = np.clip(np.floor(x).astype(int), 0, len(grid) - 2)
        fr = x - i0
        rr = np.abs((1 - fr) * roll[np.arange(T), i0] + fr * roll[np.arange(T), i0 + 1])
        gain = float(np.max(r0) - np.max(rr))
        if not (gain >= GAIN_MIN or np.max(r0) > ROLL_BIG) or np.max(np.abs(sw)) < 0.5:
            sw = np.zeros(T)
        swiv[s] = sw
        for f in range(T):
            if abs(sw[f]) < 1e-3:
                continue
            qq = qaxis(ax[f], sw[f])
            ug = qnorm(qmul(qq, grot[f, u]))
            lg = qnorm(qmul(qq, grot[f, lo]))
            rot[f, u] = qnorm(qmul(qinv(grot[f, c]), ug))
            rot[f, h] = qnorm(qmul(qinv(lg), grot[f, h]))      # the hand's global turn kept
    # ---- 1b. the roll traded into the forearm where the elbow is near straight (the forearm and hand kept)
    grot, gpos = sk.fk(rot, pos)
    rgrid = np.arange(-RHO_SPAN, RHO_SPAN + 1, RHO_STEP, dtype=float)
    k0 = int(np.argmin(np.abs(rgrid)))
    rhos = {}
    for s in "lr":
        c, u, lo, h = (I[f"{b}_{s}"] for b in ("clavicle", "upperarm", "lowerarm", "hand"))
        ud = gpos[:, lo] - gpos[:, u]
        ud /= np.linalg.norm(ud, axis=-1, keepdims=True)
        fd = gpos[:, h] - gpos[:, lo]
        fd /= np.linalg.norm(fd, axis=-1, keepdims=True)
        q = np.stack([np.stack([qaxis(ud[f], g) for g in rgrid]) for f in range(T)])          # [T, K, 4]
        Ug = qmul(q, grot[:, None, u])
        Ul = qmul(qinv(grot[:, None, c]), Ug)
        Ll = qmul(qinv(Ug), grot[:, None, lo])
        Hl = np.broadcast_to(rot[:, None, h], Ll.shape)
        roll = _wrap(twist_y(qmul(qinv(sk.rest_rot[u]), Ul)))
        pro, fl, dv = wrist(sk, Ll, Hl, s)
        hx = qrot(Ug, np.broadcast_to(np.array(HINGE[s]) / np.linalg.norm(HINGE[s]), Ug.shape[:-1] + (3,)))
        h0 = np.degrees(np.arcsin(np.clip(np.abs(np.einsum("tki,ti->tk", hx, fd)), 0, 1)))
        herr = np.maximum(0.0, h0 - np.maximum(HINGE_OK, h0[:, k0:k0 + 1]))     # (never worse than the clip's)
        cost = (_hinge(roll, ROLL_OK, ROLL_SCALE) + _hinge(fl, FLEX_OK, FLEX_SCALE) + _hinge(dv, DEV_OK, DEV_SCALE)
                + _hinge(pro, PRO_OK, PRO_SCALE) + (rgrid[None] / RHO_STAY) ** 2 + 50.0 * (herr / HINGE_SCALE) ** 2)
        path = _viterbi(cost, rgrid, loop)
        rr = np.clip(_smooth(rgrid[path], SIGMA, loop), -RHO_SPAN, RHO_SPAN)
        x = (rr + RHO_SPAN) / RHO_STEP
        i0 = np.clip(np.floor(x).astype(int), 0, len(rgrid) - 2)
        fr = x - i0
        r1 = np.abs((1 - fr) * roll[np.arange(T), i0] + fr * roll[np.arange(T), i0 + 1])
        gain = float(np.max(np.abs(roll[:, k0]) - r1))     # (per frame: the forearm and hand never move)
        if gain < GAIN_MIN or np.max(np.abs(rr)) < 0.5:
            rr = np.zeros(T)
        rhos[s] = rr
        for f in range(T):
            if abs(rr[f]) < 1e-3:
                continue
            ug = qnorm(qmul(qaxis(ud[f], rr[f]), grot[f, u]))
            rot[f, u] = qnorm(qmul(qinv(grot[f, c]), ug))
            rot[f, lo] = qnorm(qmul(qinv(ug), grot[f, lo]))     # the forearm's global kept (and so the hand's)
    # ---- 2. the wrist: the hand turned the least way into its comfortable range (eased, capped); not where both
    # hands hold one weapon (the grip kept)
    dw = np.linalg.norm(gpos[:, I["hand_l"]] - gpos[:, I["hand_r"]], axis=-1)
    xw = np.clip((dw - TWO_HAND[0]) / (TWO_HAND[1] - TWO_HAND[0]), 0, 1)
    wone = np.clip(_smooth(xw * xw * (3 - 2 * xw), 2 * TURN_SIGMA, loop), 0, 1)
    def _free(d, lim):
        x = np.clip((d - lim[0]) / (lim[1] - lim[0]), 0, 1)
        return x * x * (3 - 2 * x)

    turn, tilt = {}, {}
    z = np.broadcast_to(np.array([0, 0, 1.0]), (T, 3))
    mid = measure(sk, rot, pos)
    for s in "lr":
        lo, h = I[f"lowerarm_{s}"], I[f"hand_{s}"]
        xa = np.clip((mid[s]["A"] - W_DEV_A[0]) / (W_DEV_A[1] - W_DEV_A[0]), 0, 1)
        ra = xa * xa * (3 - 2 * xa)
        v = _rotvec(_comfort(sk, rot[:, lo], rot[:, h], s, W_DEV_LOW + (W_DEV - W_DEV_LOW) * ra,
                             W_EXT + (W_EXT_HIGH - W_EXT) * ra))
        a = np.linalg.norm(v, axis=-1)
        Hs = gpos[:, h]
        thigh = np.minimum(*(_seg_dist(Hs, gpos[:, I[f"thigh_{k}"]], gpos[:, I[f"calf_{k}"]]) for k in "lr"))
        w = (wone * _free(Hs[:, 1], PLANT_FLOOR) * _free(thigh, PLANT_THIGH) * _free(_seg_dist(Hs, pel, nk), PLANT_TRUNK)
             * _free(np.linalg.norm(Hs - head, axis=-1), PLANT_HEAD))
        w = np.clip(_smooth(w, 2 * TURN_SIGMA, loop), 0, 1)
        v = v * (np.minimum(a, math.radians(TURN_CAP)) / np.maximum(a, 1e-12))[:, None] * w[:, None]
        v = _smooth(v, TURN_SIGMA, loop)
        rq = _qexp(v)
        turn[s] = float(np.degrees(np.max(np.linalg.norm(v, axis=-1))))
        tilt[s] = float(np.degrees(np.max(np.arccos(np.clip(qrot(rq, z)[:, 2], -1, 1)))))
        if turn[s] > 0.05:
            rot[:, h] = qnorm(qmul(rot[:, h], rq))
    if report is not None:
        b, a = _stats(measure(sk, rot0, pos)), _stats(measure(sk, rot, pos))
        for s in "lr":
            report[s] = dict(before=b[s], after=a[s], swivel=float(np.max(np.abs(swiv[s]))), turn=turn[s],
                             rho=float(np.max(np.abs(rhos[s]))),
                             tilt=tilt[s], two_hand=float(1 - np.min(wone)))
    return rot


def arrays(sk: Skeleton, d):
    """A clip JSON's local rotations and positions [T, J, ...] (rest where it has no track)."""
    I = sk.index
    n = len(d["tracks"][0]["keys"])
    rot = np.tile(sk.rest_rot, (n, 1, 1)).astype(float)
    pos = np.tile(sk.rest_pos, (n, 1, 1)).astype(float)
    for t in d["tracks"]:
        j = I.get(t["bone"])
        if j is None:
            continue
        (rot if t["type"] == "rot" else pos)[:, j] = np.array(t["keys"], float)
    return rot, pos


def solve_json(sk: Skeleton, d, report=None):
    """A clip JSON (rig.Clip.to_json's form) with its arms re-solved (a new dict)."""
    I = sk.index
    rot, pos = arrays(sk, d)
    new = solve_rot(sk, rot, pos, float(d["fps"]), bool(d.get("loop", False)), report)
    out = dict(d)
    tracks = [dict(t) for t in d["tracks"]]
    have = {t["bone"]: t for t in tracks if t["type"] == "rot"}
    for s in "lr":
        for b in (f"upperarm_{s}", f"lowerarm_{s}", f"hand_{s}"):
            j = I[b]
            if np.max(np.abs(new[:, j] - rot[:, j])) < 1e-7:
                continue
            keys = np.round(qcontinuous(new[:, j]), 6).tolist()
            if b in have:
                have[b]["keys"] = keys
            else:
                t = {"bone": b, "type": "rot", "keys": keys}
                tracks.insert(0, t)
                have[b] = t
    out["tracks"] = tracks
    return out


def chain_tracks(d):
    """Body 6's twist chain: upperarm_twist_02/03/04 get upperarm_twist_01's track, as the pack Body 6 shot with
    (B5/a2/pack/clips_chain) carried them (the game's twist chain drives them at run time). In place; returns d."""
    have = {t["bone"]: t for t in d["tracks"] if t["type"] == "rot"}
    for s in "lr":
        t1 = have.get(f"upperarm_twist_01_{s}")
        if t1 is None:
            continue
        for b in CHAIN:
            n = f"{b}_{s}"
            if n not in have:
                t = {"bone": n, "type": "rot", "keys": [list(k) for k in t1["keys"]]}
                d["tracks"].append(t)
                have[n] = t
    return d


def row(name, rep):
    out = []
    for s in "lr":
        r = rep.get(s)
        if not r:
            continue
        b, a = r["before"], r["after"]
        out.append(f"{name:24s} {s}  roll {b['roll']:4.0f}->{a['roll']:4.0f}  dev {b['dev']:3.0f}->{a['dev']:3.0f}  "
                   f"ext {b['ext']:3.0f}->{a['ext']:3.0f}  flex {b['flex']:3.0f}->{a['flex']:3.0f}  "
                   f"pron {b['pro']:4.0f}->{a['pro']:4.0f}  swivel {r['swivel']:3.0f}  rho {r['rho']:3.0f}  turn {r['turn']:3.0f}  "
                   f"tilt {r['tilt']:3.0f}  2h {r['two_hand']:.2f}")
    return out


def stage(src: Path, dst: Path, sk: Skeleton, log=print, table=None):
    """Every clip JSON in src re-solved into dst (dst may be src: clavhold's stage, re-solved in place); the chain
    bones' tracks added (ARM_CHAIN=0: not). table: a path for the per-clip report (ARM_ROLL_TABLE). Returns dst."""
    dst.mkdir(parents=True, exist_ok=True)
    rows, moved = [], []
    chain = os.environ.get("ARM_CHAIN", "1") != "0"
    table = table or os.environ.get("ARM_ROLL_TABLE")
    for f in sorted(src.glob("*.json")):
        d = json.loads(f.read_text())
        rep = {}
        r = solve_json(sk, d, rep)
        if chain:
            chain_tracks(r)
        (dst / f.name).write_text(json.dumps(r, separators=(",", ":")))
        rows += row(d["name"], rep)
        if max((max(rep[s]["swivel"], rep[s]["rho"], rep[s]["turn"]) for s in rep), default=0.0) >= 0.5:
            moved.append(d["name"])
    log(f"  arm roll: {len(moved)} clips re-solved")
    if table:
        Path(table).write_text("\n".join(rows) + "\n")
    return dst


if __name__ == "__main__":
    import sys
    from rig import DATA
    sk = Skeleton.load(DATA / "heroine_skeleton.json")
    for p in sys.argv[1:]:
        d = json.loads(Path(p).read_text())
        rep = {}
        solve_json(sk, d, rep)
        print("\n".join(row(d["name"], rep)))
