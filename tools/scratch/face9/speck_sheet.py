"""speck_sheet.py OUT: her breasts' skin before and after the speckle fix, each framing a pair at 1:1 (no scaling),
labelled: the Look's bust (the portrait's light), the face test's frame (the Look's close-up, its bottom), and the
book by day and by night at 2560x1440 (play's light)."""
import sys
from PIL import Image, ImageDraw

S = r'C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-aed215ba3ca60cc29/godot/.shots/'
PAIRS = [
    ('Look, bust (portrait light)', 'sp1_bust_was', 'sp3_bust', (740, 540, 1260, 840)),
    ('Face test frame (Look close-up)', 'v12c_pony', 'sp3_face', (700, 760, 1260, 1080)),
    ('Book by day, 1440p (play light)', 'sp1_bk_day_was', 'sp3_bk_day', (600, 330, 1000, 650)),
    ('Book by night, 1440p (play light)', 'sp1_bk_night_was', 'sp3_bk_night', (600, 330, 1000, 650)),
]
rows = []
for title, before, after, box in PAIRS:
    tiles = []
    for tag, n in (('before', before), ('after', after)):
        t = Image.open(S + n + '.png').convert('RGB').crop(box)
        d = ImageDraw.Draw(t)
        d.rectangle([0, 0, 330, 15], fill=(0, 0, 0))
        d.text((4, 2), '%s: %s (%s)' % (title, tag, n), fill=(255, 230, 120))
        tiles.append(t)
    w = sum(t.width for t in tiles) + 6
    h = max(t.height for t in tiles)
    r = Image.new('RGB', (w, h), (16, 16, 16))
    r.paste(tiles[0], (0, 0))
    r.paste(tiles[1], (tiles[0].width + 6, 0))
    rows.append(r)
W = max(r.width for r in rows)
H = sum(r.height for r in rows) + 6 * (len(rows) - 1)
sheet = Image.new('RGB', (W, H), (16, 16, 16))
y = 0
for r in rows:
    sheet.paste(r, (0, y))
    y += r.height + 6
sheet.save(sys.argv[1], quality=94)
print(sys.argv[1], sheet.size)
