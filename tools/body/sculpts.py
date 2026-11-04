"""Our own sculpts of MakeHuman's woman, where it has no target (copied from tools/assets/face_shapes.py, which made
her shipped head): name -> f(points, anatomy) -> moves. MakeHuman's world: z up, her front toward -y."""
import numpy as np


def _smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def anatomy(P):
    """The tip of her nose, the point of her chin (where her profile steps back under it) and her mouth's height."""
    top = P[:, 2].max()
    face = P[(P[:, 2] > top - 0.30) & (P[:, 1] < 0.02)]
    mid = face[np.abs(face[:, 0]) < 0.006]
    nose = mid[np.argmin(mid[:, 1])]
    prof = []
    for z in np.arange(nose[2] - 0.03, nose[2] - 0.15, -0.003):
        m = np.abs(mid[:, 2] - z) < 0.003
        if m.any():
            prof.append((z, mid[m, 1].min()))
    chin = None
    for (z0, y0), (z1, y1) in zip(prof, prof[1:]):
        if y1 - y0 > 0.015:
            chin = np.array([0.0, y0, z0])
            break
    return {"nose": nose, "chin": chin, "mouth_z": nose[2] - 0.35 * (nose[2] - chin[2])}


def _chin_narrow(P, a):
    """Her chin and the front of her jaw drawn in toward her middle (a smooth field, a soft V)."""
    c = a["chin"]
    up = (P[:, 2] - c[2]) / (a["mouth_z"] - c[2])
    back = (P[:, 1] - c[1]) / 0.075
    below = (c[2] - P[:, 2]) / 0.03
    w = (1 - _smooth(up)) * (1 - _smooth(back)) * (1 - _smooth(below)) * (np.abs(P[:, 0]) < 0.09)
    d = np.zeros_like(P)
    d[:, 0] = -P[:, 0] * 0.22 * w
    return d


SCULPTS = {"sculpt-chin-narrow": _chin_narrow}
