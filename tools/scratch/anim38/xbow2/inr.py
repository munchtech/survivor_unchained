"""The left hand in hand_r's space (the crossbow's: +Y the stock, +Z its top, -X her left; mm): its skin points' extent,
the palm's centre, the wrist and the hand's axes (palm +X, fingers +Y). python inr.py clip f... [--tag=]"""
import sys; from pathlib import Path
W = Path(__file__).resolve().parents[4]; sys.path.insert(0, str(W / "tools/anim"))
import numpy as np
import armscheck as A
ck = A.Checker(); b = ck.b; I = b.sk.index
a = [x for x in sys.argv[1:] if not x.startswith("--")]
c = b.clip(a[0], W / "tools/anim/out" / ("anim38_her" + next((x[6:] for x in sys.argv if x.startswith("--tag=")), ""))); Gs = b.frames(c)
pts, along, _ = ck.m.arm["l"]
for f in map(int, a[1:]):
    G = Gs[f]; P = b.pose(G); M = G[I["hand_r"]]; Ri = M[:3, :3].T
    loc = lambda X: (X - M[:3, 3]) @ Ri.T
    hp = loc(P[pts[along >= 2]]) * 1000
    H = G[I["hand_l"]]
    ax = (H[:3, :3].T @ M[:3, :3]).T if False else (M[:3, :3].T @ H[:3, :3])
    ax = ax / np.linalg.norm(ax, axis=0)
    C = G[I["spine_03"]][:3, :3]; C = C / np.linalg.norm(C, axis=0); Rr = M[:3, :3] / np.linalg.norm(M[:3, :3], axis=0)
    rc = C.T @ Rr
    print(f"   hand_r in chest: +Y(stock) {np.round(rc[:,1],2).tolist()} +Z(top) {np.round(rc[:,2],2).tolist()}  world: +Z(top) {np.round(Rr[:,2],2).tolist()}")
    E = G[I["lowerarm_l"]][:3, 3]; fa = loc(H[:3, 3]) - loc(E); fa /= np.linalg.norm(fa)
    print(f"   forearm {np.round(fa, 2).tolist()} elbow {np.round(loc(E)*1000).tolist()}")
    print(f"f{f}: hand x {hp[:,0].min():.0f}..{hp[:,0].max():.0f} y {hp[:,1].min():.0f}..{hp[:,1].max():.0f} z {hp[:,2].min():.0f}..{hp[:,2].max():.0f}"
          f" wrist {np.round(loc(H[:3,3])*1000).tolist()} palm+X {np.round(ax[:,0],2).tolist()} fing+Y {np.round(ax[:,1],2).tolist()}")
