"""Blade readability by pixels: a full shoot against its --hide-blade twin (same seed, fixed fps).
Usage: blade_contrast.py DIR_FULL DIR_HIDDEN NLEGS [--thr 25 --px 40 --dip 3]
Per frame, count pixels whose luminance differs by more than --thr; a leg frame is 'low' under --px pixels."""
import sys, os, argparse
import numpy as np
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("full"); ap.add_argument("hidden"); ap.add_argument("nlegs", type=int)
ap.add_argument("--thr", type=float, default=25); ap.add_argument("--px", type=int, default=40); ap.add_argument("--dip", type=int, default=3)
a = ap.parse_args()

def turn2(d):
    p = os.path.join(d, "views.log")
    return [l.rstrip() for l in open(p, errors="replace") if l.startswith("TURN2")]

def lum(p):
    return np.asarray(Image.open(p).convert("RGB"), dtype=np.float32) @ np.array([0.299, 0.587, 0.114], dtype=np.float32)

ta, tb = turn2(a.full), turn2(a.hidden)
ok = len(ta) == len(tb) and ta == tb
if ok:
    print(f"DETERMINISM ok ({len(ta)} TURN2 lines)")
else:
    first = next((i for i, (x, y) in enumerate(zip(ta, tb)) if x != y), min(len(ta), len(tb)))
    print(f"MISMATCH first differing TURN2 line {first} (counts {len(ta)} vs {len(tb)})")

legs_fail, worst, worst_at = 0, 0, ""
for i in range(a.nlegs):
    base = 60 + 60 * i
    counts = []
    for k in range(60):
        f = f"f{base + k:08d}.png"
        pa, pb = os.path.join(a.full, "views", f), os.path.join(a.hidden, "views", f)
        if not (os.path.exists(pa) and os.path.exists(pb)):
            counts.append(None); continue
        counts.append(int((np.abs(lum(pa) - lum(pb)) > a.thr).sum()))
    have = [c for c in counts if c is not None]
    if not have:
        print(f"L{i} no frames"); continue
    low = [k for k, c in enumerate(counts) if c is not None and c < a.px]
    runs, s = [], None
    for k in range(61):
        isl = k < 60 and counts[k] is not None and counts[k] < a.px
        if isl and s is None: s = k
        if not isl and s is not None: runs.append((s, k - 1)); s = None
    lr = max((e - s + 1 for s, e in runs), default=0)
    fail = lr > a.dip
    legs_fail += fail
    if lr > worst: worst, worst_at = lr, f"L{i}+{max(runs, key=lambda r: r[1]-r[0])[0]}..+{max(runs, key=lambda r: r[1]-r[0])[1]}"
    zero = sum(1 for c in have if c == 0)
    rs = " ".join(f"+{s}..+{e}" if s != e else f"+{s}" for s, e in runs)
    print(f"L{i} min {min(have)} low {len(low)} runs [{rs}] zero {zero}{' FAIL' if fail else ''}")
print(f"BC legs_fail={legs_fail} worst_run={worst} {worst_at if worst else 'none'}")
