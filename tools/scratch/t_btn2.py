import sys
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\uiforge")
import preview as PV
from PIL import Image, ImageDraw, ImageFont
UI = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\godot\art\ui\frames"
SCR = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad"
FONT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\comfy\out\uiforge\fonts\alegreya-sans-700.ttf"
fnt = ImageFont.truetype(FONT, 16)
names = ["button", "button_hover", "button_pressed", "button_disabled", "button_primary", "button_primary_hover", "button_primary_pressed"]
bg = Image.new("RGBA", (4 * 170 + 20, 130), (22, 19, 26, 255))
d = ImageDraw.Draw(bg)
for i, n in enumerate(names):
    im = PV.halve(Image.open(UI + "\\" + n + ".png"))
    b = PV.nine(im, (150, 36), (12, 10, 12, 10), tile=True)
    x, y = 10 + (i % 4) * 170, 10 + (i // 4) * 60
    bg.alpha_composite(b, (x, y))
    txt = "Begin" if "primary" in n else "Close"
    col = (255, 228, 176) if "primary" in n else (243, 217, 160)
    if "disabled" in n: col = (150, 140, 115)
    if "hover" in n or "pressed" in n: col = (255, 255, 255)
    tw = d.textlength(txt, font=fnt)
    d.text((x + 75 - tw / 2, y + 8), txt, font=fnt, fill=col)
bg.resize((bg.width * 2, bg.height * 2), Image.LANCZOS).save(SCR + r"\btn2.png")
