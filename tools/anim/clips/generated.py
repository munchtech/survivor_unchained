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
from rig import qinv, qrot, qslerp

MOCAP = Path(os.environ.get("MOCAP_DIR", r"C:\Users\munch\Tools\mocap"))

LICENCE = {
    "kimodo": ("Kimodo-SOMA-RP (NVIDIA, NVIDIA Open Model License): generated", "soma"),
    "video": ("SAM 3D Body (Meta, SAM License) from video", "mhr"),
    "mixamo": ("Mixamo (Adobe): used in the game under Mixamo's terms, raw files not redistributed", "mixamo"),
}

# name: {source, file, warp: [(from s, to s, lasting s)], loop, place:
# "keep" | "line" (straight travel out) | "pin" (all travel out, sway kept),
# ground: the lower foot held to the ground (the game makes the flight),
# layer, note}
TABLE = {
    "test_kimodo_leap": dict(source="kimodo", file="example_01_single_text_prompt.bvh", place="keep",
                             note="Kimodo's own example: runs and leaps an obstacle (pipeline test)"),
    "test_video_pose": dict(source="video", file="pexels_6769391_pose.bvh", place="line",
                            note="SAM 3D Body on Pexels video 6769391 (https://www.pexels.com/video/woman-wearing-denim-pants-6769391/, "
                                 "Pexels licence), 2-14 s: a woman posing, hands to hips and pockets (pipeline test)"),
    # The Crashing Leap: 0.42 s in the air (Arts.Leap), the game carries her
    # along the arc: from the spring, the flight squeezed into its time, the
    # axe brought down as she lands, and the crouch she lands in.
    "leap": dict(source="mixamo", file="run_jump_attack.bvh", warp=[(0.78, 1.70, 0.42), (1.70, 2.35, 0.65)],
                 place="pin", ground="exact",
                 note="Mixamo 'Standing Melee Run Jump Attack' (axe running jump attack), the flight retimed to the art's"),
}


def warp(src, segments):
    """The take resampled so each (from, to) stretch lasts its given time."""
    times = []
    for a, b, d in segments:
        n = max(2, int(round(d * 30)))
        for k in range(n):
            times.append(a + (b - a) * k / n)
    times.append(segments[-1][1])
    t = np.clip(np.array(times) * 30.0, 0, src.rot.shape[0] - 1)
    lo = np.floor(t).astype(int)
    hi = np.minimum(lo + 1, src.rot.shape[0] - 1)
    f = (t - lo)[:, None]
    pos = src.pos[lo] * (1 - f[..., None]) + src.pos[hi] * f[..., None]
    rot = np.empty((len(t),) + src.rot.shape[1:])
    for i in range(len(t)):
        for j in range(src.rot.shape[1]):
            rot[i, j] = qslerp(src.rot[lo[i], j], src.rot[hi[i], j], f[i, 0])
    src.rot, src.pos = rot, pos


def pin(sk, pos, sigma=6):
    """All horizontal travel taken out, the sway about it kept."""
    pel, root = sk.i("pelvis"), sk.i("root")
    w = qrot(sk.rest_rot[root], pos[:, pel])
    k = np.exp(-0.5 * (np.arange(-3 * sigma, 3 * sigma + 1) / sigma) ** 2)
    k /= k.sum()
    for ax in (0, 2):
        trend = np.convolve(np.pad(w[:, ax], 3 * sigma, mode="edge"), k, mode="valid")
        w[:, ax] -= trend
    p = pos.copy()
    p[:, pel] = qrot(qinv(sk.rest_rot[root]), w)
    return p


def make(rig, name, source, file, warp_=None, loop=False, place="line", ground=False, layer="full", note="", span=None):
    path = MOCAP / source / file
    if not path.exists():
        return None
    desc, profile = LICENCE[source]
    src = Source(path, profile=profile)
    if ground:
        src.profile = dict(src.profile, ground=ground)
    if warp_:
        warp(src, warp_)
    local, pos, info = retarget(rig.sk, src)
    local, pos = face_forward(rig.sk, local, pos)
    speed = 0.0
    if loop == "cycle":
        # The take is one whole cycle (Mixamo's walks): closed by its own
        # first frame, carried on by a frame's travel.
        pel = rig.sk.i("pelvis")
        step = (pos[-1, pel] - pos[0, pel]) / (len(pos) - 1)
        first = pos[:1].copy()
        first[0, pel] = pos[0, pel] + step * len(pos)
        local = np.concatenate([local, local[:1]])
        pos = np.concatenate([pos, first])
    # Travel out before looping (a loop's seam is spread over the clip, and
    # would take the travel with it).
    if place == "line":
        pos, speed, _ = in_place(rig.sk, pos)
    elif place == "pin":
        pos = pin(rig.sk, pos)
    if loop is True:
        d, a, b = best_loop(local, pos, rig.sk, int(0.6 * len(local)), len(local) - 1)
        local, pos = make_loop(local, pos, a, b)
    meta = {"source": f"{desc}: {file}", "licence": desc.split(":")[0],
            "changes": "retargeted to her skeleton, feet locked" + (", retimed" if warp_ else "") +
                       (", looped" if loop else "") + ("" if place == "keep" else ", in place"),
            "layer": layer, "speed": speed, "note": note}
    return clip_from(name, rig.sk, local, pos, loop=loop, meta=meta)


def clips(rig, want):
    out = []
    for name, row in TABLE.items():
        if name.startswith("test_") and not any(name in w for w in want):
            continue
        if want and not any(w in name for w in want):
            continue
        row = dict(row)
        row["warp_"] = row.pop("warp", None)
        c = make(rig, name, **row)
        if c is not None:
            out.append(c)
    return out
