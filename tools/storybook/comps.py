"""SB00's layout-and-light comps for the outside painter (OWNER_NOTES 19 Oct: a
human painter over our comps). Renders the plate plan comps/sb00_comps.json
(shapes in plate units; delivered 1.2 px per unit) into, per plate:

  <id>_block.png    the block-in at the plate's gen px (add layers added, others over)
  <id>_edges.png    the ControlNet map: unify.block_edges of the structure render
                    (no add layers, glows, glowing dots, rims), so lights make no rings
  <id>_layers.png   the layer map over the grayscale block-in, plus a legend far to near
  <id>_notes.png    the camera sheet: each key's frame on the reference plane, beats
  extents.md        what each layer must cover as the camera moves (StoryLens parallax)
  sheet_block.jpg   a contact sheet of the block-ins

    python tools/storybook/comps.py [--only p3,p5] [--out tools/storybook/out/comps]
           [--base <png or pattern with {id}>] [--jobs] [--appendix] [--underlay]
    python tools/storybook/comps.py --palette | --selftest
    python tools/storybook/comps.py --picks DIR [--out ...]
    python tools/storybook/comps.py --soften a.png [b.png ...] --out DIR

The camera is a port of godot/logic/Storybook/StoryMotion.cs (StoryCurve, Camera,
StoryLens); --selftest checks the extents formula against StoryLens.Project.
"""
import argparse
import json
import math
import os
import sys
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
from unify import block_edges  # noqa: E402

PLAN = os.path.join(HERE, "comps", "sb00_comps.json")
FRAME = (3200.0, 1339.0)          # the frame at rest, units (the 2.39:1 band)
DENS = 1.2                         # delivered px per unit
NEAREST = 0.05                     # StoryLens.Nearest
FONT = r"C:\Windows\Fonts\segoeui.ttf"
FONTB = r"C:\Windows\Fonts\segoeuib.ttf"


def rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)], np.float32)


def font(px, bold=False):
    try:
        return ImageFont.truetype(FONTB if bold else FONT, px)
    except OSError:
        return ImageFont.load_default()


def tfmt(t):
    t = round(t, 1)
    return f"{int(t // 60)}:{t - 60 * int(t // 60):04.1f}"


def tfmt0(t):
    t = int(round(t))
    return f"{t // 60}:{t % 60:02d}"


# ---------------------------------------------------------------- camera (port)

class Curve:
    """StoryCurve: cubic Hermite through the keys, eased per key, monotone."""

    def __init__(self, t, v, ease):
        self.t, self.v, self.e = list(t), list(v), list(ease)
        self.m = [self.tangent(i) for i in range(len(t))]

    def hold(self, seg):
        return self.e[seg + 1] == "hold"

    def chord(self, seg):
        t, v = self.t, self.v
        return 0.0 if t[seg + 1] - t[seg] < 1e-9 else (v[seg + 1] - v[seg]) / (t[seg + 1] - t[seg])

    def tangent(self, i):
        n = len(self.t)
        start = i == 0 or self.hold(i - 1)
        end = i == n - 1 or self.hold(i)
        if start and end:
            return 0.0
        before = self.e[i] if i > 0 else None
        after = self.e[i + 1] if i < n - 1 else None
        if start:
            return self.chord(i) if after in ("linear", "out", "stop") else 0.0
        if end:
            return self.chord(i - 1) if before in ("linear", "in") else 0.0
        if before in ("inout", "out", "stop") or after in ("inout", "in"):
            return 0.0
        d0, d1 = self.chord(i - 1), self.chord(i)
        if d0 * d1 <= 0:
            return 0.0
        span = self.t[i + 1] - self.t[i - 1]
        c = 0.0 if span < 1e-9 else (self.v[i + 1] - self.v[i - 1]) / span
        lim = 3 * min(abs(d0), abs(d1))
        return max(-lim, min(lim, c))

    def at(self, time_):
        t, v, m = self.t, self.v, self.m
        n = len(t)
        if n == 0:
            return 0.0
        if time_ <= t[0]:
            return v[0]
        if time_ >= t[-1]:
            return v[-1]
        i = 0
        while i < n - 2 and time_ >= t[i + 1]:
            i += 1
        if self.hold(i):
            return v[i]
        h = t[i + 1] - t[i]
        if h < 1e-9:
            return v[i + 1]
        s = (time_ - t[i]) / h
        s2, s3 = s * s, s * s * s
        return ((2 * s3 - 3 * s2 + 1) * v[i] + (s3 - 2 * s2 + s) * h * m[i]
                + (-2 * s3 + 3 * s2) * v[i + 1] + (s3 - s2) * h * m[i + 1])


def camera(keys, cw, ch):
    """StoryMotion.Camera: returns t -> (x, y, zoom, dolly); zoom moves in log space."""
    if not keys:
        return lambda t: (cw / 2, ch / 2, 1.0, 0.0)
    x, y, z, d = cw / 2, ch / 2, 1.0, 0.0
    ts, vals, eases = [], [], []
    for k in sorted(keys, key=lambda k: k["t"]):
        x = k.get("x", x); y = k.get("y", y); z = k.get("zoom", z); d = k.get("dolly", d)
        ts.append(k["t"]); vals.append([x, y, math.log(max(1e-3, z)), d]); eases.append(k.get("ease"))
    cs = [Curve(ts, [v[c] for v in vals], eases) for c in range(4)]
    return lambda t: (cs[0].at(t), cs[1].at(t), math.exp(cs[2].at(t)), cs[3].at(t))


def lens_layer(cam, z, cw, ch, sw, sh):
    """StoryLens.Layer (no roll)."""
    X, Y, zoom, d = cam
    k = sw / cw * zoom
    dz = max(NEAREST, z - d)
    f = z / dz
    cx, cy = cw / 2, ch / 2
    return k * f, sw / 2 + k * ((cx - X) / dz - cx * f), sh / 2 + k * ((cy - Y) / dz - cy * f)


def lens_project(cam, z, px, py, cw, ch, sw, sh):
    sc, ox, oy = lens_layer(cam, z, cw, ch, sw, sh)
    return ox + sc * px, oy + sc * py


def rest_of(p):
    if "rest" in p:
        return tuple(p["rest"])
    return (p["camera"][0]["x"], p["camera"][0]["y"])


def view_rect(cam, z, rest):
    """The rect a camera sees on a layer's own painting, and its on-screen magnification."""
    X, Y, zoom, d = cam
    X0, Y0 = rest
    dz = max(NEAREST, z - d)
    cx, cy = X0 + (X - X0) / z, Y0 + (Y - Y0) / z
    hw, hh = FRAME[0] / 2 * dz / (z * zoom), FRAME[1] / 2 * dz / (z * zoom)
    return (cx - hw, cy - hh, cx + hw, cy + hh), zoom * z / dz


def samples(p):
    cam = camera(p["camera"], *p["size"])
    dur = p["until"] - p["at"]
    return [cam(t) for t in np.arange(0, dur + 1e-9, 1 / 30.0)]


# ---------------------------------------------------------------- drawing

class Lyr:
    """One layer: premultiplied paint C, alpha A, and light L (added on top).
    Units map to px by (x * sx + ox, y * sy + oy)."""

    def __init__(self, w, h, sx, sy, ox=0.0, oy=0.0, structure=False, frame_c=(0, 0)):
        self.w, self.h, self.sx, self.sy, self.ox, self.oy = w, h, sx, sy, ox, oy
        self.C = np.zeros((h, w, 3), np.float32)
        self.A = np.zeros((h, w), np.float32)
        self.L = np.zeros((h, w, 3), np.float32)
        self.structure = structure
        self.fc = frame_c          # frame centre in px (rim direction)

    # coords
    def P(self, x, y):
        return x * self.sx + self.ox, y * self.sy + self.oy

    def pts(self, p):
        a = np.array(p, np.float64)[:, :2]
        return np.stack([a[:, 0] * self.sx + self.ox, a[:, 1] * self.sy + self.oy], 1)

    def S(self, v):
        return v * self.sx

    def blank(self):
        return np.zeros((self.h, self.w), np.float32)

    # masks in px
    def mpoly(self, pp, soft=0.6, m=None):
        m = self.blank() if m is None else m
        cv2.fillPoly(m, [np.round(np.asarray(pp) * 16).astype(np.int32)], 1.0, cv2.LINE_AA, shift=4)
        return m

    def mline(self, pp, w, m=None):
        m = self.blank() if m is None else m
        cv2.polylines(m, [np.round(np.asarray(pp) * 16).astype(np.int32)], False, 1.0,
                      max(1, int(round(w))), cv2.LINE_AA, shift=4)
        return m

    def mell(self, c, r, ang=0.0, stroke=-1, m=None, a0=0, a1=360):
        m = self.blank() if m is None else m
        cv2.ellipse(m, (int(round(c[0] * 16)), int(round(c[1] * 16))),
                    (max(1, int(round(r[0] * 16))), max(1, int(round(r[1] * 16)))), ang, a0, a1, 1.0,
                    stroke if stroke < 0 else max(1, int(round(stroke))), cv2.LINE_AA, shift=4)
        return m

    def mcap(self, a, b, ra, rb, m=None):
        """A tapered capsule (limb) between px points a and b."""
        m = self.blank() if m is None else m
        th = np.linspace(0, 2 * np.pi, 28, endpoint=False)
        ring = np.stack([np.cos(th), np.sin(th)], 1)
        pts = np.concatenate([np.asarray(a) + ring * ra, np.asarray(b) + ring * rb])
        hull = cv2.convexHull(np.round(pts * 16).astype(np.int32))
        cv2.fillConvexPoly(m, hull, 1.0, cv2.LINE_AA, shift=4)
        return m

    # paint
    def paint(self, m, col, a=1.0):
        ma = np.clip(m, 0, 1) * a
        if not ma.any():
            return
        c = rgb(col) if isinstance(col, str) else np.asarray(col, np.float32)
        self.C *= (1 - ma)[..., None]
        self.C += c * ma[..., None]
        self.A = self.A * (1 - ma) + ma

    def cut(self, m):
        self.C *= (1 - m)[..., None]
        self.A *= (1 - m)

    def light(self, m, col, a=1.0):
        if self.structure:
            return
        c = rgb(col) if isinstance(col, str) else np.asarray(col, np.float32)
        self.L += (m * a)[..., None] * c

    def glow_px(self, x, y, r, col, a=1.0, ry=None):
        if self.structure or r <= 0:
            return
        ry = ry or r
        x0, x1 = int(max(0, x - 1.7 * r)), int(min(self.w, x + 1.7 * r + 1))
        y0, y1 = int(max(0, y - 1.7 * ry)), int(min(self.h, y + 1.7 * ry + 1))
        if x1 <= x0 or y1 <= y0:
            return
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        d = ((xx - x) / r) ** 2 + ((yy - y) / ry) ** 2
        self.L[y0:y1, x0:x1] += (np.exp(-d * 2.2) * a)[..., None] * rgb(col)


