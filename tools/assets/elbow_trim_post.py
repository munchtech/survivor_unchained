"""Her elbow's weights kept off the humerus (Body 14, 26 Oct 2026): helpers.elbow_trim (SPEC "elbow_trim") on a built
body, weights only.

    python tools/assets/elbow_trim_post.py <in heroine.glb> <out heroine.glb>

The bones that follow the elbow's bend (the forearm, its twists, the hand and fingers, the elbow's share and point)
reached up her humerus (body B, back side: 5.5% of the bend at t .75, 16% at .85), so any bend swung the triceps out
and the biceps in there (B at 90 deg: back +3.9 mm, front -3.1 at t .75) and caved the outer side. Their weight is
eased out above the joint by sector (back/front tighter than the sides) and handed to the upper arm's twist chain by t.
Only the Heroine mesh's vertices whose weights change are rewritten (the rest of the file byte for byte, positions,
normals, shapes and the bind pose untouched). Runs on any body with the helpers; idempotent by its asset mark
`elbow_trim` (a marked body is copied unchanged). The outfits and armor take the change in the G3 chain's follow
(body_follow_post.py: BODY's weights minus BASE's, by bone name, at each piece point's skin place).
"""
import os
import shutil
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "anim"))
sys.path.insert(0, HERE)
from scap_rig_post import Glb  # noqa: E402
from shoulder_rig_post import rest_globals  # noqa: E402
import helpers as hp  # noqa: E402

MARK = "elbow_trim"


def run(src, dst):
    G = Glb(src)
    g = G.g
    ex = g["asset"].setdefault("extras", {})
    if MARK in ex:
        shutil.copyfile(src, dst)
        print("ELBOW_TRIM already marked: copied")
        return
    names, _, Grest = rest_globals(G)
    heads = {n: M[:3, 3] for n, M in Grest.items()}
    hn = [n for n in g["nodes"] if n.get("name") == "Heroine"][0]
    total = 0
    for p in g["meshes"][hn["mesh"]]["primitives"]:
        at = p["attributes"]
        sets = [k for k in ("0", "1") if "JOINTS_" + k in at]
        P = G.get(at["POSITION"]).astype(float)
        J = np.hstack([G.get(at["JOINTS_" + k]).astype(int) for k in sets])
        W = np.hstack([G.get(at["WEIGHTS_" + k]).astype(float) for k in sets])
        D = np.zeros((len(P), len(names)))
        np.add.at(D, (np.repeat(np.arange(len(P)), J.shape[1]), J.ravel()), W.ravel())
        D2 = D
        for s in "lr":
            if f"lowerarm_share_{s}" in names:
                D2 = hp.elbow_trim(D2, P, names, heads, s)
        rows = np.nonzero(np.abs(D2 - D).max(1) > 1e-7)[0]
        if not len(rows):
            continue
        n = J.shape[1]
        top = np.argsort(-D2[rows], 1, kind="stable")[:, :n]
        tw = np.take_along_axis(D2[rows], top, 1)
        tw[tw < 1e-5] = 0
        tw /= tw.sum(1, keepdims=True)
        top[tw == 0] = 0
        J[rows], W[rows] = top, tw
        for i, k in enumerate(sets):
            G.put(at["JOINTS_" + k], J[:, 4 * i:4 * i + 4])
            G.put(at["WEIGHTS_" + k], W[:, 4 * i:4 * i + 4].astype(np.float32))
        total += len(rows)
        print(f"ELBOW_TRIM {g['materials'][p['material']].get('name')}: {len(rows)} points, weight moved max "
              f"{float(np.abs(D2 - D).max()):.3f}")
    ex[MARK] = dict(hp.SPEC["elbow_trim"])
    G.save(dst)
    print("ELBOW_TRIM", total, "points ->", dst)


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])
