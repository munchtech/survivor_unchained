"""Her walks, from 100STYLE's forward walks (Ian Mason, CC BY 4.0): a stretch
of a style's walk, retargeted, its travel taken out and closed into one
stride pair, with its speed for the game to carry her at (so the feet hold
to the ground).

Tried by name: python tools/anim/build.py try_walk_<Style> (any 100STYLE
style with a forward walk).
"""
from __future__ import annotations

from clips.mocap import STYLE, cuts
from retarget import Source, best_loop, clip_from, face_forward, in_place, lean_neck, make_loop, retarget


def straight(style, seconds=2.2, after=3.0, within=40.0):
    """Where in a style's forward walk the performer goes straightest for
    `seconds` (they walk a small room, turning every few metres): seconds
    into the walk."""
    import numpy as np
    import bvh
    c = cuts()[style]
    a, b = int(c["FW_START"]), int(c["FW_STOP"])
    take = bvh.load(STYLE / style / f"{style}_FW.bvh")
    _, p = take.globals(a, min(b, a + int(within * 60)))
    xz = p[:, 0][:, [0, 2]]
    n = int(seconds * 60)
    best = (0.0, after)
    for t in range(int(after * 60), len(xz) - n, 15):
        seg = xz[t:t + n]
        path = np.sum(np.linalg.norm(np.diff(seg, axis=0), axis=1))
        chord = np.linalg.norm(seg[-1] - seg[0])
        if path > 0 and chord / path > best[0]:
            best = (chord / path, t / 60)
    return best[1]


def walk_loop(name, rig, style, start_s=None, seconds=2.2, cycle=(0.9, 1.4)):
    """One closed stride pair from a style's forward walk, from its
    straightest stretch (or `start_s` into it)."""
    c = cuts()[style]
    if start_s is None:
        start_s = straight(style, seconds)
    a0 = int(c["FW_START"]) + int(start_s * 60)
    path = STYLE / style / f"{style}_FW.bvh"
    src = Source(path, a0, a0 + int(seconds * 60))
    local, pos, _ = retarget(rig.sk, src, stance=0.8)
    local, pos = face_forward(rig.sk, local, pos)
    local = lean_neck(rig, local)
    pos, speed, _ = in_place(rig.sk, pos)
    d, a, b = best_loop(local, pos, rig.sk, int(cycle[0] * 30), int(cycle[1] * 30))
    L, P = make_loop(local, pos, a, b)
    # The speed over the loop's own stretch (in_place measured the whole window).
    meta = {"source": f"100STYLE {style}_FW frames {a0 + a * 2}-{a0 + b * 2} (60 fps)", "licence": "CC BY 4.0",
            "changes": "retargeted to her skeleton, feet locked, travel taken out, looped (seam spread)",
            "layer": "full", "speed": speed, "note": f"her walk ({style})"}
    return clip_from(name, rig.sk, L, P, loop=True, meta=meta)


TRY = ["Neutral", "Depressed", "Old", "HighKnees", "BentForward", "Heavyset", "Proud"]


