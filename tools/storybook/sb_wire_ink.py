"""Wire the ink plates (tools/storybook/out/ink_layers/<plate>/layers.json) into SB00.

Re-runnable: reads each plate's layers.json and tools/storybook/ink_picks.json (which
drawing plays each state), copies only the used layers (base layers, glows, the picked
state drawings) to godot/art/storybook/sb00/<plate>/ under clean names (<name>.png for a
base layer, <state>.png for a state drawing), writes their .import files, and rewrites
SB00's plates in godot/data/storybook/sb00.json: the placeholder cards a wired ink plate
covers (COVERS; or the ink plates of an earlier run) are replaced by the ink plates, and every
plate cue keeps its absolute time (moved to whichever new plate is up then). Cards no ink plate
covers yet, the file's own cues and "live" are left as they are.

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

# The placeholder cards each ink plate replaces: a card goes only once the ink plate that covers its span is wired
# (a plate function below and its layers.json built). Every ink_ plate of an earlier run is replaced too.
COVERS = {"p0": {"p0"}, "p1": {"p1", "p2"}, "p1d": set(), "p2": {"p3"}, "p3": {"p4", "p5"}, "p4": {"p6"},
          "p5": {"p7", "p8", "p9", "p10a", "p10b", "p10c"}}
PLATE_ORDER = ["p0", "p1", "p1d", "p2", "p3", "p3d", "p4", "p5", "p6", "p7", "p7u"]
PREFIX = "ink_"

# Where the art's own features are (comps units, found in the layer images; they follow the comps).
P5_FOURTH_LIGHT = (1918, 565)   # Storybook 5 (E2): the water under the hanging basket lamp (out/ink_layers/p5)
P5_LAMP = (1918, 438)           # the basket lamp itself
P3_AT = {"hand": (399, 882), "dead": (1030, 430), "wound": (2780, 560), "stones": (2730, 1070)}   # p3 rc units
P1_ANVIL = (1652, 746)          # p1 (r6): the anvil, where the hammer sparks fly
P7_FLASK = (1550, 1490)         # the comps' rings from the flask
GLARE_FLICKER = {"kind": "flicker", "rate": 0.9, "amount": 0.2, "seed": 4}   # p7's lamp glare (blue_rim breathes with it)
# Storybook 5, solver AB (tools/storybook/ink_sb5_ab.py writes them): built file -> (patched file, entry overrides)
SB5_AB = {
    "p0": {f + ".png": (f + "_sb5.png", {}) for f in ("dark", "lit", "glow", "flame")},
    "p2": {f + ".png": (f + "_sb5.png", {}) for f in ("base", "threads", "threads_glow", "door_glow")},
    "p6": {"near.png": ("near_sb5.png", {})},
    "p7": {"water.png": ("water_sb5.png", {})},
    "p1": {f + ".png": (f + "_sb5p.png", {}) for f in ("base", "torches")},     # solver P (ink_sb5_p.py): procession out
    "p7u": {"bubbles.png": ("bubbles_sb5.png", {"pos": [0, 700], "scale": 1.0, "size_px": [3200, 1100]})},
}
P6_LAMP_REFL = dict(file="lamp_refl_sb5.png", far_px=(860, 735), size_px=(300, 140))   # on the far layer's grid (z 3)
P7U_BUBBLE_COLUMN = (1480, 1100)    # p7u: where the bubble column rises (units, the traveler's way in)

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
        for e in self.meta["layers"]:     # Storybook 5 (solver AB): patched copies beside the built layers
            alt = SB5_AB.get(pid, {}).get(e["file"])
            if alt and os.path.exists(os.path.join(LAYERS, pid, alt[0])):
                e["file"] = alt[0]
                e.update(alt[1])
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
    """The Low Ford (Storybook 4, ink_rc_build): one plane (the re-carved ChatGPT source, the wagon re-cut) + the blue
    fires (add, flickering). Close on the fourth light midstream with nobody in frame (rings drifting under it), a slow
    push; from 7.5 s the pull back to the full wide by 14.5 s: the drowned stand in the ditch water. The mist band
    over the river (z 1.3) gives the pull-back its depth."""
    P = Plate("p5")
    fx, fy = P5_FOURTH_LIGHT
    layers = []
    for e in P.bases():
        L = P.layer(e, e["name"])
        if e["name"] == "land":
            L["touch"] = [{"kind": "ripple", "centers": [P.S(fx, fy)], "period": 3.6, "speed": 30, "amp": 1.4,
                           "rings": 3, "gap": 20, "reach": 260, "squash": 0.28, "light": 0.3}]
        elif e["name"] == "fires":    # the blue flames breathe: slow, small
            L["touch"] = [{"kind": "flicker", "rate": 1.3, "amount": 0.18, "seed": 5}]
        layers.append(L)
    return P, {
        "id": PREFIX + "p5", "at": 56, "until": 71,
        "in": {"kind": "fade", "dur": 1.4, "color": "#000000"},
        # Storybook 5: no close (the judge: the wide pushed past its detail at 2.35). Opens on the wide (1.08, the
        # carve's px at 1.14x), a slow push toward the hanging lamp to 7.5 s (1.15, the most), the pull back to the
        # whole ford road by 13 s (0.93: the lamp and its chain stay in, the near dead's feet go under the frame).
        "camera": [P.cam(0, 1880, 820, 1.08), P.cam(7.5, P5_LAMP[0], 700, 1.15, ease="out"),
                   P.cam(13.0, 1800, 1050, 0.93, ease="inout"), P.cam(15.0, 1800, 1050, 0.93)],
        "note": "INK: The Low Ford; the drowned (tools/storybook/sb_wire_ink.py writes this plate; edit the script, not here).",
        "layers": layers,
        "fx": [{"kind": "mist", "rect": P.S(-200, 520) + [4000, 260], "z": 1.3, "color": "#8f9fb6", "density": 0.24,
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


SB5_P6_SIT = False      # Storybook 5: the seated drawing is no longer shown


def p6_lamp_refl(P, cam_keys, end=10.5, soft=0.02):
    """The far bank lamps' reflections on the lamps' own layer (far, z 3), drawn over near; a reveal map shows each
    pixel only from when the near layer under it is river water for good (the near hill hides it before)."""
    src = os.path.join(LAYERS, "p6", P6_LAMP_REFL["file"])
    if not os.path.exists(src):
        return None
    far = next(e for e in P.meta["layers"] if e["name"] == "far")
    near = next(e for e in P.meta["layers"] if e["name"] == "near")
    sc = far["scale"]
    u0, v0 = P6_LAMP_REFL["far_px"]
    w, h = P6_LAMP_REFL["size_px"]
    e = {"file": P6_LAMP_REFL["file"], "name": "lamp_refl", "z": far["z"], "blend": "mix",
         "pos": [far["pos"][0] + u0 * sc, far["pos"][1] + v0 * sc], "scale": sc, "size_px": [w, h]}
    river = np.asarray(Image.open(os.path.join(LAYERS, "_work", "p6_sam_river.png")).convert("L")
                       .resize(tuple(near["size_px"]), Image.NEAREST)) > 127
    ts = [k["t"] for k in cam_keys]
    es = [k.get("ease") for k in cam_keys]
    fX, fY = (story_curve(ts, [k[c] for k in cam_keys], es) for c in ("x", "y"))
    fZ = story_curve(ts, [np.log(k["zoom"]) for k in cam_keys], es)
    V, U = np.mgrid[0:h, 0:w].astype(np.float32)
    cx = e["pos"][0] + P.shift[0] + (U + 0.5) * sc          # shifted canvas units on the far layer
    cy = e["pos"][1] + P.shift[1] + (V + 0.5) * sc
    z = far["z"]
    t_w = np.zeros((h, w), np.float32)
    for t in np.arange(0, end + 1e-9, 0.02):
        X, Y = fX(t), fY(t)
        dx, dy = cx - 1600 - (X - 1600) / z, cy - 900 - (Y - 900) / z      # from the screen centre (units)
        nx = ((1600 + (X - 1600) + dx - near["pos"][0] - P.shift[0]) / near["scale"]).astype(int)
        ny = ((900 + (Y - 900) + dy - near["pos"][1] - P.shift[1]) / near["scale"]).astype(int)
        ok = (nx >= 0) & (ny >= 0) & (nx < river.shape[1]) & (ny < river.shape[0])
        wet = np.zeros((h, w), bool)
        wet[ok] = river[ny[ok], nx[ok]]
        t_w = np.where(~wet, t + 0.02, t_w)          # the last time it was not over the water (+ a step)
    p = np.clip(t_w / end, 0, 1)
    v = np.where(t_w > end, 1.0, np.clip(p * (1 + soft) - soft, 0, 1))
    m = (v * 255 + 0.5).astype(np.uint8)
    P.used["lamp_refl_map.png"] = "lamp_refl_map.png"
    P.made["lamp_refl_map.png"] = np.dstack([m, m, m, np.full_like(m, 255)])
    a = np.asarray(Image.open(src))[..., 3] > 20
    print(f"p6 lamp_refl: shows from {t_w[a].min():.2f}..{t_w[a].max():.2f} s plate time ({(t_w[a] > end).mean():.0%} never)")
    return P.layer(e, "lamp_refl", touch=[{"kind": "reveal", "map": f"{RES}/p6/lamp_refl_map.png", "t0": 0, "t1": end,
                                            "soft": soft}, {"kind": "flicker", "rate": 1.3, "amount": 0.18, "seed": 13}])


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
        for x in range(m.shape[1] - 1, -1, -1):           # Storybook 5: runs from the right (the water side)
            run = np.where(m[:, x], run + 1, 0)
            w[:, x] = np.maximum(w[:, x], np.where((run >= 1) & (run <= 3), 1 - (run - 1) / 3.0, 0) * np.where(run > 0, 1, 0))
        # a pixel counts only if the run began at the left edge of the silhouette (leftmost in its row)
        lead = np.zeros(m.shape, bool)
        for y in range(m.shape[0]):
            xr = np.nonzero(m[y])[0]
            if len(xr):
                lead[y, xr.max() - 2:xr.max() + 1] = True        # Storybook 5: the right edge, facing the water
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
        k = (0.9 * np.maximum(w, hood))[..., None]       # Storybook 5: 0.6 did not show at 1:1 (judge r1)
        rim = rim + 0.3 * (255 - rim)                     # a paler cold rim against the pale river
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

    # Storybook 5: one drawing for the whole fire beat (judge r1: the sit -> stand swap showed on screen): the standing
    # traveler (her flask pays off in p7) from the first frame, until the off-screen swap to walk2
    L = P.layer(e_stand, "stand")
    pts = [(0, 1.0), (T, 1.0), (T + 0.02, 0.0)]
    L["keys"] = opacity_keys(pts, [p[0] for p in pts])
    layers.append(L)
    L = P.layer(e_w2, "walk2")
    pts = [(0, 0.0), (T, 0.0), (T + 0.02, 1.0)]
    L["keys"] = opacity_keys(pts, [p[0] for p in pts])
    layers.append(L)
    refl = p6_lamp_refl(P, cam_keys)
    if refl:
        layers.insert(next(i for i, l in enumerate(layers) if l["id"] == "near") + 1, refl)
    if "sit" in picks and SB5_P6_SIT:
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
        "fx": [{"kind": "particles", "preset": "bubbles", "at": list(P7U_BUBBLE_COLUMN), "area": [160, 120], "z": 0.85,
                "rate": 7, "speed": [70, 130], "size": [4, 10], "seed": 9}],
        "cues": [],
    }


# ---------------------------------------------------------------- Storybook 4: p0, p1, p2, p4 (ink_r6.py builds them)
def r6_map(P, e, fn, name):
    """A reveal map for layer e, the size of its image (small), from fn(canvas_x, canvas_y) in the plate's own units."""
    w, h = e["size_px"]
    mw = 256
    mh = max(2, round(mw * h / w))
    ys, xs = np.mgrid[0:mh, 0:mw].astype(np.float32)
    cx = e["pos"][0] + (xs + 0.5) * w / mw * e["scale"]
    cy = e["pos"][1] + (ys + 0.5) * h / mh * e["scale"]
    v = (np.clip(fn(cx, cy), 0, 1) * 255 + 0.5).astype(np.uint8)
    P.used[name + ".png"] = name + ".png"
    P.made[name + ".png"] = np.dstack([v, v, v, np.full_like(v, 255)])
    return f"{RES}/{P.pid}/{name}.png"


