"""python lab.py GLB LOG STILLTAG OUT.png [nohead]: label map of her mouth at a still (exact weights from MOUTHCAM)."""
import sys, numpy as np
from PIL import Image
sys.argv = [sys.argv[0]] + sys.argv[1:]
A = sys.argv + [None]*3
GLB, LOG, TAG, OUT, MODE = A[1], A[2], A[3], A[4], A[5]
import importlib.util
spec = importlib.util.spec_from_file_location("cl", __file__.replace("lab.py", "camlab_f20.py"))
import types
src = open(__file__.replace("lab.py", "camlab_f20.py")).read().split('if __name__ == "__main__":')[0]
src = src.replace("A = sys.argv + [None] * 6", "A = [None]*7")
cl = types.ModuleType("cl"); exec(src, cl.__dict__)
ls = open(LOG, encoding="utf-8", errors="replace").read().splitlines()
i = next(j for j, l in enumerate(ls) if l.strip() == "STILL " + TAG)
line = None
for l in ls[i+1:]:
    if l.startswith("MOUTHCAM"):
        f = l.split()
        o = np.array([float(v) for v in f[f.index("o")+1:f.index("o")+4]])
        if np.abs(o).max() < 10: line = f; break
g = lambda k, n=3: np.array([float(v) for v in line[line.index(k)+1:line.index(k)+1+n]])
o, B, fov, vp = g("o"), np.c_[g("bx"), g("by"), g("bz")], float(g("fov", 1)[0]), g("vp", 2)
W = {}
for kv in line[line.index("w")+1:]:
    k, v = kv.split("="); W[k] = float(v)
print("weights", W)
cl.POSES["x"] = W
js, meshes = cl.load(GLB, "own", "x")
BOX = (1020, 690, 1260, 810); SX = 2
keep = int(g("keep", 1)[0])
if keep == 0: fov = float(np.degrees(2*np.arctan(np.tan(np.radians(fov)/2)*vp[1]/vp[0])))
orig, dirs, shp = cl.rays(o, B, fov, vp, BOX, SX)
if MODE == "nohead":
    X, F, C, D, V = meshes["HeroineHead"]; meshes["HeroineHead"] = (X, F[:1]*0, C, D, V)
lab, val, pos = cl.cast(meshes, orig, dirs)
lab = lab.reshape(shp); val = val.reshape(shp); pos = pos.reshape(shp + (3,))
img = np.zeros(shp + (3,))
base = {0: (0, 0, 0), 1: (0.85, 0.65, 0.5), 2: (1, 1, 1), 3: (0.3, 1, 1), 4: (1, 0.45, 0.6), 5: (0.8, 0.1, 0.1)}
for L, c in base.items():
    m = lab == L
    k = val[m][:, None] if L in (2, 3, 4) else (val[m][:, None]*0.6+0.4 if L == 1 else 1.0)
    img[m] = np.array(c) * k
Image.fromarray((img*255).astype(np.uint8)).save(OUT)
np.savez_compressed(OUT[:-4] + ".npz", lab=lab, val=val, pos=pos)
for c0 in range(0, shp[1], 20*SX):
    col = lab[:, c0:c0+20*SX]; op = (col != 1).sum(0).mean()
    if op < 2*SX: continue
    print("px %4d: open %5.1f | U %4.1f L %4.1f T %4.1f in %4.1f none %4.1f" % (BOX[0]+c0/SX, op/SX, *[(col == L).sum(0).mean()/SX for L in (2, 3, 4, 5, 0)]))
