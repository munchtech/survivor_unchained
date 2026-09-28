#!/usr/bin/env python3
"""Gather the world's kits (Quaternius, CC0) into public/assets/env.

    python3 tools/assets/env.py [unpacked-root]

The root (default .packs) holds the packs as they unzip: the Medieval
Village MegaKit (modular houses), the Stylized Nature MegaKit (trees, rocks,
plants) and the Fantasy Props MegaKit (the furniture of a town). Each kit
lands in a folder of its own (village, nature, props), every model as glTF
with its textures shared by name and turned to WebP at full size. Vertex
colours stay (the kits use them: ambient occlusion on foliage, tints on
props); UV sets past the first go (nothing reads them). A manifest lists
each model's name and bounds, for the game's loader and for placing things.
Needs Pillow built with WebP.
"""
import json
import os
import shutil
import sys

from PIL import Image

ROOT = sys.argv[1] if len(sys.argv) > 1 else '.packs'
OUT = 'public/assets/env'

KITS = {
    'village': 'Medieval Village MegaKit/Medieval Village MegaKit[Standard]/glTF',
    'nature': 'Stylized Nature MegaKit/glTF',
    'props': 'Fantasy Props MegaKit/Exports/glTF',
}


def quality(name):
    n = name.lower()
    if 'normal' in n or 'orm' in n or 'roughness' in n:
        return 95
    return 92


def texture(src_dir, out_dir, uri):
    name = os.path.splitext(uri)[0]
    out = os.path.join(out_dir, name + '.webp')
    if not os.path.exists(out):
        im = Image.open(os.path.join(src_dir, uri))
        # Leaves and grass cut out by alpha keep it.
        im = im.convert('RGBA' if 'A' in im.getbands() or im.mode == 'P' else 'RGB')
        im.save(out, quality=quality(name), method=5)
    return name + '.webp'


def bounds(g):
    lo, hi = [1e9] * 3, [-1e9] * 3
    for m in g.get('meshes', []):
        for p in m['primitives']:
            a = g['accessors'][p['attributes']['POSITION']]
            for i in range(3):
                lo[i] = min(lo[i], a['min'][i])
                hi[i] = max(hi[i], a['max'][i])
    return [round(v, 3) for v in lo], [round(v, 3) for v in hi]


def main():
    manifest = {}
    for kit, rel in KITS.items():
        src = os.path.join(ROOT, rel)
        out = os.path.join(OUT, kit)
        os.makedirs(out, exist_ok=True)
        models = {}
        for f in sorted(os.listdir(src)):
            if not f.endswith('.gltf'):
                continue
            with open(os.path.join(src, f)) as fh:
                g = json.load(fh)
            for mesh in g.get('meshes', []):
                for prim in mesh['primitives']:
                    prim['attributes'] = {k: v for k, v in prim['attributes'].items() if not (k.startswith('TEXCOORD_') and k != 'TEXCOORD_0')}
            for img in g.get('images', []):
                img['uri'] = texture(src, out, img['uri'])
                img['mimeType'] = 'image/webp'
            for tex in g.get('textures', []):
                if 'source' in tex:
                    tex.setdefault('extensions', {})['EXT_texture_webp'] = {'source': tex.pop('source')}
            if g.get('textures'):
                for key in ('extensionsUsed', 'extensionsRequired'):
                    g[key] = sorted(set(g.get(key, [])) | {'EXT_texture_webp'})
            for buf in g.get('buffers', []):
                shutil.copyfile(os.path.join(src, buf['uri']), os.path.join(out, buf['uri']))
            with open(os.path.join(out, f), 'w') as fh:
                json.dump(g, fh, separators=(',', ':'))
            lo, hi = bounds(g)
            models[f[:-5]] = {'min': lo, 'max': hi}
        manifest[kit] = models
        size = sum(os.path.getsize(os.path.join(out, x)) for x in os.listdir(out))
        print(f'{kit}: {len(models)} models, {size / 1e6:.1f} MB')
    with open(os.path.join(OUT, 'manifest.json'), 'w') as fh:
        json.dump(manifest, fh, separators=(',', ':'))


main()