def r6_layers(P):
    return {e["name"]: e for e in P.bases()}


def plate_p0(picks):
    """The lamp at the post: dusk-blue and unlit; at 0.9 s the flame catches from a spark, its warm light spreads (1-2.2 s)."""
    P = Plate("p0")
    E = r6_layers(P)
    fx_, fy_bot, fy_top = P.meta["features"]["flame"]
    fy = (fy_bot + fy_top) / 2
    W, H = P.meta["canvas_units"]
    dmax = max(np.hypot(x - fx_, (y - fy) * 1.15) for x in (0, W) for y in (0, H))
    lit = P.layer(E["lit"], "lit", touch=[
        {"kind": "reveal", "map": r6_map(P, E["lit"], lambda x, y: (np.hypot(x - fx_, (y - fy) * 1.15) / dmax) ** 0.8, "lit_map"),
         "t0": 1.0, "t1": 2.2, "soft": 0.14},
        {"kind": "flicker", "rate": 5, "amount": 0.05, "seed": 2}])
    flame = P.layer(E["flame"], "flame", pivot=P.S(fx_, fy_bot),
                    keys=[{"t": 0, "scale": 0.06, "opacity": 0}, {"t": 0.88, "scale": 0.06, "opacity": 0},
                          {"t": 0.9, "scale": 0.1, "opacity": 1}, {"t": 1.2, "scale": 1, "opacity": 1, "ease": "out"}],
                    touch=[{"kind": "flicker", "rate": 8, "amount": 0.16, "seed": 3}])
    glow = P.layer(E["glow"], "glow", keys=[{"t": 0, "opacity": 0}, {"t": 0.95, "opacity": 0}, {"t": 1.9, "opacity": 1, "ease": "out"}],
                   touch=[{"kind": "flicker", "rate": 6, "amount": 0.3, "seed": 1}])
    return P, {
        "id": PREFIX + "p0", "at": 0, "until": 2.5,
        "in": {"kind": "fade", "dur": 0.6, "color": "#000000"},
        # Static, a tiny push toward the lamp through the light run into Plate 1 (drawn until 4.1 s).
        "camera": [P.cam(0, 1700, 751, 1.0), P.cam(4.1, 1688, 772, 1.045, ease="linear")],
        "note": "INK: The lamp at the post (tools/storybook/sb_wire_ink.py writes this plate; edit the script, not here).",
        "layers": [P.layer(E["dark"], "dark"), lit, flame, glow],
        "fx": [{"kind": "particles", "preset": "sparks", "at": P.S(fx_, fy_bot - 30), "area": [30, 14], "z": 1.0, "rate": 0,
                "burst": [0.86], "count": 16, "speed": [60, 170], "size": [3, 6], "seed": 5}],
        "cues": [],
    }


