import sys
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\uiforge")
import paper, forge as F, preview as PV
from PIL import Image, ImageDraw, ImageFont
SCR = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad"
p = paper.sheet(512, 512, (32, 32, 32, 32), seed=3)
F.to_pil(p).save(SCR + r"\paper_new.png")
hnt = paper.sheet(512, 256, (40, 40, 40, 40), seed=5, corners=False, nail=True, wax=True, tone="#e6d6b0")
F.to_pil(hnt).save(SCR + r"\hint_new.png")
bg = Image.open(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\godot\.shots\s3_journal.png").convert("RGBA")
pv = PV.nine(PV.halve(F.to_pil(p)), (1240, 686), (32, 32, 32, 32), tile=True)
bg.alpha_composite(pv, (340, 214))
hv = PV.nine(PV.halve(F.to_pil(hnt)), (380, 130), (40, 40, 40, 40), tile=True)
bg.alpha_composite(hv, (40, 820))
d = ImageDraw.Draw(bg)
f = ImageFont.truetype(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\comfy\out\uiforge\fonts\alegreya-700.ttf", 18)
d.text((370, 250), "Nothing written yet. What people ask of you is written here.", font=f, fill=(42, 33, 24))
d.text((70, 860), "SPACE  a quick roll", font=f, fill=(42, 33, 24))
bg.save(SCR + r"\paper_ctx.png")
bg.crop((300, 180, 940, 540)).resize((1280, 720), Image.LANCZOS).save(SCR + r"\paper_zoom.png")
