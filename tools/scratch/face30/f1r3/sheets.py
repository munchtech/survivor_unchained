"""face30 F1 r3 sheets (1:1 crops, labelled, F1 beside R3): python sheets.py OUTDIR"""
import sys, os
from PIL import Image, ImageDraw
S = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\.shots"
O = sys.argv[1]; os.makedirs(O, exist_ok=True)
def sheet(out, rows, box, title):
    w, h = box[2]-box[0], box[3]-box[1]; nc = max(len(r[1]) for r in rows)
    S_ = Image.new("RGB", (nc*w, 18 + len(rows)*(h+16)), "white"); d = ImageDraw.Draw(S_); d.text((4, 3), title, fill="black")
    for i, (rl, cells) in enumerate(rows):
        for j, (cl, f) in enumerate(cells):
            x, y = j*w, 18 + i*(h+16)
            p = os.path.join(S, f)
            if os.path.exists(p): S_.paste(Image.open(p).convert("RGB").crop(box), (x, y+16))
            d.text((x+3, y+3), f"{rl} | {cl}", fill="black")
    assert S_.width <= 1568 and S_.width*S_.height <= 1.16e6, S_.size
    S_.save(os.path.join(O, out)); print(out, S_.size)
F3 = ["own", "saffron", "sunborn"]
A = (975, 690, 1285, 850); LB = (872, 507, 1072, 677)
sheet("a_c04a_A5_f1_r3.png", [(f, [("before (integration)", f"f30bef_{f}_c04a_sa5_2.png"), ("S2 73a798ca", f"f30s2_{f}_c04a_sa5_2.png"),
      ("face30 F1 08a6b735", f"f30fin_{f}_c04a_sa5_2.png"), ("face30 R3", f"f30r3_{f}_c04a_sa5_2.png")]) for f in F3], A, "c04a still A5, mouth_open 0.25, 1:1 crops of 1920x1080")
sheet("b_look_closed_06_smile_r3.png", [(f, [("closed F1", f"f30lkc_{f}.png"), ("closed R3", f"f30lkc3_{f}.png"), ("open 0.6 F1", f"f30lk6_{f}.png"), ("open 0.6 R3", f"f30lk63_{f}.png"),
      ("smile+open 0.6 F1", f"f30lkso_{f}.png"), ("smile+open 0.6 R3", f"f30lkso3_{f}.png")]) for f in F3], LB, "the Look, 1:1 crops (F1 frames are from the build before the hair rebuild)")
T = ["own", "doe", "fey", "hardwon", "highborn", "moonlit", "saffron", "sunborn", "vixen", "wildling"]
sheet("b2_look_closed_ten_r3.png", [("closed F1", [(f, f"f30lkc_{f}.png") for f in T[:5]]), ("closed R3", [(f, f"f30lkc3_{f}.png") for f in T[:5]]),
      ("closed F1", [(f, f"f30lkc_{f}.png") for f in T[5:]]), ("closed R3", [(f, f"f30lkc3_{f}.png") for f in T[5:]])], LB, "the Look, mouth closed, ten presets, F1 and R3, 1:1")
