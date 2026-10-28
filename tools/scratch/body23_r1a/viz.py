"""1:1 (or zoomed) clay crops with outlines: rows = bodies, cols = (frame, side, region box); A's outline red on later
rows, the row's own outline cyan.  viz.sheet([(name, Body)], out, cols, zoom)"""
import numpy as np
from PIL import Image
import k, m
import harness as h
import sh

BOXES = {   # (frame, side): box about the shoulder joint (dx0, dy0, dx1, dy1) px
    "sh": (-120, -90, 110, 150),
    "arm": (-130, -90, 130, 260),
    "pit": (-90, -40, 90, 120),
}


def box(fr, sd, kind):
    if kind == "elbow":
        q = h.project(fr.Pm, k.joint(fr, "lowerarm_" + sd)[None])[0]
        b = (-110, -110, 110, 110)
    else:
        q = h.project(fr.Pm, k.joint(fr, "upperarm_" + sd)[None])[0]
        b = BOXES[kind]
    return (int(q[0] + b[0]), int(q[1] + b[1]), int(q[0] + b[2]), int(q[1] + b[3]))


def sheet(bodies, out, cols, zoom=1, outlines=True, game=None):
    rows = []
    EA = {}
    for ri, (name, body) in enumerate(bodies):
        ims = []
        for f, sd, kind in cols:
            fr = k.frame(f)
            bx = box(fr, sd, kind)
            g = k.geom(fr, body)
            rgb, ids = sh.clay(fr, g, bx)
            zt = g["z"][g["I"]].mean(1)
            E = h.edges(ids, zt)
            e = sh.down(E)
            a = rgb.copy()
            if outlines:
                if (f, sd, kind) in EA and ri > 0:
                    ea = EA[(f, sd, kind)]
                    a[:ea.shape[0], :ea.shape[1]][ea[:a.shape[0], :a.shape[1]]] = (255, 40, 40)
                if ri > 0:
                    a[:e.shape[0], :e.shape[1]][e[:a.shape[0], :a.shape[1]]] = (0, 230, 255)
            if ri == 0:
                EA[(f, sd, kind)] = e
            im = Image.fromarray(a)
            if zoom != 1:
                im = im.resize((int(im.width * zoom), int(im.height * zoom)), Image.LANCZOS)
            ims.append(im)
        rows.append(ims)
    W = sum(im.width for im in rows[0]) + 4 * (len(rows[0]) - 1)
    H = sum(max(im.height for im in r) for r in rows) + 4 * (len(rows) - 1)
    S = Image.new("RGB", (W, H), (255, 0, 255))
    y = 0
    for r in rows:
        x = 0
        for im in r:
            S.paste(im, (x, y)); x += im.width + 4
        y += max(im.height for im in r) + 4
    S.save(out)
    return S.size
