#!/usr/bin/env python3
"""GPU-compressed textures: every image of the people and the world's kits as
KTX2 (Basis UASTC, zstd-supercompressed, with mipmaps).

    python3 tools/assets/ktx2.py [--keep] [dir ...]

A WebP is small on disk but decodes to four bytes a pixel in video memory,
and the game's sheets are 2K and 4K: about 1.8 GB if everything were up at
once. UASTC transcodes on the GPU's side to BC7 (or ASTC, ETC2) at one byte
a pixel, at the same resolution and close to lossless (about 50 dB on the
people's base colours; ETC1S, a quarter the size again, bands the smooth
cloth that the dyes read, so it is not used).

Per image, by what the materials use it for:
  base colour, emissive     sRGB
  normal                    linear, renormalised through the mip chain
  roughness, metal, AO      linear

The glTFs are rewritten to KHR_texture_basisu (required), and the WebPs they
used are removed unless --keep. A person's base colour also gets a 1024 px
readable copy (<name>.bake.webp, named in the image's extras): the crowd
bake paints its atlas on the CPU (src/render/bakePerson.ts), which a
compressed texture cannot give it.

Needs toktx from KTX-Software 4.x
(https://github.com/KhronosGroup/KTX-Software/releases; point TOKTX at the
binary, and LD_LIBRARY_PATH at its lib/, if it is not on PATH) and Pillow.
Run after tools/assets/people.py, figure.py and env.py, which write WebPs.
Encoding is slow (a 4K sheet takes most of a minute); files already encoded
and newer than their source are kept.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
DIRS = ['public/assets/people', 'public/assets/env/village', 'public/assets/env/nature', 'public/assets/env/props']
TOKTX = os.environ.get('TOKTX') or shutil.which('toktx')
BAKE = 1024  # the readable copies' size


def source_of(tex):
    if 'source' in tex:
        return tex['source']
    ext = tex.get('extensions', {})
    for k in ('EXT_texture_webp', 'KHR_texture_basisu'):
        if k in ext:
            return ext[k]['source']
    return None


def usage(gltfs):
    """uri -> set of slots ('base', 'emissive', 'normal', 'linear')."""
    out = {}
    for g in gltfs.values():
        for m in g.get('materials', []):
            pbr = m.get('pbrMetallicRoughness', {})
            for slot, t in (('base', pbr.get('baseColorTexture')), ('emissive', m.get('emissiveTexture')),
                            ('normal', m.get('normalTexture')), ('linear', pbr.get('metallicRoughnessTexture')),
                            ('linear', m.get('occlusionTexture'))):
                if not t:
                    continue
                uri = g['images'][source_of(g['textures'][t['index']])]['uri']
                out.setdefault(uri, set()).add(slot)
    return out


def encode(src: Path, dst: Path, slots: set):
    if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
        return 'kept'
    srgb = bool(slots & {'base', 'emissive'})
    normal = 'normal' in slots
    if srgb and (normal or 'linear' in slots):
        raise SystemExit(f'{src.name} is used as both colour and data: {slots}')
    im = Image.open(src)
    if im.mode == 'RGBA' and im.getchannel('A').getextrema()[0] == 255:
        im = im.convert('RGB')
    elif im.mode not in ('RGB', 'RGBA'):
        im = im.convert('RGBA' if 'A' in im.mode else 'RGB')
    with tempfile.TemporaryDirectory() as tmp:
        png = Path(tmp) / 'in.png'
        im.save(png)
        cmd = [TOKTX, '--t2', '--encode', 'uastc', '--uastc_quality', '1',
               '--uastc_rdo_l', '0.25' if normal else '1.0', '--zcmp', '18', '--genmipmap',
               '--assign_oetf', 'srgb' if srgb else 'linear']
        if normal:
            cmd.append('--normalize')
        subprocess.run(cmd + [str(dst), str(png)], check=True, capture_output=True)
    return 'encoded'


def convert(folder: Path, keep: bool):
    paths = sorted(folder.glob('*.gltf'))
    gltfs = {p: json.loads(p.read_text()) for p in paths}
    uses = usage(gltfs)
    people = folder.name == 'people'
    todo = [(u, s) for u, s in uses.items() if u.endswith('.webp')]
    print(f'{folder.relative_to(ROOT)}: {len(paths)} glTF, {len(todo)} images to encode')

    def job(item):
        uri, slots = item
        src = folder / uri
        r = encode(src, src.with_suffix('.ktx2'), slots)
        if people and 'base' in slots:
            bake = src.with_name(src.stem + '.bake.webp')
            if not bake.exists() or bake.stat().st_mtime < src.stat().st_mtime:
                im = Image.open(src)
                im.thumbnail((BAKE, BAKE), Image.LANCZOS)
                im.save(bake, quality=90, method=6)
        return f'  {uri}: {r} ({"/".join(sorted(slots))})'

    with ThreadPoolExecutor(max_workers=3) as ex:
        for line in ex.map(job, todo):
            print(line, flush=True)

    for p, g in gltfs.items():
        changed = False
        for tex in g.get('textures', []):
            s = source_of(tex)
            if s is None:
                continue
            tex.pop('source', None)
            tex['extensions'] = {k: v for k, v in tex.get('extensions', {}).items() if k != 'EXT_texture_webp'}
            tex['extensions']['KHR_texture_basisu'] = {'source': s}
            changed = True
        for im in g.get('images', []):
            uri = im.get('uri', '')
            if uri.endswith('.webp'):
                slots = uses.get(uri, set())
                im['uri'] = uri[:-5] + '.ktx2'
                im['mimeType'] = 'image/ktx2'
                if people and 'base' in slots:
                    im.setdefault('extras', {})['readable'] = uri[:-5] + '.bake.webp'
                changed = True
        if not changed:
            continue
        for key in ('extensionsUsed', 'extensionsRequired'):
            ext = [e for e in g.get(key, []) if e != 'EXT_texture_webp']
            if 'KHR_texture_basisu' not in ext:
                ext.append('KHR_texture_basisu')
            g[key] = ext
        p.write_text(json.dumps(g, separators=(',', ':')))

    if not keep:
        for uri, _ in todo:
            (folder / uri).unlink(missing_ok=True)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    keep = '--keep' in sys.argv
    if not TOKTX:
        raise SystemExit('toktx not found: set TOKTX (see the header of this file)')
    for d in args or DIRS:
        convert(ROOT / d, keep)


if __name__ == '__main__':
    main()
