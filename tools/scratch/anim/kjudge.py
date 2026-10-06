"""Kimodo's takes onto her, for judging: build k_<name>_<k> clips (root
motion kept, or taken out for walks), pack, and render a board per group.

    kjudge.py build                  retarget every take and pack
    kjudge.py board <out.png> <name> [<name> ...] [--view three] [--frames 8] [--weapon W] [--outfit O]
    kjudge.py clean                  drop the k_ clips and repack
"""
import json
import os
import sys
from pathlib import Path

W = Path(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa4f5fc266b043035')
sys.path.insert(0, str(W / 'tools' / 'anim'))
os.chdir(W / 'tools' / 'anim')

from PIL import Image, ImageDraw  # noqa: E402

KDIR = Path(r'C:\Users\munch\Tools\mocap\kimodo')
OUT = W / 'tools' / 'anim' / 'out' / 'clips'
INPLACE = ('walk', 'shamble', 'her_walk')


def build():
    from keyed import Rig
    from rig import Skeleton, write_clip
    from clips.generated import make
    import build as B
    sk = Skeleton.load()
    rig = Rig(sk)
    for f in sorted(KDIR.glob('*_[0-9].bvh')):
        name = 'k_' + f.stem
        place = 'line' if any(f.stem.startswith(w) for w in INPLACE) else 'keep'
        c = make(rig, name, 'kimodo', f.name, place=place)
        if c is not None:
            write_clip(c, sk, OUT)
            print(name, c.frames)
    B.pack()


def clean():
    import build as B
    for f in OUT.glob('k_*.json'):
        f.unlink()
    B.pack()


def board(out, names, view='three', frames=8, weapon='', outfit='ranger', size=(180, 240)):
    from review import sheet
    rows = []
    for n in names:
        for k in range(3):
            clip = f'k_{n}_{k}'
            d = json.loads((OUT / f'{clip}.json').read_text())
            nfr = int(round(d['length'] * 30))
            step = max(1, nfr // frames)
            p = sheet(f'her/{clip}', view, frames=frames, step=step, weapon=weapon, outfit=outfit, size=size,
                      cols=frames, extra={'LOOK': 'pelvis'})
            rows.append((clip, Image.open(p)))
    w = max(r.width for _, r in rows)
    b = Image.new('RGB', (w, sum(r.height for _, r in rows)), (40, 40, 44))
    y = 0
    d = ImageDraw.Draw(b)
    for name, r in rows:
        b.paste(r, (0, y))
        d.rectangle([0, y, 8 * len(name) + 10, y + 16], fill=(0, 0, 0))
        d.text((5, y + 2), name, fill=(255, 220, 120))
        y += r.height
    b.save(out)
    print(out, b.size)


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[0] == 'build':
        build()
    elif a[0] == 'clean':
        clean()
    else:
        kw, names, i = {}, [], 2
        while i < len(a):
            if a[i].startswith('--'):
                k, v = a[i][2:], a[i + 1]
                kw[k] = int(v) if k == 'frames' else v
                i += 2
            else:
                names.append(a[i])
                i += 1
        board(a[1], names, **kw)
