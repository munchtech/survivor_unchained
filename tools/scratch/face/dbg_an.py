import json
import sys

import numpy as np

an = dict(np.load(sys.argv[1]))
lm = json.load(open(sys.argv[2]))
P0 = an["P0"]
for k in (1, 33, 263, 152, 10, 234, 454, 13):
    print(k, np.round(lm["points"][k], 1), np.round(P0[k], 4), an["hit"][k])
print("cam", np.round(np.array(lm["camera"]["matrix"]), 3))
