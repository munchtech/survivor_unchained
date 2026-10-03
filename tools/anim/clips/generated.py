"""Clips from motion made elsewhere and retargeted onto her: Kimodo
(generated, NVIDIA Open Model License), SAM 3D Body (video, SAM License)
and Mixamo (Adobe; usable in the game, never shipped as its own files).

Each source's motion lands as BVH under C:/Users/munch/Tools/mocap/<source>/
(MOCAP_DIR): kimodo_gen.py and kimodo_bvh.py for Kimodo, video_motion.py for
SAM 3D Body, fbx_bvh.py for Mixamo's FBX. The table below says which BVH
becomes which clip of hers, which stretch of it, and how it is cleaned up.
Takes that are not on this machine are skipped (the clip then stays as it
was, or the library plays).
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np

from retarget import Source, best_loop, clip_from, face_forward, in_place, make_loop, retarget

MOCAP = Path(os.environ.get("MOCAP_DIR", r"C:\Users\munch\Tools\mocap"))

LICENCE = {
    "kimodo": ("Kimodo-SOMA-RP (NVIDIA, NVIDIA Open Model License): generated", "soma"),
    "video": ("SAM 3D Body (Meta, SAM License) from video", "soma"),
    "mixamo": ("Mixamo (Adobe): used in the game under Mixamo's terms, raw files not redistributed", "mixamo"),
}

# name: (source, file, (start s, end s) or None, loop, in place, layer, note)
TABLE = {
    "test_kimodo_leap": ("kimodo", "example_01_single_text_prompt.bvh", None, False, False, "full",
                         "Kimodo's own example: runs and leaps an obstacle (pipeline test)"),
}


def make(rig, name, source, file, span, loop, place, layer, note):
    path = MOCAP / source / file
    if not path.exists():
        return None
    desc, profile = LICENCE[source]
    src = Source(path, profile=profile)
    if span:
        a, b = int(span[0] * 30), int(span[1] * 30)
        src.rot, src.pos = src.rot[a:b], src.pos[a:b]
    local, pos, info = retarget(rig.sk, src)
    local, pos = face_forward(rig.sk, local, pos)
    speed = 0.0
    if loop:
        d, a, b = best_loop(local, pos, rig.sk, int(0.6 * len(local)), len(local) - 1)
        local, pos = make_loop(local, pos, a, b)
    if place:
        pos, speed, _ = in_place(rig.sk, pos)
    meta = {"source": f"{desc}: {file}" + (f" {span[0]}-{span[1]} s" if span else ""), "licence": desc.split(":")[0],
            "changes": "retargeted to her skeleton, feet locked" + (", looped" if loop else "") + (", in place" if place else ""),
            "layer": layer, "speed": speed, "note": note}
    return clip_from(name, rig.sk, local, pos, loop=loop, meta=meta)


def clips(rig, want):
    out = []
    for name, row in TABLE.items():
        if name.startswith("test_") and not any(name in w for w in want):
            continue
        if want and not any(w in name for w in want):
            continue
        c = make(rig, name, *row)
        if c is not None:
            out.append(c)
    return out
