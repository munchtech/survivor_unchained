"""The hip fold's numbers at a flexed pose (P1 R5): what a judge called "a hard, dark, straight line ... nowhere does the
belly roll over the thigh", as numbers.

  inside       the check's own parity count and TRUE depth (bends.penetration: count, true_max_mm, true_over_2mm)
  touch        her thigh's front skin (rest: her side's thigh by seg_g, in front of the hip joint) lying ON the belly
               (outside it by parity, within `touch_mm` of the belly's posed surface): the contact patch, cm^2
  overhang     how far the belly lies over the thigh: in 2 cm lateral bands across the thigh's front, the touching
               patch's extent along the posed thigh axis from its root (the fold's floor) out toward the knee, mm;
               the median band (a cut line is 0: the skins cross, they never lie on each other)
  bulge        the belly's roll: the trunk's front skin within 10 cm above the fold, moved out along its own posed
               normal against the plain skinning (LBS), p95 mm (the tissue the thigh displaced, rolled up)

    python tools/body/hip_measure.py <build out dir> [--tier close|play] [--degs 112,135] [--shapes|--lbs]
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
for p_ in (HERE, os.path.dirname(os.path.dirname(HERE))):
    if p_ not in sys.path:
        sys.path.insert(0, p_)

import bends  # noqa: E402
import ray  # noqa: E402


def measure(st, V, G, T_all, V_lbs=None, touch_mm=3.0):
    p = st.poser
    P0 = p.P0
    fr = st.fr
    pen = bends.penetration(st, V, T_all)
    out = {"inside": pen["count"], "true_max_mm": pen.get("true_max_mm", 0.0),
           "true_over_2mm": pen.get("true_over_2mm", 0), "depth_max_mm": pen["depth_max_mm"]}
    O = st.O
    front0 = (P0 - O) @ fr.front
    up0 = (P0 - O) @ fr.up
    thigh = st.seg_g & (front0 > 0)
    belly = st.rend & ~st.seg_g & (front0 > 0) & (up0 > -0.03) & (up0 < 0.16) & \
        (np.abs((P0 - O) @ fr.lat) < 0.12)
    Tb = T_all[belly[T_all].all(1)]
    sc = ray.scene(V, T_all)
    N = bends.normals(V, T_all)
    ti = np.nonzero(thigh & (np.linalg.norm(P0 - O, axis=1) < 0.30))[0]
    ins = ray.inside(sc, V[ti] + 3e-4 * N[ti])
    d = bends.surface_depth(V, Tb, V[ti]) * 1000 if len(Tb) else np.full(len(ti), np.inf)
    tch = ti[(~ins) & (d < touch_mm)]
    # node areas (a third of each adjacent triangle)
    A = np.linalg.norm(np.cross(V[T_all[:, 1]] - V[T_all[:, 0]], V[T_all[:, 2]] - V[T_all[:, 0]]), axis=1) / 6
    na = np.zeros(len(V))
    for k in range(3):
        np.add.at(na, T_all[:, k], A)
    out["touch_cm2"] = round(float(na[tch].sum() * 1e4), 1)
    u = bends.unit(G[st.je][:3, 3] - G[st.j][:3, 3])           # the posed thigh axis
    lat0 = (P0 - O) @ fr.lat * (1 if st.s == "l" else -1)
    ax = (V - O) @ u
    bands = []
    for lo in np.arange(-0.06, 0.06, 0.02):
        m = tch[(lat0[tch] >= lo) & (lat0[tch] < lo + 0.02)]
        allb = ti[(lat0[ti] >= lo) & (lat0[ti] < lo + 0.02)]
        if len(m) < 3 or not len(allb):
            bands.append(0.0)
            continue
        bands.append(float(np.percentile(ax[m], 95) - np.percentile(ax[m], 5)) * 1000)
    out["overhang_mm"] = round(float(np.median(bands)), 1)
    out["overhang_bands_mm"] = [round(b, 1) for b in bands]
    if V_lbs is not None:
        bn = np.nonzero(belly & (up0 > 0.0))[0]
        Nl = bends.normals(V_lbs, T_all)
        mv = np.einsum("ij,ij->i", V[bn] - V_lbs[bn], Nl[bn]) * 1000
        out["bulge_p95_mm"] = round(float(np.percentile(mv, 95)), 1)
        out["sink_p5_mm"] = round(float(np.percentile(mv, 5)), 1)
    return out


def main(argv):
    import correctives as C
    a = [x for x in argv if not x.startswith("--")]
    out_dir = os.path.abspath(a[0])
    tier = argv[argv.index("--tier") + 1] if "--tier" in argv else "close"
    degs = [float(x) for x in (argv[argv.index("--degs") + 1] if "--degs" in argv else "90,112,135").split(",")]
    f_glb, f_rig, f_base, _, _ = C.TIERS[tier]
    rig = json.load(open(os.path.join(out_dir, f_rig)))
    from posers import LbsPoser
    poser = LbsPoser(os.path.join(out_dir, f_glb), rig)            # the shipped shapes driven by their laws
    base = LbsPoser(os.path.join(out_dir, "stage", f_base), dict(rig, correctives=[]))
    frame = bends.Frame(poser, rig)
    st = C.key_strip(poser, rig, frame, "hip_flex", "l")
    stb = C.key_strip(base, rig, bends.Frame(base, rig), "hip_flex", "l")
    res = {}
    for dg in degs:
        V, G = C.key_pose(st, dg)
        Vl, Gl = C.key_pose(stb, dg)
        res[str(dg)] = {"shapes": measure(st, V, G, poser.T, Vl), "lbs": measure(stb, Vl, Gl, base.T, Vl)}
        print(dg, json.dumps(res[str(dg)]), flush=True)
    return res


if __name__ == "__main__":
    main(sys.argv[1:])
