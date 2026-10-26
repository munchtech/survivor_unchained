"""Her town walks, one per calling (Animation 51): walk_warden_town, walk_reaver_town, walk_arcanist_town,
walk_stalker_town. Weapons sheathed, both arms free.

One shared base for all four, so she is one woman: Kimodo's her_walk_2 (generated.py's test_walk_her_2, a max judge's
pick of 14), upright, a real heel strike and toe-off, a feminine hip sway. Laid over it here, every calling first:

- the loop turned to start at her LEFT heel strike (as her runs start with the left foot down), and retimed;
- her stance feet laid flat (the take stood ~10 deg toes-up) and held to the ground at the clip's speed (no slide):
  each foot pivots on its heel, then flat, then on its ball, and the leg is solved to it (a pure knee hinge);
- the stance knee's dip at passing capped (the pelvis raised over it);
- the arms re-made: one swing profile shared by both arms (half a cycle apart), so the swing is centred and
  symmetric, the abduction even; the elbow bend peaking on the forward swing, 2.5 frames behind the shoulder (loose,
  not robotic); the hands in a graded half-curl, thumbs forward.

Per calling (the judge's numbers, Animation 51): the sway (the pelvis's roll and its lateral shift, about their mean)
scaled, the chest's carriage (lean, upper-spine extension, counter-tilt and counter-yaw), the head kept level and its
motion damped, the shoulders, step width and stride, the stance knee, the cadence and the arms' ranges. CALLINGS below.
"""
from __future__ import annotations

import math

import numpy as np

from rig import Clip, qaxis, qbetween, qinv, qmul, qrot, qslerp

# frames: the loop's length at 30 fps (her_2 is 42: 40 = 1.05x, 43 = cadence -7%); sway: share of her_2's hip roll and
# side shift; counter: the chest's roll against the pelvis's (share); yaw: the chest's counter-yaw (deg, +-); lean:
# forward from the hips (deg); upper: upper-spine extension (deg, - flexes forward); head: share of the head's own
# motion kept (about its mean); clav: (down, back) deg; width: change of step width (m); stride: scale of the feet's
# fore-and-aft travel; knee: the stance knee's cap at passing (deg); bend: extra stance knee bend (deg, the pelvis
# lowered); drop: extra pelvis drop at each heel contact (m); swing: the upper arm's fore-aft range (deg, + forward);
# abd: its abduction (deg); elbow: the elbow's range (deg); wrist: soft wrists (deg of lag against the swing).
# Round 2 (the max judge, Animation 51): tilt: the pelvis's mean pitch from rest (deg, + forward; her_2's is -26, a
# Kimodo retarget's tuck: her idles stand at -5, her runs and the other walks at +7);
# chest: the share of her_2's upper-back rounding kept (the chest's pitch on the lower spine's); stack: the shoulder
# joints this far ahead of the hip joints at passing (m), by turning the lower spine; neck: the neck's own extension
# (deg, the head kept level); yaw_strike: the chest's counter-yaw locked to the heel strikes; thumb: the knuckle line's
# heading in (deg); fingers: graded() bends (index's knuckle, middle, tip ranges); twist: the upper arm turned in (deg);
# bob: the hips' vertical travel kept (share, about its mean); kick: the swing foot's height kept (share).
_F0 = ((15.0, 30.0), (20.0, 45.0), (10.0, 20.0))
CALLINGS = {
    "warden": dict(frames=40, sway=1.0, counter=1 / 3, yaw=0.0, yaw_strike=False, tilt=0.0, chest=0.5, stack=0.01,
                   upper=0.0, head=1.0, neck=0.0, clav=(0.0, 0.0), width=0.0, stride=1.0, knee=15.0, bend=0.0, drop=0.01,
                   swing=(-12.0, 10.0), abd=7.5, elbow=(10.0, 25.0), wrist=0.0, thumb=10.0, fingers=_F0, outfit="warden"),
    "reaver": dict(frames=43, sway=0.7, counter=0.0, yaw=7.0, yaw_strike=True, tilt=0.0, chest=0.5, stack=0.01,
                   upper=3.5, head=1.0, neck=0.0, clav=(0.0, 2.5), width=0.04, stride=1.0, knee=22.0, bend=0.0, drop=0.005,
                   swing=(-13.0, 12.0), abd=8.0, elbow=(8.0, 25.0), wrist=0.0, thumb=10.0, fingers=_F0, outfit="reaver"),
    "arcanist": dict(frames=40, sway=0.575, counter=0.0, yaw=0.0, yaw_strike=False, tilt=0.0, chest=0.5, stack=0.01,
                     upper=0.0, head=0.5, neck=3.0, clav=(2.0, 2.0), width=-0.02, stride=1.0, knee=10.0, bend=0.0, drop=0.0,
                     swing=(-9.0, 7.0), abd=7.0, elbow=(15.0, 21.0), wrist=0.0, thumb=10.0, fingers=_F0, outfit="arcanist"),
    "stalker": dict(frames=44, sway=0.75, counter=0.0, yaw=0.0, yaw_strike=False, tilt=0.0, chest=0.5, stack=0.01,
                    upper=-4.5, head=0.5, neck=0.0, clav=(0.0, 0.0), width=0.0, stride=1.0, knee=20.0, bend=5.0, drop=0.0,
                    swing=(-12.0, 10.0), abd=7.5, elbow=(12.0, 28.0), wrist=6.0, thumb=3.0,
                    fingers=((10.0, 30.0), (14.0, 45.0), (6.0, 20.0)), outfit="ranger"),
}
# Reaver round 3 (Animation 52): her head bobbed 11 cm on the 1.1 stride (the double-support low is set by the legs'
# reach, so `bob` and `bend` don't move it); stride 1.0 and the stance knee capped at 22 at passing bring it to 7.5.
for _c in CALLINGS.values():
    _c.setdefault("twist", 5.0)
    _c.setdefault("bob", 0.75)
    _c.setdefault("kick", 0.7)
    _c.setdefault("abd_cap", 14.0)
    _c.setdefault("shrug", 0.25)

