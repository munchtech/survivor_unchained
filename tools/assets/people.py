#!/usr/bin/env python3
"""Gather the people (Quaternius, CC0) into public/assets/people.

    python3 tools/assets/people.py [unpacked-root]
    python tools/assets/figure.py      (then: a woman's figure, see there)

The root holds the packs as they unzip (Universal Base Characters, Modular
Character Outfits - Fantasy, Universal Animation Library 1 and 2). Every part
the game uses lands in one flat folder, its textures shared by name and
turned to WebP at full resolution (4K outfits, 2K bodies): a tenth of the PNG
size and nothing lost to the eye. References the packs get wrong (a few point
at "_png.png" copies that were never shipped) are put right on the way.
Needs Pillow built with WebP.
"""
import json
import os
import shutil
import sys

from PIL import Image

ROOT = sys.argv[1] if len(sys.argv) > 1 else 'public/_q'
OUT = 'public/assets/people'

BASE = 'Universal Base Characters/Universal Base Characters[Standard]/Base Characters/Godot - UE'
OUTFITS = 'Modular Character Outfits - Fantasy/Modular Character Outfits - Fantasy[Standard]/Exports/glTF (Godot-Unreal)/Modular Parts'
HAIR = 'Universal Base Characters/Universal Base Characters[Standard]/Hairstyles/Rigged to Head Bone/glTF (Godot -Unreal)'
ANIMS = {
    'UAL1.glb': 'Universal Animation Library/Universal Animation Library[Standard]/Unreal-Godot/UAL1_Standard.glb',
    'UAL2.glb': 'Universal Animation Library 2/Universal Animation Library 2[Standard]/Unreal-Godot/UAL2_Standard.glb',
}

PARTS = {
    BASE: ['Superhero_Male_FullBody', 'Superhero_Female_FullBody'],
    OUTFITS: [
        f'{sex}_{outfit}_{piece}'
        for sex in ('Male', 'Female')
        for outfit in ('Peasant', 'Ranger')
        for piece in ('Arms', 'Body', 'Legs', 'Feet')
    ] + ['Male_Ranger_Feet_Boots', 'Male_Ranger_Head_Hood', 'Female_Ranger_Head_Hood',
         'Male_Ranger_Acc_Pauldron', 'Female_Ranger_Acc_Pauldrons'],
    HAIR: ['Hair_SimpleParted', 'Hair_Long', 'Hair_Buns', 'Hair_Buzzed', 'Hair_BuzzedFemale', 'Hair_Beard',
           'Eyebrows_Regular', 'Eyebrows_Female'],
}
# The male ranger's boots are named apart from the rest.
PARTS[OUTFITS].remove('Male_Ranger_Feet')

# Colour holds up to a little compression; normals and packed maps (their
# channels are separate data) are kept closer.
def quality(name):
    return 92 if 'BaseColor' in name or name.endswith('_Dark') or 'Eye_Brown' in name else 96


def texture(folder, uri):
    """The WebP for a PNG the part names, converted once."""
    path = os.path.join(ROOT, folder, uri)
    if not os.path.exists(path):
        fixed = uri.replace('_png.png', '.png')
        path = os.path.join(ROOT, folder, fixed)
        if not os.path.exists(path):
            raise SystemExit(f'missing texture {uri} in {folder}')
        uri = fixed
    name = os.path.splitext(uri)[0]
    out = os.path.join(OUT, name + '.webp')
    if not os.path.exists(out):
        im = Image.open(path)
        im = im.convert('RGBA' if im.mode in ('RGBA', 'LA', 'P') and 'A' in im.getbands() else 'RGB')
        im.save(out, quality=quality(name), method=5)
        print(f'  {name}.webp {im.size[0]}x{im.size[1]} {os.path.getsize(out) // 1024} KB')
    return name + '.webp'


def part(folder, name):
    src = os.path.join(ROOT, folder, name + '.gltf')
    with open(src) as f:
        g = json.load(f)
    # Vertex colours here are all white and the extra UV sets unused: left
    # in, a loader would upload them and switch vertex colours on.
    for mesh in g.get('meshes', []):
        for prim in mesh['primitives']:
            prim['attributes'] = {k: v for k, v in prim['attributes'].items() if not (k.startswith('COLOR_') or (k.startswith('TEXCOORD_') and k != 'TEXCOORD_0'))}
    for img in g.get('images', []):
        img['uri'] = texture(folder, img['uri'])
        img['mimeType'] = 'image/webp'
    # Declare the WebP (EXT_texture_webp): each texture's image moves into
    # the extension, which a loader must understand.
    for tex in g.get('textures', []):
        if 'source' in tex:
            tex.setdefault('extensions', {})['EXT_texture_webp'] = {'source': tex.pop('source')}
    for key in ('extensionsUsed', 'extensionsRequired'):
        g[key] = sorted(set(g.get(key, [])) | {'EXT_texture_webp'})
    for buf in g.get('buffers', []):
        shutil.copyfile(os.path.join(ROOT, folder, buf['uri']), os.path.join(OUT, buf['uri']))
    with open(os.path.join(OUT, name + '.gltf'), 'w') as f:
        json.dump(g, f, separators=(',', ':'))
    print(name)


def main():
    os.makedirs(OUT, exist_ok=True)
    for folder, names in PARTS.items():
        for name in names:
            part(folder, name)
    for dst, src in ANIMS.items():
        shutil.copyfile(os.path.join(ROOT, src), os.path.join(OUT, dst))
        print(dst)
    total = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT))
    print(f'{OUT}: {total / 1e6:.1f} MB')
    print('Now shape the women: python tools/assets/figure.py (needs numpy).')


main()
