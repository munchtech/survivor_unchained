"""A Marionette NPC package in the real game: the game's lighting, clips, LODs and spring bones.

  python tools/npc/ingame.py <package folder | art/npc name>              # a window: it walks beside her, side camera
  python tools/npc/ingame.py <package> --view play|side|close [--still]  # the window's camera; --still: idle, not walking
  python tools/npc/ingame.py <package> --frames <out folder>             # pictures instead (no window to watch)

A folder outside the game (Marionette's generated/to_game/npc/NAME) is read through --npc-overlay NAME=FOLDER
(NpcPackage.Overlay): its manifest.json and glbs load at run time, nothing copied, nothing imported. A bare name is
the package in godot/art/npc. The game hook is GameNpcShot (--npc NAME[:walk][:side][:swap][:chest][:still]).

Frames: play_idle, play_walk (the play camera, it beside her), side_idle, side_walk (4 m off its flank at hip height,
fov 30: knees, hem and feet; six frames 0.15 s apart for the stride), close (in her place, the chest camera), and a
contact sheet (sheet.png) when Pillow is there. Each run's log is kept beside its frames (log_SHOT.txt); the lines
about the package (npc:, springs, warnings naming it) are printed after each.

Takes the godot turn (tools/turn.py) for the run and gives it back, the window included. --zone, --time pass on.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GODOT_DIR = ROOT / "godot"
GODOT = Path(os.environ.get("GODOT_EXE", "C:/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"))
TURN = Path("C:/Users/munch/Desktop/survivorsunchained/tools/turn.py")

# (name, --npc flags, extra args)
SHOTS = [
    ("play_idle", "", ["--seconds", "6"]),
    ("play_walk", ":walk", ["--seconds", "6"]),
    ("side_idle", ":side:still", ["--seconds", "6"]),
    ("side_walk", ":walk:side", ["--seconds", "6", "--every", "0.15", "--count", "6"]),
    ("close", ":swap:chest", ["--close", "1", "--idle-after", "1", "--seconds", "8"]),
]


def package(arg):
    """(name, overlay folder or None)."""
    p = Path(arg)
    if p.is_dir() and (p / "manifest.json").exists():
        p = p.resolve()
        if GODOT_DIR / "art" / "npc" in p.parents:
            return p.name, None
        return p.name, p
    if (GODOT_DIR / "art" / "npc" / arg / "manifest.json").exists():
        return arg, None
    sys.exit(f"no package: {arg} (a folder with manifest.json, or a name under godot/art/npc)")


def base_args(name, overlay, a):
    args = ["--quick", "warden", "--sex", "female", "--nohud", "--zone", a.zone, "--facing", "0", "--seed", "1"]
    if a.time:
        args += ["--time", a.time]
    if overlay:
        args += ["--npc-overlay", f"{name}={overlay.as_posix()}"]
    return args


def turn(*what):
    return subprocess.run([sys.executable, str(TURN), *what]).returncode


def build():
    r = subprocess.run(["dotnet", "build", "-v", "q", "-nologo", "SurvivorUnchained.csproj"], cwd=GODOT_DIR, capture_output=True, text=True)
    if r.returncode:
        sys.exit("dotnet build failed:\n" + r.stdout[-2000:])


def notable(log, name):
    """The log's lines about the package."""
    # (the place's own townsfolk packages load too: their npc: lines are left out)
    keep = re.compile(rf"^npc shot|^npc debug|springs|{re.escape(name)}|overlay", re.I)
    seen = []
    for line in log.splitlines():
        if line.startswith(" ") or not keep.search(line) or line in seen:
            continue
        seen.append(line)
    return seen[:25]


def sheet(out, names):
    try:
        from PIL import Image
    except ImportError:
        return
    ims = [Image.open(out / f"{n}.png") for n in names if (out / f"{n}.png").exists()]
    if not ims:
        return
    w, h = 640, 360
    cols = 3
    s = Image.new("RGB", (w * cols, h * ((len(ims) + cols - 1) // cols)), (20, 20, 20))
    for i, im in enumerate(ims):
        s.paste(im.convert("RGB").resize((w, h)), ((i % cols) * w, (i // cols) * h))
    s.save(out / "sheet.png")
    print(f"sheet: {out / 'sheet.png'}")


def frames(name, overlay, a):
    out = Path(a.frames).resolve()
    out.mkdir(parents=True, exist_ok=True)
    shots_dir = GODOT_DIR / ".shots"
    taken = []
    for shot, flags, extra in SHOTS:
        tag = f"npcig_{shot}"
        for f in shots_dir.glob(f"{tag}*.png"):
            f.unlink()
        cmd = [str(GODOT), "--path", ".", "--fixed-fps", "60", "--resolution", "1920x1080", "--",
               *base_args(name, overlay, a), *extra, "--npc", name + flags, "--npc-debug", "--shot", tag]
        r = subprocess.run(cmd, cwd=GODOT_DIR, capture_output=True, text=True, timeout=400, stdin=subprocess.DEVNULL)
        log = (r.stdout or "") + (r.stderr or "")
        (out / f"log_{shot}.txt").write_text(log, encoding="utf-8")
        # (only its own frames: a place may save others, a tip's map)
        got = sorted(f for f in shots_dir.glob(f"{tag}*.png") if re.fullmatch(rf"{tag}(_\d+)?\.png", f.name))
        for f in shots_dir.glob(f"{tag}*.png"):
            if f not in got:
                f.unlink()
        for i, f in enumerate(got):
            dest = out / (f"{shot}.png" if len(got) == 1 or i == 0 else f"{shot}_{i}.png")
            shutil.move(str(f), dest)
        if got:
            taken.append(shot)
        print(f"{shot}: {len(got)} frame(s){'' if got else f' MISSING (exit {r.returncode})'}")
        for line in notable(log, name):
            print("   ", line)
    sheet(out, taken)
    print(f"frames in {out}")


def window(name, overlay, a):
    flags = {"side": ":side", "play": "", "close": ":swap:chest"}[a.view]
    if not a.still:
        flags = ":walk" + flags
    elif a.view == "side":
        flags += ":still"
    extra = ["--close", "1", "--idle-after", "1"] if a.view == "close" else []
    cmd = [str(GODOT), "--path", ".", "--", *base_args(name, overlay, a), *extra, "--npc", name + flags]
    print("running:", subprocess.list2cmdline(cmd))
    subprocess.run(cmd, cwd=GODOT_DIR)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("package")
    ap.add_argument("--frames", help="folder for pictures (no window)")
    ap.add_argument("--view", choices=["side", "play", "close"], default="side")
    ap.add_argument("--still", action="store_true", help="idle in place, not walking")
    ap.add_argument("--zone", default="verge")   # (the Verge: no townsfolk walking through the side camera)
    ap.add_argument("--time", choices=["day", "night"])
    ap.add_argument("--no-build", action="store_true")
    a = ap.parse_args()
    name, overlay = package(a.package)
    print(f"package {name}" + (f" from {overlay}" if overlay else " (godot/art/npc)"))
    who = f"npc ingame: {name}"
    if turn("take", "godot", who, "--wait", "20"):
        sys.exit("no godot turn")
    try:
        if not a.no_build:
            build()
        frames(name, overlay, a) if a.frames else window(name, overlay, a)
    finally:
        turn("give", "godot", who)


if __name__ == "__main__":
    main()
