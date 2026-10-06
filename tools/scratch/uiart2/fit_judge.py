"""Fit each of the four icons' takes (seed 1130) into scratch, then a judging sheet: each take
at 160 and at 56 px on a dark slot, with the shipped neighbours at 56."""
import os
import sys

from PIL import Image, ImageDraw

WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748"
SCR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(WT, "tools", "uiforge"))
os.chdir(os.path.join(WT, "tools", "uiforge"))
import items  # noqa: E402

KEYS = ["red_cord", "lamp_glass", "scar_glass", "flask"]
for k in KEYS:
    for j in range(4):
        items.OUT = os.path.join(SCR, "fit", f"{k}_{j}")
        items.fit(k, (1130, j))
ITEM = os.path.join(WT, "godot", "art", "ui", "icons", "item")
NEIGH = ["lamp", "potion", "vial", "pelt", "fang", "flask"]
W = 4 * 176 + 4 * 72 + 16
sheet = Image.new("RGB", (W, len(KEYS) * 184 + 80), "#0e0c10")
dr = ImageDraw.Draw(sheet)
for r, k in enumerate(KEYS):
    y = r * 184
    for j in range(4):
        im = Image.open(os.path.join(SCR, "fit", f"{k}_{j}", k + ".png")).convert("RGBA")
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
    p = os.path.join(ITEM, n + ".png")
    if not os.path.exists(p):
        continue
    im = Image.open(p).convert("RGBA").resize((56, 56), Image.LANCZOS)
    x, y = 8 + i * 72, len(KEYS) * 184 + 8
    dr.rectangle((x - 4, y - 4, x + 60, y + 60), fill="#1b1820")
    sheet.paste(im, (x, y), im)
sheet.save(os.path.join(SCR, "judge_icons.png"))
print("ok")
