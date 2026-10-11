"""necksheet.py TAG OUT: today's neck beside -1.5 and -3 cm: Look front, Look profile (1:1 crops), in play at cam 12 (3x)."""
import sys
from PIL import Image, ImageDraw, ImageFont
S = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\.shots\\"
tag, out = sys.argv[1], sys.argv[2]
ns = [('0', 'today'), ('-1.5', '-1.5 cm (18%)'), ('-3', '-3 cm (36%)')]
rows = [('_f', (720, 120, 1160, 940), 1), ('_p', (620, 120, 1060, 940), 1)]
font = ImageFont.truetype('arial.ttf', 22)
cols = []
for n, lab in ns:
    tiles = [Image.open(S + '%s_nk%s%s.png' % (tag, n, r)).convert('RGB').crop(b) for r, b, _ in rows]
    p = Image.open(S + 't1_play12_nk%s.png' % n).convert('RGB').crop((880, 330, 1027, 530)).resize((441, 600), Image.LANCZOS)
    tiles.append(p)
    w = max(t.width for t in tiles); h = sum(t.height for t in tiles) + 40
    c = Image.new('RGB', (w, h), (20, 20, 20)); d = ImageDraw.Draw(c); d.text((8, 8), lab, fill=(255, 255, 255), font=font)
    y = 40
    for t in tiles: c.paste(t, (0, y)); y += t.height
    cols.append(c)
W = sum(c.width for c in cols) + 8 * (len(cols) - 1); H = max(c.height for c in cols)
sh = Image.new('RGB', (W, H), (0, 0, 0)); x = 0
for c in cols: sh.paste(c, (x, 0)); x += c.width + 8
sh.save(out, quality=93); print(out, sh.size)
