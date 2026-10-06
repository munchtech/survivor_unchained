import sys, time
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\uiforge")
import lightpieces as L, preview as PV
from PIL import Image
SCR = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad"
f = L.focus_ring()
e = L.ember_fill(); x = L.experience_fill(); hp = L.health_fill()
bg = Image.new("RGBA", (900, 300), (22, 19, 26, 255))
ring = PV.nine(PV.halve(f), (90, 90), (14, 14, 14, 14))
bg.alpha_composite(ring, (20, 20))
ring2 = PV.nine(PV.halve(f), (200, 48), (14, 14, 14, 14))
bg.alpha_composite(ring2, (140, 40))
def tile(im, W, H):
    sh = PV.halve(im)
    out = Image.new("RGBA", (W, H))
    for xx in range(0, W, sh.width):
        out.paste(sh.resize((sh.width, H)), (xx, 0))
    return out
bg.alpha_composite(tile(e, 600, 12), (20, 160))
bg.alpha_composite(tile(x, 600, 12), (20, 190))
bg.alpha_composite(tile(hp, 360, 24), (20, 220))
bg.resize((1800, 600), Image.LANCZOS).save(SCR + r"\light_test.png")
