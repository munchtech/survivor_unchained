import sys, math, time
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\uiforge")
import numpy as np
from PIL import Image
import forge as F, frames as FR, ornament as O, preview as PV

SCR = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad"
SHOTS = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\godot\.shots"
V = sys.argv[1] if len(sys.argv) > 1 else "s1"
OUT = 14
M = 28 + OUT

st = FR.Style(out=OUT, strap=24, strap_h=6, wire=12, wire_w=3.4, facet_cell=12, facet_tilt=0.075, rivets=1, seed=5, paint=0.0)
pieces = []
if len(sys.argv) > 2:
    pieces = [dict(img=Image.open(sys.argv[2]).convert("RGBA"), box=(2, 2, 84, 84), corner="all", shadow=4)]
t = time.time()
img = FR.frame(512 + 2 * OUT * 2 - 56, 512 + 2 * OUT * 2 - 56, (M, M, M, M), st, ss=2, pieces=pieces)
print("built", time.time() - t, img.size)
img.save(SCR + rf"\plate_{V}.png")
shown = PV.halve(img)
big = PV.nine(shown, (1500 + 2 * OUT, 790 + 2 * OUT), (M, M, M, M), tile=True)
bg = Image.open(SHOTS + r"\base_char.png").convert("RGBA")
comp = PV.over(bg, big, (210 - OUT, 145 - OUT))
comp.save(SCR + rf"\plate_{V}_ctx.png")
comp.crop((170, 90, 170 + 480, 90 + 270)).resize((960, 540), Image.LANCZOS).save(SCR + rf"\plate_{V}_zoom.png")
img.crop((0, 0, 160, 160)).resize((480, 480), Image.LANCZOS).save(SCR + rf"\plate_{V}_corner.png")
