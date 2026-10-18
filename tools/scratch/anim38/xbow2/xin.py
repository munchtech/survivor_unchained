"""Which crossbow points are in her (hand_r space, mm) at frames: python xin.py clip f... [--tag=]"""
import sys; from pathlib import Path
W = Path(__file__).resolve().parents[4]; sys.path.insert(0, str(W / "tools/anim"))
import numpy as np
import armscheck as A
ck = A.Checker(); b = ck.b
a = [x for x in sys.argv[1:] if not x.startswith("--")]
c = b.clip(a[0], W / "tools/anim/out" / ("anim38_her" + next((x[6:] for x in sys.argv if x.startswith("--tag=")), ""))); Gs = b.frames(c)
K = "crossbow@hand_r"
for f in map(int, a[1:]):
    G = Gs[f]; P = b.pose(G)
    for s in "lr":
        ck.m.arm[s][2].pose(P)
    surf = ck.m.arm["r"][2]; M = G[ck.I["hand_r"]]
    Q = ck.pts[K] @ M[:3, :3].T + M[:3, 3]
    d, near = surf.signed(P, Q, k=8)
    dep = np.where(np.isfinite(d), -d * 1000, 0)
    i = np.nonzero(dep > 1)[0]
    print(f"f{f}: {len(i)} pts > 1 mm (unconfirmed sign)")
    for j in i[np.argsort(-dep[i])][:6]:
        print("   ", np.round(ck.pts[K][j] * 1000).tolist(), f"{dep[j]:.1f}", ck.where(near[j]))