def vgrad(lyr, y0, y1, c0, c1):
    """A per-row colour field from c0 at px row y0 to c1 at y1."""
    t = np.clip((np.arange(lyr.h, dtype=np.float32) - y0) / max(1e-3, y1 - y0), 0, 1)[:, None, None]
    return rgb(c0) * (1 - t) + rgb(c1) * t


def fire_px(lyr, x, y, hp, seed=0):
    """A flame standing on (x, y), hp px tall: three nested tongues and a halo."""
    rng = np.random.default_rng(seed)
    for sc, wsc, col in ((1.0, 1.0, "#ff6a18"), (0.7, 0.62, "#ffa834"), (0.4, 0.34, "#ffe6a8")):
        H = hp * sc
        vs = np.linspace(0, 1, 14)
        half = 0.27 * hp * wsc * (1 - vs) ** 0.85 * (0.55 + 0.45 * np.minimum(1, vs * 5))
        wob = rng.normal(0, 0.06, len(vs)) * hp * wsc * (1 - vs)
        lean = 0.08 * hp * vs ** 2 * rng.uniform(-1, 1)
        left = [(x - half[i] + wob[i] + lean[i], y - vs[i] * H) for i in range(len(vs))]
        right = [(x + half[i] + wob[i] * 0.7 + lean[i], y - vs[i] * H) for i in range(len(vs))][::-1]
        lyr.paint(lyr.mpoly(left + right), col, 0.95)
        # side tongues on the outer flame
        if sc == 1.0:
            for s in (-1, 1):
                tx = x + s * 0.17 * hp
                pts = [(tx - 0.07 * hp, y - 0.25 * hp), (tx + s * 0.03 * hp, y - (0.62 + rng.uniform(0, 0.15)) * hp),
                       (tx + 0.07 * hp, y - 0.28 * hp)]
                lyr.paint(lyr.mpoly(pts), col, 0.9)
    lyr.glow_px(x, y - 0.45 * hp, 1.1 * hp, "#ff9a40", 0.55)
    lyr.glow_px(x, y - 0.3 * hp, 0.35 * hp, "#ffd07a", 0.6)


# ---------------------------------------------------------------- figures
# Joints in units of the standing height h (7.5 heads; head = 0.133), feet at v = 0,
# u forward (the facing side), v up. Side poses face +u; front/back poses are frontal.

ARM = (0.031, 0.025, 0.019)
LEG = (0.056, 0.034, 0.022)


def _pose(name, front):
    """Returns (mode, joints) for a pose. mode 'side' or 'front'."""
    if name in ("stand", "stand_slack") and front:
        if name == "stand":
            return "front", dict(P=(0, .53), N=(0, .83), head=(0, .915), ha=0,
                                 arms=[((-.115, .805), (-.135, .635), (-.14, .475)), ((.115, .805), (.135, .635), (.14, .475))],
                                 legs=[((-.055, .5), (-.058, .28), (-.055, .045)), ((.055, .5), (.058, .28), (.055, .045))])
        return "front", dict(P=(0, .52), N=(.005, .80), head=(.02, .88), ha=12,
                             arms=[((-.115, .79), (-.125, .615), (-.12, .455)), ((.11, .775), (.13, .60), (.135, .44))],
                             legs=[((-.055, .5), (-.065, .28), (-.075, .045)), ((.055, .5), (.05, .28), (.06, .045))])
    if name == "stand":
        return "side", dict(P=(0, .53), N=(.012, .825), head=(.025, .915), ha=0,
                            far_arm=((-.01, .8), (-.03, .635), (-.015, .475)), near_arm=((0, .8), (.01, .63), (.035, .47)),
                            far_leg=((-.01, .5), (-.02, .285), (-.035, .045)), near_leg=((.01, .5), (.03, .28), (.01, .045)))
    if name == "stand_slack":
        return "side", dict(P=(0, .52), N=(.03, .80), head=(.07, .87), ha=-18,
                            far_arm=((.015, .785), (.015, .615), (.045, .455)), near_arm=((.02, .785), (.03, .61), (.06, .45)),
                            far_leg=((-.01, .5), (-.01, .28), (-.05, .045)), near_leg=((.01, .5), (.04, .275), (0, .045)))
    if name == "smith_hammer":
        return "side", dict(P=(-.01, .51), N=(-.03, .81), head=(-.01, .9), ha=-10,
                            far_arm=((-.03, .79), (0, .94), (.04, 1.04)), near_arm=((-.02, .79), (.03, .93), (.06, 1.03)),
                            far_leg=((-.02, .49), (-.07, .27), (-.13, .045)), near_leg=((.0, .49), (.10, .29), (.14, .045)),
                            props=["hammer", "apron"])
    if name == "struck":
        return "side", dict(P=(-.03, .5), N=(-.13, .77), head=(-.19, .84), ha=35,
                            far_arm=((-.13, .75), (-.24, .83), (-.32, .93)), near_arm=((-.115, .75), (-.03, .68), (.04, .70)),
                            far_leg=((-.04, .49), (-.1, .27), (-.2, .045)), near_leg=((-.02, .49), (.05, .28), (.07, .045)),
                            props=["impaled"])
    if name == "spear_thrust":
        return "side", dict(P=(0, .47), N=(.1, .76), head=(.14, .845), ha=-8,
                            far_arm=((.1, .745), (.17, .66), (.24, .70)), near_arm=((.085, .745), (.07, .6), (.2, .575)),
                            far_leg=((-.01, .46), (-.12, .25), (-.27, .04)), near_leg=((.02, .46), (.17, .27), (.2, .045)),
                            props=["spear", "shield"])
    if name == "lift_lamp":
        return "side", dict(P=(0, .53), N=(.012, .825), head=(.03, .915), ha=12,
                            far_arm=((-.005, .8), (-.01, .63), (.04, .5)), near_arm=((.005, .8), (.05, .95), (.07, 1.09)),
                            far_leg=((-.01, .5), (-.02, .285), (-.035, .045)), near_leg=((.01, .5), (.03, .28), (.01, .045)),
                            props=["lamp"])
    if name == "ladder_pour":
        return "side", dict(P=(0, .51), N=(.05, .81), head=(.08, .9), ha=22,
                            far_arm=((.04, .79), (.11, .93), (.16, 1.05)), near_arm=((.045, .79), (.13, .9), (.19, 1.03)),
                            far_leg=((.0, .49), (.12, .36), (.05, .165)), near_leg=((.01, .49), (.04, .28), (0, .045)),
                            props=["jug"])
    if name == "lying":
        return "lying", dict(P=(-.02, .055), N=(.29, .06), head=(.38, .065), ha=90,
                             far_arm=((.27, .07), (.17, .13), (.24, .10)), near_arm=((.27, .07), (.12, .05), (-.03, .04)),
                             far_leg=((-.02, .05), (-.25, .15), (-.42, .03)), near_leg=((-.02, .05), (-.24, .045), (-.47, .025)))
    if name == "sit_back_read":
        return "back", dict(P=(0, .05), N=(0, .325), head=(0, .37), ha=0, seated=True,
                            arms=[((-.115, .305), (-.155, .14), (-.11, .09)), ((.115, .305), (.155, .14), (.11, .09))],
                            legs=[], props=["letter"])
    if name == "kneel_back":
        return "back", dict(P=(0, .25), N=(.015, .5), head=(.025, .54), ha=0, kneel=True,
                            arms=[((-.115, .48), (-.13, .33), (-.10, .22)), ((.115, .48), (.19, .32), (.24, .12))],
                            legs=[((-.07, .24), (-.075, .09), (-.07, .03)), ((.07, .24), (.075, .09), (.07, .03))],
                            props=["flask"])
    if name == "hand_up":
        return "hand", {}
    return _pose("stand", front)


def torso_side(P, N, front_sign=1):
    """Profile torso along the spine P->N, chest toward +u (or the spine's left for front_sign -1)."""
    P, N = np.array(P), np.array(N)
    d = N - P
    e = d / (np.linalg.norm(d) + 1e-9)
    n = np.array([e[1], -e[0]]) * front_sign
    fr = [(-.03, .058), (.2, .062), (.45, .056), (.7, .077), (.88, .062), (1.0, .036)]
    bk = [(1.0, -.032), (.9, -.062), (.6, -.056), (.35, -.046), (.1, -.068), (-.08, -.06)]
    return [tuple(P + d * t + n * o) for t, o in fr + bk]


def torso_front(P, N, coat=0.0):
    P, N = np.array(P), np.array(N)
    d = N - P
    e = d / (np.linalg.norm(d) + 1e-9)
    n = np.array([e[1], -e[0]])
    prof = [(-.03, .096 + coat), (.12, .10 + coat * .6), (.38, .08), (.62, .094), (.8, .108), (.93, .124), (1.0, .072), (1.06, .03)]
    right = [tuple(P + d * t + n * w) for t, w in prof]
    left = [tuple(P + d * t - n * w) for t, w in prof][::-1]
    return right + left


def draw_fig(lyr, s, name=""):
    """A figure, drawn on a local crop of the layer (rows hold dozens) and laid in."""
    ax, ay = lyr.P(*s["at"])
    hp = lyr.S(s["h"] / 0.27 if s.get("pose") == "hand_up" else s["h"])
    x0, x1 = int(max(0, ax - 1.1 * hp)), int(min(lyr.w, ax + 1.1 * hp + 2))
    y0, y1 = int(max(0, ay - 1.5 * hp)), int(min(lyr.h, ay + 0.25 * hp + 2))
    if x1 <= x0 or y1 <= y0:
        return
    sub = Lyr(x1 - x0, y1 - y0, lyr.sx, lyr.sy, lyr.ox - x0, lyr.oy - y0, lyr.structure, (lyr.fc[0] - x0, lyr.fc[1] - y0))
    _draw_fig(sub, s, name)
    C, A = lyr.C[y0:y1, x0:x1], lyr.A[y0:y1, x0:x1]
    C *= (1 - sub.A)[..., None]
    C += sub.C
    lyr.A[y0:y1, x0:x1] = A * (1 - sub.A) + sub.A
    lyr.L[y0:y1, x0:x1] += sub.L


