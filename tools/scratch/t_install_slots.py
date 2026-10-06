import sys
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\uiforge")
import smallforge as SF, forge as F
UI = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\godot\art\ui"
names = ["common", "uncommon", "rare", "epic", "legendary", "relic"]
F.save(SF.slot(None), UI + r"\frames\slot.png")
for r, n in enumerate(names):
    F.save(SF.slot(r), UI + rf"\frames\slot_{n}.png")
F.save(SF.track(256, 40, (24, 8, 24, 8)), UI + r"\bars\track_boss.png")
print("ok")
