"""Ground truth for her fist on a held piece, from Godot (godot/tools_scenes/grip_truth.gd's JSON): per frame, each finger
bone's signed gap (mm, negative = inside) to the grip's surface, her skin and her outfit (a glove) apart, and the grip's
line as Godot mounts it against the seat fistfit reads (WeaponSockets.cs).
    python tools/anim/griptruth.py truth.json [piece] [--fistfit]
A left-hand dump (grip_truth.gd's BONE hand_l; piece e.g. dagger_l, fistfit.PIECES) is taken to hand_r's frame through
fistfit.MIRROR, its bones named as the right's, so the seat and the pads read as the right's do.
The grip's line is fitted on the piece's own mesh (the vertices within 25 mm of the seat's line, 90 mm either side of the
seat: its axis by least squares on the ring's centres; only its grip's node, "grip_wrap", when it has one), and its
radius per 2 mm slice is the mesh's outer surface (the slice's max vertex radius, as fistfit's hilt_profile; median beside). --fistfit: fistfit.py's own posed pads at the same frames (out/clips), beside.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
PADS = [f"{f}_0{k}_r" for f in ("index", "middle", "ring", "pinky") for k in (1, 2, 3)] + ["thumb_02_r", "thumb_03_r"]
SPAN, NEAR = 0.09, 0.025


def line_fit(V, A, D, iters=4):
    """The grip's axis from its mesh: points near the seat's line, re-fitted (centroid of each slice's ring, then a line
    through those centres) a few times."""
    for _ in range(iters):
        dd = V - A; t = dd @ D; r = np.linalg.norm(dd - np.outer(t, D), axis=1)
        m = (np.abs(t) < SPAN) & (r < NEAR)
        cs = []
        for a in np.arange(-SPAN, SPAN, 0.004):
            s = m & (t >= a) & (t < a + 0.004)
            if s.sum() >= 12:
                cs.append(V[s].mean(0))
        cs = np.array(cs); c0 = cs.mean(0)
        u, sv, vt = np.linalg.svd(cs - c0); D2 = vt[0] * np.sign(vt[0] @ D)
        A = c0 + D2 * ((A - c0) @ D2); D = D2
    dd = V - A; t = dd @ D; r = np.linalg.norm(dd - np.outer(t, D), axis=1)
    m = (np.abs(t) < SPAN + 0.02) & (r < NEAR)
    prof = []
    for a in np.arange(-SPAN - 0.02, SPAN + 0.02, 0.002):
        s = m & (t >= a) & (t < a + 0.002)
        if s.sum() >= 3:
            prof.append((a + 0.001, float(np.median(r[s])), float(r[s].max())))
    return A, D, np.array(prof)


def gaps(P, A, D, prof):
    dd = P - A; t = dd @ D; r = np.linalg.norm(dd - np.outer(t, D), axis=1)
    R = np.interp(t, prof[:, 0], prof[:, 2], left=np.nan, right=np.nan)     # the slice's outer surface (as fistfit's)
    return (r - R) * 1000


def main(argv):
    path = argv[0]; piece = next((a for a in argv[1:] if not a.startswith("-")), "staff")
    import fistfit as F
    A0, D0 = F.read_seat(piece); D0 = D0 / np.linalg.norm(D0)
    d = json.load(open(path))
    left = d.get("bone", "hand_r") == "hand_l"
    assert left == (F.side_of(piece) == "l"), f"{piece} is held in the other hand from the dump's {d.get('bone', 'hand_r')}"
    mir = F.MIRROR if left else np.eye(3)
    swap = {"_l": "_r", "_r": "_l"}
    for fr in d["frames"]:
        pv = np.array(fr["piece"]["v"]) @ mir; nd = np.array(fr["piece"]["node"])
        grip = [i for i, n in enumerate(fr["piece"]["nodes"]) if "grip" in n.lower()]     # its leather, if it has a node
        A, D, prof = line_fit(pv[np.isin(nd, grip)] if grip else pv, A0, D0)
        print(f"{fr['clip']} f{fr['frame']}: grip line as mounted vs the seat read: {np.linalg.norm(A - A0 - ((A - A0) @ D) * D) * 1000:.2f} mm off, "
              f"{np.degrees(np.arccos(min(1, abs(D @ D0)))):.2f} deg; outer radius {prof[:, 2].min() * 1000:.2f}-{prof[:, 2].max() * 1000:.2f} mm "
              f"(median {prof[:, 1].min() * 1000:.2f}-{prof[:, 1].max() * 1000:.2f})")
        h = fr["her"]; V = np.array(h["v"]) @ mir; W = np.array(h["w"]); M = np.array(h["mesh"])
        B = np.array([b[:-2] + swap[b[-2:]] if left and b[-2:] in swap else b for b in h["bone"]])
        names = h["meshes"]; skin = np.isin(M, [i for i, n in enumerate(names) if n == "Heroine"])
        g = gaps(V, A, D, prof)
        row = {}
        for b in PADS:
            for kind, sel in (("skin", skin), ("outfit", ~skin)):
                s = sel & (B == b) & (W > 0.5) & ~np.isnan(g)
                row.setdefault(b, {})[kind] = round(float(g[s].min()), 1) if s.any() else None
        print("  " + "  ".join(f"{b[:-2]}: {row[b]['skin']}/{row[b]['outfit']}" for b in PADS))
        ok = ~np.isnan(g)
        print(f"  deepest: skin {np.nanmin(np.where(skin, g, np.nan)):.1f}, outfit {np.nanmin(np.where(~skin, g, np.nan)):.1f} mm")
        fr["_row"] = row
    if "--fistfit" in argv:
        import audit
        P = F.PIECES[piece]; gr = F.Grip(A0, D0, F.hilt_profile(piece, A0, D0))
        for fr in d["frames"]:
            name = fr["clip"].split("/")[-1]; _, rot, pos = F.load(F.CLIPS / f"{name}.json")
            hnd = F.Hand(rot[fr["frame"]], pos[fr["frame"]], P["outfit"], F.side_of(piece)); m = F.measure(hnd, rot[fr["frame"]], gr)
            print(f"fistfit {name} f{fr['frame']}: " + "  ".join(f"{fn}: {m[fn]['pads']}" for fn in F.ALLF))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