def _over(name, rig, base, carriage, lift=0.0, meta=None):
    """The walk with a carriage laid over it (back, neck, head, shoulders,
    the hips' lean: carriage(fr) gives the turns), and each foot lifted
    `lift` metres higher at the middle of its swing (wading)."""
    import math

    import numpy as np

    from held import solved
    sk = rig.sk
    g, p = sk.fk(base.rot, base.pos)
    I = sk.index
    n = base.frames
    poses = []
    # A foot swings while it travels forward under her (in place, a planted
    # foot slides back at the walk's speed).
    swing = {}
    for s in "lr":
        z = p[:, I[f"foot_{s}"], 2]
        vz = np.gradient(np.concatenate([z[-3:-1], z, z[1:3]]))[2:-2]
        on = vz > 0.002
        prof = np.zeros(n)
        k = 0
        while k < n:
            if on[k]:
                j = k
                while j + 1 < n and on[j + 1]:
                    j += 1
                for t in range(k, j + 1):
                    prof[t] = math.sin(math.pi * (t - k + 0.5) / (j - k + 1))
                k = j + 1
            else:
                k += 1
        swing[s] = prof
    for fr in range(n):
        pose = dict(carriage(fr))
        if lift:
            for s in "lr":
                if swing[s][fr] <= 0.01:
                    continue
                at = p[fr, I[f"foot_{s}"]]
                rest = rig.prest[I[f"foot_{s}"]]
                # Toes down as the foot comes up out of the water, the knee driven forward.
                pose[f"foot_{s}"] = {"pos": (float(at[0]), float(at[1] - rest[1] + lift * swing[s][fr]), float(at[2] + 0.03 * swing[s][fr])),
                                     "rot": tuple(_foot_euler(g[fr, I[f"foot_{s}"]], rig, s, extra_pitch=25 * swing[s][fr])),
                                     "pole": (0.1 if s == "l" else -0.1, 0.0, 1.0)}
        poses.append(pose)
    m = dict(base.meta)
    m.update(meta or {})
    clip = solved(name, rig, poses, base=base, meta=m)
    clip.loop = base.loop
    return clip


def _foot_euler(grot, rig, side, extra_pitch=0.0):
    """A foot's turn from rest as the keyed (yaw, pitch, roll), plus extra pitch."""
    import math

    import numpy as np

    from rig import qinv, qmul, qrot
    d = qmul(grot, qinv(rig.grest[rig.I[f"foot_{side}"]]))
    fwd = qrot(d, np.array([0.0, 0.0, 1.0]))
    yaw = math.degrees(math.atan2(fwd[0], fwd[2]))
    pitch = math.degrees(math.asin(max(-1.0, min(1.0, -fwd[1]))))
    return (yaw, pitch + extra_pitch, 0.0)


def walk_tired(rig):
    """C04: the walk of a woman after a night like that one: her own pace
    (100STYLE Neutral), the head a little down, the shoulders dropped and
    forward, the arms heavier."""
    base = walk_loop("walk_tired", rig, "Neutral")
    return _over("walk_tired", rig, base, lambda fr: {"spine": (0, 4, 0), "neck": (0, 4, 0), "head": (0, 5, 0),
                                                     "clav_l": (-3, 4), "clav_r": (-3, 4)},
                 meta={"note": "her walk, tired (C04: up out of the ford, up the road, into the Waystation)"})


def walk_uphill(rig):
    """C04 A8: up the road to the gate, seen from behind: leaning into the
    hill from the ankles, the head up to see where she is going."""
    base = walk_loop("walk_uphill", rig, "Neutral")
    return _over("walk_uphill", rig, base, lambda fr: {"hips": {"rot": (0, 9, 0)}, "spine": (0, 4, 0), "neck": (0, -6, 0),
                                                      "head": (0, -5, 0), "clav_l": (-2, 5), "clav_r": (-2, 5)},
                 meta={"note": "her walk up a hill, leaning into it (C04 A8)"})


def wade(rig):
    """C04 A1: wading out through the shallows: each foot lifted up out of
    the water and driven forward, a little lean. Play it at about 0.8 and change to walk_tired at the bank."""
    base = walk_loop("wade", rig, "Neutral")
    return _over("wade", rig, base, lambda fr: {"hips": {"rot": (0, 6, 0)}, "spine": (0, 4, 0), "neck": (0, 2, 0), "head": (0, 6, 0),
                                               "clav_l": (2, 0), "clav_r": (2, 0)},
                 lift=0.13, meta={"note": "her wade out of shin-deep water (C04 A1); the feet lifted clear each stride"})


def clips(rig, want):
    out = []
    for style in TRY:
        name = f"try_walk_{style}"
        if any(name in w for w in want):
            out.append(walk_loop(name, rig, style))
    for name, fn in (("walk_tired", walk_tired), ("walk_uphill", walk_uphill), ("wade", wade)):
        if (want and any(w in name for w in want)) or (not want and name in JUDGED):
            out.append(fn(rig))
    return out


JUDGED: set[str] = set()
