"""piececheck: A's skin-tight pieces (the ink slot: pieces.glb + pieces.json, tools/body/skin_pieces.py, P1Body.Piece) on a
published B, at rest and posed through a baked clip, numbers only (P1 R1 sliders).

    python tools/body/piececheck.py CLIP... [--p1 DIR] [--dump DIR] [--step N] [--out FILE]

Per piece, its vertices' signed offset from the body's skin (along the nearest body vertex's normal, mm; negative =
under the skin), p5/p50/p95/max and the count under, at B's rest and over every Nth frame of each clip (B posed as
clipcheck poses it: the dump's globals, helpers at rest local, rig_drive's laws; the piece skinned by its own glb's
skin on the same bone worlds, its corrective shapes at the body's weights, as P1Laws sets them).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import clipcheck as cc  # noqa: E402
from posers import LbsPoser  # noqa: E402

REPO = HERE.parent.parent


def offsets(Vb, Nb, tree, Vp):
    d, i = tree.query(Vp)
    sd = np.einsum("ij,ij->i", Vp - Vb[i], Nb[i]) * 1000
    return sd


def summary(sd):
    p = np.percentile(sd, [5, 50, 95])
    return {"p5_50_95_max_mm": [round(float(x), 2) for x in p] + [round(float(sd.max()), 2)],
            "min_mm": round(float(sd.min()), 2), "under": int((sd < 0).sum())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clips", nargs="*")
    ap.add_argument("--p1", default=str(REPO / "godot/art/people/body_p1"))
    ap.add_argument("--dump", default=str(HERE / "out/clips"))
    ap.add_argument("--step", type=int, default=0)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    P1 = Path(a.p1)
    rig = json.loads((P1 / "rig.json").read_text())
    pj = json.loads((P1 / "pieces.json").read_text())["pieces"]
    pieces = {k: LbsPoser(str(P1 / "pieces.glb"), {"body_mesh": k, "close_meshes": []}) for k, v in pj.items()
              if "missing" not in v and v.get("tier") == "close"}
    report = {}
    B = None
    for clip in ["rest"] + a.clips:
        if clip == "rest":
            d = json.loads((Path(a.dump) / f"{a.clips[0]}.json").read_text()) if a.clips else None
        else:
            d = json.loads((Path(a.dump) / f"{clip}.json").read_text())
        if B is None:
            if d is None:
                raise SystemExit("piececheck: give a clip (its dump lays the skeleton)")
            B = cc.Body(str(P1 / "body.glb"), rig, d["b_names"], cc.mats(d["b_rest"]), True)
        p = B.p
        body = p.piece == "body"
        r = {}
        if clip == "rest":
            frames = [None]
        else:
            Gd = np.stack([cc.mats(f) for f in d["B"]])
            step = a.step or max(1, len(Gd) // 30)
            frames = list(range(0, len(Gd), step))
            B.cache.clear()
        acc = {k: [] for k in pieces}
        for f in frames:
            if f is None:
                G, w = p.rest.copy(), {}
                V = p._skin(G, w)
            else:
                V, G, _, _ = B.pose(Gd[f], set(d["keyed"]), f)
                w = p.driver.corrective_weights(p, G, rig)
            Vb = V[body]
            Nb = cc.vnormals(V, p.T)[body]
            tree = cKDTree(Vb)
            for k, pp in pieces.items():
                Gp = np.stack([G[p.index[n]] if n in p.index else pp.rest[j] for j, n in enumerate(pp.names)])
                acc[k].append(offsets(Vb, Nb, tree, pp._skin(Gp, w)))
        for k in pieces:
            r[k] = summary(np.concatenate(acc[k]))
            r[k]["frames"] = len(frames)
            print(f"{clip}: {k}: offset mm p5/50/95/max {r[k]['p5_50_95_max_mm']}, min {r[k]['min_mm']}, under {r[k]['under']}")
        report[clip] = r
    if a.out:
        Path(a.out).write_text(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
