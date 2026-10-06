"""Contact sheet of a shot run: python sheet.py NAME OUT [x0,y0,x1,y1 w h]... (each crop resized to w x h)."""
import glob
import sys
from PIL import Image, ImageDraw

SHOTS = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a565196002a51af40\godot\.shots'
name, out = sys.argv[1], sys.argv[2]
crops = []
for spec in sys.argv[3:]:
    box, w, h = spec.split(':')
    crops.append((tuple(int(v) for v in box.split(',')), int(w), int(h)))
fs = sorted(glob.glob(f'{SHOTS}\\{name}_*.png'))
cw = sum(w for _, w, _ in crops)
ch = max(h for _, _, h in crops) + 14
cols = max(1, 2000 // cw)
rows = (len(fs) + cols - 1) // cols
sheet = Image.new('RGB', (cw * cols, ch * rows), 'black')
for i, f in enumerate(fs):
    a = Image.open(f).convert('RGB')
    x = 0
    cell = Image.new('RGB', (cw, ch))
    for box, w, h in crops:
        cell.paste(a.crop(box).resize((w, h)), (x, 0))
        x += w
    ImageDraw.Draw(cell).text((4, ch - 13), str(i), fill='yellow')
    sheet.paste(cell, ((i % cols) * cw, (i // cols) * ch))
sheet.save(out)
print(len(fs), 'frames')
