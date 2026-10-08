"""Reads the legal motion check's pictures (MARKS=1; see marks_section.py for the codes) and
reports, per outfit:
- frames where any areola shows (skin within 2.2 cm of an areola's centre, as her paint has it);
- the margin: the closest visible skin to an areola's edge, for each breast and for each edge
  of its rim (upper, upper inner, inner and so on, as seen in that view, from the posed tip),
  with the clip, view and frame. A negative margin means the areola shows;
- frames where the genital strip shows (the vulva's footprint, were one modelled);
- frames where tucked skin (pushed in under a garment) comes into view, a dent or a gap: past
  half its tuck anywhere, or any tuck within 6 cm of a nipple. The edge ring (a third of a
  tuck, where a garment's edge meets her) is counted apart, as it may show by design.
Each flagged frame, and each breast's closest frame, is saved as a crop with a banner saying
it is a test tint, not the game, and a ring on the closest pixel.
    python count.py <folder> [MIN_PX=6]
Writes <folder>/counts.csv, <folder>/summary.txt and <folder>/crops/."""
import glob
import json
import math
import os
import sys

import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

folder = sys.argv[1]
least = int(sys.argv[2]) if len(sys.argv) > 2 else 6
AREOLA = 2.2      # cm: her areola's pigment (texture rings, 4 Oct 2026)
NEAR = 6.0        # cm: the reach of the distance code
BANNER = ('TEST TINT for the legal check only. Not in the game. Blue to pink = skin within 6 cm '
          'of a nipple (pinker is further); green = where a garment must cover; cyan = skin '
          'tucked under a garment.')
EDGES = ['inner', 'upper inner', 'upper', 'upper outer', 'outer', 'lower outer', 'lower', 'lower inner']
SIDES = {'breast_l': 'her left breast', 'breast_r': 'her right breast'}


