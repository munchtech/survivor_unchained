"""scan the elbow's swivel: pole as world dirs at frame 0 -> pelvis frame. python scan2.py"""
import itertools, sys
from ev import *
c0 = apply("run_warden_town", dict(R.HILT), [0])
G0 = Gframes(c0)[0]; R0 = G0[I["pelvis"]][:3, :3]
FL = [0, 5, 10, 15]
def run(pw, extra={}):
    pw = np.array(pw, float); pw /= np.linalg.norm(pw)
    h = dict(R.HILT); h["pole"] = tuple((R0.T @ pw).round(4)); h.update(extra)
    out = []
    for nm, fl in (("run_warden_town", FL), ("sprint_warden_town", [0, 10])):
        c = apply(nm, h)
        Gs = Gframes(c)
        rows = measure(c, fl=fl, clrs=("warden", "reaver"))
        for r in rows:
            G = Gs[r["f"]]; S = G[I["upperarm_l"]][:3, 3]; E = G[I["lowerarm_l"]][:3, 3]; P = G[I["pelvis"]][:3, :3]
            e = P.T @ (E - S)  # elbow from shoulder, pelvis frame
            out.append((nm[:2], r["f"], r["el"], r["wr"], max(r[(cl, XK[0], "a")] for cl in ("warden", "reaver")), max(r[(cl, XK[1], "a")] for cl in ("warden", "reaver")),
                        max(r[(cl, k, "a")] for cl in ("warden", "reaver") for k in KEYS), min(r[("warden", k, "p")] for k in KEYS), E - S))
    return h["pole"], out
for ex, ez in [(0.17, -0.11), (0.12, -0.06), (0.12, -0.02), (0.09, -0.04), (0.09, 0.0), (0.07, 0.02)]:
    pole, out = run((ex, -0.15, ez))
    print(f"want ({ex},{ez}) pole {pole}")
    for o in out:
        print(f"  {o[0]} f{o[1]:2d} el {o[2]:5.1f} wr {o[3]:4.1f} shield {o[4]:4.1f} xbow {o[5]:4.1f} sword {o[6]:4.1f} palm {o[7]:4.1f} E-S {np.round(o[8],3)}", flush=True)
