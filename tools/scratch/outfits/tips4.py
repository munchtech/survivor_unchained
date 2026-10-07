"""The areola from her paint: on each breast's front half, the vertices whose paint is darker
than the breast's own skin, their centre, and the sharpest bump within 1.5 cm of it (the tip).
Mirrors what marks_section.py will do in the game.   python tips4.py <heroine.glb>"""
import sys

import numpy as np

from glbread import Body

b = Body(sys.argv[1])
V, N, UV, J, Wt, T = b.V, b.N, b.UV, b.J, b.W, b.T
paint = np.asarray(b.image('heroine_body_paint')).astype(float) / 255.0
h, w = paint.shape[:2]


def sample(uv):
    x = np.clip(uv[:, 0] * w - 0.5, 0, w - 1.001)
    y = np.clip(uv[:, 1] * h - 0.5, 0, h - 1.001)
    x0, y0 = x.astype(int), y.astype(int)
    fx, fy = (x - x0)[:, None], (y - y0)[:, None]
    p = paint
    return (p[y0, x0] * (1 - fx) * (1 - fy) + p[y0, x0 + 1] * fx * (1 - fy) + p[y0 + 1, x0] * (1 - fx) * fy
            + p[y0 + 1, x0 + 1] * fx * fy)


lum = sample(UV) @ np.array([0.3, 0.59, 0.11])
breast = [i for i, n in enumerate(b.jnames) if 'breast' in n.lower()]
key = np.round(V * 20000).astype(np.int64)
_, kid = np.unique(key, axis=0, return_inverse=True)
kid = kid.ravel()
nk = kid.max() + 1
nsum = np.zeros((nk, 3))
ncnt = np.zeros(nk)
e = np.vstack([T[:, [a, c]] for a, c in ((0, 1), (1, 2), (2, 0))])
e = np.vstack([e, e[:, ::-1]])
ke = np.c_[kid[e[:, 0]], kid[e[:, 1]]]
_, first = np.unique(ke, axis=0, return_index=True)
for p_, q_ in e[first]:
    nsum[kid[p_]] += V[q_]
    ncnt[kid[p_]] += 1
for bi in breast:
    wb = np.where(J == bi, Wt, 0).sum(1)
    own = wb > 0.5
    along = (np.c_[V, np.ones(len(V))] @ b.ibm[bi].T)[:, 1]
    reach = along[own].max()
    cand = own & (along >= 0.5 * reach) & (b.MAT == 0)
    med = np.median(lum[cand])
    dark = cand & (lum < 0.8 * med)
    cen = V[dark].mean(0)
    # (the darkest part only: the pigment's own centre, not the shade under the breast)
    d2 = np.linalg.norm(V - cen, axis=1)
    core = dark & (d2 < 0.03)
    cen2 = V[core].mean(0) if core.any() else cen
    near = np.where(cand & (np.linalg.norm(V - cen2, axis=1) < 0.015) & (ncnt[kid] >= 3))[0]
    nn = N[near] / np.linalg.norm(N[near], axis=1)[:, None]
    score = -((nsum[kid[near]] / ncnt[kid[near]][:, None] - V[near]) * nn).sum(1)
    tip = V[near[np.argmax(score)]]
    print(b.jnames[bi], 'dark n', int(dark.sum()), 'centre', cen.round(4), 'core centre', cen2.round(4), 'tip', tip.round(4),
          'tip to centre %.4f' % np.linalg.norm(tip - cen2))
    for name, c in (('pigment centre', cen2), ('tip', tip)):
        r = np.linalg.norm(V[dark] - c, axis=1)
        print('   from the %s: dark vertices at %s cm (50/90/100 pct)' % (name, (np.percentile(r, [50, 90, 100]) * 100).round(2)))
    rr = np.linalg.norm(V - tip, axis=1)
    prof = []
    for lo in np.arange(0, 0.04, 0.004):
        sel = cand & (rr >= lo) & (rr < lo + 0.004)
        if sel.any():
            prof.append('%.1f:%.2f' % (lo * 100, float(lum[sel].mean())))
    print('   lum by 4 mm ring from the tip (breast median %.3f):' % med, ' '.join(prof))
