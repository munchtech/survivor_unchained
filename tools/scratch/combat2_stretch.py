"""The night's stretches, as the experience lead reads them: the share of runs that dipped under half
health (and under a quarter) in each stretch, and the won rate.
usage: python combat2_stretch.py RUNS.jsonl [...]"""
import json, sys

STRETCHES = [(0, 2), (2, 7), (7, 10), (10, 12), (12, 15), (15, 17), (17, 20), (20, 25), (25, 28), (28, 30)]

for f in sys.argv[1:]:
    runs = [json.loads(l) for l in open(f) if l.strip()]
    won = sum(r["Won"] for r in runs) / len(runs)
    row_half, row_q = [], []
    for a, b in STRETCHES:
        n = h = q = 0
        for r in runs:
            mins = r["ByMinute"]
            # Minute m's record covers (m-1, m]: stretch [a, b) is records a+1 .. b.
            lows = [mins[m - 1]["LowHp"] for m in range(a + 1, b + 1) if m - 1 < len(mins)]
            if not lows:
                continue
            n += 1
            lo = min(lows)
            h += lo < 0.5
            q += lo < 0.25
        row_half.append(f"{a}-{b} {100 * h // max(1, n)}%")
        row_q.append(f"{100 * q // max(1, n)}%")
    print(f"{f}: won {100 * won:.0f}% ({len(runs)})")
    print("   under half:    " + "  ".join(row_half))
    print("   under quarter: " + "  ".join(f"{s.split()[0]} {x}" for s, x in zip(row_half, row_q)))
