"""flare_long_cut: the Warden Sunderer's Flare "The Long Cut" (docs/design/FLARE_LOOK.md), her only, two-handed with her
greatsword sunder_blade (Arms; the game mounts it in her right fist for the clip, PersonView.FlareGrip). 80 frames at
30 fps on the Flare's clock, laid over her warden standing (idle_warden's base, run so the last frame is the idle's
first). In the game the root faces the cleave line: +z below is down the line, +x her left. The times are frozen with
the VFX (VFX 9): the sweep ~0.20 s, the cleave's contact 0.545 s, the seam cooled 1.95 s.

- f0-6 THE COIL: her left hand joins the grip by f3 (above the right, toward the pommel); her right foot steps back
  0.36 m, both knees bent, the hips down and back over it; one long twist (pelvis 40 deg to her right, chest 75), her
  left shoulder down the line, the head turned back to look down it. The blade low behind her right side, its tip
  about 0.3 m off the ground a metre behind her, held tightening f5-6.
- f6-9 THE RISE: the twist unwinds and her fists go up her right side and over her head, the blade trailing; she
  rises onto the ball of her back foot.
- f9-13 THE ARCH: the arms long overhead, the blade behind her head, its tip 25-31 deg below level behind her; the
  back arched, the weight coming forward, eyes down the line; a small further drift back (the hang).
- f13-16.5 THE CLEAVE: the blade whips over and down the line (keyed every frame) as she drops: her left foot plants
  forward, her right knee going down. The tip meets the ground about 0.96 m ahead on the line at ~f16.5 (0.55 s).
- f16-24 THE KNEEL lands (the knee down by f20): right knee on the ground, toes tucked; left foot forward, its knee up;
  the blade near upright (87 deg down), its tip 0.2 m in the seam 0.56 m ahead; both fists on the grip at chest
  height, the right under the guard, the left above it; chest up, the back straight, the head bowed (a knight's kneel).
- f25-57 the kneel held, sat up (the chest back over the hips), two breaths; the head lifts f48-57 to look down the seam.
- f57-72 the recovery: the blade drawn out (the tip clear by f62), she rises, the right foot stepping through to its
  place, then the left; her left hand lets go (f64-68) and her right carries the blade down to her side.
- f72-80 eased into idle_warden's frame 0 (every joint).

The grip (WeaponSockets BladeAtR / BladeDirR, the Blade1H fist: sunder_blade's grip is that section): the right fist is
the prop's mount; the clip keys the right fist's pocket point P and the blade's way d, and puts the left fist's pocket
(the right's mirrored, MirrorRL) on the blade's line 0.170 m toward the pommel, its fist turned so its own line is the
blade's and its edge the blade's edge (the mirrored grip of a two-hander), from the right hand as last solved.
"""
from __future__ import annotations

import math

import numpy as np

from clips import idle
from clips.flare import _n, _smooth, _euler, _foot_at, _curve, _slerp_dir
from clips.soul import arms_of
from keyed import Track, build, _socket_vec, _axis_matrix, finger_curl, grip_of, WRAP, WRAP_TILT
from rig import Clip, qaxis, qinv, qmul, qrot, qslerp, qbetween, qeuler, qfrom_basis

NAME = "flare_long_cut"
END = 80
CONTACT_T = 0.545
LAND = 20
SETTLE = 72

# The right fist's pocket (hand_r space) and the grip's line in it, pommel toward blade; the edge's way (the piece's +X).
# grip_tilt (animation 58, the clip's meta): the blade turned TILT deg in her fist about hand_r +X through the pocket, toward
# a square two-handed grip (the fist fitted for it: WRAP_TILT["sunder"], the blade's); the game turns the seated piece so.
TILT = 0.0   # (tried 30: the kneel's contact pose out of her wrists' reach; animation 59 r2)
_RT = _axis_matrix([1.0, 0, 0], TILT)
GRIP_LEAN = grip_of("sunder", TILT)["r"]   # the hand turned back from the keyed blade by the grip's lean (Rig.solve)
AT = _socket_vec("BladeAtR")
DIR0 = _socket_vec("BladeDirR") / np.linalg.norm(_socket_vec("BladeDirR"))
DIR = _RT @ DIR0
EDGE = _RT @ np.array([0.0, DIR0[2], -DIR0[1]])
# hand_r to hand_l (WeaponSockets.MirrorRL).
MIRROR = np.array([[-0.999976, 0.006672, 0.001970], [0.006660, 0.999958, -0.006359], [0.002012, 0.006345, 0.999978]])
AT_L, DIR_L, EDGE_L = MIRROR @ AT, MIRROR @ DIR, MIRROR @ EDGE
# Each elbow's way smoothed over a narrower window than the default 2 frames: the elbows are keyed per beat, and the
# cleave turns the blade 120 deg in two frames (at 2, f15-f16 were pulled toward their neighbours' elbows: 6-15 deg off).
SIGMA = 1.0
LEFT_T = -0.170          # the left fist's centre along the line from the right's (m; toward the pommel)
BLADE_LEN = 1.122        # the right fist's centre to the tip (Arms sunder_blade: 1.412 - 0.290)


