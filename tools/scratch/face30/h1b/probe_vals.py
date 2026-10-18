"""print per-pixel texel values (paint sat own, paint rgb own) along screen rows. python probe_vals.py diag.npz prefix y0 y1 dy x0 x1 dx"""
import os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uvdecode import uv_at, SH
z = np.load(sys.argv[1]); S = 1024
pre = sys.argv[2]; y0, y1, dy, x0, x1, dx = map(int, sys.argv[3:9])
uv = uv_at(pre)
pa = np.asarray(Image.open(os.path.join(SH, "..", "art", "people", "head_tex", "heroine_head.jpg")).convert("RGB").resize((S, S), Image.BOX)).astype(int)
shot = np.asarray(Image.open(os.path.join(SH, pre + "_base.png")).convert("RGB")).astype(int)
E = np.zeros((S, S), bool); E[z["rows"], z["cols"]] = z["ear_tex"]; E = E[::-1]
for y in range(y0, y1, dy):
    o = []
    for x in range(x0, x1, dx):
        u, v = uv[y, x]
        if np.isnan(u): o.append("    --     "); continue
        p = pa[int(v * S), int(u * S)]
        s = (p.max() - p.min()) / max(p.max(), 1)
        o.append("%02x%02x%02x%s%02d" % (*shot[y, x], "E" if E[int(v * S), int(u * S)] else ":", int(s * 99)))
    print(y, " ".join(o))
