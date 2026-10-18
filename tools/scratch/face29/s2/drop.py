"""python drop.py GLB LOG TAG: upper teeth dropped d mm: rows of upper teeth / tongue / lower teeth per column (1:1 px)."""
import sys, types, numpy as np
GLB, LOG, TAG = sys.argv[1:4]
src = open(__file__.replace("drop.py", "camlab_f20.py")).read().split('if __name__ == "__main__":')[0].replace("A = sys.argv + [None] * 6", "A = [None]*7")
cl = types.ModuleType("cl"); exec(src, cl.__dict__)
ls = open(LOG, encoding="utf-8", errors="replace").read().splitlines()
i = next(j for j, l in enumerate(ls) if l.strip() == "STILL " + TAG)
for l in ls[i+1:]:
    if l.startswith("MOUTHCAM"):
        f = l.split(); o = np.array([float(v) for v in f[f.index("o")+1:f.index("o")+4]])
        if np.abs(o).max() < 10: line = f; break
g = lambda k, n=3: np.array([float(v) for v in line[line.index(k)+1:line.index(k)+1+n]])
o, B, fov, vp = g("o"), np.c_[g("bx"), g("by"), g("bz")], float(g("fov", 1)[0]), g("vp", 2)
if int(g("keep", 1)[0]) == 0: fov = float(np.degrees(2*np.arctan(np.tan(np.radians(fov)/2)*vp[1]/vp[0])))
W = dict(kv.split("=") for kv in line[line.index("w")+1:]); W = {k: float(v) for k, v in W.items()}
cl.POSES["x"] = W
face = next((k[5:] for k in W if k.startswith("face_")), "own")
print(TAG, face, "open %.3f" % W.get("mouth_open", 0))
BOX = (1040, 690, 1240, 790); SX = 2
orig, dirs, shp = cl.rays(o, B, fov, vp, BOX, SX)
for d in (0, 0.5, 1.0, 1.5, 2.0):
    js, M = cl.load(GLB, "own", "x")
    X, F, C, D, V = M["HeroineTeeth"]; up = np.linalg.norm(D, axis=1) < 0.002
    X = X.copy(); X[up, 1] -= d / 1000; M["HeroineTeeth"] = (X, F, C, D, V)
    lab, val, pos = cl.cast(M, orig, dirs); lab = lab.reshape(shp)
    s = []
    for c0 in range(0, shp[1], 20*SX):
        col = lab[:, c0:c0+20*SX]
        s.append("%d:U%.1f T%.1f L%.1f" % (BOX[0]+c0//SX, *[(col == L).sum(0).mean()/SX for L in (2, 4, 3)]))
    print(" d%.1f  " % d + " | ".join(s))
