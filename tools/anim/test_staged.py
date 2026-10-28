"""staged: the checks' clips are the packed ones.  python tools/anim/test_staged.py  (or pytest)
Godot pose truth (carry3 pt0.txt, 28 Oct): run_reaver f0 hand_r as the game poses it (pt0.txt BASIS). Godot's axes differ from this rig's, so the test pins staging to what build.pack wrote."""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import staged  # noqa: E402
from rig import DATA, Skeleton  # noqa: E402

HERE = Path(__file__).resolve().parent
SK = Skeleton.load(DATA / "heroine_skeleton.json")


def _hand_basis(d, f=0):
    n = len(d["tracks"][0]["keys"])
    rot = np.tile(SK.rest_rot, (n, 1, 1)).astype(float)
    pos = np.tile(SK.rest_pos, (n, 1, 1)).astype(float)
    for t in d["tracks"]:
        j = SK.index.get(t["bone"])
        if j is not None:
            (rot if t["type"] == "rot" else pos)[:, j] = np.array(t["keys"], float)
    g, _ = SK.fk(rot, pos)
    return np.asarray(g[f, SK.index["hand_r"]], float)   # global quaternion


def test_staged_differs_and_matches_pack():
    raw = json.loads((HERE / "out" / "clips" / "run_reaver.json").read_text())
    st = staged.staged_json(json.loads(json.dumps(raw)))
    ang = np.degrees(2 * np.arccos(min(1.0, abs(float(np.dot(_hand_basis(raw), _hand_basis(st)))))))
    assert ang > 5, f"staging should turn the wrist (got {ang:.1f} deg)"
    pk = HERE / "out" / "packed_heroine" / "run_reaver.json"
    if pk.exists():
        packed = json.loads(pk.read_text())
        by = {(t["bone"], t["type"]): np.array(t["keys"], float) for t in packed["tracks"]}
        for t in st["tracks"]:
            assert np.abs(np.array(t["keys"], float) - by[(t["bone"], t["type"])]).max() < 1e-3, t["bone"]


if __name__ == "__main__":
    test_staged_differs_and_matches_pack()
    print("ok")