# Her soles at rest (skin within 2.5 cm of the ground, motion.soles): the heel's and the ball's bottom.
HEEL = {"l": np.array([0.0938, 0.0, -0.0799]), "r": np.array([-0.0886, 0.0, -0.0787])}
BALL = {"l": np.array([0.1245, 0.0, 0.0648]), "r": np.array([-0.1234, 0.0, 0.0651])}
UP, FWD, LAT = np.array([0, 1.0, 0]), np.array([0, 0, 1.0]), np.array([1.0, 0, 0])
TOE_UP = 0.02       # the frames after a toe-off: the sole and toe tip at least this far up (m)
KICK0 = 0.0         # where in the swing (share) the kick's easing starts
CLEAR = 0.025       # the swing foot's sole and toe tip at least this far off the ground (m)
TOE_OUT = 6.0       # each foot's heading out from straight ahead (deg)
LAG = 2.5          # frames the elbow's bend peaks behind the shoulder's forward swing
_BASE = {}
_LAST = {}  # per calling: the clearance's opening and the mesh's near (read by the checks)


def _base(rig):
    """her_2 as built (retargeted, in place, looped), one cycle without its closing frame."""
    if "c" not in _BASE:
        from clips.generated import TABLE, make
        row = dict(TABLE["test_walk_her_2"])
        row.pop("note")
        _BASE["c"] = make(rig, "test_walk_her_2", **row)
    return _BASE["c"]


def _wrap(a):
    return (a + 180.0) % 360.0 - 180.0


def _smooth(x, sigma):
    """Circular Gaussian smoothing along axis 0."""
    if sigma <= 0:
        return x
    n = len(x)
    r = int(3 * sigma) + 1
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    out = np.zeros_like(x, dtype=float)
    for i, w in zip(range(-r, r + 1), k):
        out += w * np.roll(x, -i, axis=0)
    return out


def _shift(x, s):
    """x(t - s), circular, fractional s (frames)."""
    n = len(x)
    t = (np.arange(n) - s) % n
    i0 = np.floor(t).astype(int)
    f = t - i0
    return x[i0] * (1 - f) + x[(i0 + 1) % n] * f


class Walk:
    """One cycle being worked on: local rotations L [N, J, 4], positions P [N, J, 3] (pelvis in the root's frame)."""

    def __init__(self, rig, L, P, speed):
        self.rig, self.sk, self.I = rig, rig.sk, rig.I
        self.L, self.P, self.speed = L.copy(), P.copy(), speed
        self.grest, self.prest = (a[0] for a in self.sk.rest_globals())
        self.root_q = self.sk.rest_rot[self.I["root"]]
        self.pin = {}

    @property
    def n(self):
        return len(self.L)

    def g(self):
        return self.sk.fk(self.L, self.P)

    def turn(self, j, q, G=None):
        """Bone j (and all under it) turned by world rotations q [N, 4] about its joint."""
        if G is None:
            G, _ = self.g()
        p = self.sk.parent[j]
        for t in range(self.n):
            ng = qmul(q[t], G[t, j])
            self.L[t, j] = qmul(qinv(G[t, p]), ng)

    def set_global(self, j, want, G=None):
        """Bone j given the world rotation want [N, 4] (all under it carried)."""
        if G is None:
            G, _ = self.g()
        p = self.sk.parent[j]
        for t in range(self.n):
            self.L[t, j] = qmul(qinv(G[t, p]), want[t])

    def shift_pelvis(self, v):
        """The pelvis moved by v [N, 3] (her character space)."""
        pel = self.I["pelvis"]
        for t in range(self.n):
            self.P[t, pel] = self.P[t, pel] + qrot(qinv(self.root_q), v[t])

    def sole(self, s, G, Pp):
        """Heel and ball bottoms [N, 3] of foot s."""
        f = self.I[f"foot_{s}"]
        hl = qrot(qinv(self.grest[f]), HEEL[s] - self.prest[f])
        bl = qrot(qinv(self.grest[f]), BALL[s] - self.prest[f])
        H = np.array([Pp[t, f] + qrot(G[t, f], hl) for t in range(self.n)])
        B = np.array([Pp[t, f] + qrot(G[t, f], bl) for t in range(self.n)])
        return H, B


# ------------------------------------------------------------------ cycle --
def _cycle(rig, base, frames):
    """her_2's cycle from her left heel strike, resampled to `frames` frames."""
    sk = rig.sk
    L0, P0 = base.rot[:-1], base.pos[:-1]
    N = len(L0)
    w = Walk(rig, L0, P0, base.meta["speed"])
    G, Pp = w.g()
    H, B = w.sole("l", G, Pp)
    z = Pp[:, rig.I["foot_l"], 2]
    vz = (np.roll(z, -1) - np.roll(z, 1)) / 2
    low = (H[:, 1] < 0.012) & (vz < 0.002)
    # The start of the longest low run (circular).
    best, start = 0, 0
    for a in range(N):
        if low[a] and not low[a - 1]:
            k = 0
            while low[(a + k) % N] and k < N:
                k += 1
            if k > best:
                best, start = k, a
    # Fractional: where the heel crossed 1.2 cm coming down.
    h0, h1 = H[start - 1, 1], H[start, 1]
    t0 = start - 1 + (h0 - 0.012) / (h0 - h1) if h0 > 0.012 > h1 else float(start)
    L, P = np.empty((frames,) + L0.shape[1:]), np.empty((frames,) + P0.shape[1:])
    for k in range(frames):
        t = (t0 + k * N / frames) % N
        i0 = int(math.floor(t))
        f = t - i0
        i1 = (i0 + 1) % N
        for j in range(L0.shape[1]):
            L[k, j] = qslerp(L0[i0, j], L0[i1, j], f)
        P[k] = P0[i0] * (1 - f) + P0[i1] * f
    return Walk(rig, L, P, base.meta["speed"] * N / frames), t0


# ------------------------------------------------------------------ trunk --
def _roll_yaw(G, j):
    """A bone's world roll (about forward) and yaw (about up), deg, from its rest-relative turn's left axis."""
    x = np.array([qrot(G[t, j], LAT) for t in range(len(G))])  # not rest-relative: callers use the hip line
    return x


def _hip_line(Pp, I):
    hl = Pp[:, I["thigh_l"]] - Pp[:, I["thigh_r"]]
    roll = np.degrees(np.arctan2(hl[:, 1], hl[:, 0]))
    yaw = np.degrees(np.arctan2(-hl[:, 2], hl[:, 0]))
    return roll, yaw


