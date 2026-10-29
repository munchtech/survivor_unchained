"""armroll: a comfortable arm left alone, a raised fist's kinked wrist brought square with the wrist kept where it
was, only her library passes it.  python tools/anim/test_armroll.py  (or pytest)"""
import inspect
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import armroll as A  # noqa: E402
import build  # noqa: E402
from rig import Skeleton, qaxis, qmul  # noqa: E402

SK = Skeleton.load()
I = SK.index


def _rest(T=16):
    return np.tile(SK.rest_rot, (T, 1, 1)).astype(float), np.tile(SK.rest_pos, (T, 1, 1)).astype(float)


def _raised(dev):
    """Her right arm raised past level (A > 100), its hand bent `dev` deg sideways (about the hand's +X)."""
    rot, pos = _rest()
    u, h = I["upperarm_r"], I["hand_r"]
    for ax in ([0, 0, 1.0], [0, 0, -1.0], [1.0, 0, 0], [-1.0, 0, 0]):
        r = rot.copy()
        r[:, u] = qmul(SK.rest_rot[u], qaxis(ax, 80))
        if A.measure(SK, r, pos)["r"]["A"][0] > 100:
            break
    r[:, h] = qmul(SK.rest_rot[h], qaxis([1.0, 0, 0], dev))
    return r, pos


def test_comfortable_unchanged():
    rot, pos = _rest()
    assert np.allclose(A.solve_rot(SK, rot, pos, 30, False), rot, atol=1e-6)


def test_kinked_wrist_squared_hand_kept():
    rot, pos = _raised(-40.0)
    m0 = A.measure(SK, rot, pos)["r"]
    assert m0["A"][0] > 100 and abs(m0["dev"][0]) > 35
    new = A.solve_rot(SK, rot, pos, 30, False)
    m1 = A.measure(SK, new, pos)["r"]
    assert np.max(np.abs(m1["dev"])) <= A.W_DEV + 1.0
    _, p0 = SK.fk(rot, pos)
    _, p1 = SK.fk(new, pos)
    assert np.max(np.linalg.norm(p1[:, I["hand_r"]] - p0[:, I["hand_r"]], axis=-1)) < 1e-4


def test_her_library_only():
    src = inspect.getsource(build.pack)
    assert 'if stem == "heroine":' in src and src.index("armroll.stage") > src.index('if stem == "heroine":')


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f()
            print("ok", n)
