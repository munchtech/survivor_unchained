import sys
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\uiforge")
import valueglyphs as V, preview as PV
import numpy as np
from PIL import Image
SCR = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad"
made = V.build(SCR + r"\value")
big = PV.sheet([m.resize((96, 96), Image.LANCZOS) for m in made.values()], cols=13, bg=(30, 27, 34))
tint = (243, 217, 160)
small = []
for m in made.values():
    a = np.asarray(m.resize((17, 17), Image.LANCZOS), np.float32) / 255
    a[..., :3] *= np.array(tint) / 255
    small.append(Image.fromarray((a * 255).astype(np.uint8), "RGBA"))
row = PV.sheet(small, cols=13, pad=5, bg=(21, 19, 26))
out = Image.new("RGBA", (big.width, big.height + row.height * 3 + 10), (0, 0, 0, 255))
out.alpha_composite(big, (0, 0))
out.alpha_composite(row.resize((row.width * 3, row.height * 3), Image.NEAREST), (0, big.height + 10))
out.save(SCR + r"\value_sheet.png")
