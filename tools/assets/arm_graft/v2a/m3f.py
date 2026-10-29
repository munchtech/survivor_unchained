# Body 2 A: d_b m3.py (weights per band, shear vs rest at idle/A58/A82/show) on "orig" and a fake/real "mine".
#   FAKE_DUMP=.. FAKE_P=.. FAKE_VG=.. python m3f.py      or   MINE_GLB=<heroine.glb> python m3f.py
import os, sys
B = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\23290ad1-ed63-4a0d-8e12-ac0911d16c27\scratchpad\body2"
sys.path.insert(0, B + r"\d_b"); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cm
from skin import Body
_real = Body.heroine
if os.environ.get("FAKE_DUMP"): import fake
TAGS = os.environ.get("TAGS", "orig,mine").split(",")
def load(tag):
    if tag == "mine":
        if os.environ.get("MINE_GLB"): return _real(jiggle=False, helpers=True, body_file=os.environ["MINE_GLB"])
        return Body.heroine(jiggle=False, helpers=True)
    return _real(jiggle=False, helpers=True, body_file=cm.FILES[tag])
cm.load = load
src = open(B + r"\d_b\m3.py").read().replace('for tag in ("orig","graft"):', 'for tag in TAGS:')
exec(compile(src, "m3", "exec"))
