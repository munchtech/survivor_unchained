"""Fit a survivor's figure to a reference picture: the silhouette's width
(front view) and depth (side view) at every height, against the body's,
with MakeHuman's shape targets as the knobs.

    blender -b <hero.blend> --python tools/assets/fit_figure.py -- <front.png> [<side.png>] [--out fitted.blend] [--show plot.png]

The reference is a figure on a plain background, standing straight; heights
are taken as fractions of the figure's own height (crown to sole), so the
picture's scale does not matter. The body's profile is measured from its
mesh, its arms left out (the reference's are out to the sides). The
targets' weights are found by coordinate descent on the squared difference
of the two profiles, from the shoulders to the ankles; the head is the
face's business, not the figure's. Age is never touched.
"""
import os
import sys

import bpy
import numpy as np
from PIL import Image
from bl_ext.user_default.mpfb.services.locationservice import LocationService
from bl_ext.user_default.mpfb.services.targetservice import TargetService

ARGS = sys.argv[sys.argv.index("--") + 1:]
FRONT = ARGS[0]
SIDE = ARGS[1] if len(ARGS) > 1 and not ARGS[1].startswith("--") else None
OUT = ARGS[ARGS.index("--out") + 1] if "--out" in ARGS else None
SHOW = ARGS[ARGS.index("--show") + 1] if "--show" in ARGS else None

BANDS = np.linspace(0.15, 0.74, 32)
CROTCH = 0.47   # below this the legs are apart: each leg's own width counts   # fraction of height from the sole: ankles to shoulders

# The knobs, each a pair of opposite targets as one signed weight.
KNOBS = [
    ("breast/BreastSize", None),
    ("torso/measure-bust-circ-decr", "torso/measure-bust-circ-incr"),
    ("torso/measure-underbust-circ-decr", "torso/measure-underbust-circ-incr"),
    ("torso/measure-waist-circ-decr", "torso/measure-waist-circ-incr"),
    ("torso/measure-hips-circ-decr", "torso/measure-hips-circ-incr"),
    ("hip/hip-scale-horiz-decr", "hip/hip-scale-horiz-incr"),
    ("hip/hip-scale-depth-decr", "hip/hip-scale-depth-incr"),
    ("buttocks/buttocks-volume-decr", "buttocks/buttocks-volume-incr"),
    ("breast/breast-volume-vert-down", "breast/breast-volume-vert-up"),
    ("breast/breast-trans-down", "breast/breast-trans-up"),
    ("legs/measure-thigh-circ-decr", "legs/measure-thigh-circ-incr"),
    ("legs/measure-calf-circ-decr", "legs/measure-calf-circ-incr"),
    ("stomach/stomach-pregnant-decr", "stomach/stomach-pregnant-incr"),
    ("torso/measure-shoulder-dist-decr", "torso/measure-shoulder-dist-incr"),
    ("torso/torso-scale-horiz-decr", "torso/torso-scale-horiz-incr"),
    ("torso/torso-scale-depth-decr", "torso/torso-scale-depth-incr"),
    ("legs/l-upperleg-scale-horiz-decr", "legs/l-upperleg-scale-horiz-incr"),
    ("legs/r-upperleg-scale-horiz-decr", "legs/r-upperleg-scale-horiz-incr"),
]
# Shape keys go past their ends: a figure more extreme than MakeHuman's
# sliders reach is still a sum of the same shapes.
LIMIT = 1.6


def silhouette(path, front=True):
    """Width of the figure (its central run, not the arms) at each band."""
    im = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
    # The backdrop row by row (studio backdrops are graded top to bottom),
    # from the picture's left and right edges.
    edges = np.concatenate([im[:, :12], im[:, -12:]], axis=1)
    bg = np.median(edges, axis=1)[:, None, :]
    mask = np.abs(im - bg).max(axis=2) > 18
    # Fill small holes in a row (a dark suit's highlight matching the backdrop).
    from scipy import ndimage
    mask = ndimage.binary_closing(mask, structure=np.ones((5, 5)))
    mask = ndimage.binary_fill_holes(mask)
    # Drop the shadow on the floor: keep the biggest blob's rows only.
    rows = np.nonzero(mask.sum(axis=1) > 2)[0]
    top, bottom = rows.min(), rows.max()
    h = bottom - top
    cx = np.median(np.nonzero(mask[top + int(h * 0.5)])[0])
    out = []
    for b in BANDS:
        y = int(bottom - b * h)
        row = mask[y]
        # The run of figure containing (or nearest) the middle, both legs counted together.
        xs = np.nonzero(row)[0]
        if len(xs) == 0:
            out.append(0)
            continue
        # Split into runs; keep those within 0.3 h of the centre (not the arms).
        runs, start = [], xs[0]
        for a, c in zip(xs[:-1], xs[1:]):
            if c != a + 1:
                runs.append((start, a)); start = c
        runs.append((start, xs[-1]))
        near = [(s, e) for s, e in runs if abs((s + e) / 2 - cx) < 0.22 * h]
        if not near:
            out.append(0)
            continue
        if front and b < CROTCH and len(near) >= 2:
            # Two legs: the mean of their own widths.
            out.append(np.mean([e - s for s, e in near[:2]]) / h)
        elif front and b < CROTCH:
            # Thighs that touch read as one run: half of it is a leg.
            out.append((max(e for _, e in near) - min(s for s, _ in near)) / h / 2)
        else:
            out.append((max(e for _, e in near) - min(s for s, _ in near)) / h)
    return np.array(out)


