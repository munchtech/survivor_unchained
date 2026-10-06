"""The repaint's takes side by side: each key's four fitted takes at 160 and at 56 px on a slot,
with the shipped neighbours at 56 for scale."""
import os

from PIL import Image, ImageDraw

SCR = os.path.dirname(os.path.abspath(__file__))
ITEM = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa9c11f1e40170a4d\godot\art\ui\icons\item"
KEYS = ["red_cord", "lamp_glass", "scar_glass", "flask"]
NEIGH = ["lamp", "potion", "vial", "pelt", "fang"]
W = 4 * 176 + 4 * 72 + 16
sheet = Image.new("RGB", (W, len(KEYS) * 184 + 80), "#0e0c10")
dr = ImageDraw.Draw(sheet)
for r, k in enumerate(KEYS):
    y = r * 184
    for j in range(4):
        p = os.path.join(SCR, "uiart_fit", f"{k}_{j}", k + ".png")
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGBA")
        x = j * 176
        dr.rectangle((x + 4, y + 4, x + 172, y + 172), fill="#1b1820")
        big = im.resize((160, 160), Image.LANCZOS)
        sheet.paste(big, (x + 8, y + 8), big)
        dr.text((x + 8, y + 172), f"{k} {j}", fill="#c8bca8")
        sx = 4 * 176 + j * 72
        dr.rectangle((sx + 4, y + 50, sx + 68, y + 114), fill="#1b1820")
        sm = im.resize((56, 56), Image.LANCZOS)
        sheet.paste(sm, (sx + 8, y + 54), sm)
for i, n in enumerate(NEIGH):
    im = Image.open(os.path.join(ITEM, n + ".png")).convert("RGBA").resize((56, 56), Image.LANCZOS)
    x, y = 8 + i * 72, len(KEYS) * 184 + 8
    dr.rectangle((x - 4, y - 4, x + 60, y + 60), fill="#1b1820")
    sheet.paste(im, (x, y), im)
out = os.path.join(SCR, "uiart_judge3.png")
sheet.save(out)
print(out)
