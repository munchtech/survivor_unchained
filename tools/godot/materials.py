"""Photographed surfaces for what is made in code (View/Made.Surface): CC0 sets
from Poly Haven, at 1K, into godot/art/materials/<id>/ as albedo.jpg,
normal.jpg (OpenGL) and arm.jpg (ambient occlusion, roughness, metal).

    python tools/godot/materials.py id [id ...]

Credits each in public/assets/CREDITS.md (then WRITE_CREDITS=1 dotnet test
--filter CreditsTests rewrites the shipped credits).
"""
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'godot' / 'art' / 'materials'
UA = {'User-Agent': 'survivor-unchained-assets/1.0'}


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120)


def fetch(asset):
    out = OUT / asset
    if all((out / f).exists() for f in ('albedo.jpg', 'normal.jpg', 'arm.jpg')):
        return
    with get(f'https://api.polyhaven.com/files/{asset}') as r:
        f = json.load(r)
    out.mkdir(parents=True, exist_ok=True)
    for kind, fmt, name in (('Diffuse', 'jpg', 'albedo.jpg'), ('nor_gl', 'jpg', 'normal.jpg'), ('arm', 'jpg', 'arm.jpg')):
        with get(f[kind]['1k'][fmt]['url']) as r:
            (out / name).write_bytes(r.read())
    print(f'  fetched {asset} (Poly Haven, CC0)', flush=True)


def credit(assets):
    path = ROOT / 'public' / 'assets' / 'CREDITS.md'
    text = path.read_text(encoding='utf-8')
    add = [f'- {a}: Poly Haven (https://polyhaven.com/a/{a}), CC0\n' for a in sorted(assets)]
    add = [l for l in add if l not in text]
    if add:
        lines = text.splitlines(keepends=True)
        last = max((i for i, l in enumerate(lines) if l.startswith('- ') and ': Poly Haven (https://polyhaven.com/a/' in l and l.rstrip().endswith('CC0')), default=len(lines) - 1)
        path.write_text(''.join(lines[:last + 1] + add + lines[last + 1:]), encoding='utf-8')


if __name__ == '__main__':
    for a in sys.argv[1:]:
        fetch(a)
    credit(sys.argv[1:])
