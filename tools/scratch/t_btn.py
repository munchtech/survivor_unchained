import sys, time
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\uiforge")
import buttons as B, preview as PV
from PIL import Image, ImageDraw, ImageFont
SCR = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad"
t = time.time()
ims = []
for prim in (False, True):
    for stt in ("normal", "hover", "pressed", "disabled"):
        if prim and stt == "disabled":
            continue
        ims.append(B.button(stt, prim))
print(time.time() - t)
PV.sheet(ims, cols=4).save(SCR + r"\btn_sheet.png")
# In context: shown size, stretched to 150x36 and 96x32, on the plate tone.
fnt = ImageFont.truetype(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\comfy\out\uiforge\fonts\alegreya-sans-700.ttf", 16)
row = Image.new("RGBA", (5 * 170 + 20, 120), (22, 19, 26, 255))
for i, im in enumerate(ims):
    sh = PV.halve(im)
    b = PV.nine(sh, (150, 36), (12, 10, 12, 10), tile=True)
    x, y = 10 + (i % 4) * 170 + (i // 4) * 0, 10 + (i // 4) * 54
    row.alpha_composite(b, (x, y))
    d = ImageDraw.Draw(row)
    txt = ["Close", "Close", "Close", "Close", "Begin", "Begin", "Begin"][i]
    col = (243, 217, 160) if i < 4 else (255, 228, 176)
    if i == 3: col = (150, 140, 115)
    if i in (1, 2, 5, 6): col = (255, 255, 255)
    tw = d.textlength(txt, font=fnt)
    d.text((x + 75 - tw / 2, y + 8), txt, font=fnt, fill=col)
row.resize((row.width * 2, row.height * 2), Image.LANCZOS).save(SCR + r"\btn_ctx.png")
