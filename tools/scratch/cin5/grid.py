"""A labelled grid of stills: python grid.py OUT TILE_W COLS PATTERN... (globs under the worktree's .shots,
in the order given). A pattern may end in @x0,y0,x1,y1 to crop each still (pixels of the 1920x1080 frame)."""
import glob, os, sys
from PIL import Image, ImageDraw

SHOTS = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aece7b87e89b13f19\godot\.shots"
out, tw, cols = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
tiles = []
for pat in sys.argv[4:]:
    crop = None
    if "@" in pat:
        pat, c = pat.split("@")
        crop = tuple(int(v) for v in c.split(","))
    for f in sorted(glob.glob(os.path.join(SHOTS, pat))):
        im = Image.open(f).convert("RGB")
        if crop:
            im = im.crop(crop)
        h = int(im.height * tw / im.width)
        im = im.resize((tw, h), Image.LANCZOS)
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, tw, 16), fill=(0, 0, 0))
        d.text((4, 2), os.path.basename(f), fill=(255, 255, 0))
        tiles.append(im)
if not tiles:
    sys.exit("no stills")
rows = (len(tiles) + cols - 1) // cols
th = max(t.height for t in tiles)
sheet = Image.new("RGB", (cols * tw, rows * th), (20, 20, 20))
for i, t in enumerate(tiles):
    sheet.paste(t, ((i % cols) * tw, (i // cols) * th))
sheet.save(out, quality=90)
print(out, sheet.size, len(tiles))
