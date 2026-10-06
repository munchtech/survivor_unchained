"""A/B screenshots: the same moments with kept builds, and how far each differs from the first.
    python abshots.py NAME A=dir,B=dir,... -- game args (with --seconds/--every/--count)"""
import os
import subprocess
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7145e18b3eb78294\godot\.shots"
argv = sys.argv[1:]
i = argv.index("--")
name, builds, game = argv[0], [b.split("=", 1) for b in argv[1].split(",")], argv[i + 1:]
engine = []
if len(argv[:i]) > 2 and argv[2] == "--engine":
    engine = ["--engine", argv[3]]
for label, d in builds:
    subprocess.run([sys.executable, os.path.join(HERE, "shot.py"), d, f"{name}_{label}", *game, *engine], check=False)


def frames(label):
    pre = f"{name}_{label}"
    fs = sorted(f for f in os.listdir(SHOTS) if f.startswith(pre) and f.endswith(".png") and f[len(pre):len(pre) + 1] in ("_", "."))
    return fs


ref = frames(builds[0][0])
for label, _ in builds[1:]:
    for fa, fb in zip(ref, frames(label)):
        a = np.asarray(Image.open(os.path.join(SHOTS, fa)).convert("RGB")).astype(int)
        b = np.asarray(Image.open(os.path.join(SHOTS, fb)).convert("RGB")).astype(int)
        d = np.abs(a - b).sum(2)
        print(f"{fa} vs {fb}: mean {a.mean():.1f}, differing px {(d > 0).sum()}, >24: {(d > 24).sum()}, max {d.max()}")
