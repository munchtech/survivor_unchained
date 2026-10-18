import os
from PIL import Image
exec(open("fsheet.py").read().split("# cinematic")[0])
def grid(name, tiles, cols, scale=1.0, gap=6):
    w, h = tiles[0].width, tiles[0].height; rows = (len(tiles) + cols - 1) // cols
    out = Image.new("RGB", (cols * w + gap * (cols - 1), rows * h + gap * (rows - 1)), (40, 40, 40))
    for k, t in enumerate(tiles): out.paste(t, ((k % cols) * (w + gap), (k // cols) * (h + gap)))
    if scale != 1: out = out.resize((round(out.width * scale), round(out.height * scale)), Image.LANCZOS)
    out.save(os.path.join(J, name + ".png")); print(name, out.size)
STY = ["long", "ponytail", "braid", "bob", "pixie"]
LKH = (760, 60, 1180, 700)
for s in STY:
    grid(f"h_look_{s}_turns", [tile(f"h_lk_{s}_t{d:03d}.png", LKH, f"Look {s} turned {d} (at rest)") for d in range(0, 360, 45)], 4, 0.8)
    grid(f"h_look_{s}_spin", [tile(f"h_lk_{s}_spin_{k:02d}.png", LKH, f"Look {s} spinning 90/s #{k}") for k in range(8)], 4, 0.8)
MV = (720, 40, 1200, 800); MA = (720, 0, 1200, 760)
for s in STY:
    sheet(f"h_cu_{s}_across", [tile(f"r_cu_day_{s}_across_{k:02d}.png", MV, f"close-up day {s} run+turn #{k} (Reaver)") for k in (2, 5, 9)])
for s in ("long", "ponytail", "braid"):
    sheet(f"h_cu_{s}_away", [tile(f"r_cu_day_{s}_away_{k:02d}.png", MA, f"close-up day {s} running away #{k}") for k in (1, 5, 9)])
    sheet(f"h_cu_{s}_night", [tile(f"r_cu_night_{s}_across_{k:02d}.png", MV, f"close-up NIGHT {s} run+turn #{k}") for k in (2, 5, 9)])
sheet("h_misc_hat", [tile(f"h_cu_day_long_across_{k:02d}.png", MV, f"close-up day long, Arcanist hat #{k}") for k in (2, 9)] + [tile("h_cm_day_long_away_03.png", MA, "close-up zoom .5 running away (camera inside her)")])
sheet("h_misc_far", [tile("h_pl_day_long_across_02.png", (720, 160, 1200, 920), "play camera day long run"), tile("h_pl_night_ponytail_away_03.png", (720, 160, 1200, 920), "play camera NIGHT ponytail"), tile("h_fight_long_08.png", (720, 160, 1200, 920), "play camera fight long")])
sheet("h_cine_back_1", [tile("h_c02_long_c02_s7_2.png", (840, 300, 1360, 1060), "c02 s7 walk to warden, long"), tile("h_c02_braid_c02_s7_2.png", (840, 300, 1360, 1060), "c02 s7 braid"), tile("v_c02_own_c02_s1_2.png", (0, 300, 520, 1060), "c02 s1 walking in, ponytail")])
sheet("h_cine_back_2", [tile("h_c03_long_c03_s2_2.png", (1400, 250, 1920, 1010), "c03 s2 walk-up, long"), tile("h_c03_braid_c03_s5_2.png", (540, 300, 1060, 1060), "c03 s5 walk to warden, braid"), tile("v_c01_own_c01_s7_2.png", (0, 320, 520, 1080), "c01 s7 back of head, ponytail")])
R = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\59f6a467-b8ce-446c-8f35-44c1d92b7b9a\scratchpad\s29\shots"
S0 = S; S = R
sheet("h_reaver_sprint", [tile("rv_sprint_cu_f3.png", (440, 330, 1040, 1080), "outfits' frame: Reaver sprint close-up f3 (hair sheet x650-830 y765-815 of frame)")])
