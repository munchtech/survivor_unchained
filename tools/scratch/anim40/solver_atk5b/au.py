import sys
from pathlib import Path
ANIM = Path(__file__).resolve().parents[3] / 'anim'; sys.path.insert(0, str(ANIM))
import audit as A
sk = A.Skeleton.load(A.DATA / 'heroine_skeleton.json')
for fo in sys.argv[2:]:
    d, out = A.audit(Path(fo) / f'{sys.argv[1]}.json', sk)
    for s in 'lr':
        o = out[s]
        print(fo, s, f"spin {o['max_step']:.0f}/{o['max_step_fa']:.0f} wtw {o['max_wrist_twist']:.0f} wbend {o['max_wrist_bend']:.0f} wdev {o['max_dev']:.0f} ftw {o['max_fore_twist']:.0f} elbow {out['elbow_'+s]:.0f} knee {out['knee_'+s]:.0f}", o['flags'][:5])