def plate_p1(picks):
    """The cut and the chain: down from the smiths on the lip to the doorway; the slab slides shut (9.5-11.3 s), the glow goes out."""
    P = Plate("p1")
    E = r6_layers(P)
    f = P.meta["features"]
    ox0, oy0, ox1, oy1 = f["open"]
    sx0, sx1, sy0, sy1 = f["slab"]
    # the slab comes to rest centred on the opening; a static 1.15 (never grows on screen) so it nearly spans it,
    # the last of the glow a line either side before it goes out (r7a: 1.32 to span it all read as a giant stone)
    sw, ow = sx1 - sx0, ox1 - ox0
    sc = 1.15
    dx = r((ox0 + ox1) / 2 - (sx0 + sc * sw / 2))
    close0, close1 = 9.5, 11.3
    slab = P.layer(E["slab"], "slab", pivot=P.S(sx0, sy1),
                   keys=[{"t": 0, "dx": 0, "scale": sc}, {"t": close0, "dx": 0, "scale": sc},
                         {"t": close1, "dx": dx, "scale": sc, "ease": "inout"}])
    out = [{"t": 0, "opacity": 1}, {"t": close1 - 0.6, "opacity": 1}, {"t": close1 + 0.15, "opacity": 0, "ease": "out"}]
    curve = P.layer(E["curve"], "curve", keys=out)
    cglow = P.layer(E["curve_glow"], "curve_glow", keys=out, touch=[{"kind": "flicker", "rate": 0.5, "amount": 0.25, "seed": 11}])
    torches = P.layer(E["torches"], "torches", touch=[{"kind": "flicker", "rate": 7, "amount": 0.3, "seed": 12}])
    if sc > 1.0:
        print(f"p1: slab {sw:.0f} wide for a {ow:.0f} opening: scale {sc}")
    ax, ay = P1_ANVIL
    cx = (ox0 + ox1) / 2
    if P1_CUT:   # Storybook 5: the forge only (the torch procession painted out), a hard cut to p1d at P1_CUT
        for k in ("curve.png", "curve_glow.png", "slab.png"):   # the old doorway stays out of the new door beat
            P.used.pop(k, None)
        return P, {
            "id": PREFIX + "p1", "at": 2.5, "until": P1_CUT,
            "in": {"kind": "light", "dur": 1.6, "origin": [0.5, 0.52]},
            "camera": [P.cam(0, 1650, 700, 1.0), P.cam(1.2, 1650, 720, 1.0), P.cam(P1_CUT - 2.5, 1650, 760, 1.04)],
            "note": "INK: The cut and the chain (tools/storybook/sb_wire_ink.py writes this plate; edit the script, not here).",
            "layers": [P.layer(E["base"], "base"), torches],
            "fx": [{"kind": "particles", "preset": "sparks", "at": P.S(ax, ay), "area": [70, 20], "z": 1.0, "rate": 0,
                    "burst": [0.3, 1.1, 1.9, 2.7, 3.5, 4.3], "count": 18, "seed": 7}],
            "cues": [],
        }
    return P, {
        "id": PREFIX + "p1", "at": 2.5, "until": 15.5,
        "in": {"kind": "light", "dur": 1.6, "origin": [0.5, 0.52]},
        # The lip (hold), then down the chain and the torch column to the doorway by 8 s; a slow push while it shuts.
        "camera": [P.cam(0, 1650, 700, 1.0), P.cam(1.2, 1650, 760, 1.0),
                   P.cam(8.0, cx, 3080, 1.0, ease="inout"), P.cam(14.2, cx, 3100, 1.04)],
        "note": "INK: The cut and the chain (tools/storybook/sb_wire_ink.py writes this plate; edit the script, not here).",
        "layers": [P.layer(E["base"], "base"), curve, cglow, slab, torches],
        "fx": [{"kind": "particles", "preset": "sparks", "at": P.S(ax, ay), "area": [70, 20], "z": 1.0, "rate": 0,
                "burst": [0.3, 1.1, 1.9, 2.7, 3.5, 4.3, 5.1], "count": 18, "seed": 7}],
        # the slab shuts on a deep drum beat
        "cues": [{"at": close1, "do": "sfx", "name": "hit", "gain": 0.8}],
    }


