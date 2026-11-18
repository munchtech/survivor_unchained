"""(aim-move, 15 Nov) Prowl, the stance the owner picked on 10 Nov (P4 `idle_fight_a`, built on body B), as her drawn
idle on A (`idle_warden`, out of town).

The owner (15 Nov): "just the idle pose out of town is still so weak, we've mentioned it many times before .  that locked
elbow instead of relaxed casual badass that we've been wanting".

B's rest is A's rest remapped (same bone lengths; A spine_01/02/03 start where B spine_02/03/04 do, A neck_01 where B
neck_02 does), but the bones' own axes differ, so the body comes over as WORLD turns from rest: a bone's turn on A is
B's source bone's global turn times B's rest global inverse, times A's rest global. The legs are then re-solved onto
B's ankles (the rest knees and feet differ a little), the knees toward B's. The hands are keyed on A by keyed.solve_frames
(her grips and seats are A's): each wrist where B's is, the hand turned as B's is, read off its knuckles (the line to the
middle knuckle, the line from the little finger's to the index's) through A's own hand at rest; the sword's line is
Prowl's (44 deg below level, heading -120: trailing low behind her right hip), alive with her weight shift.

Build: reads the frozen source tools/anim/p4/frozen/idle_fight_a.json (WARDEN_PROWL_SRC=build: p4.py's fresh build), then
`WARDEN_IDLE=prowl` (the default) builds idle_warden from it; `WARDEN_IDLE=heavyset` is the old idle.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path

import numpy as np

from rig import Clip, qfrom_basis, qinv, qmul, qrot, qaxis, qbetween, two_bone_ik

REPO = Path(__file__).resolve().parents[3]
# The source, frozen in the repo (the Marionette rule, PIPELINE.md: p4.py's build runs Marionette's motion core from
# outside the repo, so its output could drift): the build Prowl was judged and approved on (15-16 Nov).
# WARDEN_PROWL_SRC=build reads p4.py's fresh build output instead (godot/art/people/body_p1/p4/, git-ignored).
B_CLIP = (REPO / "godot/art/people/body_p1/p4/idle_fight_a.json" if os.environ.get("WARDEN_PROWL_SRC") == "build"
          else REPO / "tools/anim/p4/frozen/idle_fight_a.json")
B_SKEL = REPO / "tools/body/rig/b_skeleton.json"
# A bone <- B bone (world turn from rest)
BODY = {"pelvis": "pelvis", "spine_01": "spine_02", "spine_02": "spine_03", "spine_03": "spine_05", "neck_01": "neck_02",
        "Head": "Head", "thigh_l": "thigh_l", "thigh_r": "thigh_r", "calf_l": "calf_l", "calf_r": "calf_r",
        "foot_l": "foot_l", "foot_r": "foot_r", "ball_l": "ball_l", "ball_r": "ball_r"}
# Prowl's sword line (char space) and its life: degrees of pitch with her weight shift, of yaw with her breath.
BLADE = (-0.623, -0.695, -0.359)
BLADE_PITCH = float(os.environ.get("PROWL_BLADE_PITCH", "2.0"))  # (solver 12, 16 Nov: 2, was 4: the pitch life swung the hanging
# line 66-74 below level; at 4 the tip came to 0.03 m off the floor at the steep end and the share from behind to 0.41+
# at the shallow end, no line between them; at 2 the line plays 64-70, tip 0.05+, share 0.41-)
BLADE_YAW = float(os.environ.get("PROWL_BLADE_YAW", "1.5"))  # (solver 6a: 1.5, was 2.5: the heading swung 19 deg p-p, over the 20-wide band)
# The sword elbow's bend at least this (deg; B's Prowl held 16-27, which reads straight at the play camera). 0 = B's.
ELBOW_R = float(os.environ.get("PROWL_ELBOW_R", "38"))
FORE_R = float(os.environ.get("PROWL_FORE_R", "0"))  # deg the sword forearm tips forward about B's elbow (replaces ELBOW_R)
# (m) each hand moved out from her side (motion --outfits: at 0 the sword hand met her hip 6 mm, the warden plate 24/19;
# at r 0.025 / l 0.02: skin 0, warden plate 2 r / 9 l, reaver 3 l)
HAND_OUT = {"r": float(os.environ.get("PROWL_OUT_R", "0.04")), "l": float(os.environ.get("PROWL_OUT_L", "0.02"))}
# (aim-move solver 2, 15 Nov; PROWL_TRAIL=1, off by default until the walk and run carry match it) the sword arm keyed
# by its joints (gait.arm_joints: th fwd of hanging, out, the elbow's inside angle, turn in; chest frame) and the fist by
# its grip frame (blade, knuckles; chest frame), found INSIDE armroll's caps (solve2 reach.py: forearm turned out 77,
# wrist extended 36 (W_EXT 45), 15 ulnar (W_DEV_LOW 20)), so the pack turns nothing back. Prowl's keyed line (BLADE)
# needed a forearm roll past 95 and the pack's 80 turned it out to the wing (as played -100..-85 heading, 26-35 below
# level, tip 1.04-1.16 m out); this one plays -109 / 53, tip 0.72 m out, 0.27 m behind her hips, 0.14 m off the floor.
TRAIL = os.environ.get("PROWL_TRAIL", "1") == "1"
# (solver 3a, 15 Nov: on by default; PROWL_TRAIL=0 is the old keyed line) the elbow's inside angle 147 (bend 30-36 with
# her weight shift), the grip re-keyed to 11 ulnar (was 19-25, past W_DEV_LOW), and the arm and fist ride TRAIL_FOLLOW
# of the chest's turn from its mean: the whole chest's turn swung the line -130..-97 and the tip 0.63-0.83 m out.
TRAIL_ARM = (-10.0, 14.0, float(os.environ.get("PROWL_TRAIL_EL", "141")), 22.0)  # (solver 4a: out 14, turned in 22; was out 0: the fist 58 mm into her hip; solver 6a: inside angle 141, was 147: bend 25-32 as played)
# (solver 6a, 15 Nov) ONE hold for every carry: the idle, its break, the walk and the stops carry the run's grip tilt
# (GRIP_TILT, the clips' meta "grip_tilt"; keyed.grip_of: the blade's lean in the fist 35 - tilt, - toward her fingers),
# so locomotion never turns the blade in her fist; the skills stay at 0 and land on the idle's HAND (end_keys' tilt).
# TRAIL_GRIP re-keyed for it: the wrist read in armroll's caps (pro 75, flex -40, dev 6 on f0; solve6a grip6.py), the
# line -121 / 50 below level. At tilt 0 the same line pinned pronation and the ulnar cap (armroll turned 9.9 back).
GRIP_TILT = float(os.environ.get("PROWL_GRIP_TILT", "-35"))
TRAIL_GRIP = ((-0.5866, -0.8081, -0.0249), (0.7772, -0.5541, -0.2939)) if GRIP_TILT == -35.0 else \
    ((-0.6261, -0.7783, 0.0147), (0.7324, -0.5943, -0.3285))  # (solver 4a's, at tilt 0: knuckles rolled -16 about the blade)
TRAIL_FOLLOW = float(os.environ.get("PROWL_TRAIL_FOLLOW", "0.35"))
# (solver 8a, 15 Nov) the IDLE's own sword arm and grip (the walk keeps TRAIL_ARM, and TRAIL_GRIP when PROWL_WRIST is
# None). From behind, the commonest view, TRAIL_ARM's line (-129..-110 heading, 50-55 below level as played) laid 0.56-0.60
# of the blade out to her right, a level bar. The upper arm 30 back of hanging, out 12, inside angle 145, turned in 30,
# and the fist at armroll's reading pro 66, flex -17 (extension), dev -3 (solve8a reach8.py / cand8.py: in the caps with
# 5+ to spare, so the pack turns nothing back): as played -147..-131 / 62-68 below level, sideways share
# -sin(heading)cos(down) 0.27-0.35, the tip 0.09-0.12 m off the floor by her right foot, the fist 0.18-0.20 m out of her
# pelvis, bend 33-38, 19.9 cm off her leg.
# (solver 11a, 16 Nov) At the PLAY camera (pitch 56, she faces it) that line, trailing back, threw its point up-screen
# and cancelled its fall: the idle read as a short level stub at her side, and the elbow near straight (33-38) read
# locked. Now the upper arm 30 back, out 20, inside angle 125 (bend 54-59 as played, soft), turned in 50, the fist at
# armroll's reading pro 64, flex -30, dev -5 (7 inside the caps; solve11/tools/reach11.py over frames 0/52/76/104/156,
# solve11a/tools/cand11.py's grip): as played -129..-107 / 70-77 below level, 54+ deg down-screen from the front and
# within 45 of it, sideways share from behind 0.32 max, the tip 0.06 m off the floor, the fist 50 mm clear of her hip
# (out 14: 24 mm into it at f76). Was (-30, 12, 145, 30) / ((-0.3448, -0.9363, -0.0475), (0.7678, -0.2518, -0.5876)).
# (solver 12, 16 Nov) From the DEFAULT facing (toward the den camera, pitch 62) that arm, trailing back, put the fist on
# screen only 0.05 m under her right shoulder and the elbow above it: a fist raised by her head, the blade hidden (the
# owner, 15 Nov: "the idle pose out of town is still so weak ... that locked elbow"). Now the arm hangs at her side
# (the lead's try e): 5 back of hanging, out 30, inside angle 130 (bend 41-48 as played), turned in 45; the fist at
# her hip, 0.18-0.20 m under her shoulder on screen facing the camera and from behind. The grip read off e's PLAYED
# wrist (e's keyed grip sat 10 past the ulnar cap; armroll turned it 9.7 back, so the stops and skill ends landed off
# the played hand) and turned 8 forward about her up, 5 up and 3 about the blade (s12/tools/g12.py, t2.py): in the
# caps (dev -17, pro 60, flex -34; armroll turns nothing), as played 68-85 to her right, 64-70 below level.
# Was (-30, 20, 125, 50) / ((-0.2718, -0.953, 0.1261), (0.4317, -0.2367, -0.8694)).
IDLE_ARM = (-5.0, 30.0, 130.0, 45.0)
IDLE_GRIP = ((-0.3471, -0.8573, 0.3802), (0.2497, -0.4752, -0.8437)) if GRIP_TILT == -35.0 else TRAIL_GRIP
if os.environ.get("PROWL_IDLE_ARM", "1") == "0":  # the old idle line (TRAIL_ARM / TRAIL_GRIP)
    IDLE_ARM, IDLE_GRIP = TRAIL_ARM, TRAIL_GRIP


def grip_at(blade, knuckles, tilt, frm=None):
    """(solver 6a) The grip (blade, knuckles) that puts the SAME hand bone where (blade, knuckles) does at the idle's
    tilt `frm` (GRIP_TILT if None) in a clip solved at `tilt` (keyed: hand = grip * turn(+X, 35 - tilt)), so only the
    blade turns in her fist as the game eases the tilt across the fade."""
    frm = GRIP_TILT if frm is None else frm
    if abs(tilt - frm) < 1e-6:
        return tuple(blade), tuple(knuckles)
    z = _norm(blade)
    y = np.asarray(knuckles, float)
    y = _norm(y - z * np.dot(y, z))
    G = qmul(qfrom_basis(np.cross(y, z), y, z), qaxis([1.0, 0.0, 0.0], tilt - frm))
    return tuple(float(x) for x in qrot(G, [0.0, 0.0, 1.0])), tuple(float(x) for x in qrot(G, [0.0, 1.0, 0.0]))


def _norm(v):
    v = np.asarray(v, float)
    return v / max(np.linalg.norm(v), 1e-9)


def _trail_frame(sk, ag, gT):
    """Per frame, the turn the trail arm and fist ride: TRAIL_FOLLOW of the chest's turn from its mean (a relaxed arm
    hangs; it does not lean and turn with the chest whole)."""
    from rig import qslerp
    c = sk.i("spine_03")
    C = np.array([qmul(gT[t, c], qinv(ag[c])) for t in range(len(gT))])
    C = C * np.where(C @ C[0] < 0, -1.0, 1.0)[:, None]
    m = _norm(C.mean(0))
    return np.array([qslerp(m, q, TRAIL_FOLLOW) for q in C])


def _trail_spec(sk, ag, g, p, sw, ph, C=None):
    """PROWL_TRAIL's hand_r key on one frame's body (globals g, p): the wrist where IDLE_ARM's joints put it from the
    shoulder (the elbow 3 deg softer or firmer with her weight shift), the elbow's way as the pole, the fist's grip frame
    turned whole with the arm's frame C (_trail_frame; the chest's own turn if None) and by the blade's life
    (BLADE_PITCH with the weight shift, BLADE_YAW with the breath)."""
    from gait import arm_joints
    u, lo, h, c = (sk.i(n) for n in ("upperarm_r", "lowerarm_r", "hand_r", "spine_03"))
    ap = sk.rest_globals()[1][0]
    l1, l2 = float(np.linalg.norm(ap[lo] - ap[u])), float(np.linalg.norm(ap[h] - ap[lo]))
    C = qmul(g[c], qinv(ag[c])) if C is None else C
    th, out, el, turn = IDLE_ARM
    E, H = arm_joints(th, out, el + 3.0 * sw, turn, l1, l2)
    E, H = qrot(C, E * np.array([-1.0, 1, 1])), qrot(C, H * np.array([-1.0, 1, 1]))
    bc, kc = qrot(C, np.array(IDLE_GRIP[0])), qrot(C, np.array(IDLE_GRIP[1]))
    q = qmul(qaxis([0.0, 1.0, 0.0], BLADE_YAW * math.sin(2 * ph * 2)), qaxis(_norm(np.cross([0.0, 1.0, 0.0], bc)), BLADE_PITCH * sw))
    wrist = p[u] + H + np.array([-HAND_OUT["r"], 0.0, 0.0])
    return {"pos": tuple(wrist), "pole": tuple(_norm(E)), "pole_at": "shoulder", "frame": "char",
            "blade": tuple(qrot(q, bc)), "knuckles": tuple(qrot(q, kc))}


def b_globals():
    """B's built Prowl as globals: (names, index, rot [T, J, 4], pos [T, J, 3], rest globals [J, 4])."""
    clip = json.loads(B_CLIP.read_text())
    sk = json.loads(B_SKEL.read_text())["bones"]
    names = [b["name"] for b in sk]
    idx = {n: i for i, n in enumerate(names)}
    par = [idx[b["parent"]] if b["parent"] else -1 for b in sk]
    head = np.array([b["head"] for b in sk], float)
    RG = np.array([qfrom_basis(*[np.array(a, float) for a in b["axes"]]) for b in sk])
    T = int(clip["frames"])
    J = len(names)
    lr = np.array([RG[j] if par[j] < 0 else qmul(qinv(RG[par[j]]), RG[j]) for j in range(J)])
    lp = np.array([head[j] if par[j] < 0 else qrot(qinv(RG[par[j]]), head[j] - head[par[j]]) for j in range(J)])
    rot = np.broadcast_to(lr, (T, J, 4)).copy()
    pos = np.broadcast_to(lp, (T, J, 3)).copy()
    for b, qs in clip["rot"].items():
        rot[:, idx[b]] = np.array(qs, float)
    for b, ps in clip["pos"].items():
        pos[:, idx[b]] = np.array(ps, float)
    g = np.empty_like(rot)
    p = np.empty_like(pos)
    for j in range(J):
        if par[j] < 0:
            g[:, j], p[:, j] = rot[:, j], pos[:, j]
        else:
            g[:, j] = qmul(g[:, par[j]], rot[:, j])
            p[:, j] = p[:, par[j]] + qrot(g[:, par[j]], pos[:, j])
    return names, idx, g, p, RG, float(clip["fps"]), bool(clip["loop"])


