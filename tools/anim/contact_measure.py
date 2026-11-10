"""Measure her blows' contact frames from the clips themselves, and write godot/data/anim/her_events.json.

    python tools/anim/contact_measure.py            measure, print, write
    python tools/anim/contact_measure.py --dry      measure and print only

Which clips: every "clip" / "clipHeavy" named on a skill's press record in godot/data/content/skills.json (the
clips the sim times her blows by; Sim/HerEvents.cs reads the file by clip name).

How: each clip is built by its own clip code (tools/anim/clips/*.py, as build.py does) and passed through the same
pack stages the game's library gets (clavhold, then armroll), so the motion measured is the motion packed. Its frames
are resampled at 60 fps the way the game plays them (each bone's rotation slerped between the clip's 30 fps keys),
and her right hand's blade is followed: the tip = hand_r + the fitted pocket's line (WeaponSockets.cs BladeDirR, the
shaft toward the tip) x BLADE metres, in her character space. Two measures:
  peak   the frame where the tip's speed peaks in the strike (the first 40% of the clip: the cut, not the recovery);
  cross  the frame where the tip's sweep crosses her facing (its bearing about her vertical axis passes forward).
The contact written is `cross` when the sweep crosses her facing during the strike, else `peak`; a disagreement with
the clip code's declared contact (meta "contact", seconds) of more than 2 frames is flagged.
"""
from __future__ import annotations

import importlib
import json
import math
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from keyed import Rig, slide_dir  # noqa: E402
from rig import DATA, REPO, Skeleton, qslerp, qrot, qinv, write_clip  # noqa: E402

FPS = 60
BLADE = 0.85          # metres from the grip to the tip (her arming sword)
STRIKE = 0.4          # the strike is looked for in this share of the clip
SKILLS = REPO / "godot" / "data" / "content" / "skills.json"
OUT = REPO / "godot" / "data" / "anim" / "her_events.json"
DOC = ("M3 interim: measured from today's clips by tools/anim/contact_measure.py (the blade tip's sweep crossing her "
       "facing, else its speed peak; frames from the clip's start at 60 fps, in clip time); A1's P4 pack replaces it.")


def skill_clips():
    d = json.loads(SKILLS.read_text(encoding="utf-8"))
    names = []
    for s in d["skills"]:
        r = s.get("press") or {}
        for c in (r.get("clip") or []) + ([r["clipHeavy"]] if r.get("clipHeavy") else []):
            if c not in names:
                names.append(c)
    return names


def build_clips(names, sk, rig):
    """The clips by their own code, staged as pack() stages them; {name: clip json}."""
    import armroll
    import clavhold
    tmp = Path(tempfile.mkdtemp(prefix="contact_"))
    raw, held = tmp / "raw", tmp / "held"
    raw.mkdir()
    found = set()
    for f in sorted((HERE / "clips").glob("*.py")):
        if f.name.startswith("_"):
            continue
        m = importlib.import_module(f"clips.{f.stem}")
        if not hasattr(m, "clips"):
            continue
        for clip in m.clips(rig, list(names)):
            if clip.name in names and clip.name not in found:
                write_clip(clip, sk, raw)
                found.add(clip.name)
        if found >= set(names):
            break
    src = clavhold.stage(raw, held, sk, log=lambda *_: None) if clavhold.on() else raw
    if armroll.on():
        src = armroll.stage(src, src if src != raw else held, sk, log=lambda *_: None)
    got = {n: json.loads((src / f"{n}.json").read_text()) for n in names if (src / f"{n}.json").exists()}
    shutil.rmtree(tmp, ignore_errors=True)
    return got


def tracks(sk, d):
    """Local rotations [T, J, 4] and positions [T, J, 3] from a clip JSON (rest where untracked)."""
    T = len(next(t for t in d["tracks"])["keys"])
    rot = np.broadcast_to(sk.rest_rot, (T,) + sk.rest_rot.shape).copy()
    pos = np.broadcast_to(sk.rest_pos, (T,) + sk.rest_pos.shape).copy()
    for t in d["tracks"]:
        j = sk.i(t["bone"])
        (rot if t["type"] == "rot" else pos)[:, j] = np.array(t["keys"], float)
    return rot, pos


