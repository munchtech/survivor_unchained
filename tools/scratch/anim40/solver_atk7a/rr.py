"""solver 7a: run-variant numbers. python rr.py CLIP frames(comma) [bf=9]
cm from the pelvis (x her left, y up, z fwd). hl/hr hands; elL elbow deg; uaL = left upper arm out from her side
(deg, frontal plane), uaF its forward swing; scr = screen x offset from the pelvis seen from the 315 cam ((x - z)*.707);
axe head pos, haz = head direction from the fist (azimuth deg, 0 fwd, + her left), hel = below horizontal."""
import sys, json, math
from pathlib import Path
import numpy as np
ANIM = Path(__file__).resolve().parents[3] / 'anim'; sys.path.insert(0, str(ANIM))
import audit as A
sk = A.Skeleton.load(A.DATA / 'heroine_skeleton.json'); I = sk.index
arms = json.load(open(ANIM / 'data/arms_local.json'))
v = np.array(arms['viking_axe@hand_r']['v']); r = np.linalg.norm(v, axis=1); head_l = v[r > r.max() - 0.12].mean(0)
_, rot0, pos0 = A.load(ANIM / 'out/clips' / f'{sys.argv[1]}.json', sk)
_, br, bp = A.load(ANIM / 'out/clips/run_reaver.json', sk)
bf = int(sys.argv[3]) if len(sys.argv) > 3 else 9
L = [j for n, j in I.items() if n in ('root', 'pelvis') or n.startswith(('thigh', 'calf', 'foot', 'ball', 'glute'))]
def ang(a, b, c):
    u, w = a - b, c - b; return math.degrees(math.acos(np.clip(u @ w / np.linalg.norm(u) / np.linalg.norm(w), -1, 1)))
for f in map(int, sys.argv[2].split(',')):
    rr, pp = rot0[f:f+1].copy(), pos0[f:f+1].copy(); rr[:, L] = br[bf, L]; pp[:, L] = bp[bf, L]
    g, p = sk.fk(rr, pp); g, p = g[0], p[0]; J = lambda n: p[I[n]]; pv = J('pelvis')
    hl = (J('hand_l') - pv) * 100; hr = (J('hand_r') - pv) * 100
    ua = J('lowerarm_l') - J('upperarm_l'); uaL = math.degrees(math.atan2(ua[0], -ua[1])); uaF = math.degrees(math.atan2(ua[2], -ua[1]))
    hd = J('hand_r') + A.qrot(g[I['hand_r']], head_l); dv = hd - J('hand_r')
    print(f"f{f}: hl {np.round(hl).astype(int)} scr {(hl[0]-hl[2])*.707:4.0f} elL {ang(J('upperarm_l'), J('lowerarm_l'), J('hand_l')):3.0f} uaL {uaL:3.0f} uaF {uaF:4.0f} | "
          f"hr {np.round(hr).astype(int)} scr {(hr[0]-hr[2])*.707:4.0f} | head {np.round((hd-pv)*100).astype(int)} scr {((hd-pv)[0]-(hd-pv)[2])*70.7:4.0f} haz {math.degrees(math.atan2(dv[0], dv[2])):4.0f} hel {-math.degrees(math.asin(dv[1]/np.linalg.norm(dv))):3.0f}")
