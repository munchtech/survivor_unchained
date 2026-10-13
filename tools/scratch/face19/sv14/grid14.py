"""grid14.py BASE KEY V1;V2;.. [STYLES]: ev14 lines for BASE with KEY set to each value."""
from ev14 import *
base = eval(sys.argv[1]); key = sys.argv[2]; vals = [eval(v) for v in sys.argv[3].split(";")]
sts = sys.argv[4].split(",") if len(sys.argv) > 4 else ["ponytail", "braid"]
for v in vals:
    o = dict(base)
    if key != "-": o[key] = v
    for st in sts:
        r, s_ = line(st, o, "%s=%s" % (key, v)); print(s_, flush=True)
