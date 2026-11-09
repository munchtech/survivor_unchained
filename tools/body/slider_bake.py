#!/usr/bin/env python
"""P1 B1 step 2: the slider catalogue (catalogue.json) baked as blend targets on OUR topology.

    python tools/body/slider_bake.py                 # takes a blender turn: every hm08 slider body in ONE Blender run,
                                                     # then the bake and its check (numpy)
    python tools/body/slider_bake.py --no-blender    # the bake and check again from tools/body/out/slider_bake/hm.npz

Writes tools/body/base/sliders_{close,play}.npz (+ tools/body/base/sliders.json: the index and the check) and
tools/body/out/slider_bake/hm.npz (the MPFB bodies, MakeHuman space: regenerable, git-ignored).

Derived from: (b) MakeHuman's macros and targets (CC0) through MPFB as the shape reference, read at sampled values;
(c) catalogue.json's sliders (names, ranges, what each lays) inherited as they are; (a) the game's need: targets on
OUR vertex order (topo_build.py's fixed order), evaluated with numpy alone (sliders.py `OurSliders`), so the app and
the build never need MakeHuman or Blender to shape her.

Method: for each slider, MPFB builds the hm08 body at the stored samples (`samples`: -1, -0.5, +0.5, +1 of its range,
clipped to it; quarter steps for macro sliders and one-sided ones, eighths for one-sided macros) and, for the check only, at the midpoints between them (CHECKS); each body
is hung from the head and placed as the reference was (topo_corr.Reference.close: pipeline stages 2-3), carried onto
our vertices by the correspondence (topo_corr.evaluate), and its move from the reference (the same carry of the
reference, so the correspondence's own error cancels) stored as that sample's target. sliders.py evaluates a body as
the reference plus, per slider, the piecewise-linear blend of its samples (0 at value 0) and sums the sliders.
Check: every stored sample and every midpoint, and MIXES random 6-slider bodies (the additivity error), our evaluated
body vs MPFB's own body through the correspondence: p95 <= 1.0 mm, max <= 3 mm.
"""
import json
import os
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
BLENDER = r"C:\Users\munch\Tools\blender-4.5.14-windows-x64\blender.exe"
TURN = os.path.join(r"C:\Users\munch\Desktop\survivorsunchained", "tools", "turn.py")
OUT = os.path.join(HERE, "out", "slider_bake")
BASE_DIR = os.path.join(HERE, "base")
SPEC = os.path.join(HERE, "specs", "base_woman.json")
MIXES, MIX_N, SEED = 6, 6, 20261104
UNIT_M = 1e-5            # the targets' storage step (0.01 mm), far under the check's 1 mm

try:
    import bpy  # noqa: F401
    IN_BLENDER = True
except ImportError:
    IN_BLENDER = False


def macro_knots(c, spec):
    """(b) MPFB's macro.json: each macro is piecewise linear between its parts' bounds (and the height's dead zone
    0.49..0.51: no height target at all within it, measured as a 7 mm miss at +0.125 with knots at 0 and 0.25); the
    slider values where a macro it lays crosses a bound become knots."""
    path = os.path.join(os.environ.get("APPDATA", ""), "Blender Foundation", "Blender", "4.5", "extensions",
                        "user_default", "mpfb", "data", "targets", "macrodetails", "macro.json")
    with open(path) as f:
        mt = json.load(f)["macrotargets"]
    lo, hi = c["range"]
    out = set()
    for m, k in c.get("macros", {}).items():
        for part in mt[m]["parts"]:
            for b in (part["lowest"], part["highest"]):
                v = round((b - spec["macros"][m]) / k, 4)
                if lo <= v <= hi and abs(v) > 1e-3:
                    out.add(v)
    return out


def samples(lo, hi, macro=False, extra=()):
    """(stored, checks): stored = -1, -0.5, +0.5, +1 of the range's sides (a side with a reach under 1: its half and
    its end); a slider laying MPFB macros (nonlinear: height and gender bend most near the base value, measured: 7 mm
    off at +/-0.25 with half steps) at quarter steps; a one-sided slider at quarter steps (eighths with macros); checks
    = the midpoints between neighbours (0 included as a neighbour)."""
    st = []
    for end in (lo, hi):
        if end == 0:
            continue
        one = lo == 0 or hi == 0
        n = (8 if macro else 4) if one else (4 if macro else 2)
        st += [end * k / n for k in range(1, n + 1)]
    st = sorted(set(round(x, 6) for x in st) | set(extra))
    st = [x for i, x in enumerate(st) if i == 0 or x - st[i - 1] > 2e-3]
    knots = sorted(set(st + [0.0]))
    ch = [round(0.5 * (a + b), 6) for a, b in zip(knots, knots[1:])]
    return st, ch


def jobs():
    import sliders
    cat = sliders.catalogue()
    spec = sliders.load_spec(SPEC)
    out = [{"id": "ref", "sliders": {}}]
    for name, c in cat.items():
        st, ch = samples(*c["range"], macro=bool(c.get("macros")), extra=macro_knots(c, spec))
        out += [{"id": f"{name}@{v:+.4f}", "slider": name, "v": v, "kind": "sample", "sliders": {name: v}} for v in st]
        out += [{"id": f"{name}@{v:+.4f}", "slider": name, "v": v, "kind": "check", "sliders": {name: v}} for v in ch]
    rng = np.random.default_rng(SEED)
    names = sorted(cat)
    for m in range(MIXES):
        pick = sorted(rng.choice(len(names), MIX_N, replace=False))
        s = {}
        for i in pick:
            lo, hi = cat[names[i]]["range"]
            s[names[i]] = round(float(rng.uniform(lo, hi)), 4)
        out.append({"id": f"mix{m}", "kind": "mix", "sliders": s})
    return out


