"""Face 30 H1b: shot beside custom per-texel maps laid on it (R, G, B from diag.npz expressions).
    python reproj2.py <diag.npz> <out.png> "<R expr>" "<G expr>" "<B expr>" prefix:x0:y0:x1:y1 ...
    exprs see: z (the npz), dflap (each texel's distance to her ear's flap), np"""
import os, sys
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uvdecode import uv_at, SH
z = np.load(sys.argv[1]); S = 1024
dflap = cKDTree(z["V"][z["flap"]]).query(z["P"])[0]
_tp = os.path.join(os.path.dirname(sys.argv[1]), "thick.npz")
thv = np.load(_tp)["th"][cKDTree(z["V"]).query(z["P"])[1]] if os.path.exists(_tp) else None
_kp = os.path.join(os.path.dirname(sys.argv[1]), "thick_keys.npz")
_nn = cKDTree(z["V"]).query(z["P"])[1]
K = {k: v[_nn] / v.max() for k, v in np.load(_kp).items()} if os.path.exists(_kp) else {}
def paint(face=""):
    """each texel's paint (RGB 0-1) of a face's head painting, sampled at 1024"""
    f = "heroine_head%s.jpg" % ("_" + face if face else "")
    a = np.asarray(Image.open(os.path.join(SH, "..", "art", "people", "head_tex", f)).convert("RGB").resize((S, S), Image.BOX)).astype(float) / 255
    return a[::-1][z["rows"], z["cols"]]
def sat(a):
    return (a.max(1) - a.min(1)) / np.maximum(a.max(1), 1e-3)
def satall():
    import glob as _g
    return np.array([sat(paint(os.path.basename(f)[12:-4].lstrip("_"))) for f in sorted(_g.glob(os.path.join(SH, "..", "art", "people", "head_tex", "heroine_head*.jpg")))])
def satmin():
    return satall().min(0)
def img(vals):
    a = np.zeros((S, S)); a[z["rows"], z["cols"]] = vals; return a[::-1]
ch = [img(np.asarray(eval(e), float)) for e in sys.argv[3:6]]
rows = []
for spec in sys.argv[6:]:
    pre, x0, y0, x1, y1 = spec.split(":"); x0, y0, x1, y1 = map(int, (x0, y0, x1, y1))
    uv = uv_at(pre)[y0:y1, x0:x1]
    shot = np.asarray(Image.open(os.path.join(SH, pre + "_base.png")).convert("RGB"))[y0:y1, x0:x1].astype(float) / 255
    ok = ~np.isnan(uv[..., 0])
    r = np.clip((np.nan_to_num(uv[..., 1]) * S).astype(int), 0, S - 1); c = np.clip((np.nan_to_num(uv[..., 0]) * S).astype(int), 0, S - 1)
    m = np.stack([x[r, c] for x in ch], -1) * ok[..., None]
    rows.append(np.kron(np.concatenate([shot, m], 1), np.ones((3, 3, 1))))
Image.fromarray((np.clip(np.concatenate(rows, 0), 0, 1) * 255).astype(np.uint8)).save(sys.argv[2])