def _draw_fig(lyr, s, name=""):
    """A figure silhouette; s is the shape dict (at = feet on the ground, h = standing height)."""
    pose = s.get("pose", "stand")
    face = s.get("face", "right")
    c = rgb(s.get("c", "#202020"))
    ax, ay = lyr.P(*s["at"])
    hp = lyr.S(s["h"])
    sgn = -1.0 if face == "left" else 1.0
    front = face in ("front", "back")
    mode, J = _pose(pose, front)
    hood = s.get("hood", name == "traveler")
    robe = s.get("robe", "priest" in name)
    if mode in ("front", "back"):
        sgn = 1.0 if face != "left" else -1.0

    def X(p):
        return (ax + sgn * p[0] * hp, ay - p[1] * hp)

    far = lyr.blank()
    near = lyr.blank()
    props = []          # (mask, colour)

    def limb(m, ch, rr):
        a, b, cc = ch
        lyr.mcap(X(a), X(b), rr[0] * hp, rr[1] * hp, m)
        lyr.mcap(X(b), X(cc), rr[1] * hp, rr[2] * hp, m)

    def hand(m, el, wr, r=0.022):
        el, wr = np.array(el), np.array(wr)
        dv = wr - el
        dv = dv / (np.linalg.norm(dv) + 1e-9)
        hc = wr + dv * 0.035
        lyr.mcap(X(wr), X(hc), r * 0.9 * hp, r * hp, m)

    def foot(m, an, fwd=True, up=False):
        an = np.array(an)
        if up:          # lying: feet point up
            pts = [an + (-.02, 0), an + (.02, 0), an + (.025, .07), an + (-.005, .075)]
        else:
            base = an[1] - 0.045
            pts = [(an[0] - .03, base), (an[0] + .08 * (1 if fwd else -1), base),
                   (an[0] + .03, an[1] + .005), (an[0] - .025, an[1] + .01)]
        lyr.mpoly([X(p) for p in pts], m=m)

    def head(m, hc, ang, side=True):
        hx, hy = X(hc)
        lyr.mell((hx, hy), (0.05 * hp if side else 0.047 * hp, 0.066 * hp), ang * sgn, m=m)
        if side and not hood:
            # jaw and nose toward the facing side
            a = math.radians(ang)
            off = np.array([0.04 * math.cos(a) + 0.02 * math.sin(a), -0.02 * math.cos(a) + 0.04 * math.sin(a)])
            jx, jy = X((hc[0] + off[0], hc[1] + off[1]))
            lyr.mell((jx, jy), (0.022 * hp, 0.026 * hp), m=m)
        if hood:
            off = (-.012, .006) if side else (0, .008)
            lyr.mell(X((hc[0] + off[0], hc[1] + off[1])), (0.068 * hp, 0.08 * hp), ang * sgn, m=m)
            if side:
                lyr.mpoly([X((hc[0] - .07, hc[1] + .01)), X((hc[0] + .02, hc[1] - .05)),
                           X((hc[0] - .02, hc[1] - .14)), X((hc[0] - .1, hc[1] - .12))], m=m)
            else:
                lyr.mpoly([X((hc[0] - .066, hc[1])), X((hc[0] + .066, hc[1])),
                           X((hc[0] + .12, hc[1] - .085)), X((hc[0] - .12, hc[1] - .085))], m=m)

    if mode == "hand":
        # an arm and clawing hand out of the ground; h is the visible length (forearm + hand)
        H = s["h"] / 0.27
        hpH = lyr.S(H)

        def XH(p):
            return (ax + sgn * p[0] * hpH, ay - p[1] * hpH)
        m = near
        lyr.mcap(XH((-.012, -.01)), XH((.03, .15)), .026 * hpH, .019 * hpH, m)
        lyr.mell(XH((.042, .19)), (.026 * hpH, .033 * hpH), -sgn * 15, m=m)
        knuck = [(.018, .215), (.034, .222), (.05, .22), (.064, .212)]
        for i, k in enumerate(knuck):
            spread = (i - 1.5) * 0.22
            a1 = math.pi / 2 - spread
            mid = (k[0] + math.cos(a1) * .03, k[1] + math.sin(a1) * .03)
            a2 = a1 - 0.9 * sgn * 0 - 0.9   # the tips curl forward, clawing
            tip = (mid[0] + math.cos(a2) * .024, mid[1] + math.sin(a2) * .024)
            lyr.mcap(XH(k), XH(mid), .0075 * hpH, .0065 * hpH, m)
            lyr.mcap(XH(mid), XH(tip), .0065 * hpH, .005 * hpH, m)
        lyr.mcap(XH((.02, .175)), XH((-.012, .2)), .008 * hpH, .007 * hpH, m)
        lyr.mcap(XH((-.012, .2)), XH((-.02, .225)), .007 * hpH, .0055 * hpH, m)
        # clods where it breaks the frost
        props.append((lyr.mell(XH((.0, -.004)), (.075 * hpH, .016 * hpH)), c * 0.55))
        top = ay - 0.26 * hpH
        bot = ay + 0.01 * hpH
    else:
        if mode == "side":
            fa = J["far_arm"]; na = J["near_arm"]; fl = J["far_leg"]; nl = J["near_leg"]
            # far limbs
            limb(far, fl, LEG); foot(far, fl[2])
            limb(far, fa, ARM); hand(far, fa[1], fa[2])
            # torso and near limbs
            lyr.mpoly([X(p) for p in torso_side(J["P"], J["N"])], m=near)
            limb(near, nl, LEG); foot(near, nl[2])
            if robe:
                P = J["P"]
                lyr.mpoly([X((P[0] - .075, .64)), X((P[0] + .075, .64)), X((P[0] + .12, .02)), X((P[0] - .11, .02))], m=near)
            lyr.mcap(X(J["N"]), X(J["head"]), .028 * hp, .026 * hp, near)
            head(near, J["head"], J["ha"])
            limb(near, na, ARM); hand(near, na[1], na[2])
            top_v = max(J["head"][1] + .07, na[2][1] + .05, fa[2][1] + .05)
        elif mode == "lying":
            fa = J["far_arm"]; na = J["near_arm"]; fl = J["far_leg"]; nl = J["near_leg"]
            limb(far, fl, LEG); foot(far, fl[2], up=True)
            limb(far, fa, ARM); hand(far, fa[1], fa[2])
            lyr.mpoly([X(p) for p in torso_side(J["P"], J["N"], -1)], m=near)
            limb(near, nl, LEG); foot(near, nl[2], up=True)
            lyr.mcap(X(J["N"]), X(J["head"]), .028 * hp, .026 * hp, near)
            hx, hy = X(J["head"])
            lyr.mell((hx, hy - 0.005 * hp), (0.066 * hp, 0.05 * hp), m=near)
            lyr.mell(X((J["head"][0] + .01, J["head"][1] + .04)), (0.02 * hp, 0.022 * hp), m=near)   # the face, up
            limb(near, na, ARM); hand(near, na[1], na[2])
            top_v = 0.2
        else:   # front / back
            coat = 0.05 if (J.get("seated") or J.get("kneel")) else 0.0
            for lg in J["legs"]:
                limb(near, lg, LEG)
                lx, _ = lg[2]
                lyr.mell(X((lx * 1.05, .018)), (0.032 * hp, 0.018 * hp), m=near)
            P = J["P"]
            if J.get("seated"):
                lyr.mpoly([X((-.15, 0)), X((.15, 0)), X((.12, .08)), X((-.12, .08))], m=near)
            if J.get("kneel"):
                lyr.mpoly([X((-.14, .0)), X((.14, .0)), X((.11, .2)), X((-.11, .2))], m=near)
                for sx_ in (-1, 1):   # the soles of the folded feet, toward us
                    props.append((lyr.mell(X((sx_ * .065, .02)), (0.03 * hp, 0.02 * hp)), c * 0.65))
            if robe:
                lyr.mpoly([X((-.09, .62)), X((.09, .62)), X((.14, .02)), X((-.14, .02))], m=near)
            lyr.mpoly([X(p) for p in torso_front(P, J["N"], coat)], m=near)
            lyr.mcap(X(J["N"]), X(J["head"]), .03 * hp, .028 * hp, near)
            head(near, J["head"], J["ha"], side=False)
            for i, arm in enumerate(J["arms"]):
                limb(near, arm, ARM)
                hand(near, arm[1], arm[2])
            top_v = max(J["head"][1] + .08, max(a[2][1] for a in J["arms"]) + .05)
        top = ay - top_v * hp
        bot = ay + 0.01 * hp

        # props
        for pr in J.get("props", []):
            if pr == "hammer":
                w = J["near_arm"][2]
                h0, h1 = (w[0] + .01, w[1] + .01), (w[0] - .13, w[1] + .17)
                props.append((lyr.mcap(X(h0), X(h1), .009 * hp, .009 * hp), rgb("#3a2a1c")))
                d = np.array(h1) - np.array(h0); d /= np.linalg.norm(d); n = np.array([d[1], -d[0]])
                hd = [np.array(h1) + n * .06 + d * .02, np.array(h1) - n * .06 + d * .02,
                      np.array(h1) - n * .06 - d * .03, np.array(h1) + n * .06 - d * .03]
                props.append((lyr.mpoly([X(p) for p in hd]), rgb("#2a2a2c")))
            elif pr == "apron":
                P = J["P"]
                props.append((lyr.mpoly([X((P[0] + .03, .74)), X((P[0] + .085, .70)), X((P[0] + .11, .3)), X((P[0] + .03, .3))]), c * 0.7 + rgb("#2a1a10") * 0.3))
            elif pr == "spear":
                a, b = (-.3, .602), (.6, .553)
                props.append((lyr.mcap(X(a), X(b), .009 * hp, .008 * hp), rgb("#6a5a44")))
                tip = [b, (b[0] - .02, b[1] + .018), (b[0] + .085, b[1] - .004), (b[0] - .02, b[1] - .02)]
                props.append((lyr.mpoly([X(p) for p in tip]), rgb("#8a8c90")))
            elif pr == "shield":
                props.insert(0, (lyr.mell(X((.27, .66)), (0.075 * hp, 0.15 * hp), -sgn * 6), rgb("#4a3a2a")))
                props.insert(1, (lyr.mell(X((.27, .66)), (0.075 * hp, 0.15 * hp), -sgn * 6, stroke=max(1, .012 * hp)), rgb("#6a5a40")))
            elif pr == "impaled":
                a, b = (-.31, .662), (.16, .64)
                props.append((lyr.mcap(X(a), X(b), .008 * hp, .008 * hp), rgb("#6a5a44")))
                tip = [a, (a[0] + .02, a[1] + .018), (a[0] - .08, a[1] + .004), (a[0] + .02, a[1] - .018)]
                props.append((lyr.mpoly([X(p) for p in tip]), rgb("#8a8c90")))
            elif pr == "lamp":
                w = J["near_arm"][2]
                lp = (w[0] + .01, w[1] + .035)
                props.append((lyr.mell(X(lp), (.032 * hp, .02 * hp)), rgb("#6a5030")))
                props.append((lyr.mcap(X((lp[0] + .02, lp[1] + .005)), X((lp[0] + .045, lp[1] + .015)), .007 * hp, .005 * hp), rgb("#6a5030")))
                lx, ly = X((lp[0] + .045, lp[1] + .03))
                lyr.glow_px(lx, ly, .11 * hp, s.get("lamp", "#ffd07a"), 0.85)
                lyr.glow_px(lx, ly, .025 * hp, "#fff0c0", 1.0)
                if not lyr.structure:
                    props.append((lyr.mell((lx, ly), (.009 * hp, .016 * hp)), rgb(s.get("lamp", "#ffd07a")) * 0.6 + 0.4))
            elif pr == "jug":
                w = J["near_arm"][2]
                jc = (w[0] + .03, w[1] + .04)
                props.append((lyr.mell(X(jc), (.036 * hp, .048 * hp), -sgn * 55), rgb("#6a5030")))
                props.append((lyr.mcap(X(jc), X((jc[0] + .065, jc[1] + .04)), .014 * hp, .01 * hp), rgb("#6a5030")))
            elif pr == "letter":
                props.append((lyr.mpoly([X((.15, .2)), X((.215, .215)), X((.22, .165)), X((.155, .15))]), rgb("#b8ae94")))
            elif pr == "flask":
                w = J["arms"][1][2]
                props.append((lyr.mell(X((w[0] + .01, w[1] - .045)), (.022 * hp, .03 * hp)), rgb("#4a3a2a")))
        if s.get("torch"):
            # a torch held up beside the head: the near (or right) hand raised to it
            ux = .16 if mode != "side" else .1
            props.append((lyr.mcap(X((ux, .78)), X((ux + .01, 1.02)), .011 * hp, .009 * hp), rgb("#2a1c12")))
            lyr.mcap(X((ux - .05 if mode != "side" else 0.0, .8)), X((ux + .02, .7)), ARM[0] * hp, ARM[1] * hp, near)
            lyr.mcap(X((ux + .02, .7)), X((ux, .82)), ARM[1] * hp, ARM[2] * hp, near)
            tx, ty = X((ux + .01, 1.02))
            top = min(top, ty - .2 * hp)

    # composite: far limbs darker, then the body, then the props
    lyr.paint(np.clip(far - near, 0, 1), c * 0.72 + 0.0)
    lyr.paint(near, c)
    for m, col in props:
        lyr.paint(m, col)
    if s.get("torch"):
        fire_px(lyr, tx, ty, .17 * hp, seed=int(ax * 7 + ay))
    rim = s.get("rim")
    if rim and not lyr.structure:
        sil = np.clip(far + near, 0, 1)
        for m, _ in props:
            sil = np.maximum(sil, m)
        fx, fy = lyr.fc
        dx, dy = fx - ax, (fy - ay) * 0.3 - abs(fx - ax) * 0.3
        dn = math.hypot(dx, dy) or 1.0
        r = max(1.5, 0.012 * hp)
        sh = np.float32([[1, 0, -dx / dn * r], [0, 1, -dy / dn * r]])
        moved = cv2.warpAffine(sil, sh, (lyr.w, lyr.h))
        edge = np.clip(sil - moved, 0, 1)
        rows = np.arange(lyr.h, dtype=np.float32)[:, None]
        mid = (top + bot) / 2
        wv = np.clip((mid - rows) / max(1.0, mid - top) * 1.6, 0, 1)
        lyr.paint(edge * wv, rim, 0.9)


