"""Contact sheet of a frame run: python sheet.py OUT COLS WIDTH NAME FIRST LAST [STEP]
Frames are godot/.shots/NAME_NN.png of the experience worktree, labelled with their number."""
import sys, os
from PIL import Image, ImageDraw

SHOTS = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ab03c3c85571e5085\godot\.shots"
out, cols, width, name, first, last = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], int(sys.argv[5]), int(sys.argv[6])
step = int(sys.argv[7]) if len(sys.argv) > 7 else 1
files = [os.path.join(SHOTS, f"{name}_{i:02d}.png") for i in range(first, last + 1, step)]
files = [f for f in files if os.path.exists(f)]
ims = []
for f in files:
    im = Image.open(f).convert("RGB")
    h = int(im.height * width / im.width)
    im = im.resize((width, h), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 60, 16], fill=(0, 0, 0))
    d.text((4, 2), os.path.basename(f)[len(name) + 1:-4], fill=(255, 255, 0))
    ims.append(im)
rows = (len(ims) + cols - 1) // cols
h = ims[0].height
sheet = Image.new("RGB", (cols * width, rows * h), (20, 20, 20))
for i, im in enumerate(ims):
    sheet.paste(im, ((i % cols) * width, (i // cols) * h))
sheet.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), out))
print(out, sheet.size, len(ims), "frames")

