"""The pad's buttons as the interface shows them (icons/prompt/*.png).

Face buttons are forged iron bosses with the letter set in as coloured
enamel (its colour and its letter: never colour alone); bumpers and
triggers are iron pills and trigger shoes with their names in gold; View
and Menu their marks; the D-pad a forged cross with the meant arm burning;
the sticks a cap with the side they belong to lit.
"""
from __future__ import annotations

import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import forge as F
import ornament as O

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FONTS = os.path.join(ROOT, "tools", "comfy", "out", "uiforge", "fonts")
FACE = {"a": "#6bc45a", "b": "#ec5a50", "x": "#4a9cf0", "y": "#f2c440"}


def font(name, size):
    path = os.path.join(FONTS, name + ".ttf")
    if not os.path.exists(path):
        from fontTools.ttLib import TTFont
        os.makedirs(FONTS, exist_ok=True)
        t = TTFont(os.path.join(ROOT, "godot", "art", "fonts", name + ".woff2"))
        t.flavor = None
        t.save(path)
    return ImageFont.truetype(path, size)


def text_mask(w, h, text, fnt, cx=None, cy=None, tracking=0):
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    bbox = d.textbbox((0, 0), text, font=fnt)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    cx = w / 2 if cx is None else cx
    cy = h / 2 if cy is None else cy
    d.text((cx - tw / 2 - bbox[0], cy - th / 2 - bbox[1]), text, font=fnt, fill=255)
    return np.asarray(im, np.float32) / 255


def _iron_disc(s, cx, cy, r, k):
    sd = F.sd_circle(s.xx, s.yy, cx, cy, r)
    cov = F.coverage(sd, 1.0)
    # A rolled rim, a slightly domed face.
    rim = np.clip(1 - np.abs(sd - r * 0.09) / (r * 0.09), 0, 1) ** 0.6 * r * 0.10
    dome = np.sqrt(np.clip(sd / r, 0, 1)) * r * 0.10
    edge = F.bevel(sd, r * 0.06, r * 0.10)
    h = edge + rim + dome * 0.6
    fac = F.facets(s.h, s.w, cell=r * 0.5, tilt=0.015, seed=3, soften=3.0 * k) * cov
    O.put(s, cov, h + fac, "iron_dark")
    s.alpha = np.maximum(s.alpha, cov)
    return sd


def _pill(s, x0, y0, x1, y1, r, k, mat="iron_dark"):
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    sd = F.sd_box(s.xx, s.yy, cx, cy, (x1 - x0) / 2, (y1 - y0) / 2, r)
    cov = F.coverage(sd, 1.0)
    rim = np.clip(1 - np.abs(sd - r * 0.18) / (r * 0.18), 0, 1) ** 0.6 * r * 0.16
    edge = F.bevel(sd, r * 0.12, r * 0.18)
    fac = F.facets(s.h, s.w, cell=r * 0.8, tilt=0.015, seed=5, soften=3.0 * k) * cov
    O.put(s, cov, edge + rim + fac, mat)
    return sd


def _inlay(s, mask, colour, depth, lift=0.0, enamel=True):
    """A mask set into the surface: coloured enamel, slightly proud and glossy."""
    m = mask
    s.height = s.height - m * depth + F.blur(m, 1.2) * lift
    col = F.hexc(colour)
    s.albedo = s.albedo * (1 - m[..., None]) + col * m[..., None]
    s.metal = s.metal * (1 - m)
    s.rough = s.rough * (1 - m) + 0.18 * m


def face(letter, size=104, ss=4):
    W = size * ss
    s = F.Surface(W, W)
    k = ss
    r = W * 0.47
    _iron_disc(s, W / 2, W / 2, r, k)
    fnt = font("alegreya-sans-800", int(W * 0.70))
    m = text_mask(W, W, letter.upper(), fnt, cy=W * 0.5)
    _inlay(s, m, FACE[letter], depth=1.5 * k, lift=0.8 * k)
    lin = s.shade(normal_strength=1.0, ao=0.6, shadow=0.4, light_elev=40)
    # The enamel's own colour carries: lift it so it reads at 26 px.
    lin = lin + m[..., None] * F.hexc(FACE[letter]) * 0.30
    return s.finish(lin, size=(size, size))


