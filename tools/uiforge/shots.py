"""Pictures of every screen the interface art touches, at 1920x1080.

    python tools/uiforge/shots.py [NAME ...] [--prefix P] [--res 2560x1440] [--no-import]

Runs the game once per screen (docs/UI_ART_BRIEF.md section 6) and leaves
the pictures in godot/.shots/ as P_NAME.png. With no names, all of them.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GODOT = os.environ.get("GODOT", r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe")

ITEMS = "chain_shirt:2,silver_ring:3,wolf_pelt,iron_helm:1,health_draught,ember_shard:4,hunting_bow:5,ember_staff:0,moonsilver_circlet:4,ashen_plate:3"
# The materials and oddments whose icons were painted from words.
MATS = "thornseed_pouch,wolf_pelt,boar_hide,bitterroot,bone_dust,blasting_ember,wolfhide_cloak,ember_shard"

SCREENS = {
    "title": (7, []),
    "creation": (6, ["--new"]),
    "hud_day": (8, ["--quick", "warden", "--zone", "waystation"]),
    "hud_night": (16, ["--quick", "reaver", "--zone", "arena", "--auto", "idle"]),
    "hud_verge": (9, ["--quick", "stalker", "--zone", "verge", "--time", "night"]),
    "draft": (7, ["--quick", "reaver", "--zone", "arena", "--open", "draft"]),
    "draft_pad": (8, ["--quick", "arcanist", "--zone", "arena", "--open", "draft", "--pad", "--keys", "Right"]),
    "pack": (6, ["--quick", "warden", "--zone", "waystation", "--items", ITEMS, "--open", "inventory"]),
    "pack_mats": (6, ["--quick", "warden", "--zone", "waystation", "--items", MATS, "--open", "inventory"]),
    "pack_pad": (7, ["--quick", "warden", "--zone", "waystation", "--items", ITEMS, "--open", "inventory", "--pad", "--keys", "Right,Right"]),
    "self": (6, ["--quick", "warden", "--zone", "waystation", "--open", "character"]),
    "arts": (6, ["--quick", "arcanist", "--zone", "waystation", "--open", "arts"]),
    "journal": (6, ["--quick", "warden", "--zone", "waystation", "--open", "journal"]),
    "map": (7, ["--quick", "warden", "--zone", "waystation", "--open", "map"]),
    "pause": (6, ["--quick", "warden", "--zone", "waystation", "--open", "pause"]),
    "pause_pad": (7, ["--quick", "warden", "--zone", "waystation", "--open", "pause", "--pad", "--keys", "Down"]),
    "rest": (6, ["--quick", "warden", "--zone", "waystation", "--open", "rest"]),
    "stash": (6, ["--quick", "warden", "--zone", "waystation", "--items", ITEMS, "--open", "stash"]),
    "shop": (6, ["--quick", "warden", "--zone", "waystation", "--items", ITEMS, "--open", "shop:harlan"]),
    "maps": (6, ["--quick", "warden", "--zone", "waystation", "--open", "maps"]),
    "talk": (8, ["--quick", "warden", "--zone", "waystation", "--open", "talk:rook"]),
    "result": (9, ["--quick", "reaver", "--zone", "arena", "--open", "result"]),
    "chapter": (7, ["--quick", "warden", "--zone", "waystation", "--open", "chapter"]),
}


RES = "1920x1080"


def run(name, prefix):
    secs, args = SCREENS[name]
    shot = f"{prefix}_{name}" if prefix else name
    cmd = [GODOT, "--path", os.path.join(ROOT, "godot"), "--resolution", RES, "--",
           "--shot", shot, "--seconds", str(secs)] + args
    path = os.path.join(ROOT, "godot", ".shots", shot + ".png")
    # A run that fails (out of memory on a busy machine) must not pass off the last picture as new.
    if os.path.exists(path):
        os.remove(path)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    ok = os.path.exists(path)
    print(f"{name:12} {'ok ' if ok else 'MISSING'} {path}", flush=True)
    if not ok:
        print(r.stdout[-1500:], r.stderr[-1500:])


def main():
    args = sys.argv[1:]
    prefix = ""
    if "--prefix" in args:
        i = args.index("--prefix")
        prefix = args[i + 1]
        del args[i:i + 2]
    global RES
    if "--res" in args:
        i = args.index("--res")
        RES = args[i + 1]
        del args[i:i + 2]
    skip = "--no-import" in args
    args = [a for a in args if a != "--no-import"]
    names = args or list(SCREENS)
    # Imported art loads from its import, so changed art must be imported again first.
    if not skip:
        subprocess.run([GODOT, "--headless", "--path", os.path.join(ROOT, "godot"), "--import"], capture_output=True, timeout=900)
    for n in names:
        run(n, prefix)


if __name__ == "__main__":
    main()
