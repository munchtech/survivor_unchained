"""simlog.py: parse a run's views.log into per-frame records for the offline SideCarry sim (camera exact: fixed basis, fov 34)."""
import math
import numpy as np
CX = np.array([1, 0, 0.]); CY = np.array([0, 0.46947163, -0.8829476]); CZ = np.array([0, 0.8829476, 0.46947163])
FPX = 540 / math.tan(math.radians(17))
def proj(p, O):
    q = p - O; zc = -(q @ CZ)
    return np.array([960 + (q @ CX) / zc * FPX, 540 - (q @ CY) / zc * FPX])
def jac(p, O, e=0.05):
    p0 = proj(p, O); d = [(proj(p + v * e, O) - p0) / e for v in (np.array([1., 0, 0]), np.array([0, 1., 0]), np.array([0, 0, 1.]))]
    return np.array([d[0][0], d[1][0], d[2][0]]), np.array([d[0][1], d[1][1], d[2][1]])
def rot(ax, deg, v):
    r = math.radians(deg); c, s = math.cos(r), math.sin(r)
    return v * c + np.cross(ax, v) * s + ax * (ax @ v) * (1 - c)
def load(d):
    R = {}; fi = -1; O = None
    for ln in open(d + "/views.log", errors="ignore"):
        if ln.startswith("SCR2 "):
            fi += 1; t = ln.split(); O = np.array([float(t[4]), float(t[5]), float(t[6])]); R[fi] = dict(O=O, pel=(float(t[1]), float(t[2])))
        elif ln.startswith("BODY2 ") and fi >= 0:
            t = ln.split(); R[fi]["body"] = np.array([float(x) for x in t[1:40]]).reshape(13, 3)
        elif ln.startswith("BLADE ") and fi >= 0:
            t = ln.split(); K = lambda k, n: [float(x) for x in t[t.index(k) + 1:t.index(k) + 1 + n]]
            r = R[fi]; r["g"] = (float(t[1]), float(t[2])); r["t"] = (float(t[3]), float(t[4]))
            r["hr"] = K("hr", 2); r["hd"] = K("hd", 2); r["ft"] = K("ft", 8)
            r["gw"] = np.array(K("gw", 3)); r["tw"] = np.array(K("tw", 3)); r["ax"] = np.array(K("ax", 3))
            r["kn"] = np.array(K("kn", 6)).reshape(2, 3); sc = K("sc", 4); r["w"], r["tilt"], r["spr"], r["inw"] = sc
            r["face"] = K("face", 1)[0]; sv = K("sv", 5); r["want"], r["raw"], r["sig"], r["mov"], r["stf"] = sv
            f = math.radians(r["face"]); r["left"] = np.array([math.cos(f), 0, -math.sin(f)]); r["ahead"] = np.array([math.sin(f), 0, math.cos(f)])
            b = r["tw"] - r["gw"]; r["L"] = float(np.linalg.norm(b)); b = b / r["L"]
            r["b0"] = rot(r["left"], -r["tilt"], rot(r["ahead"], -r["inw"], b))
    return {k: v for k, v in R.items() if "gw" in v and "body" in v}