def pill(text, size=(136, 104), ss=4, trigger=False):
    W, H = size[0] * ss, size[1] * ss
    s = F.Surface(W, H)
    k = ss
    if trigger:
        # A trigger: its top swept round like the trigger's own shoe, its foot square.
        cx = W / 2
        body = F.sd_box(s.xx, s.yy, cx, H * 0.55, W * 0.43, H * 0.33, H * 0.08)
        top = F.sd_box(s.xx, s.yy, cx, H * 0.42, W * 0.43, H * 0.30, H * 0.30)
        sdu = np.maximum(np.minimum(body, F.sd_box(s.xx, s.yy, cx, H * 0.70, W * 0.5, H * 0.30, 0)), top)
        cov = F.coverage(sdu, 1.0)
        edge = F.bevel(sdu, H * 0.05, H * 0.08)
        rim = np.clip(1 - np.abs(sdu - H * 0.06) / (H * 0.06), 0, 1) ** 0.6 * H * 0.06
        O.put(s, cov, edge + rim, "iron_dark")
    else:
        _pill(s, W * 0.05, H * 0.14, W * 0.95, H * 0.86, H * 0.34, k)
    fnt = font("alegreya-sans-800", int(H * 0.56))
    m = text_mask(W, H, text, fnt, cy=H * (0.55 if trigger else 0.5))
    _inlay(s, m, "#f3d9a0", depth=1.2 * k, lift=0.6 * k)
    s.metal = s.metal * (1 - m) + m
    s.rough = s.rough * (1 - m) + 0.3 * m
    lin = s.shade(normal_strength=1.0, ao=0.6, shadow=0.4, light_elev=40)
    lin = lin + m[..., None] * F.hexc("#d9b56a") * 0.25
    return s.finish(lin, size=size)


def mark_pill(kind, size=(136, 104), ss=4):
    """View (two overlapping windows) and Menu (three bars) on an iron pill."""
    W, H = size[0] * ss, size[1] * ss
    s = F.Surface(W, H)
    k = ss
    _pill(s, W * 0.05, H * 0.14, W * 0.95, H * 0.86, H * 0.34, k)
    m = np.zeros((H, W), np.float32)
    cx, cy = W / 2, H / 2
    lw = H * 0.075
    if kind == "view":
        for dx, dy in ((-0.07, -0.06), (0.07, 0.06)):
            bx, by = cx + dx * W, cy + dy * H
            o = F.sd_box(s.xx, s.yy, bx, by, W * 0.13, H * 0.17, H * 0.03)
            ring = F.coverage(lw / 2 - np.abs(o), 1.0)
            m = np.maximum(m * (1 - F.coverage(o + lw / 2, 1.0) * (dx > 0)), ring)
    else:
        for dy in (-0.16, 0, 0.16):
            o = F.sd_box(s.xx, s.yy, cx, cy + dy * H, W * 0.17, lw / 2, lw / 2)
            m = np.maximum(m, F.coverage(o, 1.0))
    _inlay(s, m, "#f3d9a0", depth=1.0 * k, lift=0.5 * k)
    s.metal = s.metal * (1 - m) + m
    lin = s.shade(normal_strength=1.0, ao=0.6, shadow=0.4, light_elev=40)
    lin = lin + m[..., None] * F.hexc("#d9b56a") * 0.25
    return s.finish(lin, size=size)


