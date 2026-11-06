"""P1 R1: the design sheet's rules, measured (tools/body/form_rules.json). The judge reads rules, not a copy of A:
every rule is a number on the built body at rest with a band, and A's number is information only.

    python tools/body/formrules.py BODY.glb [--out DIR]          (also check.py --only forms)

Sections: "neck" (the trapezius line under the chin, the neck's girth, the slope), "seam" (the throat seam as one
surface), and the breast and glute sections the form solvers add (their measure functions live here too). Each
rule: {"value", "band": [lo, hi], "ok"}; summary "forms: N of M rules in band" plus the misses.
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


def measure(body_glb, rules=None):
    rules = rules or json.loads(RULES.read_text())
    B = Glb(body_glb)
    from posers import guess_body
    V, T = rest(B, guess_body(B))
    H, HT = rest(B, "HeroineHead")
    ctx = {"V": V, "T": T, "H": H, "HT": HT, "B": B}
    out, miss, n = {}, [], 0
    for sec, rs in rules["sections"].items():
        if sec not in MEASURES:
            continue
        m = MEASURES[sec](ctx)
        out[sec] = {"measured": m, "rules": {}}
        for key, r in rs["rules"].items():
            v = m[key]
            lo, hi = r["band"]
            ok = (lo is None or v >= lo) and (hi is None or v <= hi)
            out[sec]["rules"][key] = {"value": v, "band": r["band"], "ok": bool(ok)}
            n += 1
            if not ok:
                miss.append(f"{sec}.{key} {v} not in {r['band']}")
    out["summary"] = f"forms: {n - len(miss)} of {n} rules in band" + (f"; MISS {'; '.join(miss)}" if miss else "")
    return out


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("body")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    r = measure(a.body)
    print(r["summary"])
    if a.out:
        Path(a.out).mkdir(parents=True, exist_ok=True)
        (Path(a.out) / "forms.json").write_text(json.dumps(r, indent=1))


if __name__ == "__main__":
    main()
