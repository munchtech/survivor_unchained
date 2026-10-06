import sys
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\uiforge")
import guides2 as G
import preview as PV
SCR = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad"
RAW = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\comfy\out\uiforge\guides"
import os
os.makedirs(RAW, exist_ok=True)
gs = {
    "slot": G.generic(80, 80, scale=8, strap=7, corners="rivet", corner_size=3.5, recess=True, wire=False),
    "wslot": G.generic(67, 67, scale=10, strap=6, corners="coin", corner_size=11, recess=True),
    "chip": G.generic(32, 32, scale=16, strap=4, corners="rivet", corner_size=2.4, wire=False, radius=4),
    "toast": G.generic(128, 48, scale=6, strap=5, corners="coin", corner_size=10, chamfer=4),
    "prompt": G.generic(128, 40, scale=6, strap=4, corners="none", radius=19),
    "button": G.generic(96, 32, scale=8, strap=4.5, corners="rivet", corner_size=2.2, chamfer=3),
    "tooltip": G.generic(128, 128, scale=6, strap=6, corners="coin", corner_size=9),
    "ring": G.ring(),
    "paper": G.paper(512, 512, scale=2),
    "hint": G.paper(512, 256, scale=2),
}
for n, g in gs.items():
    g.save(RAW + "\\" + n + ".png")
    print(n, g.size)
PV.sheet([g.resize((min(512, g.width), int(g.height * min(512, g.width) / g.width))) for g in gs.values()], cols=4, bg=(60, 60, 60)).save(SCR + r"\guides2.png")
