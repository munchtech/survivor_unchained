"""python measure.py TAG [TAG2 ...] [--draw]: H10/F2/F3 numbers at fixed boxes (full-res px) per shot, three faces.
eye: white = mean luma of the 80-95th pct, iris = chroma (max-min, 0-255) and luma of the 10-40th pct;
cheek: mean luma, n>=250 (any channel max); hair: mean luma, HSV hue (deg) and sat; smudge: 5th pct luma (min-ish)
against the box's median; face: mean luma (for Look diffs, use diff.py)."""
import sys, colorsys
import numpy as np
from PIL import Image, ImageDraw
SH = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\.shots" + "\\"
OUT = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\463a4243-9324-49b0-bda9-b9fb9a9d68b1\scratchpad\f30" + "\\"
B = {
 "c01_c01_s8_3":  dict(eye=[(875,370,1000,415),(1195,420,1315,465)], cheek=[(1150,490,1330,600)], smudge=[(940,690,1000,740),(1140,700,1200,750)], hair=[(850,140,1450,200)]),
 "c01_c01_s8b_3": dict(eye=[(825,300,1025,375),(1250,375,1450,425)], cheek=[(1250,450,1450,560)], smudge=[(900,760,960,820),(1220,770,1280,830)], hair=[(725,140,1650,200),(1600,150,1662,350)]),
 "c01_c01_s7_3":  dict(hair=[(60,640,330,860)]),
 "c02_c02_s8_3":  dict(eye=[(140,150,320,220),(620,150,840,220)], cheek=[(200,360,360,600),(660,300,1000,600)], smudge=[(280,680,350,730)], hair=[(1250,500,1330,900)]),
 "c04a_c04a_sa5_3": dict(eye=[(940,455,1070,515),(1190,455,1310,515)], cheek=[(760,560,880,680),(1150,560,1260,680)], smudge=[(1000,730,1050,780),(1190,730,1240,780)], hair=[(720,150,1300,250),(660,300,720,600)]),
 "c04a_c04a_sa7_3": dict(eye=[(850,462,1000,512),(1200,462,1312,512)], cheek=[(750,575,875,700),(1175,575,1300,700)], hair=[(650,137,1350,250),(612,325,687,575)]),
 "day":   dict(eye=[(862,380,930,415),(1025,380,1092,415)], cheek=[(850,450,925,537),(1037,450,1112,537)], hair=[(750,150,1100,275),(712,300,750,475)]),
 "night": dict(eye=[(862,380,930,415),(1025,380,1092,415)], cheek=[(850,450,925,537),(1037,450,1112,537)], hair=[(750,150,1100,275),(712,300,750,475)]),
}
L = lambda a: a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722
def stat(kind, a):
    px = a.reshape(-1, 3); l = L(px); o = np.argsort(l); n = len(l)
    if kind == "eye":
        w = o[int(.80 * n):int(.95 * n)]; i = o[int(.10 * n):int(.40 * n)]
        ch = (px[i].max(1) - px[i].min(1)).mean()
        return f"white {l[w].mean():5.1f} iris L{l[i].mean():4.1f} C{ch:4.1f}"
    if kind == "cheek":
        return f"L{l.mean():5.1f} n250 {(px.max(1) >= 250).sum():5d}"
    if kind == "hair":
        m = px.mean(0) / 255; h, s, v = colorsys.rgb_to_hsv(*m)
        hi = (l > np.percentile(l, 95)); m2 = px[hi].mean(0) / 255; h2, s2, _ = colorsys.rgb_to_hsv(*m2)
        return f"L{l.mean():5.1f} h{h*360:4.0f} s{s:.2f} | top5% h{h2*360:4.0f} s{s2:.2f} L{l[hi].mean():5.1f} | sd{l.std():4.1f}"
    if kind == "smudge":
        return f"p5 {np.percentile(l, 5):5.1f} med {np.median(l):5.1f}"
draw = "--draw" in sys.argv; tags = [t for t in sys.argv[1:] if not t.startswith("--")]
for shot, boxes in B.items():
    print("==", shot)
    for tag in tags:
        for f in ("own", "saffron", "sunborn"):
            p = f"{SH}f30c{tag}_{f}_{shot}.png"
            try: im = Image.open(p).convert("RGB")
            except FileNotFoundError: continue
            a = np.asarray(im).astype(float)
            parts = []
            for k, bl in boxes.items():
                for j, (x0, y0, x1, y1) in enumerate(bl): parts.append(f"{k}{j}: " + stat(k, a[y0:y1, x0:x1]))
            print(f"  {tag:5s} {f:8s} " + " || ".join(parts))
            if draw and tag == tags[0]:
                d = ImageDraw.Draw(im)
                for k, bl in boxes.items():
                    for bx in bl: d.rectangle(bx, outline={"eye": (0,255,0), "cheek": (255,255,0), "hair": (255,0,255), "smudge": (0,255,255)}[k], width=3)
                im.resize((480, 270)).save(f"{OUT}box_{f}_{shot}.jpg")
