"""Each arena's own ground: photoscanned CC0 sets from Poly Haven, stacked
per place into the texture arrays the arena's ground shader reads
(shaders/arena_ground.gdshader, View/ArenaGround.cs).

    python tools/godot/arena_ground.py [place ...]

Writes godot/art/arena/<place>/{albedo,normal,arh}.jpg (one 1K layer per
material, Godot imports them as texture arrays: see the .import files) and
layers.json (each layer's source and size in metres). Downloads are cached
in .packs/ground/ (shared with tools/assets/ground.py).

A place's seven layers, in the order the shader reads them:
  0, 1  the ground itself, mixed in broad patches (the macro variation);
  2..5  what the place paints over it (splat R, G, B, A: a way, ruts, a
        stream bed, graves, ash, spoil...);
  6     what steep faces show.

Each layer's mean colour in linear light goes in layers.json too: the game
brings every photograph to the value the place asks of it (ArenaGround.cs),
however bright the day it was shot in. `--meta` rewrites only that.
"""
import json
import sys
import urllib.request
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'godot' / 'art' / 'arena'
CACHE = ROOT / '.packs' / 'ground'
SIZE = 1024
UA = {'User-Agent': 'survivor-unchained-assets/1.0'}

# What each place stands on. The comments say what each layer is in the world.
PLACES = {
    # The Risen's barrow field: the Seventh Legion's dead under dry grass, the
    # old empire's way through them, graves opened from below, ash where the
    # ember came up.
    'barrow': [
        ('turf', 'withered_grass'),         # dead grass over chalk
        ('bare', 'ground_grey'),            # grey soil where the grass gave up
        ('way', 'grassy_cobblestone', 160), # the Legion's road: polygonal slabs, grass in the joints
        ('grave', 'brown_mud_02'),          # earth dug and heaped: the graves opened
        ('ash', 'burned_ground_01'),        # where the ember burned through
        ('rubble', 'rocky_trail'),          # chalk and stone round the ruins
        ('face', 'dark_rock'),
    ],
    # The Pack's Hollow: a sunk bowl of old wood, the leaf litter of years, roots
    # breaking through, the stream the Dig's slurry runs in.
    'hollow': [
        # (Not leaves_forest_ground: its pale chips on black read as gravel from 30 m. Nor
        # forest_leaves_03: small leaves, speckled pale, the same.)
        ('litter', 'dry_decay_leaves'),     # the leaves of years, red-brown, whole: leaves read as leaves from 30 m
        ('rot', 'forest_ground_06'),        # rotted down to black earth between the drifts (moss is the shader's)
        ('roots', 'roots'),                 # where the great trees' roots surface
        ('mud', 'mud_forest'),              # trodden black mud: the den's runs, the banks
        ('bed', 'river_small_rocks'),       # the stream's bed
        ('needles', 'forest_leaves_04'),    # drier litter, needles, twigs
        ('face', 'mossy_rock'),
    ],
    # The Kerchiefs' ruts: the caravan road where the wagons were taken, churned
    # to mud, and the Roost's camp beside it.
    'ruts': [
        ('verge', 'grass_path_3'),          # trodden grass and earth
        ('churn', 'brown_mud_03'),          # churned dark mud
        ('ruts', 'muddy_tracks'),           # the road: wheel ruts and hooves
        ('wet', 'brown_mud_02'),            # standing wet in the low places
        ('camp', 'wood_chips'),             # the camp floor: chips, straw, dung
        ('metal', 'gravel_road'),           # the old road's metalling, showing through
        ('face', 'rocky_terrain'),
    ],
    # The Lamplings' dig: ember-stained clay, black spoil, broken stone, the
    # slurry the Dig cooks running where it was spilled.
    'dig': [
        ('clay', 'dry_ground_rocks'),       # the working's floor: ochre clay and broken stone
        ('spoil', 'gray_rocks', 160),       # black spoil, tipped: blasted rock in lumps
        ('ballast', 'stony_dirt_path'),     # broken stone: the rails' bed, the blast drifts
        ('slurry', 'brown_mud_03'),         # spilled slurry, glossy (the shader wets it)
        ('rust', 'red_dirt_mud_01'),        # clay stained rust by the ember, in drifts
        ('burnt', 'burned_ground_01'),      # ember-burnt
        ('face', 'excavated_soil_wall'),    # the working's cut walls
    ],
}

IMPORT = """[remap]

importer="2d_array_texture"
type="CompressedTexture2DArray"

[deps]

source_file="res://art/arena/{place}/{name}.jpg"

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


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120)


def fetch(url, dst):
    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        with get(url) as r:
            dst.write_bytes(r.read())
    return dst


def files(asset):
    d = CACHE / asset
    if all((d / f).exists() for f in ('diff.jpg', 'nor.png', 'arm.jpg', 'disp.png')):
        return d
    with get(f'https://api.polyhaven.com/files/{asset}') as r:
        f = json.load(r)
    pick = lambda kind, fmt: f[kind]['1k'][fmt]['url']
    fetch(pick('Diffuse', 'jpg'), d / 'diff.jpg')
    fetch(pick('nor_gl', 'png'), d / 'nor.png')
    fetch(pick('arm', 'jpg'), d / 'arm.jpg')
    fetch(pick('Displacement', 'png'), d / 'disp.png')
    print(f'  fetched {asset} (Poly Haven, CC0)', flush=True)
    return d


def square(im):
    return im if im.size == (SIZE, SIZE) else im.resize((SIZE, SIZE), Image.LANCZOS)


def height(path):
    """Displacement, 8-bit, stretched so every layer spans the same range
    (blending compares heights across layers)."""
    im = Image.open(path)
    if im.mode in ('I;16', 'I;16B', 'I'):
        im = im.point(lambda v: v / 256).convert('L')
    else:
        im = im.convert('L')
    return square(ImageOps.autocontrast(im, cutoff=1))


def mean_linear(im):
    """A photograph's mean colour in linear light (what the shader multiplies)."""
    small = im.resize((128, 128), Image.BOX)
    px = [c / 255 for p in small.getdata() for c in p]
    lin = [c / 12.92 if c < 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in px]
    n = len(lin) // 3
    return [round(sum(lin[i::3]) / n, 5) for i in range(3)]


