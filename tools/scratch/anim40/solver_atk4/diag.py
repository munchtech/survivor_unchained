"""where the right arm's worst points go in, at one frame: along (1=elbow), hit part, the point in chest space (cm)"""
import sys
from pathlib import Path
import numpy as np
ANIM = Path(__file__).resolve().parents[3] / 'anim'
sys.path.insert(0, str(ANIM))
import motion as M
clipn, folder, fr = sys.argv[1], sys.argv[2], int(sys.argv[3]); side = sys.argv[4] if len(sys.argv) > 4 else 'r'
m = M.Measure(M.Body.heroine(jiggle=True), ())
b = m.b; clip = b.clip(clipn, folder if folder != '-' else None)
Gs = b.frames(clip); G = Gs[fr]; P = b.pose(G)
dist, along, hit, brst, near = m.contact(P)[side]
pts = m.arm[side][0]
ok = np.isfinite(dist); d = np.where(ok, -dist, -1)
I = b.sk.index
o = np.argsort(-d)[:400]
o = o[d[o] > 0.02]
print('n>20mm', len(o))
sh = None
for lo, hi in ((0.35, 0.6), (0.6, 0.8), (0.8, 1.0), (1.0, 2.0)):
    mk = (along[o] >= lo) & (along[o] < hi)
    if mk.any():
        oo = o[mk]
        print(f'along {lo}-{hi}: n {len(oo)} max {1000*d[oo].max():.0f} breast {brst[oo].mean():.2f} parts', sorted(set(b.parts[h] for h in hit[oo])))
        q = P[pts[oo]].mean(0); print('   at (world cm)', np.round(q*100).astype(int), 'nearest skin', np.round(P[near[oo]].mean(0)*100).astype(int))
