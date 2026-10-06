"""Sheet of named frames: python tsheet.py OUT COLS WIDTH FILE [FILE...] (names in .shots, .png optional)."""
import sys, os
from PIL import Image, ImageDraw

SHOTS = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-af2c026d86e1b532b\godot\.shots"
HERE = os.path.dirname(os.path.abspath(__file__))
out, cols, width = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
names = [f if f.endswith(".png") else f + ".png" for f in sys.argv[4:]]
files = [os.path.join(SHOTS, f) for f in names if os.path.exists(os.path.join(SHOTS, f))]
ims = []
for f in files:
    im = Image.open(f).convert("RGB")
    im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 170, 16], fill=(0, 0, 0))
    d.text((4, 2), os.path.basename(f)[:-4], fill=(255, 255, 0))
    ims.append(im)
rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGB", (cols * width, rows * ims[0].height), (20, 20, 20))
for i, im in enumerate(ims):
    sheet.paste(im, ((i % cols) * width, (i // cols) * im.height))
sheet.save(os.path.join(HERE, out))
print(out, sheet.size, len(ims))
