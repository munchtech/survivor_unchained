"""python sheet.py OUT.jpg COLS WIDTH file1 file2 ...  (globs ok; labels each tile with its name)"""
import sys, glob, os
from PIL import Image, ImageDraw, ImageFont
out, cols, w = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
SH = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a59432fe3bfc6eb92\godot\.shots"
files = []
for a in sys.argv[4:]:
    g = sorted(glob.glob(a if os.path.isabs(a) else os.path.join(SH, a)))
    files += g
if not files: print("no files"); sys.exit(1)
ims = [Image.open(f).convert("RGB") for f in files]
h = int(w * ims[0].height / ims[0].width)
rows = (len(ims) + cols - 1) // cols
S = Image.new("RGB", (cols * w, rows * (h + 18)), (20, 20, 20))
d = ImageDraw.Draw(S)
try: font = ImageFont.truetype("arial.ttf", 13)
except Exception: font = None
for i, (im, f) in enumerate(zip(ims, files)):
    x, y = (i % cols) * w, (i // cols) * (h + 18)
    S.paste(im.resize((w, h), Image.LANCZOS), (x, y + 18))
    d.text((x + 4, y + 2), os.path.basename(f)[:-4], fill=(230, 230, 230), font=font)
S.save(out, quality=88)
print(out, S.size, len(ims))
