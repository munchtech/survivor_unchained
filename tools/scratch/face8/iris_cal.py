"""iris_cal.py CALTAG FITTAG: her irises dyed through greys under the white rig (CALTAG_eyecal_NN.png: paint, then the
greys) give each channel's curve (shown against dye, linear); each face's target (FITTAG's iris_fit json: its
portrait's iris over its cheek, times its own cheek in the game) read back through the curves gives the dye each face
needs. Prints the swatches (iris and ring, keeping each old swatch's ring against its iris) and her painted iris's tint.
Run with the facefit venv's python."""
import json
import sys
import numpy as np
from iris_sample import measure, lin, hexc

cal, fit = sys.argv[1], sys.argv[2]
G = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2\godot\.shots'
SC = r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8'
W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2'
CAL = 'paint,#0c0c0c,#1a1a1a,#2a2a2a,#3c3c3c,#565656,#787878,#a0a0a0,#c8c8c8'.split(',')
CROP = [660, 150, 1160, 740]
WI = 0.8    # (the measured ring of the iris: four fifths the iris's colour, a fifth the ring's round the pupil)


def hx(h):
    return lin(np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)]))


rows = []
for i, c in enumerate(CAL):
    r = measure(G + r'\%s_eyecal_%02d.png' % (cal, i), CROP)
    if r is None or r['r'] is None or r['l'] is None:
        print(i, c, 'no eyes')
        continue
    m = (hx(r['r']['iris']) + hx(r['l']['iris'])) / 2
    rows.append((c, m, hx(r['cheek'])))
    print('%-8s -> %s  cheek %s' % (c, hexc(m), r['cheek']))
greys = sorted((hx(c)[0], m) for c, m, _ in rows if c != 'paint')
A = np.array([g for g, _ in greys])
M = np.array([m for _, m in greys])
# (shown = veil + gain * dye, per channel, from the darker greys where it is straight)
fitk = [np.polyfit(A[:5], M[:5, k], 1) for k in range(3)]
print('gain', np.round([f[0] for f in fitk], 3), 'veil', np.round([f[1] for f in fitk], 4))
cheek_cal = np.median([ch for _, _, ch in rows], 0)


def dye_for(t):
    out = []
    for k in range(3):
        if t[k] <= M[0, k]:
            out.append(max((t[k] - fitk[k][1]) / fitk[k][0], 0.0005))
        elif t[k] >= M[-1, k]:
            out.append(A[-1] * t[k] / M[-1, k])
        else:
            out.append(np.interp(t[k], M[:, k], A))
    return np.array(out)


F = json.load(open(SC + r'\iris_%s.json' % fit))
looks = json.load(open(W + r'\godot\data\content\looks.json', encoding='utf-8'))
sw = {e['id']: e for e in looks['heroes']['female']['eyes']}
res = {}
for k, v in F.items():
    ri, rc, gc = (np.array(v[x]) for x in ('ref_iris', 'ref_cheek', 'game_cheek'))
    t = ri / rc * gc
    d = dye_for(t)
    res[k] = (v['eyes'], t, d)
    print('%-9s target %s -> dye %s (lin %s)' % (k, hexc(t), hexc(d), np.round(d, 4)))
paint = [m for c, m, _ in rows if c == 'paint'][0]
veil = np.array([f[1] for f in fitk])
t = res['own'][1]
tint = (t - veil) / np.maximum(paint - veil, 1e-4)
print('moss (painted): shows %s, wants %s: tint (linear) %s' % (hexc(paint), hexc(t), np.round(tint, 3)))
print()
for k, (eye, t, d) in res.items():
    if k == 'own' or not sw.get(eye) or not sw[eye]['color']:
        continue
    i0, r0 = hx(sw[eye]['color']), hx(sw[eye]['ring'] or sw[eye]['color'])
    eff = WI * i0 + (1 - WI) * r0
    ni, nr = d * i0 / eff, d * r0 / eff
    print('%-9s (%s) iris %s ring %s' % (k, eye, hexc(ni), hexc(nr)))
json.dump({k: {'eyes': e, 'target': t.tolist(), 'dye': d.tolist()} for k, (e, t, d) in res.items()} | {'_tint': tint.tolist(), '_veil': veil.tolist()},
          open(SC + r'\iris_cal_%s.json' % cal, 'w'), indent=1)