def srgb_to_linear(c):
    c = c / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def codes(im):
    """The codes, read exactly (unlit, linear tonemapper; see marks_section.py)."""
    a = np.asarray(im).astype(np.int32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    tucked_near = (b >= 250) & (g >= 182) & (g <= 194)
    near = (b >= 250) & ((g <= 8) | tucked_near)
    dist = np.where(near, srgb_to_linear(r) / 0.9 * NEAR, np.inf)
    # A lone pixel reading her very tip (red under 30: within 0.8 mm of the areola's centre)
    # with no neighbour within 5 mm of it is a render artefact (a silhouette sample shaded
    # with values carried past its triangle), not skin: skin that near the tip is seen as a
    # patch, its neighbours a pixel's width (about a millimetre) further out.
    ring = np.ones((3, 3), bool)
    ring[1, 1] = False
    lone = near & (r < 30) & (ndimage.minimum_filter(dist, footprint=ring, mode='constant', cval=np.inf) > 0.5)
    near &= ~lone
    tucked_near &= ~lone
    dist[lone] = np.inf
    genital = (g >= 250) & (r <= 8) & (b <= 8)
    tucked = (g >= 250) & (b >= 250)
    depth = np.where(tucked, 1.0 - srgb_to_linear(r) / 0.9, 0.0)  # (a clipped white reads below 0)
    return dist, genital, tucked_near, depth


def labelled(im, box, out, ring=None):
    """A crop with the banner above it (the owner once took the test tint for the game)."""
    crop = im.crop(box)
    k = max(1, min(3, 480 // max(crop.width, 1)))  # small crops enlarged, pixel for pixel
    crop = crop.resize((crop.width * k, crop.height * k), Image.NEAREST)
    if ring is not None:
        ring = (box[0] + (ring[0] - box[0]) * k, box[1] + (ring[1] - box[1]) * k)
    w = max(crop.width, 560)
    try:
        font = ImageFont.truetype('arial.ttf', 12)
    except OSError:
        font = ImageFont.load_default()
    measure = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    words, line, lines = BANNER.split(), '', []
    for wd in words:
        if measure.textlength(line + ' ' + wd, font=font) > w - 12 and line:
            lines.append(line)
            line = wd
        else:
            line = (line + ' ' + wd).strip()
    lines.append(line)
    top = 6 + 15 * len(lines)
    canvas = Image.new('RGB', (w, crop.height + top), (20, 20, 20))
    canvas.paste(crop, (0, top))
    d = ImageDraw.Draw(canvas)
    if ring is not None:
        x, y = ring[0] - box[0], ring[1] - box[1] + top
        d.ellipse((x - 7, y - 7, x + 7, y + 7), outline=(255, 220, 90))
    for i, ln in enumerate(lines):
        d.text((6, 3 + 15 * i), ln, fill=(255, 220, 90), font=font)
    canvas.save(out)


def landmarks(path, im):
    """Tips (posed, with their 2 cm up and in) and breast bones, in this picture's pixels."""
    if not os.path.exists(path):
        return {}, {}
    raw = json.load(open(path))
    sw, sh = raw.get('size', {}).get('xy', [im.width, im.height])
    sx, sy = im.width / sw, im.height / sh
    tips, bones = {}, {}
    for k, v in raw.items():
        if k == 'size' or v.get('behind'):
            continue
        p = (v['xy'][0] * sx, v['xy'][1] * sy)
        if k.startswith('tip_'):
            tips[k[4:]] = (p, (v['up'][0] * sx, v['up'][1] * sy), (v['inner'][0] * sx, v['inner'][1] * sy))
        else:
            bones[k] = p
    return tips, bones


def place(xs, ys, tips, bones):
    """For pixels (xs, ys): which breast (the nearest posed tip on screen) and which edge of
    its rim, from the offset expressed in that tip's own up and inner directions on screen."""
    side = np.full(xs.shape, '', dtype=object)
    edge = np.full(xs.shape, '', dtype=object)
    if tips:
        names = list(tips)
        d2 = np.stack([(xs - tips[n][0][0]) ** 2 + (ys - tips[n][0][1]) ** 2 for n in names])
        pick = np.argmin(d2, axis=0)
        for i, n in enumerate(names):
            m = pick == i
            (tx, ty), (ux, uy), (ix, iy) = tips[n]
            u = np.array([ux - tx, uy - ty])
            v = np.array([ix - tx, iy - ty])
            det = u[0] * v[1] - u[1] * v[0]
            dx, dy = xs[m] - tx, ys[m] - ty
            if abs(det) > 0.15 * np.linalg.norm(u) * np.linalg.norm(v) + 1e-6:
                a = (dx * v[1] - dy * v[0]) / det      # along up
                b = (u[0] * dy - u[1] * dx) / det      # along in
            else:  # seen edge on: only the longer direction can be read
                if np.linalg.norm(u) >= np.linalg.norm(v):
                    a, b = (dx * u[0] + dy * u[1]) / (u @ u + 1e-9), np.zeros_like(dx, dtype=float)
                else:
                    a, b = np.zeros_like(dx, dtype=float), (dx * v[0] + dy * v[1]) / (v @ v + 1e-9)
            ang = np.degrees(np.arctan2(a, b)) % 360.0
            side[m] = n
            edge[m] = [EDGES[int(((t + 22.5) % 360) // 45)] for t in ang]
    elif bones:
        names = list(bones)
        d2 = np.stack([(xs - bones[n][0]) ** 2 + (ys - bones[n][1]) ** 2 for n in names])
        pick = np.argmin(d2, axis=0)
        for i, n in enumerate(names):
            side[pick == i] = n
            edge[pick == i] = 'edge unknown (no posed tip)'
    return side, edge


os.makedirs(os.path.join(folder, 'crops'), exist_ok=True)
rows = []
dents = {}  # outfit: [(px, frame name, (x, y))], each frame's largest patch of deep-tucked skin
# best[outfit][(side, edge)] = (cm, frame name, (x, y)); edge '' is the breast's closest of all
best = {}
for f in sorted(glob.glob(os.path.join(folder, '*_[0-9][0-9].png'))):
    name = os.path.basename(f)
    outfit = name.split('_')[0]
    im = Image.open(f).convert('RGB')
    dist, gen, tnear, depth = codes(im)
    tips, bones = landmarks(f[:-4] + '.json', im)
    areola_px = int((dist < AREOLA).sum())
    gen_px = int(gen.sum())
    deep_px = int((depth > 0.5).sum()) + int(tnear.sum())
    ring_px = int(((depth > 0.02) & (depth <= 0.5)).sum())
    ys, xs = np.nonzero(np.isfinite(dist))
    dmin = float(dist.min()) if xs.size else math.inf
    per = {}
    if xs.size:
        ds = dist[ys, xs]
        side, edge = place(xs.astype(float), ys.astype(float), tips, bones)
        ob = best.setdefault(outfit, {})
        for s in set(side):
            for e in [''] + sorted(set(edge[side == s])):
                m = (side == s) & ((edge == e) if e else True)
                k = int(np.argmin(np.where(m, ds, np.inf)))
                key = (s, e)
                if not e:
                    per[s] = ds[k]
                if key not in ob or ds[k] < ob[key][0]:
                    ob[key] = (float(ds[k]), name, (int(xs[k]), int(ys[k])))
    rows.append((name, areola_px, gen_px, deep_px, ring_px, dmin, per.get('breast_l', math.inf), per.get('breast_r', math.inf)))
    deep = (depth > 0.5) | tnear
    if deep.sum() >= least:
        lab, n = ndimage.label(deep)
        sizes = ndimage.sum(deep, lab, range(1, n + 1))
        k = int(np.argmax(sizes)) + 1
        cy, cx = ndimage.center_of_mass(deep, lab, k)
        dents.setdefault(outfit, []).append((int(sizes[k - 1]), name, (int(cx), int(cy))))
    if areola_px >= least or gen_px >= least or deep_px >= least:
        fy, fx = np.nonzero((dist < AREOLA) | gen | (depth > 0.5) | tnear)
        box = (max(fx.min() - 70, 0), max(fy.min() - 70, 0), min(fx.max() + 70, im.width), min(fy.max() + 70, im.height))
        labelled(im, box, os.path.join(folder, 'crops', 'flag_' + name))


def cm(v):
    return '%.2f' % v if np.isfinite(v) else ''


with open(os.path.join(folder, 'counts.csv'), 'w') as out:
    out.write('frame,areola_px,genital_px,tucked_seen_px,edge_ring_px,closest_cm,closest_left_cm,closest_right_cm\n')
    for r in rows:
        out.write('%s,%d,%d,%d,%d,%s,%s,%s\n' % (r[0], r[1], r[2], r[3], r[4], cm(r[5]), cm(r[6]), cm(r[7])))


def margin(v):
    return '%+.2f cm' % (v - AREOLA)


lines = ['Margins are past the areola\'s edge (2.2 cm from its centre): negative means the areola shows.',
         'Edges are as seen in that view, from the posed tip: "inner" is towards her midline.',
         'No near skin in view at all means every margin is past %.1f cm.' % (NEAR - AREOLA), '']
for outfit in sorted({r[0].split('_')[0] for r in rows}):
    rs = [r for r in rows if r[0].startswith(outfit + '_')]
    af = [r for r in rs if r[1] >= least]
    gf = [r for r in rs if r[2] >= least]
    tf = [r for r in rs if r[3] >= least]
    lines.append('%s: %d frames; areola shows in %d; genital strip shows in %d; tucked skin seen in %d '
                 '(the edge ring in %d)' % (outfit, len(rs), len(af), len(gf), len(tf),
                                            sum(1 for r in rs if r[4] >= least)))
    ob = best.get(outfit, {})
    for s in ('breast_l', 'breast_r'):
        if (s, '') not in ob:
            lines.append('  %s: no skin within %.0f cm of the tip in view in any frame' % (SIDES[s], NEAR))
            continue
        v, nm, loc = ob[(s, '')]
        edge = next((e for (s2, e), (v2, n2, l2) in ob.items() if s2 == s and e and n2 == nm and l2 == loc), '')
        lines.append('  %s: closest %s (%s edge), in %s' % (SIDES[s], margin(v), edge or '?', nm))
        im = Image.open(os.path.join(folder, nm)).convert('RGB')
        x, y = loc
        labelled(im, (max(x - 120, 0), max(y - 90, 0), min(x + 120, im.width), min(y + 90, im.height)),
                 os.path.join(folder, 'crops', 'closest_%s_%s.png' % (outfit, s)), ring=loc)
        for e in EDGES:
            if (s, e) in ob:
                v, nm, _ = ob[(s, e)]
                lines.append('      %-12s %s  in %s' % (e, margin(v), nm))
    for i, (px, nm, loc) in enumerate(sorted(dents.get(outfit, []), reverse=True)[:6]):
        lines.append('  tucked skin in view: %d px around (%d, %d) in %s (crop tuck_%s_%d.png)' % (px, loc[0], loc[1], nm, outfit, i))
        im = Image.open(os.path.join(folder, nm)).convert('RGB')
        x, y = loc
        labelled(im, (max(x - 120, 0), max(y - 90, 0), min(x + 120, im.width), min(y + 90, im.height)),
                 os.path.join(folder, 'crops', 'tuck_%s_%d.png' % (outfit, i)), ring=loc)
    for r in [r for r in rs if r in af or r in gf][:16]:
        lines.append('  flagged: %s (areola %d px, genital %d px, tucked %d px)' % (r[0], r[1], r[2], r[3]))
open(os.path.join(folder, 'summary.txt'), 'w').write('\n'.join(lines) + '\n')
print('\n'.join(lines))
