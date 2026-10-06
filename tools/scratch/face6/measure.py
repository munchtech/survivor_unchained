"""measure.py ref.png[:left] img ... : each image's face proportions against the reference's (MediaPipe), one line each."""
import sys
import numpy as np
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2f7b0f1283f6144a\tools\assets")
import face_fit as ff  # noqa: E402

KEYS = ["iod_fw", "eyemouth_fl", "jaw_fw", "chin_fw", "mouth_fw", "nose_fw", "lipl_u", "fl_fw", "eyew_fw", "nose_len", "chin_len", "brow_eye", "lips_h"]


def ratios(L):
    pup = (L[468] + L[473]) / 2
    fw = np.linalg.norm(L[234] - L[454])
    fl = np.linalg.norm(L[10] - L[152])
    return dict(iod_fw=np.linalg.norm(L[468] - L[473]) / fw, eyemouth_fl=np.linalg.norm(pup - (L[13] + L[14]) / 2) / fl,
                jaw_fw=np.linalg.norm(L[172] - L[397]) / fw, chin_fw=np.linalg.norm(L[149] - L[378]) / fw,
                mouth_fw=np.linalg.norm(L[61] - L[291]) / fw, nose_fw=np.linalg.norm(L[129] - L[358]) / fw,
                lipl_u=np.linalg.norm(L[14] - L[17]) / max(np.linalg.norm(L[0] - L[13]), 1e-6), fl_fw=fl / fw,
                eyew_fw=(np.linalg.norm(L[33] - L[133]) + np.linalg.norm(L[263] - L[362])) / 2 / fw,
                nose_len=np.linalg.norm(L[168] - L[2]) / fl, chin_len=np.linalg.norm(L[17] - L[152]) / fl,
                brow_eye=np.linalg.norm(L[105] - L[159]) / fl, lips_h=np.linalg.norm(L[0] - L[17]) / fl)


ref = sys.argv[1]
part = "whole"
if ref.endswith(":left"):
    ref, part = ref[:-5], "left"
R = ratios(ff.detect(ff.load(ref, part)[0])[:, :2])
print("%-14s" % "ref" + " ".join("%9s" % k[:9] for k in KEYS))
print("%-14s" % "" + " ".join("%9.3f" % R[k] for k in KEYS))
for p in sys.argv[2:]:
    L = ff.detect(ff.load(p)[0])
    if L is None:
        print(p, "no face")
        continue
    r = ratios(L[:, :2])
    err = np.mean([abs(r[k] / R[k] - 1) for k in KEYS])
    print("%-14s" % p.replace("\\", "/").split("/")[-1][:14] + " ".join("%+8.0f%%" % (100 * (r[k] / R[k] - 1)) for k in KEYS) + "  mean %.1f%%" % (100 * err))
