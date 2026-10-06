"""Board of folk clips on the kit bodies: fboard.py out.png f_idle m_idle ... [--view three] [--frames 8]"""
import json
import sys
from pathlib import Path

W = Path(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa4f5fc266b043035')
sys.path.insert(0, str(W / 'tools' / 'anim'))
from PIL import Image, ImageDraw  # noqa: E402
from review import sheet  # noqa: E402

PARTS = {'f': 'Female_Peasant_Arms,Female_Peasant_Body,Female_Peasant_Legs,Female_Peasant_Feet',
         'm': 'Male_Peasant_Arms,Male_Peasant_Body,Male_Peasant_Legs,Male_Peasant_Feet'}
a = sys.argv[1:]
out = a[0]
view, frames, names, i = 'three', 8, [], 1
while i < len(a):
    if a[i] == '--view':
        view = a[i + 1]; i += 2
    elif a[i] == '--frames':
        frames = int(a[i + 1]); i += 2
    else:
        names.append(a[i]); i += 1
rows = []
for n in names:
    d = json.loads((W / 'tools/anim/out/folk' / f'{n}.json').read_text())
    nfr = int(round(d['length'] * 30))
    sex = n[0]
    p = sheet(f'folk/{n}', view, frames=frames, step=max(1, nfr // frames), size=(170, 230), cols=frames,
              extra={'MODEL': 'female' if sex == 'f' else 'male', 'PARTS': PARTS[sex]})
    rows.append((f'{n} {d["length"]:.1f}s', Image.open(p)))
w = max(r.width for _, r in rows)
b = Image.new('RGB', (w, sum(r.height for _, r in rows)), (40, 40, 44))
y = 0
dr = ImageDraw.Draw(b)
for name, r in rows:
    b.paste(r, (0, y))
    dr.rectangle([0, y, 8 * len(name) + 10, y + 16], fill=(0, 0, 0))
    dr.text((5, y + 2), name, fill=(255, 220, 120))
    y += r.height
b.save(out)
print(out, b.size)
