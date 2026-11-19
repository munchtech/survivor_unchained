#!/usr/bin/env python3
"""Look spec, frozen 19 Nov 2026 from the owner's night/day reference: score a game frame against it.

  python tools/look/look_spec.py FRAME.png --panel day|night [--regions R.json] [--marks MASK.png] [--debug OUT.png] [--json OUT.json]
  python tools/look/look_spec.py --ref day|night      # a reference panel scored against the frozen spec (self-check)
  python tools/look/look_spec.py --freeze [--force]   # ONE TIME (done 19 Nov): measure the ref, write look_spec_ref19nov.json

Doc: docs/design/look_spec_ref_19nov.md. Every pixel constant is defined at 1080p and scaled by s = H/1080, so the ref (887 px
panels) and 1080p frames are measured the same way. Regions are hand-placed boxes: look_spec_regions_ref.json (the ref) and
look_spec_regions_verge.json (default for 1920x1080 frames: the fixed-camera Verge judge shots vdayN / vnightN).
--marks takes the game's `--ink-dbg marks` frame (magenta = + marks, cyan = - marks) instead of detecting marks.
"""
import argparse, json, os, sys
import numpy as np, cv2
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
REF = 'C:/Users/munch/Desktop/survivorsunchained_inputs/scratch_coord15/owner_frames/owner_ref_night_day_colors_19nov.webp'
SPEC = os.path.join(HERE, 'look_spec_ref19nov.json')
REF_REG = os.path.join(HERE, 'look_spec_regions_ref.json')
VERGE_REG = os.path.join(HERE, 'look_spec_regions_verge.json')
PANELS = {'night': (0, 880), 'day': (890, 1774)}          # columns of the 1774x887 ref (white gutter 882-889)
MATS = ('ground', 'path', 'stones', 'bark', 'crowns')
FAM = (('red', 350, 40), ('orange', 40, 68), ('gold', 68, 120), ('green', 120, 165), ('teal', 165, 235),
       ('blue', 235, 280), ('violet', 280, 318), ('magenta', 318, 350))   # Oklab hue degrees; neutral = C < .04
NEUTRAL_C = 0.04
# object classes: (hue lo, hue hi, C min, L lo, L hi), on pixels (not ink); the panel's saturated accents
OBJ = {'day': {'leaf_red': (350, 40, .15, 0, 1), 'leaf_orange': (40, 68, .15, 0, 1), 'gold': (68, 100, .13, .55, 1),
               'moss': (100, 135, .06, .3, .85)},
       'night': {'glow': (0, 360, 0, .82, 1.01), 'teal': (165, 235, .09, 0, .82), 'blue_leaf': (235, 280, .14, 0, .82),
                 'violet': (280, 318, .12, 0, .82), 'magenta': (318, 350, .12, 0, .82)}}
INK_L, INK_BH = 0.22, 0.08      # ink = dark (L < .22) AND darker than its closing by > .08 (thin dark line)
MARK_DL, MARK_DC = 0.05, 0.05   # mark = |L - field L| >= .05 or |ab - field ab| >= .05 (Oklab), away from ink
EDGE_DE = 0.12                  # strong colour edge: field dE across 2r px >= .12
HUE_C = 0.04                    # hue deviation only where mark and field C >= .04


def oklab(rgb):
    lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566],
                   [0.0883024619, 0.2817188376, 0.6299787005]], np.float32)
    M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099],
                   [0.0259040371, 0.7827717662, -0.8086757660]], np.float32)
    return (np.cbrt(np.clip(lin @ M1.T, 0, None)) @ M2.T).astype(np.float32)


def hue(a, b): return np.degrees(np.arctan2(b, a)) % 360
def odd(x): return max(3, int(round(x)) | 1)
def inh(h, lo, hi): return ((h >= lo) | (h < hi)) if lo > hi else ((h >= lo) & (h < hi))


def cmean(h, w=None):
    if h.size == 0: return None
    r = np.radians(h); w = np.ones_like(r) if w is None else w
    return float(np.degrees(np.arctan2((np.sin(r) * w).sum(), (np.cos(r) * w).sum())) % 360)


def pct(x, q): return float(np.percentile(x, q)) if x.size >= 20 else None


