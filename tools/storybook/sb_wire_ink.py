"""Wire the ink plates (tools/storybook/out/ink_layers/<plate>/layers.json) into SB00.

Re-runnable: reads each plate's layers.json and tools/storybook/ink_picks.json (which
drawing plays each state), copies only the used layers (base layers, glows, the picked
state drawings) to godot/art/storybook/sb00/<plate>/ under clean names (<name>.png for a
base layer, <state>.png for a state drawing), writes their .import files, and rewrites
SB00's plates from 56 s on in godot/data/storybook/sb00.json: the placeholder cards
(or the ink plates of an earlier run) are replaced by the four ink plates, and every plate
cue keeps its absolute time (moved to whichever new plate is up then). Plates before 56 s,
the file's own cues and "live" are left as they are.

    python tools/storybook/sb_wire_ink.py
    Godot_console.exe --headless --path godot --import     (after new or changed art)

Staging (the Storybook 3 lead's, phase 2; the plan is tools/storybook/comps/sb00_comps.json):
all positions below are in each plate's own comps units, shifted on the way in by
(1600, 900) - rest, as layers.json says.
"""
import hashlib
import json
import os
import shutil
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as nd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
from make_test_plates import write_import  # noqa: E402

LAYERS = os.path.join(HERE, "out", "ink_layers")
PICKS = os.path.join(HERE, "ink_picks.json")
SB = os.path.join(ROOT, "godot", "data", "storybook", "sb00.json")
ART = os.path.join(ROOT, "godot", "art", "storybook", "sb00")
RES = "res://art/storybook/sb00"

# The plates this replaces (the placeholder cards p7-p10c) and its own earlier output.
REPLACED = {"p7", "p8", "p9", "p10a", "p10b", "p10c"}
PREFIX = "ink_"

# Where the art's own features are (comps units, found in the layer images; they follow the comps).
P5_FOURTH_LIGHT = (2362, 684)   # round 4 base: the fourth cage (gen 1344,389; ink_layers.P5_CAGES[-1])
P7_FLASK = (1550, 1490)         # the comps' rings from the flask
GLARE_FLICKER = {"kind": "flicker", "rate": 0.9, "amount": 0.2, "seed": 4}   # p7's lamp glare (blue_rim breathes with it)

# Plate cues the ink staging moved (absolute seconds; matched by what they do, applied every run).
RETIME = [
    ({"do": "sfx", "name": "kneel_water"}, 81.6),                  # p7 opens on the kneel
    ({"do": "sfx", "name": "cloth_water"}, 86.9),                  # the plunge, just ahead of the water closing
    ({"do": "sfx", "name": "water_close"}, 87.0),                  # the tip under (p7u)
    ({"do": "bus", "lowpass": 650}, 87.0),                         # the underwater muffle
    ({"do": "sfx", "name": "heart_hum"}, 87.7),                    # under, as before 0.7 s after the water closes
]


def r(v, n=1):
    v = round(float(v), n)
    return int(v) if v == int(v) else v


def pw(points, t):
    """Piecewise-linear value of [(t, v), ...] at t (held past both ends)."""
    if t <= points[0][0]:
        return points[0][1]
    for (t0, v0), (t1, v1) in zip(points, points[1:]):
        if t <= t1:
            return v0 if t1 == t0 else v0 + (v1 - v0) * (t - t0) / (t1 - t0)
    return points[-1][1]


