"""Face 30 neck: python nk_uvpaint.py FACE TURN: the head paint (and maps) under the shade box's pixels, from the uv10 frame."""
import sys, os
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from nk_measure import oklab, BOX
W = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
SH = os.path.join(W, "godot", ".shots"); T = os.path.join(W, "godot", "art", "people", "head_tex")
face, turn = sys.argv[1], int(sys.argv[2]); tag = sys.argv[3] if len(sys.argv) > 3 else "a1"
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
u = lin(np.asarray(Image.open(os.path.join(SH, f"nk_b0_{face}_t{turn:03d}_night_uv10.png")).convert("RGB")).astype(float) / 255)
fr = np.asarray(Image.open(os.path.join(SH, f"nk_{tag}_{face}_t{turn:03d}_night.png")).convert("RGB")).astype(float)
P = np.asarray(Image.open(os.path.join(T, "heroine_head.jpg" if face == "own" else f"heroine_head_{face}.jpg")).convert("RGB")).astype(float)
G = np.asarray(Image.open(os.path.join(T, "heroine_graft.jpg")).convert("RGB")).astype(float)
fm = np.asarray(Image.open(os.path.join(T, "heroine_features.png")).convert("RGBA")).astype(float) / 255
def lc(p): L = oklab(p.reshape(-1, 3)); return L[:, 0].mean(), np.hypot(L[:, 1], L[:, 2]).mean(), np.degrees(np.arctan2(L[:, 2].mean(), L[:, 1].mean()))
sb = BOX[turn][0]
for y in range(sb[1], sb[3], 10):
    row = []
    for x in range(sb[0], sb[2], 10):
        b = u[y, x, 2]
        if b < 0.2 or u[y, x, 0] / b > 1.01: row.append("   graft/none   "); continue
        uu, vv = u[y, x, 0] / b, u[y, x, 1] / b
        tx, ty = int(uu * 4096), int(vv * 4096)
        pl = lc(P[ty - 6:ty + 6, tx - 6:tx + 6]); sl = lc(fr[y - 2:y + 3, x - 2:x + 3])
        row.append(f"p{pl[1]:.3f}/s{sl[1]:.3f} fb{fm[int(vv*1024), int(uu*1024), 2]:.1f}")
    print(y, " | ".join(row))
print("graft paint L%.3f C%.3f h%.0f" % lc(G[::8, ::8]))
