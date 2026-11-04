import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import measure as M
import gen as G

R = 44100


def sine(db=-6.0, s=1.0):
    t = np.arange(int(R * s)) / R
    return 10 ** (db / 20) * np.sin(2 * np.pi * 1000 * t)


def test_peak():
    m = M.measure(sine(), R)
    assert abs(m["peak_dbfs"] + 6) < 0.1, m
    assert abs(m["true_peak_dbfs"] + 6) < 0.2, m
    assert not m["lufs_padded"]
    assert 900 < m["centroid_hz"] < 1100, m


def test_short_padded():
    assert M.measure(sine(s=0.2), R)["lufs_padded"]


def test_trim_fade_lengths():
    x = np.concatenate([np.zeros(R // 10), sine(s=0.5), np.zeros(R // 10)])
    a = G.trim_lead(x)
    assert len(a) <= len(x) and len(a) >= len(x) - R // 10
    b = G.trim_tail(a, -55)
    assert len(b) <= len(a)
    assert abs(b[-1]) < 1e-3
    c = G.fade_in(b)
    assert len(c) == len(b) and c[0] == 0


def test_loop_length():
    x = np.random.RandomState(1).randn(R * 5, 2) * 0.1
    assert len(G.make_loop(x)) == len(x) - int(1.5 * R)


if __name__ == "__main__":
    for k, v in list(globals().items()):
        if k.startswith("test_"):
            v()
    print("ok")
