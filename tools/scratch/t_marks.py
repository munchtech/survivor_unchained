import sys
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\uiforge")
import mapmarks as M, preview as PV
from PIL import Image
SCR = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad"
made = M.build(SCR + r"\marks")
big = PV.sheet(list(made.values()), cols=7, bg=(40, 36, 44))
small = []
for sz in (22, 15):
    small += [im.resize((sz, sz), Image.LANCZOS) for im in made.values()]
row_dark = PV.sheet(small, cols=7, pad=6, bg=(21, 19, 26))
row_paper = PV.sheet(small, cols=7, pad=6, bg=(217, 203, 168))
out = Image.new("RGBA", (max(big.width, row_dark.width * 4), big.height + row_dark.height * 8 + 20), (0, 0, 0, 255))
out.alpha_composite(big, (0, 0))
out.alpha_composite(row_dark.resize((row_dark.width * 4, row_dark.height * 4), Image.NEAREST), (0, big.height + 10))
out.alpha_composite(row_paper.resize((row_paper.width * 4, row_paper.height * 4), Image.NEAREST), (0, big.height + 20 + row_dark.height * 4))
out.save(SCR + r"\marks_sheet.png")
