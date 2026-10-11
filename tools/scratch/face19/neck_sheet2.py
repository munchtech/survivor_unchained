"""neck_sheet2.py TAG OUT: the owner's neck-length sheet (judge j6's fixes: equal steps, a tick at each column's own
notch, captions): today, -1, -2 and -3 cm; front and profile at the Look,
and in play facing the camera (camera 12, upscaled 3x); her portrait as a fifth column at the same eye-to-chin size; a
guide line at today's collarbone (env NOTCH_Y: its height in TAG_nk0_f.png); labelled, with the note that no helmet or
gorget model exists yet."""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\tools\assets")
import face_fit as ff  # noqa
LOGS = "C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/91211d34-e079-4956-a2a0-7b52c04594a8/scratchpad/f18/logs"
S = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\.shots"
tag, out = sys.argv[1], sys.argv[2]
font = ImageFont.truetype('arial.ttf', 22); small = ImageFont.truetype('arial.ttf', 18)
L = ['0', '-1', '-2', '-3']; names = {'0': 'today', '-1': '1 cm shorter', '-2': '2 cm shorter', '-3': '3 cm shorter'}
def img(n): return Image.open(os.path.join(S, n + '.png')).convert('RGB')
f0 = img('%s_nk0_f' % tag); lm = ff.detect(np.asarray(f0))[:, :2]
pup = (lm[468] + lm[473]) / 2; chin = lm[152]; u = chin[1] - pup[1]; cx = chin[0]
fbox = (int(cx - 1.25 * u), int(pup[1] - 0.9 * u), int(cx + 1.25 * u), int(chin[1] + 2.1 * u))
pbox = (560, 60, 1160, 960); qbox = (890, 380, 1030, 680)
W = 420
def fit(im, w): return im.resize((w, int(w * im.height / im.width)), Image.LANCZOS)
R = "C:/Users/munch/Desktop/survivorsunchained_inputs/face4/refs_front"
ref = Image.open(os.path.join(R, 'own_her_23.png')).convert('RGB'); rl = ff.detect(np.asarray(ref))[:, :2]
rp = (rl[468] + rl[473]) / 2; rc = rl[152]; ru = rc[1] - rp[1]; k = u / ru
ref0, rp0, rc0 = ref, rp, rc
def refbuild(k):
    r = ref0.resize((int(ref0.width * k), int(ref0.height * k)), Image.LANCZOS); p, c = rp0 * k, rc0 * k
    bx = (int(c[0] - 1.25 * u), int(p[1] - 0.9 * u), int(c[0] + 1.25 * u), int(c[1] + 2.1 * u))
    return r, bx, fit(r.crop(bx), W)
ref, rbox, rtile = refbuild(k)
front = [fit(img('%s_nk%s_f' % (tag, n)).crop(fbox), W) for n in L] + [rtile]
from scipy.ndimage import gaussian_filter1d
def det(im):
    # (mediapipe misses some frames at full size: try again at 2x)
    l = ff.detect(np.asarray(im))
    if l is None: l = ff.detect(np.asarray(im.resize((im.width * 2, im.height * 2), Image.LANCZOS))); l = None if l is None else l / 2
    return l
def pc(im):
    # pupil-to-chin of a final tile, re-detected on it
    l = det(im)[:, :2]; return (l[468] + l[473]) / 2, l[152]
# (the portrait matched to today's tile within 2%: rescale and re-detect until it is)
def span(t): p, c = pc(t); return c[1] - p[1]
for _ in range(4):
    a0, a1 = span(front[0]), span(front[4])
    if abs(a1 / a0 - 1) < 0.005: break
    k *= a0 / a1; ref, rbox, rtile = refbuild(k); front[4] = rtile
match = (span(front[0]), span(front[4])); print("pupil-to-chin px today/portrait", match, "diff %.2f%%" % (100 * (match[1] / match[0] - 1)))
def tick(t, y, x):
    dd = ImageDraw.Draw(t); dd.line((x - 34, y, x + 34, y), fill=(255, 210, 60), width=3)
def mark(n, suf):
    # (MARK x y: the sternum top's screen point, printed by the game at the shot, --mark-bones)
    for ln in open(os.path.join(os.environ.get('LOGS', LOGS), '%s_nk%s_%s.log' % (tag, n, suf)), errors='replace'):
        if ln.startswith('MARK '): return [float(v) for v in ln.split()[1:3]]
    raise SystemExit('no MARK in the log of %s_nk%s_%s' % (tag, n, suf))
