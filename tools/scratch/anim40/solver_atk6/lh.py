"""solver 6: left hand vs pelvis midline (lateral axis = thigh_r->thigh_l, horizontal), cm. lh.py clip... [-v]"""
import sys, json, hashlib
from pathlib import Path
import numpy as np
ANIM = Path(__file__).resolve().parents[3] / 'anim'
sys.path.insert(0, str(ANIM))
import audit as A  # noqa
sk = A.Skeleton.load(A.DATA / 'heroine_skeleton.json'); I = sk.index
arms = json.load(open(ANIM / 'data/arms_local.json'))
v = np.array(arms['viking_axe@hand_l']['v']); r = np.linalg.norm(v, axis=1); far = v[r > r.max() - 0.12].mean(0)
verb = '-v' in sys.argv
for n in [a for a in sys.argv[1:] if a != '-v']:
    d, rot, pos = A.load(ANIM / 'out/clips' / f'{n}.json', sk); g, p = sk.fk(rot, pos)
    pel = p[:, I['pelvis']]; lat = p[:, I['thigh_l']] - p[:, I['thigh_r']]; lat[:, 1] = 0
    lat /= np.linalg.norm(lat, axis=1)[:, None]
    fwd = np.cross(lat, [0, 1, 0]); fwd *= -1 if np.mean(fwd[:, 2]) < 0 else 1
    hl = p[:, I['hand_l']] - pel
    x = (hl * lat).sum(1) * 100; z = (hl * fwd).sum(1) * 100; y = hl[:, 1] * 100
    legs = [t for t in d['tracks'] if t['bone'].startswith(('pelvis', 'thigh', 'calf', 'foot', 'ball', 'root'))]
    h = hashlib.md5(json.dumps(legs).encode()).hexdigest()[:10]
    kn = ((p[:, I['middle_01_l']] - pel) * lat).sum(1) * 100; tip = ((p[:, I['middle_04_leaf_l']] - pel) * lat).sum(1) * 100
    f = int(np.argmax(z))
    s = f"{n:22s} wrist min x {x.min():5.1f} (f{int(np.argmin(x))}) knuckle min {kn.min():5.1f} (f{int(np.argmin(kn))}) tip min {tip.min():5.1f}  fwd end f{f}: x {x[f]:.1f} y {y[f]:.0f} z {z[f]:.0f}  legs {h}"
    if 'axes' in n:
        head = p[:, I['hand_l']] + np.array([A.qrot(g[i, I['hand_l']], far) for i in range(len(p))]) - pel
        hx = (head * lat).sum(1) * 100; hz = (head * fwd).sum(1) * 100; hy = head[:, 1] * 100
        tl = ((p[:, I['calf_l']] - pel) * lat).sum(1) * 100
        s += f"  | axe head min x {hx.min():.1f}, x-knee_l min {(hx - tl).min():.1f}"
    print(s)
    if verb:
        for i in range(len(p)):
            line = f"   f{i:2d} kn x{kn[i]:5.1f} hand x{x[i]:5.1f} y{y[i]:5.0f} z{z[i]:5.0f}"
            if 'axes' in n: line += f"  head x{hx[i]:5.1f} y{hy[i]:5.0f} z{hz[i]:5.0f} kneeL x{tl[i]:5.1f}"
            print(line)
