"""lash_rows.py: each lash card (lash_grid.json) ordered as a grid: rows from the lid (root) outward, columns along
the lid; prints each card's length (mm, root row to tip row, by column) and writes lash_rows.json:
[{uv: [rows][cols][2], co: [rows][cols][3], eye, upper}]."""
import json
import os

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
cards = json.load(open(os.path.join(D, 'lash_grid.json')))
out = []
for ci, c in enumerate(cards):
    adj = [set(a) for a in c['adj']]
    n = len(adj)
    corners = [i for i in range(n) if len(adj[i]) == 2]
    on_edge = {i for i in range(n) if len(adj[i]) < 4}

    def side(a, nxt):
        path, prev, cur = [a], a, nxt
        while True:
            path.append(cur)
            if cur in corners and cur != a:
                return path
            step = [b for b in adj[cur] if b in on_edge and b != prev and b not in path]
            if not step:
                return path
            prev, cur = cur, step[0]
    c0 = corners[0]
    s1, s2 = (side(c0, b) for b in adj[c0])
    long_side, short_side = (s1, s2) if len(s1) >= len(s2) else (s2, s1)
    rows = [long_side]
    used = set(long_side)
    while len(rows) < len(short_side):
        nxt = []
        for p in rows[-1]:
            up = [b for b in adj[p] if b not in used]
            nxt.append(up[0] if up else None)
        if None in nxt:
            break
        rows.append(nxt)
        used |= set(nxt)
    dist = np.array(c['dist'])
    if dist[rows[-1]].mean() < dist[rows[0]].mean():
        rows = rows[::-1]                                   # (root row first: nearest the eye)
    co = np.array(c['co'])
    uv = np.array(c['uv'])
    G = np.array(rows)
    upper = co[G[0], 2].mean() > np.array([cc['co'] for cc in cards if cc['eye'] == c['eye']], dtype=object).shape and \
        co[:, 2].mean() > np.mean([np.array(cc['co'])[:, 2].mean() for cc in cards if cc['eye'] == c['eye']])
    length = np.linalg.norm(co[G[-1]] - co[G[0]], axis=1)
    seg = np.linalg.norm(np.diff(co[G], axis=0), axis=2).sum(0)
    print('card %d (%s, eye %d): %d rows x %d cols; root-to-tip %s mm (along the rows %s); root row length %.1f mm' % (
        ci, 'upper' if upper else 'lower', c['eye'], G.shape[0], G.shape[1], np.round(length, 1), np.round(seg, 1),
        np.linalg.norm(np.diff(co[G[0]], axis=0), axis=1).sum()))
    out.append({'uv': uv[G].tolist(), 'co': co[G].tolist(), 'eye': c['eye'], 'upper': bool(upper)})
json.dump(out, open(os.path.join(D, 'lash_rows.json'), 'w'))
