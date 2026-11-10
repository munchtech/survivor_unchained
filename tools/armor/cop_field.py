"""The CLEARANCE FIELD under a rigid plate on a bone ride: a REPORT (it never changes a recipe).

    python tools/armor/cop_field.py --bones upperarm --out <dir>     -> field.json, field.md

For every skin vertex of her shoulder patch (in the spaulder's arm frame: s along the upper arm from its joint, theta
0 front / 90 outer / 180 back) and a candidate rigid ride (one bone, or a few: "upperarm,upperarm_twist_01"), the
STANDOFF a plate point riding that bone needs over that vertex at rest so that on every frame of every clip it stays
`--clear` (5 mm) over her skin: the game skin (linear blend of her rest plus her corrective shapes at each frame's
weights, reach_table's reading, nearest vertex along its normal; no tuck, no worn top). A plate whose inner face stands
at least the field's value over each vertex it covers passes reach_table's height >= clear (to the field's ~1 mm
reading error: the nearest-vertex height is not linear in the standoff where her skin curves). The probe point is the
vertex lifted `--probe` (20 mm) along its rest normal; need = probe - least height + clear.
"""
import argparse
import json
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
MM = 0.001


def height(P, V, N):
    d, j = cKDTree(V).query(P)
    return ((P - V[j]) * N[j]).sum(1)


def field(sc, z, on, frame_of, side, rides, probe=0.02, clear=0.005, box=(-0.12, 0.18, 0.13)):
    """{ride: need [n]} and the patch (vs, s, th) for one side ("l" | "r"); frame_of(side) -> native_build.Frame."""
    fr = frame_of(side)
    P = sc.P0[sc.isk]
    s, th, rho = fr.cyl(P)
    hand = 1 if side == "l" else -1
    ok = (s > box[0]) & (s < box[1]) & (rho < box[2]) & (P[:, 0] * hand > 0.02)
    vs = sc.isk[ok]
    sub, nsub = sc.restrict(vs), sc.restrict(vs, sc.ntargets)
    eye = np.broadcast_to(np.eye(4), (len(sc.poser.names), 4, 4))

    def skin(S, f=None):
        wts = {} if f is None else {k: float(w[f]) for k, w in z["cw"].items()}
        return sc.lbs(S, sc.rest(vs, wts, sub), sc.J[vs], sc.W[vs]), sc.stored_normals(S, wts, vs, nsub)
    V0, N0 = skin(eye)
    Q = np.c_[V0 + probe * N0, np.ones(len(vs))]
    idx = sc.poser.index
    out = {}
    for name, bones in rides.items():
        b = [idx[f"{x}_{side}"] for x in bones]
        w = np.full(len(b), 1.0 / len(b))
        low, at = np.full(len(vs), np.inf), np.full(len(vs), -1)
        for k, f in enumerate(on):
            S = z["S"][f]
            X = np.einsum("b,bij,nj->ni", w, S[b][:, :3, :], Q)
            h = height(X, *skin(S, f))
            m = h < low
            low[m], at[m] = h[m], f
        out[name] = {"need": probe - low + clear, "at": at}
    return vs, s[ok], th[ok], out


def grid(s, th, need, ds=0.01, dth=15.0, s0=-0.10, s1=0.16):
    rows = []
    for a in np.arange(s0, s1, ds):
        row = []
        for t in np.arange(0, 180, dth):
            m = (s >= a) & (s < a + ds) & (th >= t) & (th < t + dth)
            row.append(float(need[m].max() / MM) if m.any() else None)
        rows.append((round(a / MM), row))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--gear", default=os.path.join(os.path.dirname(os.path.dirname(HERE)), "godot", "art", "gear", "out", "body_p1"))
    ap.add_argument("--bones", default="upperarm", help="rides, ';' between rides, ',' between a ride's bones (equal shares)")
    ap.add_argument("--clips", default="all")
    ap.add_argument("--clear", type=float, default=5.0)
    ap.add_argument("--drop0", default="", help="leave out frame 0 of these clips (a READING of what a clip's first frame costs, never a pass)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    import gear_wear as gw
    import native_build as nb
    import native_travel as nt
    ix, _ = gw.load_rows(a.gear)
    sc = gw.build_scene(os.path.join(gw.REPO, "godot", "art", "people", ix["body"]), [])
    ref = nb.Ref.her()
    z = nt.frames()
    keep = nt.clip_frames(a.clips)
    if a.drop0:
        keep &= ~((z["frame"] == 0) & np.isin(z["clip"], a.drop0.split(",")))
    on = np.flatnonzero(keep)
    rides = {r: [x.strip() for x in r.split(",")] for r in a.bones.split(";")}
    frame_of = lambda sd: nb.Frame.bones(ref, f"upperarm_{sd}", f"lowerarm_{sd}", hand=1 if sd == "l" else -1)  # noqa: E731
    os.makedirs(a.out, exist_ok=True)
    js, md = {}, [f"# clearance field ({a.clear:g} mm on every frame, {len(on)} frames, game skin)", ""]
    for sd in ("l", "r"):
        vs, s, th, F = field(sc, z, on, frame_of, sd, rides, clear=a.clear * MM)
        js[sd] = {"vs": vs.tolist(), "s_mm": (s / MM).round(1).tolist(), "theta": th.round(1).tolist(),
                  **{r: {"need_mm": (v["need"] / MM).round(1).tolist(),
                         "at": [f"{z['clip'][f]}@{int(z['frame'][f])}" for f in v["at"]]} for r, v in F.items()}}
        for r, v in F.items():
            md += [f"## {sd} ride {r}: need mm (max per cell), s rows 10 mm, theta cols 0..165 by 15", "",
                   "| s | " + " | ".join(str(t) for t in range(0, 180, 15)) + " |", "|" + "---|" * 13]
            for a0, row in grid(s, th, v["need"]):
                md.append(f"| {a0} | " + " | ".join("" if x is None else f"{x:.0f}" for x in row) + " |")
            md.append("")
    json.dump(js, open(os.path.join(a.out, "field.json"), "w"))
    open(os.path.join(a.out, "field.md"), "w").write("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main()
