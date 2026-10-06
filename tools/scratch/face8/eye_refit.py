"""eye_refit.py TAG: each eye swatch put right by its face's render over portrait (iris_TAG.json, iris_fit's): the
dye scaled per channel by its inverse (the response is near straight at these levels, its veil near nothing).
Swatches no portrait measures take the faces' mean correction. MAP renames a face's swatch (its own, new)."""
import json
import sys
import numpy as np
from iris_sample import lin, hexc

tag = sys.argv[1]
SC = r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8'
W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2'
MAP = {}
DAMP = {'sloe': 0.5, 'umber': 0.5, 'peat': 0.5, 'chestnut': 0.5}
F = json.load(open(SC + r'\iris_%s.json' % tag))
looks = json.load(open(W + r'\godot\data\content\looks.json', encoding='utf-8'))
sw = {e['id']: e for e in looks['heroes']['female']['eyes']}


def hx(h):
    return lin(np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)]))


fs = []
for k, v in F.items():
    ri, rc, gi, gc = (np.array(v[x]) for x in ('ref_iris', 'ref_cheek', 'game_iris', 'game_cheek'))
    f = (gi / gc) / (ri / rc)
    fs.append(f)
    src = sw[v['eyes']]
    if not src['color']:
        continue
    sid = MAP.get(k, v['eyes'])
    fk = f ** DAMP.get(sid, 1.0)
    print('%-9s %-9s iris %s ring %s   (over %s)' % (k, sid, hexc(hx(src['color']) / fk), hexc(hx(src['ring']) / fk), np.round(f, 2)))
m = np.exp(np.mean(np.log(fs), 0))
print('mean correction', np.round(m, 2))
for sid in ('wolf', 'cornflower', 'heather'):
    print('%-9s %-9s iris %s ring %s' % ('-', sid, hexc(hx(sw[sid]['color']) / m), hexc(hx(sw[sid]['ring']) / m)))