# ---------------------------------------------------------------- shapes

def shape(lyr, s, name, ctx):
    k = s["k"]
    a = s.get("a", 1.0)
    st = lyr.structure
    if k == "rect":
        x, y, w, h = s["r"]
        pp = lyr.pts([(x, y), (x + w, y), (x + w, y + h), (x, y + h)])
        m = lyr.mpoly(pp)
        if "grad" in s:
            lyr.paint(m, vgrad(lyr, pp[0][1], pp[2][1], *s["grad"]), a)
        else:
            lyr.paint(m, s["c"], a)
    elif k == "poly":
        pp = lyr.pts(s["p"])
        m = lyr.mpoly(pp)
        if "grad" in s:
            lyr.paint(m, vgrad(lyr, pp[:, 1].min(), pp[:, 1].max(), *s["grad"]), a)
        else:
            lyr.paint(m, s["c"], a)
    elif k == "cut":
        lyr.cut(lyr.mpoly(lyr.pts(s["p"])))
    elif k == "line":
        pp = lyr.pts(s["p"])
        w = lyr.S(s.get("w", 4))
        if s.get("glow"):
            if st:
                return
            core = cv2.GaussianBlur(lyr.mline(pp, w), (0, 0), max(0.6, w * 0.15))
            halo = cv2.GaussianBlur(lyr.mline(pp, w), (0, 0), max(2.0, w * 2.2))
            lyr.light(core, s["c"], a)
            lyr.light(halo, s["c"], 1.4 * a)
        else:
            lyr.paint(lyr.mline(pp, w), s["c"], a)
    elif k == "ellipse":
        cx, cy = lyr.P(*s["at"])
        rx, ry = s["r"]
        stroke = s.get("stroke")
        m = lyr.mell((cx, cy), (lyr.S(rx), ry * lyr.sy), stroke=lyr.S(stroke) if stroke else -1)
        lyr.paint(m, s["c"], a)
    elif k == "glow":
        cx, cy = lyr.P(*s["at"])
        r = lyr.S(s["r"])
        lyr.glow_px(cx, cy, r, s["c"], a, s["ry"] * lyr.sy if "ry" in s else None)
    elif k == "dots":
        rng = np.random.default_rng(s.get("seed", 0))
        x, y, w, h = s["region"]
        r0, r1 = s.get("r", [4, 8])
        flat = s.get("flat", 1.0)
        m = lyr.blank()
        rs = []
        for _ in range(s["n"]):
            px, py = lyr.P(rng.uniform(x, x + w), rng.uniform(y, y + h))
            rr = lyr.S(rng.uniform(r0, r1))
            rs.append(rr)
            lyr.mell((px, py), (rr, rr * flat), rng.uniform(-10, 10), m=m)
        if s.get("glow"):
            if st:
                return
            lyr.light(m, s["c"], a * 1.1)
            lyr.light(cv2.GaussianBlur(m, (0, 0), max(1.5, np.mean(rs) * 1.6)), s["c"], a * 2.2)
        else:
            if st and r1 * lyr.sx < 4:     # specks (frost) would only make edge noise
                return
            lyr.paint(m, s["c"], a)
    elif k == "trees":
        rng = np.random.default_rng(s.get("seed", 0))
        x, y, w, h = s["region"]
        m = lyr.blank()

        def branch(p0, ang, ln, wd, depth):
            p1 = (p0[0] + ln * math.sin(ang), p0[1] - ln * math.cos(ang))
            lyr.mcap(lyr.P(*p0), lyr.P(*p1), max(0.5, lyr.S(wd) / 2), max(0.5, lyr.S(wd * 0.7) / 2), m)
            if depth == 0:
                return
            branch(p1, ang + rng.uniform(-.25, .25), ln * .74, wd * .68, depth - 1)
            for _ in range(rng.integers(1, 3)):
                branch(p1, ang + rng.choice([-1, 1]) * rng.uniform(.35, .95), ln * rng.uniform(.5, .68), wd * .52, depth - 1)
        n = s["n"]
        for i in range(n):
            tx = x + (i + rng.uniform(0.15, 0.85)) * w / n
            th = h * rng.uniform(0.62, 1.0)
            branch((tx, y + h), rng.uniform(-.08, .08), th * 0.3, th * 0.045, 5)
        lyr.paint(m, s["c"], a)
    elif k == "houses":
        rng = np.random.default_rng(s.get("seed", 0))
        x, y, w, h = s["region"]
        n = s["n"]
        base = y + h
        order = rng.permutation(n)
        col = rgb(s["c"])
        for j, i in enumerate(order):
            hw = w / n * rng.uniform(0.75, 1.25)
            hx = x + (i + 0.5) * w / n - hw / 2 + rng.uniform(-.15, .15) * w / n
            wall = h * rng.uniform(0.32, 0.55)
            roof = min(h - wall, hw * rng.uniform(0.35, 0.6))
            by = base - rng.uniform(0, 0.12) * h
            tone = col * rng.uniform(0.8, 1.15)
            body = [(hx, by), (hx + hw, by), (hx + hw, by - wall), (hx + hw / 2, by - wall - roof), (hx, by - wall)]
            if rng.random() < 0.6:
                cxh = hx + hw * rng.uniform(0.2, 0.75)
                lyr.paint(lyr.mpoly(lyr.pts([(cxh, by - wall - roof * 0.3), (cxh + hw * .09, by - wall - roof * 0.3),
                                             (cxh + hw * .09, by - wall - roof * 0.95), (cxh, by - wall - roof * 0.95)])), tone)
            lyr.paint(lyr.mpoly(lyr.pts(body)), tone)
            lyr.paint(lyr.mline(lyr.pts([(hx - hw * .03, by - wall + 4), (hx + hw / 2, by - wall - roof), (hx + hw * 1.03, by - wall + 4)]),
                                lyr.S(8)), tone * 0.7)
            for _ in range(rng.integers(1, 3)):
                ww, wh = hw * .1, wall * .2
                wx = hx + rng.uniform(.15, .8) * hw
                wy = by - wall * rng.uniform(.35, .7)
                lyr.paint(lyr.mpoly(lyr.pts([(wx, wy), (wx + ww, wy), (wx + ww, wy + wh), (wx, wy + wh)])), s.get("win", "#ffbe6a"))
                gx, gy = lyr.P(wx + ww / 2, wy + wh / 2)
                lyr.glow_px(gx, gy, lyr.S(ww * 2.2), s.get("win", "#ffbe6a"), 0.35)
    elif k == "roots":
        rng = np.random.default_rng(s.get("seed", 0))
        x, y, w, h = s["region"]
        m = lyr.blank()

        def root(p, ang, wd, depth):
            while p[1] < y + h and wd > 1.2:
                ln = h / 9 * rng.uniform(.6, 1.2)
                ang += rng.uniform(-.45, .45)
                ang = max(-1.2, min(1.2, ang))
                q = (p[0] + ln * math.sin(ang), min(y + h, p[1] + ln * math.cos(ang)))
                lyr.mcap(lyr.P(*p), lyr.P(*q), lyr.S(wd) / 2, lyr.S(wd * .82) / 2, m)
                p, wd = q, wd * .82
                if depth < 2 and rng.random() < .32:
                    root(p, ang + rng.choice([-1, 1]) * rng.uniform(.5, 1.0), wd * .6, depth + 1)
        for _ in range(s["n"]):
            root((rng.uniform(x, x + w), y), rng.uniform(-.4, .4), rng.uniform(8, 16), 0)
        lyr.paint(m, s["c"], a)
    elif k == "threads":
        if st:
            return
        rng = np.random.default_rng(s.get("seed", 0))
        f, t = s["from"], s["to"]
        core = lyr.blank()
        w = lyr.S(s.get("w", 4))
        for _ in range(s["n"]):
            x0, x1 = rng.uniform(f[0], f[1]), rng.uniform(t[0], t[1])
            amp, ph, fr = rng.uniform(40, 150), rng.uniform(0, 6.28), rng.uniform(1.5, 3.5)
            ts = np.linspace(0, 1, 60)
            xs = x0 + (x1 - x0) * (ts ** 1.3) + np.sin(ts * math.pi * fr + ph) * amp * np.sin(math.pi * ts)
            ys = f[2] + (t[2] - f[2]) * ts
            lyr.mline(lyr.pts(np.stack([xs, ys], 1)), w * rng.uniform(.6, 1.2), core)
        _, y0 = lyr.P(0, f[2])
        _, y1 = lyr.P(0, t[2])
        field = vgrad(lyr, y0, y1, s["c0"], s["c1"])
        core = np.clip(core, 0, 1)
        halo = cv2.GaussianBlur(core, (0, 0), max(2, w * 2.5))
        lyr.L += (core * 0.7 + halo * 0.9)[..., None] * field
    elif k == "chain":
        pp = lyr.pts(s["p"])
        ln, wd = s["link"]
        L, W = lyr.S(ln), lyr.S(wd)
        seg = np.r_[0, np.cumsum(np.hypot(*np.diff(pp, axis=0).T))]
        step = L * 0.74
        m = lyr.blank()
        hi = lyr.blank()
        for i, d in enumerate(np.arange(L / 2, seg[-1], step)):
            cx, cy = np.interp(d, seg, pp[:, 0]), np.interp(d, seg, pp[:, 1])
            j = min(len(pp) - 2, np.searchsorted(seg, d) - 1)
            ang = math.degrees(math.atan2(pp[j + 1][1] - pp[j][1], pp[j + 1][0] - pp[j][0]))
            if i % 2 == 0:
                lyr.mell((cx, cy), (L / 2, W / 2), ang, stroke=W * 0.26, m=m)
                lyr.mell((cx - W * .06, cy - W * .06), (L / 2 - W * .1, W / 2 - W * .1), ang, stroke=max(1, W * .06), m=hi, a0=190, a1=300)
            else:
                lyr.mcap((cx - L / 2 * math.cos(math.radians(ang)), cy - L / 2 * math.sin(math.radians(ang))),
                         (cx + L / 2 * math.cos(math.radians(ang)), cy + L / 2 * math.sin(math.radians(ang))), W * .16, W * .16, m)
                lyr.mcap((cx - L * .4 * math.cos(math.radians(ang)) - W * .08, cy - L * .4 * math.sin(math.radians(ang)) - W * .08),
                         (cx + L * .4 * math.cos(math.radians(ang)) - W * .08, cy + L * .4 * math.sin(math.radians(ang)) - W * .08),
                         max(.6, W * .04), max(.6, W * .04), hi)
        lyr.paint(m, s["c"])
        lyr.paint(hi * m, s.get("hi", "#6a5a48"))
    elif k == "cart":
        x, y = s["at"]
        w = s["w"]
        col = rgb(s["c"])
        r = 0.17 * w
        wx = x - 0.08 * w
        lyr.paint(lyr.mpoly(lyr.pts([(x - .5 * w, y - r - .02 * w), (x + .42 * w, y - r - .02 * w),
                                     (x + .46 * w, y - r - .2 * w), (x - .52 * w, y - r - .2 * w)])), col)
        heap = lyr.blank()
        rng = np.random.default_rng(int(x))
        for _ in range(14):
            hx, hy = lyr.P(x + rng.uniform(-.42, .38) * w, y - r - .2 * w - rng.uniform(0, .07) * w)
            lyr.mell((hx, hy), (lyr.S(.05 * w), lyr.S(.035 * w)), m=heap)
        lyr.paint(heap, col * 1.25)
        lyr.paint(lyr.mline(lyr.pts([(x + .44 * w, y - r - .08 * w), (x + .95 * w, y - .2 * w)]), lyr.S(.025 * w)), col)
        cx, cy = lyr.P(wx, y - r)
        lyr.paint(lyr.mell((cx, cy), (lyr.S(r), lyr.S(r)), stroke=lyr.S(.035 * w)), col * 0.8)
        sp = lyr.blank()
        for i in range(6):
            aa = i * math.pi / 3 + .3
            lyr.mline([(cx, cy), (cx + math.cos(aa) * lyr.S(r), cy + math.sin(aa) * lyr.S(r))], lyr.S(.015 * w), sp)
        lyr.paint(sp, col * 0.8)
    elif k == "fire":
        x, y = lyr.P(*s["at"])
        fire_px(lyr, x, y, lyr.S(s["h"]), seed=int(s["at"][0]))
    elif k in ("fig", "row"):
        if k == "fig":
            draw_fig(lyr, s, name=name)
            return
        rng = np.random.default_rng(s.get("seed", 0))
        n = s["n"]
        jit = s.get("jitter", 0.06)
        if "path" in s:
            p = np.array(s["path"], np.float64)
        else:
            p = np.array([s["from"], s["to"]], np.float64)
        segl = np.r_[0, np.cumsum(np.hypot(*np.diff(p[:, :2], axis=0).T))]
        tt = np.linspace(0, segl[-1], n)
        figs = []
        for d in tt:
            fx, fy, fh = (np.interp(d, segl, p[:, i]) for i in range(3))
            fh *= 1 + rng.uniform(-jit, jit)
            fx += rng.uniform(-jit, jit) * fh * 0.6
            figs.append(dict(s, k="fig", at=[fx, fy], h=fh))
        for f in sorted(figs, key=lambda f: f["at"][1]):   # far (higher) first
            draw_fig(lyr, f, name=name)
    else:
        print(f"  unknown shape kind {k!r} in layer {name}")


