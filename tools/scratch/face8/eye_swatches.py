"""eye_swatches.py CALTAG: the eye swatches from iris_cal's fit: each preset's own (two faces whose dyes are within a
few per cent share one, their mean), the others (no portrait) from a target of their own read through the same
curves. Keeps each old swatch's ring against its iris (new ones take their nearest's)."""
import json
import sys
import numpy as np
from iris_sample import lin, hexc

cal = sys.argv[1]
SC = r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8'
W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2'
WI = 0.8
R = json.load(open(SC + r'\iris_cal_%s.json' % cal))
looks = json.load(open(W + r'\godot\data\content\looks.json', encoding='utf-8'))
sw = {e['id']: e for e in looks['heroes']['female']['eyes']}


def hx(h):
    return lin(np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)]))


def gm(ds):
    return np.exp(np.mean(np.log(np.array(ds)), 0))


# swatch id: (faces it is fitted to, the old swatch whose ring it keeps)
PLAN = {'frost': (['highborn'], 'frost'), 'dove': (['fey'], 'frost'), 'flint': (['hardwon'], 'flint'),
        'lichen': (['vixen'], 'flint'), 'sloe': (['sunborn'], 'sloe'), 'peat': (['moonlit', 'saffron'], 'peat'),
        'chestnut': (['doe'], 'peat'), 'hazel': (['wildling'], 'hazel')}
out = {}
for sid, (faces, like) in PLAN.items():
    d = gm([R[f]['dye'] for f in faces])
    spread = [np.round(np.array(R[f]['dye']) / d, 3).tolist() for f in faces]
    i0, r0 = hx(sw[like]['color']), hx(sw[like]['ring'])
    eff = WI * i0 + (1 - WI) * r0
    out[sid] = (hexc(d * i0 / eff), hexc(d * r0 / eff))
    print('%-9s %s iris %s ring %s   (faces over it %s)' % (sid, faces, *out[sid], spread))
# No portrait: an amber, a cornflower blue and a heather violet, each as such an eye stands to a fair cheek in a
# photograph like the presets' (her cheek in the game, (0.68, 0.40, 0.27)), read back through the greys' curves.
cheek = np.array([0.68, 0.40, 0.27])
def gain(f):
    return np.array(R[f]['dye']) / np.array(R[f]['target'])      # (dye over target, as a near face's needed)
for sid, ratio, near in (('wolf', (0.26, 0.24, 0.10), 'wildling'), ('cornflower', (0.10, 0.21, 0.40), 'highborn'), ('heather', (0.16, 0.18, 0.36), 'highborn')):
    t = np.array(ratio) * cheek
    d = t * gain(near)
    i0, r0 = hx(sw[sid]['color']), hx(sw[sid]['ring'])
    eff = WI * i0 + (1 - WI) * r0
    k = d / eff
    out[sid] = (hexc(i0 * k), hexc(r0 * k))
    print('%-9s (no portrait) target %s iris %s ring %s' % (sid, hexc(t), *out[sid]))
json.dump(out, open(SC + r'\eye_swatches_%s.json' % cal, 'w'), indent=1)
