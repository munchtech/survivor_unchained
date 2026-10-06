import sys, json
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\uiforge")
import blrender, forge as F
from PIL import Image
SCR = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad"
name = sys.argv[1]
spec = json.load(open(SCR + "\\" + name + ".json"))
img, raw = blrender.render(spec, name)
im = Image.open(raw).convert("RGBA")
bg = Image.new("RGBA", im.size, (70, 60, 50, 255))
bg.alpha_composite(im)
bg.save(SCR + "\\" + name + "_full.png")
bg.crop((0, 0, min(512, im.width), min(512, im.height))).save(SCR + "\\" + name + "_tl.png")
F.to_pil(img).save(SCR + "\\" + name + "_file.png")
