# Reversed walking grip: relaxed configurations with the foot on the ground (g in [0.79, 1.065]), staff tilted outward.
import numpy as np, math, itertools
S = np.array([-0.193, 1.506, -0.011]); LU, LF = 0.25, 0.266
A = np.array([-0.0326, 0.0841, -0.0104]); D = np.array([-0.2116, 0.4141, 0.8853]); D /= np.linalg.norm(D)
FLEX, EXT, RAD, ULN = 75., 65., 22., 38.
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
for taz, ttl in itertools.product(range(45, 136, 15), (4, 8, 12)):
    u = np.array([-math.sin(math.radians(taz)) * math.sin(math.radians(ttl)), math.cos(math.radians(ttl)), math.cos(math.radians(taz)) * math.sin(math.radians(ttl))])
    R0 = rot_between(-D, u)
    for psi in range(0, 360, 5):
        Rs.append(axrot(u, math.radians(psi)) @ R0); info.append((taz, ttl, psi, *u))
Rs = np.array(Rs); info = np.array(info, float); U = info[:, 3:]
RA = Rs @ A
out = []
for uaz, uel in itertools.product(range(-20, 61, 10), range(-90, -59, 5)):
    ua = sph(uaz, uel); E = S + LU * ua
    for faz, fel in itertools.product(range(-60, 61, 10), range(-80, -9, 5)):
        f = sph(faz, fel); flexion = math.degrees(math.acos(np.clip(f @ ua, -1, 1)))
        if not 15 <= flexion <= 75: continue
        Wr = E + LF * f
        fh = np.einsum("nji,j->ni", Rs, f)
        phi = np.degrees(np.arctan2(fh[:, 0], fh[:, 1])); dev = np.degrees(np.arctan2(-fh[:, 2], fh[:, 1]))
        e = ((phi / np.where(phi > 0, FLEX, EXT)) ** 4 + (dev / np.where(dev > 0, RAD, ULN)) ** 4) ** 0.25
        G = Wr + RA
        # foot on the ground along -u from the grip: g = G.y / u.y
        g = G[:, 1] / U[:, 1]
        F = G - g[:, None] * U
        ok = (fh[:, 1] > 0) & (e <= 0.75) & (g >= 0.80) & (g <= 1.06) & (G[:, 0] <= -0.27) & (F[:, 0] <= -0.17)
        for i in np.where(ok)[0]:
            out.append((round(float(e[i]), 2), dict(ua=(uaz, uel), fa=(faz, fel), elbow=round(flexion), staff=tuple(info[i, :3]), phi=round(float(phi[i])), dev=round(float(dev[i])), g=round(float(g[i]), 3), G=np.round(G[i], 2), F=np.round(F[i], 2), thumb=np.round(Rs[i][:, 2], 2), fingers=np.round(Rs[i][:, 1], 2))))
out.sort(key=lambda r: r[0])
print(len(out))
for r in out[:12]: print(r)
