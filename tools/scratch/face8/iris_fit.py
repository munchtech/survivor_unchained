"""iris_fit.py TAG: each face's irises under the white rig (TAG_w_<id>.png; hers TAG_white.png) against its portrait's,
each as it stands to its own cheek (so the light's level cancels): per channel, render over portrait, and lightness.
Run with the facefit venv's python."""
import json
import sys
import numpy as np
from iris_sample import measure, lin

tag = sys.argv[1]
w = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2'
g = w + r'\godot\.shots'
s4 = r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face4'
crop = [660, 150, 1160, 740]
LW = np.array([0.2126, 0.7152, 0.0722])
P = json.load(open(w + r'\tools\assets\heroine_face\presets.json', encoding='utf-8'))


def hx(h):
    return lin(np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)]))


def iris(r):
    if r is None or r['r'] is None or r['l'] is None:
        return None, None
    i = (hx(r['r']['iris']) + hx(r['l']['iris'])) / 2
    return i, hx(r['cheek'])


out = {}
for p in P:
    ref = s4 + (r'\from_face3\refs_her\her_23.png' if p['id'] == 'own' else '\\refs_front\\' + p['ref'].split('/')[-1] + '.png')
    shot = g + ('\\%s_white.png' % tag if p['id'] == 'own' else '\\%s_w_%s.png' % (tag, p['id']))
    import os
    if not os.path.exists(shot):
        continue
    (ia, ca), (ib, cb) = iris(measure(ref)), iris(measure(shot, crop))
    if ia is None or ib is None:
        print('%-9s no eyes' % p['id'])
        continue
    ra, rb = ia / ca, ib / cb
    f = rb / ra
    L = (rb @ LW) / (ra @ LW) if False else ((ib @ LW) / (cb @ LW)) / ((ia @ LW) / (ca @ LW))
    out[p['id']] = {'eyes': p['eyes'], 'ref_iris': ia.tolist(), 'ref_cheek': ca.tolist(), 'game_iris': ib.tolist(), 'game_cheek': cb.tolist()}
    print('%-9s %-6s render/portrait (iris over cheek)  r %.2f g %.2f b %.2f   L %.2f' % (p['id'], p['eyes'], *f, L))
json.dump(out, open(r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8\iris_%s.json' % tag, 'w'), indent=1)
