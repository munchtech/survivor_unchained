"""Her face's features drawn bold, for the game to deepen when her face is
small on screen. Seen from the game's camera her face is a few pixels
across, and her paint's mipmaps average her eyes, brows and lips into her
skin: a red-orange blur with no face in it. This draws them large and
soft in her head's UVs (so the mask survives its own mipmaps), for her
skin's shader to darken and redden by, the more the smaller she is
(shaders/heroine_skin.gdshader, "features").

    blender -b tools/comfy/out/heroes/heroine_built.blend --python tools/assets/heroine_features.py -- godot/art/people/head_tex

Written to <out>/heroine_features.png: red, her eyes (their lash lines
deepest) and brows, to darken; green, her lips, to deepen to their red.
Run again when her head is rebuilt (heroine_head.py).
"""
import os
import sys

import bpy
import numpy as np
from scipy import ndimage

OUT = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
SIZE = 1024

head = bpy.data.objects["HeroineHead"]
me = head.data
mw = np.array(head.matrix_world)
V = np.array([v.co[:] for v in me.vertices]) @ mw[:3, :3].T + mw[:3, 3]
me.calc_loop_triangles()
T = np.array([t.vertices[:] for t in me.loop_triangles])
L = np.array([t.loops[:] for t in me.loop_triangles])
UV = np.array([d.uv[:] for d in me.uv_layers[0].data])[L] * SIZE


