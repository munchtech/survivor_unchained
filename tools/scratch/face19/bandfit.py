"""bandfit.py TAG LIFT_B [faces]: her lit neck's lift per face fitted on a band (judge j6), at both neck lengths.
Shots (godot/.shots): TAG_a3_FACE, TAG_b3_FACE (--neck-cm -3, lift 1 / LIFT_B) and TAG_a0_FACE, TAG_b0_FACE (today's).
Profile: Oklab L down her neck's middle / her cheek's L, from the chin in pupil-chin steps of 0.1. Band 0.3-0.8 at -3 cm;
at today's length the same anatomy sits 3 cm lower (shifted by 3 cm in the shot's own scale: 6.2 cm between pupils).
Prints, per face: the portrait's band ratio, each shot's, the lift that meets it at each length (log-interpolated), the
one lift for both (the mean of the two in log), and each step's miss at that lift (linear between a and b)."""
import sys, os, math
import numpy as np
from PIL import Image
sys.path.insert(0, "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a2d632df7c7f21ec0/tools/scratch/face17")
import meas  # noqa

STEPS = np.round(np.arange(0.0, 1.21, 0.1), 2)


def profile(p, shift_cm=0.0):
    im = Image.open(p).convert('RGB'); a = np.asarray(im, np.float32) / 255
    up = 2 if im.height < 900 else 1
    L = meas.ff.detect(np.asarray(im.resize((im.width * up, im.height * up))))[:, :2] / up
    pup = (L[468] + L[473]) / 2; chin = L[152]; u = chin[1] - pup[1]; w = max(2, int(0.05 * u))
    ipd = np.linalg.norm(L[468] - L[473])
    sh = shift_cm * (ipd / 6.2) / u
    out = {}
    for t in STEPS:
        y = int(chin[1] + (t + sh) * u)
        if y + 2 >= a.shape[0]: continue
        c = np.median(a[y - 2:y + 3, int(chin[0]) - w:int(chin[0]) + w].reshape(-1, 3), 0)
        out[t] = meas.ok(c)[0]
    ck = meas.spots(p)[0]['cheek'][0]
    return {t: v / ck for t, v in out.items()}, sh


def band(pr): return np.mean([pr[t] for t in STEPS if 0.3 <= t <= 0.8 and t in pr])


tag, lb = sys.argv[1], float(sys.argv[2])
faces = sys.argv[3:] or ['own', 'highborn', 'doe', 'sunborn', 'vixen', 'moonlit', 'saffron', 'wildling', 'hardwon', 'fey']
for fc in faces:
    ref, _ = profile(os.path.join(meas.R, ("own_her_23" if fc == "own" else fc + "_11") + ".png"))
    tgt = band(ref)
    lifts, rows = [], []
    for ln, shift in (("3", 0.0), ("0", 3.0)):
        A, sh = profile(os.path.join(meas.S, "%s_a%s_%s.png" % (tag, ln, fc)), shift)
        B, _ = profile(os.path.join(meas.S, "%s_b%s_%s.png" % (tag, ln, fc)), shift)
        ka = (tgt - band(A)) / max(band(B) - band(A), 1e-4)
        lifts.append(ka * math.log(lb))
        rows.append((ln, A, B, sh))
    lift = math.exp(np.mean(lifts))
    k = math.log(lift) / math.log(lb)
    print("%-9s portrait band %.3f | lift -3: %.3f  today: %.3f  both: %.3f" % (fc, tgt, math.exp(lifts[0]), math.exp(lifts[1]), lift))
    for ln, A, B, sh in rows:
        miss = ["%+.2f" % ((A[t] + k * (B[t] - A[t])) - ref[t]) if t in A and t in B and t in ref else "  -- " for t in STEPS]
        print("   %s (shift %.2f) band at fit %.3f | step miss %s" % (ln, sh, band(A) + k * (band(B) - band(A)), " ".join(miss)))
