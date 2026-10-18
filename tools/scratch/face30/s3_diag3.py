"""Face 30 S3: the swinging hair's middle against its chain, along it (a hairdump frame).  python s3_diag3.py RUN [frame]"""
import os, sys, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "face29"))
from posed_clip import load
run = sys.argv[1]; kf = int(sys.argv[2]) if len(sys.argv) > 2 else 0
S, C, ks = load(run)
raw = np.fromfile(os.path.join(run, ks[kf]), np.float32); o = 1; pos = {}
for s in S: pos[s["i"]] = raw[o:o + 3 * s["n"]].reshape(-1, 3).astype(np.float64); o += 3 * s["n"]
ch = raw[o:].reshape(-1, 8, 3)[0]
for s in S:
    if s["kind"] != "hair": continue
    a = np.fromfile(os.path.join(run, f"s{s['i']:02d}.attr"), np.float32).reshape(-1, 5)
    sw = a[:, 2] > 0.5
    if not sw.any(): continue
    P = pos[s["i"]]
    for i in range(8):
        m = sw & (np.abs(a[:, 1] * 7 - i) < 0.3)
        if m.any(): print(f"{s['name']} {s['mat']} pt{i}: hair mean {P[m].mean(0).round(3)}  chain {ch[i].round(3)}  gap {np.linalg.norm(P[m].mean(0)-ch[i])*1000:.0f} mm")
