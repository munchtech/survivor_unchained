"""eyecal.py TAG [iris_light]: her irises as the game shows them, dyed through a range (TAG_eyecal_NN.png, the colours
shots_v8.ps1 cycles), against the albedo given: each channel's curve, and from it the dyes the presets' eyes need
for their irises to stand to her cheek as their portraits' do to hers (her own as the light's measure)."""
import json
import sys
import numpy as np
from iris_sample import measure, lin, hexc

tag = sys.argv[1]
G = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2\godot\.shots'
S4 = r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face4'
CAL = 'paint,#0c0c0c,#1a1a1a,#2a2a2a,#3c3c3c,#565656,#787878,#a0a0a0,#3a2014,#20304a,#304a24,#6a3a1c,#4a6a8a,#8a6a4a'.split(',')
LIGHT = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0           # (iris_light as the calibration was shot)
CROP = [560, 100, 1260, 900]


def hx2lin(h):
    return lin(np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)]))


def mean_iris(r):
    return (hx2lin(r["r"]["iris"]) + hx2lin(r["l"]["iris"])) / 2


rows = []
for i, c in enumerate(CAL):
    r = measure(G + r'\%s_eyecal_%02d.png' % (tag, i), CROP)
    if r is None or r["r"] is None or r["l"] is None:
        print(i, c, "no eyes")
        continue
    m = mean_iris(r)
    rows.append((c, m, hx2lin(r["cheek"])))
    print("%-8s -> %s (%s / %s) cheek %s" % (c, hexc(m), r["r"]["iris"], r["l"]["iris"], r["cheek"]))
greys = [(hx2lin(c)[0] * LIGHT, m) for c, m, _ in rows if c != 'paint' and c[1:3] == c[3:5] == c[5:7]]
greys.sort()
A = np.array([0.0] + [g for g, _ in greys])
M = np.array([[0.0, 0.0, 0.0]] + [m for _, m in greys])
# (what is added whatever the dye: the cornea's sheen, the light off the iris's own shape)
print("veil (measured at black, extrapolated):", np.round(M[1] - (M[2] - M[1]) / (A[2] - A[1]) * A[1], 4))


def albedo_for(target):
    """Each channel's albedo (after iris_light) that the game shows as `target` (linear), by the greys' curves."""
    return np.array([np.interp(target[k], M[1:, k], A[1:]) for k in range(3)])


# The coloured dyes: what the curves predict against what was shown (do the channels keep apart?)
for c, m, _ in rows:
    if c == 'paint' or c[1:3] == c[3:5] == c[5:7]:
        continue
    pred = np.array([np.interp(hx2lin(c)[k] * LIGHT, A[1:], M[1:, k]) for k in range(3)])
    print("check %s: shown %s, the greys' curves say %s" % (c, hexc(m), hexc(pred)))
cheek_game = np.median([ch for _, _, ch in rows], 0)
refs = json.load(open(r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8\iris_refs.json'))
ref = {k.replace('\\', '/').split('/')[-1].split('_')[0]: v for k, v in refs.items()}
cheek_her = hx2lin(ref['her']['cheek'])
USE = {'moss': ['her'], 'frost': ['highborn', 'fey'], 'flint': ['vixen', 'hardwon'], 'sloe': ['sunborn', 'moonlit'],
       'peat': ['doe', 'saffron'], 'hazel': ['wildling']}
out = {}
for eye, who in USE.items():
    tgt = np.mean([(hx2lin(ref[w]['r']['iris']) + hx2lin(ref[w]['l']['iris'])) / 2 / cheek_her * cheek_game for w in who], 0)
    a = albedo_for(tgt)
    out[eye] = a
    print("%-6s portrait iris over her cheek -> game %s; albedo %s (sRGB %s)" % (eye, hexc(tgt), np.round(a, 4), hexc(a)))
paint = [m for c, m, _ in rows if c == 'paint']
if paint:
    a_now = albedo_for(paint[0])
    gain = out['moss'] @ [0.2126, 0.7152, 0.0722] / (a_now @ [0.2126, 0.7152, 0.0722])
    print("paint as painted shows %s (albedo %s): for moss's target, iris_light x %.3f" % (hexc(paint[0]), np.round(a_now, 4), gain))
json.dump({k: v.tolist() for k, v in out.items()}, open(r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face8\eyecal_%s.json' % tag, 'w'))
