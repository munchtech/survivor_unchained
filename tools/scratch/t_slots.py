import sys
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\uiforge")
import smallforge as SF, preview as PV
from PIL import Image
SCR = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad"
ims = [SF.slot(None)] + [SF.slot(r) for r in range(6)]
for i, im in enumerate(ims):
    im.save(SCR + f"\\slot_{i}.png")
photos = r"C:\Users\munch\AppData\Roaming\Godot\app_userdata\Survivor Unchained\icons"
items = [None, "potion", "ring", "helm", "armor_heavy", "staff", "ember"]
bg = Image.new("RGBA", (7 * 90 + 20, 110), (24, 21, 28, 255))
for i, im in enumerate(ims):
    sh = PV.nine(PV.halve(im), (80, 80), (10, 10, 10, 10))
    bg.alpha_composite(sh, (10 + i * 90, 15))
    if items[i]:
        it = Image.open(photos + "\\" + items[i] + ".v1.png").convert("RGBA").resize((69, 69), Image.LANCZOS)
        bg.alpha_composite(it, (10 + i * 90 + 6, 15 + 4))
bg.resize((bg.width * 2, bg.height * 2), Image.LANCZOS).save(SCR + r"\slots_proc.png")
