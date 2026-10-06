import sys, glob, os
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\uiforge")
import icons, preview as PV
import numpy as np
from PIL import Image, ImageDraw
SCR = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad"
RAW = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\comfy\out\uiforge\icons"
keys = sys.argv[1:]
cells = []
for k in keys:
    for j in range(2):
        src = RAW + f"\\{k}_900_{j}.png"
        if not os.path.exists(src):
            continue
        dst = SCR + f"\\ic\\{k}_{j}.png"
        icons.fit(src, dst)
        im = Image.open(dst).convert("RGBA")
        # On the draft's disc (68 px on a dark disc), at 28 and at 17.
        cell = Image.new("RGBA", (190, 120), (22, 19, 26, 255))
        d = ImageDraw.Draw(cell)
        d.ellipse((4, 4, 116, 116), fill=(40, 28, 22, 255), outline=(200, 140, 80, 255), width=2)
        cell.alpha_composite(im.resize((68, 68), Image.LANCZOS), (26, 26))
        cell.alpha_composite(im.resize((28, 28), Image.LANCZOS), (124, 20))
        cell.alpha_composite(im.resize((17, 17), Image.LANCZOS), (130, 70))
        cells.append(cell)
PV.sheet(cells, cols=4, pad=4).save(SCR + r"\icons_test.png")
