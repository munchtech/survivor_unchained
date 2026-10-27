# pose her at reaver_show f24 (right arm, and mirrored onto the left) and idle; dump for b_render.py
import os, sys
os.environ["ANIM_PEOPLE"] = os.path.abspath(sys.argv[1])
from common import *
import meas
b=load(); meas.prep(b); out=sys.argv[2]
G=b.globals(b.clip("reaver_show"),24)
np.savez(out,P=b.pose(G),Pl=b.pose(meas.mirrorG(b,G)),P0=b.pose(b.globals(b.clip("idle_reaver_town"),0)),T=b.T)
print("posed")
