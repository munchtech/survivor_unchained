"""addball.py: extra balls on neck_01 for the offline runs: each frame's dump gets them inserted after the file's 11 balls,
placed by neck_01's move (from balls b1, b2 and b1's back direction)."""
import numpy as np
B1, B2 = np.array([0, 1.6240698, -0.0467118]), np.array([0, 1.5740698, -0.0433942])
def nz(v): n = np.linalg.norm(v); return v / n
def frame(u, v):
    u = nz(u); v = nz(v - (v @ u) * u); return np.c_[u, v, np.cross(u, v)]
def add(fr, extra):
    """extra: list of (rest point, r, behind)."""
    for d in fr:
        if d.get("_added"): continue
        at = d["at"]; s = np.linalg.norm(at[1] - at[2]) / np.linalg.norm(B1 - B2)
        R = frame(at[1] - at[2], d["back"][1]) @ frame(B1 - B2, np.array([0, 0, -1.0])).T
        for j, (P, r, bh) in enumerate(extra):
            w = at[1] + s * R @ (np.array(P) - B1)
            d["at"] = np.insert(d["at"], 11 + j, w, axis=0)
            d["back"] = np.insert(d["back"], 11 + j, d["back"][1], axis=0)
            d["across"] = np.insert(d["across"], 11 + j, np.zeros(3), axis=0)
            d["r"] = np.insert(d["r"], 11 + j, r * s / 1.04 * 1.04 / s * s if False else r * s / s, axis=0)
            d["behind"] = np.insert(d["behind"], 11 + j, bh, axis=0)
        d["_added"] = True
    return fr
