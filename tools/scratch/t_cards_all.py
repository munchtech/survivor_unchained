import sys
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\uiforge")
import cards, preview as PV, batch
from PIL import Image
R = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\comfy\out\uiforge" + "\\"
UI = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\godot\art\ui\frames" + "\\"
SCR = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad" + "\\"
CORNER_L, CORNER_R = (56, 944), (680, 944)
picks = {
    "common": (R + r"card_v3\card_v3_401_3.png", ()),
    "uncommon": (R + r"card_uncommon\card_uncommon_600_1.png", ()),
    "rare": (R + r"card2_rare\card2_rare_650_1.png", ()),
    "epic": (R + r"card_epic\card_epic_602_0.png", (((98, 852, 150, 902), (-1000, -1000)), ((606, 852, 658, 902), (-1000, -1000)))),
    "legendary": (R + r"card2_legendary\card2_legendary_651_0.png", (((76, 866, 154, 952), CORNER_L), ((598, 866, 677, 952), CORNER_R))),
    "evolution": (R + r"card2_evolution\card2_evolution_652_2.png", ()),
}
only = sys.argv[1:] or list(picks)
for kind in only:
    src, coins = picks[kind]
    cards.fit(src, UI + f"card_{kind}.png", kind=kind, hole_light=0.35 if kind != "common" else 0.55, coins=coins, heal_prompt=(batch.RARITY.get(kind, "") + ". " + batch.S) if coins else None)
    print(kind, flush=True)
ims = [PV.halve(Image.open(UI + f"card_{k}.png")) for k in picks]
PV.sheet(ims, cols=6, bg=(30, 26, 22)).save(SCR + "cards_all.png")
