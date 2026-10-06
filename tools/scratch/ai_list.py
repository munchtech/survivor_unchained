"""Write the appendix of AI-made shipped files (markdown), grouped by generator and folder, from the tracked file list."""
import collections, sys, re
tracked = [l.strip() for l in open(sys.argv[1], encoding='utf-8') if l.strip()]
files = [f for f in tracked if not f.endswith(('.import', '.uid'))]

KREA_FREE_UI = re.compile(r'^godot/art/ui/(icons/(glyph|prompt|map)/|cursors/|frames/focus\.png|bars/(ember|experience|health)_fill\.png|minimap/you\.png)')
groups = collections.OrderedDict()
def add(g, f):
    groups.setdefault(g, []).append(f)

for f in files:
    if f.startswith('godot/art/ui/create/'):
        add('Renders of the heroine (carry her Krea 2 face paint; body of unknown origin)', f)
    elif f.startswith('godot/art/ui/') and f.endswith('.png'):
        if KREA_FREE_UI.match(f):
            add('UI made without AI (forged in code or modelled in Blender, no paint-over)', f)
        else:
            add('Krea 2 turbo + darkbrush LoRA (painted, or a Blender/forge render painted over)', f)
    elif f.startswith('godot/art/fx/marks/'):
        add('Krea 2 turbo (ground marks, tools/comfy/marks.py)', f)
    elif f.startswith('godot/art/fx/fb/'):
        add('LTX 2.5 video (flipbooks, tools/comfy/fx_clips.py + flipbook.py)', f)
    elif re.match(r'^godot/art/sound/tell_', f):
        add('LTX 2.5 audio (tools/comfy/sfx_clips.py)', f)
    elif f in ('godot/art/people/head_tex/heroine_head.jpg', 'godot/art/people/head_tex/heroine_iris.png',
               'godot/art/people/head_tex/heroine_eye.png', 'godot/art/people/heroine.glb', 'godot/art/people/hero.glb'):
        add('Krea 2 turbo face and iris paint (heroine_face.py, heroine_eyes.py, hero_male_face.py; embedded in the .glb)', f)
    elif f.startswith('godot/art/vo/'):
        add('Voice placeholders: Maya1 performance, Seed-VC conversion, VoxCPM2-designed voice', f)
    elif f == 'godot/art/anim/folk.res':
        add('Kimodo-SOMA-RP motion (10 of its clips; the rest Mixamo and keyed)', f)

out = []
for g, fs in groups.items():
    out.append(f'\n### {g} ({len(fs)} files)\n')
    by = collections.OrderedDict()
    for f in sorted(fs):
        d, n = f.rsplit('/', 1)
        by.setdefault(d, []).append(n)
    for d, ns in by.items():
        out.append(f'- `{d}/`: ' + ', '.join(ns))
open(sys.argv[2], 'w', encoding='utf-8').write('\n'.join(out) + '\n')
for g, fs in groups.items():
    print(len(fs), g)
