"""swivel the elbow about shoulder->hand: python scan3.py t1 t2 ...  (deg). E-S printed in WORLD (x her left, z forward)."""
import sys
from ev import *
from opt import rotv
c0 = apply("run_warden_town", dict(R.HILT), [0]); G0 = Gframes(c0)[0]
P0 = G0[I["pelvis"]][:3, :3]
ax = P0.T @ (G0[I["hand_l"]][:3, 3] - G0[I["upperarm_l"]][:3, 3])
FL = [0, 5, 10, 15]
for t in [float(a) for a in sys.argv[1:]]:
    h = dict(R.HILT); h["pole"] = tuple(np.round(rotv(np.array(R.HILT["pole"]), ax, t), 4))
    print(f"swivel {t:+.0f} pole {h['pole']}")
    for nm, fl in (("run_warden_town", FL), ("sprint_warden_town", [0, 10])):
        c = apply(nm, h); Gs = Gframes(c)
        for r in measure(c, fl=fl, clrs=("warden", "reaver")):
            G = Gs[r["f"]]; S, E, H = (G[I[b]][:3, 3] for b in ("upperarm_l", "lowerarm_l", "hand_l"))
            sh = max(r[(cl, XK[0], "a")] for cl in ("warden", "reaver")); xb = max(r[(cl, XK[1], "a")] for cl in ("warden", "reaver"))
            sw = max(r[(cl, k, "a")] for cl in ("warden", "reaver") for k in KEYS); pa = min(r[("warden", k, "p")] for k in KEYS)
            print(f"  {nm[:2]} f{r['f']:2d} wr {r['wr']:4.1f} shield {sh:4.1f} xbow {xb:4.1f} sword {sw:4.1f} palm {pa:4.1f} E-S {np.round(E-S,3)} H-E {np.round(H-E,3)}", flush=True)