def load_frame(path, panel=None):
    im = np.asarray(Image.open(path).convert('RGB')).astype(np.float32) / 255
    if panel: c0, c1 = PANELS[panel]; im = im[:, c0:c1]
    return np.ascontiguousarray(im)


def maps(rgb, marks_img=None):
    """Per-pixel maps, computed once per frame; every metric is then read inside a mask (whole, crop or box)."""
    H, W = rgb.shape[:2]; s = H / 1080.0
    lab = oklab(rgb); L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    se = lambda k: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    bh = cv2.morphologyEx(L, cv2.MORPH_CLOSE, se(odd(11 * s))) - L
    ink = (L < INK_L) & (bh > INK_BH)
    near = cv2.dilate(ink.astype(np.uint8), se(odd(1 + 4 * s))) > 0
    # de-inked image (ink pixels inpainted), then the flat field = median over a 27 px (1080p) window
    q = np.stack([L * 255, (a + .5) * 255, (b + .5) * 255], -1).clip(0, 255).astype(np.uint8)
    q = cv2.inpaint(q, near.astype(np.uint8), max(2, int(round(3 * s))), cv2.INPAINT_TELEA)
    f = cv2.medianBlur(q, odd(27 * s)).astype(np.float32)
    Lf, af, bf = f[..., 0] / 255, f[..., 1] / 255 - .5, f[..., 2] / 255 - .5
    # strong colour edges of the field and the ink distance
    r = max(2, int(round(3 * s))); F = np.stack([Lf, af, bf], -1); pad = np.pad(F, ((r, r), (r, r), (0, 0)), mode='edge')
    sh = lambda dy, dx: pad[r + dy:r + dy + H, r + dx:r + dx + W]
    edge = np.max([np.linalg.norm(sh(dy, dx) - sh(-dy, -dx), axis=-1) for dy, dx in ((0, r), (r, 0), (r, r), (r, -r))], 0)
    dink = ndi.distance_transform_edt(~ink)
    skel = cv2.ximgproc.thinning(ink.astype(np.uint8) * 255) > 0   # ink width = ink area / skeleton length
    # marks: detected the same way for the ref and the game, or taken from the game's --ink-dbg marks frame
    dL = L - Lf; dab = np.hypot(a - af, b - bf)
    if marks_img is not None:
        m = marks_img
        plus = (m[..., 0] > .55) & (m[..., 2] > .55) & (m[..., 0] - m[..., 1] > .25)
        minus = (m[..., 1] > .55) & (m[..., 2] > .55) & (m[..., 1] - m[..., 0] > .25)
        mk = (plus | minus) & ~near
    else:
        mk = ~near & ((np.abs(dL) >= MARK_DL) | (dab >= MARK_DC))
    n, lab_id, st, _ = cv2.connectedComponentsWithStats(mk.astype(np.uint8), connectivity=8)
    keep = st[:, 4] >= max(3, int(round(6 * s * s))); keep[0] = False
    mk = keep[lab_id]; lab_id = np.where(mk, lab_id, 0)
    # component length = sqrt(12 * major-axis variance) (exact for a 1-px segment), per label
    ys, xs = np.nonzero(mk); ids = lab_id[ys, xs]; cnt = np.bincount(ids, minlength=n).astype(np.float64)
    c = np.maximum(cnt, 1); mx, my = np.bincount(ids, xs, n) / c, np.bincount(ids, ys, n) / c
    vxx = np.bincount(ids, xs * xs, n) / c - mx * mx; vyy = np.bincount(ids, ys * ys, n) / c - my * my
    vxy = np.bincount(ids, xs * ys, n) / c - mx * my
    lam = (vxx + vyy) / 2 + np.sqrt(((vxx - vyy) / 2) ** 2 + vxy ** 2)
    clen = np.sqrt(12 * np.maximum(lam, 0) + 1)
    return dict(s=s, H=H, W=W, L=L, a=a, b=b, C=np.hypot(a, b), h=hue(a, b), ink=ink, near=near, Lf=Lf, af=af, bf=bf,
                Cf=np.hypot(af, bf), hf=hue(af, bf), edge=edge, dink=dink, skel=skel, dL=dL, mk=mk,
                dmk=ndi.distance_transform_edt(~mk), cid=lab_id, ccnt=cnt, cx=mx, cy=my, clen=clen, r=r)


