"""overlay.py out.jpg render.png ref.png[:left|right] : the ref's landmarks (similarity-aligned) drawn over the render's.
Green: render; red: reference. Prints key proportions of each."""
import sys
import numpy as np
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7905c3e498df9528\tools\assets")
import face_fit as ff  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

out, ren, ref = sys.argv[1:4]
rpart = "whole"
if ref.endswith(":left") or ref.endswith(":right"):
    ref, rpart = ref.rsplit(":", 1)
part = "whole"
if ren.endswith(":left") or ren.endswith(":right"):
    ren, part = ren.rsplit(":", 1)
A, _ = ff.load(ren, part)
B, _ = ff.load(ref, rpart)
Fa, Fb = ff.detect(A), ff.detect(B)
La, Lb = Fa[:, :2], Fb[:, :2]
idx = sorted(set(ff.OVAL + ff.EYES + ff.BROWS + ff.NOSE + ff.LIPS))
a, b = La[idx], Lb[idx]
ma, mb = a.mean(0), b.mean(0)
aa, bb = a - ma, b - mb
U, S, Vt = np.linalg.svd(bb.T @ aa)
R = (U @ Vt).T
s = S.sum() / (bb ** 2).sum()
Lb2 = (s * (R @ (Lb - mb).T)).T + ma
img = Image.fromarray(np.ascontiguousarray(A)).convert("RGB")
d = ImageDraw.Draw(img)


def poly(L, ids, col, close=True):
    pts = [tuple(L[i]) for i in ids] + ([tuple(L[ids[0]])] if close else [])
    d.line(pts, fill=col, width=2)


for L, col in ((La, (60, 255, 60)), (Lb2, (255, 60, 60))):
    poly(L, ff.OVAL, col)
    poly(L, [33, 246, 161, 160, 159, 158, 157, 173, 133, 155, 154, 153, 145, 144, 163, 7], col)
    poly(L, [263, 466, 388, 387, 386, 385, 384, 398, 362, 382, 381, 380, 374, 373, 390, 249], col)
    poly(L, [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291, 375, 321, 405, 314, 17, 84, 181, 91, 146], col)
    poly(L, [78, 191, 80, 81, 82, 13, 312, 311, 310, 415, 308], col, False)
    poly(L, [70, 63, 105, 66, 107], col, False)
    poly(L, [300, 293, 334, 296, 336], col, False)
    poly(L, [168, 6, 197, 195, 5, 4, 1], col, False)
    poly(L, [129, 98, 2, 327, 358], col, False)


def ratios(L):
    pup = (L[468] + L[473]) / 2
    iod = np.linalg.norm(L[468] - L[473])
    fw = np.linalg.norm(L[234] - L[454])
    fl = np.linalg.norm(L[10] - L[152])
    return dict(iod_fw=iod / fw, eyemouth_fl=np.linalg.norm(pup - (L[13] + L[14]) / 2) / fl,
                jaw_fw=np.linalg.norm(L[172] - L[397]) / fw, chin_fw=np.linalg.norm(L[149] - L[378]) / fw,
                mouth_fw=np.linalg.norm(L[61] - L[291]) / fw, nose_fw=np.linalg.norm(L[129] - L[358]) / fw,
                lipl_u=np.linalg.norm(L[14] - L[17]) / max(np.linalg.norm(L[0] - L[13]), 1e-6), fl_fw=fl / fw,
                eyew_fw=(np.linalg.norm(L[33] - L[133]) + np.linalg.norm(L[263] - L[362])) / 2 / fw,
                nose_len=np.linalg.norm(L[168] - L[2]) / fl, chin_len=np.linalg.norm(L[17] - L[152]) / fl,
                brow_eye=np.linalg.norm(L[105] - L[159]) / fl)


ra, rb = ratios(La), ratios(Lb)
for k in ra:
    print("%-12s render %.3f  ref %.3f  (%+.0f%%)" % (k, ra[k], rb[k], 100 * (ra[k] / rb[k] - 1)))
img.save(out, quality=92)
