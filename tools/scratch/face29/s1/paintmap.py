"""Her head's paint and shadow mask, with the region behind/above her left ear outlined (UV)."""
import sys, numpy as np
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\tools\scratch\face29")
from gl import G, skinned
from PIL import Image, ImageDraw
ART = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\art\people"
her = G(ART + r"\heroine.glb")
HJ = {her.j["nodes"][n].get("name"): her.W(n) for n in her.j["skins"][0]["joints"]}
for (node, mesh, k, mat, P, J, Wt, s, I, ni) in her.meshes():
    if node == "HeroineHead":
        at = her.j["meshes"][her.j["nodes"][ni]["mesh"]]["primitives"][k]["attributes"]
        M = np.array([HJ.get(n, her.W(her.j["skins"][s]["joints"][q])) for q, n in enumerate(her.joint_names(s))]) @ her.ibm(s)
        HV = skinned(P, J, Wt, M); HUV = her.acc(at["TEXCOORD_0"]).astype(float); HI = I
th = np.degrees(np.arctan2(HV[:, 0], HV[:, 2])); z = (HV[:, 1] - 1.748) * 1000
m = (th > 80) & (th < 135) & (z > -50) & (z < 50)
uv = HUV[m]
print("uv range", uv.min(0), uv.max(0))
for name in ("heroine_head.jpg", "heroine_shadow.png"):
    im = Image.open(ART + r"\head_tex" + "\\" + name).convert("RGB")
    W, H = im.size
    x0, y0 = int(uv[:, 0].min() * W) - 40, int(uv[:, 1].min() * H) - 40
    x1, y1 = int(uv[:, 0].max() * W) + 40, int(uv[:, 1].max() * H) + 40
    d = ImageDraw.Draw(im)
    # mark the iso-lines: angle 90, 105, 120 and heights
    for t, (lo, hi) in ((90, (85, 95)),):
        pass
    for i in np.nonzero(m)[0][::3]:
        u, v = HUV[i]; c = (255, 0, 0) if abs(th[i] - 90) < 1.5 else (0, 255, 0) if abs(th[i] - 105) < 1.5 else (0, 0, 255) if abs(th[i] - 120) < 1.5 else (255, 255, 0) if abs(z[i]) < 1.5 else None
        if c: d.point((u * W, v * H), fill=c)
    im.crop((x0, y0, x1, y1)).save(sys.argv[1] + "_" + name.split(".")[0] + ".png")
    print(name, (W, H), (x0, y0, x1, y1))
