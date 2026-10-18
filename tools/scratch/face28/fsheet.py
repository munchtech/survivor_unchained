import os, sys
from PIL import Image, ImageDraw
S = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\.shots"
J = os.path.join(os.path.dirname(os.path.abspath(__file__)), "j")
def tile(f, box, label):
    im = Image.open(os.path.join(S, f)).convert("RGB")
    if im.size != (1920, 1080): label += " (frame %dx%d)" % im.size
    t = im.crop(box); d = ImageDraw.Draw(t); d.rectangle((0, 0, 8 + 7 * len(label), 16), fill=(0, 0, 0)); d.text((4, 3), label, fill=(255, 255, 0)); return t
def sheet(name, tiles, gap=6):
    w = sum(t.width for t in tiles) + gap * (len(tiles) - 1); h = max(t.height for t in tiles)
    out = Image.new("RGB", (w, h), (40, 40, 40)); x = 0
    for t in tiles: out.paste(t, (x, 0)); x += t.width + gap
    out.save(os.path.join(J, name + ".png")); print(name, out.size)
# cinematic face close-ups (boxes found on own; the cameras frame every face alike)
A5 = (600, 200, 1320, 960); A7 = (600, 200, 1320, 960)
C8 = (620, 140, 1340, 900); C4 = (230, 110, 950, 870); C8b = (620, 140, 1340, 900); C28 = (0, 110, 720, 870)
for f in ("own", "saffron", "sunborn"):
    p = lambda c, s, k: f"v_{c}_{f}_{c}_s{s}_{k}.png"
    sheet(f"cf_{f}_c04a_A5", [tile(p("c04a", "a5", 1), A5, f"{f} c04a A5 #1 (mouth_open rising to 0.25)"), tile(p("c04a", "a5", 2), A5, f"{f} c04a A5 #2 (open 0.25)")])
    if f == "own": sheet(f"cf_{f}_c04a_A5b_A7", [tile(p("c04a", "a5", 4), A5, f"{f} c04a A5 #4 (squint .2, frown .2)"), tile(p("c04a", "a7", 2), A7, f"{f} c04a A7 (brows_sad .45)")])
    if f == "own": sheet(f"cf_{f}_c01_s8", [tile(p("c01", "8", 3), C8, f"{f} c01 s8 (open .12, brows_sad .4)"), tile(p("c01", "8b", 3), C8b, f"{f} c01 s8b (85mm)")])
    sheet(f"cf_{f}_c02_s4_s8", [tile(p("c02", "4", 2), C4, f"{f} c02 s4 (85mm, night)"), tile(p("c02", "8", 2), C28, f"{f} c02 s8 (135mm, night)")])
LK = (720, 170, 1200, 790)
for t in ("day",):
    sheet(f"lk_rest_{t}", [tile(f"v_lk_{f}_{t}.png", LK, f"Look {f} rest --time {t}") for f in ("own", "saffron", "sunborn")])
