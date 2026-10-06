"""Scratch: Kimodo takes onto the kit bodies as <sex>_k_<take> in out/folk, for judging.

    python folk_try.py m|f|fm take [take ...] [--loop] [--place line|pin|keep]
"""
import sys
from pathlib import Path

REPO = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a1e3002b800ee55ac")
sys.path.insert(0, str(REPO / "tools" / "anim"))

from clips.generated import make  # noqa: E402
from keyed import Rig  # noqa: E402
from rig import DATA, Skeleton, write_clip  # noqa: E402

OUT = REPO / "tools" / "anim" / "out" / "folk"
argv = sys.argv[1:]
place = "line"
if "--place" in argv:
    i = argv.index("--place")
    place = argv[i + 1]
    del argv[i:i + 2]
loop = "--loop" in argv
argv = [a for a in argv if not a.startswith("--")]
sexes, takes = argv[0], argv[1:]
for sex in sexes:
    sk = Skeleton.load(DATA / ("folk_female_skeleton.json" if sex == "f" else "folk_male_skeleton.json"))
    rig = Rig(sk)
    for take in takes:
        c = make(rig, f"{sex}_k_{take}", "kimodo", f"{take}.bvh", loop=loop, place=place)
        write_clip(c, sk, OUT)
        print(c.name, c.frames, round(c.length, 2), "speed", round(c.meta.get("speed", 0), 2))
