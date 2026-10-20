"""grid search over f8 wand-hand keys. python fs.py"""
import sys, math, json, itertools
from pathlib import Path
import numpy as np
ANIM = Path(__file__).resolve().parents[3] / 'anim'; sys.path.insert(0, str(ANIM))
import clips.actions as M
from keyed import Rig
from rig import DATA, Skeleton, qmatrix
sk = Skeleton.load(DATA / 'heroine_skeleton.json'); rig = Rig(sk, body='her'); I = sk.index
V = np.array(json.load(open(ANIM / 'data/arms_local.json'))['wand@hand_r']['v']); c = V.mean(0)
W = np.linalg.svd(V - c)[2][0]; W = W * np.sign(W @ (V[np.linalg.norm(V, axis=1).argmax()] - c))
src = open(Path(__file__).parent / 'pf_flick.py').read()
def run(fp, frames=(8,)):
    M.__dict__['FP'] = fp; exec(src, M.__dict__)
    clip = M.cast_flick(rig); g, p = sk.fk(clip.rot, clip.pos); out = []
    for f in frames:
        d = qmatrix(g[f, I['hand_r']]) @ W
        e = math.degrees(math.acos(np.clip(((p[f, I['upperarm_r']] - p[f, I['lowerarm_r']]) @ (p[f, I['hand_r']] - p[f, I['lowerarm_r']])) / np.linalg.norm(p[f, I['upperarm_r']] - p[f, I['lowerarm_r']]) / np.linalg.norm(p[f, I['hand_r']] - p[f, I['lowerarm_r']]), -1, 1)))
        out.append((d, e))
    return out
if __name__ == '__main__':
    tgt = np.array([0.05, -0.22, 0.97]); tgt /= np.linalg.norm(tgt)
    res = []
    for bx, by, ky in itertools.product((-0.9, -0.5, -0.2, 0.2), (-0.8, -0.4, 0.0, 0.4, 0.8), (None,)):
        b = tuple(np.array([bx, by, 1.0]) / np.linalg.norm([bx, by, 1.0]))
        (d, e), = run({"b8": b, "b3": b})
        res.append((math.degrees(math.acos(np.clip(d @ tgt, -1, 1))), bx, by, np.round(d, 2).tolist(), round(e)))
    for r in sorted(res)[:8]: print(r)