def _d(theta, x=0.0):
    """The blade's way in her sagittal plane: theta degrees from down-the-line (+z) toward up (+y)."""
    t = math.radians(theta)
    return _n(x, math.sin(t), math.cos(t))


# ---------------------------------------------------------------- blade --
# (frame, P: the right fist's pocket point in her space, d: the blade's way, pole: the right elbow's way from the
# shoulder in the chest's frame). The cleave keyed every frame.
BLADE = [
    # The press: the blade swung out low to her right side (the tip 0.7 m off her right leg, the pommel clear of her side) on its way behind her.
    (1, (-0.40, 1.00, -0.10), _n(-0.45, -0.70, -0.55), (0.16, 0.37, 0.91), (0.47, -0.88, -0.09), (0.87, -0.49, 0.07), (-0.83, -0.43, 0.35)),
    (3, (-0.35, 0.95, -0.25), _n(-0.10, -0.50, -0.86), (0.16, 0.37, 0.91), (0.06, -0.87, 0.50), (0.87, -0.49, 0.07), (-0.83, -0.43, 0.35)),
    (5, (-0.45, 0.91, -0.42), _n(-0.12, -0.55, -0.83), (0.68, 0.50, 0.54), (0.08, -0.84, 0.54), (0.57, -0.51, -0.64), (-0.82, -0.42, 0.4)),
    (6, (-0.458, 0.895, -0.44), _n(-0.12, -0.57, -0.82), (0.72, 0.48, 0.51), (0.08, -0.82, 0.56), (0.6, -0.5, -0.62), (-0.82, -0.41, 0.41)),
    (7, (-0.46, 1.20, -0.25), _n(-0.19, -0.37, -0.91), (0.21, 0.78, 0.59), (-0.42, -0.81, 0.42), (0.79, -0.6, 0.14), (-0.98, 0, 0.2)),
    (8, (-0.40, 1.50, -0.17), _n(-0.25, -0.15, -0.96), (0.15, 0.94, 0.31), (-0.96, 0.17, 0.22), (0.65, -0.44, 0.62), (-0.86, 0.49, 0.15)),
    (9, (-0.10, 1.86, -0.22), _n(-0.12, -0.25, -0.96), (0.12, -0.14, 0.98), (0.14, 0.95, -0.27), (0.56, -0.02, 0.83), (-0.29, 0.94, -0.21)),
    (11, (-0.03, 1.90, -0.30), _d(200), (0.22, -0.07, 0.97), (0.0, 0.94, -0.34), (0.38, -0.21, 0.9), (0, 0.94, -0.34)),
    (13, (-0.03, 1.86, -0.34), _d(205), (0.19, -0.10, 0.98), (0.0, 0.91, -0.42), (0.35, -0.28, 0.89), (0.26, 0.88, -0.41)),
    (14, (-0.02, 2.00, -0.03), _d(150), (0.83, -0.32, 0.46), (0.0, 0.87, 0.50), (-0.04, -0.5, 0.87), (-0.5, 0.75, 0.43)),
    (15, (0.00, 1.58, 0.50), _d(60), (0.70, 0.17, -0.70), (0.87, -0.25, 0.43), (0.21, -0.84, 0.50), (-0.71, -0.35, 0.61)),
    (16, (0.00, 1.06, 0.62), _d(-70), (0.42, 0.86, 0.30), (0.97, -0.14, -0.22), (0.28, 0.96, -0.04), (-0.26, 0.33, 0.91)),
    (17, (0.00, 0.99, 0.64), _d(-73), (0.02, 0.97, 0.23), (1.0, 0.0, 0.0), (0.42, 0.89, -0.16), (0.0, 0.29, 0.96)),
    (18, (0.00, 0.93, 0.60), _d(-74), (-0.27, 0.96, 0.05), (1.0, 0.0, 0.0), (0.17, 0.81, -0.56), (-0.5, 0.24, 0.83)),
    (LAND, (0.00, 0.889, 0.551), _d(-74), (-0.72, 0.63, 0.31), (0.87, 0.14, 0.48), (0.19, 0.84, -0.51), (-0.5, 0.24, 0.83)),
    (25, (0.00, 0.93, 0.52), _d(-75.5), (-0.75, 0.56, 0.35), (0.87, 0.13, 0.48), (0.45, 0.85, -0.25), (-0.5, 0.22, 0.84)),
    (57, (0.00, 0.93, 0.52), _d(-75.5), (-0.75, 0.56, 0.35), (0.87, 0.13, 0.48), (0.45, 0.85, -0.25), (-0.5, 0.22, 0.84)),
    # The edge rolled 50 deg about the blade's own line as it comes out (the tip does not move for it) and the elbow
    # lifted, so her forearm is near square (twist +9 deg, the wrist 18) before it turns to the idle's (+93): from the
    # kneel's -60 the forearm had 150-180 deg to turn on the way to her side and the blade swung across her with it.
    (62, (0.00, 1.13, 0.50), _d(-72), (-0.22, 0.80, -0.55), (0.50, 0.27, 0.82), (0.47, 0.40, -0.79), (-0.98, 0.05, 0.17)),
    # Still lifting out along its own line as she rises (the tip 0.18 m up); then her arm eased into the idle's own
    # (_settle, ARM_SETTLE).
    (66, (-0.04, 1.22, 0.47), _d(-66), (-0.22, 0.80, -0.55), (0.26, 0.39, 0.88), (0.47, 0.40, -0.79), (-0.98, 0.05, 0.17)),
]
CLEAVE = range(13, 18)   # keyed every frame: interpolated straight, not eased
# How much of the right hand is the path's (the rest the idle's own arm).
R_ON = [(0, 0.0), (1, 1.0)]   # (the tail: the arm's own joints eased into the idle's, _settle)
# The left hand on the grip: it joins at the top of the rise (travelling f7-9, in front of her face).
L_ON = [(0, 0.0), (7, 0.0), (9, 1.0), (62, 1.0), (66, 0.0)]
# The coil is one-handed: the left arm reaches forward down the line, open-handed (a counterweight), from the idle's
# hand by f4. REACH: (frame, the wrist from the left shoulder in her space, the elbow's way); the hand's fingers along
# the reach, its palm down and in (the thumb side REACH_THUMB).
L_REACH = [(0, 0.0), (4, 1.0), (9, 1.0), (10, 0.0)]
REACH = [(4, (0.05, -0.16, 0.40), (0.55, -0.80, -0.20)),
         (6, (0.06, -0.14, 0.42), (0.55, -0.80, -0.20)),
         (7, (0.04, -0.02, 0.42), (0.55, -0.75, -0.30))]