P1_CUT = 7.6        # Storybook 5: the hard cut from the forge to the door plate (absolute s; between the two lines)
P1D_HIT = 13.8      # the slab lands on the drum hit (absolute s)
P1D_SLIDE = 2.4     # its slide (s)


def plate_p1d(picks):
    """The door (ChatGPT p1_D2 / p1_D2_shut, ink_sb5_p.py): a hard cut in from the forge; the doorway lit gold from deep
    inside, a slow push; the slab slides in from behind the right jamb, the gold dimming as the gap narrows, and lands
    on the drum hit: a hard switch to the shut picture (the chain across the slab), its gold seams flicker and settle."""
    P = Plate("p1d")
    E = r6_layers(P)
    f = P.meta["features"]
    sx0 = f["slab"][0]
    hit = round(P1D_HIT - P1_CUT, 3)
    t0 = hit - P1D_SLIDE
    dx0 = E["jamb"]["pos"][0] + 4 - sx0          # the slab's left edge starts just behind the jamb's edge
    prog = lambda u: -u ** 3 + 2 * u ** 2         # StoryCurve's segment with ease "in" (from rest, arriving at speed)
    slab = P.layer(E["slab"], "slab", keys=[{"t": 0, "dx": r(dx0)}, {"t": r(t0, 3), "dx": r(dx0)},
                                             {"t": hit, "dx": 0, "ease": "in"}])
    gk = [{"t": 0, "opacity": 1}, {"t": r(t0, 3), "opacity": 1}]
    for i in range(1, 7):
        u = i / 6
        gk.append({"t": r(t0 + u * P1D_SLIDE, 3), "opacity": r(0.3 + 0.7 * (1 - prog(u)) ** 1.3, 3)})
    gold = P.layer(E["gold"], "gold", keys=gk, touch=[{"kind": "flicker", "rate": 0.5, "amount": 0.12, "seed": 11}])
    shut = P.layer(E["shut"], "shut", keys=[{"t": 0, "opacity": 0}, {"t": hit, "opacity": 1, "ease": "hold"}])
    end = round(15.5 - P1_CUT, 3)
    sk = [{"t": 0, "opacity": 0}, {"t": hit, "opacity": 1, "ease": "hold"}]
    for i, v in enumerate((0.72, 1.0, 0.8, 0.97, 0.86, 0.93, 0.9)):    # a slow small flicker that dies down
        t = round(hit + 0.26 * (i + 1), 3)
        if t <= end:
            sk.append({"t": t, "opacity": v})
    seams = P.layer(E["seams"], "seams", keys=sk)
    W, H = P.meta["canvas_units"]
    cx = W / 2
    keys = [P.cam(0, cx, 845, 0.972), P.cam(end, cx - 60, 829, 1.016, ease="linear")]
    check_p1d(P, keys, f["lintel_top"])
    return P, {
        "id": PREFIX + "p1d", "at": P1_CUT, "until": 15.5,
        "in": {"kind": "cut"},
        # the whole door at 1.15x ChatGPT's px (zoom 0.972), a slow push to 1.2x (1.016) drifting toward the doorway
        "camera": keys,
        "note": "INK: The door shut (tools/storybook/sb_wire_ink.py writes this plate; edit the script, not here).",
        "layers": [P.layer(E["base"], "base"), gold, slab, P.layer(E["jamb"], "jamb"), shut, seams],
        "cues": [{"at": hit, "do": "sfx", "name": "hit", "gain": 0.8}],
    }


