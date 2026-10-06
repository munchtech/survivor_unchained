import json
import subprocess
from pathlib import Path

import numpy as np

W = Path(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa4f5fc266b043035')
S = Path(r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\anim')
G = r'C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe'
models = {'heroine': 'art/people/heroine.glb', 'female': 'assets/people/Superhero_Female_FullBody.gltf',
          'male': 'assets/people/Superhero_Male_FullBody.gltf', 'ual': 'assets/people/UAL1.glb'}
for k, m in models.items():
    out = S / f'sk_{k}.json'
    subprocess.run([G, '--headless', '--path', str(W / 'godot'), '-s', 'res://tools_scenes/anim_skeleton.gd', '--', str(out), f'res://{m}'],
                   capture_output=True, timeout=180)
    print(k, out.exists())


def load(p):
    return {b['name']: b for b in json.loads(Path(p).read_text())['bones']}


def cmp(a, b, label):
    rot = max(1 - abs(float(np.dot(a[n]['rot'], b[n]['rot']))) for n in a if n in b)
    gp = max(float(np.linalg.norm(np.array(a[n]['gpos']) - np.array(b[n]['gpos']))) for n in a if n in b)
    print(f'{label}: local rot diff {rot:.2e}, global pos diff {gp:.3f} m')
    return gp


cmp(load(W / 'tools/anim/data/heroine_skeleton.json'), load(S / 'sk_heroine.json'), 'heroine: stored vs now')
ual = load(W / 'tools/anim/data/ual_skeleton.json')
cmp(ual, load(S / 'sk_ual.json'), 'ual: stored vs now')
for k in ('female', 'male'):
    d = load(S / f'sk_{k}.json')
    cmp(ual, d, f'ual vs {k}')
    for n in ('pelvis', 'thigh_l', 'calf_l', 'foot_l', 'Head', 'upperarm_l', 'hand_l'):
        print(f'   {n:10s} {k} {np.round(d[n]["gpos"], 3)}  ual {np.round(ual[n]["gpos"], 3)}')
