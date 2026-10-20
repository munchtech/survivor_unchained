import sys
from pathlib import Path
import numpy as np
ANIM = Path(__file__).resolve().parents[3] / 'anim'
sys.path.insert(0, str(ANIM))
import audit as A
label, folder, skel = A.SETS[0]
folder = Path(sys.argv[2]) if len(sys.argv) > 2 else folder
sk = A.Skeleton.load(A.DATA / skel); I = sk.index
d, rot, pos = A.load(folder / f'{sys.argv[1]}.json', sk)
g, p = sk.fk(rot, pos)
for f in range(rot.shape[0]):
    print(f, ' '.join(f"{n}:{np.round(p[f, I[n]]*100).astype(int)}" for n in ('foot_l','ball_l','foot_r','ball_r','pelvis')))