def check_p1d(P, keys, lintel_top, band=402, gap=40):
    """Every camera key: the lintel's top at least gap px under the picture's top edge (1080-px frame)."""
    for k in keys:
        y = 540 + (lintel_top - (k["y"] - P.shift[1])) * 0.6 * k["zoom"]
        assert y >= 540 - band + gap, f"p1d: lintel top at {y:.0f} px at t={k['t']}"
        print(f"p1d: lintel top at {y:.0f} px (t={k['t']})")


def plate_p2(picks):
    """Ember: up from the buried door through the threads of light to the town; the threads light upward as the camera rises."""
    P = Plate("p2")
    E = r6_layers(P)
    W, H = P.meta["canvas_units"]
    dx_, dy_ = P.meta["features"]["door"]
    up = lambda x, y: 1 - y / H                    # dark (first) at the bottom
    th = [{"kind": "reveal", "map": r6_map(P, E["threads"], up, "threads_map"), "t0": -1.5, "t1": 8.5, "soft": 0.12},
          {"kind": "flicker", "rate": 0.6, "amount": 0.3, "seed": 6}]
    tg = [{"kind": "reveal", "map": r6_map(P, E["threads_glow"], up, "threads_glow_map"), "t0": -1.5, "t1": 8.5, "soft": 0.12},
          {"kind": "flicker", "rate": 0.6, "amount": 0.3, "seed": 6}]
    x0 = max(dx_, 3200 / 1.12 / 2 + 40)
    return P, {
        "id": PREFIX + "p2", "at": 15.5, "until": 25.5,
        "in": {"kind": "dissolve", "dur": 1.2},
        "camera": [P.cam(0, x0, min(dy_, H - 1339 / 1.12 / 2 - 30), 1.12), P.cam(9.0, 1650, 760, 1.0, ease="inout")],
        "note": "INK: Ember (tools/storybook/sb_wire_ink.py writes this plate; edit the script, not here).",
        "layers": [P.layer(E["base"], "base"), P.layer(E["threads"], "threads", touch=th),
                   P.layer(E["threads_glow"], "threads_glow", touch=tg),
                   P.layer(E["door_glow"], "door_glow", touch=[{"kind": "flicker", "rate": 0.45, "amount": 0.3, "seed": 8}]),
                   P.layer(E["lights"], "lights", touch=[{"kind": "flicker", "rate": 6, "amount": 0.25, "seed": 7}])],
        "cues": [],
    }


