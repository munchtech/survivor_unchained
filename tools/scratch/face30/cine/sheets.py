"""python sheets.py BEFORE AFTER: 1:1 crop sheets per shot, rows own/saffron/sunborn, BEFORE | AFTER (<=1568 wide, <=1.16 MP)
-> scratchpad f30/cj/"""
import sys, os
from PIL import Image, ImageDraw
SH = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\.shots" + "\\"
OUT = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\463a4243-9324-49b0-bda9-b9fb9a9d68b1\scratchpad\f30\cj" + "\\"
os.makedirs(OUT, exist_ok=True)
A, B = sys.argv[1:3]
C = {"c02_mouth": ("c02_c02_s8_3", (150, 560, 930, 805)), "c02_cheek": ("c02_c02_s8_3", (100, 300, 880, 545)),
     "c01_s8": ("c01_c01_s8_3", (720, 340, 1500, 585)), "c01_s8b": ("c01_c01_s8b_3", (760, 280, 1540, 525)),
     "c01_s7": ("c01_c01_s7_3", (0, 600, 780, 845)),
     "c04a_a5": ("c04a_c04a_sa5_3", (740, 430, 1520, 675)), "c04a_a7": ("c04a_c04a_sa7_3", (690, 440, 1470, 685)),
     "look_day": ("day", (590, 330, 1370, 575)), "look_night": ("night", (590, 330, 1370, 575))}
for name, (shot, box) in C.items():
    box = (box[0], box[1], box[2], box[1] + 235); w, h = box[2] - box[0], 235
    m = Image.new("RGB", (2 * w + 8, 3 * h + 2 * 4 + 20), (40, 40, 40)); d = ImageDraw.Draw(m)
    d.text((4, 4), f"{name}  BEFORE ({A})", fill=(255, 255, 255)); d.text((w + 12, 4), f"AFTER ({B})", fill=(255, 255, 255))
    for r, f in enumerate(("own", "saffron", "sunborn")):
        for c, t in enumerate((A, B)):
            p = f"{SH}f30c{t}_{f}_{shot}.png"
            if os.path.exists(p): m.paste(Image.open(p).convert("RGB").crop(box), (c * (w + 8), 20 + r * (h + 4)))
    assert m.width <= 1568 and m.width * m.height <= 1.16e6, (name, m.size)
    m.save(OUT + f"{name}.png"); print(name, m.size)
