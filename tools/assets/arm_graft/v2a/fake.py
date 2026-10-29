# Body 2 A: the measuring harness (body2 d_a/d_b/d_c scripts, which call skin.Body.heroine) on a blend dump instead of
# an exported glb. Import first: FAKE_DUMP=<dump.npz (topology)> FAKE_P=<P.npy> FAKE_VG=<VG.npy> python -c "import fake; ..."
# (the head and everything but the Heroine piece from FAKE_BASE, default body2/orig_people/heroine.glb)
import os, sys, numpy as np
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\armor-7"
sys.path.insert(0, W + r"\tools\anim"); sys.path.insert(0, W + r"\tools\assets\arm_graft\g2a")
from skin import Body
import g2lib
BASE = os.environ.get("FAKE_BASE", r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\23290ad1-ed63-4a0d-8e12-ac0911d16c27\scratchpad\body2\orig_people\heroine.glb")
_orig = Body.heroine
_cache = {}


def _mk(outfit=None, jiggle=True, body_file=None, helpers=False, head=False):
    d = g2lib.load_dump(os.environ["FAKE_DUMP"])
    P = np.load(os.environ["FAKE_P"]) if os.environ.get("FAKE_P") else d["P"]
    VG = np.load(os.environ["FAKE_VG"]) if os.environ.get("FAKE_VG") else d["VG"]
    b0 = _orig(outfit=outfit, jiggle=jiggle, body_file=BASE, helpers=helpers, head=head)
    b = g2lib.dbody(b0, P, d["polys"], VG, d["names"])
    b.dump = d
    return b


if os.environ.get("FAKE_DUMP"):
    Body.heroine = staticmethod(_mk)