def panel_metrics(M, sel, panel):
    """Whole-panel metrics inside mask sel (the whole frame, or one of the 9 band crops)."""
    o = {}; L, C, h = M['L'][sel], M['C'][sel], M['h'][sel]; n = max(L.size, 1)
    o['neutral'] = 100 * (C < NEUTRAL_C).sum() / n
    for nm, lo, hi in FAM: o['fam_' + nm] = 100 * ((C >= NEUTRAL_C) & inh(h, lo, hi)).sum() / n
    for lo, hi in ((.04, .08), (.08, .12), (.12, .18), (.18, 9)): o['C_%02d_%02d' % (lo * 100, min(hi, .99) * 100)] = 100 * ((C >= lo) & (C < hi)).sum() / n
    o['C_p50'], o['C_p90'] = pct(C, 50), pct(C, 90)
    for lo, hi in ((0, .2), (.2, .4), (.4, .6), (.6, .8), (.8, 9)): o['L_%02d_%02d' % (lo * 100, min(hi, .99) * 100)] = 100 * ((L >= lo) & (L < hi)).sum() / n
    o['L_gt85'] = 100 * (L > .85).sum() / n
    o['L_p10'], o['L_p50'], o['L_p90'] = pct(L, 10), pct(L, 50), pct(L, 90)
    ink = M['ink'][sel]; o['ink_cover'] = 100 * ink.sum() / n
    e = sel & (M['edge'] >= EDGE_DE) & ~M['ink']
    o['ink_on_edges'] = 100 * (M['dink'][e] <= M['r'] + 1.5).mean() if e.sum() > 50 else None
    sk = (sel & M['skel']).sum()
    o['ink_width'] = float(ink.sum() / sk / M['s']) if sk > 200 else None
    fl = sel & ~M['near']; Lf = M['Lf'][fl]
    if Lf.size > 100:
        core = fl & (M['Lf'] <= np.percentile(Lf, 10))
        o['core_L'], o['core_C'], o['core_h'] = pct(M['Lf'][core], 50), pct(M['Cf'][core], 50), cmean(M['hf'][core], M['Cf'][core])
    for k, (lo, hi, cmin, l0, l1) in OBJ[panel].items():
        m = fl & inh(M['h'], lo, hi) & (M['C'] >= cmin) & (M['L'] >= l0) & (M['L'] < l1)
        o['obj_%s' % k] = 100 * m.sum() / max(fl.sum(), 1)
        if m.sum() >= 50:
            o['obj_%s_L' % k], o['obj_%s_C' % k] = pct(M['L'][m], 50), pct(M['C'][m], 50)
            if k != 'glow': o['obj_%s_h' % k] = cmean(M['h'][m], M['C'][m])
    return o


def mat_metrics(M, sel, s):
    """Marks, ink and field colour inside one material mask (one box, or all boxes of the material pooled)."""
    o = {}; fl = sel & ~M['near']; n = fl.sum()
    if n < 400: return o
    mk = fl & M['mk']; nm = mk.sum()
    o['cover'] = 100 * nm / n
    o['ink'] = 100 * (sel & M['ink']).sum() / sel.sum()
    o['L_sd'] = float(M['L'][fl].std())
    o['bare'] = 100 * (M['dmk'][fl] > 13 * s).mean()
    T = max(8, int(round(48 * s))); ys, xs = np.nonzero(sel); cov = []
    for y in range(ys.min(), ys.max() - T + 2, T):
        for x in range(xs.min(), xs.max() - T + 2, T):
            t = fl[y:y + T, x:x + T]
            if t.sum() >= .75 * T * T: cov.append(100 * M['mk'][y:y + T, x:x + T][t].mean())
    o['tile_sd'] = float(np.std(cov)) if len(cov) >= 4 else None
    if nm >= 30:
        dL = M['dL'][mk]; o['dL50'], o['dL90'], o['plus'] = pct(np.abs(dL), 50), pct(np.abs(dL), 90), 100 * (dL > 0).mean()
        hm = mk & (M['C'] >= HUE_C) & (M['Cf'] >= HUE_C)
        if hm.sum() >= 30:
            dh = np.abs((M['h'][hm] - M['hf'][hm] + 180) % 360 - 180)
            o['dh50'], o['dh90'], o['dh30'] = pct(dh, 50), pct(dh, 90), 100 * (dh >= 30).mean()
        ids = np.unique(M['cid'][mk]); ids = ids[ids > 0]
        if ids.size >= 8: o['len50'] = float(np.median(M['clen'][ids]) / s)
    Lf = M['Lf'][fl]; o['field_L'], o['field_C'], o['field_h'] = pct(Lf, 50), pct(M['Cf'][fl], 50), cmean(M['hf'][fl], M['Cf'][fl])
    return o