def _hand_basis(p, hand, mid, idx_k, pinky_k):
    """A hand's frame from its knuckles: y along the line to the middle knuckle, z from the little finger's knuckle to
    the index's (made square to y)."""
    y = _norm(p[mid] - p[hand])
    z = p[idx_k] - p[pinky_k]
    z = _norm(z - y * np.dot(z, y))
    return qfrom_basis(np.cross(y, z), y, z)


def body(rig):
    """A's frames with Prowl's body (pelvis, spine, neck, head, legs) and every other bone at A's rest; and the B globals
    the hands are keyed from."""
    sk = rig.sk
    names, bi, gB, pB, RG, fps, loop = b_globals()
    T = gB.shape[0]
    J = len(sk)
    ag, ap = sk.rest_globals()
    ag, ap = ag[0], ap[0]
    order = list(range(J))  # parents come first in her skeleton
    rot = np.broadcast_to(sk.rest_rot, (T, J, 4)).copy()
    pos = np.broadcast_to(sk.rest_pos, (T, J, 3)).copy()
    # wanted globals for the mapped bones
    want = {a: qmul(qmul(gB[:, bi[b]], qinv(RG[bi[b]])), ag[sk.i(a)]) for a, b in BODY.items()}
    # The feet flat on her ground: B's rest foot is not A's, so B's foot turn carried over pitched A's toes up 9 degrees
    # and rolled them 8 (the ball 3 cm off the floor). Each foot keeps B's heading only, its toes at rest under it.
    flat = {}
    for s in "lr":
        f = sk.i(f"foot_{s}")
        fw = qrot(qmul(gB[:, bi[f"foot_{s}"]], qinv(RG[bi[f"foot_{s}"]])), np.array([0.0, 0.0, 1.0]))
        yaw = np.degrees(np.arctan2(fw[..., 0], fw[..., 2]))
        flat[s] = np.array([qmul(qaxis([0.0, 1.0, 0.0], float(y)), ag[f]) for y in yaw])
        want[f"foot_{s}"] = flat[s]
        b = sk.i(f"ball_{s}")
        want[f"ball_{s}"] = np.array([qmul(q, sk.rest_rot[b]) for q in flat[s]])
    root, pel = sk.i("root"), sk.i("pelvis")
    for t in range(T):
        g = np.empty((J, 4))
        gp = np.empty((J, 3))
        for j in order:
            n = sk.names[j]
            pj = sk.parent[j]
            if n in want:
                rot[t, j] = want[n][t] if pj < 0 else qmul(qinv(g[pj]), want[n][t])
            if n == "pelvis":
                pos[t, j] = qrot(qinv(g[root]), pB[t, bi["pelvis"]] - gp[root])
            g[j] = rot[t, j] if pj < 0 else qmul(g[pj], rot[t, j])
            gp[j] = pos[t, j] if pj < 0 else gp[pj] + qrot(g[pj], pos[t, j])
        # the legs onto B's ankles, knees toward B's
        for s in "lr":
            th, ca, fo = sk.i(f"thigh_{s}"), sk.i(f"calf_{s}"), sk.i(f"foot_{s}")
            a, b_, c_ = gp[th], gp[ca], gp[fo]
            tgt = pB[t, bi[f"foot_{s}"]].copy()
            tgt[1] = ap[fo, 1]  # (the ankle at its rest height: the sole on the floor)
            nb, nc = two_bone_ik(a, b_, c_, tgt, pB[t, bi[f"calf_{s}"]] + (pB[t, bi[f"calf_{s}"]] - (pB[t, bi[f"thigh_{s}"]] + tgt) / 2))
            r1 = qbetween(b_ - a, nb - a)
            gth = qmul(r1, g[th])
            c2 = nb + qrot(r1, c_ - b_)
            gca = qmul(qbetween(c2 - nb, nc - nb), qmul(r1, g[ca]))
            rot[t, th] = qmul(qinv(g[sk.parent[th]]), gth)
            rot[t, ca] = qmul(qinv(gth), gca)
            rot[t, fo] = qmul(qinv(gca), want[f"foot_{s}"][t])
            # (ball: its own wanted turn under the solved foot)
            rot[t, sk.i(f"ball_{s}")] = qmul(qinv(want[f"foot_{s}"][t]), want[f"ball_{s}"][t])
    return rot, pos, (names, bi, gB, pB), fps, loop


