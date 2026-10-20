"""The free (left) hand at the run's forward end, rel. pelvis (cm), and a hash of the leg tracks. runhand.py clip..."""
import sys, json, hashlib
from pathlib import Path
import numpy as np
ANIM = Path(__file__).resolve().parents[3] / 'anim'
sys.path.insert(0, str(ANIM))
import audit as A  # noqa
sk = A.Skeleton.load(A.DATA / 'heroine_skeleton.json'); I = sk.index
for n in sys.argv[1:]:
    path = ANIM / 'out/clips' / f'{n}.json'
    d, rot, pos = A.load(path, sk); g, p = sk.fk(rot, pos)
    hl = (p[:, I['hand_l']] - p[:, I['pelvis']]) * 100
    f = int(np.argmax(hl[:, 2]))
    legs = [t for t in d['tracks'] if t['bone'].startswith(('pelvis', 'thigh', 'calf', 'foot', 'ball', 'root'))]
    h = hashlib.md5(json.dumps(legs).encode()).hexdigest()[:10]
    print(f"{n:22s} fwd end f{f}: hand_l {np.round(hl[f]).astype(int)}  (min x {hl[:, 0].min():.0f}, y at fwd {hl[f, 1]:.0f})  legs {h}")
