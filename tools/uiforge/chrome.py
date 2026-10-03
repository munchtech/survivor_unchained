"""The interface's metal chrome, modelled and rendered in Blender (blender_frames.py)
under the house light: buttons in all their states, the gold segment, the book's
tabs, the chosen row, keycaps, item slots by rarity, the skill socket, chips,
toasts, the prompt's pill, tooltips, the bars' groove and casing.

Every piece is built at its exact file size and nine-slice layout; its middle is
then set to the tone the text was chosen for, and it is checked to tile.

    python tools/uiforge/chrome.py [NAME ...]
"""
from __future__ import annotations

import copy
import math
import os
import sys

import numpy as np

import blrender
import forge as F

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
UI = os.path.join(ROOT, "godot", "art", "ui")

IRON = {"color": "#1e1b23", "worn": "#9894a0", "rough": 0.36, "hammer": 0.8, "dent_scale": 0.12, "wear": 0.9}
GOLD = "#c9a256"
RARITY = ["#c8c0b0", "#6fd46a", "#5aa8ff", "#c070ff", "#ffb040", "#ff6a3a"]


def corner_pts(W, H, d):
    return [(d, d), (W - d, d), (d, H - d), (W - d, H - d)]


def calibrate(img, margins, tone, region_inset=None):
    """The flat middle set to `tone` (the fallback's colour, which the text was chosen for)."""
    if tone is None:
        return img
    H, W = img.shape[:2]
    l, t, r, b = region_inset or margins
    lin = F.srgb_to_lin(img[..., :3])
    sel = lin[t:H - b, l:W - r]
    a = img[t:H - b, l:W - r, 3] > 0.99
    if not a.any():
        return img
    cur = np.median(sel[a], axis=0)
    gain = np.clip(F.hexc(tone) / np.maximum(cur, 1e-5), 0.05, 20)
    # Applied only inside the strap's inner edge (feathered), so the metal keeps its light.
    m = np.zeros((H, W), np.float32)
    m[t:H - b, l:W - r] = 1
    import cv2
    m = cv2.GaussianBlur(m, (0, 0), max(1.0, min(l, t) * 0.15))
    out = img.copy()
    out[..., :3] = F.lin_to_srgb(lin * (1 + (gain - 1) * m[..., None]))
    return out


# The paint-over (paintover.py): what each piece is, for the Krea to give the render its hand.
IRON_PROMPT = ("hand-forged blackened iron, hammer marks, pitted and worn edges, soot in the corners, a thin twisted gold "
               "wire inlaid, the inside plain flat dark iron, isolated on a pure black background, seen straight on")
PAINT = {
    "plate": ("an empty square window frame of " + IRON_PROMPT + ", at each corner a square iron coin with a round hole and a "
              "curled iron bracket", 0.30),
    "tooltip": ("an empty square tooltip frame, a narrow strap of " + IRON_PROMPT + ", small square coins at the corners", 0.28),
    "tooltip_worn": ("an empty square tooltip frame, a narrow strap of " + IRON_PROMPT.replace("gold", "pewter") +
                     ", small square coins at the corners", 0.28),
    "toast": ("a small wide plate of " + IRON_PROMPT + ", two rivets at its left end", 0.28),
    "prompt": ("a small long pill-shaped plate with rounded ends of " + IRON_PROMPT, 0.26),
    "weapon_slot": ("a square socket of " + IRON_PROMPT + ", a square coin with a round hole on each corner, a recessed dark centre", 0.30),
    "slot": ("an empty square recessed well of hand-forged blackened iron, hammered rim, rivets at the corners, the inside plain "
             "dark, isolated on a pure black background, seen straight on", 0.28),
    "row_on": ("a long chosen-row plate of dark bronze and iron, a gold wire inlaid, ember light at its inner edge, plain inside, "
               "isolated on a pure black background, seen straight on", 0.26),
    "tab": ("a ledger tab of " + IRON_PROMPT + ", rounded at the top corners, flat at the bottom", 0.26),
    "tab_on": ("a ledger tab of dark bronze and iron, a gold wire inlaid, ember light at its inner edge, rounded at the top corners, "
               "flat at the bottom, plain inside, isolated on a pure black background, seen straight on", 0.26),
}