def specs(rig, fingers_l=None):
    """Prowl on A before the hands are solved: the body's frames and each frame's hand keys (her space)."""
    sk = rig.sk
    rot, pos, (bn, bi, gB, pB), fps, loop = body(rig)
    T = rot.shape[0]
    ag, ap = sk.rest_globals()
    ag, ap = ag[0], ap[0]
    # A's hand at rest against its knuckles' frame (the calibration that reads B's knuckles as A's hand turn)
    off = {}
    for s in "lr":
        L = _hand_basis(ap, sk.i(f"hand_{s}"), sk.i(f"middle_01_{s}"), sk.i(f"index_01_{s}"), sk.i(f"pinky_01_{s}"))
        off[s] = qmul(qinv(L), ag[sk.i(f"hand_{s}")])
    pel = pB[:, bi["pelvis"]]
    sway = pel[:, 0] - pel[:, 0].mean()
    sway = sway / max(np.abs(sway).max(), 1e-6)
    bl0 = _norm(BLADE)
    side = _norm(np.cross([0.0, 1.0, 0.0], bl0))
    poses = []
    gT, pT = sk.fk(rot, pos) if TRAIL else (None, None)
    KT = _trail_frame(sk, ag, gT) if TRAIL else None
    for t in range(T):
        hands = {}
        for s in "lr":
            L = _hand_basis(pB[t], bi[f"hand_{s}"], bi[f"middle_01_{s}"], bi[f"index_01_{s}"], bi[f"pinky_01_{s}"])
            H = qmul(L, off[s])
            wrist = pB[t, bi[f"hand_{s}"]]
            elbow = pB[t, bi[f"lowerarm_{s}"]]
            sh = pB[t, bi[f"upperarm_{s}"]]
            pole = _norm(elbow - (sh + wrist) / 2)
            if s == "r" and FORE_R > 0:
                # the sword forearm tipped FORE_R deg forward about the elbow (a hanging forearm leaves the blade, square
                # off the fist, level: the tip out at her right at hip height, a bar; tipped forward, the trail can fall)
                l2 = np.linalg.norm(ap[sk.i("hand_r")] - ap[sk.i("lowerarm_r")])
                tip = qaxis([1.0, 0.0, 0.0], -FORE_R)
                wrist = elbow + qrot(tip, _norm(wrist - elbow)) * l2
                H = qmul(tip, H)
            elif s == "r" and ELBOW_R > 0:
                # the sword elbow soft (the owner: "that locked elbow"): the wrist drawn in along the shoulder's line
                # until the elbow bends ELBOW_R
                l1 = np.linalg.norm(ap[sk.i("lowerarm_r")] - ap[sk.i("upperarm_r")])
                l2 = np.linalg.norm(ap[sk.i("hand_r")] - ap[sk.i("lowerarm_r")])
                d = math.sqrt(l1 * l1 + l2 * l2 + 2 * l1 * l2 * math.cos(math.radians(ELBOW_R + 3.0 * float(sway[t]))))
                wrist = sh + _norm(wrist - sh) * min(d, np.linalg.norm(wrist - sh))
            # each hand a little out from her side, clear of her hip and the plate (her right is -X)
            wrist = wrist + np.array([HAND_OUT[s] * (-1.0 if s == "r" else 1.0), 0.0, 0.0])
            spec = {"pos": tuple(wrist), "knuckles": tuple(qrot(H, [0, 1.0, 0])), "blade": tuple(qrot(H, [0, 0, 1.0])),
                    "pole": tuple(pole), "frame": "char"}
            if s == "r":
                ph = 2 * math.pi * t / T
                b = qrot(qaxis(side, BLADE_PITCH * float(sway[t])), bl0)
                b = qrot(qaxis([0.0, 1.0, 0.0], BLADE_YAW * math.sin(2 * ph * 2)), b)
                spec["blade"] = tuple(b)
            if s == "r" and TRAIL:
                spec = _trail_spec(sk, ag, gT[t], pT[t], float(sway[t]), 2 * math.pi * t / T, KT[t])
            hands[f"hand_{s}"] = spec
        pose = dict(hands)
        pose["fingers_r"] = "grip"
        pose["fingers_l"] = fingers_l or {"curl": 0.95, "cascade": 0.05, "thumb": 1.6, "oppose": 0.9}
        poses.append(pose)
    return rot, pos, poses, fps, loop