class Plate:
    def __init__(self, pid):
        self.pid = pid
        self.meta = json.load(open(os.path.join(LAYERS, pid, "layers.json"), encoding="utf-8"))
        rest = self.meta["rest"]
        self.shift = (1600 - rest[0], 900 - rest[1])
        self.used = {}  # clean name -> source file
        self.made = {}  # clean name -> RGBA uint8 array made here (written instead of copied)

    def S(self, x, y):
        return [r(x + self.shift[0]), r(y + self.shift[1])]

    def cam(self, t, x, y, zoom, **kw):
        k = {"t": t, "x": r(x + self.shift[0]), "y": r(y + self.shift[1]), "zoom": zoom}
        k.update(kw)
        return k

    def entry(self, file):
        for e in self.meta["layers"]:
            if e["file"] == file:
                return e
        raise SystemExit(f"{self.pid}: picked file {file} is not in layers.json")

    def box(self, e):
        """Canvas box of a layer entry (shifted): x, y, w, h."""
        sc = e["scale"]
        return (e["pos"][0] + self.shift[0], e["pos"][1] + self.shift[1], e["size_px"][0] * sc, e["size_px"][1] * sc)

    def layer(self, e, clean, **extra):
        self.used[clean + ".png"] = e["file"]
        L = {"id": clean, "image": f"{RES}/{self.pid}/{clean}.png", "pos": self.S(*e["pos"]),
             "scale": e["scale"], "z": e["z"]}
        if e.get("blend", "mix") != "mix":
            L["blend"] = e["blend"]
        L.update(extra)
        return L

    def bases(self):
        return [e for e in self.meta["layers"] if e.get("state") is None]

    def bright_center(self, e, frac=0.01):
        """Canvas point of a layer's brightest pixels (top frac by luminance x alpha)."""
        im = np.asarray(Image.open(os.path.join(LAYERS, self.pid, e["file"])).convert("RGBA")).astype(np.float32)
        lum = im[..., :3].mean(-1) * im[..., 3] / 255
        thr = np.quantile(lum, 1 - frac)
        ys, xs = np.nonzero(lum >= thr)
        x, y, _, _ = self.box(e)
        return (x + xs.mean() * e["scale"], y + ys.mean() * e["scale"])


def opacity_keys(points, times, extra=None):
    """Layer keys at the given times, every channel set (so nothing carries over)."""
    keys = []
    for t in sorted(set(round(t, 3) for t in times)):
        k = {"t": r(t, 3), "opacity": r(pw(points, t), 3)}
        if extra:
            k.update(extra(t))
        keys.append(k)
    return keys


# ---------------------------------------------------------------- plates
def plate_p5(picks):
    P = Plate("p5")
    layers = []
    for e in P.bases():
        if e["name"] == "drowned":
            continue
        L = P.layer(e, e["name"])
        if e["name"] == "lamps":    # the blue flames breathe: slow, small
            L["touch"] = [{"kind": "flicker", "rate": 1.3, "amount": 0.16, "seed": 5}]
        if e["name"] == "far":      # the ford's water: rings under the fourth light
            fx, fy = P5_FOURTH_LIGHT
            L["touch"] = [{"kind": "ripple", "centers": [P.S(fx, fy + 18)], "period": 3.2, "speed": 38, "amp": 1.4,
                           "rings": 3, "gap": 20, "reach": 230, "squash": 0.28, "light": 0.3}]
        layers.append(L)
    for state, file in picks.items():
        e = P.entry(file)
        layers.append(P.layer(e, state))
    layers.sort(key=lambda L: -L["z"])
    return P, {
        "id": PREFIX + "p5", "at": 56, "until": 71,
        "in": {"kind": "fade", "dur": 1.4, "color": "#000000"},
        # Open at 1.6 on the ford and the fourth light (1 image px a screen px holds to 1.6), push to 1.75 by 7 s,
        # hold, then pull back up the road to the wide rest by 14.5 s: the drowned in both ditches.
        "camera": [P.cam(0, 1880, 700, 1.6, dolly=0.15), P.cam(7.0, 1990, 705, 1.75, dolly=0.15, ease="out"),
                   P.cam(7.5, 1990, 705, 1.75, dolly=0.15),
                   P.cam(14.5, 1800, 1000, 1.0, dolly=0, ease="inout")],
        "note": "INK: The Low Ford; the drowned (tools/storybook/sb_wire_ink.py writes this plate; edit the script, not here).",
        "layers": layers,
        "fx": [{"kind": "mist", "rect": [-200, 560, 3600, 260], "z": 3.3, "color": "#8f9fb6", "density": 0.28,
                "speed": [9, 0], "scale": 320, "seed": 3}],
        "cues": [],
    }


