import sys, types, numpy as np, trimesh
from PIL import Image
W_="C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a2d632df7c7f21ec0/"
src = open("camlab_f20.py").read().split('if __name__ == "__main__":')[0].replace("A = sys.argv + [None] * 6", "A = [None]*7")
cl = types.ModuleType("cl"); exec(src, cl.__dict__)
hs = cl.hs
LOG, TAG, X0 = sys.argv[1], sys.argv[2], int(sys.argv[3])
ls = open(LOG, encoding="utf-8", errors="replace").read().splitlines()
i = next(j for j, l in enumerate(ls) if l.strip() == "STILL " + TAG)
for l in ls[i+1:]:
    if l.startswith("MOUTHCAM"):
        f = l.split(); o = np.array([float(v) for v in f[f.index("o")+1:f.index("o")+4]])
        if np.abs(o).max() < 10: line = f; break
g = lambda k, n=3: np.array([float(v) for v in line[line.index(k)+1:line.index(k)+1+n]])
o, B, fov, vp = g("o"), np.c_[g("bx"), g("by"), g("bz")], float(g("fov", 1)[0]), g("vp", 2)
if int(g("keep", 1)[0]) == 0: fov = float(np.degrees(2*np.arctan(np.tan(np.radians(fov)/2)*vp[1]/vp[0])))
W = {k: float(v) for k, v in (kv.split("=") for kv in line[line.index("w")+1:])}
js, binc = hs._load(W_+"godot/art/people/heroine.glb")
m = next(m for m in js["meshes"] if m["name"] == "HeroineHead"); p = m["primitives"][0]; names = m["extras"]["targetNames"]
V = hs._read(js, binc, p["attributes"]["POSITION"]).astype(float); F = hs._read(js, binc, p["indices"]).reshape(-1, 3).astype(np.int64)
UV = hs._read(js, binc, p["attributes"]["TEXCOORD_0"]); COL = hs._read(js, binc, p["attributes"]["COLOR_0"])
for k_, n in enumerate(names):
    if n in W: V = V + W[n] * hs._read(js, binc, p["targets"][k_]["POSITION"])
orig, dirs, shp = cl.rays(o, B, fov, vp, (X0, 760, X0+1, 800), 1)
tm = trimesh.Trimesh(V, F, process=False)
loc, ri, ti = tm.ray.intersects_location(orig, dirs, multiple_hits=False)
ao = np.asarray(Image.open(W_+"godot/art/people/head_tex/heroine_ao_softlip.png").convert("RGBA")).astype(float)/255
for r, t, L in sorted(zip(ri, ti, loc)):
    bc = trimesh.triangles.points_to_barycentric(V[F[t]][None], L[None])[0]
    uv = (UV[F[t]] * bc[:, None]).sum(0)
    px = ao[int(uv[1]*ao.shape[0]) % ao.shape[0], int(uv[0]*ao.shape[1]) % ao.shape[1]]
    col=(COL[F[t]]*bc[:,None]).sum(0); print(760+r, "col", np.round(col,2), np.round(L*1000,1), "uv", np.round(uv,4), "ao rgba", np.round(px,2))
