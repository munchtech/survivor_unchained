"""Kimodo takes, whole, onto a body for judging: "k_<prompt>_<take>".

    python try_takes.py her|hero|m|f prompt [prompt ...] [place=keep|pin|line]

her/hero write to their out folders (packed into heroine.res / hero.res);
m/f to out/folk as "m_k_..." / "f_k_..." (folk.res). Delete k_ files and
repack when done.
"""
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\tools\anim")
sys.path.insert(0, str(ROOT))
import build  # noqa: E402
import folk  # noqa: E402
from clips.generated import make  # noqa: E402
from keyed import Rig  # noqa: E402
from rig import DATA, Skeleton, write_clip  # noqa: E402

who = sys.argv[1]
names = [a for a in sys.argv[2:] if "=" not in a]
kw = dict(a.split("=", 1) for a in sys.argv[2:] if "=" in a)
place = kw.get("place", "keep")
if who in ("her", "hero"):
    skel, body, out, stem = build.BODIES["heroine" if who == "her" else "hero"]
    sk = Skeleton.load(DATA / skel)
    rig = Rig(sk, body=body)
    prefix = ""
else:
    sk = Skeleton.load(DATA / ("folk_male_skeleton.json" if who == "m" else "folk_female_skeleton.json"))
    rig = Rig(sk)
    out = folk.OUT
    prefix = who + "_"
made = []
for n in names:
    for t in range(3):
        c = make(rig, f"{prefix}k_{n}_{t}", "kimodo", f"{n}_{t}.bvh", place=place)
        if c is None:
            print("missing", n, t)
            continue
        write_clip(c, sk, out)
        made.append(c.name)
        print(f"  {c.name:28s} {c.frames} frames {c.length:.2f} s")
if kw.get("pack", "1") == "1":
    if who in ("her", "hero"):
        build.pack(out, stem)
    else:
        folk.pack()
print(made)
