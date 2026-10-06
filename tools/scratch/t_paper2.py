import sys
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\uiforge")
import numpy as np
import paper, forge as F, preview as PV, paintover as PO, painted as P, nineslice as N
from PIL import Image, ImageDraw, ImageFont
SCR = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad"


def make(W, H, margins, seed, prompt, tone, name, **kw):
    base = paper.sheet(W, H, margins, seed=seed, tone=tone, **kw)
    out = PO.paint(base, prompt, name, denoise=0.38, seed=21, keep_light=0.4)
    m = [v * 2 for v in margins]
    region = np.zeros((H, W), np.float32)
    region[m[1] + 8:H - m[3] - 8, m[0] + 8:W - m[2] - 8] = 1
    out[..., :3] = P.calm(out[..., :3], region, tone, keep=0.7, low=0.05, sigma=10, feather=10)
    out = N.tileable(out, tuple(m), blend=16)
    return out


p = make(512, 512, (32, 32, 32, 32), 3, "an old sheet of ledger parchment, warm cream, foxed and browned at the deckled edges, "
         "small blackened iron corner caps riveted on the four corners, the middle clean and even, flat lay, isolated on black",
         "#e4d6b6", "paper")
hnt = make(512, 256, (40, 40, 40, 40), 5, "a small note of old parchment, warm cream, browned at the deckled edges, pinned at the "
           "top left by a square iron nail, a drop of red sealing wax at the bottom right, the middle clean, flat lay, isolated on black",
           "#e6d6b0", "hint", corners=False, nail=True, wax=True)
F.to_pil(p).save(SCR + r"\paper_new.png")
F.to_pil(hnt).save(SCR + r"\hint_new.png")
bg = Image.open(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\godot\.shots\s3_journal.png").convert("RGBA")
bg.alpha_composite(PV.nine(PV.halve(F.to_pil(p)), (1240, 686), (32, 32, 32, 32), tile=True), (340, 214))
bg.alpha_composite(PV.nine(PV.halve(F.to_pil(hnt)), (380, 130), (40, 40, 40, 40), tile=True), (40, 820))
d = ImageDraw.Draw(bg)
f = ImageFont.truetype(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\comfy\out\uiforge\fonts\alegreya-700.ttf", 18)
d.text((370, 250), "Nothing written yet. What people ask of you is written here.", font=f, fill=(42, 33, 24))
d.text((70, 860), "SPACE  a quick roll", font=f, fill=(42, 33, 24))
bg.save(SCR + r"\paper_ctx.png")
