"""flare_burns_twice: the arcanist's Flare, played at her own speed while the
world runs at 8%. Two seconds at 30 fps, laid over her captured standing
(idle_arcanist's base, run so its last frame is the idle's first):

- f0-f7 wind-up: the staff swung across and up in both hands to overhead,
  the left hand leaving her hip to take the shaft on the way; her left foot
  steps back half a metre and she rises on the balls of both feet, chest
  and shoulders lifting on the inhale.
- f7-f16 the poster: the staff overhead, a little diagonal (its head up to
  her left), both fists on it 25 cm apart, the elbows soft; heels up, the
  back leg long behind her in one line with the body, the back a little
  arched, chin up; a slow breath through it.
- f16-f20 the drive: the staff wheeled down to upright and driven into the
  ground beside her right foot (contact f20, both hands on it) as she drops
  into a deep lunge: the left foot shot back, its knee low, the right knee
  deep over the right foot, the hips 35 cm down, bent over the staff.
- f20-f43 the look up: from the lunge the chest lifts and the head goes
  back to the sky, one line from the back knee to the chin; the left hand
  lets go and opens to the falling embers; held, the head tracking a little.
- f40-f43 the sweep: the right hand sweeps the planted staff's head down
  and out to her right on the last impact (contact f43); then she rises,
  the left foot stepping through to its place, the staff lifted back to her
  side, and settles into idle_arcanist by f60 (the run may take over from
  f46).

The staff is held at its grip (Arms.Spec Grip 0.45 from the butt), so with
the butt on the ground her right fist is at most 0.79 m up, and a staff goes
square through the fist (the wrist bends 22 degrees to the thumb side,
38 to the little finger's): planted, the forearm is near level, so her right
shoulder can be little more than an upper arm above the fist. Standing she
can't plant it; in the lunge she can (the hips let down a little further
where the arm still needs it: `reach_drop`).

The staff's line in the right fist, the butt and the shaft (from
data/arms_local.json, mage_staff@hand_r): the shaft runs 6.6 degrees off the
mount's +Z toward the fingers; the left fist is laid on that line.
"""
from __future__ import annotations

import math

import numpy as np

from clips import idle
from clips.soul import arms_of
from keyed import Track, build
from rig import Clip, qinv, qmul, qrot, qslerp, qbetween

NAME = "flare_burns_twice"
END, CONTACT, SWEEP, BLEND = 60, 20, 43, 46

# The staff in hand_r's own space (the bound staff, seated on the fist's line by Arms.Seat: WeaponSockets.FistSeat).
M_R = np.array([-0.025, 0.075, 0.0])                 # the mount: the shaft through the right fist
BUTT = np.array([-0.0398, -0.0331, -0.7803])         # the butt's foot (on the shaft's line, 787.6 mm below the pocket)
AXIS = np.array([0.001, 0.1157, 0.9933])             # the shaft's line, butt toward head (the fist's line)
AXIS = AXIS / np.linalg.norm(AXIS)
SHAFT0 = np.array([-0.039, 0.058, 0.002])            # the shaft's centre where it crosses the fist (the fist's pocket)
LEFT_AT = 0.235                                      # the left fist this far up the shaft (m along it)
# The left fist's pocket (the mirror of the right's: her left hand's +X is
# across the palm, her right's across the back).
M_L = np.array([0.039, 0.058, 0.002])


def _n(*v):
    v = np.array(v, float)
    return v / np.linalg.norm(v)


