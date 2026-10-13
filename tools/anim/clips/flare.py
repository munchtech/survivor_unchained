"""flare_burns_twice: the arcanist's Flare, played at her own speed while the
world runs at 8%. Two seconds at 30 fps, laid over her captured standing
(idle_arcanist's base, run so its last frame is the idle's first):

- f0-f7 wind-up: the staff swung across and up in both hands to overhead,
  the left hand leaving her hip to take the shaft on the way; she rises on
  the balls of her feet, chest and shoulders lifting on the inhale.
- f7-f16 the poster: the staff overhead, a little diagonal (its head up to
  her left), both fists on it 25 cm apart; heels up, legs long, the back a
  little arched, chin up; a slow breath through it.
- f16-f20 the drive: the staff wheeled down to upright and driven into the
  ground beside her right foot (contact f20), the knees giving, bent over it.
- f20-f43 the look up: the chest lifts and the head goes back to the sky,
  the left hand letting go and opening to the falling embers; held, the
  head tracking a little.
- f40-f43 the sweep: the right hand sweeps the planted staff's head down
  and out to her right on the last impact (contact f43); then she rises,
  the staff lifted back to her side, and settles into idle_arcanist by f60
  (the run may take over from f46).

The staff is held at its grip (Arms.Spec Grip 0.45 from the butt), so with
the butt on the ground her right fist is at most 0.79 m up, and a staff goes
square through the fist (the wrist bends 22 degrees to the thumb side,
38 to the little finger's): planted, the forearm is near level, and her
shoulder can be no higher than about 1.15 m. So while the staff is planted
she is low (the hips are let down as far as the right arm needs:
`_reach_drop`).

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

# The staff in hand_r's own space.
M_R = np.array([-0.025, 0.075, 0.0])                 # the mount: the shaft through the right fist
BUTT = np.array([-0.016, -0.006, -0.7875])           # the butt's foot
AXIS = np.array([0.001, 0.1157, 0.9933])             # the shaft's line, butt toward head
AXIS = AXIS / np.linalg.norm(AXIS)
SHAFT0 = np.array([-0.015, 0.089, 0.0])              # the shaft's centre where it crosses the fist
LEFT_AT = 0.25                                       # the left fist this far up the shaft (m along it)
# The left fist's channel (the mirror of the right's mount: her left hand's
# +X is across the palm, her right's across the back).
M_L = np.array([0.025, 0.075, 0.0])


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


def _feet(rig, base):
    """The base's planted feet as keyed feet, and each foot up on its ball by
    `lift` degrees (the ball where it stands, the toes flat on the ground)."""
    from rig import qeuler
    g, p = rig.sk.fk(base.rot[END][None], base.pos[END][None])
    I = rig.I
    out = {}
    for s in "lr":
        fo, ba = I[f"foot_{s}"], I[f"ball_{s}"]
        d = qmul(g[0, fo], qinv(rig.grest[fo]))
        yaw, pitch, roll = _euler(d)
        ball = p[0, ba]
        sgn = 1 if s == "l" else -1
        pole = (sgn * 0.15, 0, 1.0)

        def foot(lift, yaw=yaw, pitch=pitch, roll=roll, ball=ball, fo=fo, ba=ba, pole=pole):
            q = qeuler(yaw, pitch + lift, roll)
            ankle = ball - qrot(q, rig.prest[ba] - rig.prest[fo])
            return {"pos": (float(ankle[0]), float(ankle[1] - rig.prest[fo][1]), float(ankle[2])),
                    "rot": (yaw, pitch + lift, roll), "toe": float(lift), "pole": pole}
        out[s] = foot
    return out


# ------------------------------------------------------------------ body --
def _body_keys(feet):
    up = {"foot_l": feet["l"](24.0), "foot_r": feet["r"](24.0)}
    flat = {"foot_l": feet["l"](0.0), "foot_r": feet["r"](0.0)}
    half = {"foot_l": feet["l"](10.0), "foot_r": feet["r"](10.0)}

    def k(fr, ease="auto", hips=(0, 0, 0), hrot=(0, 0, 0), spine=(0, 0, 0), neck=(0, 0, 0), head=(0, 0, 0),
          cl=(0, 0), cr=(0, 0), ft=flat):
        return (fr, {"hips": {"pos": hips, "rot": hrot}, "spine": spine, "neck": neck, "head": head,
                     "clav_l": cl, "clav_r": cr, **ft}, ease)
    return [
        k(0, "ease"),
        # A dip into it, the shoulders already going.
        k(3, "auto", hips=(0, -0.025, 0), spine=(0, 4, 0), head=(0, 2, 0), cl=(3, 2), cr=(3, 2), ft=half),
        # The poster: up on the balls of her feet, long, the back a little
        # arched, chin up; the breath in it (f12 the top of the inhale).
        k(7, "auto", hips=(0, 0.045, 0.005), hrot=(0, -3, 0), spine=(0, -8, 0), neck=(0, -3, 0), head=(0, -9, 0),
          cl=(8, 0), cr=(8, 0), ft=up),
        k(12, "auto", hips=(0, 0.05, 0.005), hrot=(0, -3, 0), spine=(0, -10, 0), neck=(0, -3, 0), head=(0, -11, 0),
          cl=(10, 0), cr=(10, 0), ft=up),
        k(16, "ease", hips=(0, 0.047, 0.005), hrot=(0, -3, 0), spine=(0, -9, 0), neck=(0, -3, 0), head=(0, -10, 0),
          cl=(9, 0), cr=(9, 0), ft=up),
        # The drive: wheeled down, the heels down, bent over the staff.
        k(18, "auto", hips=(-0.01, -0.05, 0.02), hrot=(-2, 8, -3), spine=(-4, 10, -6), head=(0, 6, 0),
          cl=(2, 2), cr=(-2, 3), ft=half),
        k(CONTACT, "ease", hips=(-0.03, -0.15, 0.03), hrot=(-5, 15, -6), spine=(-8, 22, -10), head=(0, 8, 0),
          cl=(0, 2), cr=(-10, 4)),
        # The look up: the chest lifted and the head back to the sky, the
        # knees still deep (the staff is planted and the fist low).
        k(23, "auto", hips=(-0.03, -0.19, 0.01), hrot=(-5, 10, -6), spine=(-6, 8, -10), head=(0, -4, 0),
          cl=(2, 0), cr=(-10, 2)),
        k(28, "ease", hips=(-0.03, -0.22, -0.01), hrot=(-4, 5, -6), spine=(-4, -12, -10), neck=(0, -8, 0),
          head=(4, -22, 0), cl=(8, 0), cr=(-10, 0)),
        k(34, "auto", hips=(-0.03, -0.22, -0.01), hrot=(-4, 5, -6), spine=(-4, -13.5, -10), neck=(0, -8, 0),
          head=(7, -24, 2), cl=(9, 0), cr=(-10, 0)),
        k(40, "ease", hips=(-0.03, -0.22, -0.01), hrot=(-4, 5, -6), spine=(-4, -12, -10), neck=(0, -8, 0),
          head=(-3, -20, -1), cl=(8, 0), cr=(-10, 0)),
        # The sweep: the planted staff's head swept out to her right.
        k(SWEEP, "auto", hips=(-0.05, -0.21, -0.01), hrot=(-6, 6, -8), spine=(-8, -6, -14), neck=(0, -4, 0),
          head=(0, -12, 0), cl=(4, 0), cr=(-12, 0)),
        # Up out of it and back into her standing.
        k(BLEND, "auto", hips=(-0.02, -0.10, 0.0), hrot=(-3, 4, -3), spine=(-4, 2, -5), head=(0, -5, 0),
          cl=(2, 0), cr=(-4, 0)),
        k(52, "auto", hips=(0, -0.02, 0), spine=(0, 1, 0), head=(0, -1, 0)),
        k(END, "ease"),
    ]


# ----------------------------------------------------------------- staff --
# The staff's path in her space: (frame, anchor, point, shaft's way butt to
# head, right elbow's way). anchor "grip": the shaft's point in the fist at
# `point`; "butt": the butt's foot at `point` (planted).
BUTT_AT = np.array([-0.33, 0.004, 0.13])
STAFF = [
    (3, "grip", (-0.17, 1.40, 0.30), _n(0.75, 0.62, 0.15), (-0.9, -0.4, -0.2)),
    (5, "grip", (-0.13, 1.76, 0.22), _n(0.95, 0.30, 0.05), (-1.0, 0.0, 0.1)),
    (7, "grip", (-0.11, 1.99, 0.10), _n(0.975, 0.21, 0.0), (-1.0, 0.2, 0.3)),
    (12, "grip", (-0.11, 2.005, 0.095), _n(0.975, 0.21, 0.0), (-1.0, 0.2, 0.3)),
    (16, "grip", (-0.11, 1.995, 0.10), _n(0.975, 0.21, 0.0), (-1.0, 0.2, 0.3)),
    (18, "grip", (-0.27, 1.38, 0.24), _n(0.45, 0.88, 0.12), (-1.0, 0.0, -0.3)),
    (CONTACT, "butt", BUTT_AT, _n(0.02, 1.0, 0.18), (-0.8, 0.0, -0.6)),
    (28, "butt", BUTT_AT, _n(0.05, 1.0, 0.14), (-0.8, 0.0, -0.6)),
    (40, "butt", BUTT_AT, _n(0.0, 1.0, 0.15), (-0.8, 0.0, -0.6)),
    (SWEEP, "butt", BUTT_AT, _n(-0.30, 0.94, 0.15), (-0.8, -0.2, -0.6)),
    (BLEND, "grip", (-0.30, 1.02, 0.17), _n(-0.20, 0.96, 0.15), (-0.8, -0.3, -0.6)),
    (52, "grip", (-0.26, 1.12, 0.14), _n(-0.12, 1.0, 0.18), (-0.8, -0.3, -0.6)),
]
# How much of the hand is the path's (the rest the idle's own arm).
R_ON = [(0, 0.0), (3, 1.0), (52, 1.0), (58, 0.0)]
# The left hand: on the shaft from f5 to f21, then open to the embers.
L_SHAFT = [(1, 0.0), (5, 1.0), (CONTACT + 1, 1.0), (25, 0.0)]
L_OPEN = [(CONTACT + 1, 0.0), (26, 1.0), (SWEEP + 2, 1.0), (54, 0.0)]
L_OPEN_ARC = (0.34, 0.02, 0.26)        # from the left shoulder, in the chest's frame
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
            if a[0] == 16:
                u = u ** 2.2            # the drive: from still, hard into the ground
            elif a[0] == 18:
                u = 1 - (1 - u) ** 1.3  # still accelerating through
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
        self.feet = _feet(rig, self.base)
        self.keys = _body_keys(self.feet)
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
        S_r, S_l, chest = [], [], []
        for fr in range(self.n):
            pose = self.track(fr)
            pose = dict(pose, hips=dict(pose["hips"], pos=self._hips(pose, fr)))
            b = (self.base.rot[fr], self.base.pos[fr])
            local, pos = rig.solve(pose, base=b)
            g, p = rig.sk.fk(local[None], pos[None])
            S_r.append(p[0, I["upperarm_r"]])
            S_l.append(p[0, I["upperarm_l"]])
            s3 = I["spine_03"]
            chest.append(qmul(g[0, s3], qinv(rig.grest[s3])))
        return np.array(S_r), np.array(S_l), np.array(chest)

    def _hips(self, pose, fr):
        h = pose.get("hips", {}).get("pos", (0, 0, 0))
        return (h[0], h[1] + self.dy[fr], h[2])

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
            pole = np.array(a[4]) + (np.array(b[4]) - np.array(a[4])) * u
            w = _curve(R_ON, fr)
            if w < 1.0:
                Wi = S_r[fr] + qrot(chest[fr], v_idle)
                bi = qrot(chest[fr], np.array(idle_r["blade"], float))
                pi = qrot(chest[fr], np.array(idle_r["pole"], float))
                W = Wi + (W - Wi) * w
                d = _slerp_dir(bi / np.linalg.norm(bi), d, w)
                pole = pi + (pole - pi) * w
            out.append({"pos": tuple(float(x) for x in W), "blade": tuple(float(x) for x in d), "frame": "char",
                        "pole": tuple(float(x) for x in pole), "twist": 0.5})
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
            wi = 1.0 - max(_curve(L_SHAFT, fr), _curve(L_OPEN, fr))
            ws, wo = _curve(L_SHAFT, fr), _curve(L_OPEN, fr)
            Wi = S_l[fr] + qrot(chest[fr], v_idle)
            ki = qrot(chest[fr], np.array(idle_l["knuckles"], float))
            pole_i = qrot(chest[fr], np.array(idle_l["pole"], float))
            spec = {"frame": "char", "twist": 0.4}
            if ws > 0 and G is not None:
                qr, pr = G[0][fr], G[1][fr]
                on = pr + qrot(qr, SHAFT0 + AXIS * LEFT_AT)
                dw = qrot(qr, AXIS)
                Rl = self.Rl[fr] if self.Rl is not None else None
                Ws = on - (qrot(Rl, M_L) if Rl is not None else 0.0)
                pole_s = np.array((1.0, 0.1, 0.2)) if fr < 18 else np.array((0.9, 0.0, -0.4))
                W = Wi + (Ws - Wi) * ws
                spec["blade"] = tuple(float(x) for x in dw)
                if ws < 1.0:
                    spec["aim"] = ws
                pole = pole_i + (pole_s - pole_i) * ws
            else:
                Wo = S_l[fr] + qrot(chest[fr], np.array(L_OPEN_ARC))
                ko = qrot(chest[fr], L_OPEN_KNUCKLES)
                pole_o = qrot(chest[fr], np.array((0.9, -0.5, -0.3)))
                W = Wi + (Wo - Wi) * wo
                k = _slerp_dir(ki / np.linalg.norm(ki), ko / np.linalg.norm(ko), wo)
                spec["knuckles"] = tuple(float(x) for x in k)
                pole = pole_i + (pole_o - pole_i) * wo
            spec["pos"] = tuple(float(x) for x in W)
            spec["pole"] = tuple(float(x) for x in pole)
            out.append(spec)
        return out

    def fingers(self, fr):
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
        self.Rr = [qmul(g[f, hr], np.array([0, 0, 0, 1.0])) for f in range(self.n)]
        self.Rl = [g[f, hl] for f in range(self.n)]
        return (g[:, hr], p[:, hr]), (g[:, hl], p[:, hl])

    def reach_drop(self, S_r, HR, top=0.425):
        """The hips let down where the right fist (on the planted staff) is
        further from the shoulder than a soft-elbowed arm reaches."""
        need = np.zeros(self.n)
        for fr in range(CONTACT, SWEEP + 1):  # only while the staff is planted
            W = np.array(HR[fr]["pos"])
            d = W - S_r[fr]
            h = math.hypot(d[0], d[2])
            if np.linalg.norm(d) > top and h < top:
                # the shoulder lowered by dy so that |W - S| = top
                need[fr] = max(-0.25, min(0.0, d[1] + math.sqrt(top * top - h * h)))
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


def flare_burns_twice(rig, rounds=4, log=None):
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
    return clip


def clips(rig, want):
    if want and not any(w in NAME for w in want):
        return []
    return [flare_burns_twice(rig)]
