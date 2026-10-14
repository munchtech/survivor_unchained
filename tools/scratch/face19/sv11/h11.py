"""h11.py: solver 11's shared setup: the C# at HEAD (c9d893ae) as the replica runs it (hs10 + solver 8's carry options +
solver 10's braid corner), and an every-frame dump's photographed frame k (dump index k+3)."""
import sys; sys.path[:0] = ["../sv10", "../sv9", "../sv8", "../sv6", "../sv5", "../sv4", "../sv3"]
from hs10 import *
def HEAD(st, **o):
    b = dict(rtime=0.35, rrad=1, rin=1)
    if st == "braid": b.update(sm=60, smheld=1, smvn=1)
    b.update(o); return b
def run(fr, st, **o): return sim10(fr, st, **HEAD(st, **o))
