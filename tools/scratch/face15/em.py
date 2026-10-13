"""em.py TAG face... : the eyes measured on godot/.shots/TAG_face.png without MediaPipe (iris edges fitted from the
round-2 judge's centres, judge_ey2/all_fit.json), against the judge's targets: iris R/IPD, upper and lower lid cover,
mid-iris ring colour (Look rig), collarette/outer light, pupil/iris light, lash darkness (inner/centre/outer, the
judge's lash2 method) and band colour, catchlight colour and place, the whites' gradient. Writes TAG_fit.json."""
import sys, os, json, colorsys
import numpy as np
from PIL import Image
SHOTS = os.environ.get('SHOTS', r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\.shots')
J = r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\181eef02-779f-45de-b419-31a949a4d27e\scratchpad\judge_ey2'
HERE = os.path.dirname(os.path.abspath(__file__))
seeds = {m['name']: m for m in json.load(open(os.path.join(HERE, 'ey2_all_fit.json')))}
TARGET = {'own': (107, 111, 90), 'highborn': (88, 90, 90), 'doe': (61, 32, 20), 'sunborn': (30, 22, 19), 'vixen': (93, 84, 72),
          'moonlit': (50, 31, 25), 'saffron': (46, 29, 24), 'wildling': (106, 87, 65), 'hardwon': (88, 84, 76), 'fey': (113, 105, 96)}
COVER = {'own': 0.20, 'highborn': 0.205, 'doe': 0.19, 'sunborn': 0.215, 'vixen': 0.18, 'moonlit': 0.12, 'saffron': 0.15,
         'wildling': 0.175, 'hardwon': 0.205, 'fey': 0.155}
IRIS = {'sunborn': 0.108, 'moonlit': 0.109, 'saffron': 0.114, 'wildling': 0.121}


def lum(a): return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def sample(a, pts):
    pts = np.atleast_2d(pts); x, y = pts[:, 0], pts[:, 1]
    x0 = np.clip(np.floor(x).astype(int), 0, a.shape[1] - 2); y0 = np.clip(np.floor(y).astype(int), 0, a.shape[0] - 2)
    fx = np.clip(x - x0, 0, 1); fy = np.clip(y - y0, 0, 1)
    if a.ndim == 3: fx, fy = fx[:, None], fy[:, None]
    return a[y0, x0] * (1 - fx) * (1 - fy) + a[y0, x0 + 1] * fx * (1 - fy) + a[y0 + 1, x0] * (1 - fx) * fy + a[y0 + 1, x0 + 1] * fx * fy


def circle_fit(pts):
    x, y = pts[:, 0], pts[:, 1]
    A = np.c_[2 * x, 2 * y, np.ones(len(x))]
    (cx, cy, k), *_ = np.linalg.lstsq(A, x * x + y * y, rcond=None)
    return np.array([cx, cy]), np.sqrt(k + cx * cx + cy * cy)


def edge_fit(Y, c, R):
    for it in range(3):
        pts = []
        for dy in np.linspace(-0.5, 0.5, 21):
            yv = c[1] + dy * R
            for sgn in (-1, 1):
                xs = c[0] + sgn * np.linspace(0.6 * R, 1.45 * R, 86)
                h = 0.06 * R
                g = sample(Y, np.c_[xs + sgn * h, np.full_like(xs, yv)]) - sample(Y, np.c_[xs - sgn * h, np.full_like(xs, yv)])
                k = int(np.argmax(g))
                if g[k] > 0.04 and 0 < k < len(xs) - 1:
                    pts.append((xs[k], yv))
        pts = np.array(pts)
        if len(pts) < 10:
            return c, R
        c2, R2 = circle_fit(pts)
        res = np.abs(np.linalg.norm(pts - c2, axis=1) - R2)
        keep = res < max(0.8, 2.5 * np.median(res))
        c, R = circle_fit(pts[keep])
    return c, R


def col_prof(Y, x, y0, hs, sgn): return sample(Y, np.c_[np.full_like(hs, x), y0 + sgn * hs])


def vis_top(Y, c, R, irisL):
    from scipy.ndimage import binary_dilation
    x0, x1 = int(c[0] - 1.2 * R), int(c[0] + 1.2 * R) + 2; y0, y1 = int(c[1] - 1.5 * R), int(c[1] + 1.2 * R) + 2
    gy, gx = np.mgrid[y0:y1, x0:x1]
    sub = Y[y0:y1, x0:x1]
    inside = (gx - c[0]) ** 2 + (gy - c[1]) ** 2 <= R ** 2
    hot = binary_dilation(inside & (sub > max(0.55, irisL + 0.4 * (1 - irisL))), iterations=max(1, int(round(0.12 * R))))
    M = np.zeros(Y.shape); M[y0:y1, x0:x1] = hot
    tops = []
    hs = np.linspace(0.3 * R, 1.4 * R, 111); h = 0.06 * R
    for k in np.linspace(-0.5, 0.5, 21):
        x = c[0] + k * R
        prof = col_prof(Y, x, c[1], hs, -1)
        g = col_prof(Y, x, c[1], hs + h, -1) - col_prof(Y, x, c[1], hs - h, -1)
        bad = (col_prof(M, x, c[1], hs + h, -1) > 0.01) | (col_prof(M, x, c[1], hs - h, -1) > 0.01) | (col_prof(M, x, c[1], hs, -1) > 0.01)
        lo = int(np.searchsorted(hs, 0.45 * R)); i_min = lo + int(np.argmin(prof[lo:]))
        if i_min <= lo + 1: continue
        gg = np.where(bad, 0.0, g)[lo:i_min + 1]
        if gg.min() > -0.015: continue
        tops.append((k, hs[lo + int(np.argmin(gg))] / R))
    if not tops: return np.nan
    t = np.array(tops); mid = t[np.abs(t[:, 0]) <= 0.3]
    return float(np.median(mid[:, 1] if len(mid) >= 3 else t[:, 1]))


def margin_top(Y, c, R):
    """the upper lid's margin over the iris's middle (in R above its centre): beside the iris (|x| 1.1 to 1.6 R),
    going up from the white at mid height, where the light falls half way to the lash line's; a parabola in x read
    at x = 0 (the judge's lid_margin, without landmarks)."""
    xs, hs = [], []
    up = np.linspace(0.0, 1.6 * R, 161)
    for sg in (-1, 1):
        for x in np.linspace(1.1, 1.6, 6):
            p = sample(Y, np.c_[np.full_like(up, c[0] + sg * x * R), c[1] - up])
            w = p[:int(len(up) * 0.25)].max(); i_w = int(np.argmax(p[:int(len(up) * 0.25)]))
            i_m = i_w + int(np.argmin(p[i_w:]))
            if p[i_m] > 0.8 * w: continue
            half = p[i_m] + 0.5 * (w - p[i_m])
            j = i_w
            while j < i_m and p[j] > half: j += 1
            xs.append(x); hs.append(up[j] / R)
    if len(xs) < 4: return np.nan
    A = np.c_[np.ones(len(xs)), np.array(xs) ** 2]
    (a0, a2), *_ = np.linalg.lstsq(A, np.array(hs), rcond=None)
    return float(a0)


def vis_bot(Y, c, R):
    bots = []
    hs = np.linspace(0.5 * R, 1.3 * R, 81); h = 0.06 * R
    for k in np.linspace(-0.4, 0.4, 17):
        x = c[0] + k * R
        g = col_prof(Y, x, c[1], hs + h, 1) - col_prof(Y, x, c[1], hs - h, 1)
        bots.append(hs[int(np.argmax(np.abs(g)))] / R)
    return float(np.median(bots))


def ann(c, R, r0, r1, t0, t1, nr=6, nt=40):
    return np.array([c + rr * R * np.array([np.cos(t), np.sin(t)]) for rr in np.linspace(r0, r1, nr) for t in np.linspace(t0, t1, nt)])


def lash(a, Y, c, R, ew, s):
    outer = -1 if s == 'R' else 1
    res = {}
    for zone, xs in (("inner", [-outer * t for t in (1.15, 1.3, 1.45)]), ("centre", [-0.25, 0.0, 0.25]), ("outer", [outer * t for t in (1.15, 1.3, 1.45)])):
        ds, cols = [], []
        for xo in xs:
            x = c[0] + xo * R
            hs = np.linspace(0.3 * R, 2.4 * R, 211)
            p = sample(Y, np.c_[np.full_like(hs, x), c[1] - hs])
            lo = int(np.searchsorted(hs, 0.45 * R)); hi = int(np.searchsorted(hs, 1.7 * R))
            i_min = lo + int(np.argmin(p[lo:hi]))
            up = p[i_min:min(len(p), i_min + int(0.8 * R / (hs[1] - hs[0])))]
            ds.append(1 - p[i_min] / max(np.percentile(up, 90), 1e-6))
            cols.append(sample(a, np.array([[x, c[1] - hs[i_min]]]))[0])
        res[zone] = (np.median(ds), np.median(np.array(cols), 0))
    return res


tag = sys.argv[1]
out = {}
print("face      side R/IPD  (want) | cover top (want) bot | ring rgb   (target)      dL%  | coll/out pupil/iris | lash dark in/ctr/out  band rgb | catch rgb  at(R)       | white below/ctr")
for arg in sys.argv[2:]:
    face, nm = (arg.split(':')[0], f'{tag}_' + arg.split(':')[1]) if ':' in arg else (arg, f'{tag}_{arg}')
    a = np.asarray(Image.open(os.path.join(SHOTS, nm + '.png')).convert('RGB')).astype(float) / 255
    Y = lum(a)
    sd = seeds.get('ey2_' + face)
    if sd is None: print(face, 'no seed'); continue
    k = IRIS.get(face, 0.117) / 0.13
    fits = {}
    for s in 'RL':
        c, R = edge_fit(Y, np.array(sd[s]['c']), sd[s]['R'] * k)
        fits[s] = (c, R)
    ipd = np.linalg.norm(fits['R'][0] - fits['L'][0]); ew = 0.43 * ipd
    out[nm] = {}
    for s in 'RL':
        c, R = fits[s]
        lower = ann(c, R, 0.5, 0.75, -0.25 * np.pi, 1.25 * np.pi)   # (the mid-iris ring but its top quarter: clear of the lid shadow and catchlight)
        rgb = np.median(sample(a, lower), 0)
        irisL = float(lum(rgb))
        top = margin_top(Y, c, R); bot = vis_bot(Y, c, R)
        coll = np.median(lum(sample(a, ann(c, R, 0.3, 0.45, 0.1 * np.pi, 0.9 * np.pi))))
        outr = np.median(lum(sample(a, ann(c, R, 0.62, 0.85, 0.1 * np.pi, 0.9 * np.pi))))
        side = np.r_[ann(c, R, 0.0, 0.12, 0, 2 * np.pi, 3, 24)]
        pup = np.percentile(lum(sample(a, side)), 30)
        L = lash(a, Y, c, R, ew, s)
        # catchlight: the brightest spot inside the iris
        gy, gx = np.mgrid[int(c[1] - R):int(c[1] + R) + 1, int(c[0] - R):int(c[0] + R) + 1]
        ins = (gx - c[0]) ** 2 + (gy - c[1]) ** 2 <= (0.95 * R) ** 2
        sub = Y[gy, gx]; i = np.argmax(np.where(ins, sub, -1))
        cat = a[gy.ravel()[i], gx.ravel()[i]]; cat_at = ((gx.ravel()[i] - c[0]) / R, (gy.ravel()[i] - c[1]) / R)
        wc = np.median(lum(sample(a, np.array([[c[0] + sg * x * R, c[1]] for sg in (-1, 1) for x in np.linspace(1.15, 1.5, 8)]))))
        wb = np.median(lum(sample(a, np.array([[c[0] + sg * x * R, c[1] + 0.5 * R] for sg in (-1, 1) for x in np.linspace(1.15, 1.5, 8)]))))
        t = np.array(TARGET[face]); r255 = rgb * 255
        dl = 100 * (lum(rgb) / lum(t / 255) - 1)
        cov = (1 - top) / 2; cov_lo = (1 - bot) / 2
        print(f"{face:9s} {s}  {R / ipd:.4f} ({'%.4f' % (0.0975 * IRIS.get(face, 0.117) / 0.117)}) | {cov:.3f} ({COVER[face]:.3f}) {cov_lo:.3f} | "
              f"{np.round(r255).astype(int)} ({t}) {dl:+4.0f} | {coll / max(outr, 1e-6):.2f}     {pup / max(irisL, 1e-6):.2f} {pup:.3f}| "
              f"{L['inner'][0]:.2f}/{L['centre'][0]:.2f}/{L['outer'][0]:.2f}  {np.round(L['centre'][1] * 255).astype(int)} | "
              f"{np.round(cat * 255).astype(int)} ({cat_at[0]:+.2f},{cat_at[1]:+.2f}) | {wb / max(wc, 1e-6):.2f}")
        out[nm][s] = dict(c=[float(c[0]), float(c[1])], R=float(R), rgb=[float(v) for v in rgb], cover=cov, cover_lo=cov_lo,
                          coll=float(coll / max(outr, 1e-6)), lash=[float(L[z][0]) for z in ('inner', 'centre', 'outer')])
json.dump(out, open(os.path.join(HERE, f'{tag}_fit.json'), 'w'), indent=1)
