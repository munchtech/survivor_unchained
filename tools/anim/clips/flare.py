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
from rig import Clip, qaxis, qinv, qmul, qrot, qslerp, qbetween

NAME = "flare_burns_twice"
END, CONTACT, SWEEP, BLEND = 60, 20, 43, 46

# The staff in hand_r's own space (the bound staff, seated on the fist's line by Arms.Seat: WeaponSockets.FistSeat).
M_R = np.array([-0.025, 0.075, 0.0])                 # the mount: the shaft through the right fist
# 18 October (animation 38): the staff's fist refitted on a diagonal (WeaponSockets.FistAtR / FistDirR, keyed.py
# WRAP["staff"], GRIP["staff"] 18); the line, its pocket and the butt (the grip 787.7 mm up from the butt, Arms.Spec)
# as the game seats them (data/arms_local.json, mage_staff@hand_r: its foot at 0.1336, -0.2413, -0.7081).
AXIS = np.array([-0.2116, 0.4141, 0.8853])           # the shaft's line, butt toward head (WeaponSockets.FistDirR)
AXIS = AXIS / np.linalg.norm(AXIS)
SHAFT0 = np.array([-0.0326, 0.0841, -0.0104])        # the shaft's centre where it crosses the fist (WeaponSockets.FistAtR)
# (Animation 48: on the idle's tilted grip, idle.ARC_GRIP_TILT, the clip holds the staff so for its whole length, the
# line turned in the fist about hand +X through the pocket, keyed.grip_pose; the hand leans the tilt less, below.)
if idle.ARC_GRIP_TILT:
    AXIS = qrot(qaxis([1.0, 0, 0], idle.ARC_GRIP_TILT), AXIS)
BUTT = SHAFT0 - 0.7877 * AXIS                        # the butt's foot (on the shaft's line)
LEFT_AT = 0.235                                      # the left fist this far up the shaft (m along it)
# On the drive the left fist slides a little up the shaft (eased over f16-20, held to its letting go): at the plant
# the staff's head is out at her right and the straight left arm crossed her chest into it (18 Oct, the refitted fist).
LEFT_SLIDE = [(16, 0.0), (CONTACT, 0.0)]
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
        # (Her knee's way in the idle, off the hip-ankle line: on a restaged stand, idle.ARC_ST, the legs' pole, so
        # the last frame's thighs meet the idle's; on the fixed (+-0.15, 0, 1) they came 4.5 deg twisted off it.)
        h, k, a = p[0, I[f"thigh_{s}"]], p[0, I[f"calf_{s}"]], p[0, fo]
        ax = (a - h) / np.linalg.norm(a - h)
        m = (k - h) - ax * float((k - h) @ ax)
        out["pole_" + s] = tuple(float(x) for x in m / np.linalg.norm(m))
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
# On a restaged stand (idle.ARC_ST: the HandsInPockets take stood) her pelvis and chest stand 10-11 deg further over
# her feet than on the Strutting take these keys were made on: in the lunge the planted fist came 50-80 mm nearer her
# shoulder, the right elbow went back into her side (upper arm 25 mm into her, 45 into the warden's plate, f20-40).
# The hips pitched back by FLARE_LEAN over the move (eased in over f0-7, out over f43-54), so her body in the lunge
# leans as it did, and the chest rolled FLARE_ROLL toward her left (her right shoulder up: the stand carries it 5 deg
# lower), the plant's elbow keyed further out (FLARE_PLANT_E): at the contact (f20) the upper arm went 14-30 mm into her
# side with the lean alone; now 0 (the warden's plate 5 mm, R1 10). Her head, carried 15 deg further chin-down and
# 10-14 deg further toward her right shoulder by the stand, given back FLARE_HEAD (pitch) and FLARE_HROLL (roll): the look
# to the sky as high as R1's (f28-40, 46-51 deg up), and the hat's brim, tipped down to her right, off the planted
# crescent (f21-22 and f45 at 1-6 mm; now 40-68, R1 30-57). The ends stay the idle's.
FLARE_LEAN = -10.0
FLARE_ROLL = 7.0
FLARE_PLANT_E = (-0.9, -0.45, -0.1)
FLARE_HEAD = -15.0
FLARE_HROLL = -16.0
FLARE_SHIFT = 0.0   # (hips, m, + her left; tried, no help to the brim)
FLARE_YAW = 0.0     # (head, deg; tried, no help)