def story_curve(ts, vs, es):
    """The player's StoryCurve (godot/logic/Storybook/StoryMotion.cs), replicated: Hermite with rest tangents."""
    n = len(ts)

    def chord(i):
        return 0.0 if ts[i + 1] - ts[i] < 1e-9 else (vs[i + 1] - vs[i]) / (ts[i + 1] - ts[i])

    def hold(i):
        return es[i + 1] == "hold"

    def tangent(i):
        start, end = i == 0 or hold(i - 1), i == n - 1 or hold(i)
        if start and end:
            return 0.0
        before = es[i] if i > 0 else None
        after = es[i + 1] if i < n - 1 else None
        if start:
            return chord(i) if after in ("linear", "out", "stop") else 0.0
        if end:
            return chord(i - 1) if before in ("linear", "in") else 0.0
        if before in ("inout", "out", "stop") or after in ("inout", "in"):
            return 0.0
        d0, d1 = chord(i - 1), chord(i)
        if d0 * d1 <= 0:
            return 0.0
        c = (vs[i + 1] - vs[i - 1]) / (ts[i + 1] - ts[i - 1])
        lim = 3 * min(abs(d0), abs(d1))
        return max(-lim, min(lim, c))
    m = [tangent(i) for i in range(n)]

    def at(t):
        if t <= ts[0]:
            return vs[0]
        if t >= ts[-1]:
            return vs[-1]
        i = 0
        while i < n - 2 and t >= ts[i + 1]:
            i += 1
        if hold(i):
            return vs[i]
        h = ts[i + 1] - ts[i]
        s = (t - ts[i]) / h
        s2, s3 = s * s, s * s * s
        return ((2 * s3 - 3 * s2 + 1) * vs[i] + (s3 - 2 * s2 + s) * h * m[i]
                + (-2 * s3 + 3 * s2) * vs[i + 1] + (s3 - s2) * h * m[i + 1])
    return at


def check_p6_camera(P, keys, stand_span, walk_span, margin=60, min_window=0.8, end=10.5):
    """From the real camera keys and the player's curve: the visible x range every 0.02 s (canvas 3200x1800,
    view 3200/zoom wide; both figures sit at z 1, so no parallax). Asserts the stand is visible only before T,
    walk2 only after, an empty window (neither within `margin`) >= min_window, and nothing past the plate edges.
    -> T, the middle of the empty window."""
    ts = [k["t"] for k in keys]
    es = [k.get("ease") for k in keys]
    fx, fy = (story_curve(ts, [k[c] for k in keys], es) for c in ("x", "y"))
    fz = story_curve(ts, [np.log(k["zoom"]) for k in keys], es)
    grid = np.arange(0, end + 1e-9, 0.02)
    empty, vis = [], []
    for t in grid:
        z = float(np.exp(fz(t)))
        x0, x1 = fx(t) - 1600 / z, fx(t) + 1600 / z
        vis.append((t, x0, x1, fy(t) - 900 / z, fy(t) + 900 / z, z))
        empty.append(x0 > stand_span[1] + margin and x1 < walk_span[0] - margin)
    runs, i = [], 0
    while i < len(grid):
        if empty[i]:
            j = i
            while j + 1 < len(grid) and empty[j + 1]:
                j += 1
            runs.append((grid[i], grid[j]))
            i = j + 1
        else:
            i += 1
    assert runs, "p6: no moment with neither figure in frame"
    w0, w1 = max(runs, key=lambda r_: r_[1] - r_[0])
    assert w1 - w0 >= min_window, f"p6: empty window only {w1 - w0:.2f} s"
    T = round((w0 + w1) / 2, 2)
    for t, x0, x1, y0, y1, z in vis:
        sees_stand = x1 > stand_span[0] and x0 < stand_span[1]
        sees_walk = x1 > walk_span[0] and x0 < walk_span[1]
        assert not (sees_stand and t >= T), f"p6: stand in frame at {t:.2f} s after the swap"
        assert not (sees_walk and t < T), f"p6: walk2 in frame at {t:.2f} s before the swap"
    # Plate edges (shifted units): the near plate spans the whole picture; y by the plate height.
    lo_x, hi_x = 0 + P.shift[0] + 0, 5000 + P.shift[0]
    lo_y, hi_y = 0 + P.shift[1], 1900 + P.shift[1]
    ok = {"x": min(v[1] for v in vis) - lo_x, "x2": hi_x - max(v[2] for v in vis),
          "y": min(v[3] for v in vis) - lo_y, "y2": hi_y - max(v[4] for v in vis)}
    print(f"p6 camera: stand x {stand_span[0]:.0f}..{stand_span[1]:.0f}, walk2 x {walk_span[0]:.0f}..{walk_span[1]:.0f}; "
          f"empty window {w0:.2f}..{w1:.2f} s ({w1 - w0:.2f} s), swap T = {T:.2f} s; "
          f"edge clearance units {{{', '.join(f'{k}: {v:.0f}' for k, v in ok.items())}}}")
    assert min(ok.values()) >= -1, f"p6: the camera shows past the plate edge: {ok}"
    return T


