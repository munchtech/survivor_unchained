import sys
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\uiforge")
import cards, preview as PV
from PIL import Image
SCR = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad"
SRC = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\comfy\out\uiforge\card_v2_60\card_v2_60_202_1.png"
cards.fit(SRC, SCR + r"\card_common.png")
im = Image.open(SCR + r"\card_common.png")
bg = Image.open(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\godot\.shots\t1_draft_pad.png").convert("RGBA")
sh = PV.halve(im)
for x in (452, 800, 1148):
    bg.alpha_composite(sh, (x - 14, 278 - 14))
bg.save(SCR + r"\card_ctx.png")
bg.crop((420, 240, 1160, 770)).save(SCR + r"\card_ctx_crop.png")
