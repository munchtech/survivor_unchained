"""m2.py FACE SHOT [SHOT...]: one line per shot (godot/.shots/SHOT.png, front view of FACE at the Look): meas.py's cheek,
jaw, lit neck; neckx.py's rows (.15, .30: hue off the lit neck, least C share, largest 4 px L step) and far-neck box;
and the portrait's lit neck and neck-side shade (the targets). --json: also print the numbers as JSON (for fits).
Run with the facefit venv."""
import sys, os, json
import numpy as np
H = os.path.dirname(os.path.abspath(__file__))
for d in ("face17", "face19", "face21"): sys.path.insert(0, os.path.join(H, "..", d))
import meas, neckx, farneck_portrait as fp  # noqa

def lab(v): return np.array([v[0], v[1] * np.cos(np.radians(v[2])), v[1] * np.sin(np.radians(v[2]))])

def one(face, shot):
    p = os.path.join(meas.S, shot + ".png")
    m, _ = neckx.measure(p)
    sp = meas.spots(p)[0]
    r = {k: m["rows"][t] for k, t in (("r15", 0.15), ("r30", 0.3))}
    return dict(cheek=sp["cheek"], jaw=sp["jaw"], neck=sp["neck"], far=m["fn"],
                r15=(r["r15"]["dh"], r["r15"]["cmin"], r["r15"]["step"], r["r15"]["hmean"], r["r15"]["cmean"]),
                r30=(r["r30"]["dh"], r["r30"]["cmin"], r["r30"]["step"], r["r30"]["hmean"], r["r30"]["cmean"]))

def portrait(face):
    pp = os.path.join(meas.R, ("own_her_23" if face == "own" else face + "_11") + ".png")
    sp = meas.spots(pp)[0]
    (_, vp), _ = fp.spot(pp)
    return dict(cheek=sp["cheek"], jaw=sp["jaw"], neck=sp["neck"], shade=vp)

if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    face, shots = a[0], a[1:]
    pt = portrait(face); f = meas.f
    print("%s portrait: cheek %s jaw %s neck %s shade %s" % (face, f(pt["cheek"]), f(pt["jaw"]), f(pt["neck"]), f(pt["shade"])))
    out = {"portrait": pt}
    for s in shots:
        q = one(face, s); out[s] = q
        print("%-16s ck %s jw %s nk %s | far %s dC%+4.0f%% dh%+3.0f | r15 %+4.0f %3.0f%% %.3f h%2.0f C.%03d | r30 %+4.0f %3.0f%% %.3f h%2.0f C.%03d" % (
            s, f(q["cheek"]), f(q["jaw"]), f(q["neck"]), f(q["far"]), (q["far"][1] / pt["shade"][1] - 1) * 100,
            (q["far"][2] - pt["shade"][2] + 180) % 360 - 180,
            q["r15"][0], q["r15"][1] * 100, q["r15"][2], q["r15"][3], q["r15"][4] * 1000,
            q["r30"][0], q["r30"][1] * 100, q["r30"][2], q["r30"][3], q["r30"][4] * 1000))
    if "--json" in sys.argv:
        print(json.dumps(out, default=lambda o: o.tolist() if hasattr(o, "tolist") else float(o)))
