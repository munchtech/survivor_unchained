#!/usr/bin/env python
"""The topology sheet: front, back, side, 3/4 of a tier (flat gray clay, the wireframe over it) and two crops at a
larger scale (her left shoulder and armpit, her hip and groin). Under 1800 x 1000.

    python tools/body/topo_sheet.py [--tier close] [--out tools/body/out/topo/sheet_close.png]
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ray  # noqa: E402


def view(cam, px, x0, x1, y0, y1, up=(0, 1.0, 0)):
    cam = np.asarray(cam, float) / np.linalg.norm(cam)
    ey = np.asarray(up, float) - (np.asarray(up, float) @ cam) * cam
    ey /= np.linalg.norm(ey)
    ex = np.cross(ey, cam)
    return ray.View(np.zeros(3), ex, ey, cam, px, x0, x1, y0, y1)


def render(V, Q, vw, edges, eq):
    T = np.concatenate([Q[:, [0, 1, 2]], Q[:, [0, 2, 3]]])
    tq = np.concatenate([np.arange(len(Q)), np.arange(len(Q))])
    img, m = ray.clay(V, T, vw)
    pid, _ = vw.cast(ray.scene(V, T))
    qmap = np.where(pid >= 0, tq[np.maximum(pid, 0)], -1)
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).convert("RGB")
    dr = ImageDraw.Draw(im)
    P = np.stack([(V - vw.o) @ vw.ex, (V - vw.o) @ vw.ey], 1)
    cx = (P[:, 0] - vw.x0) * vw.px
    cy = (vw.y1 - P[:, 1]) * vw.px
    for (a, b), qs in zip(edges, eq):
        vis = 0
        for f in (0.3, 0.5, 0.7):
            x = int((1 - f) * cx[a] + f * cx[b])
            y = int((1 - f) * cy[a] + f * cy[b])
            if 0 <= x < vw.w and 0 <= y < vw.h and qmap[y, x] in qs:
                vis += 1
        if vis >= 2:
            dr.line([(cx[a], cy[a]), (cx[b], cy[b])], fill=(40, 70, 140), width=1)
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", default="close")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    z = np.load(os.path.join(HERE, "out", "topo", a.tier + ".npz"))
    V, Q = z["V"].astype(float), z["Q"].astype(np.int64)
    E = {}
    for qi, q in enumerate(Q):
        for k in range(4):
            e = (min(q[k], q[(k + 1) % 4]), max(q[k], q[(k + 1) % 4]))
            E.setdefault(e, set()).add(qi)
    edges, eq = list(E.keys()), list(E.values())
    px = 400
    views = [((0, 0, 1), -0.56, 0.56), ((0, 0, -1), -0.56, 0.56), ((1, 0, 0), -0.24, 0.30), ((0.7, 0, 0.7), -0.5, 0.5)]
    tiles = [render(V, Q, view(c, px, x0, x1, 0.12, 1.66), edges, eq) for c, x0, x1 in views]
    crops = [render(V, Q, view((0.55, -0.1, 0.83), 1100, 0.02, 0.26, 1.30, 1.70), edges, eq),
             render(V, Q, view((0.25, -0.25, 0.93), 1100, -0.10, 0.14, 0.86, 1.26), edges, eq)]
    W = sum(t.width for t in tiles) + max(c.width for c in crops) + 10
    H = max(max(t.height for t in tiles), sum(c.height for c in crops) + 6)
    sheet = Image.new("RGB", (W, H), (255, 255, 255))
    x = 0
    for t in tiles:
        sheet.paste(t, (x, 0))
        x += t.width
    y = 0
    for c in crops:
        sheet.paste(c, (x + 10, y))
        y += c.height + 6
    out = a.out or os.path.join(HERE, "out", "topo", f"sheet_{a.tier}.png")
    sheet.save(out)
    print(out, sheet.size)


if __name__ == "__main__":
    main()
