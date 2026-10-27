"""Made.Frog's twin (Body 17): the frog's surface as points in the axe's mount space, for row.py --frog.
HaftOf's twin on the dump's surface samples (the grip window at mount y 0: the sheath point, on the haft)."""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "anim"))
import armscheck as ac


def haft(pts, inward):
    q = pts; g = 0.0
    w = q[np.abs(q[:, 1] - g) < 0.04]
    cx, cz = (w[:, 0].min() + w[:, 0].max()) / 2, (w[:, 2].min() + w[:, 2].max()) / 2
    r = max(np.ptp(w[:, 0]), np.ptp(w[:, 2])) / 2; rim = 1.5 * r + 0.005
    D = np.hypot(q[:, 0] - cx, q[:, 2] - cz)
    m = (q[:, 1] > g + 0.10) & (D > rim) & (D < 0.10)
    top = q[m, 1].min() if m.any() else q[:, 1].max() - 0.12
    s = (q[:, 1] >= top - 0.06) & (q[:, 1] <= top - 0.003) & (D <= rim)
    u, v = np.abs(q[s, 0] - cx).max(), np.abs(q[s, 2] - cz).max()
    h = (q[:, 1] >= top) & (q[:, 1] <= top + 0.12) & (D < 0.12)
    back = ((q[h, 0] - cx) * inward[0] + (q[h, 2] - cz) * inward[2]).max()
    return np.array([cx, top, cz]), u, v, back


def frog(u, v, inward, back, reach, n=24):
    t, lo, hi, half, thick = 0.0035, -0.042, -0.001, 0.014, 0.002
    d = np.array([inward[0], 0, inward[2]]); d /= np.linalg.norm(d)
    side = np.cross([0, 1, 0], d); side /= np.linalg.norm(side)
    P = []
    a, b = u + t, v + t
    for y in np.linspace(lo, hi, 10):
        for th in np.linspace(0, 2 * np.pi, 48, endpoint=False):
            P.append([a * np.cos(th), y, b * np.sin(th)])
    rd = a * b / np.sqrt(b * b * d[0] ** 2 + a * a * d[2] ** 2)
    up = max(back + 0.004, reach - 0.002 - thick)
    U = np.array([0, 1, 0])
    path = [d * (rd - 0.004) + U * (lo - 0.004), d * (rd + thick) + U * (lo + 0.006), d * (rd + thick) + U * (hi - 0.006),
            d * up + U * 0.012, d * up + U * 0.050, d * (up - 0.001) + U * 0.062]
    for k in range(len(path) - 1):
        for f in np.linspace(0, 1, 8):
            p = path[k] * (1 - f) + path[k + 1] * f
            tg = path[min(len(path) - 1, k + 1)] - path[max(0, k)]; tg /= np.linalg.norm(tg)
            fc = np.cross(tg, side); fc /= np.linalg.norm(fc)
            for s in np.linspace(-half, half, 6):
                for o in (-thick, thick):
                    P.append(p + side * s + fc * o)
    c = d * (up - 0.0035) + U * 0.060
    for s in np.linspace(-half - 0.001, half + 0.001, 8):
        for th in np.linspace(0, 2 * np.pi, 12, endpoint=False):
            P.append(c + side * s + (d * np.cos(th) + U * np.sin(th)) * 0.0055)
    return np.array(P), up
