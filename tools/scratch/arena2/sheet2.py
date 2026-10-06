"""Contact sheet of named frames: python sheet2.py OUT COLS WIDTH name [name ...]
A name is a file in the arena worktree's godot/.shots (without .png) or a path.
Each frame is labelled with its name. OUT is written beside this script unless a path."""
import sys, os
from PIL import Image, ImageDraw

SHOTS = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a52b851395b3ab3f4\godot\.shots"
HERE = os.path.dirname(os.path.abspath(__file__))
out, cols, width = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
ims = []
for n in sys.argv[4:]:
    p = n if os.path.exists(n) else os.path.join(SHOTS, n + ".png")
    if not os.path.exists(p):
        print("missing", n); continue
    im = Image.open(p).convert("RGB")
    im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    label = os.path.splitext(os.path.basename(n))[0]
    d.rectangle([0, 0, 8 + 7 * len(label), 16], fill=(0, 0, 0))
    d.text((4, 2), label, fill=(255, 255, 0))
    ims.append(im)
rows = (len(ims) + cols - 1) // cols
h = max(im.height for im in ims)
sheet = Image.new("RGB", (cols * width, rows * h), (20, 20, 20))
for i, im in enumerate(ims):
    sheet.paste(im, ((i % cols) * width, (i // cols) * h))
dst = out if os.path.isabs(out) else os.path.join(HERE, out)
os.makedirs(os.path.dirname(dst), exist_ok=True)
sheet.save(dst, quality=90)
print(dst, sheet.size, len(ims), "frames")

