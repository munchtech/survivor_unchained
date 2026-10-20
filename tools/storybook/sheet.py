"""A contact sheet: pictures in a grid, each labelled, at the size a look needs.

    python tools/storybook/sheet.py <out.jpg> <img> [<img> ...] [--cols 4] [--cell 448] [--window]
"""
import argparse
import os

import cv2
import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("imgs", nargs="+")
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--cell", type=int, default=448, help="cell width in px")
    ap.add_argument("--window", action="store_true", help="crop each plate to the 2.39 window's band (about y 13-87%%)")
    a = ap.parse_args()
    cells = []
    for f in a.imgs:
        im = cv2.imread(f, cv2.IMREAD_COLOR)
        if a.window:
            hh = im.shape[0]
            im = im[int(hh * 0.134):int(hh * 0.866)]
        h, w = im.shape[:2]
        im = cv2.resize(im, (a.cell, int(h * a.cell / w)), interpolation=cv2.INTER_AREA)
        label = os.path.splitext(os.path.basename(f))[0]
        cv2.rectangle(im, (0, 0), (8 + 9 * len(label), 20), (0, 0, 0), -1)
        cv2.putText(im, label, (4, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
        cells.append(im)
    ch = max(c.shape[0] for c in cells)
    rows = []
    for i in range(0, len(cells), a.cols):
        row = [np.pad(c, ((0, ch - c.shape[0]), (0, 0), (0, 0))) for c in cells[i:i + a.cols]]
        while len(row) < a.cols:
            row.append(np.zeros((ch, a.cell, 3), np.uint8))
        rows.append(np.concatenate([np.pad(c, ((2, 2), (2, 2), (0, 0))) for c in row], axis=1))
    cv2.imwrite(a.out, np.concatenate(rows, axis=0), [cv2.IMWRITE_JPEG_QUALITY, 88])
    print(a.out)


if __name__ == "__main__":
    main()
