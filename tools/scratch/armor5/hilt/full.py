import sys, json
import numpy as np
from opt import hilt_of
from ev import *
a = json.loads(sys.argv[1])
h = hilt_of(np.array(a, float)) if isinstance(a, list) else a
h.update(json.loads(sys.argv[2]) if len(sys.argv) > 2 else {})
print(json.dumps(h))
for nm in ("run_warden_town", "sprint_warden_town"):
    c = apply(nm, h)
    rows = measure(c, clrs=("warden", "reaver", "none"))
    for r in rows:
        print(nm[:6], f"f{r['f']:2d} el {r['el']:5.1f} fa {r['fa']:4.1f} wr {r['wr']:4.1f} H {np.round(r['H'],3)} |",
              " ".join(f"{cl[0]}:a{max(r[(cl,k,'a')] for k in KEYS):4.1f} p{min(r[(cl,k,'p')] for k in KEYS):4.1f}-{max(r[(cl,k,'p')] for k in KEYS):4.1f}" for cl in ("warden", "reaver", "none")), "X", " ".join(f"{max(r[(cl,k,'a')] for cl in ('warden','reaver','none')):.1f}" for k in XK), flush=True)
