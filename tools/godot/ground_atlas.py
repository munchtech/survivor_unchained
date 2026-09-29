"""The ground's materials for the Godot slice: the same Poly Haven sets as
the web game (tools/assets/ground.py, whose downloads in .packs/ground this
reads), stacked into three strips Godot imports as texture arrays (one
layer per material, VRAM-compressed, mipmapped: see the .import files).

    python3 tools/godot/ground_atlas.py

Writes godot/art/ground/{albedo,normal,arh}.jpg: colour; OpenGL normals;
R occlusion, G roughness, B height (stretched per layer, as the web game's).
Run tools/assets/ground.py first if .packs/ground is empty.
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools' / 'assets'))
import ground  # noqa: E402  (the layer list and helpers)

OUT = ROOT / 'godot' / 'art' / 'ground'
SIZE = ground.SIZE

IMPORT = """[remap]

importer="2d_array_texture"
type="CompressedTexture2DArray"

[deps]

source_file="res://art/ground/{name}.jpg"

[params]

compress/mode=2
compress/high_quality=true
compress/lossy_quality=0.9
compress/hdr_compression=1
compress/channel_pack=0
mipmaps/generate=true
mipmaps/limit=-1
slices/horizontal=1
slices/vertical={layers}
"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    strips = {k: Image.new('RGB', (SIZE, SIZE * len(ground.LAYERS))) for k in ('albedo', 'normal', 'arh')}
    meta = []
    for i, (name, asset) in enumerate(ground.LAYERS):
        d = ground.CACHE / asset
        if not (d / 'diff.jpg').exists():
            raise SystemExit(f'{d} is missing: run tools/assets/ground.py first')
        a = ground.square(Image.open(d / 'diff.jpg').convert('RGB'))
        n = ground.square(Image.open(d / 'nor.png').convert('RGB'))
        ao, rough, _ = ground.square(Image.open(d / 'arm.jpg').convert('RGB')).split()
        h = ground.height(d / 'disp.png')
        for k, im in (('albedo', a), ('normal', n), ('arh', Image.merge('RGB', (ao, rough, h)))):
            strips[k].paste(im, (0, i * SIZE))
        meta.append(name)
    for k, im in strips.items():
        im.save(OUT / f'{k}.jpg', quality=95, subsampling=0)
        (OUT / f'{k}.jpg.import').write_text(IMPORT.format(name=k, layers=len(ground.LAYERS)))
        print(f'{k}.jpg: {(OUT / f"{k}.jpg").stat().st_size / 1e6:.1f} MB')
    src = json.loads((ROOT / 'public' / 'assets' / 'ground' / 'ground.json').read_text())
    (OUT / 'ground.json').write_text(json.dumps(src, indent=1) + '\n')


if __name__ == '__main__':
    main()
