"""A --perf-flip run read both ways (as flip.py), from any folder and over a stretch of it.

    python tools/perf/flipwin.py DIR RUN [T0 T1 [STAGES]]   (STAGES: Prologue stage numbers, e.g. 2,3)
"""
import csv, os, statistics, sys

d, run = sys.argv[1], sys.argv[2]
t0, t1 = (float(sys.argv[3]), float(sys.argv[4])) if len(sys.argv) > 4 else (0, 1e9)
stages = set(int(x) for x in sys.argv[5].split(",")) if len(sys.argv) > 5 else None
rows = list(csv.DictReader(open(os.path.join(d, run + ".csv"), encoding="utf-8")))
blocks, cur, state, since = [], [], None, 0
for r in rows:
    s = int(float(r["flip"]))
    if s != state:
        if cur: blocks.append((state, cur))
        cur, state, since = [], s, 0
    since += 1
    if since > 6 and t0 <= float(r["t"]) < t1 and (stages is None or int(float(r["stage"])) in stages):
        cur.append(r)
if cur: blocks.append((state, cur))
out = [f"{run} t {t0:.0f}-{min(t1, float(rows[-1]['t'])):.0f}:"]
for c in ["ms", "gpu", "render_cpu", "main", "draws", "shadow_draws", "primitives"]:
    ins = [float(r[c]) for s, b in blocks if s == 0 for r in b]
    outs = [float(r[c]) for s, b in blocks if s == 1 for r in b]
    if not ins or not outs: continue
    pairs = [statistics.mean(float(r[c]) for r in blocks[i + 1][1]) - statistics.mean(float(r[c]) for r in blocks[i][1])
             for i in range(len(blocks) - 1) if blocks[i][0] == 0 and blocks[i][1] and blocks[i + 1][1]]
    q = statistics.quantiles(pairs, n=4) if len(pairs) >= 4 else [0, 0, 0]
    mi, mo = statistics.mean(ins), statistics.mean(outs)
    k = 1e6 if c == "primitives" else 1
    out.append(f"  {c:12} in {mi / k:8.3f} out {mo / k:8.3f} out-in {(mo - mi) / k:+8.3f} (median {statistics.median(pairs) / k:+.3f}, IQR {q[0] / k:+.3f}..{q[2] / k:+.3f}, n {len(pairs)})")
print("\n".join(out))