def plate_p3(picks):
    """The dead get up (Storybook 4, ink_rc_build): the night frieze at 0.7 units a px (its height fits the band at
    zoom 1). Close on the crack and the rising hand (push), up to the standing dead (3.5 s), across to the spear and
    the spilled stones (7.5 s); at 11.5 s the light drains (glows only, the sky grays by the grade); at 12.5 s a hard
    cut to the dawn plate (p3d)."""
    P = Plate("p3")
    hx, hy = P3_AT["hand"]
    wx, wy = P3_AT["wound"]
    drain = lambda vals: [{"t": t, "opacity": o} for t, o in vals]
    layers = []
    for e in P.bases():
        n = e["name"]
        L = P.layer(e, n)
        if n == "dead_light":   # the lamp behind paper, breathing slowly; it goes into the ground at first light
            L["touch"] = [{"kind": "flicker", "rate": 0.35, "amount": 0.3, "seed": 21}]
            L["keys"] = drain([(0, 1), (11.5, 1), (12.4, 0.0)])
        elif n == "ember":      # the crack brightens with the frost's crack (2.0 s); drains with him
            L["touch"] = [{"kind": "flicker", "rate": 0.6, "amount": 0.16, "seed": 22}]
            L["keys"] = drain([(0, 0.55), (1.8, 0.55), (2.4, 1), (11.5, 1), (12.4, 0.1)])
        layers.append(L)
    return P, {
        "id": PREFIX + "p3", "at": 25.5, "until": 38.0,
        "in": {"kind": "ink", "dur": 1.4, "origin": [0.5, 0.55]},
        # Storybook 5: the night is shown at no more than ~1.2x its own carving (frame px per gen px = 0.933 x zoom, so
        # zoom <= 1.285; the old 1.8 open read as an enlargement). Opens on the staged wide: the crack + the dead hand
        # and the standing dead whole (the canvas's left edge sets the zoom, 1.22: x from 19), a slow push to 7.2 s,
        # then across to the spear, framed so the standing dead is fully out (left edge x >= 1270) and the right edge
        # stays on the canvas (3780).
        "camera": [P.cam(0, 1330, 660, 1.22), P.cam(3.3, 1340, 655, 1.24, ease="inout"),
                   P.cam(7.2, 1360, 645, 1.27, ease="in"),
                   P.cam(9.3, 2520, 680, 1.28, ease="out"), P.cam(12.5, 2525, 690, 1.285, ease="out")],
        "grade": [{"t": 0, "exposure": 1, "sat": 1, "tint": "#ffffff"}, {"t": 11.5, "exposure": 1, "sat": 1, "tint": "#ffffff"},
                  {"t": 12.5, "exposure": 1.1, "sat": 0.8, "tint": "#e6eaf0"}],
        "note": "INK: The dead get up (tools/storybook/sb_wire_ink.py writes this plate; edit the script, not here).",
        "layers": layers,
        "fx": [{"kind": "particles", "preset": "motes", "at": P.S(hx - 20, hy + 200), "area": [520, 160], "z": 1, "rate": 3,
                "size": [4, 8], "color": ["#ffa040e0", "#ff602000"], "seed": 23},
               {"kind": "particles", "preset": "sparks", "at": P.S(wx, wy), "area": [50, 40], "z": 1, "burst": [7.6],
                "count": 22, "dir": [0.2, 1], "speed": [40, 140], "gravity": [0, 320], "size": [3, 6], "life": 1.3, "seed": 24}],
        "cues": [],
    }


