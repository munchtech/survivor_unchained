"""The kit laid out on a page, at 1920x1080 or 2560x1440, to judge its pieces together and at
1:1 without a Godot run. It composes what Backdrop and UiArt do (the page's vellum and light,
the head and foot bands, nine-slices drawn as Godot draws them, a panel's ground tiled at 1:1
under its edge) and writes a page of every surface in the kit with real words on it. The game's
own shots are still the judge before anything goes in; this is for getting there quickly.

    python tools/uiforge/kitboard.py [--src kit|game] [--scale 1|1.333] [--out PATH]

  --src kit   the pieces in tools/comfy/out/uiforge/kit/ (default), else the game's art
"""
from __future__ import annotations

import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import forge as F

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
UI = os.path.join(ROOT, "godot", "art", "ui")
KIT = os.path.join(ROOT, "tools", "comfy", "out", "uiforge", "kit")
FONTS = os.path.join(ROOT, "tools", "comfy", "out", "uiforge", "fonts")


def font_path(name):
    """The game's woff2 as a ttf PIL can read (made once, beside the kit's outputs)."""
    p = os.path.join(FONTS, name + ".ttf")
    if not os.path.exists(p):
        from fontTools.ttLib import TTFont
        os.makedirs(FONTS, exist_ok=True)
        t = TTFont(os.path.join(ROOT, "godot", "art", "fonts", name + ".woff2"))
        t.flavor = None
        t.save(p)
    return p


def load(rel, src="kit"):
    """A piece as straight-alpha float RGBA: the kit's if it has one (when asked), else the game's."""
    for root in ((KIT, UI) if src == "kit" else (UI,)):
        p = os.path.join(root, rel)
        if os.path.exists(p):
            return np.asarray(Image.open(p).convert("RGBA"), np.float32) / 255
    return None


def resize(img, w, h):
    w, h = max(1, int(round(w))), max(1, int(round(h)))
    if w == img.shape[1] and h == img.shape[0]:
        return img
    interp = cv2.INTER_AREA if w < img.shape[1] or h < img.shape[0] else cv2.INTER_LINEAR
    return cv2.resize(img, (w, h), interpolation=interp)


def axis(n_src, n_dst, tile, s):
    """Source and destination spans for one axis' middle: TileFit repeats the source middle a
    whole number of times, each stretched to fit; Stretch draws it once."""
    if not tile:
        return [(0, n_src, 0, n_dst)]
    natural = n_src * s / 2
    count = max(1, int(round(n_dst / max(natural, 1e-6))))
    step = n_dst / count
    return [(0, n_src, i * step, (i + 1) * step) for i in range(count)]