def _bone_axes(w, G, j):
    """A bone's turn from rest, as world (roll about +Z, yaw about +Y, pitch about +X) of its carried axes."""
    d = np.array([qmul(G[t, j], qinv(w.grest[j])) for t in range(w.n)])
    x = np.array([qrot(q, LAT) for q in d])
    z = np.array([qrot(q, FWD) for q in d])
    roll = np.degrees(np.arctan2(x[:, 1], x[:, 0]))
    yaw = np.degrees(np.arctan2(-x[:, 2], x[:, 0]))
    pitch = np.degrees(np.arctan2(-z[:, 1], z[:, 2]))
    return roll, yaw, pitch


def _trunk(w, c, pas):
    I, n = w.I, w.n
    pel, s1, s2, s3 = I["pelvis"], I["spine_01"], I["spine_02"], I["spine_03"]
    G, Pp = w.g()
    head0 = G[:, I["Head"]].copy()
    chest0 = _bone_axes(w, G, s3)
    roll, yaw = _hip_line(Pp, I)
    k = c["sway"] - 1.0
    # Round 2: her_2 walks sway-backed (the pelvis tilted back, the lumbar leaning back, the upper back rounded
    # forward over it: the shoulder joints 9-14 cm behind the hip joints). The pelvis turned forward c["tilt"] (the
    # spine above kept), the rounding (the chest's pitch on the lower spine's) cut to c["chest"] of itself at the
    # chest joint; the trunk then stacked from the lower spine (below, once the chest is square).
    if c["tilt"] is not None:
        G, _ = w.g()
        s1g = G[:, s1].copy()
        w.turn(pel, np.tile(qaxis(LAT, c["tilt"] - float(_bone_axes(w, G, pel)[2].mean())), (n, 1)), G)
        G, _ = w.g()
        w.set_global(s1, s1g, G)
        G, Pp = w.g()
        roll2, _ = _hip_line(Pp, I)
        k = c["sway"] * np.ptp(roll) / max(np.ptp(roll2), 1e-6) - 1.0  # (the tilt changes the hip line's roll: her_2's kept)
        roll = roll2
    # Sway: the pelvis's roll and its side shift scaled about their mean; the spine above kept where it was.
    # (her_2 carries her hips 4 deg low on the left on average: that mean is taken out, a limp's tilt.)
    if True:
        d = k * (roll - roll.mean()) - roll.mean()
        q = np.array([qaxis(FWD, a) for a in d])
        s1g = G[:, s1].copy()
        w.turn(pel, q, G)
        G, _ = w.g()
        w.set_global(s1, s1g, G)
        x = Pp[:, pel, 0]
        v = np.zeros((n, 3))
        v[:, 0] = k * (x - x.mean())
        w.shift_pelvis(v)
    # The spine straightened: her_2's lumbar leans back (spine_02 -19 deg) under a chest pitched forward (+16): the
    # lower spine and spine_02 brought to one lean (solved below), the chest's own forward pitch cut to c["chest"].
    G, _ = w.g()
    p1, p2, p3 = (_bone_axes(w, G, j)[2] for j in (s1, s2, s3))
    w.turn(s2, np.tile(qaxis(LAT, float((p1 - p2).mean())), (n, 1)), G)
    G, _ = w.g()
    w.turn(s3, np.tile(qaxis(LAT, float((p1.mean() + c["chest"] * p3.mean()) - _bone_axes(w, G, s3)[2].mean())), (n, 1)), G)
    # The upper spine's extension (+, a sternum lift: at the chest joint only) or flexion (-, the stalker's hunch).
    if c["upper"] > 0:
        w.turn(s3, np.tile(qaxis(LAT, -c["upper"]), (n, 1)))
    elif c["upper"]:
        for j, share in ((s2, 0.4), (s3, 0.6)):
            w.turn(j, np.tile(qaxis(LAT, -c["upper"] * share), (n, 1)))
    # The chest's roll against the pelvis's (counter share), and its counter-yaw (deg).
    G, Pp = w.g()
    roll, yaw = _hip_line(Pp, I)
    cr, cy, _ = _bone_axes(w, G, s3)
    dr = np.zeros(n)
    dy = np.zeros(n)
    if c["counter"]:
        dr = -c["counter"] * (roll - roll.mean()) - (cr - cr.mean())
    if c["yaw"] and c["yaw_strike"]:
        # The shoulder opposite the leading leg forward, peaking at each heel strike (frame 0 the left's: the
        # chest turned to her left, + about up, the right shoulder ahead), the arms riding on it.
        want = c["yaw"] * np.cos(2 * math.pi * np.arange(n) / n)
        dy = want - (cy - cy.mean())
    elif c["yaw"]:
        y = yaw - yaw.mean()
        want = -c["yaw"] * y / max(np.abs(y).max(), 1e-6)
        dy = want - (cy - cy.mean())
    # The chest square on average (her_2's is turned 7 deg to her right, its left shoulder 5 cm ahead: lopsided).
    dr = dr - cr.mean()
    dy = dy - cy.mean()
    if True:
        dr, dy = _smooth(dr, 1.0), _smooth(dy, 1.0)
        for j, share in ((s2, 0.5), (s3, 0.5)):
            q = np.array([qmul(qaxis(UP, b * share), qaxis(FWD, a * share)) for a, b in zip(dr, dy)])
            w.turn(j, q)
    # The chest over the pelvis (her_2's sits 1.2 cm to her left of it, its right hand nearer her hip): the lower
    # spine leaned, the chest turned back level.
    G, Pp = w.g()
    dx = float((Pp[:, s3, 0] - Pp[:, pel, 0]).mean())
    a = math.degrees(math.atan2(dx, float(np.linalg.norm(Pp[:, s3] - Pp[:, s1], axis=1).mean())))
    w.turn(s1, np.tile(qaxis(FWD, a), (n, 1)), G)
    w.turn(s3, np.tile(qaxis(FWD, -a), (n, 1)))
    # Shoulders level in the chest (her_2 carries the left 2 cm high), then (down, back) deg, about the chest's axes.
    G, Pp = w.g()
    yl, yr = (np.mean([qrot(qinv(G[t, s3]), Pp[t, I[f"upperarm_{s}"]] - Pp[t, s3])[1] for t in range(n)]) for s in "lr")
    lv = math.degrees(math.atan2((yl - yr) / 2, 0.17)) if c["shrug"] >= 1.0 else 0.0  # (the unshrug squares them)
    down, back = c["clav"]
    # her_2 shrugs: each shoulder joint 4.4 cm up and 2.3 back in the chest from where it stands at rest (her runs
    # carry 1 cm): c["shrug"] of that kept, the clavicle turned (about the chest's axes) to put it there.
    G, Pp = w.g()
    unshrug = {}
    for s in "lr":
        cj, uj = I[f"clavicle_{s}"], I[f"upperarm_{s}"]
        loc = np.mean([qrot(qmul(w.grest[s3], qinv(G[t, s3])), Pp[t, uj] - Pp[t, cj]) for t in range(n)], 0)
        rest = w.prest[uj] - w.prest[cj]
        unshrug[s] = qbetween(loc, rest + c["shrug"] * (loc - rest))
    if True:
        G, _ = w.g()
        for s, sg in (("l", 1.0), ("r", -1.0)):
            j = I[f"clavicle_{s}"]
            q = []
            for t in range(n):
                dc = qmul(G[t, s3], qinv(w.grest[s3]))
                loc = qmul(qmul(qaxis(UP, back * sg), qaxis(FWD, -(down + sg * lv) * sg)), unshrug[s])
                q.append(qmul(qmul(dc, loc), qinv(dc)))
            # turn the clavicle, the upper arm set again later
            w.turn(j, np.array(q), G)
    # Stacked: the lower spine turned (forward +) until the shoulder joints stand c["stack"] ahead of the hip joints
    # at passing (pas: weights), the chest above carried.
    wt = pas / max(pas.sum(), 1e-6)
    for _ in range(4):
        G, Pp = w.g()
        hip = (Pp[:, I["thigh_l"]] + Pp[:, I["thigh_r"]]) / 2
        sho = (Pp[:, I["upperarm_l"]] + Pp[:, I["upperarm_r"]]) / 2
        dz = float(((sho - hip)[:, 2] * wt).sum())
        h = float((np.linalg.norm(sho - Pp[:, s1], axis=1) * wt).sum())
        da = math.degrees(math.asin(np.clip((c["stack"] - dz) / h, -0.5, 0.5)))
        if abs(da) < 0.05:
            break
        w.turn(s1, np.tile(qaxis(LAT, da), (n, 1)), G)
    # The head: her_2's own head turn, its motion about its mean kept by c["head"], its mean as it was (chin level).
    G, _ = w.g()
    hj, nj = I["Head"], I["neck_01"]
    mean = head0[0].copy()
    acc = np.zeros(4)
    for q in head0:
        acc += q if np.dot(q, head0[0]) >= 0 else -q
    mean = acc / np.linalg.norm(acc)
    # the mean square to her too (her_2 tips it 4.6 deg to her right and turns it 3.6 to her right)
    x, z = qrot(qmul(mean, qinv(w.grest[hj])), LAT), qrot(qmul(mean, qinv(w.grest[hj])), FWD)
    fix = qmul(qaxis(UP, -math.degrees(math.atan2(-x[2], x[0]))), qaxis(FWD, -math.degrees(math.atan2(x[1], x[0]))))
    head0 = np.array([qmul(fix, q) for q in head0])
    mean = qmul(fix, mean)
    want = np.array([qslerp(mean, q, c["head"]) for q in head0])
    delta = np.array([qmul(want[t], qinv(G[t, hj])) for t in range(n)])
    half = np.array([qslerp(np.array([0, 0, 0, 1.0]), d, 0.5) for d in delta])
    w.turn(nj, half, G)
    if c["neck"]:
        # A long neck: the neck itself stood up (extended), the head kept level on it.
        w.turn(nj, np.tile(qaxis(LAT, -c["neck"]), (n, 1)))
    G, _ = w.g()
    w.set_global(hj, want, G)
    return chest0


