"""anim-40: fistfit's table on the conformed viking axe, MODELLED as the game will seat it (before any re-dump):
anchored (its haft's line the piece's +Y), on the Blade1H pocket (BladeAtR / BladeDirR), Spec.Lean 35 (so FistSeat's
turn is none), the scale kept (Spec.Length so k is the old). The arms_local mesh is replaced by the conformed glb's in
hand_r space.
    python tools/scratch/anim40/fist/model_axe.py GLB [--wrap sword|axe] [--fit] [--verify]
"""
import json
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(ROOT / "tools" / "anim"))
from axe_haft import gc, haft_frame  # noqa: E402
import fistfit as F  # noqa: E402
import keyed  # noqa: E402


def mount(lean):
    b = np.array([[0, 0, 1.0], [1.0, 0, 0], [0, 1.0, 0]])      # columns x=(0,1,0), y=(0,0,1), z=(1,0,0)
    a = np.radians(-lean); c, s = np.cos(a), np.sin(a)
    Rx = np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    return Rx @ b


def old_hand(pc):
    T = pc.turn; k = pc.k
    p = k * (pc.P - pc.centre) @ T.T + np.array([0, pc.row["length"] * (0.5 - pc.row["grip"]), 0])
    return np.array([-0.025, 0.075, 0]) + p @ mount(30.0).T


def new_hand(pc, O, d, k):
    Z = pc.turn[2] - d * (pc.turn[2] @ d); Z /= np.linalg.norm(Z); X = np.cross(d, Z)
    Tn = np.array([X, d, Z])
    At, Dir = F._pocket("sword")
    p = k * (pc.P - O) @ Tn.T
    M = mount(35.0)
    assert abs(M @ [0, 1.0, 0] @ (Dir / np.linalg.norm(Dir)) - 1) < 1e-5
    return At + p @ M.T


if __name__ == "__main__":
    glb = sys.argv[1]; wrap = "sword"
    if "--wrap" in sys.argv:
        wrap = sys.argv[sys.argv.index("--wrap") + 1]
    old = gc.load("viking_axe")
    if "--verify" in sys.argv:
        V = np.array(json.load(open(F.DATA / "arms_local.json"))["viking_axe@hand_r"]["v"], float)
        Hd = old_hand(old)
        print("old plain mount vs arms_local: max nn mm", cKDTree(Hd).query(V)[0].max() * 1000)
    pc = gc.load("viking_axe", path=Path(glb))
    O, d, _, _ = haft_frame(old)
    ext = np.ptp(pc.P @ d)
    k = old.k
    print(f"Spec.Length for k unchanged: {k * ext:.4f} m (extent along the haft {ext * old.mm:.1f} mm)")
    Vn = new_hand(pc, O, d, k)
    P = F.PIECES["axe"]
    P.update(at="BladeAtR", dir="BladeDirR"); P.pop("dump", None); P.pop("axis", None)
    F._arms_v = lambda piece, _V=Vn: _V if piece == "axe" else None
    if "--fit" in sys.argv:
        extra = sys.argv[sys.argv.index("--fit") + 1:]
        sys.exit(F.main(["axe", "--fit"] + extra))
    F.table("axe", wrap=keyed.WRAP[wrap])
