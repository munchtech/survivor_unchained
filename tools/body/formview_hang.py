"""P1 R1: arms-hanging clay of a BUILD (the lbs poser = the game's drive on B: the girdle law from the arm), a row
per build (and a cel row with --both). python tools/body/formview_hang.py OUT.png BUILD... [--deg 8] [--views ...]"""
import sys, json, math, argparse
import numpy as np
from pathlib import Path
import os; WT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WT + '/tools/body')
import check, rig_drive as rd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from formview import tiles
from PIL import Image
ap = argparse.ArgumentParser()
ap.add_argument("out"); ap.add_argument("builds", nargs="+")
ap.add_argument("--views", default="front,q34,side,back")
ap.add_argument("--y0", type=float, default=1.05); ap.add_argument("--y1", type=float, default=1.90)
ap.add_argument("--x", type=float, default=0.32); ap.add_argument("--px", type=float, default=700)
ap.add_argument("--deg", type=float, default=8.0); ap.add_argument("--both", action="store_true")
ap.add_argument("--cel", action="store_true"); ap.add_argument("--npz")
a = ap.parse_args()
rows = []
for b in a.builds:
    P = check.make_poser('lbs', b + '/body.glb', json.loads(Path(b + '/rig.json').read_text()))
    I = P.index; h = lambda G, n: G[I[n]][:3, 3]
    V, G, _ = P.pose([])
    t = []
    for s, sg in (('l', 1), ('r', -1)):
        d = rd._n(h(G, 'lowerarm_' + s) - h(G, 'upperarm_' + s))
        e = math.radians(a.deg)
        t.append(('upperarm_' + s, rd._arc(d, rd._n(np.array([sg * math.sin(e), -math.cos(e), 0.03])))))
    V, G, _ = P.pose(t)
    T = np.asarray(P.T)
    if a.npz:
        np.savez(a.npz, V=V, T=T)
    vs = a.views.split(",")
    if a.both:
        rows.append(tiles(V, T, vs, a.y0, a.y1, a.x, a.px, False)); rows.append(tiles(V, T, vs, a.y0, a.y1, a.x, a.px, True))
    else:
        rows.append(tiles(V, T, vs, a.y0, a.y1, a.x, a.px, a.cel))
Image.fromarray(np.concatenate(rows, 0)).save(a.out); print("wrote", a.out)
