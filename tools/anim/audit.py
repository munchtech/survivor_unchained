"""Wrists and forearms checked in every clip we make: no flips, nothing past
what an arm can do.

    python tools/anim/audit.py [names...] [--all]   (her, the hero, the folk)

For each side, frame by frame, it measures:
- the forearm's turn on the upper arm, split into the elbow's bend and the
  forearm's own twist (pronation, about its length), and any sideways bend
  an elbow can't make;
- the hand's turn on the forearm, split into the wrist's bend and a twist
  about the hand's length (the wrist has none of its own: a twist there
  is a forearm twist put in the wrong bone); the bend split again as a
  wrist bends, toward the palm or the back (flexion, extension: far) and
  toward the thumb or the little finger (radial, ulnar: a little), on the
  wrist's own axes, which turn with the forearm as it rolls;
- how far the hand turns in her space from one frame to the next (a flip
  shows as a turn of tens of degrees in a frame that the arm can't make).

Flags (degrees): a hand or forearm spinning about its own length more than
FLIP in one frame (30 fps), or any hand turning more than 120; a
wrist twist past WRIST_TWIST; a wrist bend past WRIST_BEND, or past what a
wrist can do (FLEX, EXT, RADIAL, ULNAR: some degrees past the solver's own
limits, keyed.Rig, as the solver reads the bend about the forearm's line
and this about the hand's, up to 13 degrees apart on the hero); a forearm
twist past FORE_TWIST from rest; an elbow
bent sideways past ELBOW_SIDE. Reports the worst frames of each clip.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rig import DATA, Skeleton, qinv, qmul, qrot  # noqa: E402

HERE = Path(__file__).resolve().parent
FLIP = 30.0
WRIST_TWIST = 50.0
WRIST_BEND = 95.0
FORE_TWIST = 120.0
ELBOW_SIDE = 25.0
FLEX, EXT, RADIAL, ULNAR = 85.0, 75.0, 30.0, 45.0

SETS = [("her", HERE / "out" / "clips", "heroine_skeleton.json"),
        ("hero", HERE / "out" / "hero", "hero_skeleton.json"),
        ("folk_f", HERE / "out" / "folk", "folk_female_skeleton.json"),
        ("folk_m", HERE / "out" / "folk", "folk_male_skeleton.json")]


def swing_twist(q, axis):
    """q split into a twist about axis and the swing after it: (swing deg,
    twist deg signed)."""
    v = q[:3]
    p = axis * np.dot(v, axis)
    t = np.array([p[0], p[1], p[2], q[3]])
    n = np.linalg.norm(t)
    t = t / n if n > 1e-9 else np.array([0, 0, 0, 1.0])
    if t[3] < 0:
        t = -t
    tw = math.degrees(2 * math.atan2(np.dot(t[:3], axis), t[3]))
    s = qmul(q, qinv(t))
    sw = math.degrees(2 * math.acos(min(1.0, abs(s[3]))))
    return sw, tw


def wrist_bend(dh, y, side):
    """A hand's local turn from rest (dh) as the wrist's flexion (+ toward the
    palm) and deviation (+ toward the thumb), degrees: the twist about the
    hand's length (y) taken off first, so the bend is read on the axes the
    forearm's roll leaves (dh = twist * bend)."""
    t = np.array([*(y * np.dot(dh[:3], y)), dh[3]])
    n = np.linalg.norm(t)
    t = t / n if n > 1e-9 else np.array([0, 0, 0, 1.0])
    s = qmul(qinv(t), dh)
    if s[3] < 0:
        s = -s
    a = 2 * math.acos(min(1.0, s[3]))
    if a < 1e-6 or np.linalg.norm(s[:3]) < 1e-9:
        return 0.0, 0.0
    ax = s[:3] / np.linalg.norm(s[:3])
    # The hand's +Z is its thumb side (keyed.Rig); +X = Y x Z is the back of
    # her right hand and the palm of her left.
    z = np.array([0, 0, 1.0]) - y * y[2]
    z = z / np.linalg.norm(z)
    x = np.cross(y, z)
    d = math.degrees(a)
    return d * float(np.dot(ax, z)) * (1 if side == "r" else -1), d * float(np.dot(ax, x))


