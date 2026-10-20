import sys, json
sys.argv = ['x5.py', 'axe_heavy', 'dbg', sys.argv[1]]
from pathlib import Path
ANIM = Path('../../../anim').resolve(); sys.path.insert(0, str(ANIM))
import keyed
_ostrain = keyed.Rig._strain
log = []
def st(self, d_la, want, ha, fa, side):
    r = _ostrain(self, d_la, want, ha, fa, side)
    if side == 'r': log.append((round(r[0]), round(r[1])))
    return r
keyed.Rig._strain = st
exec(open('x5.py').read())
print(len(log)); print(log[-40:])
