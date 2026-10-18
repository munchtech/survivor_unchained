"""Where the pale wedge is: her head's skin behind/above her ears, per style: cap cover, shadow mask, paint."""
import sys, numpy as np
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\tools\scratch\face29")
from gl import G, skinned
from scipy.spatial import cKDTree
from PIL import Image
A = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\art\people"
ART = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\art\people"
her = G(ART + r"\heroine.glb")
HJ = {her.j["nodes"][n].get("name"): her.W(n) for n in her.j["skins"][0]["joints"]}
def mats_for(g, s=0):
    return np.array([HJ.get(n, g.W(g.j["skins"][s]["joints"][q])) for q, n in enumerate(g.joint_names(s))]) @ g.ibm(s)
for (node, mesh, k, mat, P, J, Wt, s, I, ni) in her.meshes():
    if node == "HeroineHead":
        at = her.j["meshes"][her.j["nodes"][ni]["mesh"]]["primitives"][k]["attributes"]
        HV = skinned(P, J, Wt, mats_for(her, s)); HUV = her.acc(at["TEXCOORD_0"]).astype(float); HI = I
        print("head", mat, len(P))
eye_y = 1.748
shadow = np.asarray(Image.open(ART + r"\head_tex\heroine_shadow.png").convert("RGB"), float) / 255
paint = np.asarray(Image.open(ART + r"\head_tex\heroine_head.jpg").convert("RGB"), float) / 255
def samp(img, uv):
    h, w = img.shape[:2]
    x = np.clip((uv[:, 0] % 1) * w, 0, w - 1).astype(int); y = np.clip((uv[:, 1] % 1) * h, 0, h - 1).astype(int)
    return img[y, x]
sh = samp(shadow, HUV); pa = samp(paint, HUV)
# angle round her head: 0 front (+Z), 90 her left (+X), 180 back
c = HV.mean(0)
th = np.degrees(np.arctan2(HV[:, 0], HV[:, 2] - 0.0))
z = HV[:, 1] - eye_y
print("head extent x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f" % (HV[:,0].min(), HV[:,0].max(), HV[:,1].min(), HV[:,1].max(), HV[:,2].min(), HV[:,2].max()))
for s in sys.argv[2:] or ["pixie", "ponytail", "braid", "bob", "long"]:
    g = G(A + rf"\heroine_hair_{s}.gltf"); M = mats_for(g)
    caps, cards = [], []
    for (node, mesh, k, mat, P, J, Wt, sk, I, ni) in g.meshes():
        at = g.j["meshes"][g.j["nodes"][ni]["mesh"]]["primitives"][k]["attributes"]
        V = skinned(P, J, Wt, M)
        col = g.acc(at["COLOR_0"]).astype(float) if "COLOR_0" in at else None
        if col is not None and col.max() > 1.5: col = col / 65535.0
        if mat == "hair_cap": caps.append((V, col, I))
        elif mat in ("hair", "hair_fine"): cards.append((V, col, mat))
    CV = np.vstack([v for v, c_, i in caps]); CA = np.concatenate([c_[:, 3] for v, c_, i in caps])
    tree = cKDTree(CV)
    d, idx = tree.query(HV)
    fade = np.where(d < 0.004, CA[idx], 0.0)
    KV = np.vstack([v for v, c_, m in cards if m == "hair"]); kt = cKDTree(KV)
    dk, _ = kt.query(HV)
    print(f"== {s}: cap {len(CV)} v, cards {len(KV)} v")
    # bins by angle (side: |th| 60..180) and height
    for side, sgn in (("her left (+x)", 1), ("her right (-x)", -1)):
        print("  ", side, "rows: z above eye (mm); cols: angle from front (deg). cell: cap fade (avg) / shadow green / paint lum / nearest card mm")
        for zz in range(90, -100, -15):
            row = []
            for a in range(60, 181, 15):
                m = (np.abs(z * 1000 - zz) < 7.5) & (np.abs(np.abs(th) - a) < 7.5) & (np.sign(th) == sgn) & (np.hypot(HV[:, 0], HV[:, 2]) > 0.04)
                if m.sum() < 2: row.append("      .       "); continue
                row.append("%4.2f/%4.2f/%4.2f/%3.0f" % (fade[m].mean(), sh[m, 1].mean(), pa[m].mean(1).mean(), np.median(dk[m]) * 1000))
            print("   %+4d " % zz + " ".join(row))
    break
