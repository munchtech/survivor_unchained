"""anim-40: fistfit's table on the wand, MODELLED as the game will seat it (before any re-dump): Made.Wand's lathe (the
profile below, 16 sides, as Shapes.Lathe turns it), scaled as Arms.Make does (0.38 m over its extent), its grip point
Spec.Grip along it, seated (Spec Seated) on the Blade1H pocket (BladeAtR / BladeDirR).
    python tools/scratch/anim40/fist/model_wand.py [--wrap sword] [--fit ...]
"""
import sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / "tools" / "anim"))
import fistfit as F  # noqa: E402
import keyed  # noqa: E402

RG = 0.0470          # the grip's radius (lathe units: x 294.6 mm = 13.85 mm at the 16-gon's corners)
WOOD = [(0, -0.6), (0.047, -0.6), (0.054, -0.59), (0.054, -0.578), (RG, -0.566), (RG, -0.21), (0.040, -0.19),
        (0.033, 0.1), (0.025, 0.4), (0.021, 0.48), (0, 0.5)]
BRASS = [(RG, -0.215), (0.053, -0.200), (0.053, -0.172), (0.040, -0.155)]
TOP = 0.69           # the crystal's tip (lathe y): the extent's top
LENGTH, GRIP = 0.38, 0.12


def lathe(prof, seg=16):
    out = []
    for i in range(seg):
        a = 2 * np.pi * i / seg
        for r, y in prof:
            out.append((r * np.cos(a), y, r * np.sin(a)))
    return np.array(out)


def model():
    P = np.concatenate([lathe(WOOD), lathe(BRASS)])
    lo, hi = -0.6, TOP; k = LENGTH / (hi - lo)
    yG = (lo + hi) / 2 - LENGTH * (0.5 - GRIP) / k
    At, Dir = F._pocket("sword"); D = Dir / np.linalg.norm(Dir)
    e1 = np.array([1.0, 0, 0]); e2 = np.cross(D, e1)
    p = (P - [0, yG, 0]) * k
    return At + np.outer(p[:, 1], D) + np.outer(p[:, 0], e1) + np.outer(p[:, 2], e2), k, yG


if __name__ == "__main__":
    wrap = sys.argv[sys.argv.index("--wrap") + 1] if "--wrap" in sys.argv else "sword"
    V, k, yG = model()
    print(f"k {k * 1000:.1f} mm/unit, grip point {(yG + 0.6) * k * 1000:.1f} mm from the butt, grip r {RG * k * 1000:.2f} mm")
    F.PIECES["wand"] = dict(arms="wand@hand_r", at="BladeAtR", dir="BladeDirR", outfit="arcanist", rest=("cast_flick", 0),
                            weapon=("wand",), wrap=wrap, seed="sword")
    F._arms_v = lambda piece, _V=V: _V
    if "--fit" in sys.argv:
        sys.exit(F.main(["wand", "--fit"] + sys.argv[sys.argv.index("--fit") + 1:]))
    F.table("wand", wrap=keyed.WRAP[wrap])