REACH_THUMB = (-0.75, 0.65, 0.0)
OPEN_L = {"curl": 0.07, "thumb": 0.12, "cascade": 0.45, "spread": 3}


def _blade_at(fr):
    """(P, d, pole (chest frame), k: the grip's knuckles / the blade's edge, square to d) at a frame."""
    def fix(d, k):
        k = k - d * float(k @ d)
        return k / np.linalg.norm(k)
    for a, b in zip(BLADE, BLADE[1:]):
        if a[0] <= fr <= b[0]:
            u = (fr - a[0]) / (b[0] - a[0])
            if a[0] not in CLEAVE:
                u = _smooth(u)
            P = np.array(a[1]) + (np.array(b[1]) - np.array(a[1])) * u
            d = _slerp_dir(np.array(a[2]), np.array(b[2]), u)
            kl = _slerp_dir(fix(np.array(a[2]), _n(*a[6])), fix(np.array(b[2]), _n(*b[6])), u)
            ka, kb = fix(np.array(a[2]), _n(*a[4])), fix(np.array(b[2]), _n(*b[4]))
            k = _slerp_dir(ka, kb, u)
            return (P, d, np.array(a[3]) + (np.array(b[3]) - np.array(a[3])) * u, fix(d, k),
                    np.array(a[5]) + (np.array(b[5]) - np.array(a[5])) * u, fix(d, kl))
    key = BLADE[0] if fr < BLADE[0][0] else BLADE[-1]
    return (np.array(key[1]), np.array(key[2]), np.array(key[3]), fix(np.array(key[2]), _n(*key[4])), np.array(key[5]),
            fix(np.array(key[2]), _n(*key[6])))


# ----------------------------------------------------------------- feet --
# Each foot by its ball (as flare.py): (frame, the ball's offset from the idle's (x, z), lift (deg up on the ball),
# arc (how high it is carried to this key)). The right foot steps back into the coil, rises on its ball, and from f16
# goes down onto its tucked toes under the kneeling knee (KNEEL, below); it steps through to its place on the rise.
FOOT_R = [(0, (0.0, 0.0), 0, 0), (4, (-0.04, -0.40), 0, 0.05), (6, (-0.04, -0.40), 0, 0), (9, (-0.04, -0.40), 28, 0),
          (13, (-0.04, -0.40), 34, 0), (16, (-0.04, -0.40), 40, 0),
          (62, (-0.04, -0.40), 40, 0), (69, (0.0, 0.0), 0, 0.06), (END, (0.0, 0.0), 0, 0)]
FOOT_L = [(0, (0.0, 0.0), 0, 0), (4, (0.0, 0.10), 0, 0.03), (9, (0.0, 0.10), 0, 0), (13, (0.0, 0.10), 12, 0),
          (17, (0.07, 0.45), 0, 0.06), (66, (0.07, 0.45), 0, 0), (74, (0.0, 0.0), 0, 0.05), (END, (0.0, 0.0), 0, 0)]
# The kneel: the right knee down on the ground at z KNEE_KZ (her space), the foot up on tucked toes behind it; eased in
# over f16-20 and out over f58-63 (the hips and the right leg between the kneel's and the keys').
KNEE_KZ = 0.02
KNEEL_IN, KNEEL_OUT = (16, LAND), (58, 63)


def _kneel_w(fr):
    a, b = KNEEL_IN
    c, d = KNEEL_OUT
    if fr <= a or fr >= d:
        return 0.0
    if fr < b:
        return _smooth((fr - a) / (b - a))
    if fr > c:
        return 1.0 - _smooth((fr - c) / (d - c))
    return 1.0


