"""P1 R1: the design sheet's rules, measured (tools/body/form_rules.json). The judge reads rules, not a copy of A:
every rule is a number on the built body at rest with a band, and A's number is information only.

    python tools/body/formrules.py BODY.glb [--spec SPEC.json] [--out DIR]   (also check.py --only forms)

Sections: "neck" (the trapezius line under the chin, the neck's girth, the slope), "seam" (the throat seam as one
surface), and, given the build's spec (--spec, else build.json beside the glb), "breast" (sculpt/breast_measure.py)
and "glutes" (sculpt/glute_measure.py), measured on formview.body(spec) and the spec with the breast sliders at 0.
Each rule: {"value", "band": [lo, hi], "ok"}; summary "forms: N of M rules in band" plus the misses.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from gl import Glb, weld  # noqa: E402

RULES = HERE / "form_rules.json"


def rest(B: Glb, name):
    from headbake import rest_world
    m = B.mesh(name)
    return rest_world(m, B.skeleton())[0], m.T


def vnormals(V, T):
    w = np.asarray(weld(V, 2e-5))
    Vw = np.zeros((w.max() + 1, 3))
    Vw[w] = V
    Tw = w[T]
    fn = np.cross(Vw[Tw[:, 1]] - Vw[Tw[:, 0]], Vw[Tw[:, 2]] - Vw[Tw[:, 0]])
    N = np.zeros_like(Vw)
    for k in range(3):
        np.add.at(N, Tw[:, k], fn)
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    return N[w]


def chin(H):
    hz = H[(np.abs(H[:, 0]) < 0.02) & (H[:, 2] > H[:, 2].mean())]
    return float(hz[:, 1].min())


def neck(V, H):
    """The shoulder top under the chin at 7..17 cm out (both sides averaged, mm, negative below), the neck's width
    2-4 cm under the chin, the trapezius' slope 7 -> 13 cm, and the profile's worst rise outward (a knob or shelf)."""
    c = chin(H)
    xs = [0.07, 0.09, 0.11, 0.13, 0.15, 0.17]
    prof = []
    for x in xs:
        ys = []
        for s in (1, -1):
            sel = V[(np.abs(V[:, 0] * s - x) < 0.004) & (V[:, 1] < c)]
            ys.append(sel[:, 1].max())
        prof.append((float(np.mean(ys)) - c) * 1e3)

    def width(y):
        nb = V[(np.abs(V[:, 1] - y) < 0.003) & (np.abs(V[:, 0]) < 0.12)]
        return float(nb[:, 0].max() - nb[:, 0].min()) * 1e3 if len(nb) else float("nan")
    w = [width(c - k / 100) for k in (2, 3, 4)]
    rise = max(prof[i + 1] - prof[i] for i in range(len(prof) - 1))
    return {"top_under_chin_mm": [round(p, 1) for p in prof], "at_x_cm": [7, 9, 11, 13, 15, 17],
            "top_7cm_mm": round(prof[0], 1), "top_9cm_mm": round(prof[1], 1), "top_17cm_mm": round(prof[-1], 1),
            "width_2_4cm_mm": [round(x, 1) for x in w], "width_max_2_4cm_mm": round(max(w), 1),
            "trap_slope_7_13_deg": round(math.degrees(math.atan2(prof[0] - prof[3], 60.0)), 1),
            "profile_worst_rise_mm": round(rise, 1)}


def seam(V, T, H, HT):
    """Each point of the body's open ring (its boundary at the head) against the head there: the angle between the
    body's normal and the head's (one surface: near 0)."""
    from scipy.spatial import cKDTree
    from gl import boundary_edges
    w = np.asarray(weld(V, 1e-7))
    bv = np.unique(boundary_edges(w[T]))
    first = {}
    for i, r in enumerate(w):
        first.setdefault(int(r), i)
    idx = np.array([first[int(k)] for k in bv])
    d, hi = cKDTree(H).query(V[idx])
    ring = idx[d < 1e-4]
    NB, NH = vnormals(V, T), vnormals(H, HT)
    _, hi = cKDTree(H).query(V[ring])
    ang = np.degrees(np.arccos(np.clip((NB[ring] * NH[hi]).sum(1), -1, 1)))
    return {"ring_points": int(len(ring)), "angle_mean_deg": round(float(ang.mean()), 1),
            "angle_p90_deg": round(float(np.percentile(ang, 90)), 1), "angle_max_deg": round(float(ang.max()), 1)}


MEASURES = {"neck": lambda ctx: neck(ctx["V"], ctx["H"]), "seam": lambda ctx: seam(ctx["V"], ctx["T"], ctx["H"], ctx["HT"])}


BREAST_SLIDERS = ["bust_firmness", "bust_lift", "bust_point", "bust_set", "bust_size", "bust_spacing", "chest_wall",
                  "breast_a", "breast_b", "support_lift", "support_press", "support_fill"]


def _derived(spec_path, zero, keep, tmp):
    """A flat copy of the spec (base merged, as sliders.load_spec) with the `zero` sliders at 0 (the `keep` ones
    restored to the spec's value), written to tmp."""
    from sliders import load_spec
    sp = load_spec(spec_path)
    sl = dict(sp.get("sliders", {}))
    for k in zero:
        sl[k] = sp.get("sliders", {}).get(k, 0.0) if k in keep else 0.0
    sp["sliders"] = sl
    p = Path(tmp) / f"derived_{abs(hash((tuple(sorted(sl.items())), spec_path)))}.json"
    p.write_text(json.dumps(sp))
    return str(p)


def spec_measures(spec_path, body_glb):
    """Breast and glute numbers on the spec's own body (formview.body): sections "breast" and "glutes"."""
    import tempfile
    sys.path.insert(0, str(HERE / "sculpt"))
    import formview
    import breast_measure as bm
    import glute_measure as gm
    from sliders import load_spec
    V, T, H, HT, z, rep = formview.body(spec_path)
    sl = load_spec(spec_path).get("sliders", {})
    with tempfile.TemporaryDirectory() as tmp:
        bare = _derived(spec_path, BREAST_SLIDERS, (), tmp)
        Vb = formview.body(bare)[0]
        if sl.get("breast_a", 0) > 0 or sl.get("breast_b", 0) > 0:
            Vref = formview.body(_derived(spec_path, BREAST_SLIDERS, ("chest_wall",), tmp))[0]
        else:
            Vref = Vb
    b = bm.measure(V, T, Vb, Vref, H, HT, "spec")
    b = {k: v for k, v in b.items() if not k.startswith("_")}
    g = gm.measure(spec_path, V=V, z=z, skel_glb=body_glb)
    g = {k: v for k, v in g.items() if not k.startswith("_")}
    for k in ("apex_y_mm", "apex_z_mm"):
        b[k] = None
    b["apex_y_mm"], b["apex_z_mm"] = b["apex_mm"][1], b["apex_mm"][2]
    b["cleavage_floor_over60"] = g.get("cleavage_floor_over60")
    return {"breast": b, "glutes": g}


def measure(body_glb, rules=None, spec=None):
    rules = rules or json.loads(RULES.read_text())
    if spec is None and (Path(body_glb).parent / "build.json").exists():
        sp = json.loads((Path(body_glb).parent / "build.json").read_text()).get("spec")
        if sp:
            spec = str(HERE.parents[1] / sp)
    B = Glb(body_glb)
    from posers import guess_body
    V, T = rest(B, guess_body(B))
    H, HT = rest(B, "HeroineHead")
    ctx = {"V": V, "T": T, "H": H, "HT": HT, "B": B}
    out, miss, n, skipped = {}, [], 0, []
    extra = spec_measures(spec, body_glb) if spec else {}
    for sec, rs in rules["sections"].items():
        if sec in ("breast", "glutes") and not spec:
            skipped.append(sec)
            continue
        if sec not in MEASURES and sec not in extra:
            continue
        m = MEASURES[sec](ctx) if sec in MEASURES else extra[sec]
        out[sec] = {"measured": m, "rules": {}}
        for key, r in rs["rules"].items():
            v = m.get(key)
            if v is None:
                miss.append(f"{sec}.{key} not measured")
                out[sec]["rules"][key] = {"value": None, "band": r["band"], "ok": False}
                n += 1
                continue
            lo, hi = r["band"]
            ok = (lo is None or v >= lo) and (hi is None or v <= hi)
            out[sec]["rules"][key] = {"value": v, "band": r["band"], "ok": bool(ok)}
            n += 1
            if not ok:
                miss.append(f"{sec}.{key} {v} not in {r['band']}")
    out["summary"] = f"forms: {n - len(miss)} of {n} rules in band" + (f"; MISS {'; '.join(miss)}" if miss else "") + (f" (skipped {','.join(skipped)}: no spec)" if skipped else "")
    return out


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("body")
    ap.add_argument("--spec", help="the body's spec (default: build.json's, beside the glb)")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    r = measure(a.body, spec=a.spec)
    print(r["summary"])
    for sec in ("breast", "glutes"):
        if sec in r:
            print(sec, json.dumps(r[sec]["measured"]))
    if a.out:
        Path(a.out).mkdir(parents=True, exist_ok=True)
        (Path(a.out) / "forms.json").write_text(json.dumps(r, indent=1))


if __name__ == "__main__":
    main()