def plate_p6(picks):
    P = Plate("p6")
    layers = []
    for e in P.bases():
        L = P.layer(e, e["name"])
        if e["name"] == "fire_glow":
            L["touch"] = [{"kind": "flicker", "rate": 5, "amount": 0.22, "seed": 2}]
        layers.append(L)
    fire = next(e for e in P.bases() if e["name"] == "fire_glow")
    fx, fy = P.bright_center(fire)

    # The traveler: nothing moves or fades on screen. She sits, stands up at the fire (the small in-place crossfade),
    # and the camera pans right along the road (pushing in) and leaves the standing figure behind out of frame;
    # while NEITHER figure is in frame the drawing swaps (instant step) to the unlit one already standing at the
    # water's edge, and the pan brings that one into frame.
    def span_x(e, a):
        """Canvas x span (shifted units) of a layer's figure (alpha > 127)."""
        xs = np.nonzero((a[..., 3] > 127).any(0))[0]
        x, _, _, _ = P.box(e)
        return x + xs.min() * e["scale"], x + (xs.max() + 1) * e["scale"]

    def own_filled(e):
        """walk2 at its own place as a crisp solid ink silhouette in the plate's hand (traveler_walk2.png itself is
        untouched): inside alpha > 127 the colour is near.png's deep ink (median of its darkest 5% opaque pixels)
        with 15% of the drawing's own luminance detail kept, clamped to ink + 12; the alpha edge hardened (127,
        1 px antialias); a thin cold rim (the lamp points' blue, 60%, fading over 3 px) on the left edge and hood top."""
        a = np.array(Image.open(os.path.join(LAYERS, "p6", e["file"])).convert("RGBA")).astype(np.float32)
        near = np.asarray(Image.open(os.path.join(LAYERS, "p6", "near.png")).convert("RGBA")).astype(np.float32)
        op = near[near[..., 3] > 250][:, :3]
        lum = op.mean(1)
        ink = np.median(op[lum <= np.quantile(lum, 0.05)], 0)
        rr, gg, bb = near[..., 0], near[..., 1], near[..., 2]
        pts = near[(bb > 170) & (bb > rr + 40) & (near[..., 3] > 200)][:, :3]
        rim = np.median(pts, 0)
        m = a[..., 3] > 127
        L = a[..., :3].mean(-1)
        detail = L - np.median(L[m])
        col = ink[None, None, :] + 0.15 * detail[..., None]
        col = np.clip(col, ink - 12, ink + 12)
        # alpha: hard at 127, 1 px antialias (a one-pixel blur of the mask, kept to the edge band)
        soft = nd.gaussian_filter(m.astype(np.float32), 0.5)
        al = np.clip((soft - 0.25) / 0.5, 0, 1)
        # rim: run length inside the mask from the left, and from the top within the hood (top quarter)
        ys, xs = np.nonzero(m)
        y0, y1 = ys.min(), ys.max() + 1
        w = np.zeros(m.shape, np.float32)
        run = np.zeros(m.shape[0], int)
        for x in range(m.shape[1]):
            run = np.where(m[:, x], run + 1, 0)
            w[:, x] = np.maximum(w[:, x], np.where((run >= 1) & (run <= 3), 1 - (run - 1) / 3.0, 0) * np.where(run > 0, 1, 0))
        # a pixel counts only if the run began at the left edge of the silhouette (leftmost in its row)
        lead = np.zeros(m.shape, bool)
        for y in range(m.shape[0]):
            xr = np.nonzero(m[y])[0]
            if len(xr):
                lead[y, xr.min():xr.min() + 3] = True
        w = np.where(lead, w, 0)
        hood = np.zeros(m.shape, np.float32)
        run = np.zeros(m.shape[1], int)
        for y in range(m.shape[0]):
            run = np.where(m[y], run + 1, 0)
            if y0 <= y < y0 + (y1 - y0) // 4:
                hood[y] = np.where((run >= 1) & (run <= 3), 1 - (run - 1) / 3.0, 0)
        top_ok = np.zeros(m.shape, bool)
        for x in range(m.shape[1]):
            yr = np.nonzero(m[:, x])[0]
            if len(yr):
                top_ok[yr.min():yr.min() + 3, x] = True
        hood = np.where(top_ok, hood, 0)
        k = (0.6 * np.maximum(w, hood))[..., None]
        col = col * (1 - k) + rim[None, None, :] * k
        out = np.dstack([np.clip(col, 0, 255), al * 255]).astype(np.uint8)
        P.made["walk2.png"] = out
        print(f"p6 walk2: ink {tuple(int(v) for v in ink)}, rim {tuple(int(v) for v in rim)}")
        return out

    sit_end, stand_fade = 4.0, 0.4
    e_stand, e_w2 = P.entry(picks["stand"]), P.entry(picks["walk2"])
    a_stand = np.asarray(Image.open(os.path.join(LAYERS, "p6", e_stand["file"])).convert("RGBA"))
    a_w2 = own_filled(e_w2)
    sx, wx = span_x(e_stand, a_stand), span_x(e_w2, a_w2)

    # The camera (unshifted comps units as P.cam takes them): hold, then an eased push-in pan to the water.
    cam_keys = [P.cam(0, 1650, 1000, 1.0), P.cam(4.6, 1650, 1000, 1.0),
                P.cam(7.55, 2760, 1055, 1.3), P.cam(10.5, 3650, 1060, 1.3, ease="inout")]
    T = check_p6_camera(P, cam_keys, sx, wx)

    L = P.layer(e_stand, "stand")
    pts = [(0, 0.0), (sit_end, 0.0), (sit_end + stand_fade / 2, 1.0), (T, 1.0), (T + 0.02, 0.0)]
    L["keys"] = opacity_keys(pts, [p[0] for p in pts])
    layers.append(L)
    L = P.layer(e_w2, "walk2")
    pts = [(0, 0.0), (T, 0.0), (T + 0.02, 1.0)]
    L["keys"] = opacity_keys(pts, [p[0] for p in pts])
    layers.append(L)
    if "sit" in picks:
        L = P.layer(P.entry(picks["sit"]), "sit")
        pts = [(0, 1.0), (sit_end + stand_fade / 2, 1.0), (sit_end + stand_fade, 0.0)]
        L["keys"] = opacity_keys(pts, [p[0] for p in pts])
        layers.insert(len(layers) - 2, L)
    return P, {
        "id": PREFIX + "p6", "at": 71, "until": 81.5,
        "in": {"kind": "dissolve", "dur": 1.0},
        "camera": cam_keys,
        "note": "INK: The traveler (tools/storybook/sb_wire_ink.py writes this plate; edit the script, not here).",
        "layers": layers,
        "fx": [{"kind": "particles", "preset": "sparks", "at": [r(fx), r(fy - 60)], "area": [110, 40], "z": 1.0,
                "rate": 4, "life": 2.2, "speed": [40, 95], "dir": [0, -1], "spread": 18, "gravity": [0, -20],
                "size": [3, 6], "wobble": 0.7, "damping": 0.3, "seed": 6}],
        "cues": [],
    }


