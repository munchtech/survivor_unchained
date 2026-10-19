"""Left hand to crossbow: the gap and its direction in the chest's frame, per sampled frame. python gapvec.py clip f1 f2 ..."""
import sys; from pathlib import Path
W = Path(__file__).resolve().parents[4]; sys.path.insert(0, str(W / "tools/anim"))
import numpy as np
from scipy.spatial import cKDTree
import armscheck as A
from rig import qrot, qinv
ck = A.Checker(); b = ck.b; I = b.sk.index
c = b.clip(sys.argv[1], W / "tools/anim/out/anim38_her"); Gs = b.frames(c)
grot, _ = b.sk.fk(c.rot, c.pos)
rg, _ = b.sk.rest_globals()
pts, along, _ = ck.m.arm["l"]
for f in map(int, sys.argv[2:]):
    G = Gs[f]; P = b.pose(G); Q = ck.piece_points("crossbow@hand_r", G)
    hp = pts[along >= 2]
    d, j = cKDTree(Q).query(P[hp], k=1)
    i = int(d.argmin()); v = Q[j[i]] - P[hp[i]]
    ch = grot[f, I["spine_03"]]; from rig import qmul
    cq = qmul(ch, qinv(rg[0, I["spine_03"]]))
    vc = qrot(qinv(cq), v)
    # where on the hand
    nm = np.array(b.sk.names)[b.J[hp[i], b.W[hp[i]].argmax()]]
    print(f"f{f}: gap {d[i]*1000:.1f} mm at {nm}, to the bow (chest frame, mm) {np.round(vc*1000,1).tolist()}; hand-palm pts within 15 mm: {int((d<0.015).sum())}")
