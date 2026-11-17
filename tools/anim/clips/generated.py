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

from retarget import Source, best_loop, clip_from, face_forward, in_place, lean_neck, make_loop, retarget
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
    "test_walk_her_0": dict(source="kimodo", file="her_walk_0.bvh", loop=True, place="line", cycle=(0.9, 1.4),
                              note="Kimodo her_walk take 0 (walk candidate)"),
    "test_walk_her_1": dict(source="kimodo", file="her_walk_1.bvh", loop=True, place="line", cycle=(0.9, 1.4),
                              note="Kimodo her_walk take 1 (walk candidate)"),
    "test_walk_her_2": dict(source="kimodo", file="her_walk_2.bvh", loop=True, place="line", cycle=(0.9, 1.4),
                              note="Kimodo her_walk take 2 (walk candidate)"),
    "test_walk_her_3": dict(source="kimodo", file="her_walk_3.bvh", loop=True, place="line", cycle=(0.9, 1.4),
                              note="Kimodo her_walk take 3 (walk candidate)"),
    "test_walk_her_4": dict(source="kimodo", file="her_walk_4.bvh", loop=True, place="line", cycle=(0.9, 1.4),
                              note="Kimodo her_walk take 4 (walk candidate)"),
    "test_walk_woman_0": dict(source="kimodo", file="walk_woman_0.bvh", loop=True, place="line", cycle=(0.9, 1.4),
                              note="Kimodo woman_walk take 0 (walk candidate)"),
    "test_walk_woman_1": dict(source="kimodo", file="walk_woman_1.bvh", loop=True, place="line", cycle=(0.9, 1.4),
                              note="Kimodo woman_walk take 1 (walk candidate)"),
    "test_walk_woman_2": dict(source="kimodo", file="walk_woman_2.bvh", loop=True, place="line", cycle=(0.9, 1.4),
                              note="Kimodo woman_walk take 2 (walk candidate)"),
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


# (body-b-skill-clips, 17 Nov) The warden's leap is the shared take's timing (still landing at frame 13, Arts.Leap's
# 0.42 s) resampled with aa: at 2.2x each frame took the take at one instant and skipped the 1.2 source frames between
# (aliasing), so its fast beats came out as one-frame snaps and reversals (27 pops): the spring's knees 79-88 deg in a
# frame (calf_l, calf_r, foot_l at f2), the left fingers' regrip 31-37 deg at f11, the arms at f9-13, and the speed
# halving in one frame at f13. Each frame now averages the take over the stretch it stands for (a tent 2.5 of its
# frames wide each side), and the speed eases across the join. The other callings' leap keeps TABLE's (no aa).
LEAP_WARDEN_AA = 2.5


