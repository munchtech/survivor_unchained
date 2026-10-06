"""Crowd sheets (CrowdSheet.cs) for several kinds and roles, tiled with labels.

    python csheet.py out.png visual:role[,role...] ... [N=8] [STEP=0.1] [START=0] [YAW=90] [CELL=1.6] [W=1800] [H=420] [LIFT=10] [fresh=1]
"""
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

GODOT = r"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
PROJ = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a03acf30b3e9bdd70\godot"
HERE = Path(__file__).parent / "sh"
HERE.mkdir(exist_ok=True)

out = Path(sys.argv[1])
rows, env = [], {"N": "8", "STEP": "0.1", "YAW": "90", "CELL": "1.6", "W": "1800", "H": "420", "LIFT": "10"}
fresh = False
for a in sys.argv[2:]:
    if "=" in a:
        k, v = a.split("=", 1)
        if k == "fresh":
            fresh = v == "1"
        else:
            env[k] = v
    else:
        vis, roles = a.split(":")
        for r in roles.split(","):
            rows.append((vis, r))
imgs = []
first = {}
for vis, role in rows:
    p = HERE / f"cs_{vis}_{role}.png"
    e = dict(os.environ, VISUAL=vis, ROLE=role, OUT=str(p), **env)
    args = [GODOT, "--path", PROJ, "-s", "res://tools_scenes/crowd_sheet.gd", "--"]
    if fresh and vis not in first:
        args.append("--vat-fresh")
        first[vis] = 1
    r = subprocess.run(args, env=e, capture_output=True, text=True, timeout=600)
    if "CROWDSHEET" not in r.stdout:
        print("\n".join(l for l in (r.stdout + r.stderr).splitlines() if "ERROR" in l or "rror" in l)[:1500])
        continue
    imgs.append((f"{vis} {role}", Image.open(p)))
w = max(i.width for _, i in imgs)
h = sum(i.height for _, i in imgs)
board = Image.new("RGB", (w, h), (30, 30, 34))
d = ImageDraw.Draw(board)
y = 0
for name, i in imgs:
    board.paste(i, (0, y))
    d.rectangle([0, y, 9 * len(name) + 10, y + 18], fill=(0, 0, 0))
    d.text((5, y + 3), name, fill=(255, 220, 120))
    y += i.height
board.save(out)
print(out)
