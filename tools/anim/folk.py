"""The townsfolk's own clips: captured and generated motion retargeted onto
the kit's bodies (the game's women and men, People.Build), packed into
godot/art/anim/folk.res for People.Clip (FolkClips.cs); the crowd's
own motion, keyed (crowd.py), which the crowd bakes (Vat.cs); and the
Ford-Warden's cinematic clips on the man (clips/warden.py), which the
cinematics play by name ("folk/m_rise_stiff").

    python tools/anim/folk.py [names]

The kit's female and male bodies stand on skeletons of their own (dumped by
godot/tools_scenes/anim_skeleton.gd to tools/anim/data/folk_*_skeleton.json):
the same bones as the library's, but their rests differ from it by up to
23 degrees (the neck), so each clip is made for each body, "f_<name>" and
"m_<name>". Sources: Mixamo (Adobe, used in the game, raw files not
redistributed) and Kimodo (NVIDIA Open Model License), both under
C:/Users/munch/Tools/mocap (see clips/generated.py).
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import crowd  # noqa: E402
from build import GODOT  # noqa: E402
from clips import warden  # noqa: E402
from clips.generated import make  # noqa: E402
from keyed import Rig  # noqa: E402
from rig import DATA, REPO, Skeleton, write_clip  # noqa: E402

OUT = Path(__file__).resolve().parent / "out" / "folk"

LOOP = dict(loop=True, place="pin")

# name: {sex: (source, file, options)}; "fm" for both. Each was picked from
# its takes on contact sheets (tools/anim/review.py).
FOLK = {
    # Walking about town: the women's walk with a sway, the men's easy stride.
    "walk": {"f": ("mixamo", "folk_walk_feminine.bvh", dict(loop="cycle", place="line")),
             "m": ("kimodo", "walk_man_2.bvh", dict(loop=True, place="line"))},
    # Standing: weight shifting from foot to foot.
    "idle": {"fm": ("mixamo", "folk_weight_shift_idle.bvh", LOOP)},
    # Talking: hers with both hands, his the general conversation.
    "talk": {"f": ("kimodo", "talk_0.bvh", LOOP), "m": ("mixamo", "folk_talking.bvh", LOOP)},
    "arms_crossed": {"fm": ("kimodo", "arms_crossed_0.bvh", LOOP)},
    "sit_chair": {"fm": ("mixamo", "folk_sitting_chair.bvh", LOOP)},
    "sit_floor": {"fm": ("mixamo", "folk_sitting_floor.bvh", LOOP)},
    # Gestures played once.
    "cheer": {"f": ("kimodo", "cheer_2.bvh", dict(place="pin")), "m": ("kimodo", "cheer_0.bvh", dict(place="pin"))},
    "wave": {"fm": ("kimodo", "wave_1.bvh", dict(place="pin"))},
    "work": {"fm": ("kimodo", "work_0.bvh", dict(place="pin", warp=[(0.4, 3.2, 2.8)]))},
    "pick_up": {"fm": ("mixamo", "folk_pick_up.bvh", dict(place="pin"))},
}


def build(want):
    made = []
    for sex, sk_file in (("f", "folk_female_skeleton.json"), ("m", "folk_male_skeleton.json")):
        sk = Skeleton.load(DATA / sk_file)
        rig = Rig(sk)
        for name, rows in FOLK.items():
            if want and not any(w in name for w in want):
                continue
            row = next((r for k, r in rows.items() if sex in k), None)
            if row is None:
                continue
            source, file, opts = row
            opts = dict(opts)
            opts["warp_"] = opts.pop("warp", None)
            t0 = time.time()
            clip = make(rig, f"{sex}_{name}", source, file, note=f"townsfolk ({'women' if sex == 'f' else 'men'})", **opts)
            if clip is None:
                print(f"  {sex}_{name}: {file} not on this machine")
                continue
            write_clip(clip, sk, OUT)
            made.append(clip.name)
            print(f"  {clip.name:16s} {clip.frames:4d} frames {clip.length:5.2f} s  speed {clip.meta.get('speed', 0):.2f}  "
                  f"({time.time() - t0:.1f} s)")
        # The Ford-Warden's cinematic clips, on the man (clips/warden.py).
        for name, fn in (warden.CLIPS.items() if sex == "m" else ()):
            if want and not any(w in name for w in want):
                continue
            t0 = time.time()
            clip = fn(f"{sex}_{name}", rig)
            if clip is None:
                print(f"  {sex}_{name}: its take is not on this machine")
                continue
            write_clip(clip, sk, OUT)
            made.append(clip.name)
            print(f"  {clip.name:16s} {clip.frames:4d} frames {clip.length:5.2f} s  (the Warden, {time.time() - t0:.1f} s)")
        # The crowd's own motion, keyed (crowd.py).
        for name, fn in crowd.KEYED.items():
            if want and not any(w in name for w in want):
                continue
            clip = fn(f"{sex}_{name}", rig)
            write_clip(clip, sk, OUT)
            made.append(clip.name)
            print(f"  {clip.name:16s} {clip.frames:4d} frames {clip.length:5.2f} s  speed {clip.meta.get('speed', 0):.2f}  (keyed)")
    return made


def pack():
    lib = REPO / "godot" / "art" / "anim"
    r = subprocess.run([GODOT, "--headless", "--path", str(REPO / "godot"), "-s", "res://tools_scenes/anim_pack.gd", "--",
                        str(OUT), "res://art/anim/folk.res", str(lib / "folk_clips.json")], capture_output=True, text=True)
    for line in (r.stdout + r.stderr).splitlines():
        if "PACKED" in line or "ERROR" in line or "SCRIPT" in line:
            print(line)


if __name__ == "__main__":
    # (A name that matches nothing packs nothing: the library is every clip
    # in out/folk, and a fresh checkout has none there yet.)
    if build([a for a in sys.argv[1:] if not a.startswith("--")]) and "--no-pack" not in sys.argv:
        pack()
