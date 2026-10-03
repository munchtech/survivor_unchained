"""Clips from 100STYLE (Ian Mason, CC BY 4.0): her idles and walks.

The takes are fetched once by tools/anim/fetch.py into C:/Users/munch/Tools/
mocap/100STYLE (or MOCAP_DIR). Each clip names its take, the stretch used and
what was done to it, for the credit's "indication of changes".
"""
from __future__ import annotations

import csv
import os
from pathlib import Path

import numpy as np

from retarget import Source, best_loop, clip_from, face_forward, in_place, make_loop, retarget

STYLE = Path(os.environ.get("MOCAP_DIR", r"C:\Users\munch\Tools\mocap")) / "100STYLE"


def cuts():
    rows = {}
    with open(STYLE / "Frame_Cuts.csv") as f:
        for r in csv.DictReader(f):
            rows[r["STYLE_NAME"]] = r
    return rows


def take(style, kind):
    c = cuts()[style]
    start = int(c[f"{kind}_START"])
    stop = int(c[f"{kind}_STOP"])
    return STYLE / style / f"{style}_{kind}.bvh", start, stop


def idle_loop(name, rig, style, seconds=(4.0, 8.0), window=None, stance=0.8):
    """A standing loop from a style's idle take: the stretch whose ends meet
    best, between the given lengths."""
    path, start, stop = take(style, "ID")
    if window:
        start, stop = start + window[0] * 60, start + window[1] * 60
    src = Source(path, start, stop)
    local, pos, info = retarget(rig.sk, src, stance=stance)
    local, pos = face_forward(rig.sk, local, pos)
    d, a, b = best_loop(local, pos, rig.sk, int(seconds[0] * 30), int(seconds[1] * 30))
    L, P = make_loop(local, pos, a, b)
    P, speed, heading = in_place(rig.sk, P)
    meta = {"source": f"100STYLE {style}_ID frames {start + a * 2}-{start + b * 2} (60 fps)", "licence": "CC BY 4.0",
            "changes": "retargeted to her skeleton, feet locked, looped (seam spread), centred",
            "layer": "full", "speed": 0.0}
    return clip_from(name, rig.sk, L, P, loop=True, meta=meta)


def clips(rig, want):
    out = []
    if not want or any("idle_neutral" in w for w in want):
        out.append(idle_loop("idle_neutral", rig, "Neutral"))
    if not want or any("idle_proud" in w for w in want):
        out.append(idle_loop("idle_proud", rig, "Proud"))
    return out