def angle(a, b):
    d = abs(float(np.dot(a, b)))
    return math.degrees(2 * math.acos(min(1.0, d)))


def load(path, sk):
    d = json.loads(path.read_text())
    n = len(d["tracks"][0]["keys"])
    rot = np.tile(sk.rest_rot, (n, 1, 1)).astype(float)
    pos = np.tile(sk.rest_pos, (n, 1, 1)).astype(float)
    for t in d["tracks"]:
        j = sk.index[t["bone"]]
        k = np.array(t["keys"], float)
        if t["type"] == "rot":
            rot[:, j] = k
        else:
            pos[:, j] = k
    return d, rot, pos


def hinge_off(g, p, sk, f, top, mid, end, way, rest):
    """How far a bent elbow or knee bends off its hinge (degrees between the
    bend's axis and the hinge carried by the upper bone; 90 is straight
    sideways, 180 backwards), or 0 for a joint all but straight."""
    rest_g, rest_p = rest
    u0 = rest_p[0, mid] - rest_p[0, top]
    h0 = np.cross(u0 / np.linalg.norm(u0), way)
    h0 = h0 / np.linalg.norm(h0)
    h = qrot(qmul(g[f, top], qinv(rest_g[0, top])), h0)
    u, v = p[f, mid] - p[f, top], p[f, end] - p[f, mid]
    n = np.cross(u, v)
    s = np.linalg.norm(n) / (np.linalg.norm(u) * np.linalg.norm(v))
    if s < math.sin(math.radians(20)):
        return 0.0
    return math.degrees(math.acos(max(-1.0, min(1.0, np.dot(n / np.linalg.norm(n), h)))))


def audit(path, sk):
    d, rot, pos = load(path, sk)
    g, p = sk.fk(rot, pos)
    I = sk.index
    n = rot.shape[0]
    out = {}
    fwd = np.array([0.0, 0.0, 1.0])
    rest = sk.rest_globals()
    for s in "lr":
        knee = [hinge_off(g, p, sk, f, I[f"thigh_{s}"], I[f"calf_{s}"], I[f"foot_{s}"], -fwd, rest) for f in range(n)]
        elbow = [hinge_off(g, p, sk, f, I[f"upperarm_{s}"], I[f"lowerarm_{s}"], I[f"hand_{s}"], fwd, rest) for f in range(n)]
        out[f"knee_{s}"] = max(knee)
        out[f"elbow_{s}"] = max(elbow)
        out[f"knee_{s}_bad"] = [f for f, a in enumerate(knee) if a > ELBOW_SIDE]
        out[f"elbow_{s}_bad"] = [f for f, a in enumerate(elbow) if a > ELBOW_SIDE + 20]
    for s in "lr":
        fa, h = I[f"lowerarm_{s}"], I[f"hand_{s}"]
        mid = I.get(f"middle_01_{s}")
        fa_axis = sk.rest_pos[h] / np.linalg.norm(sk.rest_pos[h])
        h_axis = sk.rest_pos[mid] / np.linalg.norm(sk.rest_pos[mid]) if mid is not None else np.array([0, 1.0, 0])
        rows = []
        for f in range(n):
            dfa = qmul(qinv(sk.rest_rot[fa]), rot[f, fa])
            dh = qmul(qinv(sk.rest_rot[h]), rot[f, h])
            fa_sw, fa_tw = swing_twist(dfa, fa_axis)
            h_sw, h_tw = swing_twist(dh, h_axis)
            # The elbow's sideways bend: the swing's part off its main hinge
            # (the hinge taken as the axis the rest-to-now swing turns about
            # most across the clip is unknown, so use the swing about the
            # axis across the bone and the rest bend's plane: approximated as
            # how far the forearm leaves the plane of upper arm and rest forearm).
            # A frame's turn of the hand and of the forearm, and the part of
            # it that spins each about its own length (a flip shows as a spin:
            # the bone's direction barely changes, it rolls over).
            step = angle(g[f, h], g[f - 1, h]) if f else 0.0
            step_fa = angle(g[f, fa], g[f - 1, fa]) if f else 0.0
            roll_h = roll_fa = 0.0
            if f:
                ax = qrot(g[f, h], h_axis)
                roll_h = abs(swing_twist(qmul(g[f, h], qinv(g[f - 1, h])), ax / np.linalg.norm(ax))[1])
                ax = qrot(g[f, fa], fa_axis)
                roll_fa = abs(swing_twist(qmul(g[f, fa], qinv(g[f - 1, fa])), ax / np.linalg.norm(ax))[1])
            flex, dev = wrist_bend(dh, h_axis, s)
            rows.append((f, step, step_fa, fa_tw, h_sw, h_tw, roll_h, roll_fa, flex, dev))
        flags = []
        for f, step, step_fa, fa_tw, h_sw, h_tw, roll_h, roll_fa, flex, dev in rows:
            why = []
            if roll_h > FLIP:
                why.append(f"hand spins {roll_h:.0f} in a frame")
            if roll_fa > FLIP:
                why.append(f"forearm spins {roll_fa:.0f} in a frame")
            if step > 120:
                why.append(f"hand turns {step:.0f} in a frame")
            if abs(h_tw) > WRIST_TWIST:
                why.append(f"wrist twist {h_tw:+.0f}")
            if h_sw > WRIST_BEND:
                why.append(f"wrist bend {h_sw:.0f}")
            if dev > RADIAL or -dev > ULNAR:
                why.append(f"wrist bent {'to the thumb' if dev > 0 else 'to the little finger'} {abs(dev):.0f}")
            if flex > FLEX or -flex > EXT:
                why.append(f"wrist {'flexed' if flex > 0 else 'bent back'} {abs(flex):.0f}")
            if abs(fa_tw) > FORE_TWIST:
                why.append(f"forearm twist {fa_tw:+.0f}")
            if f in out[f"elbow_{s}_bad"]:
                why.append("elbow bent off its hinge")
            if f in out[f"knee_{s}_bad"]:
                why.append("knee bent off its hinge")
            if why:
                flags.append((f, "; ".join(why)))
        out[s] = {"max_step": max(r[6] for r in rows), "max_step_fa": max(r[7] for r in rows),
                  "max_wrist_twist": max(abs(r[5]) for r in rows), "max_wrist_bend": max(r[4] for r in rows),
                  "max_fore_twist": max(abs(r[3]) for r in rows), "max_dev": max(abs(r[9]) for r in rows),
                  "flags": flags}
    return d, out


