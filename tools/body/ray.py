"""Orthographic software raycasts (embreex) for the body check: masks, lambert clay, inside tests."""
from __future__ import annotations

import numpy as np
from embreex import rtcore_scene as rtcs
from embreex.mesh_construction import TriangleMesh


def scene(V, T):
    s = rtcs.EmbreeScene()
    TriangleMesh(s, V.astype(np.float32)[T])
    return s


def hits(s, org, dirs, chunk=2_000_000):
    """(primID [N], tfar [N]) of the first hit of each ray (-1 / inf where none)."""
    n = len(org)
    pid = np.full(n, -1, np.int64)
    tf = np.full(n, np.inf)
    for a in range(0, n, chunk):
        b = min(n, a + chunk)
        r = s.run(org[a:b].astype(np.float32), dirs[a:b].astype(np.float32), output=1)
        p = np.asarray(r["primID"]).astype(np.int64)
        pid[a:b] = p
        t = np.asarray(r["tfar"]).astype(float)
        tf[a:b] = np.where(p >= 0, t, np.inf)
    return pid, tf


class View:
    """An orthographic view: image x along ex, image y (up) along ey, looking along -cam (cam: toward the viewer).
    Pixel (i row, j col) centres; `px` pixels per metre; the window [x0,x1] x [y0,y1] metres about `origin`."""

    def __init__(self, origin, ex, ey, cam, px, x0, x1, y0, y1):
        self.o, self.ex, self.ey, self.cam = (np.asarray(a, float) for a in (origin, ex, ey, cam))
        self.px = px
        self.x0, self.y1 = x0, y1
        self.w = int(round((x1 - x0) * px))
        self.h = int(round((y1 - y0) * px))

    def grid(self):
        j, i = np.meshgrid(np.arange(self.w), np.arange(self.h))
        x = self.x0 + (j + 0.5) / self.px
        y = self.y1 - (i + 0.5) / self.px
        return x, y

    def to_px(self, xy):
        xy = np.asarray(xy, float)
        return np.stack([(xy[..., 0] - self.x0) * self.px, (self.y1 - xy[..., 1]) * self.px], -1)

    def xy(self, P):
        r = np.asarray(P, float) - self.o
        return np.stack([r @ self.ex, r @ self.ey], -1)

    def cast(self, s, far=5.0):
        x, y = self.grid()
        org = self.o + x[..., None] * self.ex + y[..., None] * self.ey + far * self.cam
        org = org.reshape(-1, 3)
        d = np.broadcast_to(-self.cam, org.shape)
        pid, tf = hits(s, org, d)
        return pid.reshape(self.h, self.w), tf.reshape(self.h, self.w)


def mask(V, T, view):
    pid, _ = view.cast(scene(V, T))
    return pid >= 0


def clay(V, T, view, light=None):
    """Flat gray clay, lambert: [h,w] floats 0..1 (background 1) and the mask."""
    pid, _ = view.cast(scene(V, T))
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    fn = fn / np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
    if light is None:
        light = 0.75 * view.cam + 0.45 * view.ey - 0.3 * view.ex
    light = light / np.linalg.norm(light)
    m = pid >= 0
    img = np.ones(pid.shape)
    n = fn[pid[m]]
    n = np.where((n @ view.cam)[:, None] < 0, -n, n)   # (two-sided)
    img[m] = 0.18 + 0.62 * np.clip(n @ light, 0, 1) + 0.08 * np.clip(n @ view.cam, 0, 1)
    return img, m


def inside(s, P, dirs=None, max_hits=24, eps=2e-5):
    """Parity inside test of points P against the scene (3 rays, majority). Open meshes leak; the rest pose's count
    is the noise floor."""
    if dirs is None:
        dirs = np.array([[0.5774, 0.5774, 0.5774], [-0.7071, 0.1, 0.7], [0.1, -0.9, -0.42]])
        dirs = dirs / np.linalg.norm(dirs, axis=1, keepdims=True)
    votes = np.zeros(len(P), int)
    for d in dirs:
        org = P.copy()
        cnt = np.zeros(len(P), int)
        live = np.ones(len(P), bool)
        for _ in range(max_hits):
            idx = np.nonzero(live)[0]
            if not len(idx):
                break
            pid, tf = hits(s, org[idx], np.broadcast_to(d, (len(idx), 3)))
            h = pid >= 0
            cnt[idx[h]] += 1
            org[idx[h]] = org[idx[h]] + (tf[h, None] + eps) * d
            live[idx[~h]] = False
        votes += cnt % 2
    return votes >= 2


def boundary(m):
    """Mask pixels on its edge (4-neighbour)."""
    e = np.zeros_like(m)
    e[1:-1, 1:-1] = m[1:-1, 1:-1] & ~(m[:-2, 1:-1] & m[2:, 1:-1] & m[1:-1, :-2] & m[1:-1, 2:])
    e[0, :] = m[0, :]
    e[-1, :] = m[-1, :]
    e[:, 0] = m[:, 0]
    e[:, -1] = m[:, -1]
    return e