# ------------------------------------------------------------------ body --
def _body_keys():
    def k(fr, ease="auto", hips=(0, 0, 0), hrot=(0, 0, 0), spine=(0, 0, 0), neck=(0, 0, 0), head=(0, 0, 0),
          cl=(0, 0), cr=(0, 0)):
        return (fr, {"hips": {"pos": hips, "rot": hrot}, "spine": spine, "neck": neck, "head": head,
                     "clav_l": cl, "clav_r": cr}, ease)
    return [
        k(0, "ease"),
        k(3, "auto", hips=(-0.025, -0.07, -0.12), hrot=(-22, -2, 0), spine=(-18, -1, 0), neck=(18, 0, 0), head=(18, 0, 0),
          cl=(0, 10), cr=(0, -3)),
        # The coil: the hips down and back over the back foot, one long twist, the head back down the line.
        k(5, "auto", hips=(-0.045, -0.14, -0.26), hrot=(-40, -5, 0), spine=(-28, -4, 0), neck=(35, -2, 0), head=(35, 0, 0),
          cl=(0, 16), cr=(0, -5)),
        k(6, "auto", hips=(-0.05, -0.15, -0.27), hrot=(-42, -5, 0), spine=(-29, -4, 0), neck=(36, -2, 0), head=(36, 0, 0),
          cl=(0, 17), cr=(0, -5)),
        # The rise: unwinding, up onto the ball of the back foot.
        k(8, "auto", hips=(-0.03, -0.045, -0.13), hrot=(-24, 0, 0), spine=(-16, -2, 0), neck=(16, 0, 0), head=(18, 2, 0),
          cl=(4, 6), cr=(8, 0)),
        k(9, "auto", hips=(-0.02, 0.0, -0.08), hrot=(-14, -2, 0), spine=(-8, -6, 0), neck=(8, 0, 0), head=(9, 4, 0),
          cl=(10, 2), cr=(12, 2)),
        # The arch: chest up, the back extended, the eyes down the line; the hang.
        k(11, "auto", hips=(0.0, 0.005, -0.04), hrot=(-5, -5, 0), spine=(-3, -15, 0), neck=(2, 0, 0), head=(3, 12, 0),
          cl=(16, 4), cr=(16, 4)),
        k(13, "auto", hips=(0.0, 0.0, -0.05), hrot=(-3, -6, 0), spine=(-2, -18, 0), neck=(1, 0, 0), head=(1, 14, 0),
          cl=(17, 4), cr=(17, 4)),
        # The cleave: whipped over and down, the drop.
        k(14, "linear", hips=(0.0, -0.04, 0.0), hrot=(0, -2, 0), spine=(0, -8, 0), head=(0, 10, 0), cl=(14, 6), cr=(14, 6)),
        k(15, "linear", hips=(0.01, -0.12, 0.05), hrot=(0, 5, 0), spine=(0, 10, 0), head=(0, 6, 0), cl=(6, 10), cr=(6, 10)),
        k(16, "linear", hips=(0.02, -0.22, 0.09), hrot=(0, 8, 0), spine=(0, 14, 0), head=(0, 8, 0), cl=(0, 12), cr=(0, 12)),
        k(17, "auto", hips=(0.02, -0.32, 0.11), hrot=(0, 8, 0), spine=(0, 14, 0), head=(0, 14, 0), cl=(-2, 12), cr=(-2, 12)),
        k(18, "auto", hips=(0.02, -0.42, 0.12), hrot=(0, 6, 0), spine=(0, 11, 0), head=(0, 20, 0), cl=(-2, 10), cr=(-2, 10)),
        # The kneel lands: chest coming up, the head bowed.
        k(LAND, "auto", hips=(0.02, -0.50, 0.12), hrot=(0, 5, 0), spine=(0, 8, 0), neck=(0, 6, 0), head=(0, 22, 0),
          cl=(-2, 8), cr=(-2, 8)),
        k(21, "auto", hips=(0.02, -0.51, 0.12), hrot=(0, 5, 0), spine=(0, 9, 0), neck=(0, 7, 0), head=(0, 23, 0),
          cl=(-2, 8), cr=(-2, 8)),
        # Risen into the held kneel by f25: sat up (the chest back over the hips, the shoulders back), the head bowed
        # less; two breaths (in f25-33, out -41, in -48), the head lifting f48-57 to look down the seam.
        k(25, "ease", hips=(0.02, -0.50, 0.12), hrot=(0, -2, 0), spine=(0, -10, 0), neck=(0, 7, 0), head=(0, 17, 0),
          cl=(0, -1), cr=(0, -1)),
        k(33, "ease", hips=(0.02, -0.495, 0.12), hrot=(0, -2, 0), spine=(0, -11.5, 0), neck=(0, 7, 0), head=(0, 17, 0),
          cl=(5, -1.5), cr=(5, -1.5)),
        k(41, "ease", hips=(0.02, -0.50, 0.12), hrot=(0, -2, 0), spine=(0, -10, 0), neck=(0, 7, 0), head=(0, 16, 0),
          cl=(0, -1), cr=(0, -1)),
        k(48, "ease", hips=(0.02, -0.495, 0.12), hrot=(0, -2, 0), spine=(0, -11.5, 0), neck=(0, 7, 0), head=(0, 16, 0),
          cl=(5, -1.5), cr=(5, -1.5)),
        k(57, "ease", hips=(0.02, -0.50, 0.12), hrot=(0, -2, 0), spine=(0, -10, 0), neck=(0, 4, 0), head=(0, 6, 0),
          cl=(0, -1), cr=(0, -1)),
        # The recovery.
        k(62, "auto", hips=(0.02, -0.46, 0.12), hrot=(0, 6, 0), spine=(0, 8, 0), neck=(0, 4, 0), head=(0, 8, 0),
          cl=(0, 6), cr=(0, 6)),
        k(66, "auto", hips=(0.01, -0.24, 0.10), hrot=(0, 4, 0), spine=(0, 6, 0), neck=(0, 2, 0), head=(0, 4, 0),
          cl=(0, 3), cr=(0, 3)),
        k(70, "auto", hips=(0.0, -0.07, 0.03), spine=(0, 3, 0), head=(0, 2, 0)),
        k(75, "auto", hips=(0.0, -0.01, 0.0), spine=(0, 1, 0)),
        k(END, "ease"),
    ]