def blender_main():
    import mh_base
    import sliders
    spec = sliders.load_spec(SPEC)
    js = jobs()
    V = []
    t0 = time.time()
    for j in js:
        macros, targets = sliders.resolve({**spec, "sliders": j["sliders"]})
        V.append(mh_base.human(spec, macros, targets)[1])
        print("BAKE", j["id"], round(time.time() - t0, 1), flush=True)
    os.makedirs(OUT, exist_ok=True)
    np.savez(os.path.join(OUT, "hm.npz"), V=np.stack(V), ids=np.array([j["id"] for j in js]))


def stats_mm(D):
    e = np.linalg.norm(D, axis=-1).ravel() * 1000
    return {"p95": round(float(np.percentile(e, 95)), 4), "max": round(float(e.max()), 4)}


def bake():
    import topo_corr as tc
    import sliders
    z = np.load(os.path.join(OUT, "hm.npz"))
    HV, ids = z["V"], list(z["ids"])
    js = {j["id"]: j for j in jobs()}
    assert set(ids) == set(js), "hm.npz is from another job list: run with Blender again"
    ref = tc.Reference()
    d_ref = np.abs(HV[ids.index("ref")] - ref.base["V"]).max()
    print("MPFB's reference body vs run_a base.npz, max m:", d_ref)
    assert d_ref < 1e-6
    t = time.time()
    closes = {i: ref.close(HV[k]) for k, i in enumerate(ids)}
    print("placed", len(closes), "bodies", round(time.time() - t, 1), "s")
    cat = sliders.catalogue()
    index = {"about": "P1 B1 step 2 (slider_bake.py): catalogue.json's sliders as targets on OUR topology; per slider its "
                      "stored sample values (piecewise-linear, 0 at value 0). sliders.py OurSliders evaluates them.",
             "sliders": {}, "check": {}}
    for tier in ("close", "play"):
        corr = tc.load(tier)
        V0 = tc.evaluate(corr, closes["ref"])
        ours = {i: tc.evaluate(corr, P) - V0 for i, P in closes.items()}
        arrays = {"V0": V0.astype(np.float64), "names": np.array(sorted(cat)), "d_unit_m": np.float64(UNIT_M)}
        for name in sorted(cat):
            st = [j for j in js.values() if j.get("slider") == name and j["kind"] == "sample"]
            st.sort(key=lambda j: j["v"])
            arrays[f"v:{name}"] = np.array([j["v"] for j in st])
            d = np.stack([ours[j["id"]] for j in st])
            arrays[f"d:{name}"] = np.round(d / UNIT_M).astype(np.int32)     # (whole 0.01 mm: the file packs ~3x)
            index["sliders"][name] = {"range": cat[name]["range"], "samples": [j["v"] for j in st]}
        path = os.path.join(BASE_DIR, f"sliders_{tier}.npz")
        np.savez_compressed(path, **arrays)
        ev = sliders.OurSliders(path)
        chk = {"sample": [], "check": [], "mix": []}
        worst = {}
        for i, j in js.items():
            if i == "ref":
                continue
            D = ev.evaluate(j["sliders"]) - (V0 + ours[i])
            s = stats_mm(D)
            chk[j["kind"]].append(s)
            if j["kind"] == "mix":
                worst[i] = {"sliders": j["sliders"], **s}
            elif s["max"] > worst.get(j["kind"] + "_worst", {"max": -1})["max"]:
                worst[j["kind"] + "_worst"] = {"id": i, **s}
        res = {k: {"n": len(v), "p95_worst": max(x["p95"] for x in v), "max_worst": max(x["max"] for x in v)}
               for k, v in chk.items()}
        res["detail"] = worst
        res["pass"] = bool(all(r["p95_worst"] <= 1.0 and r["max_worst"] <= 3.0 for k, r in res.items()
                               if k in chk))
        res["file_mb"] = round(os.path.getsize(path) / 1e6, 2)
        index["check"][tier] = res
        print(tier, json.dumps({k: v for k, v in res.items() if k != "detail"}))
        for k, v in worst.items():
            print("  ", k, v)
    with open(os.path.join(BASE_DIR, "sliders.json"), "w") as f:
        json.dump(index, f, indent=1)
    return index


def main():
    if IN_BLENDER:
        blender_main()
        return
    if "--no-blender" not in sys.argv:
        os.makedirs(OUT, exist_ok=True)
        subprocess.run([sys.executable, TURN, "take", "blender", "body-p1: slider bake", "--wait", "600", "--stale-ok"], check=True)
        try:
            r = subprocess.run([BLENDER, "-b", "--python-exit-code", "1", "--python", os.path.abspath(__file__)])
        finally:
            subprocess.run([sys.executable, TURN, "give", "blender", "body-p1: slider bake"])
        if r.returncode:
            sys.exit(r.returncode)
    bake()


if __name__ == "__main__":
    main()
