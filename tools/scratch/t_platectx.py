import sys
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\uiforge")
import preview as PV
from PIL import Image
SCR = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad"
SHOTS = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\godot\.shots"
name = sys.argv[1]
OUT, M = 12, 64
img = Image.open(SCR + "\\" + name + ".png")
sh = PV.halve(img)
big = PV.nine(sh, (1500 + 2 * OUT, 790 + 2 * OUT), (M, M, M, M), tile=True)
bg = Image.open(SHOTS + r"\base_char.png").convert("RGBA")
comp = PV.over(bg, big, (210 - OUT, 145 - OUT))
comp.save(SCR + "\\" + name + "_ctx.png")
comp.crop((170, 90, 170 + 640, 90 + 360)).resize((1280, 720), Image.LANCZOS).save(SCR + "\\" + name + "_zoom.png")
small = PV.nine(sh, (300 + 2 * OUT, 200 + 2 * OUT), (M, M, M, M), tile=True)
bg2 = Image.new("RGBA", (360, 260), (60, 70, 50, 255))
bg2.alpha_composite(small, (30 - OUT, 30 - OUT))
bg2.resize((720, 520), Image.LANCZOS).save(SCR + "\\" + name + "_small.png")