def split_lit(M, sel, thr):
    """lit / shade halves of a material (stones, crowns): field L above / below a threshold (Otsu of the pooled material)."""
    fl = sel & ~M['near']; o = {}
    for nm, m in (('lit', fl & (M['Lf'] >= thr)), ('shade', fl & (M['Lf'] < thr))):
        if m.sum() >= 200:
            o[nm + '_L'], o[nm + '_C'], o[nm + '_h'] = pct(M['Lf'][m], 50), pct(M['Cf'][m], 50), cmean(M['hf'][m], M['Cf'][m])
    return o


def otsu(x):
    hst, e = np.histogram(x, 64, (0, 1)); p = hst / max(hst.sum(), 1); c = (e[:-1] + e[1:]) / 2
    w = np.cumsum(p); mu = np.cumsum(p * c); best = np.nanargmax((mu[-1] * w - mu) ** 2 / (w * (1 - w) + 1e-9))
    return float(c[best] + .5 / 64)


def glow_metrics(M):
    """Night glow sources (L >= .82 blobs) and their spill on what is around them, per source; value = median over sources."""
    src = (M['L'] >= .82) & ~M['ink']; s = M['s']
    n, lab, st, _ = cv2.connectedComponentsWithStats(src.astype(np.uint8), connectivity=8)
    big = [i for i in range(1, n) if st[i, 4] >= 40 * s * s]
    if not big: return {}, []
    bg = np.median(M['Lf'][~M['near'] & ~src]); per = []
    for i in sorted(big, key=lambda i: -st[i, 4])[:16]:
        x, y, w, hh = st[i, :4]; rs = np.sqrt(st[i, 4] / np.pi); R = int(8 * rs) + 2
        y0, y1, x0, x1 = max(0, y - R), min(M['H'], y + hh + R), max(0, x - R), min(M['W'], x + w + R)
        me = lab[y0:y1, x0:x1] == i; d = ndi.distance_transform_edt(~me) / rs
        ok = ~src[y0:y1, x0:x1] & ~M['near'][y0:y1, x0:x1]; Lw, Cw, hw = M['Lf'][y0:y1, x0:x1], M['Cf'][y0:y1, x0:x1], M['hf'][y0:y1, x0:x1]
        prof = []
        for lo, hi in ((0, .5), (.5, 1), (1, 2), (2, 3), (3, 4), (4, 6), (6, 8)):
            ring = ok & (d > lo) & (d <= hi)
            prof.append(float(np.median(Lw[ring])) if ring.sum() >= 20 else np.nan)
        prof = np.array(prof); lift = prof[0] - bg
        if not np.isfinite(lift) or lift <= .02: continue
        half = next((r for r, v in zip((.5, 1, 2, 3, 4, 6, 8), prof) if np.isfinite(v) and v - bg < lift / 2), 8.0)
        sm = M['L'][lab == i]; sc = M['C'][lab == i]; sh = M['h'][lab == i]; near1 = ok & (d > 0) & (d <= 1)
        per.append(dict(L=float(np.median(sm)), C=float(np.median(sc)), h=cmean(sh, sc), lift=float(lift), half=float(half),
                        spill_h=cmean(hw[near1], Cw[near1]), spill_C=float(np.median(Cw[near1])) if near1.sum() >= 20 else None))
    if not per: return {}, []
    o = {}
    for k in ('L', 'C', 'lift', 'half', 'spill_C'):
        v = [p[k] for p in per if p[k] is not None]; o['glow_' + k] = float(np.median(v)) if v else None
    o['glow_h'] = cmean(np.array([p['h'] for p in per]), np.array([p['C'] for p in per]) + 1e-3)
    o['glow_spill_h'] = cmean(np.array([p['spill_h'] for p in per if p['spill_h'] is not None]))
    return o, per