# ---------------------------------------------------------------- render

def layer_order(p):
    return sorted(range(len(p["layers"])), key=lambda i: -p["layers"][i]["z"])


def render(p, w, h, sx, sy, ox=0.0, oy=0.0, structure=False, keep=True):
    """Composite the plate far to near. Returns (img, per-layer content masks)."""
    img = np.ones((h, w, 3), np.float32) * rgb(p.get("bg", "#000000"))
    rx, ry = rest_of(p)
    fc = (rx * sx + ox, ry * sy + oy)
    masks = {}
    for i in layer_order(p):
        ly = p["layers"][i]
        add = ly.get("blend") == "add"
        if structure and add:
            continue
        L = Lyr(w, h, sx, sy, ox, oy, structure, fc)
        for s in ly["shapes"]:
            shape(L, s, ly["name"], p)
        if add:
            img += L.C + L.L
            if keep:
                masks[i] = np.clip(np.max(L.C + L.L, axis=2), 0, 1)
        else:
            img = img * (1 - L.A)[..., None] + L.C + L.L
            if keep:
                masks[i] = L.A.copy()
        del L
    return np.clip(img, 0, 1), masks


def save(f, img):
    cv2.imwrite(f, cv2.cvtColor((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), cv2.COLOR_RGB2BGR))


