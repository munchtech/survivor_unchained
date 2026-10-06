import sys, glob, os
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\uiforge")
import preview as PV
from PIL import Image, ImageDraw, ImageFont
SCR = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad"
RAW = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\comfy\out\uiforge\icons"
FONT = ImageFont.truetype(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\comfy\out\uiforge\fonts\alegreya-sans-700.ttf", 14)
keys = sorted({os.path.basename(p).rsplit("_900_", 1)[0] for p in glob.glob(RAW + r"\*_900_*.png")})
if sys.argv[1].isdigit():
    start, count = int(sys.argv[1]), int(sys.argv[2])
    sel = keys[start:start + count]
else:
    start, sel = "named", sys.argv[1:]
cells = []
for k in sel:
    cell = Image.new("RGBA", (300, 166), (20, 18, 24, 255))
    for j in range(2):
        p = RAW + f"\\{k}_900_{j}.png"
        if os.path.exists(p):
            cell.paste(Image.open(p).convert("RGBA").resize((140, 140)), (5 + j * 150, 22))
    ImageDraw.Draw(cell).text((6, 3), k, font=FONT, fill=(240, 220, 170))
    cells.append(cell)
PV.sheet(cells, cols=6, pad=4).save(SCR + f"\\iconpick_{start}.png")
print(len(keys))
