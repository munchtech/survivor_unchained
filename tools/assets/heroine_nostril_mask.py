"""Where paint may never go on her face: her nostrils, the wings of her nose
(alae) and the creases round them, found from her head's own shape.

Every paint looked almost right until it reached her nostrils (the owner, 20
October 2026): a stroke over the curl of a nose wing, or into its crease,
reads as a smudge. So the skin shader multiplies every paint's alpha by this
mask (heroine_skin.gdshader, face_paint_keep; People.HerPaint), which holds
for any paint, now or later, without drawing it again.

Found on heroine_paint.py's sheet (her face unrolled round her head): her
nose is where her face stands out of its own smoothed shape; its lower part
(the tip's height down to where it meets her lip) is the wings and the
nostrils, and the crease round each wing is the ring just outside it, where
her face turns back in. That region, grown CREASE mm past the wing's edge,
fades to nothing over FALLOFF mm more.

    python tools/assets/heroine_nostril_mask.py          # godot/art/people/paint/nostril_keep.png
    NOSE_DEBUG=<folder>: the mask over her face on the sheet, to look at

Out: godot/art/people/paint/nostril_keep.png, on her head's UV layout, grey:
white where paint may go, black where it may not. Run again when her head is
rebuilt (heroine_paint.py too).
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heroine_paint as hp  # noqa: E402

CREASE = 2.5     # mm: the mask's full strength past the wing's edge (its crease)
FALLOFF = 3.0    # mm: then fading to nothing over this
STAND = 1.6      # mm: how far out of her face's smoothed shape counts as nose


def nose_mask():
    ref, back, valid, eyes = hp.maps()
    doc, blob = hp.read_glb(hp.GLB)
    P, UV, F = hp.mesh(doc, blob, 'HeroineHead')
    xy = hp.sheet_xy(P)
    th = np.arctan2(P[:, 0], P[:, 2] - hp.Z0)
    rad = np.hypot(P[:, 0], P[:, 2] - hp.Z0)
    keep = (np.abs(th[F]).max(1) < np.radians(105)) & (P[F, 1].min(1) > hp.Y_RANGE[0] - 0.01)
    rd, drawn = hp.raster(xy, rad[:, None].astype(np.float32), F, hp.W, hp.H, depth=rad, keep=keep)
    rd = rd[..., 0]
    px = 1e-3 / hp.MM  # pixels a millimetre
    # Her face's own shape without the nose: the radius smoothed far wider than a nose.
    fill = np.where(drawn, rd, 0).astype(np.float32)
    wsum = cv2.GaussianBlur(drawn.astype(np.float32), (0, 0), 14 * px)
    smooth = cv2.GaussianBlur(fill, (0, 0), 14 * px) / np.maximum(wsum, 1e-6)
    stand = (rd - smooth) * 1000  # mm out of it
    mid = hp.MID
    eye_y = (eyes[0][1] + eyes[1][1]) / 2
    f = hp.features(ref, eyes)
    lip_top = np.nonzero(f['lips'].any(1))[0].min()
    # The nose: what stands out, between her eyes and her lip, near her middle.
    box = np.zeros(stand.shape, bool)
    box[int(eye_y):int(lip_top), int(mid - 25 * px):int(mid + 25 * px)] = True
    nose = (stand > STAND) & box & drawn
    n, lab, stats, _ = cv2.connectedComponentsWithStats(nose.astype(np.uint8))
    k = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
    nose = lab == k
    ys, xs = np.nonzero(nose)
    # Its tip: the most stood-out point; the wings and nostrils from a little above it down.
    ti = np.argmax(np.where(nose, stand, -1))
    tip_y = np.unravel_index(ti, stand.shape)[0]
    lower = nose.copy()
    lower[:int(tip_y - 4 * px)] = False
    # (the nostrils' dark openings under it, which may not stand out: the hull of the lower nose takes them)
    hull = np.zeros(stand.shape, np.uint8)
    cnts, _ = cv2.findContours(lower.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cv2.fillPoly(hull, [cv2.convexHull(np.vstack(cnts))], 1)
    # (down to where her nose meets her lip)
    hull[int(lip_top):] = 0
    grow = int(round(CREASE * px))
    m = cv2.dilate(hull, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * grow + 1, 2 * grow + 1))).astype(np.float32)
    # (the fade: distance past that edge, over FALLOFF mm, smoothstepped)
    dist = cv2.distanceTransform((m < 0.5).astype(np.uint8), cv2.DIST_L2, 5) / px
    t = np.clip(dist / FALLOFF, 0, 1)
    block = 1 - t * t * (3 - 2 * t)
    # (her lips kept: the fade reaches the top of her upper lip, and rouge belongs there)
    block *= 1 - np.clip(cv2.GaussianBlur(f['lips'].astype(np.float32), (0, 0), 0.5 * px) * 2, 0, 1)
    info = dict(tip_y=int(tip_y), eye_y=float(eye_y), lip_top=int(lip_top), width_mm=float((xs.max() - xs.min()) / px))
    return ref, back, valid, block.astype(np.float32), info


if __name__ == '__main__':
    ref, back, valid, block, info = nose_mask()
    print('nose', info)
    dbg = os.environ.get('NOSE_DEBUG')
    if dbg:
        os.makedirs(dbg, exist_ok=True)
        img = np.clip(ref, 0, 1) * (1 - 0.6 * block[..., None]) + np.array([1, 0, 1]) * 0.6 * block[..., None]
        y0, x0 = info['tip_y'] - 450, hp.MID - 450
        Image.fromarray((img[y0:y0 + 900, x0:x0 + 900] * 255).astype(np.uint8)).save(os.path.join(dbg, 'nose_sheet.png'))
        Image.fromarray((np.clip(ref, 0, 1)[y0:y0 + 900, x0:x0 + 900] * 255).astype(np.uint8)).save(os.path.join(dbg, 'nose_ref.png'))
    # On her UV layout: the block laid as a design's alpha; kept = 1 - block (outside the sheet, kept).
    L = np.zeros(block.shape + (4,), np.float32)
    L[..., 3] = block
    uv = hp.to_uv(L, back, valid)[..., 3]
    keep = np.clip(1 - uv, 0, 1)
    os.makedirs(hp.OUT, exist_ok=True)
    Image.fromarray((keep * 255 + 0.5).astype(np.uint8), 'L').save(os.path.join(hp.OUT, 'nostril_keep.png'), optimize=True)
    print('saved nostril_keep.png, blocked texels', int((keep < 0.5).sum()))