def meta_only(place):
    """Rewrite layers.json's means from the strips already made (no new images,
    so nothing for Godot to import again)."""
    out = OUT / place
    meta = json.loads((out / 'layers.json').read_text())
    strip = Image.open(out / 'albedo.jpg').convert('RGB')
    for i, m in enumerate(meta['layers']):
        m['mean'] = mean_linear(strip.crop((0, i * SIZE, SIZE, (i + 1) * SIZE)))
    (out / 'layers.json').write_text(json.dumps(meta, indent=1) + '\n')
    print(place, [m['mean'] for m in meta['layers']])


def flatten(im, radius=48):
    """The photograph's broad light and shade taken out (each pixel over its
    blurred surroundings, times the mean): a tile with lumps in it repeats as
    a grid from thirty metres up, however its copies are offset. The ground's
    broad variation is the shader's, in world space, where it never repeats."""
    import numpy as np
    from PIL import ImageFilter
    a = np.asarray(im, dtype=np.float32)
    pad = radius * 3
    # Blurred as the tile it is (wrapped), so its edges stay seamless.
    wrapped = Image.fromarray(np.pad(a, ((pad, pad), (pad, pad), (0, 0)), mode='wrap').astype(np.uint8))
    blur = np.asarray(wrapped.filter(ImageFilter.GaussianBlur(radius)), dtype=np.float32)[pad:-pad, pad:-pad]
    mean = a.reshape(-1, 3).mean(0)
    out = a * mean / np.maximum(blur, 1.0)
    return Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8))


def build(place, layers, info):
    out = OUT / place
    out.mkdir(parents=True, exist_ok=True)
    strips = {k: Image.new('RGB', (SIZE, SIZE * len(layers))) for k in ('albedo', 'normal', 'arh')}
    meta = []
    for i, layer in enumerate(layers):
        name, asset = layer[0], layer[1]
        # A layer of big stones keeps their light and shade (a wider flattening).
        radius = layer[2] if len(layer) > 2 else 48
        d = files(asset)
        a = flatten(square(Image.open(d / 'diff.jpg').convert('RGB')), radius)
        n = square(Image.open(d / 'nor.png').convert('RGB'))
        ao, rough, _ = square(Image.open(d / 'arm.jpg').convert('RGB')).split()
        h = height(d / 'disp.png')
        for k, im in (('albedo', a), ('normal', n), ('arh', Image.merge('RGB', (ao, rough, h)))):
            strips[k].paste(im, (0, i * SIZE))
        metres = info[asset]['dimensions'][0] / 1000
        meta.append({'name': name, 'source': asset, 'metres': round(metres, 3), 'mean': mean_linear(a)})
    for k, im in strips.items():
        im.save(out / f'{k}.jpg', quality=93, subsampling=0)
        # Godot keeps its own lines (the uid) in an import file once made: never rewritten.
        if not (out / f'{k}.jpg.import').exists():
            (out / f'{k}.jpg.import').write_text(IMPORT.format(place=place, name=k, layers=len(layers)))
    (out / 'layers.json').write_text(json.dumps({'layers': meta}, indent=1) + '\n')
    print(f'{place}: ' + ', '.join(f"{m['name']}={m['source']}" for m in meta), flush=True)


def credit(assets):
    path = ROOT / 'public' / 'assets' / 'CREDITS.md'
    text = path.read_text(encoding='utf-8') if path.exists() else ''
    add = [f'- {a}: Poly Haven (https://polyhaven.com/a/{a}), CC0\n' for a in sorted(assets)]
    add = [l for l in add if l not in text]
    if add:
        # Into the Poly Haven list, after its last line (the credits read that section only;
        # godot/tests/CreditsTests then says to rewrite the shipped credits).
        lines = text.splitlines(keepends=True)
        last = max((i for i, l in enumerate(lines) if l.startswith('- ') and ': Poly Haven (https://polyhaven.com/a/' in l and l.rstrip().endswith('CC0')), default=len(lines) - 1)
        path.write_text(''.join(lines[:last + 1] + add + lines[last + 1:]), encoding='utf-8')


def main():
    if '--meta' in sys.argv:
        for place in [a for a in sys.argv[1:] if a != '--meta'] or list(PLACES):
            meta_only(place)
        return
    want = sys.argv[1:] or list(PLACES)
    with get('https://api.polyhaven.com/assets?t=textures') as r:
        info = json.load(r)
    for place in want:
        build(place, PLACES[place], info)
    credit({layer[1] for p in want for layer in PLACES[p]})


if __name__ == '__main__':
    main()
