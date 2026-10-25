"""Her arms re-solved where a clip wrings them: a pass at pack time (build.pack), after clavhold.

The owner (24 Oct, the raised arm at reaver_show and the Warden cast): "still twisting like a towel, even the
wrist angle is bizarre". The twist chain (helpers SPEC "twist_chain") spreads the upper arm's roll evenly down
the humerus, but a roll of 75-110 deg still reads as a wrung towel under linear skinning, and her keyed IK left
the wrist bent 45-57 deg to the side (a real wrist: under ~20 deg of deviation, ~45 deg of extension).

The fix is the pose, not the skin. Per frame and side, the arm swivels about its shoulder-to-wrist line (the
elbow swung round that line; the wrist stays where the clip put it, the hand's global turn is kept, so the
weapon and any two-handed grip are untouched). The swivel is chosen to bring the upper arm's roll (its twist
about its own line from rest, what the game's twist chain reads) toward a real arm's comfortable range and the
wrist into its natural range, staying near the clip's own elbow, the elbow and forearm kept clear of her head
and trunk; one Viterbi pass over every frame picks a smooth path (no pops), then a light Gaussian.
What the swivel takes off the upper arm's roll lands in the forearm's pronation (the hand's turn about the
forearm, which the game's forearm twist bones carry), never past a real forearm's range.

Off with ARM_ROLL=0. A frame whose arm is already comfortable gets no swivel (the cost is flat there).
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path

import numpy as np

from rig import Skeleton, qaxis, qcontinuous, qinv, qmul, qnorm, qrot

# Comfortable ranges (deg): the upper arm's roll from rest, the wrist's flexion/extension and deviation, the
# forearm's pronation/supination (the hand's turn about the forearm). Past them the cost climbs (per SCALE deg).
ROLL_OK, ROLL_SCALE = float(os.environ.get("ARM_ROLL_OK", "35")), 15.0
FLEX_OK, FLEX_SCALE = 45.0, 10.0
DEV_OK, DEV_SCALE = 20.0, 8.0
PRO_OK, PRO_SCALE = 85.0, 10.0
STAY = 50.0          # deg of swivel that cost as much as ROLL_SCALE past ROLL_OK (stay near the clip's elbow)
STEP = 3             # the swivel grid (deg), +-SPAN
SPAN = 120
JERK = 4.0           # deg per frame of swivel change that costs one unit (Viterbi's smoothness)
SIGMA = 1.5          # frames: the chosen path's final smoothing
# Clearance (m): the elbow from her head's centre and from her trunk's line (pelvis to neck_01), the forearm
# (elbow to wrist) from her head's centre. Under it the cost climbs steeply (per CLEAR_SCALE m), unless the
# clip's own arm was already that close (never worse than the clip).
ELBOW_HEAD, ELBOW_TRUNK, FORE_HEAD, CLEAR_SCALE = 0.17, 0.15, 0.12, 0.015
HEAD_UP = 0.09       # her head's centre above the Head bone (m)


def on():
    return os.environ.get("ARM_ROLL", "1") != "0"


def twist_y(d):
    """Twist angle (deg) of local rotation(s) d [..., 4] about the bone's own +Y."""
    return np.degrees(2 * np.arctan2(d[..., 1], d[..., 3]))


def _wrap(a):
    return (a + 180.0) % 360.0 - 180.0


def _hinge(x, ok, scale):
    return (np.maximum(0.0, np.abs(x) - ok) / scale) ** 2


