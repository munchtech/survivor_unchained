"""Her forms' check: how close a built body B stands to her shipped body A posed into B's rest (her_target.py).

    python tools/body/formcheck.py <B.glb> --out DIR [--ref godot/art/people/heroine.glb]
Out: forms.json, summary.txt, sheet.png (flat gray clay, orthographic: front, side, back of B beside the posed A).
- distance per region: B's points to A's surface, p50/p95/max mm; and to "symmetric her" (the mean of the signed
  point-to-plane distances to A and to A mirrored: A is not symmetric, B is by rule, so B's floor against A is half
  her own asymmetry, reported too). Regions by B's own skin weights (wrap.A_SETS): neck (0..10 cm under SPLIT), bust,
  torso, hips, thigh, calf (TIGHT, without the blend bands: arm, hand or foot weight 0.05..0.5), arm, hand, foot,
  band;
- the arm's girth: the plane cut's hull perimeter at 10 stations (upper arm 0.2..0.8, forearm 1.2..1.8 of each
  segment from the shoulder), B against A, per side, and the segments' lengths (joint to joint);
- height (the top of all meshes) and the lowest skin point, B against A.
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import headmatch as hm   # noqa: E402
import her_target as ht  # noqa: E402
import surfdist          # noqa: E402
import wrap              # noqa: E402
from gl import Glb       # noqa: E402

STATIONS = np.array([0.2, 0.35, 0.5, 0.65, 0.8, 1.2, 1.35, 1.5, 1.65, 1.8])
REG = ["neck", "bust", "torso", "hips", "thigh", "calf", "arm", "hand", "foot", "band"]
TIGHT = ["neck", "bust", "torso", "hips", "thigh", "calf"]


def set_weights(m, names):
    nb = len(names)
    out = {}
    for k, pre in list(wrap.A_SETS.items()) + [("bust", ("breast_",))]:
        sel = np.array([n.startswith(pre) for n in names])
        out[k] = (m.W * sel[np.clip(m.J, 0, nb - 1)]).sum(1)
    return out


def regions(P, g):
    dep = -hm.s_split(hm.to_blender(P))
    r = np.full(len(P), REG.index("torso"))
    r[g["hips"] > 0.5] = REG.index("hips")
    r[g["bust"] > 0.3] = REG.index("bust")
    for k in ("thigh", "calf", "arm", "hand", "foot"):
        r[g[k] > 0.5] = REG.index(k)
    lim = g["arm"] + g["hand"] + g["foot"]
    r[(lim > 0.05) & (lim <= 0.5)] = REG.index("band")
    r[(dep < 0.10) & np.isin(r, [REG.index("torso"), REG.index("bust")])] = REG.index("neck")
    r[dep < 0.0] = -1
    return r


def stats(d):
    return [round(float(np.percentile(d, 50)) * 1000, 2), round(float(np.percentile(d, 95)) * 1000, 2),
            round(float(d.max()) * 1000, 2)]


def sheet(B, A, path, h_px=420):
    from PIL import Image
    import ray
    PB, TB = B
    PA, TA = A
    lo = min(PB[:, 1].min(), PA[:, 1].min()) - 0.02
    hi = max(PB[:, 1].max(), PA[:, 1].max()) + 0.02
    px = h_px / (hi - lo)
    views = [("front", [1, 0, 0], [0, 0, 1]), ("side", [0, 0, 1], [-1, 0, 0]), ("back", [-1, 0, 0], [0, 0, -1])]
    tiles = []
    for name, ex, cam in views:
        for P, T in ((PB, TB), (PA, TA)):
            v = ray.View([0, 0, 0], ex, [0, 1, 0], cam, px, -0.65, 0.65, lo, hi)
            img, _ = ray.clay(P, T, v)
            tiles.append((np.clip(img, 0, 1) * 255).astype(np.uint8))
    w = tiles[0].shape[1]
    row = np.concatenate([np.concatenate([tiles[2 * i], tiles[2 * i + 1]], 1) for i in range(3)], 1)
    Image.fromarray(row).save(path)
    return row.shape[1], row.shape[0], w


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("glb")
    ap.add_argument("--ref", default=os.path.join(REPO, "godot", "art", "people", "heroine.glb"))
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    tg = ht.target(a.glb, a.ref)
    gb = Glb(a.glb)
    m = gb.mesh("Heroine")
    fs = gb.skeleton(0)
    first, inv = ht.weld(m.P.astype(float))
    P = m.P.astype(float)[first]
    T = inv[m.T]
    g = set_weights(m, fs.names)
    g = {k: v[first] for k, v in g.items()}
    reg = regions(P, g)
    SA = surfdist.Surface(tg["P"], tg["T"])
    SM = surfdist.Surface(tg["P"] * np.array([-1.0, 1, 1]), tg["T"][:, ::-1])
    qa, na, _, da = SA.closest(P)
    qm, nm, _, dm = SM.closest(P)
    sym = np.abs(0.5 * (np.einsum("ij,ij->i", P - qa, na) + np.einsum("ij,ij->i", P - qm, nm)))
    _, _, _, asym = SA.closest(tg["P"] * np.array([-1.0, 1, 1]))
    out = {"glb": os.path.relpath(a.glb, REPO).replace("\\", "/"), "turns_deg": tg["turns"], "regions": {}}
    for i, k in enumerate(REG):
        s = reg == i
        if s.any():
            out["regions"][k] = {"points": int(s.sum()), "to_A_mm": stats(da[s]), "to_symmetric_her_mm": stats(sym[s])}
    tight = np.isin(reg, [REG.index(k) for k in TIGHT])
    out["tight"] = {"to_A_mm": stats(da[tight]), "to_symmetric_her_mm": stats(sym[tight]),
                    "her_asymmetry_mm (A to mirrored A, all her points)": stats(asym)}
    # the arm's girth
    out["arm"] = {}
    nA = len(tg["names"])
    ga = {}
    for k in ("arm", "hand"):
        sel = np.array([n.startswith(wrap.A_SETS[k]) for n in tg["names"]] + [False])
        ga[k] = (tg["W"] * sel[np.clip(tg["J"], 0, nA)]).sum(1)
    for sd in "lr":
        jb = [fs.rest[fs.index[f"{b}_{sd}"]][:3, 3] for b in ("upperarm", "lowerarm", "hand")]
        ja = [tg["bones"][f"{b}_{sd}"][0] for b in ("upperarm", "lowerarm", "hand")]
        sgn = 1 if sd == "l" else -1
        selb = ((g["arm"] + g["hand"]) > 0.3) & (P[:, 0] * sgn > 0)
        selA = ((ga["arm"] + ga["hand"]) > 0.3) & (tg["P"][:, 0] * sgn > 0)
        pb, _ = wrap.section_perims(P, T[selb[T].all(1)], None, jb, STATIONS)
        pa, _ = wrap.section_perims(tg["P"], tg["T"][selA[tg["T"]].all(1)], None, ja, STATIONS)
        out["arm"][sd] = {"stations": STATIONS.tolist(), "B_mm": [round(float(x) * 1000, 1) for x in pb],
                          "A_mm": [round(float(x) * 1000, 1) for x in pa],
                          "err_pct": [round(float(x), 2) for x in (pb / pa - 1) * 100],
                          "segments_B_m": [round(float(np.linalg.norm(jb[1] - jb[0])), 4), round(float(np.linalg.norm(jb[2] - jb[1])), 4)],
                          "segments_A_m": [round(float(np.linalg.norm(ja[1] - ja[0])), 4), round(float(np.linalg.norm(ja[2] - ja[1])), 4)]}
    ref = Glb(a.ref)
    topB = max(float(mm.P[:, 1].max()) for mm in gb.meshes)
    topA = max(float(mm.P[:, 1].max()) for mm in ref.meshes)
    lowA = float(ref.mesh("Heroine").P[:, 1].min())
    out["height"] = {"B_top_m": round(topB, 4), "A_top_m": round(topA, 4), "diff_mm": round((topB - topA) * 1000, 2),
                     "B_lowest_m": round(float(P[:, 1].min()), 5), "A_lowest_m": round(lowA, 5),
                     "feet_diff_mm": round((float(P[:, 1].min()) - lowA) * 1000, 2)}
    W_, H_, _ = sheet((P, T), (tg["P"], tg["T"]), os.path.join(a.out, "sheet.png"))
    out["sheet"] = {"path": "sheet.png", "size": [W_, H_], "order": "front B, front A, side B, side A, back B, back A"}
    with open(os.path.join(a.out, "forms.json"), "w") as f:
        json.dump(out, f, indent=1)
    lines = [f"forms {out['glb']}  (B against her A posed into B's rest)"]
    for k, v in out["regions"].items():
        lines.append(f"  {k:6s} n {v['points']:6d}  to A p50/p95/max {v['to_A_mm']}  to symmetric her {v['to_symmetric_her_mm']}")
    lines.append(f"  TIGHT to A {out['tight']['to_A_mm']}  to symmetric her {out['tight']['to_symmetric_her_mm']}  her own asymmetry {out['tight']['her_asymmetry_mm (A to mirrored A, all her points)']}")
    for sd in "lr":
        v = out["arm"][sd]
        lines.append(f"  arm {sd} girth err % {v['err_pct']}  segments B {v['segments_B_m']} A {v['segments_A_m']}")
    lines.append(f"  height {out['height']}")
    open(os.path.join(a.out, "summary.txt"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
