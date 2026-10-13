"""lowface.py TAG: her lower face against each portrait's (judge j6 (g)1): lip-to-chin over eye-to-lip, from the
Look's front shot TAG_FACE (pupils' mean, the mouth's middle, the chin), and its pitch hint (nose tip to the eye line
over eye-to-lip). Accept within 5%."""
import sys, os
import numpy as np
from PIL import Image
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\tools\scratch\face17")
import meas  # noqa


def ratios(p):
    L = meas.ff.detect(np.asarray(Image.open(p).convert("RGB")))[:, :2]
    eye = (L[468] + L[473]) / 2; lip = (L[13] + L[14]) / 2; chin = L[152]; nose = L[1]
    el = np.linalg.norm(lip - eye)
    return np.linalg.norm(chin - lip) / el, np.linalg.norm(nose - eye) / el


tag = sys.argv[1]
print("%-9s %-14s %-14s %s" % ("face", "render lc/el", "portrait", "miss  (nose/el render, portrait)"))
for fc in sys.argv[2:] or ['own', 'highborn', 'doe', 'sunborn', 'vixen', 'moonlit', 'saffron', 'wildling', 'hardwon', 'fey']:
    r, rn = ratios(os.path.join(meas.S, "%s_%s.png" % (tag, fc)))
    q, qn = ratios(os.path.join(meas.R, ("own_her_23" if fc == "own" else fc + "_11") + ".png"))
    print("%-9s %.3f          %.3f          %+5.1f%%  (%.3f, %.3f)" % (fc, r, q, (r / q - 1) * 100, rn, qn))
