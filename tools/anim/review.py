"""Contact sheets of clips on her, for judging them (godot/tools_scenes/anim_review.gd).

    python tools/anim/review.py <clip> [view ...] [--frames N] [--step K] [--speed M] [--weapon W] [--outfit O] [--start S] [--size WxH]

<clip> is "her/<name>" or "ual/<name>"; views are front, side, back, three,
top and game. Sheets land in tools/anim/out/sheets/<clip>_<view>.png.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
OUT = HERE / "out" / "sheets"
GODOT = os.environ.get("GODOT", r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe")


def sheet(clip, view="three", frames=16, step=2, speed=0.0, weapon="", outfit="warden", start=0.0, size=(300, 400),
          cols=None, hair="ponytail", play=1.0, out=None, extra=None):
    OUT.mkdir(parents=True, exist_ok=True)
    out = out or OUT / f"{clip.replace('/', '_')}_{view}.png"
    env = dict(os.environ, VIEW=view, FRAMES=str(frames), STEP=str(step), SPEED=str(speed), WEAPON=weapon,
               OUTFIT=outfit, START=str(start), W=str(size[0]), H=str(size[1]), COLS=str(cols or min(5, frames)),
               HAIR=hair, PLAY=str(play))
    env.update(extra or {})
    r = subprocess.run([GODOT, "--path", str(REPO / "godot"), "--fixed-fps", "30", "-s", "res://tools_scenes/anim_review.gd",
                        "--", clip, str(out)], env=env, capture_output=True, text=True)
    ok = any("SHEET" in l for l in r.stdout.splitlines())
    if not ok:
        print("\n".join(l for l in (r.stdout + r.stderr).splitlines() if "ERROR" in l or "SCRIPT" in l)[:2000])
    return out


def main(argv):
    clip = argv[0]
    views = []
    kw = {}
    i = 1
    while i < len(argv):
        a = argv[i]
        if a.startswith("--"):
            k = a[2:]
            v = argv[i + 1]
            i += 2
            if k == "size":
                w, h = v.split("x")
                kw["size"] = (int(w), int(h))
            elif k in ("frames", "step", "cols"):
                kw[k] = int(v)
            elif k in ("speed", "start", "play"):
                kw[k] = float(v)
            else:
                kw[k] = v
        else:
            views.append(a)
            i += 1
    for v in views or ["three"]:
        print(sheet(clip, v, **kw))


if __name__ == "__main__":
    main(sys.argv[1:])
