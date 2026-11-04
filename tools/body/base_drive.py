"""The lbs poser's driver for the base rig (rig.json "poser": "tools.body.base_drive"): its helpers as
base_drive.json says (rig.json "helpers", copied there at build), then rig_drive's correctives table.

    drive(poser, G, rig) -> (G, {shape: weight})
"""
from __future__ import annotations

import numpy as np

from tools.body import rig_drive


def _rotvec(R):
    c = np.clip((np.trace(R) - 1) / 2, -1, 1)
    a = np.arccos(c)
    if a < 1e-9:
        return np.zeros(3)
    v = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]])
    n = np.linalg.norm(v)
    if n < 1e-9:                              # 180 degrees: the axis from R + I
        w, U = np.linalg.eigh((R + np.eye(3)) / 2)
        return U[:, -1] * a
    return v / n * a


def _expm(v):
    a = np.linalg.norm(v)
    if a < 1e-12:
        return np.eye(3)
    k = v / a
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K


def _unit(M):
    return M[:3, :3] / np.linalg.norm(M[:3, :3], axis=0)


def _roll(Rd, y):
    """The twist of rotation Rd about axis y (swing-twist), radians."""
    v = _rotvec(Rd)
    a = np.linalg.norm(v)
    if a < 1e-12:
        return 0.0
    q = np.concatenate([np.sin(a / 2) * v / a, [np.cos(a / 2)]])
    p = q[:3] @ y
    return 2 * np.arctan2(p, q[3])


def _set(poser, G, j, new):
    D = new @ np.linalg.inv(G[j])
    for k in poser.subtree(j):
        G[k] = D @ G[k]


def drive(poser, G, rig):
    G = G.copy()
    R0 = poser.rest
    for hd in rig.get("helpers", []):
        for s in ("l", "r"):
            n, f = hd["name"].replace("{s}", s), hd["follow"].replace("{s}", s)
            j, fj = poser.index.get(n), poser.index.get(f)
            if j is None or fj is None:
                continue
            p = poser.parent[j]
            a = float(hd["amount"])
            if hd["kind"] == "share":
                # the follow bone's turn from rest, in the world, about the joint; the share takes `a` of it
                Rf = _unit(G[fj]) @ _unit(R0[fj]).T
                Rp = _unit(G[p]) @ _unit(R0[p]).T
                Rrel = Rp.T @ Rf                     # the follow bone's turn beyond its parent's (world, rest-aligned)
                Rh = Rp @ _expm(a * _rotvec(Rrel))
                h_now = G[p] @ np.linalg.inv(R0[p]) @ R0[j][:, 3]
                new = np.eye(4)
                new[:3, :3] = Rh @ R0[j][:3, :3]
                new[:3, 3] = h_now[:3]
                _set(poser, G, j, new)
            elif hd["kind"] in ("counter_twist", "twist"):
                y = _unit(G[j])[:, 1]
                if hd["kind"] == "counter_twist":
                    pp = poser.parent[fj]
                    Rd = (_unit(G[fj]) @ _unit(R0[fj]).T) @ (_unit(G[pp]) @ _unit(R0[pp]).T).T
                    ang = -a * _roll(Rd, y)
                else:
                    Rd = (_unit(G[fj]) @ _unit(R0[fj]).T) @ (_unit(G[p]) @ _unit(R0[p]).T).T
                    ang = a * _roll(Rd, y)
                if abs(ang) < 1e-12:
                    continue
                R = _expm(y * ang)
                new = G[j].copy()
                new[:3, :3] = R @ G[j][:3, :3]
                _set(poser, G, j, new)
    G, shapes = rig_drive.drive(poser, G, rig)
    return G, shapes
