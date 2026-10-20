"""solver 4: per-frame arm contact (mm) for clips. python pf.py CLIP [CLIP..] [--side r] [--outfits reaver,warden] [--folder DIR]
Columns per frame: up fa hd br (skin), then max(up,fa,hd) per outfit."""
import sys, argparse, time
from pathlib import Path
import numpy as np
ANIM = Path(__file__).resolve().parents[3] / 'anim'
sys.path.insert(0, str(ANIM))
import motion as M
ap = argparse.ArgumentParser(); ap.add_argument('clips', nargs='+'); ap.add_argument('--side', default='r')
ap.add_argument('--outfits', default='reaver'); ap.add_argument('--folder')
a = ap.parse_args()
outs = tuple(o for o in a.outfits.split(',') if o)
m = M.Measure(M.Body.heroine(jiggle=True), outs)
mw = None
if 'warden' in outs:
    mw = M.Measure(M.Body.heroine(outfit=None, jiggle=True), ()); mw.b.jiggle.amount, mw.b.jiggle.squash = 0.55, 0.0; mw.cover = m.cover
for c in a.clips:
    b = m.b; clip = b.clip(c, Path(a.folder) if a.folder else None)
    pts, along, _ = m.arm[a.side]
    zone = np.where(along < 0.35, 0, np.where(along < 1, 1, np.where(along < 2, 2, 3)))
    rows = {}
    for tag, mm in [('free', m)] + ([('plate', mw)] if mw else []):
        for f, G in enumerate(mm.b.frames(clip)):
            P = mm.b.pose(G); dist, al, hit, brst, near = mm.contact(P)[a.side]
            ok = np.isfinite(dist)
            def z(d):
                r = []
                for zi in (1, 2, 3):
                    mk = (zone == zi) & ok; r.append(max(0, float(d[mk].max())) * 1000 if mk.any() else 0)
                mb = ok & brst; r.append(max(0, float(d[mb].max())) * 1000 if mb.any() else 0); return r
            d = -dist.copy(); d[~ok] = -1
            row = rows.setdefault(f, {})
            if tag == 'free':
                row['skin'] = z(d)
            for o in outs:
                if (o == 'warden') != (tag == 'plate'): continue
                dd = d.copy(); cov = m.cover[o]; dd[ok] += cov[pts[ok]] + cov[np.maximum(near[ok], 0)]
                row[o] = max(z(dd)[:3])
    print(f'{c} side {a.side}:  f  up  fa  hd  br | ' + ' '.join(o[:3] for o in outs))
    for f in sorted(rows):
        s = rows[f]['skin']; print(f'  {f:3d} ' + ' '.join(f'{x:3.0f}' for x in s) + ' | ' + ' '.join(f"{rows[f].get(o, 0):3.0f}" for o in outs))
