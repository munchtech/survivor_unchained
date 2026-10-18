"""Face 30 H1b: decode the UV probes (People.H1Debug uv10/uv11) to her head's UV at given pixels.
    from uvdecode import uv_at; uv_at(prefix) -> (H, W, 2) UV, nan off her head"""
import numpy as np
from PIL import Image
SH = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\.shots"
def lin(a):
    a = a / 255.0
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
def uv_at(prefix):
    c = lin(np.asarray(Image.open(SH + "/" + prefix + "_uv10.png").convert("RGB")).astype(float))
    f = lin(np.asarray(Image.open(SH + "/" + prefix + "_uv11.png").convert("RGB")).astype(float))
    uc = c[..., :2] / np.maximum(c[..., 2:3], 1e-6)
    uf = f[..., :2] / np.maximum(f[..., 2:3], 1e-6)
    k = np.round(16 * uc - uf)
    uv = (k + uf) / 16
    ok = (c[..., 2] > 0.02) & (np.abs(c[..., 2] - f[..., 2]) < 0.05 * c[..., 2]) & (np.abs(16 * uc - uf - k) < 0.3).all(-1)
    uv[~ok] = np.nan
    return uv
