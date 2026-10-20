"""per-frame wrist flex/dev of a side (audit's measure). wb.py CLIP [side]"""
import sys; sys.path.insert(0, '.')
import audit as A
from pathlib import Path
rec = []; orig = A.wrist_bend
def wb(dh, ax, s):
    r = orig(dh, ax, s); rec.append((s, r)); return r
A.wrist_bend = wb
sk = A.Skeleton.load(A.DATA / 'heroine_skeleton.json')
A.audit(Path('out/clips/' + sys.argv[1] + '.json'), sk)
side = sys.argv[2] if len(sys.argv) > 2 else 'l'
v = [r for s, r in rec if s == side]
print(side, 'flex', ' '.join(f"{x[0]:.0f}" for x in v)); print(side, 'dev ', ' '.join(f"{x[1]:.0f}" for x in v))