def _smooth(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def _shifted_base(base, end=END):
    """The captured standing run so that frame `end` is its frame 0 (the
    idle's first), the frames before it the loop's last."""
    n = base.frames - 1  # the loop's last frame is its first again
    idx = [(fr - end) % n for fr in range(end + 1)]
    return Clip(f"{NAME}_base", base.fps, base.rot[idx], base.pos[idx], loop=False, meta=dict(base.meta))


def _euler(q):
    """(yaw, pitch, roll) for qeuler from a turn (Ry * Rx * Rz)."""
    R = np.stack([qrot(q, e) for e in np.eye(3)], axis=1)
    b = math.degrees(math.asin(max(-1.0, min(1.0, -R[1, 2]))))
    a = math.degrees(math.atan2(R[0, 2], R[2, 2]))
    c = math.degrees(math.atan2(R[1, 0], R[1, 1]))
    return (a, b, c)


def _stand(rig, base):
    """Each foot as it stands in the idle (the base's last frame, the idle's
    first): its turn (yaw, pitch, roll) and its ball."""
    g, p = rig.sk.fk(base.rot[END][None], base.pos[END][None])
    I = rig.I
    out = {}
    for s in "lr":
        fo, ba = I[f"foot_{s}"], I[f"ball_{s}"]
        out[s] = _euler(qmul(g[0, fo], qinv(rig.grest[fo]))) + (p[0, ba].copy(),)
    return out


# ----------------------------------------------------------------- feet --
# Each foot keyed by its ball: (frame, the ball's offset from where it
# stands in the idle (x, z), lift (degrees up on the ball: the heel raised,
# the toes flat on the ground), arc (how high the ball is carried on its way
# to this key)). Between keys where the ball stays it stays exactly (the
# heel rising and falling about it). The right foot is the lunge's lead and
# never leaves its place; the left steps back for the poster, shoots back
# into the lunge on the drive, and steps through to its place on the rise.
FOOT_R = [(0, (0.0, 0.0), 0, 0), (3, (0.0, 0.0), 10, 0), (7, (0.0, 0.0), 24, 0), (16, (0.0, 0.0), 24, 0),
          (19, (0.0, 0.0), 0, 0), (END, (0.0, 0.0), 0, 0)]
FOOT_L = [(0, (0.0, 0.0), 0, 0), (1, (0.0, 0.0), 8, 0), (6, (-0.01, -0.45), 34, 0.05), (16, (-0.01, -0.45), 34, 0),
          (CONTACT, (-0.03, -0.95), 55, 0.025), (SWEEP + 1, (-0.03, -0.95), 55, 0), (BLEND, (-0.03, -0.95), 64, 0),
          (54, (0.0, 0.0), 0, 0.07), (END, (0.0, 0.0), 0, 0)]


def _foot_at(keys, fr):
    """The ball's offset (x, height, z) and the lift at frame fr."""
    for a, b in zip(keys, keys[1:]):
        if a[0] <= fr <= b[0]:
            u = (fr - a[0]) / (b[0] - a[0])
            s = _smooth(u)
            off = np.array(a[1]) + (np.array(b[1]) - np.array(a[1])) * s
            lift = a[2] + (b[2] - a[2]) * s
            h = b[3] * math.sin(math.pi * u) if a[1] != b[1] else 0.0
            return np.array([off[0], h, off[1]]), lift
    return np.array([keys[-1][1][0], 0.0, keys[-1][1][1]]), keys[-1][2]


# ------------------------------------------------------------------ body --
def _body_keys():
    def k(fr, ease="auto", hips=(0, 0, 0), hrot=(0, 0, 0), spine=(0, 0, 0), neck=(0, 0, 0), head=(0, 0, 0),
          cl=(0, 0), cr=(0, 0)):
        return (fr, {"hips": {"pos": hips, "rot": hrot}, "spine": spine, "neck": neck, "head": head,
                     "clav_l": cl, "clav_r": cr}, ease)
    return [
        k(0, "ease"),
        # A dip into it, the weight onto her right foot as the left steps back.
        k(3, "auto", hips=(-0.03, -0.02, -0.06), spine=(0, 4, 0), head=(0, 2, 0), cl=(3, 2), cr=(3, 2)),
        # The poster: up on the balls of her feet, the back leg long behind,
        # the back a little arched, chin up; the breath in it (f12 the top of
        # the inhale).
        k(7, "auto", hips=(-0.01, 0.004, -0.19), hrot=(0, -3, 0), spine=(0, -8, 0), neck=(0, -3, 0), head=(0, -9, 0),
          cl=(8, 0), cr=(8, 0)),
        k(12, "auto", hips=(-0.01, 0.01, -0.20), hrot=(0, -3, 0), spine=(0, -10, 0), neck=(0, -3, 0), head=(0, -11, 0),
          cl=(10, 0), cr=(10, 0)),
        # The drive: wheeled down, dropping into the lunge, bent over the
        # staff. The head's bow is capped near 20 degrees (world) and the
        # rest of the bow is the chest's; the swing from the poster to the
        # bow is spread over f14-19 (the chest and head leaving together).
        k(14, "auto", hips=(-0.01, 0.005, -0.20), hrot=(0, -3, 0), spine=(0, -10, 0), neck=(0, -4, 0), head=(0, -9, 0),
          cl=(9, 0), cr=(9, 0)),
        k(15, "auto", hips=(-0.012, -0.015, -0.21), hrot=(0, -3, 0), spine=(0, -7, 0), neck=(0, -3, -2), head=(0, -8, -1),
          cl=(9, 0), cr=(9, 0)),
        k(16, "auto", hips=(-0.014, -0.05, -0.23), hrot=(0, -3, 0), spine=(0, -1, 0), neck=(0, -2, -4), head=(0, -4, -2),
          cl=(9, 0), cr=(9, 0)),
        k(17, "auto", hips=(-0.017, -0.095, -0.25), hrot=(-1.5, 3, 1), spine=(-4, 7, 1), neck=(0, -1, -8), head=(0, -2, -4),
          cl=(5, 6), cr=(3, 1.5)),
        k(18, "auto", hips=(-0.02, -0.15, -0.27), hrot=(-3, 8, 2), spine=(-9, 14, 2), neck=(0, 1, -13), head=(0, 3, -7),
          cl=(2, 12), cr=(-2, 3)),
        k(19, "auto", hips=(-0.025, -0.225, -0.30), hrot=(-3.5, 12, 2.5), spine=(-12.5, 18, 2), neck=(0, 0, -32), head=(0, 5, -12),
          cl=(1, 16), cr=(-6, 3.5)),
        k(CONTACT, "ease", hips=(-0.03, -0.33, -0.33), hrot=(-4, 16, 3), spine=(-16, 19, 2), neck=(0, -3, -20), head=(0, 1, -3),
          cl=(0, 20), cr=(-10, 4)),
        # The settle: the weight lands, the pelvis 2-3 cm lower and the chest
        # a few degrees further over than the pose it comes back to (f25).
        k(21, "auto", hips=(-0.03, -0.39, -0.33), hrot=(-2, 15, 3), spine=(-8, 21, 3), neck=(0, -3, -22), head=(0, -2, -3),
          cl=(1, 12), cr=(-10, 4)),
        k(22, "auto", hips=(-0.03, -0.395, -0.33), hrot=(-1, 14.5, 3), spine=(-4, 17, 4), neck=(0, -2, -22), head=(0, -1, -5),
          cl=(2, 6), cr=(-10, 3.5)),
        # The look up: the chest lifted and the head back to the sky, deep in
        # the lunge (the staff is planted and the fist low), the body in one
        # line on from the back thigh, the chest turned a little open to her
        # left where her hand opens.
        k(23, "auto", hips=(-0.03, -0.38, -0.33), hrot=(0, 14, 3), spine=(-2, 8, 5), neck=(0, 0, -16), head=(0, 10, -6),
          cl=(3, 2), cr=(-10, 3)),
        # One line from the hips to the head: the hips thrust forward, the
        # chest arched back (and rising a few degrees through the hold), the
        # neck taking only its share of the head's tilt.
        k(28, "ease", hips=(-0.03, -0.37, -0.26), hrot=(2, 15, 2), spine=(6, -27, 5), neck=(0, -4, 0),
          head=(4, -7, 0), cl=(8, 0), cr=(-10, 4)),
        k(34, "auto", hips=(-0.03, -0.37, -0.255), hrot=(2, 15, 2), spine=(6, -29, 5), neck=(0, -4, 0),
          head=(7, -8, 2), cl=(9, 0), cr=(-10, 4)),
        k(40, "ease", hips=(-0.03, -0.37, -0.255), hrot=(2, 15, 2), spine=(6, -31, 5), neck=(0, -4, 0),
          head=(-3, -6, -1), cl=(8, 0), cr=(-10, 4)),
        # The sweep: the planted staff's head swept out to her right.
        k(SWEEP, "auto", hips=(-0.07, -0.35, -0.28), hrot=(0, 12, 3), spine=(0, -6, 10), neck=(0, -4, 0),
          head=(0, -12, 0), cl=(4, 0), cr=(-12, 2)),
        # Up out of it, the left foot stepping through, back into her standing.
        k(BLEND, "auto", hips=(-0.03, -0.22, -0.20), hrot=(-2, 5, 1), spine=(-3, 2, 3), head=(0, -5, 0),
          cl=(2, 0), cr=(-4, 0)),
        k(50, "auto", hips=(-0.03, -0.09, -0.08), spine=(0, 2, 0), head=(0, -2, 0)),
        k(54, "auto", hips=(0, -0.02, -0.01), spine=(0, 1, 0), head=(0, -1, 0)),
        k(END, "ease"),
    ]


# ----------------------------------------------------------------- staff --
# The staff's path in her space: (frame, anchor, point, shaft's way butt to
# head, right elbow's way). anchor "grip": the shaft's point in the fist at
# `point`; "butt": the butt's foot at `point` (planted).
BUTT_AT = np.array([-0.40, 0.004, -0.17])  # beside her right foot (the lunge's lead), by its heel
STAFF = [
    (3, "grip", (-0.17, 1.40, 0.36), _n(0.75, 0.62, 0.15), (-0.9, -0.4, -0.2)),
    (5, "grip", (-0.13, 1.70, 0.12), _n(0.95, 0.30, 0.05), (-1.0, 0.0, 0.1)),
    (7, "grip", (-0.11, 1.89, -0.21), _n(0.996, 0.087, 0.0), (-1.0, 0.2, 0.3)),
    (12, "grip", (-0.11, 1.90, -0.22), _n(0.996, 0.087, 0.0), (-1.0, 0.2, 0.3)),
    (15, "grip", (-0.11, 1.91, -0.21), _n(0.996, 0.087, 0.0), (-1.0, 0.2, 0.3)),
    # The drive: the staff wheeled about the middle of her two fists (its
    # head up, its butt down at her right), down in front of her face and
    # out of its way, then driven straight down into the ground. The right
    # elbow keyed by its way from the shoulder (E): forward, then down, the
    # forearm out-forward to the planted staff.
    (16, "grip", (-0.13, 1.93, -0.15), _n(1.0, 0.07, -0.05), (-1.0, 0.0, 0.4)),
    (17, "grip", (-0.20, 1.60, 0.10), _n(0.90, 0.44, -0.08), _n(0.1, -0.2, 0.9), "E"),
    (18, "grip", (-0.32, 1.32, 0.20), _n(0.56, 0.83, -0.04), _n(-0.1, -0.6, 0.7), "E"),
    (19, "grip", (-0.41, 1.00, -0.06), _n(0.15, 0.99, 0.04), _n(-0.35, -0.9, 0.1), "E"),
    # Planted the fist's +Z is keyed (the staff's own line is AXIS in it,
    # 6.6 degrees toward the fingers, which face out to her right here): so
    # the shaft stands about (-0.05, 0.99, 0.10), near upright, its head over
    # the butt and the left fist within her reach.
    (CONTACT, "butt", BUTT_AT, _n(0.0, 1.0, 0.04), _n(0.15, -0.97, -0.10), "E"),
    (22, "butt", BUTT_AT, _n(0.0, 1.0, 0.04), _n(0.15, -0.97, -0.10), "E"),
    (28, "butt", BUTT_AT, _n(0.03, 1.0, 0.03), _n(0.15, -0.97, -0.10), "E"),
    (40, "butt", BUTT_AT, _n(0.02, 1.0, 0.03), _n(0.15, -0.97, -0.10), "E"),
    (SWEEP, "butt", BUTT_AT, _n(-0.24, 0.96, 0.14), (-0.6, -0.8, -0.4)),
    (BLEND, "grip", (-0.40, 0.98, -0.14), _n(-0.08, 0.99, 0.10), (-0.8, -0.3, -0.6)),
    (52, "grip", (-0.33, 1.12, -0.06), _n(-0.03, 1.0, 0.14), (-0.8, -0.3, -0.6)),
]
# Through the drive the fist turns on one even turn from its last poster
# frame to its plant (as last solved), this far along at each frame: the
# staff wheels in her front plane and the fist rolls no more than it must.
DRIVE_U = {16: 0.1, 17: 0.32, 18: 0.64, 19: 0.94}
# How much of the hand is the path's (the rest the idle's own arm; done
# with by f56 so the idle's own elbow is settled by the seam).
R_ON = [(0, 0.0), (3, 1.0), (51, 1.0), (56, 0.0)]
# The left hand: on the shaft from f5 through the contact, letting go over
# f21-30 (turned evenly from its hold on the shaft to its opening: RELEASE,
# OPEN), open to the embers, back to the idle by f54.
L_SHAFT = [(1, 0.0), (5, 1.0), (CONTACT + 1, 1.0), (30, 0.0)]
L_OPEN = [(CONTACT + 1, 0.0), (30, 1.0), (SWEEP + 2, 1.0), (54, 0.0)]
RELEASE, OPEN = CONTACT + 1, 31
FINGER_OPEN_AT = {"thumb": 23.5, "index": 23.5, "middle": 24.5, "ring": 25.5, "pinky": 26.5}
L_OPEN_ARC = (0.35, -0.20, -0.13)      # from the left shoulder, in the chest's frame (hangs about 25 deg low, 20 behind)
AIM_LET_GO = 1.0                       # how far the hand stops being aimed at mid-release
L_BUMP = (0.15, 0.12, 0.30)                # the way round, in the chest's frame
L_REACH = (0.06, 0.02, 0.16)               # the reach to the shaft goes out in front of her breast, not through it
L_OPEN_KNUCKLES = _n(0.55, 0.55, 0.6)  # the fingers out and up, the palm up to the sky


def _curve(keys, fr):
    """A weight through (frame, value) keys, eased between them."""
    if fr <= keys[0][0]:
        return keys[0][1]
    for (f0, v0), (f1, v1) in zip(keys, keys[1:]):
        if fr <= f1:
            return v0 + (v1 - v0) * _smooth((fr - f0) / (f1 - f0))
    return keys[-1][1]


def _staff_at(fr):
    """The staff's key either side of fr and how far between (drive: eased
    in, so it lands moving)."""
    for a, b in zip(STAFF, STAFF[1:]):
        if a[0] <= fr <= b[0]:
            u = (fr - a[0]) / (b[0] - a[0])
            if a[0] in (15, 16, 17, 18, 19):
                pass                    # the drive: keyed every frame
            elif a[0] == SWEEP:
                u = 1 - (1 - u) ** 2    # off the ground fast
            else:
                u = _smooth(u)
            return a, b, u
    return (STAFF[0], STAFF[0], 0.0) if fr < STAFF[0][0] else (STAFF[-1], STAFF[-1], 0.0)


def _slerp_dir(a, b, u):
    q = qbetween(a, b)
    return qrot(qslerp(np.array([0, 0, 0, 1.0]), q, u), a)


class Flare:
    def __init__(self, rig):
        self.rig = rig
        self.base = _shifted_base(idle.base_of(rig, "arcanist"))
        self.stand = _stand(rig, self.base)
        self.keys = _body_keys()
        self.track = Track(self.keys)
        self.n = END + 1
        self.dy = np.zeros(self.n)
        # The hands' turns as solved last (for the anchors), and the poses.
        self.Rr = None
        self.Rl = None
        self.idle = arms_of("arcanist")

    # -- the body alone (shoulders, chest) at each frame
    def body(self):
        rig, I = self.rig, self.rig.I
        S_r, S_l, chest, E_r = [], [], [], []
        for fr in range(self.n):
            pose = self.track(fr)
            pose = dict(pose, hips=dict(pose["hips"], pos=self._hips(pose, fr)))
            b = (self.base.rot[fr], self.base.pos[fr])
            local, pos = rig.solve(pose, base=b)
            g, p = rig.sk.fk(local[None], pos[None])
            S_r.append(p[0, I["upperarm_r"]])
            S_l.append(p[0, I["upperarm_l"]])
            E_r.append(p[0, I["lowerarm_r"]])
            s3 = I["spine_03"]
            chest.append(qmul(g[0, s3], qinv(rig.grest[s3])))
        self.E_r = np.array(E_r)
        return np.array(S_r), np.array(S_l), np.array(chest)

    def _hips(self, pose, fr):
        h = pose.get("hips", {}).get("pos", (0, 0, 0))
        return (h[0], h[1] + self.dy[fr], h[2])

    def foot(self, s, fr):
        """Foot s at frame fr as a keyed foot: its ball where FOOT_L/FOOT_R
        put it, up on it by the keyed lift (the toes flat on the ground)."""
        from rig import qeuler
        rig, I = self.rig, self.rig.I
        off, lift = _foot_at(FOOT_L if s == "l" else FOOT_R, fr)
        yaw, pitch, roll, ball0 = self.stand[s]
        fo, ba = I[f"foot_{s}"], I[f"ball_{s}"]
        ball = ball0 + off
        q = qeuler(yaw, pitch + lift, roll)
        ankle = ball - qrot(q, rig.prest[ba] - rig.prest[fo])
        return {"pos": (float(ankle[0]), float(ankle[1] - rig.prest[fo][1]), float(ankle[2])),
                "rot": (yaw, pitch + lift, roll), "toe": float(lift), "pole": ((0.15 if s == "l" else -0.15), 0, 1.0)}

    # -- the right hand's wanted wrist and blade at each frame
    def right(self, S_r, chest):
        out = []
        idle_r = self.idle["hand_r"]
        v_idle = np.array(_arc_vec(idle_r["arc"]))
        for fr in range(self.n):
            a, b, u = _staff_at(fr)
            d = _slerp_dir(a[3], b[3], u)
            R = self.Rr[fr] if self.Rr is not None else None
            if a[1] == "butt" and b[1] == "butt":
                anchor, point = BUTT, np.array(BUTT_AT)
                W = point - (qrot(R, anchor) if R is not None else -0.79 * d)
            else:
                pa = self._wrist_of(a, fr, R)
                pb = self._wrist_of(b, fr, R)
                W = pa + (pb - pa) * u
            kn = None
            # The elbow's way: a pole from where the arm hangs, or (E) the
            # elbow's way from the shoulder; laid between keys as ways from
            # the shoulder, then given back as a pole.
            hang = self.E_r[fr] - S_r[fr]
            va = np.array(a[4]) if len(a) > 5 else hang + np.array(a[4])
            vb = np.array(b[4]) if len(b) > 5 else hang + np.array(b[4])
            pole = (va + (vb - va) * u) - hang
            if fr in DRIVE_U and self.Rr is not None:
                qa, qb = self.Rr[15], self.Rr[CONTACT]
                q = qslerp(qa, -qb if float(np.dot(qa, qb)) < 0 else qb, DRIVE_U[fr])
                d = qrot(q, np.array([0, 0, 1.0]))
                kn = qrot(q, np.array([0, 1.0, 0]))
            w = _curve(R_ON, fr)
            if w < 1.0:
                Wi = S_r[fr] + qrot(chest[fr], v_idle)
                bi = qrot(chest[fr], np.array(idle_r["blade"], float))
                pi = qrot(chest[fr], np.array(idle_r["pole"], float))
                W = Wi + (W - Wi) * w
                d = _slerp_dir(bi / np.linalg.norm(bi), d, w)
                pole = pi + (pole - pi) * w
            spec = {"pos": tuple(float(x) for x in W), "blade": tuple(float(x) for x in d), "frame": "char",
                    "pole": tuple(float(x) for x in pole), "twist": 0.5}
            if kn is not None:
                spec["knuckles"] = tuple(float(x) for x in kn)
            out.append(spec)
        return out

    def _wrist_of(self, key, fr, R):
        """The wrist that puts the key's anchor at its point (with the hand
        turned as last solved at this frame)."""
        anchor = BUTT if key[1] == "butt" else M_R
        p = np.array(key[2], float)
        if R is None:
            return p - (0.79 * -key[3] if key[1] == "butt" else 0.0)
        return p - qrot(R, anchor)

    # -- the left hand at each frame (on the shaft as last solved)
    def left(self, S_l, chest, G):
        rig, I = self.rig, self.rig.I
        idle_l = self.idle["hand_l"]
        v_idle = np.array(_arc_vec(idle_l["arc"]))
        out = []
        for fr in range(self.n):
            ws, wo = _curve(L_SHAFT, fr), _curve(L_OPEN, fr)
            if G is None:
                ws = 0.0  # (the first round: no staff yet to hold)
            wi = max(0.0, 1.0 - ws - wo)
            Wi = S_l[fr] + qrot(chest[fr], v_idle)
            ki = qrot(chest[fr], np.array(idle_l["knuckles"], float))
            pole_i = qrot(chest[fr], np.array(idle_l["pole"], float))
            Wo = S_l[fr] + qrot(chest[fr], np.array(L_OPEN_ARC))
            ko = qrot(chest[fr], L_OPEN_KNUCKLES)
            pole_o = qrot(chest[fr], np.array((0.9, -0.5, -0.3)))
            spec = {"frame": "char", "twist": 0.4}
            # The hand goes round her front (out and forward) between the
            # shaft and the open hand, and between the open hand and the idle,
            # not through her breast and ribs.
            bump = qrot(chest[fr], np.array(L_BUMP)) * math.sin(math.pi * min(1.0, wo)) if wo < 1.0 else 0.0
            if 0.0 < ws < 1.0 and fr < CONTACT:
                bump = bump + qrot(chest[fr], np.array(L_REACH)) * math.sin(math.pi * ws)
            if ws > 0:
                qr, pr = G[0][fr], G[1][fr]
                on = pr + qrot(qr, SHAFT0 + AXIS * LEFT_AT)
                dw = qrot(qr, AXIS)
                Rl = self.Rl[fr] if self.Rl is not None else None
                Ws = on - (qrot(Rl, M_L) if Rl is not None else 0.0)
                k = _smooth((fr - 16) / 3.0)
                pole_s = np.array((0.6, -0.3, 0.8)) * (1 - k) + np.array((0.9, -0.3, -0.4)) * k
                # Letting go across her front: the elbow up and back, so the
                # forearm clears her breasts as the hand comes away.
                k2 = _smooth((fr - 18) / 8.0)
                pole_s = pole_s * (1 - k2) + np.array((0.3, 0.8, -0.4)) * k2
                W = Wi * wi + Ws * ws + Wo * wo + bump
                pole = pole_i * wi + pole_s * ws + pole_o * wo
                if wo > 0 and self.Rl is not None:
                    # Letting go: turned evenly from its hold on the shaft to
                    # how it opens (both as last solved).
                    q = qslerp(self.Rl[RELEASE], self.Rl[OPEN], wo)
                    spec["blade"] = tuple(float(x) for x in qrot(q, np.array([0, 0, 1.0])))
                    spec["knuckles"] = tuple(float(x) for x in qrot(q, np.array([0, 1.0, 0])))
                    # Letting go the hand rides the forearm a little, so the
                    # elbow can go up and back (clear of her breast).
                    spec["aim"] = 1.0 - AIM_LET_GO * math.sin(math.pi * wo)
                else:
                    spec["blade"] = tuple(float(x) for x in dw)
                    # The fist's long way across the shaft: from her shoulder
                    # to the shaft (fixed, so the fist does not roll round the
                    # shaft as the elbow settles, and its channel stays on it).
                    kn = on - S_l[fr]
                    kn = kn - dw * float(np.dot(kn, dw))
                    spec["knuckles"] = tuple(float(x) for x in kn / np.linalg.norm(kn))
                    if ws < 1.0:
                        spec["aim"] = ws
            else:
                W = Wi + (Wo - Wi) * wo + bump
                k = _slerp_dir(ki / np.linalg.norm(ki), ko / np.linalg.norm(ko), wo)
                spec["knuckles"] = tuple(float(x) for x in k)
                pole = pole_i + (pole_o - pole_i) * wo
            spec["pos"] = tuple(float(x) for x in W)
            spec["pole"] = tuple(float(x) for x in pole)
            out.append(spec)
        return out

    def fingers(self, fr):
        if CONTACT + 1 <= fr <= 30:
            # Letting go: each finger opens on its own window (thumb with the
            # index, then middle, ring, little a frame apart), 3 frames each.
            rel, grip, spread = finger_mix()
            u = {k: _smooth((fr - s0) / 3.0) for k, s0 in FINGER_OPEN_AT.items()}
            mix = lambda key, w: grip[key] * (1 - w) + spread[key] * w
            f = {"curl": mix("curl", u["middle"]), "index": mix("curl", u["index"]), "thumb": mix("thumb", u["thumb"]),
                 "spread": mix("spread", u["index"]),
                 "cascade": mix("cascade", u["middle"]) + 0.25 * math.sin(math.pi * u["middle"])}
            return f
        g = _curve(L_SHAFT, fr)
        o = _curve(L_OPEN, fr)
        rel, grip, spread = finger_mix()
        f = {k: rel[k] * (1 - g - o) + grip[k] * g + spread[k] * o for k in rel}
        return f

    def solve(self, HR, HL):
        def post(fr, pose):
            p = dict(pose)
            p["hips"] = dict(p["hips"], pos=self._hips(p, fr))
            p["hand_r"], p["hand_l"] = HR[fr], HL[fr]
            p["foot_l"], p["foot_r"] = self.foot("l", fr), self.foot("r", fr)
            p["fingers_r"] = "grip"
            p["fingers_l"] = self.fingers(fr)
            return p
        meta = {"layer": "full", "weapon": "staff", "contact": CONTACT / 30, "contacts": [CONTACT / 30, SWEEP / 30],
                "blend_out": BLEND / 30}
        return build(NAME, self.rig, self.keys, meta=meta, post=post, base=self.base)

    def hands_of(self, clip):
        rig = self.rig
        g, p = rig.sk.fk(clip.rot, clip.pos)
        hr, hl = rig.I["hand_r"], rig.I["hand_l"]
        Rr = [qmul(g[f, hr], np.array([0, 0, 0, 1.0])) for f in range(self.n)]
        Rl = [g[f, hl] for f in range(self.n)]
        # Relaxed, half way from the last round's to this one's: left whole,
        # the drive's f17 fist flipped between two settings round by round.
        if self.Rr is not None:
            Rr = [qslerp(o, -n if float(np.dot(o, n)) < 0 else n, 0.5) for o, n in zip(self.Rr, Rr)]
            Rl = [qslerp(o, -n if float(np.dot(o, n)) < 0 else n, 0.5) for o, n in zip(self.Rl, Rl)]
        self.Rr, self.Rl = Rr, Rl
        return (g[:, hr], p[:, hr]), (g[:, hl], p[:, hl])

    def reach_drop(self, S_r, HR, top=0.425, over=0.265):
        """The hips let down where the right fist (on the planted staff) is
        further from the shoulder than a soft-elbowed arm reaches, or the
        shoulder higher over it than a hanging upper arm and a near-level
        forearm allow (`over`)."""
        need = np.zeros(self.n)
        for fr in range(CONTACT, SWEEP + 1):  # only while the staff is planted
            W = np.array(HR[fr]["pos"])
            d = W - S_r[fr]
            h = math.hypot(d[0], d[2])
            dn = 0.0
            if np.linalg.norm(d) > top and h < top:
                # the shoulder lowered by dy so that |W - S| = top
                dn = d[1] + math.sqrt(top * top - h * h)
            need[fr] = max(-0.06, min(0.0, dn, over + d[1]))
        # Eased, never sudden (a Gaussian, the deepest kept).
        k = np.exp(-0.5 * (np.arange(-6, 7) / 2.5) ** 2)
        k /= k.sum()
        pad = np.pad(need, 6, mode="edge")
        sm = np.convolve(pad, k, mode="valid")
        return np.minimum(sm, need)


def _arc_vec(arc):
    az, el, r = arc
    return (math.sin(math.radians(az)) * math.cos(math.radians(el)) * r, math.sin(math.radians(el)) * r,
            math.cos(math.radians(az)) * math.cos(math.radians(el)) * r)


def finger_mix():
    from keyed import FINGER_PRESETS
    keys = ("curl", "thumb", "spread", "cascade")

    def full(p):
        p = FINGER_PRESETS[p]
        return {k: float(p.get(k, 0.0)) for k in keys}
    return full("relaxed"), full("grip"), full("spread")


def flare_burns_twice(rig, rounds=10, log=None):
    F = Flare(rig)
    clip = None
    G = None
    for r in range(rounds):
        S_r, S_l, chest = F.body()
        HR = F.right(S_r, chest)
        if r == 1:
            F.dy = F.dy + F.reach_drop(S_r, HR)
            S_r, S_l, chest = F.body()
            HR = F.right(S_r, chest)
        HL = F.left(S_l, chest, G)
        clip = F.solve(HR, HL)
        G, _ = F.hands_of(clip)
        if log:
            log(r, F, clip)
    _settle(rig, F, clip)
    return clip


def _settle(rig, F, clip, a=50, b=56):
    """Her right arm eased over f50-56 into the idle's own (solved here over
    the idle's frames about its first, as idle_arcanist solves them), and her
    toes into her standing's, so the last frame is idle_arcanist's first."""
    from keyed import solve_frames
    base = idle.base_of(rig, "arcanist")
    n = base.frames - 1
    lo = a - 6
    idx = [(fr - END) % n for fr in range(lo, END + 7)]
    rot, _ = solve_frames(rig, [idle.arcanist(0, 0) for _ in idx], [(base.rot[k], base.pos[k]) for k in idx],
                          loop=False, weapon="staff")
    I, sk = rig.I, rig.sk
    arm = [I["upperarm_r"]]
    for j in arm:
        arm += [k for k, p in enumerate(sk.parent) if p == j and k not in arm]
    toes = [I["ball_l"], I["ball_r"]]
    for fr in range(a, END + 1):
        w = _smooth((fr - a) / (b - a))
        for j in arm:
            clip.rot[fr, j] = qslerp(clip.rot[fr, j], rot[fr - lo, j], w)
        for j in toes:
            clip.rot[fr, j] = qslerp(clip.rot[fr, j], F.base.rot[fr, j], _smooth((fr - 52) / 8))


def clips(rig, want):
    if want and not any(w in NAME for w in want):
        return []
    return [flare_burns_twice(rig)]