def wrist(sk: Skeleton, lo_rot, h_rot, s):
    """Forearm pronation and wrist flexion/deviation (deg) from the forearm's and hand's local rotations
    [..., 4]: the forearm's own roll is handed down to the hand, as the game does (helpers SPEC "unroll").
    Pronation: the hand's twist about its own +Y; flexion: its swing about +Z (the thumb's axis); deviation:
    about +X (the palm's normal)."""
    I = sk.index
    l, h = I[f"lowerarm_{s}"], I[f"hand_{s}"]
    rl, rh = sk.rest_rot[l], sk.rest_rot[h]
    dl = qmul(qinv(rl), lo_rot)
    t = np.zeros_like(dl)
    t[..., 1], t[..., 3] = dl[..., 1], dl[..., 3]
    t = t / np.maximum(np.linalg.norm(t, axis=-1, keepdims=True), 1e-12)
    hl = qmul(qmul(qinv(rl), qmul(t, rl)), h_rot)     # the forearm's roll moved onto the hand
    dh = qmul(qinv(rh), hl)
    pro = twist_y(dh)
    tw = np.zeros_like(dh)
    tw[..., 1], tw[..., 3] = dh[..., 1], dh[..., 3]
    tw = tw / np.maximum(np.linalg.norm(tw, axis=-1, keepdims=True), 1e-12)
    sw = qmul(dh, qinv(tw))
    sw = np.where(sw[..., 3:4] < 0, -sw, sw)
    v = sw[..., :3]
    n = np.linalg.norm(v, axis=-1)
    ang = 2 * np.degrees(np.arctan2(n, sw[..., 3]))
    ax = v / np.maximum(n, 1e-12)[..., None]
    return _wrap(pro), ang * ax[..., 2], ang * ax[..., 0]


def _seg_dist(p, a, b):
    ab = b - a
    t = np.clip(np.einsum("...i,...i", p - a, ab) / np.maximum(np.einsum("...i,...i", ab, ab), 1e-12), 0, 1)
    return np.linalg.norm(p - (a + t[..., None] * ab), axis=-1)


def _seg_seg(a0, a1, p):
    """Distance from point p to segment a0-a1 (all [..., 3])."""
    return _seg_dist(p, a0, a1)


def measure(sk: Skeleton, rot, pos=None):
    """Per side, per frame: (roll, pronation, flexion, deviation, A) of a clip's local rotations [T, J, 4]."""
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
    if sigma < 0.5 or len(x) < 3:
        return x.copy()
    r = int(3 * sigma)
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    if loop:
        body = x[:-1]
        idx = np.arange(-r, len(body) + r) % len(body)
        out = np.convolve(body[idx], k, mode="valid")
        return np.append(out, out[0])
    pad = np.concatenate([np.full(r, x[0]), x, np.full(r, x[-1])])
    return np.convolve(pad, k, mode="valid")


def _viterbi(cost, grid, loop):
    """cost [T, K]: the path of grid indices minimising sum cost + ((d swivel)/JERK)^2."""
    T, K = cost.shape
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


def solve_rot(sk: Skeleton, rot, pos, fps, loop, report=None):
    """rot [T, J, 4] local rotations (a changed copy returned), pos [T, J, 3]."""
    I = sk.index
    if "upperarm_l" not in I or "Head" not in I:
        return rot
    rot = rot.copy()
    T = rot.shape[0]
    grot, gpos = sk.fk(rot, pos)
    head = gpos[:, I["Head"]] + qrot(grot[:, I["Head"]], np.broadcast_to([0, HEAD_UP, 0], (T, 3)))
    pel, nk = gpos[:, I["pelvis"]], gpos[:, I["neck_01"]]
    grid = np.arange(-SPAN, SPAN + 1, STEP, dtype=float)
    K = len(grid)
    for s in "lr":
        c, u, lo, h = (I[f"{b}_{s}"] for b in ("clavicle", "upperarm", "lowerarm", "hand"))
        S, E, H = gpos[:, u], gpos[:, lo], gpos[:, h]
        ax = H - S
        ax /= np.maximum(np.linalg.norm(ax, axis=-1, keepdims=True), 1e-12)
        # every candidate swivel at every frame: [T, K]
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
        f_head = _seg_seg(E2, np.broadcast_to(H[:, None], E2.shape), head[:, None])
        j0 = int(np.argmin(np.abs(grid)))
        cost = (_hinge(roll, ROLL_OK, ROLL_SCALE) + _hinge(fl, FLEX_OK, FLEX_SCALE) + _hinge(dv, DEV_OK, DEV_SCALE)
                + _hinge(pro, PRO_OK, PRO_SCALE) + (grid[None] / STAY) ** 2)
        for d, lim in ((e_head, ELBOW_HEAD), (e_trunk, ELBOW_TRUNK), (f_head, FORE_HEAD)):
            lim_f = np.minimum(lim, d[:, j0])[:, None]      # never worse than the clip's own arm
            cost = cost + 50.0 * (np.maximum(0.0, lim_f - d) / CLEAR_SCALE) ** 2
        path = _viterbi(cost, grid, loop)
        sw = _smooth(grid[path], SIGMA, loop)
        if report is not None:
            k = path
            fr = np.arange(T)
            report[s] = dict(swivel=float(np.max(np.abs(sw))),
                             roll0=float(np.max(np.abs(roll[:, j0]))), roll1=float(np.max(np.abs(roll[fr, k]))),
                             dev0=float(np.max(np.abs(dv[:, j0]))), dev1=float(np.max(np.abs(dv[fr, k]))),
                             flex0=float(np.max(np.abs(fl[:, j0]))), flex1=float(np.max(np.abs(fl[fr, k]))),
                             pro0=float(np.max(np.abs(pro[:, j0]))), pro1=float(np.max(np.abs(pro[fr, k]))))
        if np.max(np.abs(sw)) < 0.5:
            continue
        for f in range(T):
            if abs(sw[f]) < 1e-3:
                continue
            qq = qaxis(ax[f], sw[f])
            ug = qnorm(qmul(qq, grot[f, u]))
            lg = qnorm(qmul(qq, grot[f, lo]))
            rot[f, u] = qnorm(qmul(qinv(grot[f, c]), ug))
            rot[f, h] = qnorm(qmul(qinv(lg), grot[f, h]))      # the hand's global turn kept
    return rot