def build(rig, name="idle_warden", arms_l=None, fingers_l=None):
    from keyed import solve_frames
    rot, pos, poses, fps, loop = specs(rig, fingers_l)
    T = rot.shape[0]
    r2, p2 = solve_frames(rig, poses, [(rot[t], pos[t]) for t in range(T)], loop=loop, weapon="sword+shield", tilt=GRIP_TILT)
    meta = {"weapon": "sword+shield", "made_by": "Prowl (P4 idle_fight_a on B, Kimodo take + Marionette fit) carried onto A",
            "changes": "B's body as world turns from rest, legs re-solved onto B's ankles, hands keyed on A",
            **({"grip_tilt": GRIP_TILT} if GRIP_TILT else {})}
    return Clip(name, fps, r2, p2, loop=loop, meta=meta)


# The break (every 10-16 s standing, PlayerView): over Prowl's own first BREAK_F frames she rolls her wrist and the
# blade's point draws one slow circle about its trailing line (BREAK_CONE degrees out at most, the fist lifting
# BREAK_LIFT), then falls back to the trail. (Replaces soul.warden_break, which rested the flat on her shoulder from the
# old square stand: from Prowl the game's blend into it snapped her feet and hips.)
BREAK_F = 96
# (solver 4a) the circle drawn ABOVE the trailing line (it starts and ends on it, rising BREAK_CONE at its top), the
# blade and knuckles turned together about the fist's grip (the fist stays where Prowl holds it, clear of her hip): at
# 34 deg about the line the point dipped onto her right thigh (-0.1 cm) and the wrist went past armroll's caps.
# (solver 6a, at grip tilt -35: cone 20 took the wrist to the ulnar cap (armroll turned 21.5 back), the bend to 53, the
# tip 0.94 m out)
BREAK_CONE = float(os.environ.get("PROWL_BREAK_CONE", "12"))
# (solver 11a) the circle's rise (deg, at its top) and its sweep across (deg, side to side) apart; both BREAK_CONE: the
# round circle as before
BREAK_RISE = float(os.environ.get("PROWL_BREAK_RISE", "0"))  # (solver 11a: 0, 12 sweep; the rise took the wrist past its caps)
BREAK_SWEEP = float(os.environ.get("PROWL_BREAK_SWEEP", "12"))
BREAK_LIFT = float(os.environ.get("PROWL_BREAK_LIFT", "0.01"))
# (solver 11c, 16 Nov) the break's own wrist caps (armroll W_PRO: meta "wrist_caps", widen only; pack and every check
# re-solve it alike): extension 48 (armroll's 45; life's 60-70). Solved open (not as the idle's loop), the break's wrist
# passed 45 by under 2 deg and armroll turned the hand 1.4 back, at any sweep (10: 1.35, 12: 1.39); at 47 or 48 it turns
# nothing and the flourish plays as keyed. "null": armroll's own caps.
BREAK_CAPS = json.loads(os.environ.get("PROWL_BREAK_CAPS") or '{"ext": 48}')
BREAK_GRIP = 0.045  # m, the wrist to the fist's grip point along the knuckles


