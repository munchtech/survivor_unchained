"""Keep frames as evidence: python keep.py NAME=OUT [NAME=OUT ...] -> docs/experience/OUT.jpg (1920 wide, q85)."""
import sys, os
from PIL import Image

WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-af2c026d86e1b532b"
SHOTS = os.path.join(WT, "godot", ".shots")
DOCS = os.path.join(WT, "docs", "experience")
for pair in sys.argv[1:]:
    name, out = pair.split("=")
    im = Image.open(os.path.join(SHOTS, name if name.endswith(".png") else name + ".png")).convert("RGB")
    path = os.path.join(DOCS, out + ".jpg")
    im.save(path, quality=85)
    print(path, os.path.getsize(path) // 1024, "KB")
