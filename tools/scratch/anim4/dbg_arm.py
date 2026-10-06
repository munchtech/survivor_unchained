"""Per-frame arm trace of a keyed clip: python dbg_arm.py module clipfn side f0 f1"""
import math
import sys
from pathlib import Path
WT = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7dd95d00c4a6a017")
sys.path.insert(0, str(WT / "tools" / "anim"))
import importlib
import numpy as np
from rig import DATA, Skeleton, qinv, qmul, qrot
from keyed import Rig

mod, fn, side, f0, f1 = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
folk = mod == "crowd"
sk = Skeleton.load(DATA / ("folk_male_skeleton.json" if folk else "heroine_skeleton.json"))
rig = Rig(sk)
I = sk.index
m = importlib.import_module("crowd" if folk else f"clips.{mod}")
log = {}
orig = rig._strain


def st(d_la, want, ha, fa):
    r = orig(d_la, want, ha, fa)
    log.setdefault("s", []).append((round(r[0]), round(r[1])))
    return r


rig._strain = st
c = m.KEYED[fn]("m_" + fn, rig) if folk else getattr(m, fn)(rig)
g, p = sk.fk(c.rot, c.pos)
for f in range(f0, f1):
    S, E, W = p[f, I[f"upperarm_{side}"]], p[f, I[f"lowerarm_{side}"]], p[f, I[f"hand_{side}"]]
    fa = (W - E) / np.linalg.norm(W - E)
    fing = qrot(g[f, I[f"hand_{side}"]], qrot(qinv(sk.rest_globals()[0][0, I[f"hand_{side}"]]), [0, 0, 0]) + [0, 1, 0])
    hq, hq0 = g[f, I[f"hand_{side}"]], g[f - 1, I[f"hand_{side}"]]
    step = math.degrees(2 * math.acos(min(1, abs(float(np.dot(hq, hq0))))))
    fq, fq0 = g[f, I[f"lowerarm_{side}"]], g[f - 1, I[f"lowerarm_{side}"]]
    fstep = math.degrees(2 * math.acos(min(1, abs(float(np.dot(fq, fq0))))))
    e_dir = (E - S) / np.linalg.norm(E - S)
    print(f"f{f} hand step {step:5.1f} forearm step {fstep:5.1f} forearm dir {np.round(fa, 2)} elbow dir {np.round(e_dir, 2)} |S-W| {np.linalg.norm(W - S):.3f}")
s = log["s"]
n = c.frames
tail = s[-2 * n:]
print("pass-2 strains (twist, swing), l then r:")
for f in range(f0, f1):
    print(f, tail[2 * f:2 * f + 2])
