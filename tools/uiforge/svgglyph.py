"""The designer's line glyphs (godot/data/content/glyphs.json, a 24-unit square,
1.6 stroke) as masks at any size: strokes, and fills for closed shapes.
"""
from __future__ import annotations

import json
import os

import cv2
import numpy as np
from svgelements import Path, Move, Close

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
_G = None


def glyphs():
    global _G
    if _G is None:
        _G = json.load(open(os.path.join(ROOT, "godot", "data", "content", "glyphs.json"), encoding="utf-8"))
    return _G


def subpaths(d):
    """Polylines (lists of (x, y) in glyph units) and whether each is closed."""
    p = Path(d)
    out = []
    cur = []
    closed = False
    for seg in p:
        if isinstance(seg, Move):
            if len(cur) > 1:
                out.append((cur, closed))
            cur = [(seg.end.x, seg.end.y)]
            closed = False
            continue
        if isinstance(seg, Close):
            closed = True
            if cur and seg.end is not None:
                cur.append((seg.end.x, seg.end.y))
            continue
        n = max(2, int(seg.length() * 6)) if hasattr(seg, "length") else 2
        for i in range(1, n + 1):
            pt = seg.point(i / n)
            cur.append((pt.x, pt.y))
    if len(cur) > 1:
        out.append((cur, closed))
    return out


def masks(key, size, stroke=1.6, pad=1.0, fill_closed=True, ss=4):
    """(stroke mask, fill mask) at `size` px for the glyph's 24-unit box with `pad` units margin."""
    d = glyphs()[key]
    S = size * ss
    scale = S / (24 + 2 * pad)
    stroke_m = np.zeros((S, S), np.uint8)
    fill_m = np.zeros((S, S), np.uint8)
    for pts, closed in subpaths(d):
        P = np.round((np.asarray(pts) + pad) * scale * 16).astype(np.int32)
        if len(P) < 2:
            continue
        # Degenerate dots (M x y L x+0.01 y): a round dot.
        span = np.ptp(np.asarray(pts), axis=0).max()
        if span < 0.05:
            c = tuple((P[0] // 16).tolist())
            cv2.circle(stroke_m, c, max(1, int(stroke * scale / 2)), 255, -1, cv2.LINE_AA)
            continue
        cv2.polylines(stroke_m, [P], closed, 255, max(1, int(round(stroke * scale))), cv2.LINE_AA, shift=4)
        if closed and fill_closed:
            cv2.fillPoly(fill_m, [P], 255, cv2.LINE_AA, shift=4)
    st = cv2.resize(stroke_m, (size, size), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    fl = cv2.resize(fill_m, (size, size), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    return st, fl


def bold(key, size, stroke=1.6, pad=1.2, ss=4, groove=1.25):
    """A bold silhouette of the glyph: closed shapes filled, their outlines kept,
    detail strokes that fall inside a fill cut into it as grooves (the skull's eyes,
    the eye's pupil). Returns (body, groove) masks 0..1 at `size`."""
    d = glyphs()[key]
    S = size * ss
    scale = S / (24 + 2 * pad)
    fill_m = np.zeros((S, S), np.uint8)
    line_m = np.zeros((S, S), np.uint8)
    cut_m = np.zeros((S, S), np.uint8)
    subs = subpaths(d)
    sw = max(1, int(round(stroke * scale)))

    def poly(pts):
        return np.round((np.asarray(pts) + pad) * scale * 16).astype(np.int32)

    big = [(pts, closed) for pts, closed in subs if closed and np.ptp(np.asarray(pts), axis=0).max() > 2.5]
    for pts, closed in big:
        P = poly(pts)
        cv2.fillPoly(fill_m, [P], 255, cv2.LINE_AA, shift=4)
        cv2.polylines(line_m, [P], True, 255, sw, cv2.LINE_AA, shift=4)
    for pts, closed in subs:
        arr = np.asarray(pts)
        if closed and np.ptp(arr, axis=0).max() > 2.5:
            continue
        P = poly(pts)
        inside = np.mean([fill_m[min(S - 1, max(0, int((y + pad) * scale))), min(S - 1, max(0, int((x + pad) * scale)))] > 127 for x, y in pts]) > 0.5
        target = cut_m if inside else line_m
        w = int(sw * (groove if inside else 1.0))
        if np.ptp(arr, axis=0).max() < 0.05 or (closed and np.ptp(arr, axis=0).max() <= 2.5):
            c = tuple((P.mean(axis=0) / 16).astype(int).tolist())
            r = max(1, int(max(np.ptp(arr, axis=0).max() * scale / 2, sw * (0.75 if inside else 0.5))))
            cv2.circle(target, c, r, 255, -1, cv2.LINE_AA)
        else:
            cv2.polylines(target, [P], closed, 255, w, cv2.LINE_AA, shift=4)
    body = np.maximum(fill_m, line_m).astype(np.float32) / 255
    cut = cut_m.astype(np.float32) / 255
    body = cv2.resize(body, (size, size), interpolation=cv2.INTER_AREA)
    cut = cv2.resize(cut, (size, size), interpolation=cv2.INTER_AREA)
    return body, cut
