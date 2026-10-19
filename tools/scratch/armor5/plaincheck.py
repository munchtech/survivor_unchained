"""armor 5b: her fist on a PLAIN-MOUNT kind, measured as the game holds it (no pocket, no Arms.Seat): fistfit's table on
the piece where the plain mount puts it (origin (-25, 75, 0) mm in hand_r, shaft turned Spec.Lean toward the fingers).
    python tools/scratch/armor5/plaincheck.py wand|axe_plain [fistfit args]
The seat is the mount's own line (fistfit's _pocket patched to return it), so R is the identity and nothing moves."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools" / "anim"))
import fistfit as F

MOUNT = (-25.0, 75.0, 0.0)
ROWS = {
    # The wand (Made.Wand, Lean 30): cast_flick is the clip that names it.
    "wand": dict(arms="wand@hand_r", outfit="arcanist", rest=("cast_flick", 0), weapon=("wand",), dump=(MOUNT, 30.0), seed="sword"),
    # The axe on the plain mount as shipped (its pocket AxeAtR is not live), its haft's own line fitted ("axis").
    "axe_plain": dict(arms="viking_axe@hand_r", outfit="reaver", rest=("idle_reaver", 0), weapon=("axe", "axes"), wrap="axe",
                      section=True, dump=(MOUNT, 30.0), axis=(-80.0, 150.0), thumb_end=(55.0, 70.0)),
}
F.PIECES.update(ROWS)
_orig = F._pocket


def _plain(piece):
    if piece in ROWS:
        P = ROWS[piece]; lean = np.radians(P["dump"][1])
        return np.array(P["dump"][0]) / 1000, np.array([0.0, np.sin(lean), np.cos(lean)])
    return _orig(piece)


F._pocket = _plain
if __name__ == "__main__":
    sys.exit(F.main(sys.argv[1:]))
