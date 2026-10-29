import os, sys
os.environ["ANIM_PEOPLE"] = os.path.abspath(sys.argv[1])
from g2lib import *
from skin import Body
import meas
b = Body.heroine(jiggle=False, head=True, helpers=True)
b._show='top_%s.png'
meas.m(b, sys.argv[2] if len(sys.argv) > 2 else "base", curv_print=False)
