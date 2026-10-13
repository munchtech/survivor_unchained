import sys
from hs3 import *
G0 = dict(FIX, push=True, hold='hang', dftl=0.9, rel_drag=0.03, bend=0.01, bend_max=math.radians(60), root_cone=math.radians(75),
          bend_mode='vn', bend_gate=True, cap_gate=True)
BEND = dict(braid=0.03, ponytail=0.03, long=0.02)
G1 = dict(G0, push_gate=True, dftl_gate=True, drag_gate=True)
def lg(d, n): return load(S + "f19/" + d + "/" + n + ".log")
def per(o, st): return dict(o, bend=BEND[st] * o.get("bscale", 1)) if o.get("bend_mode") == "vn" else o
G2 = dict(G1, cone_soft=True)
G3 = dict(G2, recede=True)