def p7t_point(what, frac=None):
    """p7 round 4: a SAM mask's centre (or its top at frac of its height) in p7's canvas units (unshifted)."""
    import ink_layers as IL
    m = np.asarray(Image.open(os.path.join(IL.WORK, f"p7t_s{IL.P7T_SEED}_{what}.png")).convert("L")) > 127
    ys, xs = np.nonzero(m)
    u = 3200 / m.shape[1]
    y = ys.mean() if frac is None else ys.min() + frac * (ys.max() - ys.min())
    return xs.mean() * u, y * u, (xs.min() * u, ys.min() * u, xs.max() * u, ys.max() * u)


def plate_p7_tall(picks):
    """p7 round 4: one tall drawing the camera tilts through (ink_layers P7T_*). Close on the hood and the flask in
    the water; blue slides into the reflection (0.6-2.5 s); the rim on the hood by 2.5 s (84.0); the tilt up until the
    cage and its holder's hand sit inside the 2.39 band; at 5.5 s the tip down into the water (p7u)."""
    P = Plate("p7")
    fx, fy, _ = p7t_point("flask")
    hx, hy, hbox = p7t_point("person")
    cx, cy, cbox = p7t_point("cage")
    _, _, obox = p7t_point("holder")
    layers = []
    for e in P.bases():
        n = e["name"]
        L = P.layer(e, n)
        if n == "water":
            L["touch"] = [{"kind": "water", "amp": 1.2, "freq": 1.2, "scale": 40},
                          {"kind": "ripple", "centers": [P.S(fx, fy + 30)], "period": 2.6, "speed": 55, "amp": 2,
                           "rings": 3, "gap": 24, "reach": 320, "squash": 0.3, "light": 0.22}]
        elif n == "lamp":
            x, y, w, h = P.box(e)
            L["pivot"] = [r(x + w / 2), r(y)]
            L["keys"] = [{"t": 0, "dy": 0}, {"t": 2.0, "dy": -6, "ease": "inout"}, {"t": 4.0, "dy": 4, "ease": "inout"},
                         {"t": 6.0, "dy": -2, "ease": "inout"}]
        elif n == "lamp_glare":
            L["touch"] = [dict(GLARE_FLICKER)]
            L["keys"] = [{"t": 0, "dy": 0}, {"t": 2.0, "dy": -6, "ease": "inout"}, {"t": 4.0, "dy": 4, "ease": "inout"},
                         {"t": 6.0, "dy": -2, "ease": "inout"}]
        elif n == "reflection_blue":
            # The cage's light slides into the reflection from the river side (right) and settles as drawn.
            L["touch"] = [{"kind": "water", "amp": 2.0, "freq": 1.1, "scale": 50}, dict(GLARE_FLICKER, amount=0.1)]
            L["keys"] = [{"t": 0, "dx": 320, "opacity": 0}, {"t": 0.6, "dx": 320, "opacity": 0},
                         {"t": 2.5, "dx": 0, "opacity": 1, "ease": "out"}]
        layers.append(L)
    for state, f in picks.items():
        e = P.entry(f)
        if state != "blue_rim":
            continue
        L = P.layer(e, state)
        L["keys"] = [{"t": 0, "opacity": 0}, {"t": 1.7, "opacity": 0}, {"t": 2.5, "opacity": 1, "ease": "out"}]
        L["touch"] = [dict(GLARE_FLICKER, amount=0.12)]
        i = next((i for i, l in enumerate(layers) if l["id"] == "traveler"), len(layers) - 1)
        layers.insert(i + 1, L)
    # Camera (unshifted canvas units). The band shows 3200/zoom x 1339/zoom units.
    import ink_layers as IL
    open_x, open_y, open_z = IL.P7T_KEYS["open"]
    up_x, up_y, up_z = IL.P7T_KEYS["up"]
    tip_x, tip_y, tip_z = IL.P7T_KEYS["tip"]
    mid_x, mid_y, mid_z = IL.P7T_KEYS["mid"]
    return P, {
        "id": PREFIX + "p7", "at": 81.5, "until": 87.5,
        "in": {"kind": "dissolve", "dur": 0.6},
        "camera": [P.cam(0, open_x, open_y + 40, open_z), P.cam(0.8, open_x, open_y, open_z, ease="out"),
                   P.cam(2.8, mid_x, mid_y, mid_z, ease="inout"),
                   P.cam(4.7, up_x, up_y, up_z, ease="inout"), P.cam(5.5, up_x, up_y - 15, up_z),
                   P.cam(6.0, tip_x, tip_y, tip_z, ease="in")],
        "note": "INK: The water (tools/storybook/sb_wire_ink.py writes this plate; edit the script, not here).",
        "layers": layers,
        "cues": [],
    }


