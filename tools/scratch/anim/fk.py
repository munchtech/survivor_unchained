import sys
sys.path.insert(0, r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa4f5fc266b043035\tools\anim')
import importlib
import numpy as np
from keyed import Rig
from rig import Skeleton

mod, name = sys.argv[1], sys.argv[2]
frames = [int(x) for x in sys.argv[3].split(',')] if len(sys.argv) > 3 else None
sk = Skeleton.load()
rig = Rig(sk)
m = importlib.import_module(f'clips.{mod}')
clip = getattr(m, name)(rig)
g, p = sk.fk(clip.rot, clip.pos)
for f in frames or range(clip.frames):
    out = []
    for n in ('pelvis', 'thigh_l', 'calf_l', 'foot_l', 'foot_r', 'hand_l', 'hand_r', 'Head'):
        v = p[f, sk.i(n)]
        out.append(f"{n} ({v[0]:5.2f},{v[1]:5.2f},{v[2]:5.2f})")
    print(f, '  '.join(out))
