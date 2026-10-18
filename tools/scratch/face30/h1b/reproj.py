"""Face 30 H1b: the shot beside her head's maps laid on it by the UV probe: red her ear's texels (zeroed), green the
scalp tint, blue the behind-her-ear weight.
    python reproj.py <diag.npz> <out.png> prefix:x0:y0:x1:y1 ...   (prefix e.g. h1d_own_pixie_t180)"""
import os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uvdecode import uv_at, SH
z = np.load(sys.argv[1]); S = 1024
def img(vals):
    a = np.zeros((S, S)); a[z["rows"], z["cols"]] = vals; return a[::-1]
E, W, G = img(z["ear_tex"].astype(float)), img(z["w"]), z["sh"][::-1]
rows = []
for spec in sys.argv[3:]:
    pre, x0, y0, x1, y1 = spec.split(":"); x0, y0, x1, y1 = map(int, (x0, y0, x1, y1))
    uv = uv_at(pre)[y0:y1, x0:x1]
    shot = np.asarray(Image.open(os.path.join(SH, pre + "_base.png")).convert("RGB"))[y0:y1, x0:x1].astype(float) / 255
    ok = ~np.isnan(uv[..., 0])
    r = np.clip((np.nan_to_num(uv[..., 1]) * S).astype(int), 0, S - 1); c = np.clip((np.nan_to_num(uv[..., 0]) * S).astype(int), 0, S - 1)
    m = np.stack([E[r, c], G[r, c], W[r, c]], -1) * ok[..., None]
    rows.append(np.kron(np.concatenate([shot, m], 1), np.ones((3, 3, 1))))
Image.fromarray((np.concatenate(rows, 0) * 255).astype(np.uint8)).save(sys.argv[2])
