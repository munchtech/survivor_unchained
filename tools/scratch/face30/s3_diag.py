"""Face 30 S3: where the hair inside her body is (one frame of a hairdump run): height, how far behind the chain,
along-card v, swing weight, tie or not.   python s3_diag.py RUN_DIR [frame]"""
import os, sys, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "face29"))
from posed_clip import load, Surf
run = sys.argv[1]; kf = int(sys.argv[2]) if len(sys.argv) > 2 else 0
S, C, ks = load(run)
raw = np.fromfile(os.path.join(run, ks[kf]), np.float32)
o = 1; pos = {}
for s in S: pos[s["i"]] = raw[o:o + 3 * s["n"]].reshape(-1, 3).astype(np.float64); o += 3 * s["n"]
ch = raw[o:].reshape(-1, 8, 3).astype(np.float64)
hair = [s for s in S if s["kind"] == "hair" and not s["cap"]]
body = [s for s in S if s["kind"] == "body" and s["name"] == "Heroine"][0]
T = pos[body["i"]][body["I"][:, [0, 2, 1]]]
sf = Surf(T)
for s in hair:
    P = pos[s["i"]]; d = sf.sd(P)
    m = d < -0.003
    print(f"{s['name']} {s['mat']} tie={s['tie']} n={s['n']} inside>3mm {m.sum()}")
    if not m.any(): continue
    Q = P[m]
    print("  y (up) range %.3f..%.3f  z range %.3f..%.3f  x range %.3f..%.3f" % (Q[:, 1].min(), Q[:, 1].max(), Q[:, 2].min(), Q[:, 2].max(), Q[:, 0].min(), Q[:, 0].max()))
    print("  uvy (1 root .. 0 tip?) pct 10/50/90:", np.percentile(s["uvy"][m], [10, 50, 90]).round(2), " uv2y:", np.percentile(s["uv2y"][m], [10, 50, 90]).round(2))
    h, e = np.histogram(Q[:, 1], bins=8)
    print("  by height:", ", ".join(f"{(e[i]+e[i+1])/2:.2f}:{h[i]}" for i in range(8)))
    print("  depth pct 50/90:", (np.percentile(-d[m][np.isfinite(d[m])], [50, 90]) * 1000).round(1))
print("chain pts:", np.round(ch[0], 3).tolist())
# the tie and the lowest hair against the chain: how far each is from the chain's nearest segment
pts = ch[0]
for s in hair:
    if not s["tie"]: continue
    P = pos[s["i"]]
    best = np.full(len(P), 9.0)
    for i in range(7):
        a, ab = pts[i], pts[i + 1] - pts[i]; u = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
        best = np.minimum(best, np.linalg.norm(P - (a + u[:, None] * ab), axis=1))
    print(s["name"], "tie: centre", P.mean(0).round(3), "dist to chain mm min/med/max", (np.percentile(best, [0, 50, 100]) * 1000).round(1))
    print("   tie sd to body pct 0/50/100 mm", (np.percentile(np.nan_to_num(sf.sd(P), posinf=0.015), [0, 50, 100]) * 1000).round(1))
