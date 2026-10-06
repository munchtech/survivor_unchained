"""The lamp on build2's Self (a 900 px panel at the right over the live world): its bracket's
plate nailed to the panel's left frame near the top, the cage hanging out over the world; its
warmth on the panel's left edge and out toward her. Normal and lit, at 1:1."""
import os
import sys

import numpy as np
from PIL import Image

WT = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748'
S = os.path.dirname(os.path.abspath(__file__))
L = os.path.join(WT, 'tools', 'comfy', 'out', 'uiforge', 'lamp', 'lamp')
plate_x = float(sys.argv[1]) if len(sys.argv) > 1 else 1010     # the panel's left frame
top = float(sys.argv[2]) if len(sys.argv) > 2 else 26
gain0 = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
LW, LH, PLATE, COAL = 220, 180, 186.5, 122.8                     # the sprite, shown px


def ld(p, size=None):
    im = Image.open(p).convert('RGBA')
    if size:
        im = im.resize(size, Image.LANCZOS)
    return np.asarray(im, np.float32) / 255


bg = np.asarray(Image.open(os.path.join(S, 'b2_self.jpg')).convert('RGB'), np.float32) / 255
light = ld(os.path.join(L, 'light.png'), (600, 600))
lx = plate_x - PLATE
cx, coal_y = lx + 110, top + COAL
for name, lit in (('normal', False), ('lit', True)):
    img = bg.copy()
    lamp = ld(os.path.join(L, 'lamp_lit.png' if lit else 'lamp.png'), (LW, LH))
    gain = gain0 * (1.6 if lit else 1.0)
    x0, y0 = int(cx - 300), int(coal_y - 300)
    H, W = img.shape[:2]
    a0, b0 = max(0, x0), max(0, y0)
    a1, b1 = min(W, x0 + 600), min(H, y0 + 600)
    part = light[b0 - y0:b1 - y0, a0 - x0:a1 - x0]
    img[b0:b1, a0:a1] = np.clip(img[b0:b1, a0:a1] + part[..., :3] * part[..., 3:4] * gain, 0, 1)
    ix, iy = int(lx), int(top)
    a = lamp[..., 3:4]
    img[iy:iy + LH, ix:ix + LW] = img[iy:iy + LH, ix:ix + LW] * (1 - a) + lamp[..., :3] * a
    out = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    out.save(os.path.join(S, f'lamp_b2_{name}.png'))
    out.crop((560, 0, 1360, 560)).save(os.path.join(S, f'lamp_b2_{name}_crop.png'))
print('ok', lx, cx)
