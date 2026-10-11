"""liftfit.py TAG LIFT_B: per face, the body lift that takes its neck's L to its portrait's neck-to-cheek ratio, from
two shots TAG_a_FACE (lift 1) and TAG_b_FACE (lift LIFT_B) (meas.py's spots), interpolated in log(lift)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import meas  # noqa
tag, lb = sys.argv[1], float(sys.argv[2])
faces = ['own', 'highborn', 'doe', 'sunborn', 'vixen', 'moonlit', 'saffron', 'wildling', 'hardwon', 'fey']
for fc in faces:
    a, _ = meas.spots(os.path.join(meas.S, "%s_a_%s.png" % (tag, fc)))
    b, _ = meas.spots(os.path.join(meas.S, "%s_b_%s.png" % (tag, fc)))
    r, _ = meas.spots(os.path.join(meas.R, ("own_her_23" if fc == "own" else fc + "_11") + ".png"))
    t = a["cheek"][0] * r["neck"][0] / r["cheek"][0]
    k = (t - a["neck"][0]) / max(b["neck"][0] - a["neck"][0], 1e-4)
    lift = math.exp(k * math.log(lb))
    print("%-9s cheek %.3f neck %.3f -> %.3f (lift %.1f: %.3f) target %.3f | ratio now %.3f portrait %.3f | lift %.3f | neck C %.3f/%.3f portrait %.3f"
          % (fc, a["cheek"][0], a["neck"][0], b["neck"][0], lb, b["neck"][0], t, a["neck"][0] / a["cheek"][0], r["neck"][0] / r["cheek"][0], lift, a["neck"][1], b["neck"][1], r["neck"][1]))