def plate_p7(picks):
    import ink_layers as IL
    if IL.PLATES["p7"].get("carved"):
        return plate_p7_tall(picks)
    P = Plate("p7")
    layers = []
    head = 2.5
    picked = {s: P.entry(f) for s, f in picks.items()}
    swap = "head_up" in picked and picked["head_up"].get("blend", "mix") == "mix"
    for e in P.bases():
        n = e["name"]
        L = P.layer(e, n)
        if n == "water":
            L["touch"] = [{"kind": "water", "amp": 1.2, "freq": 1.2, "scale": 40},
                          {"kind": "ripple", "centers": [P.S(*P7_FLASK)], "period": 2.6, "speed": 55, "amp": 2,
                           "rings": 3, "gap": 24, "reach": 320, "squash": 0.3, "light": 0.22}]
        elif n == "lamp_glare":
            L["touch"] = [dict(GLARE_FLICKER)]
        elif n == "reflection_blue":
            # Slides in from the river side over the reflected face and grows (about its left edge).
            x, y, w, h = P.box(e)
            L["pivot"] = [r(x), r(y + h / 2)]
            L["touch"] = [{"kind": "water", "amp": 2.5, "freq": 1.1, "scale": 50}]
            L["keys"] = [{"t": 0, "dx": 260, "scale": 0.8, "opacity": 0},
                         {"t": 0.6, "dx": 260, "scale": 0.8, "opacity": 0},
                         {"t": 2.5, "dx": 0, "scale": 1.5, "opacity": 1, "ease": "out"}]
        elif n == "traveler" and swap:
            L["keys"] = [{"t": 0, "opacity": 1}, {"t": head + 0.2, "opacity": 1}, {"t": head + 0.4, "opacity": 0}]
        layers.append(L)
    for state, e in picked.items():
        L = P.layer(e, state)
        if e.get("blend", "mix") == "mix":
            L["keys"] = [{"t": 0, "opacity": 0}, {"t": head, "opacity": 0}, {"t": head + 0.2, "opacity": 1}]
        else:   # an add layer (blue_rim): fades in over the hood's edge (2.5-3.3 s), breathing with the lamp's glare
            L["keys"] = [{"t": 0, "opacity": 0}, {"t": head, "opacity": 0}, {"t": head + 0.8, "opacity": 1}]
            L["touch"] = [dict(GLARE_FLICKER, amount=0.12)]
        # just above the base traveler
        i = next((i for i, l in enumerate(layers) if l["id"] == "traveler"), len(layers) - 1)
        layers.insert(i + 1, L)
    return P, {
        "id": PREFIX + "p7", "at": 81.5, "until": 87.5,
        "in": {"kind": "dissolve", "dur": 0.6},
        # Low on the reflection; tilt up to the hood and the lamp; at 5.5 s tip down into the water (into p7u).
        "camera": [P.cam(0, 1450, 1750, 1.3), P.cam(2.5, 1450, 1700, 1.3),
                   P.cam(4.6, 1500, 1150, 1.15, ease="inout"), P.cam(5.5, 1500, 1150, 1.15),
                   P.cam(6.0, 1470, 1700, 1.3, ease="in")],
        "note": "INK: The water (tools/storybook/sb_wire_ink.py writes this plate; edit the script, not here).",
        "layers": layers,
        "cues": [],
    }


