"""The L3 / R3 stick-press caps (docs/design/LAMPS_SCREEN_BRIEF.md §16): a dark disc, a light rim, a dished inner ring and a
bold L or R, baked from pad_a.png's own disc and rim so they sit with the other caps.
python tools/uiforge/prompt_sticks.py  ->  godot/art/ui/icons/prompt/pad_l3.png, pad_r3.png (104 x 104)"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROMPT = os.path.join(ROOT, 'godot', 'art', 'ui', 'icons', 'prompt')
FONT = os.path.join(ROOT, 'godot', 'art', 'fonts', 'alegreya-sans-800.woff2')
GOLD = np.array([214, 184, 122], np.float32)


def bake(letter):
    src = np.asarray(Image.open(os.path.join(PROMPT, 'pad_a.png')).convert('RGBA')).astype(np.float32)
    h, w = src.shape[:2]
    cx, cy = (w - 1) / 2, (h - 1) / 2
    Y, X = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.hypot(X - cx, Y - cy)
    out = src.copy()
    # the face: pad_a's disc without its letter (each radius's median, so the letter's green drops out)
    inner = r < 39.5
    ri = np.round(r).astype(int)
    prof = np.zeros((60, 4), np.float32)
    for k in range(60):
        m = (ri == k) & inner
        if m.any():
            v = src[m]
            sat = v[:, :3].max(1) - v[:, :3].min(1)
            if (sat < 24).sum() > 6:
                prof[k] = np.median(v[sat < 24], 0)
            else:
                prof[k, 3] = -1                          # all letter: filled from the nearest clean radius below
    good = [k for k in range(60) if prof[k, 3] >= 0 and prof[k].any()]
    for k in range(60):
        if prof[k, 3] < 0 or not prof[k].any():
            prof[k] = prof[min(good, key=lambda g: abs(g - k))]
    face = prof[np.clip(ri, 0, 59)]
    out[inner] = face[inner]
    # the dish: a soft ring at r 27, shadowed upper-left and lit lower-right (pressed in)
    ang = np.arctan2(Y - cy, X - cx)
    light = np.cos(ang - np.pi / 4)                    # +1 lower-right, -1 upper-left
    band = np.exp(-((r - 28.5) / 1.8) ** 2)
    out[..., :3] += (band * light * 40)[..., None]
    inside = np.clip((27.5 - r) / 2.0, 0, 1)
    out[..., :3] *= (1 - 0.18 * inside * (1 - np.clip(r / 27.5, 0, 1)) - 0.06 * inside)[..., None]
    out[..., :3] = np.clip(out[..., :3], 0, 255)
    img = Image.fromarray(out.astype(np.uint8), 'RGBA')
    # the letter, bold, in the caps' gold with a dark halo
    f = ImageFont.truetype(FONT, 54)
    mask = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(mask)
    bb = d.textbbox((0, 0), letter, font=f)
    tx, ty = cx - (bb[0] + bb[2]) / 2 + 0.5, cy - (bb[1] + bb[3]) / 2 + 0.5
    d.text((tx, ty), letter, font=f, fill=255)
    halo = mask.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1.5))
    a = np.asarray(img).astype(np.float32)
    hm = np.asarray(halo, np.float32)[..., None] / 255 * 0.55
    a[..., :3] = a[..., :3] * (1 - hm) + np.array([8, 7, 10]) * hm
    lm = np.asarray(mask, np.float32)[..., None] / 255
    shade = (1.0 + 0.10 * (cy - Y) / 20)[..., None]     # a little light from above, as LB's letters have
    a[..., :3] = a[..., :3] * (1 - lm) + np.clip(GOLD * shade, 0, 255) * lm
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA').save(os.path.join(PROMPT, 'pad_%s3.png' % letter.lower()))


if __name__ == '__main__':
    for L in 'LR':
        bake(L)
    print('wrote pad_l3.png, pad_r3.png')
