"""The ground's materials: photoscanned CC0 sets from Poly Haven, packed into
three KTX2 texture arrays for the terrain (src/render/terrain.ts).

    python3 tools/assets/ground.py

Downloads each set at 1K (the camera sees about 80 pixels a metre, 160 on
the high setting; a 2 m tile at 1K has 512), and writes

  public/assets/ground/albedo.ktx2   colour (sRGB), one layer per material
  public/assets/ground/normal.ktx2   OpenGL normals (linear)
  public/assets/ground/arh.ktx2      R ambient occlusion, G roughness,
                                     B height (stretched to 0..1 per layer)
  public/assets/ground/ground.json   the layers' names, sources and sizes

Needs toktx (KTX-Software 4.x, as ktx2.py; TOKTX and LD_LIBRARY_PATH) and
Pillow. Downloads are cached in .packs/ground/.
"""
import json
import os
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'public' / 'assets' / 'ground'
CACHE = ROOT / '.packs' / 'ground'
TOKTX = os.environ.get('TOKTX') or shutil.which('toktx')
SIZE = 1024
UA = {'User-Agent': 'survivor-unchained-assets/1.0'}


def get(url: str):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120)

# The terrain's layers, in the order the shader indexes them.
LAYERS = [
    ('grass', 'sparse_grass'),        # meadow: short dark grass
    ('leaves', 'forest_leaves_02'),   # forest floor: moss and fallen leaves
    ('dirt', 'forest_ground_04'),     # paths and bare ground, with stones
    ('mud', 'mud_forest'),            # wet, dark, trodden
    ('stone', 'cobblestone_05'),      # the town's setts, dirty
    ('rock', 'mossy_rock'),           # steep faces
    ('blight', 'burned_ground_01'),   # dead ground
]


def fetch(url: str, dst: Path) -> Path:
    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        with get(url) as r:
            dst.write_bytes(r.read())
    return dst


def files(asset: str):
    with get(f'https://api.polyhaven.com/files/{asset}') as r:
        f = json.load(r)
    pick = lambda kind, fmt: f[kind]['1k'][fmt]['url']
    return {
        'diff': fetch(pick('Diffuse', 'jpg'), CACHE / asset / 'diff.jpg'),
        'nor': fetch(pick('nor_gl', 'png'), CACHE / asset / 'nor.png'),
        'arm': fetch(pick('arm', 'jpg'), CACHE / asset / 'arm.jpg'),
        'disp': fetch(pick('Displacement', 'png'), CACHE / asset / 'disp.png'),
    }


def square(im: Image.Image) -> Image.Image:
    return im if im.size == (SIZE, SIZE) else im.resize((SIZE, SIZE), Image.LANCZOS)


def height(path: Path) -> Image.Image:
    """Displacement, 8-bit, stretched so every layer spans the same range
    (blending compares heights across layers)."""
    im = Image.open(path)
    if im.mode in ('I;16', 'I;16B', 'I'):
        im = im.point(lambda v: v / 256).convert('L')
    else:
        im = im.convert('L')
    return square(ImageOps.autocontrast(im, cutoff=1))


def encode(dst: Path, pngs, srgb: bool, normal=False):
    cmd = [TOKTX, '--t2', '--encode', 'uastc', '--uastc_quality', '1',
           '--uastc_rdo_l', '0.25' if normal else '1.0', '--zcmp', '18', '--genmipmap',
           '--assign_oetf', 'srgb' if srgb else 'linear', '--layers', str(len(pngs))]
    if normal:
        cmd.append('--normalize')
    subprocess.run(cmd + [str(dst)] + [str(p) for p in pngs], check=True, capture_output=True)


def main():
    if not TOKTX:
        raise SystemExit('toktx not found: set TOKTX (see tools/assets/ktx2.py)')
    with get('https://api.polyhaven.com/assets?t=textures') as r:
        info = json.load(r)
    OUT.mkdir(parents=True, exist_ok=True)
    meta = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        albedo, normal, arh = [], [], []
        for name, asset in LAYERS:
            f = files(asset)
            a = square(Image.open(f['diff']).convert('RGB'))
            n = square(Image.open(f['nor']).convert('RGB'))
            arm = square(Image.open(f['arm']).convert('RGB'))
            ao, rough, _ = arm.split()
            h = height(f['disp'])
            paths = [tmp / f'{name}_a.png', tmp / f'{name}_n.png', tmp / f'{name}_h.png']
            a.save(paths[0]); n.save(paths[1]); Image.merge('RGB', (ao, rough, h)).save(paths[2])
            albedo.append(paths[0]); normal.append(paths[1]); arh.append(paths[2])
            size = info[asset]['dimensions'][0] / 1000
            meta.append({'name': name, 'source': asset, 'metres': round(size, 3)})
            print(f'  {name}: {asset} ({size:.2f} m)', flush=True)
        encode(OUT / 'albedo.ktx2', albedo, srgb=True)
        encode(OUT / 'normal.ktx2', normal, srgb=False, normal=True)
        encode(OUT / 'arh.ktx2', arh, srgb=False)
    (OUT / 'ground.json').write_text(json.dumps({'layers': meta}, indent=1) + '\n')
    for p in sorted(OUT.iterdir()):
        print(f'{p.relative_to(ROOT)}: {p.stat().st_size / 1e6:.1f} MB')


if __name__ == '__main__':
    main()
