"""skin_ratio.py TAG: each preset's skin in the shots against hers, beside its portrait's against her portrait's
(linear light, per channel; and lightness). A ratio of 1.00 in every column: the preset's skin as true to its
portrait as hers is to hers. Run with the facefit venv's python."""
import json, os, sys
import numpy as np
from skin_sample import measure

tag = sys.argv[1]
w = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2f7b0f1283f6144a'
g = w + r'\godot\.shots'
s4 = r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face4'
crop = [660, 150, 1160, 740]
P = json.load(open(w + r'\tools\assets\heroine_face\presets.json'))
LW = np.array([0.2126, 0.7152, 0.0722])
res = {}
for p in P:
    ref = s4 + '\\refs_front\\' + p['ref'].split('/')[-1] + '.png'
    if p['id'] == 'own':
        ref = s4 + r'\from_face3\refs_her\her_23.png'
    shot = g + '\\%s_%s.png' % (tag, 'pony' if p['id'] == 'own' else 'p_' + p['id'])
    if not os.path.exists(shot):
        continue
    a, b = measure(ref), measure(shot, crop)
    if a is None or b is None:
        print(p['id'], 'no face'); continue
    res[p['id']] = (np.array(a['lin']), np.array(b['lin']), a['grain'], b['grain'])
h = res.get('own')
print('%-9s %-26s %-26s %s' % ('', 'portrait/hers (r g b L)', 'shot/hers (r g b L)', 'shot ratio / portrait ratio; grain ref/shot'))
for k, (a, b, ga, gb) in res.items():
    ra, rb = a / h[0], b / h[1]
    la, lb = (a @ LW) / (h[0] @ LW), (b @ LW) / (h[1] @ LW)
    q = rb / ra
    print('%-9s %.2f %.2f %.2f  L %.2f    %.2f %.2f %.2f  L %.2f    %.2f %.2f %.2f  L %.2f   %.3f/%.3f' % (
        k, *ra, la, *rb, lb, *q, lb / la, ga, gb))