body = next(o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("hero_") and "." not in o.name)
ARMS = {n for n in [g.name for g in body.vertex_groups] if any(k in n for k in ("upperarm", "lowerarm", "hand", "index", "middle", "ring", "pinky", "thumb"))}
HELP = {body.vertex_groups[n].index for n in ("HelperGeometry", "JointCubes") if n in body.vertex_groups}
arm_idx = {body.vertex_groups[n].index for n in ARMS}
keep = np.array([not any((g.group in arm_idx and g.weight > 0.2) or (g.group in HELP and g.weight > 0.5) for g in v.groups) for v in body.data.vertices])

tdir = os.path.join(LocationService.get_mpfb_data(), "targets")
# Measured with every vertex present and in the rest pose: no mask, no rig.
for mod in body.modifiers:
    mod.show_viewport = False


def coords():
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg)
    me = ev.to_mesh()
    c = np.array([v.co[:] for v in me.vertices])
    ev.to_mesh_clear()
    return c


def ensure(rel):
    name = os.path.basename(rel)
    if not body.data.shape_keys or name not in body.data.shape_keys.key_blocks:
        p = os.path.join(tdir, rel + ".target.gz")
        if not os.path.exists(p):
            return None
        TargetService.load_target(body, p, weight=0.0)
    return body.data.shape_keys.key_blocks[name]


# The knobs as shape keys, and each one's full effect on every vertex.
base = coords()
knobs = []
for dec, inc in KNOBS:
    if inc is None:
        continue
    kd, ki = ensure(dec), ensure(inc)
    if kd is None or ki is None:
        print("NO KNOB", dec, inc)
        continue
    w0 = ki.value - kd.value
    knobs.append((kd, ki, w0))

# Each knob's full effect, measured from the body with every knob at zero:
# a knob already partly applied would otherwise look nearly spent.
for kd, ki, _ in knobs:
    kd.value = ki.value = 0.0
base = coords()
deltas = []
for kd, ki, w0 in knobs:
    ki.value = 1.0
    up = coords() - base
    ki.value = 0.0
    kd.value = 1.0
    down = coords() - base
    kd.value = 0.0
    deltas.append((up, down, w0))


def profile(c, axis):
    m = c[keep]
    z = m[:, 2]
    lo, hi = z.min(), c[:, 2].max()
    h = hi - lo
    out = []
    for b in BANDS:
        zz = lo + b * h
        s = m[np.abs(z - zz) < h * 0.008]
        if not len(s):
            out.append(0)
        elif axis == 0 and b < CROTCH:
            legs = [s[s[:, 0] > 0], s[s[:, 0] < 0]]
            out.append(np.mean([(l[:, 0].max() - l[:, 0].min()) for l in legs if len(l)]) / h)
        else:
            out.append((s[:, axis].max() - s[:, axis].min()) / h)
    return np.array(out)


def shape(ws):
    c = base.copy()
    for (u, d, _), w in zip(deltas, ws):
        c += u * w if w > 0 else d * -w
    return c


ref_f = silhouette(FRONT)
ref_s = silhouette(SIDE, front=False) if SIDE else None


# A band wider than any torso is the arms (pictures put them at different
# heights): it says nothing about the figure.
ok_f = (ref_f > 0.01) & (ref_f < 0.27)
ok_s = (ref_s > 0.01) if ref_s is not None else None


def err(ws):
    c = shape(ws)
    e = (((profile(c, 0) - ref_f) ** 2) * ok_f).sum()
    if ref_s is not None:
        e += (((profile(c, 1) - ref_s) ** 2) * ok_s).sum()
    return e


ws = np.array([w0 for _, _, w0 in deltas])
best = err(ws)
print("START", best)
for step in (0.4, 0.2, 0.1, 0.05):
    improved = True
    while improved:
        improved = False
        for i in range(len(ws)):
            for d in (step, -step):
                t = ws.copy()
                t[i] = float(np.clip(t[i] + d, -LIMIT, LIMIT))
                e = err(t)
                if e < best - 1e-7:
                    ws, best, improved = t, e, True
    print("STEP", step, best)

for (kd, ki, _), w in zip(knobs, ws):
    kd.slider_max = ki.slider_max = LIMIT
    kd.value, ki.value = max(0.0, -w), max(0.0, w)
    print(f"KNOB {ki.name.replace('-incr', ''):40s} {w:+.2f}")
print("END", best)

if SHOW:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    c = shape(ws)
    fig, ax = plt.subplots(1, 2 if ref_s is not None else 1, figsize=(8, 6), squeeze=False)
    ax[0][0].plot(ref_f, BANDS, "k", label="reference"); ax[0][0].plot(profile(base, 0), BANDS, "r:", label="before"); ax[0][0].plot(profile(c, 0), BANDS, "b", label="fitted"); ax[0][0].set_title("front width"); ax[0][0].legend()
    if ref_s is not None:
        ax[0][1].plot(ref_s, BANDS, "k"); ax[0][1].plot(profile(base, 1), BANDS, "r:"); ax[0][1].plot(profile(c, 1), BANDS, "b"); ax[0][1].set_title("side depth")
    fig.savefig(SHOW)
if OUT:
    for mod in body.modifiers:
        mod.show_viewport = True
    bpy.ops.wm.save_as_mainfile(filepath=OUT)
