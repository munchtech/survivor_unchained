"""Build her clips and pack them for the game.

    python tools/anim/build.py                 every clip in tools/anim/clips/
    python tools/anim/build.py run idle        only clips whose names contain these
    python tools/anim/build.py --no-pack ...   write the clips, leave the library

Each module in tools/anim/clips/ has a `clips(rig)` that returns Clips (keyed
in code, or retargeted from mocap). They are written as JSON to
tools/anim/out/clips/ and packed by Godot (godot/tools_scenes/anim_pack.gd)
into godot/art/anim/heroine.res, with what the game reads about each
(speed, contacts, layer) in godot/art/anim/heroine_clips.json. Clips not in
this run are kept from earlier runs: the library is always every JSON there.
"""
from __future__ import annotations

import importlib
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from keyed import Rig  # noqa: E402
from rig import REPO, Skeleton, write_clip  # noqa: E402

OUT = Path(__file__).resolve().parent / "out" / "clips"
GODOT = os.environ.get("GODOT", r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe")


def modules():
    for f in sorted((Path(__file__).resolve().parent / "clips").glob("*.py")):
        if f.name.startswith("_"):
            continue
        yield importlib.import_module(f"clips.{f.stem}")


def pack():
    lib = REPO / "godot" / "art" / "anim"
    lib.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([GODOT, "--headless", "--path", str(REPO / "godot"), "-s", "res://tools_scenes/anim_pack.gd", "--",
                        str(OUT), "res://art/anim/heroine.res", str(lib / "heroine_clips.json")],
                       capture_output=True, text=True)
    for line in (r.stdout + r.stderr).splitlines():
        if "PACKED" in line or "ERROR" in line or "SCRIPT" in line:
            print(line)


def main(argv):
    want = [a for a in argv if not a.startswith("--")]
    sk = Skeleton.load()
    rig = Rig(sk)
    made = 0
    for m in modules():
        t0 = time.time()
        for clip in m.clips(rig, want):
            if want and not any(w in clip.name for w in want):
                continue
            write_clip(clip, sk, OUT)
            made += 1
            print(f"  {clip.name:28s} {clip.frames:4d} frames  {clip.length:5.2f} s  {m.__name__}  ({time.time() - t0:.1f} s)")
    print(f"{made} clips written to {OUT}")
    if "--no-pack" not in argv:
        pack()


if __name__ == "__main__":
    main(sys.argv[1:])
