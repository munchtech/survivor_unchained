"""The 4.7.2 look match: what differs between two frame-matched frames, by tone.

  python tools/scratch/godot47/tone_fit.py curve REF.png NEW.png          transfer: bins of REF luma -> mean NEW luma, per channel too, and the spread
  python tools/scratch/godot47/tone_fit.py glow  ON.png OFF.png [ON2 OFF2] what glow adds (ON - OFF), by bins of OFF luma; a second pair beside it

Frames are the 1:1 PNGs compare.py cuts from the look clips (same take, same second, both engines).
"""
import sys
import numpy as np
from PIL import Image

W = np.array([0.2126, 0.7152, 0.0722], np.float32)
EDGES = [0, 0.02, 0.04, 0.06, 0.08, 0.11, 0.14, 0.18, 0.23, 0.29, 0.36, 0.45, 0.56, 0.7, 0.85, 1.01]


def load(p):
    return np.asarray(Image.open(p).convert("RGB")).astype(np.float32) / 255


def curve(ref, new):
    a, b = load(ref), load(new)
    la, lb = a @ W, b @ W
    print(f"mean luma {la.mean():.4f} -> {lb.mean():.4f} ({(lb.mean() / la.mean() - 1) * 100:+.2f}%)  MAE {np.abs(a - b).mean():.4f}  rgb {a.reshape(-1, 3).mean(0).round(4)} -> {b.reshape(-1, 3).mean(0).round(4)}")
    print("bin lo-hi | share% | ref luma | new luma | diff | diff% | sd of diff | dR dG dB")
    for lo, hi in zip(EDGES, EDGES[1:]):
        m = (la >= lo) & (la < hi)
        if m.sum() < 200:
            continue
        d = lb[m] - la[m]
        dc = (b[m] - a[m]).mean(0)
        print(f"{lo:.2f}-{hi:.2f} | {m.mean() * 100:5.1f} | {la[m].mean():.4f} | {lb[m].mean():.4f} | {d.mean():+.4f} | {d.mean() / la[m].mean() * 100:+5.1f} | {d.std():.4f} | {dc[0]:+.4f} {dc[1]:+.4f} {dc[2]:+.4f}")


def glow(pairs):
    rows = []
    for on, off in pairs:
        a, b = load(on), load(off)
        la, lb = a @ W, b @ W
        d = la - lb
        r = [f"{d.mean():+.4f}"]
        for lo, hi in zip(EDGES, EDGES[1:]):
            m = (lb >= lo) & (lb < hi)
            r.append(f"{d[m].mean():+.4f}" if m.sum() >= 200 else "   -   ")
        r.append(f"p99.9 {np.percentile(d, 99.9):+.3f} max {d.max():+.3f} min {d.min():+.3f}")
        rows.append(r)
    print("what glow adds to luma (on - off): mean | by bins of the glow-off luma " + " ".join(f"{lo:.2f}" for lo in EDGES[:-1]))
    for (on, _), r in zip(pairs, rows):
        print(" | ".join(r), "|", on)


if __name__ == "__main__":
    if sys.argv[1] == "curve":
        curve(sys.argv[2], sys.argv[3])
    else:
        a = sys.argv[2:]
        glow([(a[i], a[i + 1]) for i in range(0, len(a), 2)])