def at60(rot, pos, fps):
    """The clip resampled at 60 fps as the game plays it: rotations slerped, positions lerped."""
    T = rot.shape[0]
    n = int(round((T - 1) / fps * FPS)) + 1
    r = np.empty((n,) + rot.shape[1:])
    p = np.empty((n,) + pos.shape[1:])
    for k in range(n):
        f = min(k * fps / FPS, T - 1)
        a = int(math.floor(f))
        b = min(a + 1, T - 1)
        u = f - a
        for j in range(rot.shape[1]):
            r[k, j] = qslerp(rot[a, j], rot[b, j], u)
        p[k] = pos[a] * (1 - u) + pos[b] * u
    return r, p


def measure(sk, d, weapon):
    rot, pos = tracks(sk, d)
    r, p = at60(rot, pos, d["fps"])
    grot, gpos = sk.fk(r, p)
    jr, jh, jp = sk.i("root"), sk.i("hand_r"), sk.i("pelvis")
    shaft = slide_dir(weapon)
    tips = []
    for k in range(r.shape[0]):
        tip = gpos[k, jh] + qrot(grot[k, jh], shaft) * BLADE
        # her character space (the root's: Y up, Z her facing), about her pelvis
        tips.append(qrot(qinv(grot[k, jr]), tip - gpos[k, jp]))
    tips = np.array(tips)
    n = len(tips)
    lim = max(3, int(n * STRIKE))
    speed = np.linalg.norm(np.diff(tips, axis=0), axis=1) * FPS          # speed[k]: frame k -> k+1
    # a frame's speed: the mean of the steps either side (frame 0: its first step)
    fs = np.concatenate([[speed[0]], (speed[:-1] + speed[1:]) / 2])
    peak = int(np.argmax(fs[:lim]))
    bearing = np.degrees(np.arctan2(tips[:, 0], tips[:, 2]))             # 0: straight ahead, + to her left (+X)
    cross = None
    for k in range(lim):
        a, b = bearing[k], bearing[k + 1]
        if (a <= 0 < b or b <= 0 < a) and tips[k, 2] > 0 and abs(a - b) < 120:
            cross = k + abs(a) / max(1e-6, abs(a - b))
            break
    return {"peak": peak, "cross": cross, "speed": float(fs[peak]), "frames": n, "bearing": bearing[:lim + 1]}


def main(argv):
    names = skill_clips()
    sk = Skeleton.load(DATA / "heroine_skeleton.json")
    rig = Rig(sk, body="her")
    built = build_clips(names, sk, rig)
    lib = json.loads((REPO / "godot" / "art" / "anim" / "heroine_clips.json").read_text(encoding="utf-8"))
    out = {"_doc": DOC, "fps": FPS, "clips": {}}
    for n in names:
        if n not in built:
            print(f"  {n}: no clip code builds it; left out")
            continue
        d = built[n]
        meta = d.get("meta", {})
        m = measure(sk, d, meta.get("weapon", "sword"))
        contact = int(round(m["cross"])) if m["cross"] is not None else m["peak"]
        declared = meta.get("contact", lib.get(n, {}).get("contact"))
        dec = None if declared is None else declared * FPS
        flag = "" if dec is None or abs(contact - dec) <= 2 else "  DISAGREES (>2 frames)"
        cr = "none" if m["cross"] is None else f"{m['cross']:.1f}"
        print(f"  {n:14s} contact {contact:2d}  (cross {cr}, peak {m['peak']}, tip {m['speed']:.1f} m/s)  declared "
              f"{'-' if dec is None else f'{dec:.1f}'}  of {m['frames']} frames{flag}")
        if "-v" in argv:
            print("     bearing:", " ".join(f"{b:.0f}" for b in m["bearing"]))
        out["clips"][n] = {"contact": [contact]}
    if "--dry" in argv:
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        # (the P4 pack shares the file: every clip not measured here keeps its entry, e.g. A1's four action clips)
        was = json.loads(OUT.read_text(encoding="utf-8")).get("clips", {})
        out["clips"] = dict(sorted({**was, **out["clips"]}.items()))
    OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"written {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main(sys.argv[1:])
