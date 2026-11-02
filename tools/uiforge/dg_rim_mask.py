"""hud24 r2: the rim sources for the two statues (her figure, the keeper).

The gold rim of a faded statue is taken from these, not from the art's own alpha:
  art/ui/lamp_life/drowned/lamp_rim.png   (the size of lamp_cold.png)
  art/ui/dg_keeper/keeper_rim.png         (the size of keeper.png)
Straight RGBA. A = the art's alpha with every enclosed hole smaller than 600 screen px2 filled (so a pinhole or a
gap in a lock of hair draws no rim of its own). R = where a rim may be drawn: 0 within 12 screen px of the bar's
frame (the panel's alpha on the 1080 screen, dilated 12 px, mapped back into the art), rising to 1 by 18 px, so the
rim does not run along the frame. The body alpha is the art's own (the shaders only read these for the rim).
Run from the repo root after dg_keeper_hud.py:  python tools/uiforge/dg_rim_mask.py
"""
import os
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

UI = os.path.join('godot', 'art', 'ui')
HOLE_PX2 = 600.0      # screen px2
NEAR, RAMP = 12.0, 18.0
PANEL_RECT = (576.0, 988.0, 768.0, 92.0)       # hud_a_geo.json panel.rect
KEEPER_RECT = (1254.0, 873.0, 341.0, 207.0)    # keeper.rect (the art is 2x)
LAMP_AT, LAMP_ANCHOR, LAMP_SCALE, LAMP_CANVAS = (295.33, 822.0), (295.33, 1080.0), 0.94, (474.67, 258.0)


def panel_distance():
    """Distance (screen px) from the panel's alpha > 0.5, on the 1080 screen (1 px grid)."""
    p = Image.open(os.path.join(UI, 'dg_panel', 'panel.png')).convert('RGBA')
    x, y, w, h = PANEL_RECT
    a = np.asarray(p.resize((int(round(w)), int(round(h))), Image.LANCZOS))[..., 3] > 127
    scr = np.zeros((1080, 1920), bool)
    scr[int(y):int(y) + a.shape[0], int(x):int(x) + a.shape[1]] = a
    return ndi.distance_transform_edt(~scr)


def fill_small_holes(a, max_texels):
    solid = a > 0.5
    lab, n = ndi.label(~solid)
    if n == 0:
        return a
    sizes = ndi.sum(np.ones_like(lab), lab, index=np.arange(1, n + 1))
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])).tolist())
    out = a.copy()
    filled = 0
    for i in range(1, n + 1):
        if i not in edge and sizes[i - 1] < max_texels:
            out[lab == i] = 1.0
            filled += 1
    print('  holes filled:', filled, 'of', n, 'regions')
    return out


def bake(name, src, dst, origin, screen_per_texel, dist):
    im = Image.open(os.path.join(UI, src)).convert('RGBA')
    arr = np.asarray(im).astype(np.float32) / 255.0
    h, w = arr.shape[:2]
    a = fill_small_holes(arr[..., 3], HOLE_PX2 / screen_per_texel ** 2)
    ys, xs = np.mgrid[0:h, 0:w]
    sx = np.clip(((origin[0] + (xs + 0.5) * screen_per_texel)).astype(int), 0, 1919)
    sy = np.clip(((origin[1] + (ys + 0.5) * screen_per_texel)).astype(int), 0, 1079)
    d = dist[sy, sx]
    allowed = np.clip((d - NEAR) / (RAMP - NEAR), 0.0, 1.0)
    allowed = np.where(d <= NEAR, 0.0, allowed)
    out = np.dstack([allowed, allowed, allowed, a])
    Image.fromarray((out * 255 + 0.5).astype(np.uint8), 'RGBA').save(os.path.join(UI, dst))
    print(name, dst, (w, h), 'rim-blocked texels:', int((allowed < 1).sum()), 'alpha filled texels:', int(((a > 0.5) & ~(arr[..., 3] > 0.5)).sum()))


def main():
    dist = panel_distance()
    lx = LAMP_ANCHOR[0] + (LAMP_AT[0] - LAMP_ANCHOR[0]) * LAMP_SCALE
    ly = LAMP_ANCHOR[1] + (LAMP_AT[1] - LAMP_ANCHOR[1]) * LAMP_SCALE
    bake('lamp', 'lamp_life/drowned/lamp_cold.png', 'lamp_life/drowned/lamp_rim.png', (lx, ly), LAMP_CANVAS[0] * LAMP_SCALE / 949.0, dist)
    bake('keeper', 'dg_keeper/keeper.png', 'dg_keeper/keeper_rim.png', (KEEPER_RECT[0], KEEPER_RECT[1]), 0.5, dist)


if __name__ == '__main__':
    main()