def notch(im, box):
    # (the portrait's notch, the strongest dip in lightness down her midline, 0.6-1.5 pupil-to-chin below her chin)
    a = np.asarray(im.convert('L'), np.float32); l = det(im)[:, :2]
    p = (l[468] + l[473]) / 2; c = l[152]; uu = c[1] - p[1]; x0 = int(c[0]); w = max(2, int(0.04 * uu))
    ys = np.arange(int(c[1] + 0.6 * uu), min(a.shape[0] - 1, int(c[1] + 1.5 * uu)))
    d2 = gaussian_filter1d(gaussian_filter1d(a[ys, x0 - w:x0 + w].mean(1), 0.02 * uu), 0.03 * uu, order=2)
    return (ys[int(np.argmax(d2))] - box[1]) * W / (box[2] - box[0]), (x0 - box[0]) * W / (box[2] - box[0])
def tp(m, box): return (m[1] - box[1]) * W / (box[2] - box[0]), (m[0] - box[0]) * W / (box[2] - box[0])
ratios = []; ticks = []
for n, t in zip(L, front[:4]): ticks.append(tp(mark(n, 'f'), fbox))
ticks.append(notch(ref, rbox))
for t, (ty, tx) in zip(front, ticks):
    p, c = pc(t); ratios.append((ty - c[1]) / (c[1] - p[1])); tick(t, ty, tx)
print("ratios chin-to-notch / pupil-to-chin", ratios)
prof = [fit(img('%s_nk%s_p' % (tag, n)).crop(pbox), W) for n in L]
for n, t in zip(L, prof): tick(t, *tp(mark(n, 'p'), pbox))
ny = os.environ.get('NOTCH_Y')
if ny:
    gy = int((float(ny) - fbox[1]) * W / (fbox[2] - fbox[0]))
    for t in front[:4]:
        dd = ImageDraw.Draw(t)
        for x0 in range(0, W, 14): dd.line((x0, gy, x0 + 8, gy), fill=(120, 230, 255), width=2)
rows = [("At the Look, front (%syellow: from her collarbone bones; portrait: the detected notch; right: her portrait, scaled to the same pupil-to-chin)" % ("dashed: today's collarbone; " if ny else ""), front),
        ('At the Look, profile', prof),
        ('In play facing the camera (camera 12), 3x. Her head is bowed in this pose, so her neck hardly shows: the four read alike from the front too.',
         [fit(img('%s_pf_nk%s' % (tag, n)).crop(qbox), W) for n in L])]
H = sum(r[1][0].height + 34 for r in rows) + 40 + 70 + 24
def vs(r): d = round(100 * (r / ratios[4] - 1)); return '%d%% %s than her portrait' % (abs(d), 'longer' if d >= 0 else 'shorter')
CAP = ['%.2f  (%s)' % (r, vs(r)) for r in ratios[:4]] + ['%.2f  (her portrait)' % ratios[4]]
sh = Image.new('RGB', (5 * (W + 8) + 8, H + 24), (24, 24, 24)); d = ImageDraw.Draw(sh)
for i, n in enumerate(L): d.text((8 + i * (W + 8) + 6, 8), names[n], fill=(255, 230, 120), font=font)
d.text((8 + 4 * (W + 8) + 6, 8), 'her portrait', fill=(255, 230, 120), font=font)
y = 40
for title, tiles in rows:
    d.text((10, y + 4), title, fill=(200, 200, 200), font=small); y += 30
    for i, t in enumerate(tiles): sh.paste(t, (8 + i * (W + 8), y))
    y += tiles[0].height + 4
    if tiles is front:
        for i, c in enumerate(CAP): d.text((8 + i * (W + 8) + 6, y), c, fill=(255, 210, 60), font=small)
        y += 24
d.text((10, y + 8), "Her neck only; her head, face and body are unchanged. No helmet, gorget or high-collar model exists yet,", fill=(230, 230, 230), font=small)
d.text((10, y + 32), "so none is shown: a longer neck leaves room for one without covering her bust.", fill=(230, 230, 230), font=small)
best = min(range(4), key=lambda i: abs(ratios[i] - ratios[4]))
d.text((10, y + 56), "Measured, chin-to-notch over pupil-to-chin: today %.2f, her portrait %.2f; %s comes closest (%.2f). Today's length stays a full option." % (ratios[0], ratios[4], names[L[best]], ratios[best]), fill=(230, 230, 230), font=small)
sh.save(out, quality=93); print(out, sh.size)
