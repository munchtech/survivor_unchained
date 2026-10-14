"""turn.py: HairSway.Turn() offline (world space; angles are the same in the mesh's space): per point quaternions (w, xyz)."""
import numpy as np, math
def qmul(a, b):
    w1, x1, y1, z1 = a; w2, x2, y2, z2 = b
    return np.array([w1*w2 - x1*x2 - y1*y2 - z1*z2, w1*x2 + x1*w2 + y1*z2 - z1*y2, w1*y2 - x1*z2 + y1*w2 + z1*x2, w1*z2 + x1*y2 - y1*x2 + z1*w2])
def qinv(a): return np.array([a[0], -a[1], -a[2], -a[3]])
def qnorm(a): return a / np.linalg.norm(a)
def arc(a, b):
    c = float(a @ b)
    if c > 0.999999: return np.array([1., 0, 0, 0])
    if c < -0.999999:
        ax = np.cross(a, [1, 0, 0] if abs(a[0]) < 0.9 else [0, 1, 0]); ax /= np.linalg.norm(ax); return np.array([0., *ax])
    # Godot Quaternion(arc_from, arc_to)
    ax = np.cross(a, b); d = math.sqrt((1 + c) * 2)
    return np.array([d * 0.5, ax[0] / d, ax[1] / d, ax[2] / d])
def slerp(a, b, t):
    c = float(a @ b)
    if c < 0: b = -b; c = -c
    if c > 0.9995: return qnorm(a + (b - a) * t)
    th = math.acos(c); return (math.sin((1 - t) * th) * a + math.sin(t * th) * b) / math.sin(th)
def rot(q, v):
    w, u = q[0], q[1:]
    return v + 2 * np.cross(u, np.cross(u, v) + w * v)
def turns(target, x):
    """per point (8) quaternions [w,x,y,z], as HairSway.Turn (seg j: link j->j+1)."""
    seg = []; d0 = e0 = None
    for j in range(7):
        d = target[j + 1] - target[j]; e = x[j + 1] - x[j]
        if d @ d < 1e-12 or e @ e < 1e-12: seg.append(seg[-1] if j else np.array([1., 0, 0, 0])); continue
        d = d / np.linalg.norm(d); e = e / np.linalg.norm(e)
        seg.append(arc(d, e) if j == 0 else qnorm(qmul(qmul(arc(e0, e), seg[j - 1]), qinv(arc(d0, d)))))
        d0, e0 = d, e
    out = [np.array([1., 0, 0, 0])]
    for i in range(1, 8): out.append(seg[6] if i == 7 else slerp(seg[i - 1], seg[i], 0.5))
    return np.array(out), np.array(seg)
def angle(q): return math.degrees(2 * math.acos(min(1, abs(q[0]))))
