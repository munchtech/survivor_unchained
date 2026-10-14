import sys
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\tools\assets")
import numpy as np, heroine_seam as hs
from scipy.spatial import cKDTree
js, binc = hs._load(sys.argv[1])
mats = [m.get("name") for m in js["materials"]]
def find(mat):
    for mi, m in enumerate(js["meshes"]):
        for p in m["primitives"]:
            if "material" in p and mats[p["material"]] == mat:
                nodes = [n for n in js["nodes"] if n.get("mesh") == mi]
                return m, p, nodes
for mat in ("skin_head", "skin_graft"):
    m, p, nodes = find(mat)
    print(mat, m.get("name"), [k for k in p["attributes"]], "skins", [n.get("skin") for n in nodes],
          {k: (js["accessors"][p["attributes"][k]]["componentType"], js["accessors"][p["attributes"][k]].get("normalized")) for k in p["attributes"] if k[:6] in ("JOINTS", "WEIGHT")})
hm, hp, hn = find("skin_head"); gm, gp, gn = find("skin_graft")
HV = hs._read(js, binc, hp["attributes"]["POSITION"]); GV = hs._read(js, binc, gp["attributes"]["POSITION"])
d, gi = cKDTree(GV).query(HV); sh = np.where(d < 2e-4)[0]
skins = js["skins"]
hj = [skins[hn[0]["skin"]]["joints"]][0]; gj = skins[gn[0]["skin"]]["joints"]
names = [js["nodes"][j].get("name") for j in hj]
HJ = hs._read(js, binc, hp["attributes"]["JOINTS_0"]); HW = hs._read(js, binc, hp["attributes"]["WEIGHTS_0"])
GJ = hs._read(js, binc, gp["attributes"]["JOINTS_0"]); GW = hs._read(js, binc, gp["attributes"]["WEIGHTS_0"])
print("shared", len(sh), "same skin", hn[0]["skin"] == gn[0]["skin"])
def wof(J, W, joints, name):
    out = np.zeros(len(J))
    for c in range(4):
        out += np.where(np.array([js["nodes"][joints[j]].get("name") == name for j in J[:, c]]), W[:, c], 0)
    return out
for bone in ("Head", "head", "neck01", "Neck"):
    if bone in names:
        a = wof(HJ[sh], HW[sh], hj, bone); b = wof(GJ[gi[sh]], GW[gi[sh]], gj, bone)
        dd = np.abs(a - b); o = np.argsort(-dd)[:5]
        print(bone, "max diff %.3f" % dd.max(), "n>0.02:", (dd > 0.02).sum(), [(int(sh[i]), HV[sh[i]].round(3).tolist(), round(a[i], 3), round(b[i], 3)) for i in o])
