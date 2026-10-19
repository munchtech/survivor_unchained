"""python cand.py s t clav -> HILT json for hand s down the scabbard, swivel t, clav share"""
import sys, json
from ev import *
from opt import rotv, hilt_of
X = [-0.1569, 0.06, -0.025, 7.359, 3.2895, -72.1558, 4.7238]
s, t, cl = (float(a) for a in sys.argv[1:4])
x = list(X); x[0] = s
h0 = hilt_of(np.array(x)); h0.update(pole_chest=1.0, clav=0.0)
c0 = apply("run_warden_town", h0, [0]); G0 = Gframes(c0)[0]; P0 = G0[I["pelvis"]][:3, :3]
ax = P0.T @ (G0[I["hand_l"]][:3, 3] - G0[I["upperarm_l"]][:3, 3])
h0["pole"] = [float(v) for v in np.round(rotv(np.array(h0["pole"]), ax, t), 4)]; h0["clav"] = cl
print(json.dumps(h0))
