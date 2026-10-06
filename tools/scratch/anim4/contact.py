"""Contacts of flask_drink: the spout/cork vs her lips, the left pinch vs her teeth, per frame step.
usage: python contact.py [step]"""
import sys
from pathlib import Path
WT = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7dd95d00c4a6a017")
sys.path.insert(0, str(WT / "tools" / "anim"))
import numpy as np
from keyed import Rig
from rig import DATA, Skeleton, qrot
from held import face_point
from clips import story_c04 as m

step = int(sys.argv[1]) if len(sys.argv) > 1 else 4
sk = Skeleton.load(DATA / "heroine_skeleton.json")
rig = Rig(sk)
clip = m.flask_drink(rig)
g, p = sk.fk(clip.rot, clip.pos)
I = sk.index
hr, hl = I["hand_r"], I["hand_l"]
for fr in range(0, 175, step):
    mouth = face_point(sk, g, p, fr, "mouth")
    teeth = face_point(sk, g, p, fr, "teeth")
    sp = p[fr, hr] + qrot(g[fr, hr], m.SPOUT)
    ck = p[fr, hr] + qrot(g[fr, hr], m.CORK)
    pin = p[fr, hl] + qrot(g[fr, hl], m.PINCH_L)
    up = qrot(g[fr, hr], [0, 0, 1.0])
    print(f"f{fr:3d} spout-lips {np.linalg.norm(sp - mouth)*100:5.1f} cm  cork-teeth {np.linalg.norm(ck - teeth)*100:5.1f}  pinch-teeth {np.linalg.norm(pin - teeth)*100:5.1f}  neck dir {up.round(2)}  elbow_r y {p[fr, I['lowerarm_r']][1]:.2f}")