# ------------------------------------------------------------------- arms --
def _arm_angles(G, Pp, I, s):
    sg = 1.0 if s == "l" else -1.0
    ua = Pp[:, I[f"lowerarm_{s}"]] - Pp[:, I[f"upperarm_{s}"]]
    fa = Pp[:, I[f"hand_{s}"]] - Pp[:, I[f"lowerarm_{s}"]]
    sw = np.degrees(np.arctan2(ua @ FWD, -(ua @ UP)))
    ab = np.degrees(np.arctan2(sg * (ua @ LAT), -(ua @ UP)))
    cos = np.sum(ua * fa, 1) / np.linalg.norm(ua, axis=1) / np.linalg.norm(fa, axis=1)
    el = np.degrees(np.arccos(np.clip(cos, -1, 1)))
    return sw, ab, el


def _arms(w, c, fingers):
    I, n = w.I, w.n
    G, Pp = w.g()
    sw, ab, el = {}, {}, {}
    for s in "lr":
        sw[s], ab[s], el[s] = _arm_angles(G, Pp, I, s)
    # One profile for both arms: the left's and the right's half a cycle on, each normalised 0..1, averaged.
    def norm(x):
        return (x - x.min()) / max(np.ptp(x), 1e-6)
    u = 0.5 * (norm(sw["l"]) + _shift(norm(sw["r"]), n / 2))
    u = norm(_smooth(u, 1.0))
    a_dev = 0.5 * ((ab["l"] - ab["l"].mean()) + _shift(ab["r"] - ab["r"].mean(), n / 2))
    lo, hi = c["swing"]
    e0, e1 = c["elbow"]
    for s, sg in (("l", 1.0), ("r", -1.0)):
        us = u if s == "l" else _shift(u, n / 2)
        th = lo + (hi - lo) * us
        al = c["abd"] + 0.5 * (a_dev if s == "l" else _shift(a_dev, n / 2))
        eb = e0 + (e1 - e0) * _shift(us, LAG)
        ua_j, la_j, ha_j = I[f"upperarm_{s}"], I[f"lowerarm_{s}"], I[f"hand_{s}"]
        G, Pp = w.g()
        # Upper arm: the smallest turn onto the wanted line.
        q = []
        for t in range(n):
            cur = Pp[t, la_j] - Pp[t, ua_j]
            d = np.array([sg * math.tan(math.radians(al[t])), -1.0, math.tan(math.radians(th[t]))])
            q.append(qbetween(cur, d))
        w.turn(ua_j, np.array(q), G)
        # The upper arm turned in on its own axis (the elbow pointing back, the thumb forward).
        if c["twist"]:
            G, Pp = w.g()
            w.turn(ua_j, np.array([qaxis(Pp[t, la_j] - Pp[t, ua_j], sg * c["twist"]) for t in range(n)]), G)
        # Elbow: bent about its own hinge (the plane of upper arm and forearm) to the wanted angle.
        G, Pp = w.g()
        q = []
        for t in range(n):
            a_ = Pp[t, la_j] - Pp[t, ua_j]
            b_ = Pp[t, ha_j] - Pp[t, la_j]
            ax = np.cross(a_, b_)
            if np.linalg.norm(ax) < 1e-6:
                ax = qrot(G[t, ua_j], qrot(qinv(w.grest[ua_j]), np.array([-sg * 0.0, 0.0, 0.0]) + LAT * sg))
            cur = math.degrees(math.acos(np.clip(np.dot(a_, b_) / np.linalg.norm(a_) / np.linalg.norm(b_), -1, 1)))
            q.append(qaxis(ax, eb[t] - cur))
        w.turn(la_j, np.array(q), G)
        # Soft wrists: the hand trailing the swing (flexing back against its way).
        if c["wrist"]:
            G, Pp = w.g()
            vel = np.gradient(np.concatenate([th[-2:], th, th[:2]]))[2:-2]
            vel = vel / max(np.abs(vel).max(), 1e-6)
            q = []
            for t in range(n):
                fa = Pp[t, ha_j] - Pp[t, la_j]
                side = np.cross(fa, FWD)  # turning about it swings the hand fore and aft
                q.append(qaxis(side, -c["wrist"] * vel[t]) if np.linalg.norm(side) > 1e-6 else np.array([0, 0, 0, 1.0]))
            w.turn(ha_j, np.array(q), G)
    # Thumbs forward: each hand turned about its forearm so its knuckle line (little finger to forefinger) heads
    # THUMB deg in from straight ahead (the palm to the thigh, a little back), the same both sides.
    for s, sg in (("l", 1.0), ("r", -1.0)):
        la_j, ha_j = I[f"lowerarm_{s}"], I[f"hand_{s}"]
        G, Pp = w.g()
        d = np.array([-sg * math.sin(math.radians(c["thumb"])), 0.0, math.cos(math.radians(c["thumb"]))])
        q = []
        for t in range(n):
            a = Pp[t, ha_j] - Pp[t, la_j]
            a /= np.linalg.norm(a)
            k = Pp[t, I[f"index_01_{s}"]] - Pp[t, I[f"pinky_01_{s}"]]
            kp, dp = k - a * np.dot(k, a), d - a * np.dot(d, a)
            ang = math.degrees(math.atan2(np.dot(np.cross(kp, dp), a), np.dot(kp, dp)))
            q.append(qaxis(a, ang))
        w.turn(ha_j, np.array(q), G)
    # Fingers: a graded half-curl, the same every frame.
    for name, val in fingers.items():
        w.L[:, I[name]] = val


