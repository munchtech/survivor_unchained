import sys
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\uiforge")
import smallforge as SF, preview as PV
from PIL import Image, ImageDraw, ImageFont
SCR = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad"
FONT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\comfy\out\uiforge\fonts\alegreya-sans-700.ttf"
kc, tr, seg, row, you = SF.keycap(), SF.track(), SF.segment_on(), SF.row_on(), SF.you_arrow()
for n, im in dict(keycap=kc, track=tr, segment_on=seg, row_on=row, you=you).items():
    im.save(SCR + "\\sf_" + n + ".png")
bg = Image.new("RGBA", (700, 260), (22, 19, 26, 255))
d = ImageDraw.Draw(bg)
f = ImageFont.truetype(FONT, 14)
bg.alpha_composite(PV.nine(PV.halve(kc), (24, 22), (6, 6, 6, 6)), (20, 20)); d.text((28, 22), "C", font=f, fill=(243, 217, 160))
bg.alpha_composite(PV.nine(PV.halve(kc), (40, 22), (6, 6, 6, 6)), (60, 20)); d.text((66, 22), "Enter", font=f, fill=(243, 217, 160))
bg.alpha_composite(PV.nine(PV.halve(tr), (600, 12), (8, 6, 8, 6), tile=True), (20, 60))
bg.alpha_composite(PV.nine(PV.halve(tr), (362, 26), (8, 6, 8, 6), tile=True), (20, 90))
bg.alpha_composite(PV.nine(PV.halve(seg), (60, 28), (10, 8, 10, 8)), (20, 130)); d.text((36, 134), "All", font=f, fill=(42, 26, 12))
bg.alpha_composite(PV.nine(PV.halve(row), (300, 44), (12, 10, 12, 10)), (100, 130)); d.text((120, 142), "Hunter", font=f, fill=(243, 217, 160))
bg.alpha_composite(PV.halve(you), (20, 200))
bg.resize((1400, 520), Image.LANCZOS).save(SCR + r"\small_test.png")