def plate_p3d(picks):
    """First light: a hard cut (wider than the night's last frame) to the dawn plate; the risen lie fallen, the
    Watchman leans on his spear; the tilt up to the gold band along the hills."""
    P = Plate("p3d")
    return P, {
        "id": PREFIX + "p3d", "at": 38.0, "until": 46.0,
        "in": {"kind": "cut"},
        # dawn2 plate (ink_dawn2.py): the Watchman's head (~107 units) under the bars' top from the cut, both dead
        # whole (the face-down one's feet ~1420; zoom 0.97 fits the band); a slow push and tilt up to the gold band.
        "camera": [P.cam(0, 2160, 745, 0.97), P.cam(1.0, 2160, 740, 0.97),
                   P.cam(7.5, 2160, 650, 1.05, ease="inout")],
        "note": "INK: First light (tools/storybook/sb_wire_ink.py writes this plate; edit the script, not here).",
        "layers": [P.layer(e, e["name"]) for e in P.bases()],
        "cues": [],
    }


P4_FLAMES = (200, 690, 1500, 1010)   # p4 canvas px: the keepers' held lamps (the only real flames on the plate)


def plate_p4(picks):
    """Keepers and lamps: the pan left to right; the willow (z 0.8) passes faster, the years-pass divider at ~4.5 s.
    The pan rises a little (y 760 -> 680, zoom 1.0) so the Watchman on the ladder (head top ~150 units), his jug and
    the post lamp sit under the bars' top with headroom from ~4.5 s to the end."""
    P = Plate("p4")
    E = r6_layers(P)
    nowisp = os.path.join(LAYERS, "p4", "_base_nowisp.png")   # ink_p4_wisp.py: the smoke over the lamp painted out
    sb5 = os.path.join(LAYERS, "p4", "_base_sb5.png")         # ink_sb5_c.py: + sky seam, water, post lamp, jug, haze
    for f in (sb5, nowisp):
        if os.path.exists(f):
            P.made["base.png"] = np.asarray(Image.open(f).convert("RGBA"))
            break
    # Storybook 5: ink_r6's flame mask also caught the bright sunset sky and the lit robes, so the flickering add layer
    # was an airbrushed haze over the whole sky (and kept the old genie lamp / teapot's shape over the post). Only the
    # keepers' held flames keep their glow (canvas px box).
    lam = np.asarray(Image.open(os.path.join(LAYERS, "p4", E["lamps"]["file"])).convert("RGBA")).copy()
    lx, ly = E["lamps"]["pos"]
    keep = np.zeros(lam.shape[:2], bool)
    bx0, by0, bx1, by1 = P4_FLAMES
    keep[max(0, int(by0 - ly)):int(by1 - ly), max(0, int(bx0 - lx)):int(bx1 - lx)] = True
    soft = nd.gaussian_filter(keep.astype(np.float32), 25)
    lam[..., 3] = (lam[..., 3] * soft).astype(np.uint8)
    P.made["lamps.png"] = lam
    return P, {
        "id": PREFIX + "p4", "at": 46.0, "until": 56.0,
        "in": {"kind": "dissolve", "dur": 1.0},
        "camera": [P.cam(0, 1700, 760, 1.0), P.cam(10.0, 4100, 680, 1.0, ease="inout")],
        "note": "INK: Keepers and lamps (tools/storybook/sb_wire_ink.py writes this plate; edit the script, not here).",
        "layers": [P.layer(E["base"], "base"),
                   P.layer(E["lamps"], "lamps", touch=[{"kind": "flicker", "rate": 6.5, "amount": 0.28, "seed": 9}]),
                   # the willow (z 0.8) keeps its sideways parallax but not the vertical: on the rise its top edge
                   # (the picture's top) dropped into view. dy = -(1/0.8 - 1) x (900 - camera y), keyed with the camera.
                   P.layer(E["willow"], "willow", keys=[{"t": 0, "dy": -47.5}, {"t": 10.0, "dy": -67.5, "ease": "inout"}])],
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


def wired():
    """(pid, plate function) for every ink plate that is wired: its function here and its layers.json built."""
    return [(pid, globals()["plate_" + pid]) for pid in PLATE_ORDER
            if "plate_" + pid in globals() and os.path.exists(os.path.join(LAYERS, pid, "layers.json"))]


def main():
    picks = json.load(open(PICKS, encoding="utf-8"))
    sb = json.load(open(SB, encoding="utf-8"))
    plates = wired()
    built = [f(picks.get(pid, {})) for pid, f in plates]
    for P, _ in built:
        copy_art(P)
    replaced = set().union(*(COVERS.get(pid, set()) for pid, _ in plates))
    new = [pl for _, pl in built]
    own = [{k: v for k, v in c.items() if k != "at"} for pl in new for c in pl["cues"]]

    keep, old_cues = [], []
    for p in sb["plates"]:
        if p["id"] in replaced or p["id"].startswith(PREFIX):
            old_cues += [dict(c, at=round(p["at"] + c["at"], 3)) for c in p.get("cues", [])
                         if {k: v for k, v in c.items() if k != "at"} not in own]     # a plate's own cues come back with it
        else:
            keep.append(p)
    for c in old_cues:
        for match, at in RETIME:
            if all(c.get(k) == v for k, v in match.items()):
                c["at"] = at
    for c in old_cues:   # each cue to the newest plate up at its absolute time, at the same absolute time
        host = max((pl for pl in new if pl["at"] <= c["at"] + 1e-6), key=lambda pl: pl["at"])
        host["cues"].append(dict(c, at=round(c["at"] - host["at"], 3)))
    for pl in new:
        pl["cues"].sort(key=lambda c: c["at"])
        for k in ("fx", "cues"):
            if not pl.get(k):
                pl.pop(k, None)
    sb["plates"] = sorted(keep + new, key=lambda pl: pl["at"])
    text = fmt(sb)
    json.loads(text)
    open(SB, "w", encoding="utf-8", newline="\n").write(text)
    print("plates:", ", ".join(f"{pl['id']} {pl['at']}-{pl['until']}" for pl in sb["plates"]))
    print("cues:", ", ".join(f"{pl['id']}+{c['at']}={pl['at'] + c['at']:.1f} {c.get('id') or c.get('name') or c['do']}"
                             for pl in new for c in pl.get("cues", [])))
    print("wrote", os.path.relpath(SB, ROOT))


if __name__ == "__main__":
    main()
