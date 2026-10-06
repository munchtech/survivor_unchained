"""Reads the legal motion check's pictures (MARKS=1; see marks_section.py for the codes) and
reports, per outfit:
- frames where any areola shows (skin within 2.2 cm of a nipple tip: her texture's pigment);
- the margin: the closest visible skin to an areola's edge in any frame, where on the rim (as
  seen in that view) and in which clip, view and frame. A negative margin means the areola shows;
- frames where the genital strip shows (the vulva's footprint, were one modelled).
Each flagged frame, and each outfit's closest frame, is saved as a crop with a banner saying
it is a test tint, not the game.
    python count.py <folder> [MIN_PX=6]
Writes <folder>/counts.csv, <folder>/summary.txt and <folder>/crops/."""
import glob
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

folder = sys.argv[1]
least = int(sys.argv[2]) if len(sys.argv) > 2 else 6
AREOLA = 2.2      # cm: her areola's pigment (texture rings, 4 Oct 2026)
NEAR = 6.0        # cm: the reach of the distance code
BANNER = 'TEST TINT for the legal check only. Not in the game. Blue = skin near a nipple; green = where a garment must cover.'


def srgb_to_linear(c):
    c = c / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def codes(im):
    a = np.asarray(im).astype(np.int32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    near = (b >= 250) & (g <= 8)
    dist = np.where(near, srgb_to_linear(r) / 0.9 * NEAR, np.inf)
    genital = (g >= 250) & (r <= 8) & (b <= 8)
    return dist, genital


def labelled(im, box, out):
    crop = im.crop(box)
    w = max(crop.width, 520)
    canvas = Image.new('RGB', (w, crop.height + 34), (20, 20, 20))
    canvas.paste(crop, (0, 34))
    d = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype('arial.ttf', 12)
    except OSError:
        font = ImageFont.load_default()
    words, line, lines = BANNER.split(), '', []
    for wd in words:
        if d.textlength(line + ' ' + wd, font=font) > w - 12 and line:
            lines.append(line)
            line = wd
        else:
            line = (line + ' ' + wd).strip()
    lines.append(line)
    for i, ln in enumerate(lines[:2]):
        d.text((6, 3 + 15 * i), ln, fill=(255, 220, 90), font=font)
    canvas.save(out)


def where(xy, landmarks):
    """Which breast and which way from it, as seen in the picture."""
    pts = {k: v for k, v in landmarks.items() if k in ('breast_l', 'breast_r')}
    if not pts:
        return 'unknown'
    side = min(pts, key=lambda k: (pts[k][0] - xy[0]) ** 2 + (pts[k][1] - xy[1]) ** 2)
    bx, by = pts[side]
    dx, dy = xy[0] - bx, xy[1] - by
    vert = 'upper' if dy < -abs(dx) * 0.4 else 'lower' if dy > abs(dx) * 0.4 else ''
    other = [k for k in pts if k != side]
    if other:
        ox = pts[other[0]][0]
        horiz = 'inner' if (ox - bx) * dx > 0 else 'outer'
    else:
        horiz = 'side'
    if abs(dx) < abs(dy) * 0.4:
        horiz = ''
    return '%s, %s edge' % ('her left breast' if side == 'breast_l' else 'her right breast', ' '.join(x for x in (vert, horiz) if x) or 'tip')


os.makedirs(os.path.join(folder, 'crops'), exist_ok=True)
rows, best = [], {}
for f in sorted(glob.glob(os.path.join(folder, '*_[0-9][0-9].png'))):
    name = os.path.basename(f)
    outfit = name.split('_')[0]
    im = Image.open(f).convert('RGB')
    dist, gen = codes(im)
    dmin = float(dist.min())
    areola_px = int((dist < AREOLA).sum())
    gen_px = int(gen.sum())
    loc = None
    lm = {}
    jp = f[:-4] + '.json'
    if os.path.exists(jp):
        raw = json.load(open(jp))
        sw, sh = raw.get('size', {}).get('xy', [im.width, im.height])
        lm = {k: [v['xy'][0] * im.width / sw, v['xy'][1] * im.height / sh] for k, v in raw.items()
              if k != 'size' and not v.get('behind')}
    if np.isfinite(dmin):
        y, x = np.unravel_index(np.argmin(dist), dist.shape)
        loc = (int(x), int(y))
    rows.append((name, areola_px, gen_px, dmin))
    if np.isfinite(dmin) and (outfit not in best or dmin < best[outfit][0]):
        best[outfit] = (dmin, name, loc, where(loc, lm))
    if areola_px >= least or gen_px >= least:
        ys, xs = np.nonzero((dist < AREOLA) | gen)
        box = (max(xs.min() - 70, 0), max(ys.min() - 70, 0), min(xs.max() + 70, im.width), min(ys.max() + 70, im.height))
        labelled(im, box, os.path.join(folder, 'crops', 'flag_' + name))

with open(os.path.join(folder, 'counts.csv'), 'w') as out:
    out.write('frame,areola_px,genital_px,closest_cm\n')
    for r in rows:
        out.write('%s,%d,%d,%s\n' % (r[0], r[1], r[2], '%.2f' % r[3] if np.isfinite(r[3]) else ''))

lines = []
for outfit in sorted({r[0].split('_')[0] for r in rows}):
    rs = [r for r in rows if r[0].startswith(outfit + '_')]
    af = [r for r in rs if r[1] >= least]
    gf = [r for r in rs if r[2] >= least]
    lines.append('%s: %d frames; areola shows in %d; genital strip shows in %d' % (outfit, len(rs), len(af), len(gf)))
    if outfit in best:
        dmin, name, loc, wh = best[outfit]
        lines.append('  closest visible skin to a nipple tip: %.2f cm, so the margin past the areola is %+.2f cm (%s), in %s'
                     % (dmin, dmin - AREOLA, wh, name))
        im = Image.open(os.path.join(folder, name)).convert('RGB')
        x, y = loc
        labelled(im, (max(x - 120, 0), max(y - 90, 0), min(x + 120, im.width), min(y + 90, im.height)),
                 os.path.join(folder, 'crops', 'closest_%s.png' % outfit))
    for r in (af + gf)[:12]:
        lines.append('  flagged: %s (areola %d px, genital %d px)' % (r[0], r[1], r[2]))
open(os.path.join(folder, 'summary.txt'), 'w').write('\n'.join(lines) + '\n')
print('\n'.join(lines))
