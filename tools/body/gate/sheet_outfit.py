# Lane G refit (16 Nov): A|B outfit sheet at 1:1. usage: sheet_outfit.py OUT TITLE TAG[:LABEL] [TAG[:LABEL] ...]
# Each TAG is godot/.shots/refit_b/<TAG>/{A,B}/<key>.png (shoot_outfit.sh). Writes per key a 3840x1080 A|B pair (1:1, no
# scaling) + one stacked sheet (full size .png, half-size .jpg for a glance; the judge reads the 1:1 pairs).
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
R = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a8359f8b3c48d4eb8\godot\.shots\refit_b")
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True); TITLE = sys.argv[2]
KEYS = [("look_look_day", "Look camera (character creation)"), ("close_town_day", "Close-up, town idle"),
        ("play_town_day", "Play camera, town"), ("play_play_day", "Play camera, arena idle"),
        ("play_run_hold", "Play camera, run (held frame)"), ("play_hit_hold", "Play camera, weapon swing (held frame)")]
F = lambda s: ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", s)
W, BG, FG = 3840, (24, 24, 26), (235, 235, 235)
def bar(t, s):
    im = Image.new("RGB", (W, s + 24), BG); ImageDraw.Draw(im).text((12, 8), t, font=F(s), fill=FG); return im
blocks = [bar(TITLE, 52)]
for arg in sys.argv[3:]:
    tag, _, label = arg.partition(":")
    for k, cam in KEYS:
        a, b = R / tag / "A" / f"{k}.png", R / tag / "B" / f"{k}.png"
        if not (a.exists() and b.exists()):
            print("missing", tag, k); continue
        pair = Image.new("RGB", (W, 1080), BG)
        pair.paste(Image.open(a).convert("RGB"), (0, 0)); pair.paste(Image.open(b).convert("RGB"), (1920, 0))
        ImageDraw.Draw(pair).line([(1920, 0), (1920, 1080)], fill=(255, 255, 255), width=2)
        pair.save(OUT / f"{tag}_{k}_AB_1to1.png")
        blocks += [bar(f"{label or tag}: {cam}   A (left) | B (right)", 38), pair]
H = sum(x.height for x in blocks); sh = Image.new("RGB", (W, H), BG); y = 0
for x in blocks: sh.paste(x, (0, y)); y += x.height
sh.save(OUT / "sheet.png"); sh.resize((W // 2, H // 2), Image.LANCZOS).save(OUT / "sheet_half.jpg", quality=90)
print("wrote", OUT / "sheet.png", sh.size)