def plate_p7u(picks):
    P = Plate("p7u")
    layers = []
    for e in P.bases():
        n = e["name"]
        L = P.layer(e, n)
        if n == "bubbles":
            L["keys"] = [{"t": 0, "dy": 0}, {"t": 2.6, "dy": -150, "ease": "linear"}]
        elif n == "lamp_warped":
            L["touch"] = [{"kind": "water", "amp": 6, "freq": 0.7, "scale": 150},
                          {"kind": "flicker", "rate": 1.1, "amount": 0.14, "seed": 8}]
        layers.append(L)
    for state, file in picks.items():
        layers.append(P.layer(P.entry(file), state))
    return P, {
        "id": PREFIX + "p7u", "at": 87.0, "until": 89.5,
        "in": {"kind": "dissolve", "dur": 0.5},
        "out": {"kind": "fade", "dur": 2.0, "color": "#000000"},
        # The tip carries on under: the view settles down from the surface.
        "camera": [P.cam(0, 1600, 760, 1.06), P.cam(1.2, 1600, 880, 1.04, ease="out")],
        "note": "INK: Underwater (tools/storybook/sb_wire_ink.py writes this plate; edit the script, not here).",
        "layers": layers,
        "fx": [{"kind": "particles", "preset": "bubbles", "at": [1650, 1450], "area": [1300, 300], "z": 0.85,
                "rate": 7, "speed": [70, 130], "size": [4, 10], "seed": 9}],
        "cues": [],
    }


