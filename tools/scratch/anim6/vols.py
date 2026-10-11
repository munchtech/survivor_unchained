"""Her joints' volume kept (% of rest, the left side, as sweep2.py measures
it) for tick.py's variants.

    python -u vols.py <variant> ...
"""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tick  # noqa: E402
import helpers as hp  # noqa: E402
from sweep import pose, Regions, elbow, knee  # noqa: E402
from rigtest import thigh_forward  # noqa: E402


def both(fn, *a):
    return [fn("l", *a), fn("r", *a)]


POSES = [("e90", both(elbow, 90), "elbow"), ("e120", both(elbow, 120), "elbow"), ("e145", both(elbow, 145), "elbow"),
         ("k90", both(knee, 90), "knee"), ("k120", both(knee, 120), "knee"), ("k145", both(knee, 145), "knee"),
         ("h110k135", both(thigh_forward, 110) + both(knee, 135), "knee")]

spec0 = copy.deepcopy(hp.SPEC)
for v in sys.argv[1:]:
    hp.SPEC.clear()
    hp.SPEC.update(copy.deepcopy(spec0))
    b = tick.variant_body(v)
    R = Regions(b)
    rest = R.volumes(b.P, b.rest)
    cells = []
    for name, edits, joint in POSES:
        G = pose(b, edits)
        vol = R.volumes(b.pose(G), G)
        cells.append(f"{name} {100 * vol[(joint, 'l')] / rest[(joint, 'l')]:5.1f}")
    print(f"{v:44s} " + "  ".join(cells), flush=True)
