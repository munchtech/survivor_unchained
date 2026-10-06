"""Build her clips (or his) and pack them for the game.

    python tools/anim/build.py                 every clip in tools/anim/clips/
    python tools/anim/build.py run idle        only clips whose names contain these
    python tools/anim/build.py --no-pack ...   write the clips, leave the library
    python tools/anim/build.py --body hero     the hero's library from the same code

Each module in tools/anim/clips/ has a `clips(rig, want)` that returns Clips
(keyed in code, or retargeted from mocap). They are written as JSON to
tools/anim/out/clips/ and packed by Godot (godot/tools_scenes/anim_pack.gd)
into godot/art/anim/heroine.res, with what the game reads about each
(speed, contacts, layer) in godot/art/anim/heroine_clips.json. Clips not in
this run are kept from earlier runs: the library is always every JSON there.

The hero's are made by the same code on his own skeleton (hero.glb, dumped
to tools/anim/data/hero_skeleton.json) with a man's carriage (keyed.Rig's
`body`: his feet wider, gait.manly), written to tools/anim/out/hero/ and
packed into godot/art/anim/hero.res (OwnClips.Him, played as "him/...").
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
from rig import DATA, REPO, Skeleton, write_clip  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "clips"
GODOT = os.environ.get("GODOT", r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe")

# body: (skeleton, Rig body, out folder, library file stem)
BODIES = {
    "heroine": ("heroine_skeleton.json", "her", OUT, "heroine"),
    "hero": ("hero_skeleton.json", "him", HERE / "out" / "hero", "hero"),
}


def modules():
    for f in sorted((Path(__file__).resolve().parent / "clips").glob("*.py")):
        if f.name.startswith("_"):
            continue
        m = importlib.import_module(f"clips.{f.stem}")
        # (Some modules make other bodies' clips, packed elsewhere: warden.py by folk.py.)
        if hasattr(m, "clips"):
            yield m


def pack(out=OUT, stem="heroine"):
    lib = REPO / "godot" / "art" / "anim"
    lib.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([GODOT, "--headless", "--path", str(REPO / "godot"), "-s", "res://tools_scenes/anim_pack.gd", "--",
                        str(out), f"res://art/anim/{stem}.res", str(lib / f"{stem}_clips.json")],
                       capture_output=True, text=True)
    for line in (r.stdout + r.stderr).splitlines():
        if "PACKED" in line or "ERROR" in line or "SCRIPT" in line:
            print(line)


def main(argv):
    body = "heroine"
    if "--body" in argv:
        body = argv[argv.index("--body") + 1]
        argv = [a for i, a in enumerate(argv) if a != "--body" and (i == 0 or argv[i - 1] != "--body")]
    skel, who, out, stem = BODIES[body]
    want = [a for a in argv if not a.startswith("--")]
    sk = Skeleton.load(DATA / skel)
    rig = Rig(sk, body=who)
    made = []
    for m in modules():
        t0 = time.time()
        for clip in m.clips(rig, want):
            if want and not any(w in clip.name for w in want):
                continue
            write_clip(clip, sk, out)
            made.append(clip.name)
            print(f"  {clip.name:28s} {clip.frames:4d} frames  {clip.length:5.2f} s  {m.__name__}  ({time.time() - t0:.1f} s)")
    print(f"{len(made)} clips written to {out}")
    # A full build is the whole library: clips no module makes any more go.
    if not want:
        for f in out.glob("*.json"):
            if f.stem not in made:
                f.unlink()
                print(f"  (dropped {f.stem})")
    if "--no-pack" not in argv:
        pack(out, stem)
        if body == "heroine":
            import manifest
            manifest.main()


if __name__ == "__main__":
    main(sys.argv[1:])
