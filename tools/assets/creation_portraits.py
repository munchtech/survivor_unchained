"""Creation's portraits: the cameos of the Look step (godot/src/Ui/CreateLook.cs).

    python tools/assets/creation_portraits.py [hair|face|paint|look ...] [--sex female] [--raw DIR]

Each is the heroine as the game builds her, photographed in the game
(godot/tools_scenes/Portraits.cs) by a firelit portrait light, square:

- hair_<cut>.png: her head and shoulders, turned so the cut shows, her hair
  painted grey, with hair_<cut>_mask.png (white where her hair is) so the
  cameo dyes it the colour chosen (shaders/ui_cameo.gdshader). The mask is
  found by photographing her hair white and then black: what changes is hair.
- face_<face>.png: her face shaped as each face to start from (looks.json).
- paint_<paint>.png: her own face in each paint.
- look.png: her face and hair, for the look's invitation on the first step.

They land in godot/art/ui/create/<sex>/. Run it again whenever her head,
hair, faces or paints are rebuilt. A painted pass over them is the UI art
lead's (tools/comfy/ui_assets.json, docs/UI_ART_BRIEF.md 4.9).
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GODOT_DIR = os.path.join(ROOT, 'godot')
GODOT = os.environ.get('GODOT', r'C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe')
SIZE = 1024         # rendered (twice what is written: the hair's hashed edges average out)
OUT_SIZE = 512      # written
# Grey hair: the cameo multiplies it by the dye at twice its value (ui_cameo.gdshader).
GREY = '#808080'
# How each kind is framed (Portraits.cs views) and turned (degrees; her right cheek toward us).
# Her shoulders bare in the face's pictures (the stalker's outfit shows none of itself so high, and
# her head is up in its idle); the hair's go lower, so she wears the warden's mail there.
OUTFIT = 'stalker'
HAIR_OUTFIT = 'warden'
VIEW = {'hair': ('head', -40), 'face': ('face', -14), 'paint': ('face', -10), 'look': ('head', -22)}
# A cut that hangs behind her is seen nearer her profile.
CUT_YAW = {'ponytail': -78, 'braid': -100}
CUT_BACK = {'ponytail': 0.07, 'braid': 0.09}
# Her chin lifted a little (degrees) for each kind.
CHIN = {'hair': 4, 'face': 7, 'paint': 7, 'look': 6}


def jobs_for(kinds, hero):
    jobs = []
    if 'hair' in kinds:
        for cut in hero['cuts']:
            view, yaw = VIEW['hair']
            for tag, colour in (('g', GREY), ('w', '#ffffff'), ('k', '#000000')):
                jobs.append({'name': f"hair_{cut['id']}_{tag}", 'view': view, 'yaw': CUT_YAW.get(cut['id'], yaw), 'back': CUT_BACK.get(cut['id'], 0), 'hair': cut['id'], 'hairColor': colour, 'outfit': HAIR_OUTFIT, 'chin': CHIN['hair']})
    if 'face' in kinds:
        for f in hero['faces']:
            view, yaw = VIEW['face']
            jobs.append({'name': f"face_{f['id']}", 'view': view, 'yaw': yaw, 'hair': 'ponytail', 'face': f.get('shape', {}), 'outfit': OUTFIT, 'chin': CHIN['face']})
    if 'paint' in kinds:
        for p in hero['paints']:
            view, yaw = VIEW['paint']
            jobs.append({'name': f"paint_{p['id']}", 'view': view, 'yaw': yaw, 'hair': 'ponytail', 'paint': p['id'] if p['id'] != 'none' else '', 'outfit': OUTFIT, 'chin': CHIN['paint']})
    if 'look' in kinds:
        view, yaw = VIEW['look']
        jobs.append({'name': 'look', 'view': view, 'yaw': yaw, 'hair': 'long', 'outfit': OUTFIT, 'chin': CHIN['look']})
    return jobs


def render(jobs, raw):
    os.makedirs(raw, exist_ok=True)
    path = os.path.join(raw, 'jobs.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(jobs, f, indent=1)
    env = dict(os.environ, JOBS=path, OUT=raw, SIZE=str(SIZE))
    r = subprocess.run([GODOT, '--path', GODOT_DIR, '--resolution', '1280x720', '--script', 'res://tools_scenes/portraits.gd'],
                       env=env, capture_output=True, text=True, errors='replace')
    done = [l for l in r.stdout.splitlines() if l.startswith('PORTRAIT')]
    errs = [l for l in (r.stdout + r.stderr).splitlines() if 'ERROR' in l or 'Exception' in l]
    print(f'rendered {len(done)} of {len(jobs)}' + (f'; {len(errs)} errors, first: {errs[0]}' if errs else ''))


def load(p):
    return np.asarray(Image.open(p).convert('RGB'), np.float32) / 255


def save(a, path, mode='RGB'):
    img = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), mode)
    img.resize((OUT_SIZE, OUT_SIZE), Image.LANCZOS).save(path, optimize=True)


def lum(a):
    return a @ np.array([0.2126, 0.7152, 0.0722], np.float32)


def hair_mask(white, black):
    """Where her hair is: the share of each pixel's light that changed when her
    hair went from white to black (a shadowed lock changes little in light, but
    all of what it has; the highlight off its outside is not its colour)."""
    w, k = lum(white), lum(black)
    share = (w - k) / np.maximum(w, 0.03)
    m = np.clip((share - 0.12) / 0.45, 0, 1)
    img = Image.fromarray((m * 255).astype(np.uint8), 'L').filter(ImageFilter.GaussianBlur(0.8))
    return np.asarray(img, np.float32) / 255


def finish(kinds, hero, raw, out):
    os.makedirs(out, exist_ok=True)
    written = []
    if 'hair' in kinds:
        for cut in hero['cuts']:
            g = os.path.join(raw, f"hair_{cut['id']}_g.png")
            if not os.path.exists(g):
                continue
            save(load(g), os.path.join(out, f"hair_{cut['id']}.png"))
            m = hair_mask(load(os.path.join(raw, f"hair_{cut['id']}_w.png")), load(os.path.join(raw, f"hair_{cut['id']}_k.png")))
            save(m, os.path.join(out, f"hair_{cut['id']}_mask.png"), 'L')
            written += [f"hair_{cut['id']}", f"hair_{cut['id']}_mask"]
    for kind, items in (('face', hero['faces']), ('paint', hero['paints'])):
        if kind not in kinds:
            continue
        for it in items:
            src = os.path.join(raw, f"{kind}_{it['id']}.png")
            if os.path.exists(src):
                save(load(src), os.path.join(out, f"{kind}_{it['id']}.png"))
                written.append(f"{kind}_{it['id']}")
    if 'look' in kinds and os.path.exists(os.path.join(raw, 'look.png')):
        save(load(os.path.join(raw, 'look.png')), os.path.join(out, 'look.png'))
        written.append('look')
    print('wrote', len(written), 'to', out)


if __name__ == '__main__':
    args = sys.argv[1:]
    sex = args[args.index('--sex') + 1] if '--sex' in args else 'female'
    raw = args[args.index('--raw') + 1] if '--raw' in args else os.path.join(os.environ.get('TEMP', '.'), 'creation_portraits', sex)
    kinds = [a for a in args if a in ('hair', 'face', 'paint', 'look')] or ['hair', 'face', 'paint', 'look']
    with open(os.path.join(GODOT_DIR, 'data', 'content', 'looks.json'), encoding='utf-8') as f:
        hero = json.load(f)['heroes'][sex]
    if '--finish' not in args:
        render(jobs_for(kinds, hero), raw)
    finish(kinds, hero, raw, os.path.join(GODOT_DIR, 'art', 'ui', 'create', sex))