def _reach_at(fr):
    """The open left arm's reach at a frame: (the wrist from the left shoulder, the elbow's way), both in her space."""
    if fr <= REACH[0][0]:
        return np.array(REACH[0][1]), _n(*REACH[0][2])
    for a, b in zip(REACH, REACH[1:]):
        if a[0] <= fr <= b[0]:
            u = _smooth((fr - a[0]) / (b[0] - a[0]))
            return (np.array(a[1]) + (np.array(b[1]) - np.array(a[1])) * u,
                    _slerp_dir(_n(*a[2]), _n(*b[2]), u))
    return np.array(REACH[-1][1]), _n(*REACH[-1][2])


def _qmat(q):
    return np.stack([qrot(q, np.array(e)) for e in ([1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0])], axis=1)


def _shifted_base(base):
    n = base.frames - 1
    idx = [(fr - END) % n for fr in range(END + 1)]
    return Clip(f"{NAME}_base", base.fps, base.rot[idx], base.pos[idx], loop=False, meta=dict(base.meta))


def _arc_vec(arc):
    az, el, r = arc
    return np.array([math.sin(math.radians(az)) * math.cos(math.radians(el)), math.sin(math.radians(el)),
                     math.cos(math.radians(az)) * math.cos(math.radians(el))]) * r


def _hand_frame(d, e):
    """A hand's turn putting its own line DIR (and edge EDGE) on the blade's way d (and edge e): (blade, knuckles)."""
    e = e - d * float(d @ e)
    e = e / np.linalg.norm(e)
    Y = DIR[1] * d + EDGE[1] * e        # hand +Y = 0.574 d + 0.819 e
    Z = DIR[2] * d + EDGE[2] * e        # hand +Z = 0.819 d - 0.574 e
    return Z, Y


