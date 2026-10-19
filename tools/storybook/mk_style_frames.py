"""The style frames, shot through the game's own player: SB00 with three plates
painted (one flat layer each, the rest still cards), as godot/data/storybook/
sb00_style.json, so the bars, the subtitles, the grade, the grain and the
vignette are the shipped ones. Unjudged art: not committed until it passes.

    python tools/storybook/mk_style_frames.py p1=<png> p4=<png> p9=<png>
    dotnet build godot; Godot_console.exe --headless --path godot --import
    Godot_console.exe --path godot --resolution 1920x1080 --fixed-fps 30 -- --storybook sb00_style --sb-shots 7,31.25,74 --perf
"""
import json
import os
import shutil
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from make_test_plates import ROOT, write_import  # noqa: E402

ART = os.path.join(ROOT, "godot", "art", "storybook", "sb00", "style")
DATA = os.path.join(ROOT, "godot", "data", "storybook")


def main():
    picks = dict(a.split("=", 1) for a in sys.argv[1:])
    os.makedirs(ART, exist_ok=True)
    spec = json.load(open(os.path.join(DATA, "sb00.json"), encoding="utf-8"))
    cw, ch = spec["canvas"]
    spec["id"] = "sb00_style"
    spec["title"] = "SB00 style frames (unjudged)"
    for plate in spec["plates"]:
        src = picks.get(plate["id"])
        if not src:
            continue
        dst = os.path.join(ART, plate["id"] + ".png")
        shutil.copyfile(src, dst)
        write_import(dst)
        w, h = Image.open(dst).size
        s = cw / w
        plate["layers"] = [{"id": "paint", "image": "res://art/storybook/sb00/style/" + plate["id"] + ".png",
                            "pos": [0, round((ch - h * s) / 2, 1)], "scale": round(s, 5), "z": 1}]
        print(plate["id"], "<-", os.path.relpath(src, ROOT), (w, h), "scale", round(s, 4))
    json.dump(spec, open(os.path.join(DATA, "sb00_style.json"), "w", encoding="utf-8"), indent=1)
    print("wrote godot/data/storybook/sb00_style.json")


if __name__ == "__main__":
    main()
