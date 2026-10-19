"""hand lower down the scabbard (s) x elbow swivel (t): python scan4.py "s1,s2" "t1,t2" """
import sys
from ev import *
from opt import rotv, hilt_of
X = [-0.1569, 0.06, -0.025, 7.359, 3.2895, -72.1558, 4.7238]
FL = [0, 5, 10, 15]
for s in [float(a) for a in sys.argv[1].split(",")]:
    x = list(X); x[0] = s
    h0 = hilt_of(np.array(x)); h0.update(pole_chest=1.0, clav=0.0)
    c0 = apply("run_warden_town", h0, [0]); G0 = Gframes(c0)[0]; P0 = G0[I["pelvis"]][:3, :3]
    ax = P0.T @ (G0[I["hand_l"]][:3, 3] - G0[I["upperarm_l"]][:3, 3])
    for t in [float(a) for a in sys.argv[2].split(",")]:
        h = dict(h0); h["pole"] = tuple(np.round(rotv(np.array(h0["pole"]), ax, t), 4))
        L = []
        for nm, fl in (("run_warden_town", FL), ("sprint_warden_town", [0, 10])):
            c = apply(nm, h); Gs = Gframes(c)
            for r in measure(c, fl=fl, clrs=("warden", "reaver")):
                G = Gs[r["f"]]; S, E = (G[I[b]][:3, 3] for b in ("upperarm_l", "lowerarm_l"))
                L.append((r["el"], r["wr"], max(r[(cl, XK[0], "a")] for cl in ("warden", "reaver")), max(r[(cl, XK[1], "a")] for cl in ("warden", "reaver")),
                          max(r[("warden", k, "a")] for k in KEYS), max(r[("reaver", k, "a")] for k in KEYS), min(r[("warden", k, "p")] for k in KEYS), max(r[("warden", k, "p")] for k in KEYS), (E - S)[0], (E - S)[2]))
        A = np.array(L)
        print(f"s {s:.3f} t {t:+.0f} | el {A[:,0].min():.0f}-{A[:,0].max():.0f} wr {A[:,1].min():.0f}-{A[:,1].max():.0f} shield {A[:,2].max():.1f} xbow {A[:,3].max():.1f} swordW {A[:,4].max():.1f} swordR {A[:,5].max():.1f} palm {A[:,6].min():.1f}-{A[:,7].max():.1f} Ex {A[:,8].min()*100:.1f}-{A[:,8].max()*100:.1f} Ez {A[:,9].min()*100:.1f}-{A[:,9].max()*100:.1f}", flush=True)