def render(name, spec, tone=None, calib_inset=None, post=None, paint=None):
    img, _ = blrender.render(spec, name)
    paint = PAINT.get(name) if paint is None else paint
    if paint:
        import paintover as PO
        prompt, denoise = paint
        img = PO.paint(img, prompt, name, denoise=denoise, seed=11, keep_light=0.75)
    img = calibrate(img, spec["margins"], tone, calib_inset)
    if post:
        img = post(img)
    if spec.get("tile", True) and paint:
        import nineslice as N
        l, t, r, b = spec["margins"]
        img = N.tileable(img, (l, t, r, b), blend=max(4, min(l, t) // 10))
    return img


def save(img, rel):
    path = os.path.join(UI, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    F.save(F.to_pil(img), path)


# ------------------------------------------------------------------ pieces --

def button_spec(state="normal", primary=False):
    W, H = 192, 64
    strap = dict(IRON, inset=1, width=9, thick=5, bevel=2.0, chamfer=9)
    wire = {"offset": 5, "radius": 1.7, "pitch": 5, "color": GOLD, "rough": 0.34}
    spec = {"size": [W, H], "ss": 4, "margins": [24, 20, 24, 20], "samples": 64,
            "strap": strap, "panel": {"inset": 8, "color": "#17141b", "z": 1.0}, "wire": wire}
    tone = "#221e28"
    if primary:
        strap.update(color="#4a2c16", worn="#c8925a", rough=0.32, metal=0.95)
        spec["seam"] = {"offset": 10, "radius": 0.9, "color": "#ff7a2a", "strength": 1.6, "z": 3}
        tone = "#3a230e"
    if state == "hover":
        wire.update(color="#ecc77a", rough=0.18)
        strap["tint"] = [1.35, 1.3, 1.25]
        spec.setdefault("seam", {"offset": 10, "radius": 0.8, "color": "#ff9a4a", "strength": 0.0, "z": 3})
        spec["seam"]["strength"] = spec["seam"]["strength"] + 2.2
        tone = "#2a2530" if not primary else "#4a2c12"
    elif state == "pressed":
        spec["panel"]["z"] = -2.0
        wire.update(color="#e0b868", rough=0.22)
        if primary:
            spec["seam"]["strength"] = 3.2
        tone = "#19161d" if not primary else "#3e2410"
    elif state == "disabled":
        wire.update(color="#6f6c74", rough=0.55)
        strap.update(color="#17151b", wear=0.25, worn="#55525a")
        tone = "#16141a"
    return spec, tone


def disabled_post(img):
    g = img[..., :3].mean(axis=2, keepdims=True)
    img = img.copy()
    img[..., :3] = g * 0.75 + img[..., :3] * 0.25
    return img


def build_buttons():
    for primary in (False, True):
        for state in ("normal", "hover", "pressed", "disabled"):
            if primary and state == "disabled":
                continue
            name = ("button_primary" if primary else "button") + ("" if state == "normal" else "_" + state)
            spec, tone = button_spec(state, primary)
            img = render(name, spec, tone, calib_inset=[11, 11, 11, 11],
                         post=disabled_post if state == "disabled" else None)
            save(img, f"frames/{name}.png")
            print(name, flush=True)


def build_segment():
    spec = {"size": [128, 48], "ss": 4, "margins": [20, 16, 20, 16], "samples": 64,
            "strap": dict(IRON, inset=1, width=5, thick=4, bevel=1.6, chamfer=8, color="#8a6a36", worn="#f3d9a0", metal=1.0, rough=0.3),
            "panel": {"inset": 5, "color": "#b89048", "z": 2.0, "metal": 1.0, "rough": 0.38, "hammer": 0.5}}
    save(render("segment_on", spec, "#d0a858", calib_inset=[7, 7, 7, 7]), "frames/segment_on.png")


def build_tabs():
    for on in (False, True):
        strap = dict(IRON, inset=1, width=7, thick=5, bevel=2.0, corners=[14, 14, 0, 0])
        spec = {"size": [160, 72], "ss": 4, "margins": [28, 20, 28, 12], "samples": 64, "strap": strap, "tile": False,
                "panel": {"inset": 6, "color": "#17141b", "z": 1.0},
                "wire": {"offset": 4, "radius": 1.5, "pitch": 5, "color": GOLD if on else "#a8844a", "rough": 0.3}}
        tone = "#1c1922"
        if on:
            strap.update(color="#4a2c16", worn="#c8925a", metal=0.95)
            spec["seam"] = {"offset": 8, "radius": 0.8, "color": "#ff8a3a", "strength": 1.2, "z": 3}
            tone = "#3a2614"
        name = "tab_on" if on else "tab"
        save(render(name, spec, tone, calib_inset=[9, 9, 9, 6]), f"frames/{name}.png")
        print(name, flush=True)


def build_row():
    strap = dict(IRON, inset=1, width=6, thick=4, bevel=1.8, chamfer=10, color="#4a2c16", worn="#c8925a", metal=0.95)
    spec = {"size": [512, 96], "ss": 3, "margins": [24, 20, 24, 20], "samples": 64, "strap": strap,
            "panel": {"inset": 6, "color": "#2a1a10", "z": 1.0},
            "wire": {"offset": 3.5, "radius": 1.5, "pitch": 5, "color": GOLD, "rough": 0.3},
            "seam": {"offset": 8, "radius": 0.8, "color": "#ff8a3a", "strength": 1.0, "z": 3}}
    save(render("row_on", spec, "#3a2614", calib_inset=[9, 9, 9, 9]), "frames/row_on.png")


def build_keycap():
    spec = {"size": [48, 48], "ss": 8, "margins": [12, 12, 12, 12], "samples": 64,
            "strap": dict(IRON, inset=1, width=5, thick=4, bevel=1.6, radius=6, color="#5a4626", worn="#d9b56a", metal=1.0, rough=0.35),
            "panel": {"inset": 5, "color": "#0d0c10", "z": 2.5, "hammer": 0.3}}
    save(render("keycap", spec, "#0d0c10", calib_inset=[7, 7, 7, 7]), "frames/keycap.png")


def slot_spec(rarity=None):
    W = H = 160
    strap = dict(IRON, inset=1, width=17, thick=6, bevel=3.0, chamfer=6)
    spec = {"size": [W, H], "ss": 2, "margins": [20, 20, 20, 20], "samples": 64, "strap": strap,
            "panel": {"inset": 17, "color": "#0d0b10", "z": -3.0, "hammer": 0.3}}
    if rarity is None:
        spec["rivets"] = [{"x": x, "y": y, "r": 3.2} for x, y in corner_pts(W, H, 9)]
        return spec
    col = RARITY[rarity]
    spec["wire"] = {"offset": 14, "radius": 2.0 if rarity else 1.6, "pitch": 6, "color": col, "rough": 0.25}
    spec["seam"] = {"offset": 18, "radius": 0.8, "color": col, "strength": 0.4 + 0.25 * rarity, "z": 1}
    if rarity == 0:
        spec["rivets"] = [{"x": x, "y": y, "r": 3.2} for x, y in corner_pts(W, H, 8)]
    elif rarity == 1:
        # Thorns: hooked points growing from each corner along both edges.
        th = []
        for cx, cy in corner_pts(W, H, 6):
            sx = 1 if cx < W / 2 else -1
            sy = 1 if cy < H / 2 else -1
            for (dx, dy, L) in ((1, 0.25, 30), (0.25, 1, 30), (0.85, 0.85, 20)):
                pts = []
                for t in np.linspace(0, 1, 8):
                    bend = math.sin(t * math.pi) * 3
                    pts.append((cx + sx * (dx * L * t - dy * bend * 0.3), cy + sy * (dy * L * t + dx * bend * 0.3)))
                th.append({"pts": pts, "w0": 9, "w1": 0.3, "lift": 2.5, "flat": 0.9, "color": "#4e6a2c"})
        spec["thorns"] = th
    elif rarity == 2:
        cr = []
        for cx, cy in corner_pts(W, H, 7):
            base = math.atan2(1 if cy < H / 2 else -1, 1 if cx < W / 2 else -1)
            for da, L in ((-0.55, 22), (-0.2, 30), (0.2, 26), (0.55, 20)):
                ang = base + da
                cr.append({"x": cx, "y": cy, "angle": math.degrees(-ang) if False else math.degrees(ang), "len": L, "w": 6})
        spec["crystals"] = cr
    elif rarity == 3:
        spec["gems"] = [{"x": x, "y": y, "size": 16, "color": col, "glow": 0.8, "rot": 45} for x, y in corner_pts(W, H, 9)]
    elif rarity == 4:
        fl = []
        for cx, cy in corner_pts(W, H, 5):
            sx = 1 if cx < W / 2 else -1
            sy = 1 if cy < H / 2 else -1
            for (dx, dy, L) in ((1, 0.12, 34), (0.12, 1, 34), (0.8, 0.8, 24)):
                pts = []
                for t in np.linspace(0, 1, 12):
                    wob = math.sin(t * math.pi * 1.6) * 3.5
                    pts.append((cx + sx * (dx * L * t + dy * wob), cy + sy * (dy * L * t - dx * wob)))
                fl.append({"pts": pts, "w0": 10, "w1": 0.4, "lift": 2.5, "flat": 0.8, "color": "#e0a848", "glow": 0.5})
        spec["flames"] = fl
    elif rarity == 5:
        rng = np.random.default_rng(5)
        cracks = []
        for cx, cy in corner_pts(W, H, 9):
            for _ in range(3):
                x, y = cx, cy
                a = math.atan2(H / 2 - cy, W / 2 - cx) + rng.normal() * 0.9
                pts = [(x, y)]
                for _ in range(7):
                    a += rng.normal() * 0.5
                    x += math.cos(a) * 4
                    y += math.sin(a) * 4
                    pts.append((x, y))
                cracks.append({"pts": pts, "w": 0.9, "strength": 5.0})
        spec["cracks"] = cracks
        spec["rivets"] = [{"x": x, "y": y, "r": 3.2} for x, y in corner_pts(W, H, 8)]
    return spec


def build_slots():
    names = ["common", "uncommon", "rare", "epic", "legendary", "relic"]
    save(render("slot", slot_spec(None), "#0d0b10", calib_inset=[20, 20, 20, 20]), "frames/slot.png")
    for r, n in enumerate(names):
        save(render(f"slot_{n}", slot_spec(r), "#0e0c11", calib_inset=[22, 22, 22, 22]), f"frames/slot_{n}.png")
        print("slot", n, flush=True)


def build_weapon_slot():
    W = H = 134
    spec = {"size": [W, H], "ss": 3, "margins": [24, 24, 24, 24], "samples": 64, "tile": False,
            "strap": dict(IRON, inset=1, width=14, thick=6, bevel=2.5, chamfer=8),
            "panel": {"inset": 14, "color": "#121016", "z": -2.0, "hammer": 0.3},
            "wire": {"offset": 6, "radius": 1.8, "pitch": 5, "color": GOLD, "rough": 0.3},
            "coins": [{"x": x, "y": y, "size": 15, "hole": 0.36, "ember": 1} for x, y in corner_pts(W, H, 9)],
            "ember_strength": 1.2, "ember_color": "#ff4a10"}
    save(render("weapon_slot", spec, "#16131a", calib_inset=[16, 16, 16, 16]), "frames/weapon_slot.png")


def build_chip():
    spec = {"size": [64, 64], "ss": 6, "margins": [16, 16, 16, 16], "samples": 64,
            "strap": dict(IRON, inset=1, width=5, thick=4, bevel=1.6, radius=8),
            "panel": {"inset": 5, "color": "#0f0d12", "z": 1.0, "hammer": 0.3},
            "wire": {"offset": 2.5, "radius": 1.0, "pitch": 4, "color": "#a8844a", "rough": 0.35}}
    save(render("chip", spec, "#0f0d12", calib_inset=[7, 7, 7, 7]), "frames/chip.png")


def build_toast():
    W, H = 256, 96
    spec = {"size": [W, H], "ss": 3, "margins": [28, 20, 20, 20], "samples": 64,
            "strap": dict(IRON, inset=1, width=8, thick=5, bevel=2.0, chamfer=6),
            "panel": {"inset": 8, "color": "#141117", "z": 1.0},
            "wire": {"offset": 4, "radius": 1.6, "pitch": 5, "color": GOLD, "rough": 0.3},
            "rivets": [{"x": 14, "y": 14, "r": 2.6}, {"x": 14, "y": H - 14, "r": 2.6}]}
    save(render("toast", spec, "#141117", calib_inset=[10, 10, 10, 10]), "frames/toast.png")


def build_prompt():
    spec = {"size": [256, 80], "ss": 3, "margins": [44, 24, 44, 24], "samples": 64,
            "strap": dict(IRON, inset=1, width=7, thick=5, bevel=2.0, radius=39),
            "panel": {"inset": 7, "color": "#141117", "z": 1.0},
            "wire": {"offset": 3.5, "radius": 1.5, "pitch": 5, "color": GOLD, "rough": 0.3}}
    save(render("prompt", spec, "#141117", calib_inset=[30, 10, 30, 10]), "frames/prompt.png")


def build_tooltips():
    W = H = 256
    for worn in (False, True):
        spec = {"size": [W, H], "ss": 2, "margins": [32, 32, 32, 32], "samples": 64,
                "strap": dict(IRON, inset=1, width=10, thick=5, bevel=2.0, chamfer=4),
                "panel": {"inset": 10, "color": "#100e13", "z": 1.0, "hammer": 0.3},
                "wire": {"offset": 5, "radius": 1.9, "pitch": 6, "color": "#8e8b94" if worn else GOLD, "rough": 0.4 if worn else 0.3},
                "coins": [{"x": x, "y": y, "size": 18, "hole": 0.36, "ember": 0 if worn else 1} for x, y in corner_pts(W, H, 10)],
                "ember_strength": 1.2, "ember_color": "#ff4a10"}
        name = "tooltip_worn" if worn else "tooltip"
        save(render(name, spec, "#100e13", calib_inset=[12, 12, 12, 12]), f"frames/{name}.png")
        print(name, flush=True)


def build_track():
    spec = {"size": [128, 32], "ss": 6, "margins": [16, 12, 16, 12], "samples": 64,
            "strap": dict(IRON, inset=1, width=3.5, thick=3, bevel=1.2, radius=6),
            "panel": {"inset": 3, "color": "#0a0708", "z": -1.5, "hammer": 0.2}}
    save(render("track", spec, "#0c0809", calib_inset=[5, 5, 5, 5]), "bars/track.png")


def build_casing():
    """Iron round a bar's groove (hollow: the fill shows through), the wire along it, a rivet
    at each end; GameHud.Casing lays it 6 shown px outside the bar."""
    W, H = 128, 48
    spec = {"size": [W, H], "ss": 4, "margins": [24, 16, 24, 16], "samples": 64,
            "strap": dict(IRON, inset=1, width=12, thick=5, bevel=2.0, chamfer=4),
            "wire": {"offset": 5, "radius": 1.6, "pitch": 5, "color": GOLD, "rough": 0.3},
            "rivets": [{"x": 6.5, "y": 24, "r": 2.8}, {"x": W - 6.5, "y": 24, "r": 2.8}]}
    save(render("casing", spec, None), "bars/casing.png")


def bracket_scrolls(cx, cy, sx, sy, arm, curl_r, along):
    """A lamp-iron bracket's two arms from a corner coin: along each edge, then a scroll
    curling back outward. (sx, sy) point into the frame; `along` is the arm's offset
    across the strap from the coin's centre line."""
    out = []
    for axis in (0, 1):
        pts = []
        for t in np.linspace(0, 1, 10):
            d = 14 + arm * t
            pts.append((cx + sx * d, cy + sy * along) if axis == 0 else (cx + sx * along, cy + sy * d))
        ex, ey = pts[-1]
        if axis == 0:
            ccx, ccy = ex, ey - sy * curl_r
            turn = (1 if sx * sy > 0 else -1) * -1.25
        else:
            ccx, ccy = ex - sx * curl_r, ey
            turn = (1 if sx * sy > 0 else -1) * 1.25
        a0 = math.atan2(ey - ccy, ex - ccx)
        for t in np.linspace(0, 1, 22)[1:]:
            a = a0 + turn * 2 * math.pi * t
            r = curl_r * (1 - 0.72 * t)
            pts.append((ccx + math.cos(a) * r, ccy + math.sin(a) * r))
        out.append(pts)
    return out


def build_plate():
    W = H = 512
    o = 24          # the overhang (12 shown) the coins reach into
    spec = {"size": [W, H], "ss": 2, "margins": [128, 128, 128, 128], "samples": 96,
            "strap": dict(IRON, inset=o, width=32, thick=9, bevel=3.5, chamfer=5, hammer=1.0, dent_scale=0.08),
            "panel": {"inset": o + 30, "color": "#16131a", "z": 2.0, "hammer": 0.35},
            "wire": {"offset": 16, "radius": 3.6, "pitch": 10, "color": GOLD, "rough": 0.3},
            "ember_strength": 1.4, "ember_color": "#ff4a10", "rivet_lift": 3}
    coins, scrolls, rivets = [], [], []
    for cx, cy in corner_pts(W, H, o + 12):
        sx = 1 if cx < W / 2 else -1
        sy = 1 if cy < H / 2 else -1
        coins.append({"x": cx, "y": cy, "size": 46, "hole": 0.34, "ember": 1})
        for pts in bracket_scrolls(cx, cy, sx, sy, 60, 11, 0):
            scrolls.append({"pts": pts, "w0": 13, "w1": 4, "lift": 2.0, "flat": 0.75})
        rivets += [{"x": cx + sx * 46, "y": cy, "r": 3.4}, {"x": cx, "y": cy + sy * 46, "r": 3.4}]
    spec["coins"] = coins
    spec["scrolls"] = scrolls
    spec["rivets"] = rivets
    save(render("plate", spec, "#16131a", calib_inset=[o + 34] * 4), "frames/plate.png")


GROUPS = {n[6:]: f for n, f in globals().items() if n.startswith("build_")}

if __name__ == "__main__":
    for n in sys.argv[1:] or list(GROUPS):
        GROUPS[n]()
        print("built", n, flush=True)
