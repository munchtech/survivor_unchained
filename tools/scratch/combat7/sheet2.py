"""Contact sheet of named frames: python sheet2.py OUT COLS WIDTH PREFIX tag1 tag2 ... (or a glob with *)
Frames are godot/.shots/PREFIX_TAG.png in the combat worktree, each labelled with its tag.
--crop x0,y0,x1,y1 crops each frame first (full-resolution pixels)."""
import sys, os, glob
from PIL import Image, ImageDraw

SHOTS = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a427a874da78cba8b\godot\.shots"
args = sys.argv[1:]
crop = None
if "--crop" in args:
    i = args.index("--crop"); crop = tuple(int(v) for v in args[i + 1].split(",")); args = args[:i] + args[i + 2:]
out, cols, width, prefix = args[0], int(args[1]), int(args[2]), args[3]
files = []
for t in args[4:]:
    if "*" in t: files += sorted(glob.glob(os.path.join(SHOTS, f"{prefix}_{t}.png")), key=lambda f: (len(f), f))
    else: files.append(os.path.join(SHOTS, f"{prefix}_{t}.png"))
files = [f for f in files if os.path.exists(f)]
ims = []
for f in files:
    im = Image.open(f).convert("RGB")
    if crop: im = im.crop(crop)
    h = int(im.height * width / im.width)
    im = im.resize((width, h), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    label = os.path.basename(f)[len(prefix) + 1:-4]
    d.rectangle([0, 0, 8 + 7 * len(label), 16], fill=(0, 0, 0))
    d.text((4, 2), label, fill=(255, 255, 0))
    ims.append(im)
rows = (len(ims) + cols - 1) // cols
h = ims[0].height
sheet = Image.new("RGB", (cols * width, rows * h), (20, 20, 20))
for i, im in enumerate(ims):
    sheet.paste(im, ((i % cols) * width, (i // cols) * h))
sheet.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), out))
print(out, sheet.size, len(ims), "frames")
