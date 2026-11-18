# Lane G item 3 (16 Nov): the owner's bare-shape sheet, A (shipped, left) | B (body_p1 round_39d, right), 1:1 pairs + captions
import sys, shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
P = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a8359f8b3c48d4eb8\godot\.shots\bare_g\pairs")
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
F = lambda s: ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", s)
W, BG, FG, DIM, YEL = 3840, (24, 24, 26), (235, 235, 235), (170, 170, 170), (240, 200, 90)
TITLE = "HER BARE SHAPE: A = the shipped body (left) | B = the rebuilt body (right). Nude, by day, the 4 game cameras, 1:1. Yes to B?"
SUB = ("B = body_p1 round_39d (our quad topology, rig, correctives; branch body-b). Same head, hair, camera and frame. "
       "ONE max judge: B at or above A at all four cameras; every 5 Nov fault gone (deltoid knob, boxy shoulders, throat seam, "
       "low bust and underbust fold, pink torso, stiff hand). Faults both bodies share are captioned and become B's to fix.")
CAP = {"look_look_day": ("Look camera (character creation)", "Tie: the same body to the eye; B's shoulders sit a little lower and narrower, with a smoother outline.",
                         "Both, not yet AAA at 1:1: a deep slit in her right (inked-side) armpit and a pinched dimple where her left breast meets the arm."),
       "close_town_day": ("Close-up, town idle", "B, slightly: same shape and skin; B's right shoulder is clean where A has a faint dark mark.",
                          "Both: the sun washes the lit torso to flat cream, paler than the face; a hooked crease on the chest by her right armpit."),
       "play_town_day": ("Play camera, town", "Tie: identical at this distance.", ""),
       "play_play_day": ("Play camera, arena idle", "B, slightly: B's left hip and thigh are clean where A shows faint scratch-like lines.",
                         "Both: a white glint on the left shoulder; the arena 'day' is lit by a red lamp, so skin tone isn't tested here.")}
def bar(lines, fonts, cols):
    rows = []
    for t, f, c in zip(lines, fonts, cols):
        cur = ""
        for w in t.split():
            if cur and f.getlength(cur + " " + w) > W - 30: rows.append((cur, f, c)); cur = w
            else: cur = (cur + " " + w).strip()
        if cur: rows.append((cur, f, c))
    im = Image.new("RGB", (W, 16 + sum(f.size + 10 for _, f, _ in rows)), BG); d = ImageDraw.Draw(im); y = 6
    for t, f, c in rows: d.text((12, y), t, font=f, fill=c); y += f.size + 10
    return im
blocks = [bar([TITLE, SUB], [F(56), F(32)], [FG, DIM])]
for k, (cam, better, both) in CAP.items():
    pair = Image.open(P / f"{k}_AB_1to1.png").convert("RGB")
    shutil.copy(P / f"{k}_AB_1to1.png", OUT / f"BARE_{k}_AB_1to1.png")
    blocks.append(bar([f"{cam}   A (left) | B (right)", "JUDGE: " + better] + (["Both bodies: " + both] if both else []),
                      [F(40), F(32), F(30)], [FG, YEL, DIM]))
    blocks.append(pair)
H = sum(b.height for b in blocks); sh = Image.new("RGB", (W, H), BG); y = 0
for b in blocks: sh.paste(b, (0, y)); y += b.height
sh.save(OUT / "BARE_sheet.png")
sh.resize((W // 2, H // 2), Image.LANCZOS).save(OUT / "BARE_sheet_half.jpg", quality=90)
print("wrote", OUT / "BARE_sheet.png", sh.size, "+ BARE_sheet_half.jpg + 4 pairs")
