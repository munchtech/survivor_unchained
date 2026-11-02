"""Build flare_long_cut, recording each hand's raw and continuous forearm twist per frame of the final solve pass."""
import sys
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\anim-59\tools\anim")
import keyed
from keyed import Rig
from rig import Skeleton, DATA
from clips import flare_long_cut as M
rec = []
_st, _so = Rig._strain, Rig.solve
def strain(self, d_la, want, ha, fa, side):
    r = _st(self, d_la, want, ha, fa, side)
    self._raw = getattr(self, "_raw", {}); self._raw[side] = (r[0], r[1])
    return r
def solve(self, pose, base=None):
    self._raw = {}
    out = _so(self, pose, base=base)
    rec.append((dict(self._raw), dict(getattr(self, "twist_last", {}))))
    return out
Rig._strain, Rig.solve = strain, solve
sk = Skeleton.load(DATA / "heroine_skeleton.json"); rig = Rig(sk, body="her")
M._settle = lambda rig, clip: clip
rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 6
M.flare_long_cut(rig, rounds=rounds)
n = M.END + 1
last = rec[-n:]
print("fr  L raw  L sw  L cont | R raw  R sw  R cont")
for f, (raw, tl) in enumerate(last):
    def g(s):
        r = raw.get(s); c = tl.get(s)
        return (f"{r[0]:7.1f} {r[1]:5.1f} " if r else " " * 14) + (f"{c:7.1f}" if c is not None else "   -   ")
    print(f"{f:2d} {g('l')} | {g('r')}")
