# Brute force: can her right fist (fitted staff pocket) hold the staff near-vertical with its foot on the ground?
import numpy as np, math, itertools, sys
S = np.array([-0.21, 1.476, -0.121]); LU, LF = 0.25, 0.266
A = np.array([-0.0326, 0.0841, -0.0104]); D = np.array([-0.2116, 0.4141, 0.8853]); D /= np.linalg.norm(D)
FLEX, EXT, RAD, ULN = [float(x) for x in (sys.argv[2] if len(sys.argv) > 2 else "75,65,22,38").split(",")]
GMAX = float(sys.argv[1]) if len(sys.argv) > 1 else 1.065
def rot_between(a, b):
    v = np.cross(a, b); c = a @ b
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K / (1 + c)
def axrot(ax, a):
    K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    return np.eye(3) + math.sin(a) * K + (1 - math.cos(a)) * K @ K
def sph(az, el):
    a, e = math.radians(az), math.radians(el)
    return np.array([-math.sin(a) * math.cos(e), math.sin(e), math.cos(a) * math.cos(e)])
Rs, info = [], []
for taz, ttl in itertools.product(range(0, 360, 30), (0, 8, 15)):
    u = np.array([-math.sin(math.radians(taz)) * math.sin(math.radians(ttl)), math.cos(math.radians(ttl)), math.cos(math.radians(taz)) * math.sin(math.radians(ttl))])
    for rev in (0, 1):
        R0 = rot_between(-D if rev else D, u)
        for psi in range(0, 360, 10):
            Rs.append(axrot(u, math.radians(psi)) @ R0); info.append((taz, ttl, rev, psi, u[1]))
Rs = np.array(Rs); info = np.array(info, float)
thumb = Rs[:, 1, 2]; RA = Rs @ A; uy = info[:, 4]; rev = info[:, 2]
best = {}
for uaz, uel in itertools.product(range(-30, 91, 15), range(-90, -39, 10)):
    ua = sph(uaz, uel); E = S + LU * ua
    for faz, fel in itertools.product(range(-60, 121, 10), range(-80, 61, 5)):
        f = sph(faz, fel); flexion = math.degrees(math.acos(np.clip(f @ ua, -1, 1)))
        if flexion > 145: continue
        fh = np.einsum("nji,j->ni", Rs, f)
        ok = fh[:, 1] > 0
        phi = np.degrees(np.arctan2(fh[:, 0], fh[:, 1])); dev = np.degrees(np.arctan2(-fh[:, 2], fh[:, 1]))
        e = ((phi / np.where(phi > 0, FLEX, EXT)) ** 4 + (dev / np.where(dev > 0, RAD, ULN)) ** 4) ** 0.25
        ok &= e <= 1
        Gy = (E + LF * f)[1] + RA[:, 1]
        footy = Gy - GMAX * uy
        for r in (0, 1):
            for tn in (0, 1):
                m = ok & (rev == r) & ((thumb > -0.2) == bool(tn))
                if not m.any(): continue
                i = np.where(m)[0][np.argmin(footy[m])]
                k = (r, tn)
                if k not in best or footy[i] < best[k][0]:
                    best[k] = (round(float(footy[i]), 3), dict(ua=(uaz, uel), fa=(faz, fel), elbow=round(flexion), staff=tuple(info[i, :2]), psi=info[i, 3], phi=round(float(phi[i])), dev=round(float(dev[i])), thumb=round(float(thumb[i]), 2), gripy=round(float(Gy[i]), 3)))
for k, v in sorted(best.items()): print("reversed" if k[0] else "normal  ", "thumb-ok  " if k[1] else "thumb-down", v)