def load_rgb(f, w, h):
    im = cv2.cvtColor(cv2.imread(f, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB).astype(np.float32) / 255
    return cv2.resize(im, (w, h), interpolation=cv2.INTER_AREA)


# ---------------------------------------------------------------- extents

def extents(p, masks, gw, gh):
    sx, sy = gw / p["size"][0], gh / p["size"][1]
    rest = rest_of(p)
    cams = samples(p)
    X0, Y0 = rest
    rf = (X0 - FRAME[0] / 2, Y0 - FRAME[1] / 2, X0 + FRAME[0] / 2, Y0 + FRAME[1] / 2)
    out = {}
    for i, ly in enumerate(p["layers"]):
        z = ly["z"]
        rects = []
        for cam in cams:
            r, mag = view_rect(cam, z, rest)
            rects.append((r, mag))
        x0 = min(r[0] for r, _ in rects); y0 = min(r[1] for r, _ in rects)
        x1 = max(r[2] for r, _ in rects); y1 = max(r[3] for r, _ in rects)
        pw, ph = (x1 - x0) * 0.02, (y1 - y0) * 0.02
        need = (x0 - pw, y0 - ph, x1 + pw, y1 + ph)
        m = masks.get(i)
        on = m > (0.04 if ly.get("blend") == "add" else 0.05) if m is not None else None
        bbox = None
        solid = False
        if on is not None and on.any():
            ys, xs = np.where(on)
            bbox = (xs.min() / sx, ys.min() / sy, (xs.max() + 1) / sx, (ys.max() + 1) / sy)
            ca, cb = int(max(0, rf[0] * sx)), int(min(gw, rf[2] * sx))
            ra, rb = int(max(0, rf[1] * sy)), int(min(gh, rf[3] * sy))
            cols = on[ra:rb, ca:cb].any(axis=0)
            solid = rf[0] >= -1 and rf[2] <= p["size"][0] + 1 and cols.size > 0 and cols.mean() >= 0.99
        magmax = 0.0
        seen = False
        for r, mag in rects:
            if bbox and r[0] < bbox[2] and r[2] > bbox[0] and r[1] < bbox[3] and r[3] > bbox[1]:
                seen = True
                magmax = max(magmax, mag)
        flags = []
        nw, nh = need[2] - need[0], need[3] - need[1]
        if (x1 - x0) > p["size"][0] * 1.005:      # the unpadded view, so the 2% pad alone never flags
            flags.append(f"WIDER than the plate ({round(nw * DENS)} px vs {round(p['size'][0] * DENS)})")
        if (y1 - y0) > p["size"][1] * 1.005:
            flags.append(f"TALLER than the plate ({round(nh * DENS)} px vs {round(p['size'][1] * DENS)})")
        if magmax > 1.3:
            flags.append(f"INSERT: paint at {magmax:.1f}x detail")
        if bbox and not seen:
            flags.append("content never in frame")
        out[i] = dict(need=need, bbox=bbox, solid=solid, mag=magmax, flags=flags,
                      need_px=(round(nw * DENS), round(nh * DENS)))
    return out


def working_canvas(p, ext):
    """The union of the plate and every layer's needed rect, in delivered px, and the plate's offset in it."""
    x0 = min([0.0] + [e["need"][0] for e in ext.values()])
    y0 = min([0.0] + [e["need"][1] for e in ext.values()])
    x1 = max([p["size"][0]] + [e["need"][2] for e in ext.values()])
    y1 = max([p["size"][1]] + [e["need"][3] for e in ext.values()])
    ox, oy = math.ceil(-x0 * DENS), math.ceil(-y0 * DENS)
    return dict(w=ox + math.ceil(x1 * DENS), h=oy + math.ceil(y1 * DENS), ox=ox, oy=oy)


def wc_line(wc):
    return f"Working canvas {wc['w']} x {wc['h']} px; the comp's top-left sits at ({wc['ox']}, {wc['oy']})"


def fname(p, ly):
    return f"sb00_{p['id']}_{ly['name']}.png"


def blend_txt(ly):
    return "add: paint on black" if ly.get("blend") == "add" else "normal"


def fmt_rect(r):
    return f"{r[0]:.0f}, {r[1]:.0f} to {r[2]:.0f}, {r[3]:.0f}"


def write_extents(plates, results, out):
    L = ["# SB00 layer extents", "",
         "What each layer's painting must cover as the camera moves (StoryLens parallax, sampled at 30 fps "
         "along the plate's keys, held to its end). Units are plate units (1.2 px each). 'Needed' is the union of what "
         "the camera sees on that layer's own painting, padded 2%; 'content' is what the block-in puts there; 'solid' "
         "means the content spans the rest frame's full width. Max magnification is the most the layer is enlarged on "
         "screen while any of its content is in view (1.0 = 1.2 px per unit at 4K).", ""]
    for p in plates:
        ext, wc = results[p["id"]]["ext"], results[p["id"]]["wc"]
        rx, ry = rest_of(p)
        L += [f"## {p['id']}: {p['title']}", "",
              f"Film {tfmt(p['at'])} to {tfmt(p['until'])}; painting {p['size'][0]} x {p['size'][1]} units "
              f"= {round(p['size'][0] * DENS)} x {round(p['size'][1] * DENS)} px; rest camera ({rx:.0f}, {ry:.0f}).  ",
              wc_line(wc) + ".", "",
              "| layer | z | blend | needed (units) | needed px | content (units) | solid | max mag | flags |",
              "|---|---|---|---|---|---|---|---|---|"]
        for i in layer_order(p):
            ly, e = p["layers"][i], ext[i]
            L.append(f"| {ly['name']} | {ly['z']} | {blend_txt(ly)} | {fmt_rect(e['need'])} | {e['need_px'][0]} x {e['need_px'][1]} | "
                     f"{fmt_rect(e['bbox']) if e['bbox'] else 'none'} | {'solid' if e['solid'] else 'partial'} | "
                     f"{e['mag']:.2f} | {'; '.join(e['flags'])} |")
        L.append("")
    with open(os.path.join(out, "extents.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))


# ---------------------------------------------------------------- sheets

def wrap(draw, text, fnt, width):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if draw.textlength(t, font=fnt) <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def to_u8(img):
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)


def layers_sheet(p, block, masks, ext, wc, out, base=None):
    gh, gw = block.shape[:2]
    src = base if base is not None else block
    g = cv2.cvtColor(to_u8(src), cv2.COLOR_RGB2GRAY).astype(np.float32) / 255
    pic = np.repeat(g[..., None], 3, 2)
    owner = -np.ones((gh, gw), np.int32)
    for i in layer_order(p):
        if p["layers"][i].get("blend") != "add" and i in masks:
            owner[masks[i] > 0.5] = i
    for i, ly in enumerate(p["layers"]):
        if ly.get("blend") == "add":
            continue
        m = owner == i
        pic[m] = pic[m] * 0.45 + rgb(ly["map"]) * 0.55
    u8 = to_u8(pic)
    # region borders
    bd = np.zeros((gh, gw), np.uint8)
    bd[:, 1:] |= (owner[:, 1:] != owner[:, :-1]).astype(np.uint8)
    bd[1:, :] |= (owner[1:, :] != owner[:-1, :]).astype(np.uint8)
    u8[bd > 0] = (u8[bd > 0] * 0.4).astype(np.uint8)
    for i, ly in enumerate(p["layers"]):
        if ly.get("blend") == "add" and i in masks:
            mm = (masks[i] > 0.06).astype(np.uint8)
            cs, _ = cv2.findContours(mm, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            col = tuple(int(v * 255) for v in rgb(ly["map"]))
            cv2.drawContours(u8, cs, -1, (0, 0, 0), 4, cv2.LINE_AA)
            cv2.drawContours(u8, cs, -1, col, 2, cv2.LINE_AA)
    im = Image.fromarray(u8)
    d = ImageDraw.Draw(im)
    f20, f28, f17 = font(20), font(28, True), font(17)
    for i, ly in enumerate(p["layers"]):
        if i not in masks:
            continue
        if ly.get("blend") == "add":
            mm = (masks[i] > 0.06).astype(np.uint8)
            hidden = ""
        else:
            mm = (owner == i).astype(np.uint8)
            hidden = ""
            if not mm.any():
                mm = (masks[i] > 0.5).astype(np.uint8)
                hidden = " (covered)"
        if not mm.any():
            continue
        n, lab, st, _ = cv2.connectedComponentsWithStats(mm, connectivity=8)
        j = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
        dt = cv2.distanceTransform((lab == j).astype(np.uint8), cv2.DIST_L2, 5)
        yy, xx = np.unravel_index(np.argmax(dt), dt.shape)
        t = f"{ly['name']} (z {ly['z']}){hidden}"
        tw = d.textlength(t, font=f20)
        x = int(min(max(4, xx - tw / 2), gw - tw - 4))
        y = int(min(max(4, yy - 13), gh - 30))
        d.rectangle([x - 5, y - 2, x + tw + 5, y + 26], fill=(0, 0, 0))
        d.rectangle([x - 5, y + 26, x + tw + 5, y + 28], fill=tuple(int(v * 255) for v in rgb(ly["map"])))
        d.text((x, y), t, font=f20, fill=(255, 255, 255))
    # header and legend
    meas = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    head = [(p["title"], f28), ("Layers, far to near. Far layers need less width than the comp (they slide less); near layers need more.", f20),
            (wc_line(wc) + ". Export every layer at this size so all align pixel for pixel.", f20)]
    hh = 16 + sum(40 if fn is f28 else 30 for _, fn in head)
    cols = dict(sw=16, fn=56, z=56 + 270, bl=56 + 270 + 80, bar=56 + 270 + 80 + 190, sz=56 + 270 + 80 + 190 + 230)
    notex = cols["sz"] + 150
    notew = max(220, gw - notex - 16)
    rows = []
    for i in layer_order(p):
        ly = p["layers"][i]
        nl = wrap(meas, ly["note"] + ("  [" + "; ".join(ext[i]["flags"]) + "]" if ext[i]["flags"] else ""), f17, notew)
        rows.append((i, nl, max(34, 8 + 22 * len(nl))))
    lh = 44 + sum(r[2] for r in rows) + 12
    sheet = Image.new("RGB", (gw, hh + gh + lh), (18, 18, 20))
    sheet.paste(im, (0, hh))
    d = ImageDraw.Draw(sheet)
    y = 12
    for t, fn in head:
        d.text((16, y), t, font=fn, fill=(240, 240, 240))
        y += 40 if fn is f28 else 30
    y = hh + gh + 10
    for k, t in (("fn", "file"), ("z", "depth z"), ("bl", "blend"), ("bar", "needed width vs plate"), ("sz", "needed px")):
        d.text((cols[k], y), t, font=f17, fill=(170, 170, 170))
    d.text((notex, y), "note", font=f17, fill=(170, 170, 170))
    y += 32
    PW = p["size"][0]
    for i, nl, rh in rows:
        ly, e = p["layers"][i], ext[i]
        col = tuple(int(v * 255) for v in rgb(ly["map"]))
        d.rectangle([cols["sw"], y + 4, cols["sw"] + 26, y + 26], fill=col, outline=(200, 200, 200) if ly.get("blend") == "add" else None, width=2)
        d.text((cols["fn"], y), fname(p, ly), font=f20, fill=(235, 235, 235))
        d.text((cols["z"], y), f"{ly['z']}", font=f20, fill=(235, 235, 235))
        d.text((cols["bl"], y), blend_txt(ly), font=f20, fill=(235, 235, 235))
        # bar: the plate's width in gray; the needed span in the map colour (it may run past the plate)
        bx0, bw = cols["bar"] + 30, 160
        lo = min(0, e["need"][0]); hi = max(PW, e["need"][2])
        sc = bw / (hi - lo) * min(1.0, (hi - lo) / PW) if hi - lo > 0 else 1
        sc = bw / max(PW, hi - lo)
        o = bx0 - (0 - lo) * sc if lo < 0 else bx0
        d.rectangle([o, y + 10, o + PW * sc, y + 20], fill=(80, 80, 84))
        d.rectangle([o + e["need"][0] * sc, y + 13, o + e["need"][2] * sc, y + 17], fill=col)
        if e["bbox"]:
            d.line([o + e["bbox"][0] * sc, y + 23, o + e["bbox"][2] * sc, y + 23], fill=(200, 200, 200), width=2)
        d.text((cols["sz"], y), f"{e['need_px'][0]} x {e['need_px'][1]}", font=f20, fill=(235, 235, 235))
        for j, t in enumerate(nl):
            d.text((notex, y + 2 + 22 * j), t, font=f17, fill=(205, 205, 205))
        y += rh
    sheet.save(os.path.join(out, f"{p['id']}_layers.png"))


def dashed_rect(img, a, b, col, th, dash=18):
    x0, y0 = a; x1, y1 = b
    for (p0, p1) in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        n = max(1, int(L // dash))
        for k in range(0, n, 2):
            s0, s1 = k / n, min(1, (k + 1) / n)
            q0 = (int(p0[0] + (p1[0] - p0[0]) * s0), int(p0[1] + (p1[1] - p0[1]) * s0))
            q1 = (int(p0[0] + (p1[0] - p0[0]) * s1), int(p0[1] + (p1[1] - p0[1]) * s1))
            cv2.line(img, q0, q1, col, th, cv2.LINE_AA)


def notes_sheet(p, block, out, base=None):
    gh, gw = block.shape[:2]
    sx, sy = gw / p["size"][0], gh / p["size"][1]
    src = base if base is not None else block
    u8 = to_u8(src * 0.45)
    keys = sorted(p["camera"], key=lambda k: k["t"])
    cam = camera(keys, *p["size"])
    pts = [cam(t) for t in np.arange(0, p["until"] - p["at"] + 1e-9, 1 / 30.0)]
    path = np.array([[c[0] * sx, c[1] * sy] for c in pts])
    labels = []
    seen = {}
    zc, dc = 1.0, 0.0
    for i, k in enumerate(keys):
        zc = k.get("zoom", zc); dc = k.get("dolly", dc)
        hw, hh = FRAME[0] / 2 * (1 - dc) / zc, FRAME[1] / 2 * (1 - dc) / zc
        a = (int((k["x"] - hw) * sx), int((k["y"] - hh) * sy))
        b = (int((k["x"] + hw) * sx), int((k["y"] + hh) * sy))
        if i == 0:
            cv2.rectangle(u8, a, b, (255, 255, 255), 3, cv2.LINE_AA)
        elif i == len(keys) - 1:
            dashed_rect(u8, a, b, (255, 208, 112), 3)
        else:
            cv2.rectangle(u8, a, b, (150, 190, 255), 1, cv2.LINE_AA)
        key = (round(k["x"]), round(k["y"]), round(zc, 3), round(dc, 3))
        stack = seen.get(key, 0)
        seen[key] = stack + 1
        labels.append((a, stack, i, tfmt(p["at"] + k["t"]) + (f"  zoom {zc:.2f}" + (f", dolly {dc:.2f}" if dc else ""))))
    if len(path) > 1 and np.ptp(path, axis=0).max() > 4:
        cv2.polylines(u8, [np.round(path * 16).astype(np.int32)], False, (255, 208, 112), 2, cv2.LINE_AA, shift=4)
        # the arrow head at the end of the move
        end = path[-1]
        j = len(path) - 1
        while j > 0 and np.hypot(*(path[j] - end)) < 30:
            j -= 1
        cv2.arrowedLine(u8, tuple(int(v) for v in path[j]), tuple(int(v) for v in end), (255, 208, 112), 3, cv2.LINE_AA, tipLength=0.6)
        for c in path[::30]:
            cv2.circle(u8, (int(c[0]), int(c[1])), 3, (255, 208, 112), -1, cv2.LINE_AA)
    im = Image.fromarray(u8)
    d = ImageDraw.Draw(im)
    f20, f28 = font(20), font(28, True)
    placed = []
    for a, stack, i, t in labels:
        tw = d.textlength(t, font=f20)
        x = int(min(max(4, a[0] + 6), gw - tw - 8))
        y = int(min(max(4, a[1] + 6), gh - 30))
        while any(x < q[2] and x + tw > q[0] and y < q[3] and y + 27 > q[1] for q in placed):
            y += 30
        placed.append((x - 4, y - 1, x + tw + 4, y + 26))
        col = (255, 255, 255) if i == 0 else ((255, 208, 112) if i == len(keys) - 1 else (150, 190, 255))
        d.rectangle([x - 4, y - 1, x + tw + 4, y + 26], fill=(0, 0, 0))
        d.text((x, y), t, font=f20, fill=col)
    meas = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    beats = sorted(p["beats"], key=lambda b: b["t"])
    foot = []
    for b in beats:
        ls = wrap(meas, b["text"], f20, gw - 130)
        foot.append((tfmt(p["at"] + b["t"]), ls))
    fh = 20 + sum(26 * len(ls) + 8 for _, ls in foot)
    hh = 90
    sheet = Image.new("RGB", (gw, hh + gh + fh), (18, 18, 20))
    sheet.paste(im, (0, hh))
    d = ImageDraw.Draw(sheet)
    d.text((16, 10), p["title"], font=f28, fill=(240, 240, 240))
    d.text((16, 52), f"Film {tfmt(p['at'])} to {tfmt(p['until'])}.  Painting {round(p['size'][0] * DENS)} x {round(p['size'][1] * DENS)} px.  "
                     "Frames: first solid white, middle thin blue, last dashed gold; the gold line is the path of the centre.",
           font=f20, fill=(210, 210, 210))
    y = hh + gh + 12
    for t, ls in foot:
        d.text((16, y), t, font=f20, fill=(255, 208, 112))
        for j, l in enumerate(ls):
            d.text((110, y + 26 * j), l, font=f20, fill=(225, 225, 225))
        y += 26 * len(ls) + 8
    sheet.save(os.path.join(out, f"{p['id']}_notes.png"))


def contact(out_f, items, cols, cell, label_px=22):
    """items: (label, rgb u8 image). A labelled grid."""
    f = font(label_px, True)
    cells = []
    for lab, im in items:
        h, w = im.shape[:2]
        r = cv2.resize(im, (cell, int(h * cell / w)), interpolation=cv2.INTER_AREA)
        pi = Image.fromarray(r)
        d = ImageDraw.Draw(pi)
        tw = d.textlength(lab, font=f)
        d.rectangle([0, 0, tw + 12, label_px + 10], fill=(0, 0, 0))
        d.text((6, 3), lab, font=f, fill=(255, 255, 255))
        cells.append(pi)
    rows = [cells[i:i + cols] for i in range(0, len(cells), cols)]
    H = sum(max(c.height for c in r) + 6 for r in rows)
    sheet = Image.new("RGB", (cols * (cell + 6), H), (12, 12, 12))
    y = 0
    for r in rows:
        for j, c in enumerate(r):
            sheet.paste(c, (j * (cell + 6) + 3, y + 3))
        y += max(c.height for c in r) + 6
    sheet.save(out_f, quality=88)
    return out_f


# ---------------------------------------------------------------- extras

def camera_sentence(p):
    keys = sorted(p["camera"], key=lambda k: k["t"])
    if len(keys) == 1:
        k = keys[0]
        return f"The camera holds still for the whole plate (zoom {k.get('zoom', 1):.2f})."
    parts = []
    z0, d0 = keys[0].get("zoom", 1), keys[0].get("dolly", 0)
    for a, b in zip(keys, keys[1:]):
        z1, d1 = b.get("zoom", z0), b.get("dolly", d0)
        dx, dy = b["x"] - a["x"], b["y"] - a["y"]
        mag0, mag1 = z0 / (1 - d0), z1 / (1 - d1)
        bits = []
        if abs(dx) > 20:
            bits.append(f"pans {'right' if dx > 0 else 'left'} {abs(dx):.0f} units")
        if abs(dy) > 20:
            bits.append(f"{'sinks' if dy > 0 else 'rises'} {abs(dy):.0f} units")
        if mag1 > mag0 * 1.01:
            bits.append(f"pushes in from {mag0:.2f}x to {mag1:.2f}x" + (" by moving forward" if d1 != d0 else ""))
        elif mag1 < mag0 * 0.99:
            bits.append(f"pulls back from {mag0:.2f}x to {mag1:.2f}x" + (" by moving back" if d1 != d0 else ""))
        dt = b["t"] - a["t"]
        if bits:
            s = f"from {tfmt(p['at'] + a['t'])} over {dt:.1f} s it " + " and ".join(bits)
            if b.get("ease") == "inout":
                s += ", easing in and out"
        else:
            s = f"from {tfmt(p['at'] + a['t'])} it holds for {dt:.1f} s"
        parts.append(s)
        z0, d0 = z1, d1
    if p["until"] - p["at"] > keys[-1]["t"] + 0.05:
        parts.append(f"it holds to {tfmt(p['until'])}")
    s = "The camera starts on the first frame; " + ", then ".join(parts) + "."
    return s


def write_appendix(plates, results, out):
    L = ["# SB00: the plates, for the painter", "",
         "Each plate is a painting in layers. Paint each layer as its own file on the working canvas named for the plate, "
         "so all layers align pixel for pixel. Depth 1 is the main plane; larger depths are farther away and slide less "
         "when the camera moves; depths under 1 are nearer and slide more. Layers marked 'add' are pure light: paint them "
         "on black, and they are added over the picture.", ""]
    for p in sorted(plates, key=lambda q: q["at"]):
        ext, wc = results[p["id"]]["ext"], results[p["id"]]["wc"]
        num = p["id"][1:]
        head = f"Plate {num[:-1]}, insert" if num.endswith("u") else f"Plate {num}"
        L += [f"## {head}: {p['title']}", "",
              f"Film {tfmt(p['at'])} to {tfmt(p['until'])}. Painting {round(p['size'][0] * DENS)} x {round(p['size'][1] * DENS)} px. "
              f"{wc_line(wc)}.", "",
              camera_sentence(p), ""]
        for b in sorted(p["beats"], key=lambda b: b["t"]):
            L.append(f"- {tfmt(p['at'] + b['t'])}  {b['text']}")
        L += ["", "| file | depth | blend | needed size px | content | note | flags |", "|---|---|---|---|---|---|---|"]
        for i in layer_order(p):
            ly, e = p["layers"][i], ext[i]
            L.append(f"| {fname(p, ly)} | {ly['z']} | {blend_txt(ly)} | {e['need_px'][0]} x {e['need_px'][1]} | "
                     f"{'solid across the frame' if e['solid'] else 'partial'} | {ly['note']} | {'; '.join(e['flags'])} |")
        L.append("")
    f = os.path.join(out, "plates.md")
    with open(f, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    return f


PALETTE = [("STORY (fixed)", [("Ember", "#ff8a3a"), ("Ember highlight", "#ffd07a"),
                              ("Cage blue (only iron cages and the keeper's lamp)", "#8ac8ff"), ("The Watch slate", "#4a5064")]),
           ("GUIDES", [("Night indigo", "#1b2133"), ("Night indigo mid", "#2c3651"), ("Umber", "#2b2018"), ("Umber mid", "#4a3626"),
                       ("Ink black (warm)", "#15100c"), ("Oil flame", "#f0c060"), ("Lamp smoke", "#5e5248"), ("Legion rust", "#7a2e1f"),
                       ("Legion bronze (dull)", "#6e5a34"), ("Undyed linen", "#d6cab0"), ("Dawn gray", "#8c8a86"), ("Dawn gold", "#e6b45c"),
                       ("Dusk rose (dull)", "#8a5c5c"), ("Drowned skin", "#6e786a"), ("River weed", "#3c4a2e"), ("Under water", "#0b1713")])]


def write_palette(out):
    W = 1600
    f17, f20, f26 = font(17), font(20), font(26, True)
    per = 8
    sw = (W - 40) // per
    meas = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    blocks = []
    for title, items in PALETTE:
        rows = [items[i:i + per] for i in range(0, len(items), per)]
        blocks.append((title, rows))
    H = 20 + sum(50 + len(rows) * (sw + 95) for _, rows in blocks)
    im = Image.new("RGB", (W, H), (24, 24, 26))
    d = ImageDraw.Draw(im)
    y = 16
    for title, rows in blocks:
        d.text((20, y), title, font=f26, fill=(240, 240, 240))
        y += 46
        for row in rows:
            for j, (name, hx) in enumerate(row):
                x = 20 + j * sw
                d.rectangle([x, y, x + sw - 12, y + sw - 30], fill=tuple(int(v * 255) for v in rgb(hx)), outline=(90, 90, 90))
                d.text((x, y + sw - 24), hx, font=f20, fill=(240, 240, 240))
                for k, l in enumerate(wrap(meas, name, f17, sw - 14)[:3]):
                    d.text((x, y + sw + 2 + 20 * k), l, font=f17, fill=(200, 200, 200))
            y += sw + 95
    f = os.path.join(out, "palette.png")
    im.save(f)
    return f


def soften(files, out):
    os.makedirs(out, exist_ok=True)
    res = []
    for f in files:
        im = cv2.imread(f, cv2.IMREAD_COLOR)
        k = im.shape[1] / 1792.0
        s = cv2.pyrMeanShiftFiltering(im, sp=max(2, int(round(8 * k))), sr=18)
        s = cv2.bilateralFilter(s, 0, 12, max(2, 3 * k))
        o = os.path.join(out, os.path.splitext(os.path.basename(f))[0] + "_soft.png")
        cv2.imwrite(o, s)
        res.append(o)
    return res


def picks(plan, d, out):
    res = []
    for p in plan["plates"]:
        items = []
        for nm in (f"{p['id']}_d75_s11", f"{p['id']}_d75_s23", f"{p['id']}_d88_s11", f"{p['id']}_d88_s23"):
            for ext in (".png", ".jpg"):
                f = os.path.join(d, nm + ext)
                if os.path.exists(f):
                    items.append((nm, cv2.cvtColor(cv2.imread(f, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)))
                    break
        if items:
            res.append(contact(os.path.join(out, f"pick_{p['id']}.jpg"), items, 2, 640))
    return res


def write_jobs(plan, out):
    jobs = []
    for p in plan["plates"]:
        for tag, dn in (("d75", 0.75), ("d88", 0.88)):
            jobs.append(dict(name=f"{p['id']}_{tag}", prompt=p["prompt"], seed=[11, 23], w=p["gen"][0], h=p["gen"][1],
                             init=os.path.abspath(os.path.join(out, f"{p['id']}_block.png")), denoise=dn,
                             control=os.path.abspath(os.path.join(out, f"{p['id']}_edges.png")), strength=0.55, end=0.8))
    f = os.path.join(HERE, "jobs", "comps_r1.json")
    with open(f, "w", encoding="utf-8") as fh:
        json.dump({"defaults": {"steps": 9, "shift": 3.0}, "jobs": jobs}, fh, indent=1)
    return f


def underlay(p, wc, out):
    W, H = wc["w"], wc["h"]
    img, _ = render(p, W, H, DENS, DENS, wc["ox"], wc["oy"], keep=False)
    pw, ph = round(p["size"][0] * DENS), round(p["size"][1] * DENS)
    x0, y0 = wc["ox"], wc["oy"]
    u8 = to_u8(img)
    inside = np.zeros((H, W), bool)
    inside[y0:y0 + ph, x0:x0 + pw] = True
    u8[~inside] = 0x20
    cv2.rectangle(u8, (x0, y0), (x0 + pw - 1, y0 + ph - 1), (190, 190, 190), 2, cv2.LINE_AA)
    rx, ry = rest_of(p)
    a = (int(x0 + (rx - FRAME[0] / 2) * DENS), int(y0 + (ry - FRAME[1] / 2) * DENS))
    b = (int(x0 + (rx + FRAME[0] / 2) * DENS), int(y0 + (ry + FRAME[1] / 2) * DENS))
    dashed_rect(u8, a, b, (210, 210, 210), 2, dash=24)
    f = os.path.join(out, f"{p['id']}_underlay.jpg")
    cv2.imwrite(f, cv2.cvtColor(u8, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 90])
    return f


def selftest(plan):
    """The extents formula against StoryLens.Project: the corners and centre of the rect
    view_rect says a camera sees on a layer must land on the screen's corners and centre."""
    ok = True
    sw, sh = 3840.0, 1606.8
    cw, ch = FRAME
    n = 0
    for p in plan["plates"]:
        X0, Y0 = rest_of(p)
        for cam in samples(p)[::45]:
            for ly in p["layers"]:
                z = ly["z"]
                (x0, y0, x1, y1), mag = view_rect(cam, z, (X0, Y0))
                # StoryLens has its rest at the canvas centre: shift the plate so the rest sits there
                tx, ty = cw / 2 - X0, ch / 2 - Y0
                c2 = (cam[0] + tx, cam[1] + ty, cam[2], cam[3])
                for (px, py), (ex, ey) in (((x0, y0), (0, 0)), ((x1, y1), (sw, sh)), (((x0 + x1) / 2, (y0 + y1) / 2), (sw / 2, sh / 2))):
                    gx, gy = lens_project(c2, z, px + tx, py + ty, cw, ch, sw, sh)
                    if abs(gx - ex) > 1e-6 * sw or abs(gy - ey) > 1e-6 * sw:
                        ok = False
                        print(f"  FAIL {p['id']} z {z}: ({px:.1f}, {py:.1f}) -> ({gx:.2f}, {gy:.2f}), wanted ({ex}, {ey})")
                sc, _, _ = lens_layer(c2, z, cw, ch, sw, sh)
                if abs(sc / (sw / cw) - mag) > 1e-9:
                    ok = False
                    print(f"  FAIL mag {p['id']} z {z}")
                n += 1
    # the curve passes through its keys
    for p in plan["plates"]:
        cam = camera(p["camera"], *p["size"])
        for k in p["camera"]:
            c = cam(k["t"])
            if abs(c[0] - k["x"]) > 1e-9 or abs(c[1] - k["y"]) > 1e-9:
                ok = False
                print(f"  FAIL key {p['id']} t {k['t']}")
    print(f"selftest: {n} camera/layer cases x 3 points: {'PASS' if ok else 'FAIL'}")
    return ok


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--out", default=os.path.join(HERE, "out", "comps"))
    ap.add_argument("--base", default="")
    ap.add_argument("--jobs", action="store_true")
    ap.add_argument("--appendix", action="store_true")
    ap.add_argument("--underlay", action="store_true")
    ap.add_argument("--palette", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--picks", default="")
    ap.add_argument("--soften", nargs="+", default=None)
    a = ap.parse_args()
    with open(PLAN, encoding="utf-8") as f:
        plan = json.load(f)
    os.makedirs(a.out, exist_ok=True)
    if a.selftest or a.palette or a.picks or a.soften:
        if a.selftest:
            if not selftest(plan):
                sys.exit(1)
        if a.palette:
            print(write_palette(a.out))
        if a.picks:
            for f in picks(plan, a.picks, a.out):
                print(f)
        if a.soften:
            for f in soften(a.soften, a.out):
                print(f)
        return
    only = [s for s in a.only.split(",") if s]
    plates = [p for p in plan["plates"] if not only or p["id"] in only]
    if a.base and "{id}" not in a.base and len(plates) != 1:
        sys.exit("--base without {id} needs exactly one plate (--only)")
    results = {}
    t0 = time.time()
    for p in plates:
        t1 = time.time()
        gw, gh = p["gen"]
        sx, sy = gw / p["size"][0], gh / p["size"][1]
        block, masks = render(p, gw, gh, sx, sy)
        struct, _ = render(p, gw, gh, sx, sy, structure=True, keep=False)
        save(os.path.join(a.out, f"{p['id']}_block.png"), block)
        save(os.path.join(a.out, f"{p['id']}_structure.png"), struct)
        e = block_edges(struct)
        cv2.imwrite(os.path.join(a.out, f"{p['id']}_edges.png"), (e * 255 + 0.5).astype(np.uint8))
        ext = extents(p, masks, gw, gh)
        wc = working_canvas(p, ext)
        results[p["id"]] = dict(ext=ext, wc=wc, block=block)
        base = None
        if a.base:
            base = load_rgb(a.base.replace("{id}", p["id"]), gw, gh)
        layers_sheet(p, block, masks, ext, wc, a.out, base)
        notes_sheet(p, block, a.out, base)
        if a.underlay:
            print("  " + underlay(p, wc, a.out))
        print(f"{p['id']}: {time.time() - t1:.1f} s")
    write_extents(plates, results, a.out)
    contact(os.path.join(a.out, "sheet_block.jpg"), [(p["id"] + "  " + p["title"], to_u8(results[p["id"]]["block"])) for p in plates], 3, 530)
    if a.jobs:
        print(write_jobs(plan, a.out))
    if a.appendix:
        print(write_appendix(plates, results, a.out))
    print(f"done in {time.time() - t0:.1f} s -> {a.out}")


if __name__ == "__main__":
    main()
