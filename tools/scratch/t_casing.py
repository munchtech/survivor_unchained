import sys
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\uiforge")
import smallforge as SF, forge as F, preview as PV
from PIL import Image
UI = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\godot\art\ui"
SCR = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad"
c = SF.casing()
F.save(c, UI + r"\bars\casing.png")
fill = PV.halve(Image.open(UI + r"\bars\ember_fill.png"))
hp = PV.halve(Image.open(UI + r"\bars\health_fill.png"))
tr = PV.halve(Image.open(UI + r"\bars\track.png"))
bg = Image.new("RGBA", (700, 120), (40, 44, 36, 255))
def bar(x, y, w, h, fl, k):
    bg.alpha_composite(PV.nine(tr, (w, h), (8, 6, 8, 6), tile=True), (x, y))
    f = Image.new("RGBA", (int((w - 2) * k), h - 2))
    for xx in range(0, f.width, fl.width):
        f.paste(fl.resize((fl.width, h - 2)), (xx, 0))
    bg.alpha_composite(f, (x + 1, y + 1))
    bg.alpha_composite(PV.nine(PV.halve(c), (w + 12, h + 12), (12, 8, 12, 8), tile=True), (x - 6, y - 6))
bar(20, 20, 640, 12, fill, 0.6)
bar(20, 60, 362, 26, hp, 0.85)
bg.resize((1400, 240), Image.LANCZOS).save(SCR + r"\casing_test.png")
