"""Mixamo's folk takes onto her for judging (m_<name>), like kjudge.py."""
import json
import os
import sys
from pathlib import Path

W = Path(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa4f5fc266b043035')
sys.path.insert(0, str(W / 'tools' / 'anim'))
os.chdir(W / 'tools' / 'anim')
from PIL import Image, ImageDraw  # noqa: E402

MDIR = Path(r'C:\Users\munch\Tools\mocap\mixamo')
OUT = W / 'tools' / 'anim' / 'out' / 'clips'


def build():
    from keyed import Rig
    from rig import Skeleton, write_clip
    from clips.generated import make
    import build as B
    sk = Skeleton.load()
    rig = Rig(sk)
    for f in sorted(MDIR.glob('folk_*.bvh')):
        name = 'm_' + f.stem
        place = 'line' if 'walk' in f.stem else 'keep'
        c = make(rig, name, 'mixamo', f.name, place=place)
        write_clip(c, sk, OUT)
        print(name, c.frames)
    B.pack()


def board(out, view='three', frames=10):
    from review import sheet
    rows = []
    for f in sorted(OUT.glob('m_folk_*.json')):
        d = json.loads(f.read_text())
        nfr = int(round(d['length'] * 30))
        p = sheet(f'her/{f.stem}', view, frames=frames, step=max(1, nfr // frames), outfit='ranger', size=(180, 240),
                  cols=frames, extra={'LOOK': 'pelvis'})
        rows.append((f'{f.stem} {d["length"]:.1f}s', Image.open(p)))
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


if __name__ == '__main__':
    if sys.argv[1] == 'build':
        build()
    else:
        board(sys.argv[2])
