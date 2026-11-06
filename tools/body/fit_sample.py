"""The slider fit's samples (wrap.py): MakeHuman's body at each catalogue slider set alone to a few values, in Blender.

    blender -b --python tools/body/fit_sample.py -- <spec.json> <out.npz> [values...] [--sliders a,b,c] [--at a=0.2,b=-0.1]
Writes V0 (the spec's body, with --at's sliders) and, per slider and value, "<slider>@<value>": the body with that
slider moved to it from --at's point (the rest held). Each is MPFB's own evaluation (macros as its nonlinear blends).
"""
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mh_base   # noqa: E402
import sliders   # noqa: E402


def main():
    a = sys.argv[sys.argv.index("--") + 1:]
    spec = sliders.load_spec(a[0])
    out = a[1]
    opt = {k: a[i + 1] for i, k in enumerate(a) if k.startswith("--")}
    vals = [float(x) for x in a[2:] if not x.startswith("--") and x not in opt.values()] or [-1.0, -0.5, 0.5, 1.0]
    cat = sliders.catalogue()
    names = opt["--sliders"].split(",") if "--sliders" in opt else list(cat)
    at = {}
    if "--at" in opt:
        for kv in opt["--at"].split(","):
            k, v = kv.split("=")
            at[k] = float(v)
    res = {}
    t0 = time.time()

    def body(sl):
        s = dict(spec, sliders=sl)
        m, t = sliders.resolve(s, cat)
        return mh_base.human(s, m, t)[1]
    res["V0"] = body(at)
    for n in names:
        lo, hi = cat[n]["range"]
        for v in vals:
            x = at.get(n, 0.0) + v * (hi - lo) / 2
            if x < lo - 1e-9 or x > hi + 1e-9:
                continue
            res[f"{n}@{x:g}"] = body(dict(at, **{n: x}))
    np.savez(out, **res)
    print("SAMPLES", len(res), round(time.time() - t0, 1), "s")


main()
