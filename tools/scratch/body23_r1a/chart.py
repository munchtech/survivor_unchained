"""posed and rest upper-arm / forearm charts: s (mm down the bone line), phi (0 front, 90 out, 180 back, -90 in), r (mm)"""
import numpy as np
import k

FRONT = np.array([0, 0, 1.0])


def skin_rot(fr, bone):
    """the bone's rest->posed rotation (scale removed) at a frame"""
    bs = k.base()
    S = fr.Gs[fr.bnames.index(bone)] @ bs.ibm[bs.names.index(bone)]
    R = S[:3, :3]
    U, _, Vt = np.linalg.svd(R)
    return U @ Vt, S


def rest_frame(sd, seg="U"):
    bs = k.base()
    J = bs.J
    if seg == "U":
        O, E = J["upperarm_" + sd], J["lowerarm_" + sd]
    else:
        O, E = J["lowerarm_" + sd], J["hand_" + sd]
    a = (E - O) / np.linalg.norm(E - O)
    f = FRONT - (FRONT @ a) * a
    f /= np.linalg.norm(f)
    sg = 1.0 if sd == "l" else -1.0
    l = sg * np.cross(f, a)
    return dict(O=O, a=a, f=f, l=l, L=float(np.linalg.norm(E - O)) * 1000)


def posed_frame(fr, sd, seg="U"):
    """the rest frame carried by the bone's posed rotation; origin and axis from the posed joints"""
    rf = rest_frame(sd, seg)
    b0, b1 = ("upperarm_", "lowerarm_") if seg == "U" else ("lowerarm_", "hand_")
    O, E = k.joint(fr, b0 + sd), k.joint(fr, b1 + sd)
    a = (E - O) / np.linalg.norm(E - O)
    R, _ = skin_rot(fr, b0 + sd)
    f = R @ rf["f"]
    f = f - (f @ a) * a
    f /= np.linalg.norm(f)
    sg = 1.0 if sd == "l" else -1.0
    l = sg * np.cross(f, a)
    return dict(O=O, a=a, f=f, l=l, L=float(np.linalg.norm(E - O)) * 1000)


def coords(X, F):
    d = (X - F["O"]) * 1000
    s = d @ F["a"]
    x, y = d @ F["l"], d @ F["f"]
    return s, np.degrees(np.arctan2(x, y)), np.hypot(x, y)


def radial(X, F):
    d = X - F["O"]
    q = d - (d @ F["a"])[:, None] * F["a"]
    return q / np.maximum(np.linalg.norm(q, axis=1, keepdims=True), 1e-12)


def profile_table(s, phi, r, sel, srange=range(-60, 300, 15), phis=(-90, -45, 0, 45, 90, 135, 180)):
    lines = ["  s\\phi " + "".join("%7d" % p for p in phis)]
    for s0 in srange:
        row = "%6d " % s0
        for p in phis:
            dp = (phi - p + 180) % 360 - 180
            m = sel & (np.abs(s - s0) < 7.5) & (np.abs(dp) < 15)
            row += "%7.1f" % r[m].max() if m.sum() > 2 else "%7s" % "."
        lines.append(row)
    return "\n".join(lines)
