"""top_bar.py (P2 l16): the gore bar built ON the installed plate_top_plain, staged to tmp (never the shipped files)."""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import adorn  # noqa: E402
import top_bar as tb  # noqa: E402
import worn_rest as wr  # noqa: E402


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    src = tb.stage(str(tmp_path_factory.mktemp("src")))
    once = str(tmp_path_factory.mktemp("once"))
    twice = str(tmp_path_factory.mktemp("twice"))
    g1 = tb.run(src, once)           # (the run asserts the identity gate before it writes)
    g2 = tb.run(once, twice)
    return src, once, twice, g1, g2


def test_gates_hold(built):
    g = built[3]
    assert g["bar_to_cups_min_mm"] >= 4.3 and g["skin_standoff_min_mm"] > 0
    assert g["bar_to_cups_left_mm"] < 10 and g["bar_to_cups_right_mm"] < 10


def test_other_meshes_identical(built):
    src, once = built[0], built[1]
    A, _ = tb.load(src)
    B, _ = tb.load(once)
    for m in A.meshes:
        if m["name"].split(".", 1)[1] not in tb.MESHES:
            assert adorn.soup(m) == adorn.soup(B.get(m["name"])), m["name"]


def test_bar_is_one_linked_bridge(built):
    """The bar is its own weld group (worn_rest.clusters: never welded into a cup's), within link_m of both cups."""
    M, sock = tb.load(built[1])
    m = M.get(f"{tb.PID}.top.steel")
    bar = tb.find_gore(m, tb.gore_row(M, sock), np.asarray(sock["sockets"]["gore"]["point"]))
    X = m["attrs"]["POSITION"][0].astype(np.float64)
    comp = tb.welded_comps(m)
    lead, _ = wr.clusters(X, comp, np.arange(comp.max() + 1))
    groups = lambda s: set(lead[np.unique(comp[s])].tolist())
    gb = groups(bar)
    assert len(gb) == 1                       # (plate, rolled edge and rivets: one group)
    from scipy.spatial import cKDTree
    t = cKDTree(X[bar])
    near = {}
    for side in (-1, 1):
        cup = ~bar & (np.sign(X[:, 0]) == side)
        d = t.query(X[cup])[0]
        near[side] = groups(cup & np.isin(np.arange(len(X)), np.nonzero(cup)[0][d < wr.JOIN["link_m"]]))
        assert d.min() > wr.JOIN["weld_m"] and d.min() < wr.JOIN["link_m"]
        assert not (near[side] & gb)
    assert near[-1] and near[1]


def test_targets_on_bar(built):
    M, sock = tb.load(built[1])
    row, at = tb.gore_row(M, sock), np.asarray(sock["sockets"]["gore"]["point"])
    for name in tb.MESHES:
        m = M.get(f"{tb.PID}.{name}")
        assert len(m["extras"]["targetNames"]) == 18
        tk = adorn.target_keys(m["attrs"])
        assert len({k[2:4] for k in tk}) == 18
        bar = tb.find_gore(m, row, at)
        assert bar.any()
        for k in tk:
            D = m["attrs"][k][0][bar]
            assert np.all(D == D[0])            # (rigid: one delta per target on the whole bar)


def test_rerun_idempotent(built):
    once, twice, g1, g2 = built[1], built[2], built[3], built[4]
    assert g1 == g2
    for ext in (".bin", ".sockets.json"):
        assert open(os.path.join(once, tb.PID + ext), "rb").read() == open(os.path.join(twice, tb.PID + ext), "rb").read()
