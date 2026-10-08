"""lash_grid.py: her lash cards (lash_cards.json from lash_uv.py) as grids: each card's quads, its rows (from the lid
outward) and columns (along the lid), each grid point's UV and 3D place; which UV region each card uses; the cards'
length in mm from root row to tip row. Writes lash_grid.json for lash_paint.py."""
import json
import os
from collections import defaultdict

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
J = json.load(open(os.path.join(D, 'lash_cards.json')))
faces = J['faces']
eyes = np.array(J['eyes'])
# (points: a mesh point can carry several UVs: key by (point, uv) rounded)
adj = defaultdict(set)
uv_of, co_of = {}, {}
for f in faces:
    n = len(f['v'])
    keys = [(f['v'][i], round(f['uv'][i][0], 5), round(f['uv'][i][1], 5)) for i in range(n)]
    for i, k in enumerate(keys):
        uv_of[k] = f['uv'][i]
        co_of[k] = f['co'][i]
        adj[k].add(keys[(i + 1) % n])
        adj[k].add(keys[(i - 1) % n])
# components in UV
seen, comps = set(), []
for k in adj:
    if k in seen:
        continue
    stack, comp = [k], []
    seen.add(k)
    while stack:
        a = stack.pop()
        comp.append(a)
        for b in adj[a]:
            if b not in seen:
                seen.add(b)
                stack.append(b)
    comps.append(comp)
print(len(comps), 'cards;', len(faces), 'faces;', [len(c) for c in comps], 'points each; quads:', sorted(set(len(f['v']) for f in faces)))
out = []
for ci, comp in enumerate(comps):
    U = np.array([uv_of[k] for k in comp])
    C = np.array([co_of[k] for k in comp]) * 1000.0                 # mm
    # (which eye: nearest centre)
    e = int(np.argmin([np.linalg.norm(C.mean(0) / 1000 - c) for c in eyes])) if len(eyes) else -1
    dist = np.linalg.norm(C / 1000 - eyes[e], axis=1) * 1000 if e >= 0 else np.zeros(len(C))
    # corners: valence-2 points of the grid
    val = np.array([len(adj[k]) for k in comp])
    print('card %d: %d points, UV x %.3f..%.3f y %.3f..%.3f, eye %d, 3D z %.1f..%.1f mm, dist from eye centre %.1f..%.1f mm, '
          'valence counts %s' % (ci, len(comp), U[:, 0].min(), U[:, 0].max(), U[:, 1].min(), U[:, 1].max(), e, C[:, 2].min(),
                                  C[:, 2].max(), dist.min(), dist.max(), dict(zip(*np.unique(val, return_counts=True)))))
    out.append({'uv': U.tolist(), 'co': C.tolist(), 'eye': e, 'dist': dist.tolist(),
                'adj': [[comp.index(b) for b in adj[k]] for k in comp]})
json.dump(out, open(os.path.join(D, 'lash_grid.json'), 'w'))
