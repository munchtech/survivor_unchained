"""softfit.py TAG1 TAGH [LO HI]: per face, the soft_tone (linear, per channel) that takes its jaw spot to its portrait's,
from TAG1_FACE (soft_tone 1) and TAGH_FACE (0.5 grey): the jaw's light is K + S * t per channel. Clamped to LO..HI;
prints what it then reaches (Oklab L, C, h)."""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import meas  # noqa
M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566], [0.0883024619, 0.2817188376, 0.6299787005]])
M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099], [0.0259040371, 0.7827717662, -0.8086757660]])
def lab2lin(L, C, h):
    lab = np.array([L, C * np.cos(np.radians(h)), C * np.sin(np.radians(h))])
    return np.linalg.inv(M1) @ (np.linalg.inv(M2) @ lab) ** 3
def lin2lch(c):
    L, A, B = M2 @ np.cbrt(M1 @ np.maximum(c, 1e-6))
    return L, np.hypot(A, B), np.degrees(np.arctan2(B, A))
t1, th = sys.argv[1], sys.argv[2]
lo, hi = (float(sys.argv[3]), float(sys.argv[4])) if len(sys.argv) > 4 else (0.25, 2.5)
keepL = os.environ.get('KEEPL') == '1'   # (the jaw's lightness kept, only its chroma and hue to the portrait's)
import re
cur = {}   # (env CUR=1: TAG1 was shot at People.cs's HerSoftTone, not at 1)
if os.environ.get('CUR') == '1':
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'godot', 'src', 'Actors', 'People.cs'), encoding='utf-8-sig').read()
    blk = src[src.index('Dictionary<string, Vector3> HerSoftTone'):]; blk = blk[:blk.index('};')]
    cur = {m.group(1): np.array([float(m.group(i)) for i in (2, 3, 4)]) for m in re.finditer(r'\["(\w+)"\] = new\(([\d.]+)f, ([\d.]+)f, ([\d.]+)f\)', blk)}
faces = ['own', 'highborn', 'doe', 'sunborn', 'vixen', 'moonlit', 'saffron', 'wildling', 'hardwon', 'fey']
for fc in faces:
    a = meas.spots(os.path.join(meas.S, "%s_%s.png" % (t1, fc)))[0]["jaw"]
    b = meas.spots(os.path.join(meas.S, "%s_%s.png" % (th, fc)))[0]["jaw"]
    r = meas.spots(os.path.join(meas.R, ("own_her_23" if fc == "own" else fc + "_11") + ".png"))[0]["jaw"]
    J1, Jh, T = lab2lin(*a), lab2lin(*b), lab2lin(a[0] if keepL else r[0], r[1], r[2])
    t0 = cur.get(fc, np.ones(3))
    deg = np.abs(t0 - 0.5) < 0.05   # (a channel already at 0.5: no slope from this pair; it stays)
    S = (J1 - Jh) / np.where(deg, 1, t0 - 0.5); K = Jh - 0.5 * S
    t = np.where(deg, t0, np.clip((T - K) / np.maximum(S, 1e-6), lo, hi))
    got = lin2lch(K + S * t)
    print("%-9s soft share %.2f | now L.%02d C.%.3f h%2.0f -> L.%02d C.%.3f h%2.0f (portrait L.%02d C.%.3f h%2.0f) | soft_tone (%.3f, %.3f, %.3f)"
          % (fc, float((S * t0 / J1).mean()), a[0] * 100, a[1], a[2], got[0] * 100, got[1], got[2], r[0] * 100, r[1], r[2], *t))