def warp(src, segments, aa=False):
    """The take resampled so each (from, to) stretch lasts its given time. `aa` (a width, in output frames): a frame
    that stands for more than one source frame (a stretch sped up) is the take averaged under a tent that many of its
    frames wide each side, not the one instant (the fast beats' snaps between frames: aliasing), and the speed eased
    across the joins. 0/False: as before."""
    times, rate = [], []
    for a, b, d in segments:
        n = max(2, int(round(d * 30)))
        for k in range(n):
            times.append(a + (b - a) * k / n)
            rate.append((b - a) * 30.0 / n)
    times.append(segments[-1][1])
    rate.append(rate[-1])
    if aa and len(segments) > 1:
        # The speed eased from one stretch's to the next's (a cubic through the same joins: the stretches' ends land on
        # the same frames), not changed in one frame (the arms' snap at a join).
        ns = [max(2, int(round(d * 30))) for _, _, d in segments]
        kf = np.concatenate([[0], np.cumsum(ns)]).astype(float)
        kt = np.array([segments[0][0]] + [b for _, b, _ in segments]) * 30.0
        sec = np.diff(kt) / np.diff(kf)
        m = np.concatenate([[sec[0]], (sec[:-1] + sec[1:]) / 2, [sec[-1]]])
        times, rate = [], []
        for i in range(len(segments)):
            h = kf[i + 1] - kf[i]
            for k in range(int(ns[i]) + (1 if i == len(segments) - 1 else 0)):
                u = k / h
                h00, h10, h01, h11 = 2*u**3 - 3*u**2 + 1, u**3 - 2*u**2 + u, -2*u**3 + 3*u**2, u**3 - u**2
                d00, d10, d01, d11 = 6*u**2 - 6*u, 3*u**2 - 4*u + 1, -6*u**2 + 6*u, 3*u**2 - 2*u
                times.append((h00 * kt[i] + h10 * h * m[i] + h01 * kt[i + 1] + h11 * h * m[i + 1]) / 30.0)
                rate.append((d00 * kt[i] + d01 * kt[i + 1]) / h + d10 * m[i] + d11 * m[i + 1])
    last = src.rot.shape[0] - 1

    def at(t):
        t = np.clip(t, 0, last)
        lo = np.floor(t).astype(int)
        hi = np.minimum(lo + 1, last)
        f = t - lo
        pos = src.pos[lo] * (1 - f[:, None, None]) + src.pos[hi] * f[:, None, None]
        rot = np.empty((len(t),) + src.rot.shape[1:])
        for i in range(len(t)):
            for j in range(src.rot.shape[1]):
                rot[i, j] = qslerp(src.rot[lo[i], j], src.rot[hi[i], j], f[i])
        return rot, pos

    t = np.array(times) * 30.0
    rot, pos = at(t)
    if aa:
        for i, r in enumerate(rate):
            if r <= 1.0:
                continue
            h = r * float(aa)
            d = np.linspace(-h, h, 2 * int(np.ceil(h)) + 3)
            w = 1.0 - np.abs(d) / h
            w /= w.sum()
            qs, ps = at(t[i] + d)
            sgn = np.sign(np.einsum("kjc,jc->kj", qs, rot[i]))
            sgn[sgn == 0] = 1.0
            q = np.einsum("k,kjc->jc", w, qs * sgn[..., None])
            rot[i] = q / np.linalg.norm(q, axis=-1, keepdims=True)
            pos[i] = np.einsum("k,kjc->jc", w, ps)
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


def make(rig, name, source, file, warp_=None, loop=False, place="line", ground=False, layer="full", note="", span=None, cycle=None,
         aa=False):
    path = MOCAP / source / file
    if not path.exists():
        return None
    desc, profile = LICENCE[source]
    src = Source(path, profile=profile)
    if ground:
        src.profile = dict(src.profile, ground=ground)
    if warp_:
        warp(src, warp_, aa)
    local, pos, info = retarget(rig.sk, src)
    local, pos = face_forward(rig.sk, local, pos)
    local = lean_neck(rig, local)
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
        lo, hi = (int(cycle[0] * 30), int(cycle[1] * 30)) if cycle else (int(0.6 * len(local)), len(local) - 1)
        d, a, b = best_loop(local, pos, rig.sk, lo, hi)
        local, pos = make_loop(local, pos, a, b)
    meta = {"source": f"{desc}: {file}", "licence": desc.split(":")[0],
            "changes": "retargeted to her skeleton, feet locked" + (", retimed" if warp_ else "") +
                       (", looped" if loop else "") + ("" if place == "keep" else ", in place"),
            "layer": layer, "speed": speed, "note": note}
    return clip_from(name, rig.sk, local, pos, loop=loop, meta=meta)


def clips(rig, want):
    out = []
    for name, row in TABLE.items():
        if name.startswith("test_") and not any(name in w or w in name for w in want):
            continue
        if want and not any(w in name for w in want):
            continue
        row = dict(row)
        row["warp_"] = row.pop("warp", None)
        c = make(rig, name, **row)
        if c is not None:
            out.append(c)
    # The warden's own leap: the shared take, its axe crouch settled into Prowl's f0 over 18 frames, the feet stepping
    # (prowl.settle). PlayerView plays leap_<calling> when the pack has one; the other callings keep `leap`.
    if os.environ.get("WARDEN_IDLE", "prowl") == "prowl" and (not want or any(w in "leap_warden" and len(w) > 4 or "leap_warden" in w for w in want)):
        from clips import prowl, idle
        row = dict(TABLE["leap"]); row["warp_"] = row.pop("warp", None)
        row["aa"] = LEAP_WARDEN_AA
        c = make(rig, "leap", **row)
        if c is not None:
            c = prowl.settle(rig, c, n=18, fingers_l=idle.warden(0, 0)["fingers_l"])
            c.name = "leap_warden"
            out.append(c)
    return out