def box_mask(shape, b, s0=1.0):
    m = np.zeros(shape, bool)
    if isinstance(b[0], (list, tuple)): cv2.fillPoly(m.view(np.uint8), [np.round(np.array(b) * s0).astype(np.int32)], 1)
    else: x0, y0, x1, y1 = [int(round(v * s0)) for v in b]; m[y0:y1, x0:x1] = True
    return m


def measure(M, panel, regions):
    """All metrics for one frame; for the ref also the per-crop / per-box values that make the bands."""
    H, W, s = M['H'], M['W'], M['s']; out = {}; spread = {}
    out.update(panel_metrics(M, np.ones((H, W), bool), panel))
    for i in range(3):
        for j in range(3):
            sel = np.zeros((H, W), bool); ch, cw = int(.6 * H), int(.6 * W)
            y0, x0 = int(i * (H - ch) / 2), int(j * (W - cw) / 2); sel[y0:y0 + ch, x0:x0 + cw] = True
            for k, v in panel_metrics(M, sel, panel).items(): spread.setdefault(k, []).append(v)
    out.pop('glow_n', None)
    sc = regions.get('scale', 1.0); R = regions.get(panel) or regions.get('both', {}); taken = np.zeros((H, W), bool)
    for mat in ('stones', 'crowns', 'bark', 'path', 'ground'):    # priority: a pixel belongs to one material
        boxes = R.get(mat, [])
        if not boxes: continue
        ms = [box_mask((H, W), b, sc) & ~taken for b in boxes]; pool = np.any(ms, 0); taken |= pool
        for k, v in mat_metrics(M, pool, s).items(): out[mat + '.' + k] = v
        for m in ms:
            for k, v in mat_metrics(M, m, s).items(): spread.setdefault(mat + '.' + k, []).append(v)
        if mat in ('stones', 'crowns'):
            thr = otsu(M['Lf'][pool & ~M['near']])
            for k, v in split_lit(M, pool, thr).items(): out[mat + '.' + k] = v
            for m in ms:
                for k, v in split_lit(M, m, thr).items(): spread.setdefault(mat + '.' + k, []).append(v)
    if panel == 'night':
        g, per = glow_metrics(M); out.update(g)
        for p in per:
            for k in ('L', 'C', 'lift', 'half', 'spill_C', 'h', 'spill_h'): spread.setdefault('glow_' + k, []).append(p[k])
    return out, spread


HUEKEYS = ('_h', 'glow_h', 'glow_spill_h')
def is_hue(k): return k.endswith(HUEKEYS)


def floor(k):
    """Resolution floor: a band is never narrower than ref +- this (shares 1 pt, L/L_sd .02, C .01, hue 4 deg, sizes 1 px)."""
    if is_hue(k): return 4.0
    if k.endswith(('_C', 'C_p50', 'C_p90', 'field_C', 'spill_C', 'glow_C', 'dL50', 'dL90')): return .01
    if k.endswith(('_L', 'L_p10', 'L_p50', 'L_p90', 'L_sd', 'glow_lift')): return .02
    if k.endswith(('len50', 'ink_width', 'glow_half')): return 1.0 if 'glow' not in k else .5
    return 1.0                                                     # shares and covers in percent points


def make_band(k, ref, vals):
    """Band = the reference's own spread: [min, max] over the 9 re-framed crops (60% of the panel, 3x3 positions) for panel
    metrics, over the material's boxes for material metrics, over the glow sources for glow metrics; widened to the floor."""
    v = [x for x in vals if x is not None] + ([ref] if ref is not None else [])
    if ref is None or len(v) < 3: return None
    f = floor(k)
    if is_hue(k):
        d = [((x - ref + 180) % 360) - 180 for x in v]; return [(ref + min(min(d), -f)) % 360, (ref + max(max(d), f)) % 360]
    lo, hi = min(min(v), ref - f), max(max(v), ref + f)
    return [max(lo, 0.0) if ref >= 0 else lo, hi]


def inband(k, v, bd):
    if v is None or bd is None: return None
    if is_hue(k):
        lo, hi = bd; w = (hi - lo) % 360; return ((v - lo) % 360) <= w + 1e-6
    return bd[0] - 1e-9 <= v <= bd[1] + 1e-9