def build_break(rig, name="idle_warden_break", fingers_l=None):
    from keyed import solve_frames
    rot, pos, poses, fps, loop = specs(rig, fingers_l)
    n = BREAK_F
    a0, a1 = 14, 74  # the circle's frames
    out = []
    for t in range(n + 1):
        pose = {k: (dict(v) if isinstance(v, dict) else v) for k, v in poses[t].items()}
        u = min(1.0, max(0.0, (t - a0) / (a1 - a0)))
        env = math.sin(math.pi * u) ** 2
        if env > 0:
            h = pose["hand_r"]
            b0, k0 = _norm(h["blade"]), _norm(h["knuckles"])
            e1 = _norm(np.cross(b0, [0.0, 1.0, 0.0]))  # (level, square to the blade)
            e2 = _norm(np.cross(e1, b0))  # (up, square to the blade)
            th = 2 * math.pi * u
            # the point's way off the line: a circle through the line, above it (the point first rises and comes
            # forward, sweeps over and back, and comes down onto the line again), BREAK_CONE across
            w = e2 * (1.0 - math.cos(th)) * 0.5 * BREAK_RISE - e1 * math.sin(th) * 0.5 * BREAK_SWEEP
            c = min(1.0, 2.0 * env) * float(np.linalg.norm(w))
            if c > 1e-6:
                q = qaxis(_norm(np.cross(b0, _norm(w))), c)
                grip = np.array(h["pos"]) + BREAK_GRIP * k0
                h["blade"], h["knuckles"] = tuple(qrot(q, b0)), tuple(qrot(q, k0))
                h["pos"] = tuple(grip + qrot(q, np.array(h["pos"]) - grip) + np.array([0.0, BREAK_LIFT * env, 0.0]))
        out.append(pose)
    r2, p2 = solve_frames(rig, out, [(rot[t], pos[t]) for t in range(n + 1)], loop=False, weapon="sword+shield", tilt=GRIP_TILT)
    meta = {"layer": "full", "weapon": "sword+shield", "made_by": "Prowl's first frames, the blade's point circled (prowl.build_break)",
            **({"grip_tilt": GRIP_TILT} if GRIP_TILT else {}), **({"wrist_caps": BREAK_CAPS} if BREAK_CAPS else {})}
    return Clip(name, fps, r2, p2, loop=False, meta=meta)


