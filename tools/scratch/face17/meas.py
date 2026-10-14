"""meas.py TAG: each face's cheek, jaw (jawR) and neck at landmark spots (Oklab) beside its portrait (_11 and _23),
and the armour's clipped share (max channel >= 250, lower centre of the frame). Run with the facefit venv."""
import sys, os
import numpy as np
from PIL import Image
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\tools\assets")
import face_fit as ff  # noqa
S = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\.shots"
R = r"C:\Users\munch\Desktop\survivorsunchained_inputs\face4\refs_front"
def ok(c):
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566], [0.0883024619, 0.2817188376, 0.6299787005]])
    M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099], [0.0259040371, 0.7827717662, -0.8086757660]])
    return M2 @ np.cbrt(M1 @ c)
def spots(p):
    im = Image.open(p).convert('RGB'); a = np.asarray(im, np.float32) / 255
    up = 2 if im.height < 900 else 1
    L = ff.detect(np.asarray(im.resize((im.width * up, im.height * up), Image.LANCZOS)))[:, :2] / up
    h = np.linalg.norm(L[152] - L[10]); out = {}
    for k, (x, y) in {"cheek": L[205], "jaw": L[136] + [0, 0.07 * h], "neck": L[152] + [0, 0.35 * h]}.items():
        r = max(3, int(0.025 * h)); y0, y1, x0, x1 = int(y - r), int(y + r), int(x - r), int(x + r)
        if y1 >= a.shape[0] or y0 < 0: out[k] = None; continue
        Lk, A, B = ok(np.median(a[y0:y1, x0:x1].reshape(-1, 3), 0))
        out[k] = (Lk, np.hypot(A, B), np.degrees(np.arctan2(B, A)))
    return out, a
def f(v): return "  --  " if v is None else "L.%02d C.%03d h%2.0f" % (round(v[0] * 100), round(v[1] * 1000), v[2])
def main():
    tag = sys.argv[1]; faces = sys.argv[2].split(',') if len(sys.argv) > 2 else ['own', 'highborn', 'doe', 'sunborn', 'vixen', 'moonlit', 'saffron', 'wildling', 'hardwon', 'fey']
    print("%-10s %-20s %-20s %-20s | %-20s %-20s %-20s | clip%%" % ("face", "cheek", "jaw", "neck", "portrait cheek", "jaw", "neck"))
    for fc in faces:
        p = os.path.join(S, "%s_%s.png" % (tag, fc))
        if not os.path.exists(p): print(fc, "missing"); continue
        o, a = spots(p)
        reg = a[760:1080, 600:1320]; clip = (reg.max(2) >= 250 / 255).mean() * 100
        base = fc.split('_')[0]
        rp = os.path.join(R, ("own_her_23" if base == "own" else base + "_11") + ".png")
        r = spots(rp)[0] if os.path.exists(rp) else {"cheek": None, "jaw": None, "neck": None}
        print("%-10s %s %s %s | %s %s %s | %.2f" % (fc[:10], f(o["cheek"]), f(o["jaw"]), f(o["neck"]), f(r["cheek"]), f(r["jaw"]), f(r["neck"]), clip))

if __name__ == "__main__": main()
