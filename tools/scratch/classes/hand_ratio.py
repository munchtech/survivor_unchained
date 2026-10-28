# The Hand pairs (Balance arena --pair 1, hand_measure.sh): per calling x tier, summed damage over the span with the
# Hand on / off (the same build: a mismatch is counted), its delta-method sigma, the Hand's own share of the damage
# (hand + rebuke), falls and seconds below half health per run (off/on). "all" pools tiers 1-4; "tmean" is their mean.
import json, sys, math, collections
cells = collections.defaultdict(list); bad = 0
for path in sys.argv[1:]:
    for l in open(path):
        if not l.strip(): continue
        r = json.loads(l); o, f = r['On'], r['Off']
        bad += o['Build'] != f['Build']
        x = (o['Dmg'], f['Dmg'], o['Hand'] + o['Rebuke'], f['Falls'], o['Falls'], f['Low'], o['Low'])
        cells[(r['Calling'], r['Tier'])].append(x); cells[(r['Calling'], 0)].append(x)
def stat(L):
    n = len(L); a = sum(x[0] for x in L) / n; b = sum(x[1] for x in L) / n; R = a / b
    return n, R, math.sqrt(sum((x[0] - R * x[1]) ** 2 for x in L) / max(1, n - 1)) / math.sqrt(n) / b
print(f"build mismatches {bad}")
print("calling   tier    n  ratio sigma  hand%  falls off/on  low-s off/on")
for c in sorted({k[0] for k in cells}):
    trs = []
    for t in sorted(k[1] for k in cells if k[0] == c):
        L = cells[(c, t)]; n, R, sd = stat(L)
        if t: trs.append(R)
        print(f"{c:9} {t or 'all':>4} {n:4}  {R:.3f} {sd:.3f}  {100*sum(x[2] for x in L)/sum(x[0] for x in L):4.1f}  {sum(x[3] for x in L)/n:5.2f}/{sum(x[4] for x in L)/n:5.2f}  {sum(x[5] for x in L)/n:4.0f}/{sum(x[6] for x in L)/n:4.0f}")
    print(f"{c:9} tmean       {sum(trs)/len(trs):.3f}")
