"""OpenPose skeletons for the ControlNet's pose mode: a plate's figures placed
by hand, so the painting stands them where the script says (Z-Image lays a
speared man down whatever the prompt says; r2).

    python tools/storybook/pose.py <figures.json> <out.png> [--w 1792 --h 1024]

figures.json: {"figures": [{"name": "dead", "pts": {"nose": [x, y], ...}}, ...]}
with x, y in 0..1 of the picture. Points: nose neck rsho relb rwri lsho lelb
lwri rhip rknee rank lhip lknee lank reye leye rear lear (right and left are the
figure's own). A missing point drops its limbs (a hidden arm, a face turned away).
"""
import argparse
import json
import math

import cv2
import numpy as np

NAMES = ["nose", "neck", "rsho", "relb", "rwri", "lsho", "lelb", "lwri", "rhip", "rknee", "rank",
         "lhip", "lknee", "lank", "reye", "leye", "rear", "lear"]
# The OpenPose (COCO-18) limbs and colours, as the pose annotators draw them.
LIMBS = [(2, 3), (2, 6), (3, 4), (4, 5), (6, 7), (7, 8), (2, 9), (9, 10), (10, 11), (2, 12), (12, 13),
         (13, 14), (2, 1), (1, 15), (15, 17), (1, 16), (16, 18), (3, 17), (6, 18)]
COLORS = [(255, 0, 0), (255, 85, 0), (255, 170, 0), (255, 255, 0), (170, 255, 0), (85, 255, 0), (0, 255, 0),
          (0, 255, 85), (0, 255, 170), (0, 255, 255), (0, 170, 255), (0, 85, 255), (0, 0, 255), (85, 0, 255),
          (170, 0, 255), (255, 0, 255), (255, 0, 170), (255, 0, 85)]


def draw(figures, w, h, stick=None):
    img = np.zeros((h, w, 3), np.uint8)
    stick = stick or max(3, int(round(4 * min(w, h) / 512)))
    for fig in figures:
        pts = [fig["pts"].get(n) for n in NAMES]
        pts = [None if p is None else (p[0] * w, p[1] * h) for p in pts]
        for i, (a, b) in enumerate(LIMBS[:17]):
            pa, pb = pts[a - 1], pts[b - 1]
            if pa is None or pb is None:
                continue
            mx, my = (pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2
            length = math.hypot(pa[0] - pb[0], pa[1] - pb[1])
            angle = math.degrees(math.atan2(pa[1] - pb[1], pa[0] - pb[0]))
            poly = cv2.ellipse2Poly((int(mx), int(my)), (int(length / 2), stick), int(angle), 0, 360, 1)
            c = COLORS[i]
            cv2.fillConvexPoly(img, poly, (int(c[2] * 0.6), int(c[1] * 0.6), int(c[0] * 0.6)))
        for i, p in enumerate(pts):
            if p is not None:
                c = COLORS[i]
                cv2.circle(img, (int(p[0]), int(p[1])), stick, (c[2], c[1], c[0]), -1)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("figures")
    ap.add_argument("out")
    ap.add_argument("--w", type=int, default=1792)
    ap.add_argument("--h", type=int, default=1024)
    a = ap.parse_args()
    spec = json.load(open(a.figures, encoding="utf-8"))
    cv2.imwrite(a.out, draw(spec["figures"], a.w, a.h))
    print(a.out)


if __name__ == "__main__":
    main()
