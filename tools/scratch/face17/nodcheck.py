"""Nod check for the nape weld: skin the head's and the graft's shared seam points under head and neck rotations
(linear blend skinning from the glb's own skin) and report the largest gap between partners. Zero gap = no crack.
Usage: python nodcheck.py heroine.glb"""
import sys
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\tools\assets")
import numpy as np, heroine_seam as hs
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation as R

js, binc = hs._load(sys.argv[1])
mats = [m.get("name") for m in js["materials"]]

def find(mat):
    for mi, m in enumerate(js["meshes"]):
        for p in m["primitives"]:
            if "material" in p and mats[p["material"]] == mat:
                return p, [n for n in js["nodes"] if n.get("mesh") == mi][0]

hp, hn = find("skin_head"); gp, gn = find("skin_graft")
skin = js["skins"][hn["skin"]]
joints = skin["joints"]
ibm = hs._read(js, binc, skin["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)  # column-major
parent = {}
for i, n in enumerate(js["nodes"]):
    for c in n.get("children", []):
        parent[c] = i

def local(i, extra):
    n = js["nodes"][i]
    M = np.eye(4)
    if "matrix" in n:
        return np.array(n["matrix"]).reshape(4, 4).T
    r = n.get("rotation", [0, 0, 0, 1]); t = n.get("translation", [0, 0, 0]); s = n.get("scale", [1, 1, 1])
    rot = R.from_quat(r)
    if i in extra:
        rot = rot * extra[i]
    M[:3, :3] = rot.as_matrix() * np.array(s)
    M[:3, 3] = t
    return M

def world(i, extra, memo):
    if i in memo:
        return memo[i]
    M = local(i, extra)
    if i in parent:
        M = world(parent[i], extra, memo) @ M
    memo[i] = M
    return M

def skinned(p, extra):
    V = hs._read(js, binc, p["attributes"]["POSITION"]); J = hs._read(js, binc, p["attributes"]["JOINTS_0"]).astype(int)
    W = hs._read(js, binc, p["attributes"]["WEIGHTS_0"])
    memo = {}
    mats_ = np.array([world(j, extra, memo) @ ibm[k] for k, j in enumerate(joints)])
    Vh = np.c_[V, np.ones(len(V))]
    out = np.zeros((len(V), 3))
    for c in range(4):
        out += W[:, c:c + 1] * np.einsum("nij,nj->ni", mats_[J[:, c]], Vh)[:, :3]
    return V, out

names = {js["nodes"][j].get("name"): j for j in joints}
HV0 = hs._read(js, binc, hp["attributes"]["POSITION"]); GV0 = hs._read(js, binc, gp["attributes"]["POSITION"])
d, gi = cKDTree(GV0).query(HV0); sh = np.where(d < 2e-4)[0]
print("shared", len(sh))
bones = [b for b in ("neck_01", "Head", "spine_03") if b in names]
print("bones", bones)
for axis in ("x", "y", "z"):
    for deg in (-30, -20, 20, 30):
        extra = {names[b]: R.from_euler(axis, deg / len(bones), degrees=True) for b in bones}
        _, H = skinned(hp, extra); _, G = skinned(gp, extra)
        gap = np.linalg.norm(H[sh] - G[gi[sh]], axis=1)
        print(f"{axis}{deg:+d}: max gap {gap.max() * 1000:.3f} mm  mean {gap.mean() * 1000:.4f} mm")
