"""hcsum.py LOG [K0 K1]: a HAIRCLEAR log summed up: worst signed distance (cm) over frames K0-K1 for segments 1-2 (the tie)
and 3-7, the frames under -2 cm (segs 3-7), and HAIRMOVE: largest jump, frames over 8 cm, frames over 2x both neighbours."""
import sys, re
F = "C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/91211d34-e079-4956-a2a0-7b52c04594a8/scratchpad/f19/"
L = open(F + sys.argv[1], errors="ignore").read().splitlines(); K0, K1 = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (0, 999)
seg = {}; mv = {}
for l in L:
    m = re.match(r"HAIRCLEAR k=(\d+) segs (.*)", l)
    if m: seg[int(m.group(1))] = [float(v) for v in m.group(2).split()]
    m = re.match(r"HAIRMOVE k=(\d+) max=([\d.]+)", l)
    if m: mv[int(m.group(1))] = float(m.group(2))
ks = [k for k in sorted(seg) if K0 <= k <= K1]
w12 = min(min(seg[k][:2]) for k in ks); w37 = min((min(seg[k][2:]), k) for k in ks)
bad = ["k%d:%.1f(s%d)" % (k, min(seg[k][2:]), 3 + seg[k][2:].index(min(seg[k][2:]))) for k in ks if min(seg[k][2:]) < -2]
mk = [k for k in sorted(mv) if K0 <= k <= K1]
big = max((mv[k], k) for k in mk) if mk else (0, 0)
over = [k for k in mk if mv[k] > 8]; spike = [k for k in mk if k - 1 in mv and k + 1 in mv and mv[k] > 2 * max(mv[k - 1], mv[k + 1]) and mv[k] > 2]
print("%s k%d-%d: tie segs1-2 worst %.1f | segs3-7 worst %.1f (k%d) | under -2: %s | move max %.1f (k%d), >8: %s, spikes: %s" % (sys.argv[1], ks[0], ks[-1], w12, w37[0], w37[1], " ".join(bad) or "none", big[0], big[1], over or "none", spike or "none"))