def _lean_at(fr):
    if fr <= 0 or fr >= 54:
        return 0.0
    return FLARE_LEAN * min(_smooth(fr / 7.0), 1.0 - _smooth((fr - 43) / 11.0))


def _body_keys():
    def k(fr, ease="auto", hips=(0, 0, 0), hrot=(0, 0, 0), spine=(0, 0, 0), neck=(0, 0, 0), head=(0, 0, 0),
          cl=(0, 0), cr=(0, 0)):
        if idle.ARC_ST:
            w = _lean_at(fr) / FLARE_LEAN
            hrot = (hrot[0], hrot[1] + FLARE_LEAN * w, hrot[2])
            spine = (spine[0], spine[1], spine[2] + FLARE_ROLL * w)
            head = (head[0] + FLARE_YAW * w, head[1] + FLARE_HEAD * w, head[2] + FLARE_HROLL * w)
            hips = (hips[0] + FLARE_SHIFT * w, hips[1], hips[2])
        return (fr, {"hips": {"pos": hips, "rot": hrot}, "spine": spine, "neck": neck, "head": head,
                     "clav_l": cl, "clav_r": cr}, ease)
    return [
        k(0, "ease"),
        # A dip into it, the weight onto her right foot as the left steps back.
        k(3, "auto", hips=(-0.03, -0.02, -0.06), spine=(0, 4, 0), head=(0, 2, 0), cl=(6, 2), cr=(3, 2)),
        # The poster: up on the balls of her feet, the back leg long behind,
        # the back a little arched, chin up; the breath in it (f12 the top of
        # the inhale).
        k(7, "auto", hips=(-0.01, 0.004, -0.19), hrot=(0, -3, 0), spine=(0, -8, 0), neck=(0, -3, 0), head=(0, -9, 0),
          cl=(14, 0), cr=(8, 0)),
        k(12, "auto", hips=(-0.01, 0.01, -0.20), hrot=(0, -3, 0), spine=(0, -10, 0), neck=(0, -3, 0), head=(0, -11, 0),
          cl=(15, 0), cr=(10, 0)),
        # The drive: wheeled down, dropping into the lunge, bent over the
        # staff. The head's bow is capped near 20 degrees (world) and the
        # rest of the bow is the chest's; the swing from the poster to the
        # bow is spread over f14-19 (the chest and head leaving together).
        k(14, "auto", hips=(-0.01, 0.005, -0.20), hrot=(0, -3, 0), spine=(0, -10, 0), neck=(0, -4, 0), head=(0, -9, 0),
          cl=(13, 0), cr=(9, 0)),
        k(15, "auto", hips=(-0.012, -0.015, -0.21), hrot=(-3, -3, 0), spine=(-3, -7, 0), neck=(0, -3, -5), head=(0, -8, -1),
          cl=(15, 4), cr=(9, 0)),
        k(16, "auto", hips=(-0.014, -0.05, -0.23), hrot=(-8, -3, 0), spine=(-8, -1, 0), neck=(0, -2, -12), head=(0, -4, -2),
          cl=(27, 12), cr=(9, 0)),
        k(17, "auto", hips=(-0.017, -0.095, -0.25), hrot=(-9.5, 3, 1), spine=(-15, 7, 1), neck=(0, -1, -12), head=(0, -2, -4),
          cl=(17, 18), cr=(3, 1.5)),
        k(18, "auto", hips=(-0.02, -0.15, -0.27), hrot=(-11, 8, 2), spine=(-17, 14, 2), neck=(0, 3, -12), head=(0, 5, -5),
          cl=(7, 24), cr=(-1, 3)),
        k(19, "auto", hips=(-0.025, -0.225, -0.30), hrot=(-9.5, 12, 2.5), spine=(-20, 15, 2), neck=(0, 4, -17), head=(0, 8, -7),
          cl=(2, 43), cr=(14, 3.5)),
        k(CONTACT, "ease", hips=(-0.07, -0.37, -0.33), hrot=(-7, 16, 10), spine=(-22, 19, 2), neck=(0, 2, -23), head=(0, 5, -3),
          cl=(-3, 32), cr=(-6, 4)),
        # The settle: the weight lands, the pelvis 2-3 cm lower and the chest
        # a few degrees further over than the pose it comes back to (f25).
        k(21, "auto", hips=(-0.075, -0.405, -0.33), hrot=(-4, 15, 11), spine=(-24, 21, 3), neck=(0, 1, -25), head=(0, 2, -3),
          cl=(-2, 30), cr=(-10, 4)),
        k(22, "auto", hips=(-0.05, -0.41, -0.33), hrot=(-2, 14.5, 6.5), spine=(-21, 17, 4), neck=(0, 0, -18), head=(0, 0, -5),
          cl=(-2, 24), cr=(-10, 3.5)),
        # The look up: the chest lifted and the head back to the sky, deep in
        # the lunge (the staff is planted and the fist low), the body in one
        # line on from the back thigh, the chest turned a little open to her
        # left where her hand opens.
        k(23, "auto", hips=(-0.03, -0.383, -0.33), hrot=(0, 14, 3), spine=(-13, 8, 5), neck=(0, -2, -12), head=(0, 4, -5),
          cl=(2, 12), cr=(-10, 3)),
        # One line from the hips to the head: the hips thrust forward, the
        # chest arched back (and rising a few degrees through the hold), the
        # neck taking only its share of the head's tilt.
        k(28, "ease", hips=(-0.03, -0.37, -0.26), hrot=(2, 15, 2), spine=(6, -27, 5), neck=(0, -4, 0),
          head=(4, -7, 0), cl=(8, 0), cr=(-10, 4)),
        k(34, "auto", hips=(-0.03, -0.379, -0.255), hrot=(2, 15, 2), spine=(6, -29, 5), neck=(0, -4, 0),
          head=(7, -8, 2), cl=(9, 0), cr=(-10, 4)),
        k(40, "ease", hips=(-0.03, -0.373, -0.255), hrot=(2, 15, 2), spine=(6, -31, 5), neck=(0, -4, 0),
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
BUTT_AT = np.array([-0.42, 0.004, -0.17])  # beside her right foot (the lunge's lead), by its heel
STAFF = [
    (1, "grip", (-0.299, 1.203, 0.068), _n(0.259, 0.860, 0.439), (-0.9, -0.4, -0.2)),
    (3, "grip", (-0.161, 1.397, 0.340), _n(0.784, 0.567, 0.251), (-0.9, -0.4, -0.2)),
    (5, "grip", (-0.128, 1.681, 0.108), _n(0.979, 0.161, -0.121), (-1.0, 0.0, 0.1)),
    (7, "grip", (-0.110, 1.868, -0.205), _n(0.999, -0.012, 0.044), (-1.0, 0.2, 0.3)),
    (12, "grip", (-0.110, 1.878, -0.217), _n(0.999, -0.000, 0.035), (-1.0, 0.2, 0.3)),
    (15, "grip", (-0.106, 1.925, -0.170), _n(0.981, 0.176, 0.083), (-1.0, 0.2, 0.3)),
    # The drive: the staff wheeled about the middle of her two fists (its
    # head up, its butt down at her right), down in front of her face and
    # out of its way, then driven straight down into the ground. The right
    # elbow keyed by its way from the shoulder (E): forward, then down, the
    # forearm out-forward to the planted staff.
    (16, "grip", (-0.135, 1.950, -0.070), _n(0.945, 0.307, 0.110), (-1.0, 0.0, 0.4)),
    # (New rig, 14 Oct: the forearm 5 cm longer. The f17-18 elbow keyed out
    # to her right and level, and the f18 fist 4 cm higher, so the bent arm
    # rides over her right breast rather than down its side.)
    (17, "grip", (-0.190, 1.581, 0.103), _n(0.874, 0.480, 0.066), _n(-0.3, 0.0, 0.95), "E"),
    (18, "grip", (-0.301, 1.350, 0.253), _n(0.470, 0.874, 0.123), _n(-0.7, 0.0, 0.7), "E"),
    (19, "grip", (-0.440, 1.150, 0.140), _n(0.030, 0.990, 0.105), _n(-0.8, -0.45, -0.4), "E"),
    # Planted the fist's +Z is keyed (the staff's own line is AXIS in it,
    # 6.6 degrees toward the fingers, which face out to her right here): so
    # the shaft stands about (-0.05, 0.99, 0.10), near upright, its head over
    # the butt and the left fist within her reach.
    # (18 Oct, the refitted fist: the plant's elbow keyed out to her right, -0.60 (was 0.15 in, as the hold's): at
    # f20 the upper arm went 31 mm into her side.)
    (CONTACT, "butt", BUTT_AT, _n(-0.200, 0.975, 0.095), _n(*FLARE_PLANT_E) if idle.ARC_ST else _n(-0.60, -0.80, -0.10), "E"),
    (22, "butt", BUTT_AT, _n(-0.120, 0.985, 0.120), _n(0.15, -0.97, -0.10), "E"),
    (28, "butt", BUTT_AT, _n(-0.047, 0.992, 0.117), _n(0.15, -0.97, -0.10), "E"),
    (40, "butt", BUTT_AT, _n(-0.033, 0.990, 0.133), _n(0.15, -0.97, -0.10), "E"),
    (SWEEP, "butt", BUTT_AT, _n(-0.318, 0.927, 0.196), (-0.6, -0.8, -0.4)),
    (BLEND, "grip", (-0.386, 0.985, -0.157), _n(-0.113, 0.970, 0.214), (-0.8, -0.3, -0.6)),
    (52, "grip", (-0.321, 1.129, -0.039), _n(-0.075, 0.959, 0.272), (-0.8, -0.3, -0.6)),
]
# Through the drive the fist turns on one even turn from its last poster
# frame to its plant (as last solved), this far along at each frame: the
# staff wheels in her front plane and the fist rolls no more than it must.
DRIVE_U = {16: 0.1, 17: 0.29, 18: 0.56, 19: 0.92, CONTACT: 1.0}
# How much of the hand is the path's (the rest the idle's own arm; done
# with by f56 so the idle's own elbow is settled by the seam).
R_ON = [(0, 0.0), (3, 1.0), (51, 1.0), (56, 0.0)]
# The left hand: on the shaft from f5 through the contact, letting go over
# f21-30 (turned evenly from its hold on the shaft to its opening: RELEASE,
# OPEN), open to the embers, back to the idle by f54.
L_SHAFT = [(1, 0.0), (5, 1.0), (CONTACT + 1, 1.0), (30, 0.0)]
if idle.ARC_ST:
    # The restaged free hand is palm down, ~45 deg round from the grip: the reach is spread over f0-9 so no frame turns the hand past 30 deg.
    L_SHAFT = [(0, 0.0), (9, 1.0), (CONTACT + 1, 1.0), (30, 0.0)]
L_OPEN = [(CONTACT + 1, 0.0), (30, 1.0), (SWEEP + 2, 1.0), (54, 0.0)]
RELEASE, OPEN = CONTACT + 1, 31
FINGER_OPEN_AT = {"thumb": 23.5, "index": 23.5, "middle": 24.5, "ring": 25.5, "pinky": 26.5}
L_OPEN_ARC = (0.35, -0.20, -0.13)      # from the left shoulder, in the chest's frame (hangs about 25 deg low, 20 behind)
AIM_LET_GO = 1.0                       # how far the hand stops being aimed at mid-release
L_BUMP = (0.15, 0.12, 0.30)                # the way round, in the chest's frame
L_REACH = (0.06, 0.02, 0.16)               # the reach to the shaft goes out in front of her breast, not through it
L_OPEN_KNUCKLES = _n(0.62, 0.40, 0.62)
L_OPEN_DRIFT = (0.0, 0.015, 0.010)
L_SOFT = (0.92, 0.975)                 # letting go: the wrist's reach eased in under this share of the arm (elbow >= ~25 deg)     # the open hand floats up and forward through the hold, back for the sweep


def _open_arc(fr):
    u = min(1.0, max(0.0, (fr - OPEN) / (SWEEP - OPEN)))
    return np.array(L_OPEN_ARC) + np.array(L_OPEN_DRIFT) * math.sin(math.pi * u)  # the fingers out and up, the palm up to the sky


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
            elif a[0] == 40:
                u = u * u               # into the sweep at speed (the tip stays near upright to f42)
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
        # The grip's blade and knuckles in hand_r's space: keyed.py reads a keyed blade as the grip's way, the hand
        # turned back from it by GRIP["staff"] about its +X (18 Oct; keyed with the hand's own +Z the fist was 18 deg
        # off its line and her right arm went 54 mm into her).
        from keyed import GRIP
        lq = qaxis([1.0, 0, 0], -(GRIP.get("staff", 0.0) - idle.ARC_GRIP_TILT)) if rig.grips else np.array([0, 0, 0, 1.0])
        self.gz, self.gy = qrot(lq, np.array([0, 0, 1.0])), qrot(lq, np.array([0, 1.0, 0]))
        _, rp = rig.sk.rest_globals()
        I = rig.I
        self.L_len = float(np.linalg.norm(rp[0, I["lowerarm_l"]] - rp[0, I["upperarm_l"]])
                           + np.linalg.norm(rp[0, I["hand_l"]] - rp[0, I["lowerarm_l"]]))

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
                "rot": (yaw, pitch + lift, roll), "toe": float(lift),
                "pole": self.stand["pole_" + s] if idle.ARC_ST else ((0.15 if s == "l" else -0.15), 0, 1.0)}

    # -- the right hand's wanted wrist and blade at each frame
    def right(self, S_r, chest):
        out = []
        idle_r = self.idle["hand_r"]
        v_idle = np.array(_arc_vec(idle_r["arc"]))
        for fr in range(self.n):
            a, b, u = _staff_at(fr)
            d = _slerp_dir(a[3], b[3], u)
            R = self.Rr[fr] if self.Rr is not None else None
            # The hand as it is keyed this frame (the last solved, turned so the shaft lies on the key's line; on the
            # drive, as DRIVE_U turns it): the wrist is put from this, not the last solved. (18 Oct: the refitted fist's
            # butt lies 27.7 deg off the hand's +Z; put from the last solved hand, a frame whose shaft leant out took a
            # wrist out of her reach, the arm went straight and the shaft leant on: f20 and f23-26 stuck so, the butt
            # 6-7 cm off the ground.)
            Rk = R
            if R is not None:
                Rk = qmul(qbetween(qrot(R, AXIS), d), R)
                if fr in DRIVE_U:
                    qa, qb = self.Rr[15], self.Rr[CONTACT + 1]
                    Rk = qslerp(qa, -qb if float(np.dot(qa, qb)) < 0 else qb, DRIVE_U[fr])
            if a[1] == "butt" and b[1] == "butt":
                anchor, point = BUTT, np.array(BUTT_AT)
                W = point - (qrot(Rk, anchor) if R is not None else -0.79 * d)
            else:
                pa = self._wrist_of(a, fr, Rk)
                pb = self._wrist_of(b, fr, Rk)
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
                # Turned toward the fist as planted and settled (f21): at the contact itself the arm
                # solve left alone missed the key's line by 14 degrees, the shaft leant out and the fist
                # chased it 18 cm out to her right (round 9's f20).
                qa, qb = self.Rr[15], self.Rr[CONTACT + 1]
                q = qslerp(qa, -qb if float(np.dot(qa, qb)) < 0 else qb, DRIVE_U[fr])
                d = qrot(q, self.gz)
                kn = qrot(q, self.gy)
            if kn is None and R is not None:
                # The key's way is the SHAFT's line (round 9: AXIS moved with the refitted pocket, 4eb83530): the hand's
                # +Z (the "blade" the arm solve keys) turned, as last solved, by the shortest turn putting the shaft on it.
                # (Keyed as the grip's own way, GRIP["staff"]: keyed.py turns the hand back from it by the lean.)
                d = qrot(qbetween(qrot(R, AXIS), d), qrot(R, self.gz))
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
        anchor = BUTT if key[1] == "butt" else SHAFT0
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
            Wo = S_l[fr] + qrot(chest[fr], _open_arc(fr))
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
                on = pr + qrot(qr, SHAFT0 + AXIS * (LEFT_AT + _curve(LEFT_SLIDE, fr)))
                dw = qrot(qr, AXIS)
                Rl = self.Rl[fr] if self.Rl is not None else None
                Ws = on - (qrot(Rl, M_L) if Rl is not None else 0.0)
                k = _smooth((fr - 16) / 3.0)
                pole_s = np.array((0.8, -0.15, 0.6)) * (1 - k) + np.array((0.6, 0.3, 0.6)) * k
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
            if fr > RELEASE:
                # Letting go the hand never asks past a soft elbow (the bump
                # round her front had her arm locked straight at f23).
                v = W - S_l[fr]
                r = float(np.linalg.norm(v)) / self.L_len
                a, b = L_SOFT
                if r > a:
                    W = S_l[fr] + v / np.linalg.norm(v) * self.L_len * (a + (b - a) * math.tanh((r - a) / (b - a)))
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
        if o == 0 and 0 < g < 1:
            # On the reach the thumb takes its grip by half way (it closes first, as the hand leaves her hip).
            gt = min(1.0, g / 0.5)
            for k in ("thumb", "oppose", "thumb_roll", "thumb_in", "t1", "t2", "t3"):
                f[k] = rel[k] * (1 - gt) + grip[k] * gt
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
                "blend_out": BLEND / 30, **idle.arc_grip()}
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
    keys = ("curl", "thumb", "spread", "cascade", "oppose", "thumb_roll", "thumb_in")

    def full(p):
        # (With the per-joint scales and cascades a preset may carry, keyed.finger_curl: the relaxed hand's shape.)
        p = FINGER_PRESETS[p]
        out = {k: float(p.get(k, 0.0)) for k in keys}
        out.update({f"{j}{n}": float(p.get(f"{j}{n}", 1.0)) for j in "jt" for n in (1, 2, 3)})
        out.update({f"c{n}": float(p.get(f"c{n}", out["cascade"])) for n in (1, 2, 3)})
        return out
    return full("relaxed"), full("grip"), full("spread")


