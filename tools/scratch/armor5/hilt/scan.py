import sys, json
import numpy as np
from opt import hilt_of
from ev import *
pts = json.loads(sys.argv[1])
for x in pts:
    h = hilt_of(np.array(x, float))
    r = measure(apply("run_warden_town", h, [0, 10]), fl=[0], clrs=("warden", "reaver"))[0]
    print(x, f"el {r['el']:.0f} fa {r['fa']:.0f} wr {r['wr']:.0f} |",
          "W " + " ".join(f"{r[('warden',k,'a')]:.1f}/{r[('warden',k,'p')]:.0f}" for k in KEYS),
          "| R " + " ".join(f"{r[('reaver',k,'a')]:.1f}/{r[('reaver',k,'p')]:.0f}" for k in KEYS), flush=True)