def raster():
    """Every texel her faces cover: its row, column and place on her."""
    rows, cols, pts = [], [], []
    for k, t in enumerate(UV):
        x0, y0 = np.maximum(np.floor(t.min(0)).astype(int), 0)
        x1, y1 = np.minimum(np.ceil(t.max(0)).astype(int), SIZE - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        p = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
        a, b, c = t
        v0, v1, v2 = b - a, c - a, p - a
        den = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(den) < 1e-12:
            continue
        v = (v2[:, 0] * v1[1] - v1[0] * v2[:, 1]) / den
        w = (v0[0] * v2[:, 1] - v2[:, 0] * v0[1]) / den
        bb = np.stack([1 - v - w, v, w], 1)
        m = (bb > -1e-3).all(1)
        rows.append(ys.ravel()[m])
        cols.append(xs.ravel()[m])
        pts.append((V[T[k]][None] * bb[m][:, :, None]).sum(1))
        nrm.append(np.repeat(FN[k][None], m.sum(), 0))
    return np.concatenate(rows), np.concatenate(cols), np.concatenate(pts), np.concatenate(nrm)


FN = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
FN /= np.linalg.norm(FN, axis=1)[:, None] + 1e-12
FN *= np.sign((FN * (V[T].mean(1) - V.mean(0))).sum(1).mean())     # (out from her, whichever way her faces are wound)
nrm = []


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


rows, cols, P, N = raster()
# (her outside, facing forward: not the insides of her mouth and lids)
forward = N[:, 1] < -0.35
# Her paint at each texel (its 4K image, rows from the bottom as Blender has them).
img = next(n.image for n in me.materials[0].node_tree.nodes if n.type == "TEX_IMAGE" and n.image)
W, H = img.size
paint = np.array(img.pixels[:], np.float32).reshape(H, W, 4)[..., :3]
col = paint[np.clip(((rows + 0.5) / SIZE * H).astype(int), 0, H - 1), np.clip(((cols + 0.5) / SIZE * W).astype(int), 0, W - 1)]

eyes = bpy.data.objects["HeroineEyes"]
EV = np.array([(eyes.matrix_world @ v.co)[:] for v in eyes.data.vertices])
dark = np.zeros(len(P))
for sd in (1, -1):
    e = EV[EV[:, 0] * sd > 0]
    # (the middle of her eye's opening: the front of her cornea, the mean of
    # its points within 3 mm of its foremost: her front is -y)
    front = e[:, 1].min()
    c = e[e[:, 1] < front + 0.003].mean(0)
    r = 0.0
    d = P - c
    near = P[:, 1] < front + 0.012
    # her eye's opening and the lids round it, an almond 3.4 cm across and
    # 1.7 high about it, deepest along her upper lash line
    ex, ez = d[:, 0] / 0.019, (d[:, 2] - 0.001) / 0.0105
    eye = (1 - smooth((np.hypot(ex, ez) - 0.55) / 0.45)) * near
    lash = (1 - smooth(np.abs(ez - 0.45) / 0.45)) * (1 - smooth((np.abs(ex) - 0.7) / 0.4)) * near
    # her brow above it: from her paint where it is darker than the skin
    # below her brow, within the band her brows can be in, and the band itself a little
    band = (d[:, 2] > 0.008) & (d[:, 2] < 0.032) & (np.abs(d[:, 0]) < 0.03) & near
    skin = np.median(col[(d[:, 2] > -0.03) & (d[:, 2] < -0.015) & (np.abs(d[:, 0]) < 0.015) & near], 0)
    brow = band * np.clip((skin.mean() - col.mean(1)) / 0.12, 0, 1)
    dark = np.maximum(dark, np.maximum(eye * 0.75, np.maximum(lash, brow)))
    print("EYE", "lr"[sd < 0], "centre", np.round(c, 3), "radius %.4f" % r, "texels: eye %d lash %d brow %d near %d" % (
        (eye > 0.5).sum(), (lash > 0.5).sum(), (brow > 0.5).sum(), near.sum()))

# Her lips: her paint's red, in the box her mouth is in.
redness = col[:, 0] - col[:, 1]
mouth = ((np.abs(P[:, 0]) < 0.03) & (P[:, 2] < EV[:, 2].mean() - 0.045) & (P[:, 2] > EV[:, 2].mean() - 0.11)
         & (P[:, 1] < V[:, 1].min() + 0.03) & forward)
ref = np.median(redness[mouth])
lips = mouth * np.clip((redness - ref) / 0.08, 0, 1)

out = np.zeros((SIZE, SIZE, 4), np.float32)
out[rows, cols, 0] = dark
out[rows, cols, 1] = lips
out[..., 3] = 1
# Drawn bold: widened and softened, so they stay as they shrink.
inside = np.zeros((SIZE, SIZE), bool)
inside[rows, cols] = True
for k, (grow, soft) in ((0, (4, 3.0)), (1, (3, 2.0))):
    ch = ndimage.grey_dilation(out[..., k], size=(grow * 2 + 1, grow * 2 + 1))
    ch = ndimage.gaussian_filter(ch, soft)
    out[..., k] = np.clip(np.maximum(out[..., k], ch) * inside, 0, 1)
from PIL import Image  # noqa: E402
os.makedirs(OUT, exist_ok=True)
path = os.path.join(OUT, "heroine_features.png")
Image.fromarray((out[::-1] * 255 + 0.5).astype(np.uint8)).save(path)
print("FEATURES", path, "eyes and brows %d texels, lips %d" % ((out[..., 0] > 0.3).sum(), (out[..., 1] > 0.3).sum()))

# Her scalp, under her hair (green, as the shader's shadow_mask has it): the
# game darkens it to her hair's colour, so between her hair's cards there is
# hair, not her skin, and her hairline reads as hair growing (bare skin
# there read as a bald brow, and a pale scalp worst under dark hair). From
# her hairline (face_shapes.HAIRLINE, as her hair is grown) up, eased in
# from a centimetre under it over 16 mm, as hair thickens at a real hairline (a
# soft painted edge under its fine hairs, not a line where the cards begin).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import face_shapes as fs  # noqa: E402
eye_z = EV[:, 2].mean()
theta = np.arctan2(P[:, 0], -(P[:, 1] - 0.0))
rise = P[:, 2] - (eye_z + fs.hairline_height(theta))
scalp = smooth((rise + 0.010) / 0.016)
sh = np.zeros((SIZE, SIZE, 4), np.float32)
sh[rows, cols, 1] = scalp
sh[..., 3] = 1
sh[..., 1] = np.clip(ndimage.gaussian_filter(sh[..., 1], 1.5) * inside + (1 - inside) * ndimage.grey_dilation(sh[..., 1], size=(5, 5)), 0, 1)
spath = os.path.join(OUT, "heroine_shadow.png")
Image.fromarray((sh[::-1] * 255 + 0.5).astype(np.uint8)).save(spath)
print("SCALP", spath, "%d texels" % (sh[..., 1] > 0.5).sum())
if os.environ.get("FEATURES_PREVIEW"):
    # (her paint with the mask over it: darkened where red, reddened where green)
    small = np.array(Image.fromarray((np.clip(paint[::-1], 0, 1) * 255).astype(np.uint8)).resize((SIZE, SIZE)), np.float32) / 255
    m = out[::-1]
    prev = small * (1 - 0.8 * m[..., :1])
    prev[..., 0] = np.maximum(prev[..., 0], m[..., 1])
    Image.fromarray((np.clip(prev, 0, 1) * 255).astype(np.uint8)).save(os.environ["FEATURES_PREVIEW"])
