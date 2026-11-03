"""Type at 1x with PIL/FreeType (hinted, as Godot draws it): fonts, letterspacing, halos, wrapping."""
import os
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import draw as D

FONTS = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\ui-25\godot\art\fonts'


@lru_cache(None)
def font(name, size):
    """name: cinzel-600, alegreya-700, alegreya-400-italic, alegreya-sans-800 ..."""
    return ImageFont.truetype(os.path.join(FONTS, name + '.woff2'), size)


def width(s, f, track=0.0):
    """advance width in px; track in em"""
    if not track:
        return f.getlength(s)
    return sum(f.getlength(c) for c in s) + track * f.size * max(len(s) - 1, 0)


def mask(s, f, track=0.0, pad=8):
    """the text's coverage on a 1x canvas; returns (mask float, ox, oy) where (ox, oy) is the baseline origin in it"""
    w = int(np.ceil(width(s, f, track))) + 2 * pad
    asc, desc = f.getmetrics()
    h = asc + desc + 2 * pad
    im = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(im)
    x, y = pad, pad + asc
    if not track:
        d.text((x, y), s, font=f, fill=255, anchor='ls')
    else:
        for c in s:
            d.text((x, y), c, font=f, fill=255, anchor='ls')
            x += f.getlength(c) + track * f.size
    return np.asarray(im, np.float32) / 255, pad, pad + asc


def draw(L, x, y, s, f, color, alpha=1.0, track=0.0, align='left', halo=None):
    """text with its baseline at y. align left|center|right about x. halo = (radius px, alpha, rgb)"""
    if not s:
        return 0
    m, ox, oy = mask(s, f, track)
    tw = width(s, f, track)
    x0 = x - (tw / 2 if align == 'center' else tw if align == 'right' else 0)
    X0, Y0 = int(round(x0)) - ox, int(round(y)) - oy
    if halo:
        r, ha, hc = halo
        pad = int(r * 2.5)
        mm = np.pad(m, pad)
        g = D.gauss(cv2_dilate(mm, max(1, int(r / 3))), r / 2.0)
        g = np.clip(g * 1.6, 0, 1) * ha
        p = np.zeros(g.shape + (4,), np.float32)
        p[..., :3] = g[..., None] * np.asarray(hc, np.float32)
        p[..., 3] = g
        D.stamp(L, X0 - pad, Y0 - pad, p)
    p = np.zeros(m.shape + (4,), np.float32)
    c = m * alpha
    p[..., :3] = c[..., None] * np.asarray(color, np.float32)
    p[..., 3] = c
    D.stamp(L, X0, Y0, p)
    return tw


def cv2_dilate(m, r):
    import cv2
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    return cv2.dilate(m, k)


def wrap(s, f, maxw, track=0.0):
    words, lines, cur = s.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if width(t, f, track) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def ellipsize(s, f, maxw):
    if width(s, f) <= maxw:
        return s
    while s and width(s + '\u2026', f) > maxw:
        s = s[:-1].rstrip()
    return s + '\u2026'
