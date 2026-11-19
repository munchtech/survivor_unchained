"""wearcheck openings (Caps / cap_fix): a ray leaving a piece through an open rim counts as crossing it."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wearcheck as wc  # noqa: E402


def _cup(r, h, floor, inward, n=24):
    """An open cup around z: wall r, rim at h, floor disc at `floor`; normals inward (the inner wall) or outward."""
    P = [[0, 0, floor]]
    for z in (floor, h):
        for k in range(n):
            a = 2 * np.pi * k / n
            P.append([r * np.cos(a), r * np.sin(a), z])
    P = np.array(P, float)
    T = []
    for k in range(n):
        k2 = (k + 1) % n
        T.append([0, 1 + k2, 1 + k])                      # floor, normal +z
        a, b, c, d = 1 + k, 1 + k2, 1 + n + k2, 1 + n + k
        T += [[a, b, c], [a, c, d]]                        # wall, normal outward
    T = np.array(T)
    if inward:
        T = T[:, ::-1]
    return P, T


def _piece():
    Po, To = _cup(0.010, 0.020, 0.0, inward=False)
    Pi, Ti = _cup(0.008, 0.020, 0.002, inward=True)
    return np.vstack([Po, Pi]), np.vstack([To, Ti + len(Po)])


def _read(cap):
    P, T = _piece()
    O = np.array([[0.005, 0, 0.018]])
    D = np.array([[0.6, 0, 0.8]])
    t, fa, _, _ = wc.cast(O, D, P[T][None].repeat(1, 0))
    g, _, go = wc.signed_gap(t, fa, 0.05)
    if cap:
        g, go = wc.cap_fix(O, D, g, go, t, wc.Caps(P, T).tris(lambda i: P[i]))
    return g[0]


def test_two_rim_loops_found():
    P, T = _piece()
    assert wc.Caps(P, T).ncomp == 2


def test_point_inside_cup_near_opening_reads_inside_with_caps_past_without():
    assert _read(False) < 0           # the ray leaves through the open rim: reads past the wall
    assert _read(True) > 0            # capped: inside the cup, clearance


def test_point_past_the_wall_still_reads_past():
    P, T = _piece()
    O = np.array([[0.0095, 0, 0.010]])     # in the steel between the walls... outside the inner wall (r 0.008)
    D = np.array([[1.0, 0, 0]])
    t, fa, _, _ = wc.cast(O, D, P[T][None])
    g, _, go = wc.signed_gap(t, fa, 0.05)
    g2, _ = wc.cap_fix(O, D, g, go, t, wc.Caps(P, T).tris(lambda i: P[i]))
    assert g2[0] == g[0]