def solve_json(sk: Skeleton, d, report=None):
    """A clip JSON (rig.Clip.to_json's form) with its arms re-solved (a new dict)."""
    I = sk.index
    n = len(d["tracks"][0]["keys"])
    rot = np.tile(sk.rest_rot, (n, 1, 1)).astype(float)
    pos = np.tile(sk.rest_pos, (n, 1, 1)).astype(float)
    for t in d["tracks"]:
        j = I.get(t["bone"])
        if j is None:
            continue
        (rot if t["type"] == "rot" else pos)[:, j] = np.array(t["keys"], float)
    new = solve_rot(sk, rot, pos, float(d["fps"]), bool(d.get("loop", False)), report)
    out = dict(d)
    tracks = [dict(t) for t in d["tracks"]]
    have = {t["bone"]: t for t in tracks if t["type"] == "rot"}
    for s in "lr":
        for b in (f"upperarm_{s}", f"hand_{s}"):
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


def stage(src: Path, dst: Path, sk: Skeleton, log=print):
    """Every clip JSON in src re-solved in place into dst (dst may be src's staged copy). Returns dst."""
    dst.mkdir(parents=True, exist_ok=True)
    moved = []
    for f in sorted(src.glob("*.json")):
        d = json.loads(f.read_text())
        rep = {}
        r = solve_json(sk, d, rep)
        (dst / f.name).write_text(json.dumps(r, separators=(",", ":")))
        m = max((rep[s]["swivel"] for s in rep), default=0.0)
        if m >= 0.5:
            moved.append(f"{d['name']} {m:.0f}")
    log(f"  arm roll: {len(moved)} clips re-solved (max swivel deg): {', '.join(moved)}")
    return dst


def _table(sk, paths):
    for p in paths:
        d = json.loads(Path(p).read_text())
        rep = {}
        solve_json(sk, d, rep)
        for s in "lr":
            r = rep.get(s)
            if r:
                print(f"{d['name']:24s} {s}  swivel {r['swivel']:4.0f}  roll {r['roll0']:4.0f} -> {r['roll1']:4.0f}  "
                      f"dev {r['dev0']:3.0f} -> {r['dev1']:3.0f}  flex {r['flex0']:3.0f} -> {r['flex1']:3.0f}  "
                      f"pron {r['pro0']:4.0f} -> {r['pro1']:4.0f}")


if __name__ == "__main__":
    import sys
    from rig import DATA
    _table(Skeleton.load(DATA / "heroine_skeleton.json"), sys.argv[1:])