class LongCut:
    def __init__(self, rig):
        self.rig = rig
        self.raw = idle.base_of(rig, "warden")
        self.base = _shifted_base(self.raw)
        self.stand = self._stand()
        self.keys = _body_keys()
        self.track = Track(self.keys)
        self.n = END + 1
        self.Rr = None   # the right hand's global turn as last solved, per frame
        self.Rl = None
        self.Gr = None   # the right hand's (turn, place) as last solved
        self.idle = arms_of("warden")
        I = rig.I
        _, bp = rig.sk.fk(self.base.rot, self.base.pos)
        self.bo = bp[:, I["pelvis"]] - rig.prest[I["pelvis"]]     # the base's pelvis off her rest's (Rig.solve's hp)
        bg, _ = rig.sk.fk(self.base.rot, self.base.pos)
        lq = qaxis([1.0, 0, 0], -GRIP_LEAN)
        self.R_idle = bg[:, I["hand_r"]]   # the idle's own right hand (its global turn), per frame

    def _stand(self):
        rig, base = self.rig, self.base
        g, p = rig.sk.fk(base.rot[END][None], base.pos[END][None])
        I = rig.I
        out = {}
        for s in "lr":
            fo, ba = I[f"foot_{s}"], I[f"ball_{s}"]
            out[s] = _euler(qmul(g[0, fo], qinv(rig.grest[fo]))) + (p[0, ba].copy(),)
            h, k, a = p[0, I[f"thigh_{s}"]], p[0, I[f"calf_{s}"]], p[0, fo]
            ax = (a - h) / np.linalg.norm(a - h)
            m = (k - h) - ax * float((k - h) @ ax)
            out["pole_" + s] = tuple(float(x) for x in m / np.linalg.norm(m))
        return out

    def foot(self, s, fr):
        rig, I = self.rig, self.rig.I
        off, lift = _foot_at(FOOT_L if s == "l" else FOOT_R, fr)
        yaw, pitch, roll, ball0 = self.stand[s]
        fo, ba = I[f"foot_{s}"], I[f"ball_{s}"]
        ball = ball0 + off
        q = qeuler(yaw, pitch + lift, roll)
        ankle = ball - qrot(q, rig.prest[ba] - rig.prest[fo])
        return {"pos": (float(ankle[0]), float(ankle[1] - rig.prest[fo][1]), float(ankle[2])),
                "rot": (yaw, pitch + lift, roll), "toe": float(lift), "pole": self.stand["pole_" + s]}

    def kneel(self, pose, fr):
        """The pose with the right knee down (actions._kneel: the hips brought onto the knee's pivot), the right foot up
        on tucked toes, mixed in by _kneel_w."""
        from clips.actions import _kneel, _legs, KNEE_Y, TUCK_Y, TUCK_TOE
        w = _kneel_w(fr)
        if w <= 0:
            return pose
        bo = self.bo[fr]
        h = pose["hips"]
        p = dict(pose, hips=dict(h, pos=tuple(np.array(h["pos"]) + bo)))
        yaw = self.stand["r"][0]
        p["foot_r"] = dict(p["foot_r"], rot=(yaw, 50.0, 0.0), toe=float(TUCK_TOE))
        kn = _kneel(self.rig, p, None, kz=KNEE_KZ, sides="r", ankle_y=TUCK_Y)
        hk = np.array(kn["hips"]["pos"]) - bo
        # The knee's way: _kneel aims it from where the knee would sit on the keyed hips' turn alone, but the leg's
        # solve aims it from the knee as the base's own leg has it, half a metre off here (the knee came down 9 cm
        # high and out to her side). So the way from the hip-ankle line to the knee's place on the ground, made long
        # enough that where it is aimed from no longer matters.
        pel, hip, Lt, *_ = _legs(self.rig)
        H = pel + np.array(kn["hips"]["pos"]) + qrot(qeuler(*h.get("rot", (0, 0, 0))), hip["r"])
        A = np.array(kn["foot_r"]["pos"]) + self.rig.prest[self.rig.I["foot_r"]] * np.array([0, 1.0, 0])
        kx = float(p["foot_r"]["pos"][0])
        K = np.array([kx, KNEE_Y, H[2] - math.sqrt(max(Lt * Lt - (H[1] - KNEE_Y) ** 2 - (H[0] - kx) ** 2, 1e-6))])
        ax = (A - H) / np.linalg.norm(A - H)
        m = (K - H) - ax * float((K - H) @ ax)
        kn["foot_r"]["pole"] = tuple(float(x) for x in m / np.linalg.norm(m))
        out = dict(pose)
        out["hips"] = dict(h, pos=tuple(np.array(h["pos"]) + (hk - np.array(h["pos"])) * w))
        a, b = pose["foot_r"], kn["foot_r"]
        mix = lambda x, y: tuple(float(u + (v - u) * w) for u, v in zip(x, y))
        out["foot_r"] = {"pos": mix(a["pos"], b["pos"]), "rot": mix(a["rot"], b["rot"]),
                         "toe": float(a["toe"] + (b["toe"] - a["toe"]) * w),
                         "pole": tuple(_slerp_dir(_n(*a["pole"]), _n(*b["pole"]), w) * (1.0 + 9.0 * w))}
        return out

    def pose(self, fr):
        p = self.track(fr)
        p["foot_l"], p["foot_r"] = self.foot("l", fr), self.foot("r", fr)
        return self.kneel(p, fr)

    def body(self):
        """The shoulders and the chest's turn at each frame (hands not yet solved)."""
        rig, I = self.rig, self.rig.I
        S_r, S_l, chest = [], [], []
        for fr in range(self.n):
            local, pos = rig.solve(self.pose(fr), base=(self.base.rot[fr], self.base.pos[fr]))
            g, p = rig.sk.fk(local[None], pos[None])
            S_r.append(p[0, I["upperarm_r"]])
            S_l.append(p[0, I["upperarm_l"]])
            s3 = I["spine_03"]
            chest.append(qmul(g[0, s3], qinv(rig.grest[s3])))
        return np.array(S_r), np.array(S_l), np.array(chest)

    def right(self, S_r, chest):
        out = []
        idle_r = self.idle["hand_r"]
        v_idle = _arc_vec(idle_r["arc"])
        lq = qaxis([1.0, 0, 0], -GRIP_LEAN)
        for fr in range(self.n):
            P, d, pole, kn = _blade_at(fr)[:4]
            # The hand that holds the blade along d, its edge (the grip's knuckles) along kn: the wrist put from it.
            Rk = qmul(qfrom_basis(np.cross(kn, d), kn, d), qinv(lq))
            W = P - qrot(Rk, AT)
            spec = {"pos": tuple(float(x) for x in W), "blade": tuple(float(x) for x in d),
                    "knuckles": tuple(float(x) for x in kn), "frame": "char",
                    "pole": tuple(float(x) for x in qrot(chest[fr], _n(*pole))), "pole_at": "shoulder", "twist": 0.5}
            w = _curve(R_ON, fr)
            if w < 1.0:
                Wi = S_r[fr] + qrot(chest[fr], v_idle)
                bi = qrot(chest[fr], np.array(idle_r["blade"], float))
                spec["pos"] = tuple(float(x) for x in Wi + (W - Wi) * w)
                # The hand turned from the idle's own the short way to the keyed one (blade and edge together), so
                # the wrist's turn about the forearm never takes the long way round.
                Ri = self.R_idle[fr]
                Rw = qmul(qslerp(Ri, -Rk if float(np.dot(Ri, Rk)) < 0 else Rk, w), lq)
                spec["blade"] = tuple(float(x) for x in qrot(Rw, np.array([0, 0, 1.0])))
                spec["knuckles"] = tuple(float(x) for x in qrot(Rw, np.array([0, 1.0, 0])))
                spec.pop("pole_at")

                pi = qrot(chest[fr], np.array(idle_r["pole"], float))
                spec["pole"] = tuple(float(x) for x in pi + (qrot(chest[fr], _n(*pole)) - pi) * w)
            out.append(spec)
        return out

    def left(self, S_l, chest):
        idle_l = self.idle["hand_l"]
        v_idle = _arc_vec(idle_l["arc"])
        out = []
        for fr in range(self.n):
            ws = _curve(L_ON, fr) if self.Gr is not None else 0.0
            wr = _curve(L_REACH, fr)
            Wi = S_l[fr] + qrot(chest[fr], v_idle)
            spec = {"frame": "char", "twist": 0.4}
            pole_i = qrot(chest[fr], np.array(idle_l["pole"], float))
            Rr_ = None
            if wr > 0:
                v, pole_r = _reach_at(fr)
                Wi = Wi + (S_l[fr] + v - Wi) * wr
                pole_i = pole_i + (pole_r - pole_i) * wr
                y = v / np.linalg.norm(v)
                z = np.array(REACH_THUMB) - y * float(np.array(REACH_THUMB) @ y)
                z = z / np.linalg.norm(z)
                Rr_ = np.stack([np.cross(y, z), y, z], axis=1)
            if ws > 0:
                qr, pr = self.Gr[0][fr], self.Gr[1][fr]
                d = qrot(qr, DIR)
                _, _, _, _, pole_l, kl = _blade_at(fr)
                kl = kl - d * float(kl @ d)
                kl = kl / np.linalg.norm(kl)
                Q = pr + qrot(qr, AT + DIR * LEFT_T)
                # The left fist turned so its own line (DIR_L) is the blade's, rolled about it so its own +Y (square to
                # the line) lies along kl: the roll keyed per beat (the grip is round), chosen with the elbow's way for
                # an easy wrist (tools/scratch/anim59_armsearch.py).
                yl = np.array([0, 1.0, 0]) - DIR_L * DIR_L[1]
                yl = yl / np.linalg.norm(yl)
                Mw = np.stack([d, kl, np.cross(d, kl)], axis=1)
                Mh = np.stack([DIR_L, yl, np.cross(DIR_L, yl)], axis=1)
                Rw = Mw @ Mh.T
                Ws = Q - Rw @ AT_L
                bump = qrot(chest[fr], np.array((0.04, 0.03, 0.12))) * math.sin(math.pi * ws) if ws < 1 else 0.0
                W = Wi + (Ws - Wi) * ws + bump
                Rh = Rw
                if Rr_ is not None and ws < 1.0:
                    # From the open reach to the grip, turned the short way.
                    qa, qb = qfrom_basis(*Rr_.T), qfrom_basis(*Rw.T)
                    Rh = _qmat(qslerp(qa, -qb if float(np.dot(qa, qb)) < 0 else qb, _smooth(ws)))
                spec["blade"] = tuple(float(x) for x in Rh[:, 2])
                spec["knuckles"] = tuple(float(x) for x in Rh[:, 1])
                pole_g = qrot(chest[fr], _n(*pole_l))
                if ws < 1.0:
                    if Rr_ is None:
                        spec["aim"] = ws
                    spec["pole"] = tuple(float(x) for x in pole_i + (pole_g - pole_i) * ws)
                else:
                    spec["pole"] = tuple(float(x) for x in pole_g)
                    spec["pole_at"] = "shoulder"
            elif Rr_ is not None and wr >= 1.0:
                W = Wi
                spec["blade"] = tuple(float(x) for x in Rr_[:, 2])
                spec["knuckles"] = tuple(float(x) for x in Rr_[:, 1])
                spec["pole"] = tuple(float(x) for x in pole_i)
            elif Rr_ is not None:
                # Out of the idle into the reach: the hand aimed by how far it has gone.
                W = Wi
                spec["blade"] = tuple(float(x) for x in Rr_[:, 2])
                spec["knuckles"] = tuple(float(x) for x in Rr_[:, 1])
                spec["aim"] = wr
                spec["pole"] = tuple(float(x) for x in pole_i)
            else:
                W = Wi
                spec["thumb"] = tuple(float(x) for x in qrot(chest[fr], np.array(idle_l["thumb"], float)))
                spec["pole"] = tuple(float(x) for x in pole_i)
            spec["pos"] = tuple(float(x) for x in W)
            out.append(spec)
        return out

    def fingers_l(self, fr):
        w = _curve(L_ON, fr)
        b = WRAP_TILT["sunder"][TILT] if TILT else WRAP["sunder"]   # her left fist the right's, laid mirrored
        if w >= 1.0:
            return b
        a = self.idle["fingers_l"]
        if fr < 40:
            # The coil's open hand (fingers relaxed-extended, a little spread) from the idle's, then onto the grip.
            o = _curve(L_REACH, fr)
            ci, co = finger_curl(a), finger_curl(OPEN_L)
            ca = {k: [x + (y - x) * o for x, y in zip(ci[k], co[k])] for k in co}
            sp = OPEN_L["spread"] * o
            oa, ta = a.get("oppose", 0.0) * (1 - o), a.get("thumb_roll", 0.0) * (1 - o)
        else:
            ca, sp = finger_curl(a), 0.0
            oa, ta = a.get("oppose", 0.0), a.get("thumb_roll", 0.0)
        cb = finger_curl(b)
        out = {"bends": {k: [x + (y - x) * w for x, y in zip(ca[k], cb[k])] for k in cb},
               "spreads": {k: v * w for k, v in b.get("spreads", {}).items()}, "spread": sp * (1 - w),
               "oppose": oa + (b.get("oppose", 0.0) - oa) * w,
               "thumb_roll": ta + (b.get("thumb_roll", 0.0) - ta) * w}
        return out

    def solve(self, HR, HL):
        def post(fr, pose):
            p = self.kneel(dict(pose, foot_l=self.foot("l", fr), foot_r=self.foot("r", fr)), fr)
            p["hand_r"], p["hand_l"] = HR[fr], HL[fr]
            p["fingers_r"] = "grip"
            p["fingers_l"] = self.fingers_l(fr)
            return p
        meta = {"layer": "full", "weapon": "sunder", **({"grip_tilt": TILT} if TILT else {}), "contact": CONTACT_T, "contacts": [CONTACT_T], "blend_out": 0.9,
                "elbow_sigma": SIGMA}
        return build(NAME, self.rig, self.keys, meta=meta, post=post, base=self.base)

    def hands_of(self, clip):
        g, p = self.rig.sk.fk(clip.rot, clip.pos)
        hr, hl = self.rig.I["hand_r"], self.rig.I["hand_l"]
        Rr, Rl = list(g[:, hr]), list(g[:, hl])
        if self.Rr is not None:
            Rr = [qslerp(o, -n if float(np.dot(o, n)) < 0 else n, 0.5) for o, n in zip(self.Rr, Rr)]
            Rl = [qslerp(o, -n if float(np.dot(o, n)) < 0 else n, 0.5) for o, n in zip(self.Rl, Rl)]
        self.Rr, self.Rl = Rr, Rl
        self.Gr = (g[:, hr], p[:, hr])


