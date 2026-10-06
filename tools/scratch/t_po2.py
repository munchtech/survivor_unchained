import sys
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\uiforge")
import numpy as np
from PIL import Image
import paintover as PO, forge as F, preview as PV, nineslice as N, chrome as CH
SCR = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad"
src = Image.open(SCR + r"\plate_b.png").convert("RGBA")
rgba = np.asarray(src, np.float32) / 255
prompt = ("an empty square window frame of hand-forged blackened iron strap, hammer marks, pitted and worn edges, soot "
          "in the corners, a thin twisted gold wire inlaid along it, at each corner a square iron coin with a round hole "
          "and a curled iron bracket, the inside plain flat dark iron, isolated on a pure black background, seen straight on")
for d in (0.30, 0.40):
    out = PO.paint(rgba, prompt, f"plateb_d{int(d*100)}", denoise=d, seed=11, keep_light=0.75)
    out = CH.calibrate(out, [128] * 4, "#16131a", [58] * 4)
    out = N.tileable(out, (128, 128, 128, 128), blend=12)
    F.to_pil(out).save(SCR + f"\\plate_p{int(d*100)}.png")