# The rise out of the settle, eased (14 Oct, the r10 judge): the pelvis came up
# 650 677 680 690 693 mm at f22-26 (+27 in one frame, then +3/+10/+3); these
# take it up 650 662 674 684 690 692 at f22-27 instead.
RISE_EASE = {23: -0.015, 24: -0.006, 25: -0.006, 26: -0.003}


def flare_burns_twice(rig, rounds=10, log=None):
    F = Flare(rig)
    clip = None
    G = None
    for r in range(rounds):
        S_r, S_l, chest = F.body()
        HR = F.right(S_r, chest)
        if r == 3:
            # (14 Oct: taken once the hands have settled; at round 1 the drop
            # read the first round's rough fists and sank her 4-6 cm at f20-24.)
            F.dy = F.dy + F.reach_drop(S_r, HR)
            for fr, d in RISE_EASE.items():
                F.dy[fr] += d
            S_r, S_l, chest = F.body()
            HR = F.right(S_r, chest)
        HL = F.left(S_l, chest, G)
        clip = F.solve(HR, HL)
        G, _ = F.hands_of(clip)
        if log:
            log(r, F, clip)
    _settle(rig, F, clip)
    # Her left hand on her hip at the ends (where the idle's weight is), kept on her own pelvis: in the chest's
    # frame with the relaxed fingers it sank up to 29 mm into her hip and spread at the settle.
    # (The thumb slerped by w squared, with Flare.fingers' thumb leading the reach: at f4 her glove's thumb sleeve
    # folded 1.3 mm into her hand's thenar, 2 points; now none. Animation 33.)
    # (On a restaged stand, idle.ARC_ST: the idle's free hand, its fingers in phase with the idle's, frame END its first.)
    n = idle.base_of(rig, "arcanist").frames - 1
    return idle.hip_layer(rig, clip, lambda f: 1.0 - _curve(L_SHAFT, f) - _curve(L_OPEN, f), thumb_pow=2.0,
                          phase=lambda f: (f - END) / n)


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
                          loop=False, weapon="staff", slide=idle.ARC_GRIP_SLIDE, tilt=idle.ARC_GRIP_TILT)
    I, sk = rig.I, rig.sk
    arm = [I["upperarm_r"]]
    for j in arm:
        arm += [k for k, p in enumerate(sk.parent) if p == j and k not in arm]
    toes = [I["ball_l"], I["ball_r"]]
    if idle.ARC_ST:
        # (On a restaged stand the legs too, as the toes: the joints land where the idle's are, but the thighs came
        # 2-4.5 deg rolled about their own line off the idle's capture.)
        toes += [I[f"{j}_{s}"] for j in ("thigh", "calf", "foot") for s in "lr"]
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