SCALE_KEYS = ('ink_width', '.len50', '.bare', '.tile_sd', '.ink', 'glow_n')   # canvas-scale or composition: read with the camera note


def report(vals, spec, panel, show_all=True):
    sp = spec[panel]; rows = []; nin = nout = nna = 0; worst = []
    for k, e in sp.items():
        v = vals.get(k); ok = inband(k, v, e['band'])
        tag = 'n/a' if ok is None else ('in' if ok else 'OUT')
        if ok is None: nna += 1
        elif ok: nin += 1
        else:
            nout += 1; lo, hi = e['band']
            dist = (min(abs((v - lo + 180) % 360 - 180), abs((v - hi + 180) % 360 - 180)) / 30 if is_hue(k)
                    else min(abs(v - lo), abs(v - hi)) / max(abs(hi - lo), abs(e['ref']) * .25, 1e-3))
            worst.append((dist, k))
        f = lambda x: '-' if x is None else ('%.0f' % x if abs(x) >= 10 else '%.3f' % x if abs(x) < 1 else '%.2f' % x)
        mark = '~' if any(t in k for t in SCALE_KEYS) else ' '
        rows.append('%-24s%s ref %7s  band [%7s, %7s]  frame %7s  %s' % (k, mark, f(e['ref']), f(e['band'][0]), f(e['band'][1]), f(v), tag))
    print('\n'.join(rows))
    worst.sort(reverse=True)
    print('SUMMARY %s: in %d  OUT %d  n/a %d   (~ = canvas-scale / composition metric, read with the camera note)' % (panel, nin, nout, nna))
    print('WORST OUT: ' + ', '.join('%s %s' % (k, '(%.1f bands off)' % d) for d, k in worst[:8]))
    return nin, nout, nna, [k for _, k in worst]


def debug_png(rgb, M, path):
    v = (rgb * 255).astype(np.uint8).copy(); v[M['mk'] & (M['dL'] > 0)] = (255, 0, 255); v[M['mk'] & (M['dL'] <= 0)] = (0, 255, 255)
    v[M['ink']] = (255, 0, 0); e = (M['edge'] >= EDGE_DE) & ~M['ink'] & (M['dink'] > M['r'] + 1.5); v[e] = (255, 255, 0)
    Image.fromarray(np.concatenate([(rgb * 255).astype(np.uint8), v], 1)).save(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('frame', nargs='?'); ap.add_argument('--panel', choices=('day', 'night'))
    ap.add_argument('--regions'); ap.add_argument('--marks'); ap.add_argument('--json'); ap.add_argument('--debug')
    ap.add_argument('--ref', choices=('day', 'night')); ap.add_argument('--freeze', action='store_true'); ap.add_argument('--force', action='store_true')
    A = ap.parse_args()
    if A.freeze:
        if os.path.exists(SPEC) and not A.force: sys.exit('spec is frozen (%s); --force only to rebuild it on purpose' % SPEC)
        reg = json.load(open(REF_REG)); spec = {'_note': 'FROZEN 19 Nov 2026 from %s by look_spec.py --freeze; bands = the ref own spread' % os.path.basename(REF)}
        for p in ('night', 'day'):
            M = maps(load_frame(REF, p)); out, spread = measure(M, p, reg)
            spec[p] = {k: {'ref': v, 'band': make_band(k, v, spread.get(k, []))} for k, v in out.items()}
            spec[p] = {k: e for k, e in spec[p].items() if e['band'] is not None}
        json.dump(spec, open(SPEC, 'w'), indent=0); print('wrote', SPEC); return
    spec = json.load(open(SPEC))
    if A.ref:
        rgb, panel, reg, mimg = load_frame(REF, A.ref), A.ref, json.load(open(REF_REG)), None
    else:
        if not (A.frame and A.panel): ap.error('give FRAME --panel day|night (or --ref / --freeze)')
        rgb, panel = load_frame(A.frame), A.panel
        reg = json.load(open(A.regions or VERGE_REG))
        mimg = load_frame(A.marks) if A.marks else None
    M = maps(rgb, mimg); vals, _ = measure(M, panel, reg)
    if A.debug: debug_png(rgb, M, A.debug)
    report(vals, spec, panel)
    if A.json: json.dump(vals, open(A.json, 'w'), indent=0)


if __name__ == '__main__':
    main()
