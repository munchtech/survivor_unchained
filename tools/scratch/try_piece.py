"""Render a pages.py piece to the scratchpad (not into the game): python try_piece.py NAME [OUT]"""
import os
import sys

WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa9c11f1e40170a4d"
sys.path.insert(0, os.path.join(WT, "tools", "uiforge"))
os.chdir(os.path.join(WT, "tools", "uiforge"))
import forge as F  # noqa: E402
import pages  # noqa: E402

name = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), name + ".png")
img = getattr(pages, name)()
F.save(F.to_pil(img), out)
print("saved", out)