# ---------------------------------------------------------------- copy + json
def sha(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None


def copy_art(P):
    dst_dir = os.path.join(ART, P.pid)
    os.makedirs(dst_dir, exist_ok=True)
    changed = 0
    for clean, src in P.used.items():
        s, d = os.path.join(LAYERS, P.pid, src), os.path.join(dst_dir, clean)
        if clean in P.made:
            tmp = d + ".tmp.png"
            Image.fromarray(P.made[clean], "RGBA").save(tmp)
            if sha(tmp) != sha(d):
                os.replace(tmp, d)
                changed += 1
            else:
                os.remove(tmp)
        elif sha(s) != sha(d):
            shutil.copyfile(s, d)
            changed += 1
        write_import(d)
    for f in os.listdir(dst_dir):   # drawings no longer used (a picks change)
        if f.endswith(".png") and f not in P.used:
            os.remove(os.path.join(dst_dir, f))
            if os.path.exists(os.path.join(dst_dir, f + ".import")):
                os.remove(os.path.join(dst_dir, f + ".import"))
            print("removed", P.pid, f)
    print(f"{P.pid}: {len(P.used)} layers, {changed} copied")
    return changed


def compact(v):
    return json.dumps(v, ensure_ascii=False)


def fmt(d):
    """The file's own style: top-level and plate fields a line each; long lists of objects one per line."""
    out = ["{"]
    items = list(d.items())
    for i, (k, v) in enumerate(items):
        comma = "," if i < len(items) - 1 else ""
        if k == "plates":
            out.append(f'  "plates": [')
            for j, p in enumerate(v):
                out.append("    {")
                pi = list(p.items())
                for m, (pk, pv) in enumerate(pi):
                    c2 = "," if m < len(pi) - 1 else ""
                    line = f"      {compact(pk)}: {compact(pv)}"
                    if isinstance(pv, list) and pv and isinstance(pv[0], dict) and (len(line) > 160 or (pk == "cues" and len(pv) > 1)):
                        out.append(f"      {compact(pk)}: [")
                        for n, it in enumerate(pv):
                            out.append(f"        {compact(it)}" + ("," if n < len(pv) - 1 else ""))
                        out.append("      ]" + c2)
                    else:
                        out.append(line + c2)
                out.append("    }" + ("," if j < len(v) - 1 else ""))
            out.append("  ]" + comma)
        elif k == "cues" and v:
            out.append('  "cues": [')
            for n, it in enumerate(v):
                out.append(f"    {compact(it)}" + ("," if n < len(v) - 1 else ""))
            out.append("  ]" + comma)
        else:
            out.append(f"  {compact(k)}: {compact(v)}{comma}")
    out.append("}")
    return "\n".join(out) + "\n"


def main():
    picks = json.load(open(PICKS, encoding="utf-8"))
    sb = json.load(open(SB, encoding="utf-8"))
    built = [f(picks.get(pid, {})) for pid, f in
             [("p5", plate_p5), ("p6", plate_p6), ("p7", plate_p7), ("p7u", plate_p7u)]]
    for P, _ in built:
        copy_art(P)

    keep, old_cues = [], []
    for p in sb["plates"]:
        if p["id"] in REPLACED or p["id"].startswith(PREFIX):
            old_cues += [dict(c, at=round(p["at"] + c["at"], 3)) for c in p.get("cues", [])]
        else:
            keep.append(p)
    for c in old_cues:
        for match, at in RETIME:
            if all(c.get(k) == v for k, v in match.items()):
                c["at"] = at
    new = [pl for _, pl in built]
    for c in old_cues:   # each cue to the newest plate up at its absolute time, at the same absolute time
        host = max((pl for pl in new if pl["at"] <= c["at"] + 1e-6), key=lambda pl: pl["at"])
        host["cues"].append(dict(c, at=round(c["at"] - host["at"], 3)))
    for pl in new:
        pl["cues"].sort(key=lambda c: c["at"])
        for k in ("fx", "cues"):
            if not pl.get(k):
                pl.pop(k, None)
    sb["plates"] = keep + new
    text = fmt(sb)
    json.loads(text)
    open(SB, "w", encoding="utf-8", newline="\n").write(text)
    print("cues:", ", ".join(f"{pl['id']}+{c['at']}={pl['at'] + c['at']:.1f} {c.get('id') or c.get('name') or c['do']}"
                             for pl in new for c in pl.get("cues", [])))
    print("wrote", os.path.relpath(SB, ROOT))


if __name__ == "__main__":
    main()
