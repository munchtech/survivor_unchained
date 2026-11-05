# sheet.py CAPTIONS.json OUTDIR: the P1 bare-shape gate sheet (A = shipped, B = ours), half size, + 1:1 pairs
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

WT = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\body-p1\godot\.shots")
L3 = Path(r"C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_body_p1\lead3\ek2\final")
cap = json.load(open(sys.argv[1], encoding="utf-8"))
out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
F = lambda s: ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", s)
f_t, f_c, f_s = F(60), F(40), F(34)
W = 3840
BG, FG, DIM, RED = (24, 24, 26), (235, 235, 235), (170, 170, 170), (230, 60, 50)

blocks = []
def bar(lines, h, fonts, colors):
    rows = []
    for t, f, c in zip(lines, fonts, colors):
        cur = ""
        for w in t.split():
            if cur and f.getlength(cur + " " + w) > W - 30: rows.append((cur, f, c)); cur = w
            else: cur = (cur + " " + w).strip()
        rows.append((cur, f, c))
    im = Image.new("RGB", (W, max(h, 16 + sum(f.size + 10 for _, f, _ in rows))), BG); d = ImageDraw.Draw(im); y = 6
    for t, f, c in rows:
        d.text((12, y), t, font=f, fill=c); y += f.size + 10
    return im

blocks.append(bar([cap["title"], cap["sub"]], 164, [f_t, f_s], [FG, DIM]))
for k in ["look_look", "close_town", "play_town", "play_play"]:
    a = Image.open(WT / f"{k}_A.png").convert("RGB"); b = Image.open(WT / f"{k}_B.png").convert("RGB")
    pair = Image.new("RGB", (a.width + b.width, a.height)); pair.paste(a, (0, 0)); pair.paste(b, (a.width, 0))
    pair.save(out / f"GATE_{k}_1to1.png")
    jl = cap.get("judge", {}).get(k)
    blocks.append(bar([f"{k}   A = shipped (left)  |  B = ours (right)", cap[k]] + ([f"JUDGE (max): {jl}"] if jl else []),
                      124, [f_c, f_s, f_s], [FG, DIM, (240, 200, 90)]))
    blocks.append(pair.resize((W, round(pair.height * W / pair.width)), Image.LANCZOS))

# the hip, OPEN
blocks.append(bar(["HIP 112 / 135: OPEN (not part of this pick's pass; shipped best-known, 4 of 4 rounds)", cap["hip"]],
                  124, [f_c, f_s], [RED, DIM]))
sc = Image.open(L3 / "close" / "strip_hip_flex.png").convert("RGB")
sp = Image.open(L3 / "play" / "strip_hip_flex.png").convert("RGB")
row = Image.new("RGB", (W, max(sc.height, sp.height) + 50), BG); d = ImageDraw.Draw(row)
d.text((12, 4), "close tier (B)", font=f_s, fill=DIM); d.text((sc.width + 40, 4), "play tier (B)", font=f_s, fill=DIM)
row.paste(sc, (0, 50)); row.paste(sp.resize((min(sp.width, W - sc.width - 16), round(sp.height * min(sp.width, W - sc.width - 16) / sp.width))), (sc.width + 16, 50))
d.rectangle([0, 0, W - 1, row.height - 1], outline=RED, width=6); d.text((W - 220, 2), "OPEN", font=f_t, fill=RED)
blocks.append(row)
if cap.get("judge", {}).get("overall"): blocks.append(bar([f"JUDGE (max, overall): {cap['judge']['overall']}"], 64, [f_c], [(240, 200, 90)]))
blocks.append(bar([cap["foot"]], 64, [f_s], [DIM]))

H = sum(b.height for b in blocks); s = Image.new("RGB", (W, H), BG); y = 0
for b in blocks: s.paste(b, (0, y)); y += b.height
full = out / "GATE_sheet.png"; s.save(full)
print(full, s.size)
