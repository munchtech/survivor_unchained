import sys, time
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\uiforge")
import padprompts as PP, preview as PV
from PIL import Image
SCR = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad"
t = time.time()
made = PP.build(SCR + r"\pad")
print(time.time() - t)
ims = list(made.values())
PV.sheet(ims, cols=9, bg=(30, 27, 34)).save(SCR + r"\pad_sheet.png")
# At real size: 26 px tall, on a dark footer.
small = []
for n, im in made.items():
    h = 26
    w = round(im.width * h / im.height)
    small.append(im.resize((w, h), Image.LANCZOS))
row = PV.sheet(small, cols=17, pad=6, bg=(21, 19, 26))
row.resize((row.width * 3, row.height * 3), Image.NEAREST).save(SCR + r"\pad_real_x3.png")
