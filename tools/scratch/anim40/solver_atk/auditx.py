"""audit.py's line for clips in another folder: python auditx.py FOLDER clip [clip ...]"""
import sys
from pathlib import Path
ANIM = Path(__file__).resolve().parents[3] / 'anim'
sys.path.insert(0, str(ANIM))
import audit as A  # noqa
folder, names = Path(sys.argv[1]), sys.argv[2:]
sk = A.Skeleton.load(A.DATA / 'heroine_skeleton.json')
for n in names:
    d, out = A.audit(folder / f'{n}.json', sk)
    parts = []
    for s in 'lr':
        o = out[s]
        parts.append(f"{s}: spin {o['max_step']:.0f}/{o['max_step_fa']:.0f} wtw {o['max_wrist_twist']:.0f} wbend {o['max_wrist_bend']:.0f} "
                     f"wdev {o['max_dev']:.0f} ftw {o['max_fore_twist']:.0f} elbow {out['elbow_' + s]:.0f} knee {out['knee_' + s]:.0f} ({len(o['flags'])} flagged)")
    print(f"{n:22s} " + " | ".join(parts))
    for s in 'lr':
        for fr, why in out[s]['flags']:
            print(f"         {s} f{fr}: {why}")