class Canvas:
    """A screen at `s` screen px per shown px. Godot blends 2D in sRGB (no HDR 2D), so this
    does too: a light laid at an alpha looks here as it will in the game."""

    def __init__(self, W, H, s):
        self.s, self.W, self.H = s, int(W * s), int(H * s)
        self.rgb = np.zeros((self.H, self.W, 3), np.float32)

    def over(self, img, x, y, alpha=1.0):
        """Lay straight-alpha sRGB `img` (screen px) at screen (x, y)."""
        x, y = int(round(x)), int(round(y))
        h, w = img.shape[:2]
        x0, y0, x1, y1 = max(0, x), max(0, y), min(self.W, x + w), min(self.H, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        part = img[y0 - y:y1 - y, x0 - x:x1 - x]
        a = part[..., 3:4] * alpha
        self.rgb[y0:y1, x0:x1] = self.rgb[y0:y1, x0:x1] * (1 - a) + np.clip(part[..., :3], 0, 1) * a

    def fill(self, x, y, w, h, rgb, a):
        s = self.s
        x0, y0 = int(round(x * s)), int(round(y * s))
        x1, y1 = int(round((x + w) * s)), int(round((y + h) * s))
        self.rgb[y0:y1, x0:x1] = self.rgb[y0:y1, x0:x1] * (1 - a) + np.asarray(rgb, np.float32) * a

    def tiled(self, tex, x, y, w, h, tint=(1, 1, 1, 1), phase=(0, 0)):
        """A texture made at twice its shown size, repeated at 1:1 over a shown rect."""
        s = self.s
        tw, th = tex.shape[1] * s / 2, tex.shape[0] * s / 2
        t = resize(tex, tw, th)
        X0, Y0 = int(round(x * s)), int(round(y * s))
        X1, Y1 = int(round((x + w) * s)), int(round((y + h) * s))
        reps = ((Y1 - Y0) // t.shape[0] + 2, (X1 - X0) // t.shape[1] + 2, 1)
        big = np.tile(t, reps)
        px, py = int(phase[0] * s) % t.shape[1], int(phase[1] * s) % t.shape[0]
        big = big[py:py + Y1 - Y0, px:px + X1 - X0].copy()
        big[..., :3] *= np.asarray(tint[:3], np.float32)
        big[..., 3] *= tint[3]
        self.over(big, X0, Y0)

    def nine(self, tex, x, y, w, h, L, T, R, B, tile=False, out=0, outy=None, alpha=1.0):
        """A nine-slice as Godot draws it: margins in shown px, the art at twice that."""
        outy = out if outy is None else outy
        s = self.s
        x, y, w, h = x - out, y - outy, w + 2 * out, h + 2 * outy
        sw, sh = tex.shape[1], tex.shape[0]
        sx = [0, 2 * L, sw - 2 * R, sw]
        sy = [0, 2 * T, sh - 2 * B, sh]
        dx = [x * s, (x + L) * s, (x + w - R) * s, (x + w) * s]
        dy = [y * s, (y + T) * s, (y + h - B) * s, (y + h) * s]
        X0, Y0 = int(round(dx[0])), int(round(dy[0]))
        out_img = np.zeros((int(round(dy[3])) - Y0, int(round(dx[3])) - X0, 4), np.float32)
        for j in range(3):
            for i in range(3):
                src = tex[sy[j]:sy[j + 1], sx[i]:sx[i + 1]]
                if src.size == 0:
                    continue
                xs = axis(src.shape[1], dx[i + 1] - dx[i], tile and i == 1, s) if i == 1 else [(0, src.shape[1], 0, dx[i + 1] - dx[i])]
                ys = axis(src.shape[0], dy[j + 1] - dy[j], tile and j == 1, s) if j == 1 else [(0, src.shape[0], 0, dy[j + 1] - dy[j])]
                pm = np.dstack([src[..., :3] * src[..., 3:4], src[..., 3:4]])
                for (_, _, a0, a1) in xs:
                    for (_, _, b0, b1) in ys:
                        px0, py0 = int(round(dx[i] + a0)) - X0, int(round(dy[j] + b0)) - Y0
                        px1, py1 = int(round(dx[i] + a1)) - X0, int(round(dy[j] + b1)) - Y0
                        if px1 <= px0 or py1 <= py0:
                            continue
                        out_img[py0:py1, px0:px1] = resize(pm, px1 - px0, py1 - py0)
        a = out_img[..., 3:4]
        straight = np.dstack([np.where(a > 1e-4, out_img[..., :3] / np.maximum(a, 1e-4), 0), a])
        self.over(straight, X0, Y0, alpha)

    def text(self, x, y, s_, font, size, rgb, anchor="la", shadow=True):
        """Words at shown (x, y), drawn at screen size (shadowed as Style.Font draws them)."""
        s = self.s
        fnt = ImageFont.truetype(font_path(font), int(round(size * s)))
        bbox = fnt.getbbox(s_, anchor=anchor)
        pad = int(4 * s)
        w, h = bbox[2] - bbox[0] + pad * 2, bbox[3] - bbox[1] + pad * 2
        X, Y = int(round(x * s)) + bbox[0] - pad, int(round(y * s)) + bbox[1] - pad
        for off, col, al in (((1, 1), (0, 0, 0), 0.75), ((0, 0), rgb, 1.0)) if shadow else (((0, 0), rgb, 1.0),):
            im = Image.new("L", (w, h), 0)
            ImageDraw.Draw(im).text((pad - bbox[0] + off[0] * s, pad - bbox[1] + off[1] * s), s_, font=fnt, fill=255, anchor=anchor)
            a = np.asarray(im, np.float32)[..., None] / 255 * al
            c = np.broadcast_to(np.asarray(F.hexc(col, lin=False) if isinstance(col, str) else col, np.float32), (h, w, 3))
            self.over(np.dstack([c, a[..., 0]]), X, Y)

    def image(self):
        return Image.fromarray((np.clip(self.rgb, 0, 1) * 255 + 0.5).astype(np.uint8))


def world(cv: Canvas):
    """The blurred, darkened world behind a page (an approximation of ui_backdrop.gdshader)."""
    w = cv2.resize(world_still(), (cv.W, cv.H), interpolation=cv2.INTER_LINEAR)
    w = cv2.GaussianBlur(w, (0, 0), 18 * cv.s)
    l = (w * [0.3, 0.59, 0.11]).sum(-1, keepdims=True)
    w = w * 0.45 + l * 0.55
    lit = np.clip((l - 0.08) / 0.62, 0, 1)
    w = w * (np.array([0.42, 0.42, 0.58]) * (1 - lit) + np.array([0.95, 0.8, 0.66]) * lit) * 0.66
    cv.rgb[:] = np.clip(w, 0, 1)


def backdrop(cv: Canvas, src):
    """Backdrop(page: true): the vellum at 0.9, the bands' shades, the edges, the grain, the dark."""
    world(cv)
    vel = load("page/vellum.png", src)
    cv.tiled(vel, 0, 0, 1920, 1080, (1, 1, 1, 0.9))
    s = cv.s
    ys = np.arange(cv.H, dtype=np.float32)[:, None] / s
    for y0, hgt, down, depth in ((90, 70, True, 0.6), (975, 50, False, 0.45)):
        t = (ys - y0) / hgt
        a = np.where((t >= 0) & (t <= 1), (1 - t if down else t) * depth, 0)
        cv.rgb[:] = cv.rgb * (1 - a[..., None]) + np.array([0.01, 0.008, 0.014]) * a[..., None]
    edges = load("page/backdrop_edges.png", src)
    if edges is not None:
        cv.over(resize(edges, cv.W, cv.H), 0, 0)
    grain = load("page/backdrop_grain.png", src)
    if grain is not None:
        cv.tiled(grain, 0, 0, 1920, 1080)
    # The radial dark toward the edges, and the ember low along the foot (Backdrop's gradients).
    yy, xx = np.mgrid[0:cv.H, 0:cv.W].astype(np.float32)
    u, v = xx / cv.W, yy / cv.H
    d = np.hypot(u - 0.5, v - 0.45) / np.hypot(0.55, 0.6)
    t = np.clip((d - 0.2) / 0.8, 0, 1)
    a = (0.88 * 0.12) * (1 - t) + (0.88 * 0.7) * t
    cv.rgb[:] = cv.rgb * (1 - a[..., None]) + np.array([0.025, 0.018, 0.035]) * a[..., None]
    e = np.clip(1 - (1 - v) / 0.2, 0, 1) * 0.08
    cv.rgb[:] = cv.rgb * (1 - e[..., None]) + np.array([1, 0.42, 0.12]) * e[..., None]


# The kit's slices (shown px): name -> (file, L, T, R, B, tile, out, ground, ground tint)
SLICES = {}


def piece(cv: Canvas, name, x, y, w, h, src="kit", phase=None):
    """A frame by name as UiArt draws it: its ground tiled at 1:1 inside, then its nine-slice."""
    import kit
    sl = kit.SLICES[name]
    tex = load(sl.file, src)
    if tex is None:
        return
    if sl.ground:
        g = load(sl.ground, src)
        ph = phase if phase is not None else (x * 7.3 + y * 3.1, y * 5.7 + x * 1.3)
        cv.tiled(g, x + sl.inset, y + sl.inset, w - 2 * sl.inset, h - 2 * sl.inset, sl.tint, ph)
    cv.nine(tex, x, y, w, h, sl.L, sl.T, sl.R, sl.B, sl.tile, sl.out, sl.out)


def specimen(cv: Canvas, src="kit"):
    """A page of every surface in the kit, laid as the screens lay them, with words on them."""
    import kit
    backdrop(cv, src)
    hd, ft = load("frames/header.png", src), load("frames/footer.png", src)
    cv.nine(hd, 0, 0, 1920, 100, 0, 0, 0, 12, True)
    cv.nine(ft, 0, 1016, 1920, 68, 0, 12, 0, 0, True)
    ink, ink_dim, gold, gold_hi = "#e8dcc8", "#a89c8c", "#c9a256", "#f0d9a0"
    # The tabs: words, the one open marked.
    x = 60
    for i, t in enumerate(["Pack", "Self", "Arts", "Journal", "Map"]):
        on = i == 1
        fnt = ImageFont.truetype(font_path("alegreya-sans-700"), 17)
        tw = fnt.getlength(t)
        if on:
            piece(cv, "tab_on", x - 10, 30, tw + 46, 34, src)
        cv.text(x, 52, t, "alegreya-sans-700", 17, gold_hi if on else ink_dim, "ls")
        piece(cv, "keycap", x + tw + 8, 34, 20, 20, src)
        cv.text(x + tw + 18, 49, "ICKJM"[i], "alegreya-sans-700", 12, ink_dim, "ms", shadow=False)
        x += tw + 60
    cv.text(960, 52, "WREN", "cinzel-700", 38, gold_hi, "ms")
    cv.text(960, 76, "Level 1 · Hunter Warden", "alegreya-400-italic", 15, ink_dim, "ms")
    # The figure's panel.
    piece(cv, "panel", 80, 140, 400, 430, src)
    # The attributes: a row of four, each a number, a name and a line.
    for i, (nm, n) in enumerate([("Might", "6"), ("Finesse", "3"), ("Wits", "3"), ("Resolve", "6")]):
        px = 560 + i * 214
        piece(cv, "panel", px, 140, 198, 150, src)
        rr = load("medallion/ring.png", src)
        if rr is not None:
            cv.over(resize(rr, 72 * cv.s, 72 * cv.s), (px + 99 - 36) * cv.s, 156 * cv.s)
        cv.text(px + 99, 210, n, "cinzel-700", 36, gold_hi, "ms")
        cv.text(px + 99, 252, nm.upper(), "cinzel-700", 17, gold, "ms")
        cv.text(px + 99, 276, "+2.5% damage a point", "alegreya-sans-500", 14, ink_dim, "ms")
    # A section head: words and a pressed rule.
    cv.text(560, 330, "TRAITS", "alegreya-sans-800", 13, gold, "ls")
    cv.text(622, 330, "chosen at levels, or given for what you do", "alegreya-400-italic", 14, ink_dim, "ls")
    piece(cv, "rule_h", 920, 322, 490, 6, src)
    # The traits' well, a row of empty and taken places.
    piece(cv, "well", 560, 345, 850, 120, src)
    for i in range(6):
        px = 576 + i * 138
        piece(cv, "slot" if i > 1 else "slot_2", px, 361, 88, 88, src)
    # Slots: empty, and filled at each rarity.
    for i in range(8):
        px = 560 + i * 106
        nm = "slot" if i >= 6 else f"slot_{i}"
        piece(cv, nm, px, 500, 88, 88, src)
    # Buttons: normal, hover, pressed, primary, disabled; and a chip.
    bx = 560
    for nm, t in (("button", "Sort"), ("button_hover", "Hover"), ("button_pressed", "Pressed"),
                  ("button_primary", "Take all"), ("button_disabled", "Can't")):
        piece(cv, nm, bx, 620, 140, 40, src)
        cv.text(bx + 70, 646, t, "alegreya-sans-700", 16, gold_hi if nm != "button_disabled" else "#706658", "ms")
        bx += 156
    piece(cv, "chip", 1350, 626, 120, 28, src)
    cv.text(1410, 646, "Beastlore", "alegreya-sans-500", 14, ink, "ms")
    # A tooltip card over it all.
    piece(cv, "tooltip", 1480, 140, 380, 300, src)
    cv.fill(1480, 140, 380, 3, (0.35, 0.65, 1.0), 0.9)
    cv.text(1500, 176, "Moonsilver Circlet", "cinzel-700", 20, "#8cc0ff", "ls")
    cv.text(1500, 200, "Rare helm · item level 4", "alegreya-400-italic", 14, ink_dim, "ls")
    piece(cv, "rule_h", 1500, 214, 340, 6, src)
    for k, line in enumerate(["+12 armour", "+6% critical chance", "+1 to Wits"]):
        cv.text(1500, 246 + k * 24, line, "alegreya-sans-500", 16, ink, "ls")
    piece(cv, "rule_h", 1500, 310, 340, 6, src)
    cv.text(1500, 340, "Cold to the touch even at noon.", "alegreya-400-italic", 15, ink_dim, "ls")
    # The standing column: groups of numbers on the page, rules between.
    y = 480
    for grp, rows in (("STAYING ALIVE", [("Health", "212"), ("Armour", "8 · 29% less"), ("Regeneration", "0.7 a second")]),
                      ("DEALING DEATH", [("Damage", "+15%"), ("Critical chance", "6%"), ("Weapon speed", "+3% faster")])):
        cv.text(1500, y, grp, "alegreya-sans-800", 13, gold, "ls")
        piece(cv, "rule_h", 1630, y - 8, 230, 6, src)
        for k, (a, b) in enumerate(rows):
            cv.text(1500, y + 28 + k * 24, a, "alegreya-sans-500", 17, ink, "ls")
            cv.text(1700, y + 28 + k * 24, b, "alegreya-sans-700", 17, ink, "ls")
        y += 130
    # The words on the figure's panel, and its calling below.
    cv.text(100, 610, "CALLING", "alegreya-sans-800", 13, gold, "ls")
    piece(cv, "rule_h", 180, 602, 300, 6, src)
    cv.text(100, 640, "Warden", "alegreya-sans-700", 19, ink, "ls")
    cv.text(100, 662, "Hold the line.", "alegreya-400-italic", 15, ink_dim, "ls")
    cv.text(100, 698, "Hunter", "alegreya-sans-700", 19, ink, "ls")
    cv.text(100, 720, "You read the ground and the animals on it.", "alegreya-400-italic", 15, ink_dim, "ls")
    # A vertical rule between the columns.
    piece(cv, "rule_v", 520, 140, 6, 840, src)
    piece(cv, "rule_v", 1440, 140, 6, 840, src)
    cv.text(960, 1050, "Right-click to wear or use  ·  drag to wear or take off  ·  hover to compare", "alegreya-400-italic", 15, ink_dim, "ms")
    return cv


def world_still():
    """A still of the world for a side panel's left (godot/.shots/world.png if there is one)."""
    for p in (os.path.join(ROOT, "godot", ".shots", "world.png"),
              os.path.join(os.path.dirname(ROOT), "agent-aa9c11f1e40170a4d", "godot", ".shots", "a8_pack.png")):
        if os.path.exists(p):
            return np.asarray(Image.open(p).convert("RGB"), np.float32)[:, :1000] / 255


def pack(cv: Canvas, src="kit"):
    """The Pack as the greybox lays it (UI design, 31d7a46f): the world live on the left, the
    side panel on the right, the doll between her slots, the carried grid in its well."""
    cv.rgb[:] = resize(world_still(), cv.W, cv.H)
    ink, ink_dim, gold, gold_hi = "#e8dcc8", "#a89c8c", "#c9a256", "#f0d9a0"
    X0, Y0, X1, Y1 = 866, 16, 1902, 1062
    piece(cv, "side", X0, Y0, X1 - X0, Y1 - Y0, src)
    x = 892
    for i, t in enumerate(["Pack", "Self", "Arts", "Journal", "Map"]):
        fnt = ImageFont.truetype(font_path("alegreya-sans-700"), 16)
        tw = fnt.getlength(t)
        if i == 0:
            piece(cv, "tab_on", x - 10, 32, tw + 44, 34, src)
        cv.text(x, 52, t, "alegreya-sans-700", 16, gold_hi if i == 0 else ink_dim, "ls")
        piece(cv, "keycap", x + tw + 8, 37, 20, 20, src)
        cv.text(x + tw + 18, 52, "ICKJM"[i], "alegreya-sans-700", 12, ink_dim, "ms", shadow=False)
        x += tw + 64
    piece(cv, "button", 1776, 32, 100, 36, src)
    cv.text(1826, 56, "Close", "alegreya-sans-700", 15, gold_hi, "ms")
    cv.text(1384, 114, "PACK", "cinzel-700", 30, gold_hi, "ms")
    # The doll's backing and her slots.
    piece(cv, "panel", 898, 142, 468, 738, src)
    slots = [(914, 176, None, "HEAD"), (914, 296, 1, "cl"), (914, 416, 0, "ch"), (914, 536, None, "RELIC"),
             (1272, 236, None, "AMULET"), (1272, 356, 1, "sw"), (1272, 476, 0, "sh"), (1272, 596, None, "RING"), (1272, 696, None, "RING")]
    for sx, sy, r, t in slots:
        piece(cv, "slot" if r is None else f"slot_{r}", sx, sy, 76, 76, src)
        cv.text(sx + 38, sy + 42, t, "alegreya-sans-700", 10 if r is None else 13, "#5c544c" if r is None else ink_dim, "ms", shadow=False)
    for col, rows in ((914, [("Health", "212"), ("Damage", "+15%"), ("Speed", "5.2")]),
                      (1140, [("Armour", "8 · 29%"), ("Critical", "6%"), ("Regeneration", "0.7/s")])):
        for k, (a, b) in enumerate(rows):
            yy = 914 + k * 34
            cv.text(col, yy, a, "alegreya-sans-500", 17, ink, "ls")
            cv.text(col + 206, yy, b, "alegreya-sans-700", 16, ink, "rs")
            piece(cv, "rule_h", col - 6, yy + 8, 220, 6, src)
    # Carried: the grid in its well.
    cv.text(1398, 152, "CARRIED", "alegreya-sans-800", 13, gold, "ls")
    cv.text(1462, 155, "8 of 24", "alegreya-400-italic", 14, ink_dim, "ls")
    piece(cv, "rule_h", 1510, 146, 330, 6, src)
    cv.text(1880, 152, "Sort", "alegreya-sans-700", 14, ink_dim, "rs")
    piece(cv, "well", 1398, 170, 484, 324, src)
    rar = [0, 2, 3, 1, 1, 2, 0, 3]
    for j in range(4):
        for i in range(6):
            q = j * 6 + i
            nm = f"slot_{rar[q]}" if q < len(rar) else "slot"
            piece(cv, nm, 1404 + i * 80, 176 + j * 80, 72, 72, src)
    cv.text(1398, 542, "THE POUCH", "alegreya-sans-800", 13, gold, "ls")
    cv.text(1478, 545, "materials, never in the pack", "alegreya-400-italic", 14, ink_dim, "ls")
    piece(cv, "rule_h", 1650, 536, 230, 6, src)
    for i, r in enumerate([0, 1, 0]):
        piece(cv, f"slot_{r}", 1398 + i * 64, 560, 56, 56, src)
    cv.text(1398, 664, "PURSE", "alegreya-sans-800", 13, gold, "ls")
    piece(cv, "rule_h", 1452, 656, 430, 6, src)
    cv.text(1398, 708, "25 gold", "cinzel-700", 26, gold_hi, "ls")
    # A tooltip over the world.
    piece(cv, "tooltip", 520, 202, 330, 200, src)
    cv.fill(520, 202, 330, 3, (0.75, 0.44, 1.0), 0.95)
    cv.text(536, 236, "Iron Helm of the Salamander", "alegreya-700", 19, "#c590ff", "ls")
    cv.text(536, 256, "Epic helm · level 4", "alegreya-400-italic", 14, ink_dim, "ls")
    piece(cv, "rule_h", 530, 268, 310, 6, src)
    for k, (a, b) in enumerate([("Armour 7", "+4"), ("+33% fire resistance", "+21%"), ("+8 health", "+8")]):
        cv.text(536, 296 + k * 24, a, "alegreya-sans-500", 15, ink, "ls")
        cv.text(834, 296 + k * 24, b, "alegreya-sans-700", 15, "#7fd07a", "rs")
    piece(cv, "rule_h", 530, 356, 310, 6, src)
    cv.text(536, 384, "Rclick: wear  ·  Hold Del: break down", "alegreya-sans-500", 13, ink_dim, "ls")
    for i, (k_, t) in enumerate([("Rclick", "Wear or use"), ("Drag", "Move"), ("Shift", "Compare")]):
        bx = 1124 + i * 160
        fnt = ImageFont.truetype(font_path("alegreya-sans-700"), 12)
        kw = fnt.getlength(k_) + 14
        piece(cv, "keycap", bx, 1018, kw, 22, src)
        cv.text(bx + kw / 2, 1034, k_, "alegreya-sans-700", 12, ink_dim, "ms", shadow=False)
        cv.text(bx + kw + 10, 1034, t, "alegreya-sans-500", 14, ink_dim, "ls")
    return cv


def node(cv: Canvas, name, cx, cy, size, src="kit"):
    """A round piece (nodes/NAME.png) centred at (cx, cy), drawn at its shown size."""
    img = load(f"nodes/{name}.png", src)
    if img is None:
        return
    s = cv.s
    sz = img.shape[1] / 2 if size is None else size
    cv.over(resize(img, sz * s, sz * s), (cx - sz / 2) * s, (cy - sz / 2) * s)


def self_(cv: Canvas, src="kit"):
    """Self as the greybox lays it (UI design, 31d7a46f): a page of the day's book, her figure
    large on the left, the attributes, the traits' track and the standing on the right."""
    backdrop(cv, src)
    ink, ink_dim, gold, gold_hi, ember = "#e8dcc8", "#a89c8c", "#c9a256", "#f0d9a0", "#ff9a4a"
    hd, ft = load("frames/header.png", src), load("frames/footer.png", src)
    cv.nine(hd, -4, -4, 1928, 100, 0, 0, 0, 12, True)
    cv.nine(ft, -4, 1016, 1928, 68, 0, 12, 0, 0, True)
    x = 60
    for i, t in enumerate(["Pack", "Self", "Arts", "Journal", "Map"]):
        fnt = ImageFont.truetype(font_path("alegreya-sans-700"), 17)
        tw = fnt.getlength(t)
        if i == 1:
            piece(cv, "tab_on", x - 12, 24, tw + 48, 34, src)
        cv.text(x, 44, t, "alegreya-sans-700", 17, gold_hi if i == 1 else ink_dim, "ls")
        piece(cv, "keycap", x + tw + 8, 29, 20, 20, src)
        cv.text(x + tw + 18, 44, "ICKJM"[i], "alegreya-sans-700", 12, ink_dim, "ms", shadow=False)
        x += tw + 62
    cv.text(960, 56, "WREN", "cinzel-700", 38, gold_hi, "ms")
    cv.text(960, 80, "Level 4 Hunter Warden", "alegreya-400-italic", 15, ink_dim, "ms")
    piece(cv, "button", 1784, 26, 100, 36, src)
    piece(cv, "keycap", 1796, 34, 26, 20, src)
    cv.text(1809, 49, "Esc", "alegreya-sans-700", 11, ink_dim, "ms", shadow=False)
    cv.text(1830, 50, "Close", "alegreya-sans-700", 15, gold_hi, "ls")
    # Her figure stands on the page (live 3D in the game).
    cv.text(330, 520, "her figure, live 3D", "alegreya-400-italic", 15, "#4a423c", "ms", shadow=False)
    cv.text(330, 992, "LEVEL 4", "cinzel-700", 26, gold_hi, "ms")
    piece(cv, "rule_h", 147, 1002, 366, 6, src)
    cv.fill(150, 1004, 204, 3, (0.53, 0.69, 0.85), 0.9)
    cv.text(520, 1010, "340 / 600", "alegreya-sans-500", 13, ink_dim, "ls")
    # Attributes.
    cv.text(700, 128, "ATTRIBUTES", "alegreya-sans-800", 13, gold, "ls")
    cv.text(784, 131, "more with each level", "alegreya-400-italic", 14, ink_dim, "ls")
    piece(cv, "rule_h", 905, 121, 862, 6, src)
    cv.text(1880, 128, "2 points to spend", "alegreya-sans-700", 13, ember, "rs")
    for i, (nm, n, dsc) in enumerate([("MIGHT", "6", "+2.5% damage, +4 health a point"), ("FINESSE", "3", "+0.6% critical chance, +1% speed"),
                                      ("WITS", "3", "+1% weapon speed, +2% area and ember"), ("RESOLVE", "6", "+3 health, +0.5 armour, +0.08 regeneration")]):
        px = 700 + i * 299
        piece(cv, "panel", px, 144, 283, 128, src)
        cv.text(px + 22, 205, n, "cinzel-700", 50, gold_hi, "ls")
        if i == 0:
            cv.text(px + 62, 205, "→", "alegreya-sans-700", 28, "#7fd07a", "ls")
            cv.text(px + 96, 205, "7", "cinzel-700", 36, "#7fd07a", "ls")
            node(cv, "round", px + 207, 175, 34, src)
            cv.text(px + 207, 181, "−", "alegreya-sans-700", 18, ink_dim, "ms", shadow=False)
        node(cv, "round_spend", px + 247, 175, 38, src)
        cv.text(px + 247, 182, "+", "alegreya-sans-700", 20, ember, "ms", shadow=False)
        cv.text(px + 22, 236, nm, "cinzel-700", 19, gold, "ls")
        cv.text(px + 22, 257, dsc, "alegreya-sans-500", 13, ink_dim, "ls")
    cv.text(700, 310, "Spending previews every number it changes below, green where it rises.", "alegreya-400-italic", 14, ink_dim, "ls")
    piece(cv, "button", 1626, 284, 110, 36, src)
    cv.text(1644, 308, "Undo", "alegreya-sans-700", 15, gold_hi, "ls")
    piece(cv, "button_primary", 1748, 284, 132, 36, src)
    cv.text(1766, 308, "Confirm", "alegreya-sans-700", 15, "#ffe4b0", "ls")
    # Traits: the track.
    cv.text(700, 362, "TRAITS", "alegreya-sans-800", 13, gold, "ls")
    cv.text(752, 365, "one of three at every second level, and some given for what you do", "alegreya-400-italic", 14, ink_dim, "ls")
    piece(cv, "rule_h", 1110, 355, 770, 6, src)
    piece(cv, "rule_h", 740, 411, 820, 6, src)
    node(cv, "taken", 740, 414, 44, src)
    cv.text(740, 420, "ic", "alegreya-sans-700", 13, ink_dim, "ms", shadow=False)
    node(cv, "next", 831, 414, 50, src)
    cv.text(831, 423, "4", "cinzel-700", 20, ember, "ms")
    for k, lv in enumerate(range(6, 21, 2)):
        nx = 922 + k * 91
        node(cv, "later", nx, 414, 14, src)
        cv.text(nx, 444, str(lv), "alegreya-sans-500", 12, ink_dim, "ms", shadow=False)
    cv.text(740, 458, "Steady Hand", "alegreya-sans-700", 14, ink, "ms")
    cv.text(740, 477, "level 2", "alegreya-sans-500", 12, ink_dim, "ms")
    cv.text(831, 458, "Next: level 4", "alegreya-sans-700", 14, ember, "ms")
    cv.text(831, 477, "one of three", "alegreya-sans-500", 12, ink_dim, "ms")
    cv.text(1620, 395, "GIVEN FOR DEEDS", "alegreya-sans-800", 12, gold, "ls")
    for cx0, w, t in ((1620, 84, "Wolfsbane"), (1712, 70, "Lamp-lit")):
        piece(cv, "chip", cx0, 407, w, 26, src)
        cv.text(cx0 + w / 2, 425, t, "alegreya-sans-500", 14, ink, "ms", shadow=False)
    # Standing: three aligned columns.
    cv.text(700, 502, "STANDING", "alegreya-sans-800", 13, gold, "ls")
    cv.text(774, 505, "hover a number: where it comes from", "alegreya-400-italic", 14, ink_dim, "ls")
    piece(cv, "rule_h", 985, 495, 895, 6, src)
    cols = [(700, [("STAYING ALIVE", [("Health", "212", "+4"), ("Armour", "8 · 29% less", ""), ("Regeneration", "0.7 a second", ""), ("Healing", "+18%", ""), ("Dodge", "0%", "")]),
                   ("WARDING", [("Fire", "12%", ""), ("Frost", "22%", ""), ("Storm", "0%", ""), ("Venom", "0%", "")])]),
            (1109, [("DEALING DEATH", [("Damage", "+15%", "+2.5%"), ("Critical chance", "6%", ""), ("Critical damage", "×1.5", ""), ("Weapon speed", "+3% faster", ""), ("Area", "+6%", "")]),
                    ("THE ART IN HAND", [("Shield Bash", "rank II", ""), ("Strength", "+6%", ""), ("Wait", "7 s", "")])]),
            (1518, [("MOVING", [("Speed", "5.2", ""), ("Dashes", "2", ""), ("Reach for what falls", "2.4 m", "")]),
                    ("FORTUNE", [("Experience", "+6%", ""), ("Gold found", "0%", "")])])]
    for cx0, groups in cols:
        y = 537
        for head, rows in groups:
            cv.text(cx0, y, head, "alegreya-sans-800", 12, gold, "ls")
            y += 28
            for a, b, d in rows:
                cv.text(cx0 + 22, y, a, "alegreya-sans-500", 16, ink, "ls")
                cv.text(cx0 + 308, y, b, "alegreya-sans-700", 15, ink, "rs")
                if d:
                    cv.text(cx0 + 360, y, d, "alegreya-sans-700", 13, "#7fd07a", "rs")
                piece(cv, "rule_h", cx0 - 4, y + 9, 368, 6, src)
                y += 32
            y += 44
    for i, (k_, t) in enumerate([("Arrows", "Move"), ("Enter", "Spend a point"), ("Bksp", "Take it back"), ("[ ]", "Turn the page"), ("Esc", "Close")]):
        bx = 646 + [0, 120, 278, 422, 560][i]
        fnt = ImageFont.truetype(font_path("alegreya-sans-700"), 12)
        kw = fnt.getlength(k_) + 14
        piece(cv, "keycap", bx, 1048, kw, 22, src)
        cv.text(bx + kw / 2, 1064, k_, "alegreya-sans-700", 12, ink_dim, "ms", shadow=False)
        cv.text(bx + kw + 10, 1064, t, "alegreya-sans-500", 14, ink_dim, "ls")
    return cv


def main():
    args = sys.argv[1:]
    scale = float(args[args.index("--scale") + 1]) if "--scale" in args else 1.0
    src = args[args.index("--src") + 1] if "--src" in args else "kit"
    page = args[args.index("--page") + 1] if "--page" in args else "specimen"
    out = args[args.index("--out") + 1] if "--out" in args else os.path.join(KIT, f"board_{page}_{int(1080 * scale)}.png")
    cv = {"specimen": specimen, "pack": pack, "self": self_}[page](Canvas(1920, 1080, scale), src)
    cv.image().save(out)
    print(out)


if __name__ == "__main__":
    main()