ARM_SETTLE = (66, 74)
ENTRY = 1


def _settle(rig, clip, a=SETTLE, b=END):
    """Her right arm eased over ARM_SETTLE into idle_warden's own (its solved joints, as flare.py's _settle; each turns
    the short way, so her forearm goes from the lift's +9 deg to the idle's +93 through neither limit), then every joint
    over f72-80 into idle_warden's own frames (its first at f80). (Before, the hand's keys were blended toward the
    base's bare hand_r, no arm solved: the blade aimed along her left side and its tip went 9 cm into the ground
    f65-73.)"""
    ref = idle.build_one(rig, "idle_warden")
    n = ref.frames - 1
    I, sk = rig.I, rig.sk
    arm = [I["upperarm_r"]]
    for j in arm:
        arm += [k for k, p in enumerate(sk.parent) if p == j and k not in arm]
    # The entry: her right arm crossfaded over f0-2 from idle_warden's own (its solved joints), so the press starts from
    # the idle's arm and not the base's bare hand (the f0 pop: the blade 78 mm into her right thigh).
    for fr in range(ENTRY):
        w = _smooth(fr / ENTRY)
        k = (fr - END) % n
        for j in arm:
            q, o = ref.rot[k, j], clip.rot[fr, j]
            clip.rot[fr, j] = qslerp(q, -o if float(np.dot(o, q)) < 0 else o, w)
    a0, b0 = ARM_SETTLE
    for fr in range(a0, b + 1):
        w = _smooth(min(1.0, (fr - a0) / (b0 - a0)))
        k = (fr - END) % n
        for j in arm:
            q, o = ref.rot[k, j], clip.rot[fr, j]
            clip.rot[fr, j] = qslerp(o, -q if float(np.dot(o, q)) < 0 else q, w)
    for fr in range(a, b + 1):
        w = _smooth((fr - a) / (b - a))
        k = (fr - END) % n
        for j in range(clip.rot.shape[1]):
            q = ref.rot[k, j]
            o = clip.rot[fr, j]
            clip.rot[fr, j] = qslerp(o, -q if float(np.dot(o, q)) < 0 else q, w)
        clip.pos[fr] = clip.pos[fr] + (ref.pos[k] - clip.pos[fr]) * w
    return clip


def flare_long_cut(rig, rounds=6, log=None):
    L = LongCut(rig)
    clip = None
    for r in range(rounds):
        S_r, S_l, chest = L.body()
        HR = L.right(S_r, chest)
        HL = L.left(S_l, chest)
        clip = L.solve(HR, HL)
        L.hands_of(clip)
        if log:
            log(r, L, clip)
    return _settle(rig, clip)


def clips(rig, want):
    if want and not any(w in NAME for w in want):
        return []
    return [flare_long_cut(rig)]
