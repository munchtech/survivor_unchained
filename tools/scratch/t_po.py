import sys
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\uiforge")
import numpy as np
from PIL import Image
import paintover as PO, forge as F, preview as PV
SCR = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad"
src = Image.open(SCR + r"\spec_plate_file.png").convert("RGBA")
rgba = np.asarray(src, np.float32) / 255
prompt = ("an empty square window frame of hand-forged blackened iron strap, heavy hammer marks, pitted and worn, "
          "a twisted gold wire inlaid along it, square iron coins nailed at the corners with a faint ember glow in their holes, "
          "the inside plain dark iron, isolated on a pure black background, seen straight on")
cells = []
for d in (0.28, 0.38, 0.48):
    out = PO.paint(rgba, prompt, f"plate_d{int(d*100)}", denoise=d, seed=7)
    im = F.to_pil(out)
    im.save(SCR + f"\\po_{int(d*100)}.png")
    cells.append(im.crop((0, 0, 256, 256)).resize((384, 384), Image.LANCZOS))
cells.insert(0, src.crop((0, 0, 256, 256)).resize((384, 384), Image.LANCZOS))
bg = PV.sheet(cells, cols=4, bg=(70, 60, 50))
bg.save(SCR + r"\po_sheet.png")
