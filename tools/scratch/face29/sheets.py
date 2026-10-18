"""Face 29 hair sheets: every tile a 1:1 crop of a native 1920x1080 frame; every sheet <= 1568 px wide and <= 1.15 MP
(so the judge's viewer shows it at 1:1, not downscaled)."""
import os, sys
from PIL import Image, ImageDraw
S = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\.shots"
R = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\59f6a467-b8ce-446c-8f35-44c1d92b7b9a\scratchpad\s29\shots"
J = os.path.join(os.path.dirname(os.path.abspath(__file__)), sys.argv[1] if len(sys.argv) > 1 else "j")
os.makedirs(J, exist_ok=True)
def tile(f, box, label, src=S):
    im = Image.open(os.path.join(src, f)).convert("RGB")
    if im.size != (1920, 1080): label += " (frame %dx%d)" % im.size
    t = im.crop(box); d = ImageDraw.Draw(t); d.rectangle((0, 0, 8 + 7 * len(label), 16), fill=(0, 0, 0)); d.text((4, 3), label, fill=(255, 255, 0)); return t
def sheet(name, tiles, gap=6):
    w = sum(t.width for t in tiles) + gap * (len(tiles) - 1); h = max(t.height for t in tiles)
    assert w <= 1568 and w * h <= 1.16e6, (name, w, h)
    out = Image.new("RGB", (w, h), (40, 40, 40)); x = 0
    for t in tiles: out.paste(t, (x, 0)); x += t.width + gap
    out.save(os.path.join(J, name + ".png")); print(name, out.size)
STY = ["long", "ponytail", "braid", "bob", "pixie"]
LK = (640, 30, 1180, 1070)  # the Look's Hair part: her figure between the two panels, head to hips
for s in STY:
    for a, b in ((0, 45), (90, 135), (180, 225), (270, 315)):
        sheet(f"lk_{s}_turn{a:03d}", [tile(f"h_lk_{s}_t{d:03d}.png", LK, f"Look {s} turned {d} (rest)") for d in (a, b)])
    for a, b in ((1, 3), (5, 7)):
        sheet(f"lk_{s}_spin{a}", [tile(f"h_lk_{s}_spin_{k:02d}.png", LK, f"Look {s} SPINNING 90/s #{k}") for k in (a, b)])
MV = (720, 40, 1200, 800); MA = (720, 0, 1200, 760); PL = (720, 160, 1200, 920)
for s in STY:
    sheet(f"cu_{s}_across", [tile(f"r_cu_day_{s}_across_{k:02d}.png", MV, f"close-up day {s} run+turn #{k} (Reaver)") for k in (2, 5, 9)])
for s in ("long", "ponytail", "braid"):
    sheet(f"cu_{s}_away", [tile(f"r_cu_day_{s}_away_{k:02d}.png", MA, f"close-up day {s} running away #{k} (Reaver)") for k in (1, 5, 9)])
    sheet(f"cu_{s}_night", [tile(f"r_cu_night_{s}_across_{k:02d}.png", MV, f"close-up NIGHT {s} run+turn #{k} (Reaver)") for k in (2, 5, 9)])
sheet("cu_hat", [tile(f"h_cu_day_long_across_{k:02d}.png", MV, f"close-up day long, Arcanist hat #{k}") for k in (2, 9)] + [tile("h_cu_day_bob_across_05.png", MV, "close-up day bob, Arcanist hat #5")])
sheet("cu_mid_away", [tile(f"h_cm_day_{s}_away_03.png", MA, f"close-up zoom .5 away, {s} (camera inside her: ignore)") for s in ("long", "ponytail", "braid")])
sheet("far", [tile("h_pl_day_long_across_02.png", PL, "play camera day long run"), tile("h_pl_night_ponytail_away_03.png", PL, "play camera NIGHT ponytail away"), tile("h_fight_long_08.png", PL, "play camera fight long")])
sheet("cine_back_1", [tile("h_c02_long_c02_s7_2.png", (840, 300, 1340, 1060), "c02 s7 walk to warden, long"), tile("h_c02_braid_c02_s7_2.png", (840, 300, 1340, 1060), "c02 s7 braid"), tile("v_c02_own_c02_s1_2.png", (0, 300, 500, 1060), "c02 s1 walking in, ponytail")])
sheet("cine_back_2", [tile("h_c03_long_c03_s2_2.png", (1420, 250, 1920, 1010), "c03 s2 walk-up, long"), tile("h_c03_braid_c03_s5_2.png", (540, 300, 1040, 1060), "c03 s5 walk to warden, braid"), tile("v_c01_own_c01_s7_2.png", (0, 320, 500, 1080), "c01 s7 back of head, ponytail")])
sheet("reaver_sprint", [tile("rv_sprint_cu_f3.png", (440, 330, 1040, 1080), "outfits' frame: Reaver sprint close-up f3 (claimed hair sheet over the swung arm)", R)])