def _eul(q):
    """keyed's qeuler(yaw, pitch, roll) read back off a turn (roll, then pitch, then yaw)."""
    from scipy.spatial.transform import Rotation
    y, x, z = Rotation.from_quat(np.asarray(q, float)).as_euler("YXZ", degrees=True)
    return (float(y), float(x), float(z))


def end_keys(rig, fingers_l=None, t=0, tilt=None):
    """Prowl's frame t as keyed controls (no base), for clips that land in her stance or leave it (the stops): each
    foot's ankle and heading, the hips' place and turn, the spine, neck and head as the turns between them, and the
    hands as chest-frame arcs from the shoulder (so they ride the chest as a stop's lean throws it). `tilt` (solver 6a):
    the grip tilt of the clip the keys go into (None: the idle's, GRIP_TILT): the sword hand's grip re-keyed (grip_at)
    so that clip's solve lands the idle's hand bone, the blade then off the idle's by the tilts' difference."""
    sk = rig.sk
    rot, pos, poses, fps, loop = specs(rig, fingers_l)
    g, p = sk.fk(rot[t:t + 1], pos[t:t + 1])
    g, p = g[0], p[0]
    ag, ap = sk.rest_globals()
    ag, ap = ag[0], ap[0]
    d = {n: qmul(g[sk.i(n)], qinv(ag[sk.i(n)])) for n in ("pelvis", "spine_03", "neck_01", "Head", "foot_l", "foot_r")}
    out = {"hips": {"pos": tuple(float(x) for x in p[sk.i("pelvis")] - ap[sk.i("pelvis")]), "rot": _eul(d["pelvis"])},
           "spine": _eul(qmul(qinv(d["pelvis"]), d["spine_03"])),
           "neck": _eul(qmul(qinv(d["spine_03"]), d["neck_01"])),
           "head": _eul(qmul(qinv(d["neck_01"]), d["Head"]))}
    for s in "lr":
        f = sk.i(f"foot_{s}")
        knee = p[sk.i(f"calf_{s}")] - (p[sk.i(f"thigh_{s}")] + p[f]) / 2
        out[f"foot_{s}"] = {"pos": (float(p[f, 0]), float(p[f, 1] - ap[f, 1]), float(p[f, 2])), "rot": _eul(d[f"foot_{s}"]),
                            "pole": tuple(float(x) for x in _norm(knee))}
    ch = qinv(d["spine_03"])
    for s in "lr":
        h = dict(poses[t][f"hand_{s}"])
        v = qrot(ch, np.array(h.pop("pos")) - p[sk.i(f"upperarm_{s}")])
        r = float(np.linalg.norm(v))
        h["arc"] = (math.degrees(math.atan2(v[0], v[2])), math.degrees(math.asin(v[1] / r)), r)
        for k in ("blade", "knuckles", "pole"):
            h[k] = tuple(float(x) for x in qrot(ch, np.array(h[k])))
        h["frame"] = "chest"
        if s == "r" and tilt is not None:
            h["blade"], h["knuckles"] = grip_at(h["blade"], h["knuckles"], tilt)
        out[f"hand_{s}"] = h
    out["fingers_r"], out["fingers_l"] = poses[t]["fingers_r"], poses[t]["fingers_l"]
    return out


