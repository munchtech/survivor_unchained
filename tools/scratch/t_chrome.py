import sys
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\uiforge")
import preview as PV
from PIL import Image, ImageDraw, ImageFont
UI = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\godot\art\ui"
SCR = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad"
photos = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\godot\art\ui\icons\item"
FONT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\comfy\out\uiforge\fonts\alegreya-sans-700.ttf"
fnt = ImageFont.truetype(FONT, 15)
bg = Image.new("RGBA", (900, 520), (24, 21, 28, 255))
d = ImageDraw.Draw(bg)
def put(rel, size, margins, at, tile=True):
    im = PV.halve(Image.open(UI + "\\" + rel))
    bg.alpha_composite(PV.nine(im, size, margins, tile=tile), at)
names = ["slot", "slot_common", "slot_uncommon", "slot_rare", "slot_epic", "slot_legendary", "slot_relic"]
items = [None, "potion", "ring", "helm", "armor_heavy", "staff", "ember"]
for i, n in enumerate(names):
    put("frames/" + n + ".png", (80, 80), (10, 10, 10, 10), (10 + i * 90, 10), tile=False)
    if items[i]:
        it = Image.open(photos + "\\" + items[i] + ".png").convert("RGBA").resize((68, 68), Image.LANCZOS)
        bg.alpha_composite(it, (10 + i * 90 + 6, 16))
put("frames/weapon_slot.png", (67, 67), (12, 12, 12, 12), (650, 10))
put("frames/chip.png", (32, 32), (8, 8, 8, 8), (730, 10))
put("frames/keycap.png", (24, 22), (6, 6, 6, 6), (780, 10)); d.text((787, 12), "C", font=fnt, fill=(243, 217, 160))
put("frames/tab.png", (80, 36), (14, 10, 14, 6), (10, 110)); d.text((30, 118), "Pack", font=fnt, fill=(243, 217, 160))
put("frames/tab_on.png", (80, 36), (14, 10, 14, 6), (95, 110)); d.text((118, 118), "Self", font=fnt, fill=(255, 255, 255))
put("frames/segment_on.png", (60, 28), (10, 8, 10, 8), (190, 114)); d.text((208, 118), "All", font=fnt, fill=(42, 26, 12))
put("frames/row_on.png", (300, 44), (12, 10, 12, 10), (270, 108)); d.text((290, 120), "Blink  ·  in hand", font=fnt, fill=(243, 217, 160))
put("frames/toast.png", (300, 48), (14, 10, 10, 10), (10, 170)); d.text((40, 184), "A new thing is written", font=fnt, fill=(243, 217, 160))
put("frames/prompt.png", (240, 40), (22, 12, 22, 12), (330, 172)); d.text((360, 182), "E  Talk  Mother Rook", font=fnt, fill=(243, 217, 160))
put("frames/tooltip.png", (300, 200), (16, 16, 16, 16), (10, 240)); d.text((30, 256), "Rimed Silver Ring", font=fnt, fill=(192, 112, 255))
put("frames/tooltip_worn.png", (300, 200), (16, 16, 16, 16), (320, 240)); d.text((340, 256), "WORN NOW", font=fnt, fill=(168, 156, 136))
put("bars/track.png", (360, 26), (8, 6, 8, 6), (640, 120))
fill = PV.halve(Image.open(UI + r"\bars\health_fill.png"))
f = Image.new("RGBA", (300, 24))
for xx in range(0, 300, fill.width): f.paste(fill.resize((fill.width, 24)), (xx, 0))
bg.alpha_composite(f, (641, 121))
put("bars/casing.png", (372, 38), (12, 8, 12, 8), (634, 114))
bg.resize((1800, 1040), Image.LANCZOS).save(SCR + r"\chrome_sheet.png")