def dpad(arm=None, size=104, ss=4):
    W = size * ss
    s = F.Surface(W, W)
    k = ss
    c = W / 2
    a = W * 0.155  # half arm width
    L = W * 0.46
    sd = np.maximum(F.sd_box(s.xx, s.yy, c, c, L, a, a * 0.35), F.sd_box(s.xx, s.yy, c, c, a, L, a * 0.35))
    cov = F.coverage(sd, 1.0)
    edge = F.bevel(sd, W * 0.03, W * 0.05)
    # Each arm a shallow dish toward its tip; the centre a small dimple.
    dish = -np.clip(1 - np.hypot(s.xx - c, s.yy - c) / (a * 0.8), 0, 1) * W * 0.02
    O.put(s, cov, edge + dish, "iron_dark")
    lit = np.zeros((W, W), np.float32)
    arms = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
    for name, (dx, dy) in arms.items():
        # A chevron on each arm pointing out.
        tip = (c + dx * L * 0.78, c + dy * L * 0.78)
        base1 = (c + dx * L * 0.52 + dy * a * 0.55, c + dy * L * 0.52 + dx * a * 0.55)
        base2 = (c + dx * L * 0.52 - dy * a * 0.55, c + dy * L * 0.52 - dx * a * 0.55)
        tri = F.coverage(F.sd_poly(s.xx, s.yy, [tip, base1, base2]), 1.0)
        on = arm is None or arm == name
        _inlay(s, tri, "#f3d9a0" if on else "#5a4a30", depth=0.8 * k, lift=0.4 * k)
        if on:
            lit = np.maximum(lit, tri)
            s.metal = s.metal * (1 - tri) + tri
    lin = s.shade(normal_strength=1.0, ao=0.6, shadow=0.4, light_elev=40)
    if arm is not None:
        # The meant arm burns.
        lin = lin + lit[..., None] * F.hexc("#ffb050") * 0.8 + F.blur(lit, W * 0.03)[..., None] * F.hexc("#ff8a3a") * 0.6
    else:
        lin = lin + lit[..., None] * F.hexc("#d9b56a") * 0.2
    return s.finish(lin, size=(size, size))


def stick(side, size=104, ss=4):
    W = size * ss
    s = F.Surface(W, W)
    k = ss
    c = W / 2
    r = W * 0.46
    sd = F.sd_circle(s.xx, s.yy, c, c, r)
    cov = F.coverage(sd, 1.0)
    # A stick cap: a raised rim of grip ridges round a dished top.
    rr = np.hypot(s.xx - c, s.yy - c)
    ang = np.arctan2(s.yy - c, s.xx - c)
    ridges = (0.5 + 0.5 * np.cos(ang * 24)) * np.clip((rr - r * 0.70) / (r * 0.2), 0, 1) * W * 0.012
    dish = -np.clip(1 - rr / (r * 0.68), 0, 1) ** 2 * W * 0.035
    edge = F.bevel(sd, W * 0.04, W * 0.08)
    O.put(s, cov, edge + ridges + dish, "iron_dark")
    # The side it is: a burning arc on that side of the rim (no letter).
    side_ang = math.pi if side == "l" else 0.0
    da = np.abs((ang - side_ang + math.pi) % (2 * math.pi) - math.pi)
    arc = F.coverage(W * 0.035 - np.abs(rr - r * 0.84), 1.0) * (da < 0.9)
    _inlay(s, arc, "#f3d9a0", depth=0.5 * k, lift=0.3 * k)
    lin = s.shade(normal_strength=1.0, ao=0.6, shadow=0.4, light_elev=40)
    lin = lin + arc[..., None] * F.hexc("#ffb050") * 0.9 + F.blur(arc, W * 0.02)[..., None] * F.hexc("#ff8a3a") * 0.5
    return s.finish(lin, size=(size, size))


def build(out_dir):
    made = {}
    for l in "abxy":
        made[f"pad_{l}"] = face(l)
    made["pad_lb"] = pill("LB")
    made["pad_rb"] = pill("RB")
    made["pad_lt"] = pill("LT", trigger=True)
    made["pad_rt"] = pill("RT", trigger=True)
    made["pad_view"] = mark_pill("view")
    made["pad_menu"] = mark_pill("menu")
    made["pad_dpad"] = dpad(None)
    for a in ("up", "down", "left", "right"):
        made[f"pad_dpad_{a}"] = dpad(a)
    made["pad_lstick"] = stick("l")
    made["pad_rstick"] = stick("r")
    os.makedirs(out_dir, exist_ok=True)
    for name, im in made.items():
        F.save(im, os.path.join(out_dir, name + ".png"))
    return made
