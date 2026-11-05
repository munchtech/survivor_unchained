"""Her turns, measured from a --fig8 run's TURN lines (godot/src/Game/TurnRun.cs; H6, owner note N27).

    python tools/combat/turn_measure.py LOG

For the 180 (6 s), the 90 (7 s) and the figure-eight's 45-degree steps: ms until her facing is within 10 degrees
of the stick, ms until her velocity is, her lowest speed, the worst angle between her facing and her travel while
she moves (above 90: running backwards, a moonwalk), ms spent over 45 and over 90 degrees, her peak lean and when
70% of it has come, the run blend's speed against her ground speed, and the camera's yaw over the whole run.
"""
import math
import sys


def d(a, b):
    return abs((a - b + 180) % 360 - 180)


rows = []
for line in open(sys.argv[1], encoding="utf-8", errors="replace"):
    if not line.startswith("TURN "):
        continue
    w = line.split()
    r = {"t": float(w[1])}
    for i in range(2, len(w) - 1, 2):
        try:
            r[w[i]] = float(w[i + 1])
        except ValueError:
            r[w[i]] = float("nan")
    rows.append(r)
if not rows:
    sys.exit("no TURN lines")


def turn(at, until):
    seg = [r for r in rows if at <= r["t"] < until]
    want = seg[-1]["stick"]
    def first(key):
        for r in seg:
            if d(r[key], want) <= 10 and all(d(q[key], want) <= 10 for q in seg if q["t"] >= r["t"] and q["t"] < r["t"] + 0.1):
                return (r["t"] - at) * 1000
        return float("nan")
    mov = [r for r in seg if r["sp"] > 0.4]
    skew = [d(r["face"], r["vel"]) for r in mov]
    dt = [(seg[i + 1]["t"] - seg[i]["t"]) for i in range(len(seg) - 1)] + [0]
    over = lambda k: sum(dt[i] for i, r in enumerate(seg) if r["sp"] > 0.4 and d(r["face"], r["vel"]) > k) * 1000
    pk = max(seg, key=lambda r: abs(r["bank"]))
    rise = next((r for r in seg if abs(r["bank"]) >= 0.7 * abs(pk["bank"])), pk) if abs(pk["bank"]) > 0.5 else seg[0]
    gap = max(abs(r["anim"] - r["sp"]) for r in seg)
    return dict(face=first("face"), vel=first("vel"), minsp=min(r["sp"] for r in seg), top=seg[0]["sp"],
                skew=max(skew) if skew else 0, over45=over(45), over90=over(90),
                bank=abs(pk["bank"]), bank_ms=(rise["t"] - at) * 1000, animgap=gap)


def show(name, m):
    print(f"{name}: facing<=10deg {m['face']:.0f} ms | velocity<=10deg {m['vel']:.0f} ms | speed {m['top']:.2f} -> min {m['minsp']:.2f} m/s"
          f" | facing-vs-travel max {m['skew']:.0f} deg, >45 {m['over45']:.0f} ms, >90 {m['over90']:.0f} ms"
          f" | lean peak {m['bank']:.1f} deg, 70% of it by {m['bank_ms']:.0f} ms | run blend speed off ground speed by up to {m['animgap']:.2f} m/s")


show("180", turn(6.0, 7.0))
show("90 ", turn(7.0, 8.0))
steps = [turn(1 + 0.25 * i, 1.25 + 0.25 * i) for i in range(16)]
avg = {k: sum(s[k] for s in steps if not math.isnan(s[k])) / len(steps) for k in steps[0]}
show("45 (mean of 16 loop steps)", avg)
cams = [r["cam"] for r in rows]
print(f"camera yaw over the run: {min(cams):.2f} .. {max(cams):.2f} deg (range {max(cams) - min(cams):.2f})")