_F0 = {}


def frame0(rig, fingers_l=None):
    """Prowl's frame 0 solved on A (local rot [J,4], pos [J,3]), as idle_warden's first frame."""
    if id(rig) not in _F0:
        from keyed import solve_frames
        rot, pos, poses, fps, loop = specs(rig, fingers_l)
        # (solver 6a) the whole loop solved as build() solves it, at the idle's tilt: a two-frame solve's hand_r was 5.4
        # deg off the built idle's f0 (the loop's elbow smoothing), and the leap settled onto that
        r2, p2 = solve_frames(rig, poses, [(rot[t], pos[t]) for t in range(len(poses))], loop=loop, weapon="sword+shield",
                              tilt=GRIP_TILT)
        _F0[id(rig)] = (r2[0].copy(), p2[0].copy())
    return _F0[id(rig)]


def settle(rig, clip, n=18, rise=0.05, fingers_l=None):
    """(aim-move, the owner 15 Nov: every skill lands on Prowl) `clip` with n frames laid after its last: from where
    it ends she comes up into Prowl's frame 0 (every bone's turn eased across, smoothstep), her feet stepped, not slid:
    each foot carried from its place to Prowl's on an arc `rise` high, the one further off first (its half of the
    settle), the other after, each planted the rest of the time; the legs re-solved onto them (knees their own way).
    For a clip with no keys of its own to land in (a mocap take: the leap)."""
    from rig import qslerp, Clip as C
    sk = rig.sk
    r0, p0 = clip.rot[-1], clip.pos[-1]
    r1, p1 = frame0(rig, fingers_l)
    g0, q0 = sk.fk(r0[None], p0[None]); g1, q1 = sk.fk(r1[None], p1[None])
    g0, q0, g1, q1 = g0[0], q0[0], g1[0], q1[0]
    J = len(sk)
    order = list(range(J))
    far = {s: float(np.linalg.norm((q1 - q0)[sk.i(f"foot_{s}"), [0, 2]])) for s in "lr"}
    first = max(far, key=far.get)
    span = {first: (0.0, 0.55), ("l" if first == "r" else "r"): (0.45, 1.0)}
    rots, poss = [], []
    for t in range(1, n + 1):
        u = t / n
        w = u * u * (3 - 2 * u)
        rot = np.array([qslerp(r0[j], r1[j], w) for j in range(J)])
        pos = p0 + (p1 - p0) * w
        g = np.empty((J, 4)); gp = np.empty((J, 3))
        for j in order:
            pj = sk.parent[j]
            g[j] = rot[j] if pj < 0 else qmul(g[pj], rot[j])
            gp[j] = pos[j] if pj < 0 else gp[pj] + qrot(g[pj], pos[j])
        for s in "lr":
            th, ca, fo = sk.i(f"thigh_{s}"), sk.i(f"calf_{s}"), sk.i(f"foot_{s}")
            a0, a1 = span[s]
            v = min(1.0, max(0.0, (u - a0) / (a1 - a0)))
            v = v * v * (3 - 2 * v)
            tgt = q0[fo] + (q1[fo] - q0[fo]) * v
            tgt[1] += rise * math.sin(math.pi * v) * (1.0 if far[s] > 0.03 else 0.0)
            gfo = qslerp(g0[fo], g1[fo], v)
            a, b_, c_ = gp[th], gp[ca], gp[fo]
            knee = b_ + (b_ - (a + c_) / 2)
            nb, nc = two_bone_ik(a, b_, c_, tgt, knee)
            r1q = qbetween(b_ - a, nb - a)
            gth = qmul(r1q, g[th])
            c2 = nb + qrot(r1q, c_ - b_)
            gca = qmul(qbetween(c2 - nb, nc - nb), qmul(r1q, g[ca]))
            rot[th] = qmul(qinv(g[sk.parent[th]]), gth)
            rot[ca] = qmul(qinv(gth), gca)
            rot[fo] = qmul(qinv(gca), gfo)
        rots.append(rot); poss.append(pos)
    meta = dict(clip.meta)
    meta["changes"] = (meta.get("changes", "") + f", settled into Prowl over {n} frames (prowl.settle)").lstrip(", ")
    return C(clip.name, clip.fps, np.concatenate([clip.rot, np.array(rots)]), np.concatenate([clip.pos, np.array(poss)]),
             loop=False, meta=meta)