def main(argv):
    want = [a for a in argv if not a.startswith("--")]
    verbose = "--all" in argv
    total = 0
    for label, folder, skel in SETS:
        if not folder.exists():
            continue
        sk = Skeleton.load(DATA / skel)
        files = sorted(folder.glob("*.json"))
        if label == "folk_f":
            files = [f for f in files if f.stem.startswith("f_")]
        if label == "folk_m":
            files = [f for f in files if f.stem.startswith("m_")]
        for f in files:
            if want and not any(w in f.stem for w in want):
                continue
            d, out = audit(f, sk)
            arms = {s: out[s] for s in "lr"}
            bad = {s: o for s, o in arms.items() if o["flags"]}
            if bad or verbose:
                total += sum(len(o["flags"]) for o in bad.values())
                parts = []
                for s, o in arms.items():
                    parts.append(f"{s}: spin {o['max_step']:.0f}/{o['max_step_fa']:.0f} wtw {o['max_wrist_twist']:.0f} "
                                 f"wbend {o['max_wrist_bend']:.0f} wdev {o['max_dev']:.0f} ftw {o['max_fore_twist']:.0f} elbow {out['elbow_' + s]:.0f} "
                                 f"knee {out['knee_' + s]:.0f} ({len(o['flags'])} flagged)")
                print(f"{label:6s} {f.stem:28s} " + " | ".join(parts))
                for s, o in bad.items():
                    fl = o["flags"]
                    show = fl[:4] + ([("...", f"{len(fl) - 6} more")] if len(fl) > 6 else []) + (fl[-2:] if len(fl) > 6 else fl[4:6])
                    for fr, why in show:
                        print(f"         {s} f{fr}: {why}")
    print(f"{total} frames flagged")


if __name__ == "__main__":
    main(sys.argv[1:])