def _finger_pose(rig, w, bends=None):
    from clips.town_idle import graded
    spec = graded(*bends) if bends else graded()
    rot, _ = rig.solve({"fingers_l": spec, "fingers_r": spec}, base=(w.L[0], w.P[0]))
    names = [nm for nm in rig.sk.names if nm.split("_")[0] in ("thumb", "index", "middle", "ring", "pinky")]
    return {nm: rot[rig.I[nm]] for nm in names}


# ------------------------------------------------------------------- legs --
def _feet(w, c, base_w):
    """The wanted foot globals and joint positions [N] per side, from the base (before the trunk's changes): stance
    laid flat, width and stride changed, each sole held to the ground through its stance at the clip's speed.
    Returns ({s: (Gf, Pf)}, {s: stance mask})."""
    I, n = w.I, w.n
    G, Pp = base_w.g()
    out, spells = {}, {}
    for s, sg in (("l", 1.0), ("r", -1.0)):
        f = I[f"foot_{s}"]
        H, B = base_w.sole(s, G, Pp)
        # Stance: low and not travelling forward.
        z = Pp[:, f, 2]
        vz = (np.roll(z, -1) - np.roll(z, 1)) / 2
        low = (np.minimum(H[:, 1], B[:, 1]) < 0.025) & (vz < 0.003)
        # keep the longest circular run
        best, start = 0, 0
        for a in range(n):
            if low[a] and not low[a - 1]:
                k = 0
                while low[(a + k) % n] and k < n:
                    k += 1
                if k > best:
                    best, start = k, a
        mask = np.zeros(n, bool)
        idx = [(start + k) % n for k in range(best)]
        mask[idx] = True
        # The flat pitch: the median of the stance's middle third (toes-up in the take), laid down for the whole cycle.
        mid = idx[best // 3: 2 * best // 3]
        pitch = np.degrees(np.arctan2(B[mid, 1] - H[mid, 1], np.linalg.norm((B - H)[mid][:, [0, 2]], axis=1)))
        flat = float(np.median(pitch))
        axl = qrot(qinv(w.grest[f]), LAT)
        qd = qaxis(axl, flat)
        Gf = np.array([qmul(G[t, f], qd) for t in range(n)])
        Pf = Pp[:, f].copy()
        # Side to side: her_2's feet wander (the left slides 23 cm out through its stance, crossing the line at its
        # strike), so each foot keeps one line, the pair as far apart as her_2's on average (+ the calling's width),
        # about their middle; and one heading, toed out TOE_OUT.
        xl, xr = Pp[:, I["foot_l"], 0].mean(), Pp[:, I["foot_r"], 0].mean()
        Pf[:, 0] = (xl + xr) / 2 + sg * ((xl - xr) + c["width"]) / 2
        bv = qrot(qinv(w.grest[f]), w.prest[I[f"ball_{s}"]] - w.prest[f])
        for t in range(n):
            v = qrot(Gf[t], bv)
            yaw = math.degrees(math.atan2(v[0], v[2]))
            Gf[t] = qmul(qaxis(UP, sg * TOE_OUT - yaw), Gf[t])
        zc = Pf[mask, 2].mean()
        Pf[:, 2] = zc + c["stride"] * (Pf[:, 2] - zc)
        # The swing's heel kick (her_2 folds the swing knee to ~80 deg): the foot's rise off its stance height kept
        # by c["kick"] (the toe's clearance restored below).
        # Only through the swing's fold (12-62% of it: none at the toe-off, which would scuff), none by the reach forward to the strike (a lowered foot
        # there would pull the hips down).
        if c["kick"] != 1.0:
            y0 = float(Pf[mask, 1].min())
            sw_ = [(idx[-1] + k) % n for k in range(1, n - best + 1)]
            for k, t in enumerate(sw_):
                u = (k + 1) / (len(sw_) + 1)
                f_ = 1.0 - (1.0 - c["kick"]) * math.sin(math.pi * min(max((u - KICK0) / 0.5, 0.0), 1.0)) ** 2
                Pf[t, 1] = y0 + f_ * (Pf[t, 1] - y0)
        # The sole's pivot: the heel, flat, then the ball.
        hl = qrot(qinv(w.grest[f]), HEEL[s] - w.prest[f])
        bl = qrot(qinv(w.grest[f]), BALL[s] - w.prest[f])
        Hn = np.array([Pf[t] + qrot(Gf[t], hl) for t in range(n)])
        Bn = np.array([Pf[t] + qrot(Gf[t], bl) for t in range(n)])
        # In the world (carried forward at the speed, the loop's time unwrapped through the stance), the heel is held
        # from the strike until the foot is flat (the ball as low as the heel), then the ball: both are the same
        # foot, so the ball's anchor is where it lay on that frame. One shift for all: as small as can be.
        ts = np.array([start + k for k in range(best)], float) / 30.0
        Hw, Bw = Hn[idx].copy(), Bn[idx].copy()
        Hw[:, 2] += w.speed * ts
        Bw[:, 2] += w.speed * ts
        flat_k = next((k for k in range(best) if Bw[k, 1] <= Hw[k, 1]), best // 2)
        X = Hw.copy()
        # (Round 2: from the flat foot to the toe-off the foot rolls over its ball JOINT, held where it stood when
        # flat, the toes planted with it (_toes): pivoting on the ball's skin slid the toe pads 13-19 mm forward.)
        bj = qrot(qinv(w.grest[f]), w.prest[I[f"ball_{s}"]] - w.prest[f])
        Jn = np.array([Pf[t] + qrot(Gf[t], bj) for t in range(n)])
        Jw = Jn[idx].copy()
        Jw[:, 2] += w.speed * ts
        X[flat_k:] = Hw[flat_k] - Jw[flat_k] + Jw[flat_k:]
        jy = Jn[idx[flat_k], 1] - Bn[idx[flat_k], 1]
        anchor = X.mean(0)
        corr = np.zeros((n, 3))
        for k, t in enumerate(idx):
            corr[t, 0] = anchor[0] - X[k, 0]
            corr[t, 2] = anchor[2] - X[k, 2]
            corr[t, 1] = -Hn[t, 1] if k < flat_k else jy - Jn[t, 1]
        # Eased in and out over 3 frames either side of the stance (the foot coming down and going up).
        ramp = 3
        for side_ in (-1, 1):
            edge = idx[0] if side_ < 0 else idx[-1]
            for k in range(1, ramp + 1):
                t = (edge + side_ * k) % n
                if mask[t]:
                    continue
                a = 1.0 - k / (ramp + 1)
                a = a * a * (3 - 2 * a)
                corr[t] = a * corr[edge]
        Pf = Pf + corr
        # Through the swing (away from the stance by more than the ease), the sole and the toe tip kept CLEAR off the
        # ground (her_2's swing foot passes a centimetre over it and scuffs): the foot lifted by a smooth hump.
        lf = I[f"ball_leaf_{s}"]
        toe = np.array([qrot(qinv(G[t, f]), Pp[t, lf] - Pp[t, f]) for t in range(n)])
        low_ = np.array([min((Pf[t] + qrot(Gf[t], hl))[1], (Pf[t] + qrot(Gf[t], bl))[1], (Pf[t] + qrot(Gf[t], toe[t]))[1] - 0.023)
                         for t in range(n)])
        near = np.array([min(min((t - u) % n, (u - t) % n) for u in idx) for t in range(n)])
        # (and from the frame after toe-off, off the ground at once: a toe left down while the foot eases away slides)
        after = np.array([(t - idx[-1]) % n for t in range(n)])
        lo = np.where(near > ramp, np.maximum(CLEAR - low_, 0.0), np.where((after >= 0) & (after <= ramp), np.maximum(TOE_UP - low_, 0.0), 0.0))
        hi = np.where(mask & (after != 0), 0.0, 1.0)
        lift = lo.copy()
        for _ in range(40):
            lift = np.clip(_smooth(lift, 1.5), lo, hi)
        Pf[:, 1] += lift
        out[s] = (Gf, Pf)
        w.pin[s] = [idx[k] for k in range(flat_k, best)]
        spells[s] = mask
    return out, spells


def _legs(w, feet):
    """Each leg solved to its foot: the knee a pure hinge (bent to the reach's length), the thigh turned onto the
    foot, the foot given its wanted turn."""
    I, n, sk = w.I, w.n, w.sk
    for s in "lr":
        th, ca, fo = I[f"thigh_{s}"], I[f"calf_{s}"], I[f"foot_{s}"]
        Gf, Pf = feet[s]
        G, Pp = w.g()
        a, b, cpos = Pp[:, th], Pp[:, ca], Pp[:, fo]
        l1 = float(np.linalg.norm(w.prest[ca] - w.prest[th]))
        l2 = float(np.linalg.norm(w.prest[fo] - w.prest[ca]))
        q = []
        for t in range(n):
            d = min(np.linalg.norm(Pf[t] - a[t]), (l1 + l2) * 0.9995)
            want = math.pi - math.acos(np.clip((l1 * l1 + l2 * l2 - d * d) / (2 * l1 * l2), -1, 1))
            u1, u2 = b[t] - a[t], cpos[t] - b[t]
            cur = math.acos(np.clip(np.dot(u1, u2) / np.linalg.norm(u1) / np.linalg.norm(u2), -1, 1))
            ax = np.cross(u1, u2)
            if np.linalg.norm(ax) < 1e-5 or cur < math.radians(2.0):
                ax = qrot(G[t, th], qrot(qinv(w.grest[th]), LAT))
            q.append(qaxis(ax, math.degrees(want - cur)))
        w.turn(ca, np.array(q), G)
        G, Pp = w.g()
        q = [qbetween(Pp[t, fo] - Pp[t, th], Pf[t] - Pp[t, th]) for t in range(n)]
        w.turn(th, np.array(q), G)
        G, _ = w.g()
        w.set_global(fo, Gf, G)
    _toes(w)


def _toes(w, floor=0.023):
    """(Round 2: through each foot's roll over its ball, w.pin, the toes keep the turn they had when the foot lay
    flat: planted.)"""
    I, n = w.I, w.n
    for s in "lr":
        pin = getattr(w, "pin", {}).get(s, [])
        if not pin:
            continue
        ba = I[f"ball_{s}"]
        G, _ = w.g()
        keep = G[pin[0], ba].copy()
        want = G[:, ba].copy()
        want[pin] = keep
        w.set_global(ba, want, G)
    _toes_floor(w, floor)


def _toes_floor(w, floor=0.023):
    """Each foot's toes bent up where they would go under the ground (her toe tips stand 2.3 cm up at rest), as
    they do at toe-off and through a flat stance."""
    I, n = w.I, w.n
    for s in "lr":
        fo, ba, lf = I[f"foot_{s}"], I[f"ball_{s}"], I[f"ball_leaf_{s}"]
        G, Pp = w.g()
        axl = qrot(qinv(w.grest[fo]), LAT)
        q = np.tile(np.array([0, 0, 0, 1.0]), (n, 1))
        for t in range(n):
            if Pp[t, lf, 1] >= floor:
                continue
            ax = qrot(G[t, fo], axl)
            v = Pp[t, lf] - Pp[t, ba]
            lo_, hi_ = -70.0, 0.0
            for _ in range(30):
                m = (lo_ + hi_) / 2
                if Pp[t, ba, 1] + qrot(qaxis(ax, m), v)[1] < floor:
                    hi_ = m
                else:
                    lo_ = m
            q[t] = qaxis(ax, lo_)
        w.turn(ba, q, G)


def _knees(w, spells, feet):
    """Stance knee angles [N] per side (nan off stance) and the swing foot's fore-aft lead over the stance one."""
    I = w.I
    G, Pp = w.g()
    out = {}
    for s in "lr":
        u1 = Pp[:, I[f"calf_{s}"]] - Pp[:, I[f"thigh_{s}"]]
        u2 = Pp[:, I[f"foot_{s}"]] - Pp[:, I[f"calf_{s}"]]
        k = np.degrees(np.arccos(np.clip(np.sum(u1 * u2, 1) / np.linalg.norm(u1, axis=1) / np.linalg.norm(u2, axis=1), -1, 1)))
        out[s] = k
    return out


def _passing(w, spells, feet):
    """Per frame: 1 near passing (the swing foot alongside the stance foot) for the stance side, as a weight."""
    n = w.n
    wts = {}
    for s, o in (("l", "r"), ("r", "l")):
        dz = feet[o][1][:, 2] - feet[s][1][:, 2]
        wt = np.zeros(n)
        for t in range(n):
            if spells[s][t] and not spells[o][t]:
                wt[t] = math.exp(-0.5 * (dz[t] / 0.12) ** 2)
        wts[s] = wt
    return wts


def _pelvis_height(w, c, spells, feet):
    """The pelvis raised where a stance knee passes its cap near passing, lowered for extra bend, dropped at heel
    contact; then the legs solved."""
    I, n = w.I, w.n
    pel = I["pelvis"]
    dy = np.zeros(n)
    # The hips' rise and fall (her_2's bob, 7-8 cm at the neck) scaled about its mean by c["bob"].
    if c["bob"] != 1.0:
        _, Pp = w.g()
        y = Pp[:, pel, 1]
        dy += (c["bob"] - 1.0) * (y - y.mean())
    # Drop at each heel contact (the first frames of a stance).
    if c["drop"]:
        for s in "lr":
            m = spells[s]
            st = [t for t in range(n) if m[t] and not m[t - 1]]
            for t0 in st:
                for k in range(-4, 9):
                    dy[(t0 + k) % n] -= c["drop"] * math.exp(-0.5 * ((k - 2) / 2.0) ** 2)
    if c["bend"]:
        # Lower so the mean stance knee bends c["bend"] more (found by trial).
        _legs(w, feet)
        k0 = _knees(w, spells, feet)
        m0 = np.mean([k0[s][spells[s]].mean() for s in "lr"])
        lo, hi = 0.0, 0.08
        for _ in range(14):
            mid_ = (lo + hi) / 2
            v = np.zeros((n, 3))
            v[:, 1] = -mid_
            w2 = Walk(w.rig, w.L, w.P, w.speed)
            w2.pin = w.pin
            w2.shift_pelvis(v)
            _legs(w2, feet)
            k1 = _knees(w2, spells, feet)
            m1 = np.mean([k1[s][spells[s]].mean() for s in "lr"])
            if m1 - m0 < c["bend"]:
                lo = mid_
            else:
                hi = mid_
        dy -= (lo + hi) / 2
    v = np.zeros((n, 3))
    v[:, 1] = dy
    w.shift_pelvis(v)
    # Height: each frame's pelvis between what the legs can reach (no straightened leg short of its foot) and what
    # caps the stance knee near passing; the shift smoothed between those bounds.
    pas = _passing(w, spells, feet)
    _legs(w, feet)
    G, Pp = w.g()
    lo, hi = np.full(n, -1.0), np.full(n, 1.0)
    for s in "lr":
        th, ca, fo = I[f"thigh_{s}"], I[f"calf_{s}"], I[f"foot_{s}"]
        l1 = float(np.linalg.norm(w.prest[ca] - w.prest[th]))
        l2 = float(np.linalg.norm(w.prest[fo] - w.prest[ca]))
        reach = (l1 + l2) * 0.998
        dcap = math.sqrt(l1 * l1 + l2 * l2 + 2 * l1 * l2 * math.cos(math.radians(c["knee"])))
        for t in range(n):
            hv = feet[s][1][t] - Pp[t, th]
            hor = hv[0] ** 2 + hv[2] ** 2
            if hor < reach * reach:
                hi[t] = min(hi[t], math.sqrt(reach * reach - hor) + hv[1])
            if pas[s][t] > 0.3 and hor < dcap * dcap:
                lo[t] = max(lo[t], math.sqrt(dcap * dcap - hor) + hv[1])
    lo = np.minimum(lo, hi)
    if DEBUG is not None and len(DEBUG) and DEBUG[0] == "h":
        DEBUG.append((lo.copy(), hi.copy()))
    dy = np.clip(np.zeros(n), lo, hi)
    for _ in range(40):
        dy = np.clip(_smooth(dy, 1.5), lo, hi)
    v = np.zeros((n, 3))
    v[:, 1] = dy
    w.shift_pelvis(v)
    _legs(w, feet)


# --------------------------------------------------------------- clearance --
NEAR = 0.004        # the arm's (below the armpit) least clearance from her skin and her own outfit (m), on her real mesh
_MEASURE = {}
DEBUG = []  # (a list with one item to collect: outfit, side, frame, near mm, along, part, skin mm)


def _mesh(outfit):
    if outfit not in _MEASURE:
        import motion
        from skin import Body
        m = motion.Measure(Body.heroine(jiggle=True), (outfit,))
        if outfit == "warden":  # the plate holds her springs (as motion.py's "plate" run)
            m.b.jiggle.amount, m.b.jiggle.squash = 0.55, 0.0
        _MEASURE[outfit] = m
    return _MEASURE[outfit]


def _near(w, c):
    """Per side, per frame: the forearm's and hand's least clearance (m, - into it) from the rest of her skin and
    from her own outfit, on her posed mesh with the springs run (as motion.py measures it)."""
    import skin
    m = _mesh(c["outfit"])
    cov = m.cover[c["outfit"]]
    clip = skin.Clip("walk", 30, np.concatenate([w.L, w.L[:1]]), np.concatenate([w.P, w.P[:1]]), True,
                     {"speed": float(w.speed)})
    Gs = m.b.frames(clip)
    out = {s: np.full(w.n, 0.08) for s in "lr"}
    for f in range(w.n):
        con = m.contact(m.b.pose(Gs[f]))
        for s in "lr":
            dist, along, hit, brst, nb = con[s]
            pts = m.arm[s][0]
            ok = np.isfinite(dist) & (along >= 0.35)  # (the armpit, where skin folds, kept apart as motion.py does)
            if ok.any():
                d = dist[ok]
                do = d - cov[pts[ok]] - cov[np.maximum(nb[ok], 0)]
                out[s][f] = min(float(d.min()), float(do.min()))
                if DEBUG:
                    i = int(np.argmin(np.minimum(d, do)))
                    hp = hit[ok][i]
                    DEBUG.append((c["outfit"], s, f, round(1000 * out[s][f]), round(float(along[ok][i]), 2), m.b.parts[hp] if hp >= 0 else "-", round(1000 * float(d[i]))))
    return out


def _clear(w, c, rounds=5):
    """Each arm let out from the shoulder only where (and as much as) the real mesh needs: the forearm and hand
    NEAR clear of her and her own outfit, the abduction capped at c["abd_cap"]."""
    I, n = w.I, w.n
    total = {s: np.zeros(n) for s in "lr"}
    for _ in range(rounds):
        near = _near(w, c)
        G, Pp = w.g()
        moved = False
        for s, sg in (("l", 1.0), ("r", -1.0)):
            _, ab, _ = _arm_angles(G, Pp, I, s)
            need = np.degrees(np.maximum(NEAR + 0.002 - near[s], 0.0) / 0.3)
            lo = np.minimum(need, np.maximum(c["abd_cap"] - ab, 0.0))
            add = lo.copy()
            for _k in range(6):
                add = np.maximum(_smooth(add, 1.0), lo)
            if add.max() > 0.05:
                moved = True
                w.turn(I[f"upperarm_{s}"], np.array([qaxis(FWD, sg * a) for a in add]), G)
                total[s] += add
        if not moved:
            break
    return total, _near(w, c)


# ------------------------------------------------------------------- make --
def make_walk(rig, calling):
    c = CALLINGS[calling]
    base = _base(rig)
    w, t0 = _cycle(rig, base, c["frames"])
    # The stride (and so the speed) carried by the feet.
    w.speed *= c["stride"]
    plain = Walk(rig, w.L, w.P, w.speed)
    fingers = _finger_pose(rig, w, c["fingers"])
    feet, spells = _feet(w, c, plain)
    pw = _passing(w, spells, feet)
    _trunk(w, c, pw["l"] + pw["r"])
    _arms(w, c, fingers)
    _pelvis_height(w, c, spells, feet)
    opened, near = _clear(w, c)
    L = np.concatenate([w.L, w.L[:1]])
    P = np.concatenate([w.P, w.P[:1]])
    name = f"walk_{calling}_town"
    meta = {"source": base.meta["source"], "licence": base.meta["licence"],
            "changes": "retargeted to her skeleton, looped from the left heel strike, retimed, stance feet laid flat and held, "
                       "stance knee capped, the arms re-made, the calling's carriage laid over (tools/anim/clips/walk_town.py)",
            "layer": "full", "speed": float(w.speed),
            "note": f"her town walk, {calling} (weapons sheathed, both arms free); loop starts at the left heel strike",
            "stance": {s: [int(t) for t in np.nonzero(spells[s])[0]] for s in "lr"}}
    _LAST[calling] = dict(opened=opened, near=near)
    return Clip(name, 30, L, P, loop=True, meta=meta)


def clips(rig, want):
    out = []
    for calling in CALLINGS:
        name = f"walk_{calling}_town"
        if not want or any(x in name for x in want):
            out.append(make_walk(rig, calling))
    return out
