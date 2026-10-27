"""Made.Frog's twin (Body 17, strap on the outer face): surface points in the frog's space (origin at the haft's axis at
the head's foot), for row2.py --frog. haftpc: Arms.HaftOf's poll and cheek."""
import numpy as np
T, LO, HI, HALF, THICK, EDGE, RISE = 0.0035, -0.042, -0.001, 0.014, 0.002, 0.0019, 0.045


def haftpc(q, top, inward):
    fx = -1 if inward[0] < 0 else 1; oz = -1 if inward[2] > 0 else 1
    D = np.hypot(q[:, 0] - top[0], q[:, 2] - top[2])
    h = (q[:, 1] >= top[1]) & (q[:, 1] <= top[1] + 0.12) & (D < 0.12)
    return float(((q[h, 0] - top[0]) * fx).max()), float(((q[h, 2] - top[2]) * oz).max())


def axes(inward):
    return np.array([-1. if inward[0] < 0 else 1., 0, 0]), np.array([0, 0, -1. if inward[2] > 0 else 1.])


def path(u, v, inward, poll, cheek, reach):
    f, o = axes(inward); U = np.array([0, 1., 0]); b = v + T
    zc = cheek + THICK + 0.002; far = max(poll + 0.010, reach - 0.002 - THICK)
    P = [o * (b - 0.004) + U * (LO - 0.004), o * (b + THICK) + U * (LO + 0.006), o * (b + THICK) + U * (HI - 0.008)]
    c0, c1, c2 = o * (b + THICK) + U * (HI - 0.002), o * zc + U * (RISE * 0.95), o * zc + f * (poll - 0.008) + U * RISE
    for k in range(1, 9):
        s = k / 8; q = c0 * (1 - s) ** 2 + c1 * 2 * s * (1 - s) + c2 * s * s
        q[2] = ((b + THICK + (zc - b - THICK) * 0.5) if k == 1 else zc) * o[2]
        P.append(q)
    P.append(o * (zc - 0.004) + f * (poll - 0.002) + U * RISE); P.append(o * (zc - 0.008) + f * (poll + THICK) + U * RISE)
    P = np.array(P)
    S = []
    for k in range(len(P)):
        tg = P[min(len(P) - 1, k + 1)] - P[max(0, k - 1)]; tg /= np.linalg.norm(tg)
        s = np.cross(o, tg); S.append(s / np.linalg.norm(s))
    return P, np.array(S), f, o


def strip(P, S, half, thick):
    out = []
    for k in range(len(P) - 1):
        for a in np.linspace(0, 1, 4, endpoint=False):
            p = P[k] * (1 - a) + P[k + 1] * a; s = S[k] * (1 - a) + S[k + 1] * a; s /= np.linalg.norm(s)
            tg = P[k + 1] - P[k]; tg /= np.linalg.norm(tg); fc = np.cross(tg, s); fc /= np.linalg.norm(fc)
            for w in np.linspace(-half, half, 7):
                for t in (-thick, thick): out.append(p + s * w + fc * t)
    return out


def frog(u, v, inward, poll, cheek, reach):
    pts = []
    a, b = u + T, v + T
    for y in np.linspace(LO, HI, 10):
        for th in np.linspace(0, 2 * np.pi, 48, endpoint=False): pts.append([a * np.cos(th), y, b * np.sin(th)])
    P, S, f, o = path(u, v, inward, poll, cheek, reach)
    pts += strip(P, S, HALF, THICK)
    for e in (-1, 1): pts += strip(P + S * e * (HALF - EDGE + 0.0004), S, EDGE, THICK + 0.0004)
    return np.array(pts)


def ray_start(inward, poll, cheek):
    f, o = axes(inward)
    return o * (cheek + THICK + 0.002) + np.array([0, RISE, 0]), f
