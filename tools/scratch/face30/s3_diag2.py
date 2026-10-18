import os, sys, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "face29"))
from posed_clip import load
run = sys.argv[1]; kf = int(sys.argv[2])
S, C, ks = load(run)
raw = np.fromfile(os.path.join(run, ks[kf]), np.float32); o = 1; pos = {}
for s in S: pos[s["i"]] = raw[o:o + 3 * s["n"]].reshape(-1, 3).astype(np.float64); o += 3 * s["n"]
ch = raw[o:].reshape(-1, 8, 3)
for s in S:
    P = pos[s["i"]]
    for y in (1.85, 1.6, 1.43):
        m = np.abs(P[:, 1] - y) < 0.01
        if m.any(): print(f"{s['name'][:14]:14s} {s['kind']:4s} tie={s['tie']} y{y}: x {P[m,0].min():.3f}..{P[m,0].max():.3f} z {P[m,2].min():.3f}..{P[m,2].max():.3f} (n {m.sum()})")
print(np.round(ch[0], 3))
