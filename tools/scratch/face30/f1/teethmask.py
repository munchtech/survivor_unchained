"""Upper vs lower teeth in heroine.glb: UV, colour and rest-position ranges (for a shader mask)."""
import sys, numpy as np
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\tools\assets")
import heroine_seam as hs
js, b = hs._load(sys.argv[1])
for m in js["meshes"]:
    if m.get("name") != "HeroineTeeth": continue
    p = m["primitives"][0]; names = m.get("extras", {}).get("targetNames", [])
    print("targets", names, "attrs", list(p["attributes"]))
    V = hs._read(js, b, p["attributes"]["POSITION"]).astype(float)
    D = hs._read(js, b, p["targets"][names.index("mouth_open")]["POSITION"])
    UV = hs._read(js, b, p["attributes"]["TEXCOORD_0"])
    C = hs._read(js, b, p["attributes"]["COLOR_0"])
    up = np.linalg.norm(D, axis=1) < 0.002
    for nm, s in (("upper", up), ("lower", ~up)):
        print(nm, s.sum(), "uv min", UV[s].min(0), "max", UV[s].max(0), "pos min", V[s].min(0), "max", V[s].max(0), "col min", C[s].min(0), "max", C[s].max(0))
    print("disp max", np.linalg.norm(D, axis=1).max(), "partial", ((np.linalg.norm(D,axis=1)>0.0002)&up).sum())
    if "JOINTS_0" in p["attributes"]:
        J = hs._read(js, b, p["attributes"]["JOINTS_0"]); print("joints", np.unique(J[:,0]))
    idx = np.where(up)[0]; print("upper idx range", idx.min(), idx.max(), "count", len(idx))
    for w in (0.05, 0.1, 0.25):
        X = V + w * D
        print("w", w, "upper Y min", X[up,1].min(), "lower Y max", X[~up,1].max())
    for w in (0.0, 0.1, 0.25):
        X = V + w * D; best = None
        for a in np.linspace(-1.5, 1.5, 301):
            s = X[:,1] + a * X[:,2]
            gap = s[up].min() - s[~up].max()
            if best is None or gap > best[0]: best = (gap, a, s[up].min(), s[~up].max())
        print("w", w, "best plane y+a*z: gap %.5f a %.3f upmin %.5f lomax %.5f" % best)
