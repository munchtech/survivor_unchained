import os
import shutil
import sys

WT = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748'
S = os.path.dirname(os.path.abspath(__file__))
for n in ('normal', 'lit'):
    shutil.copyfile(os.path.join(S, f'lamp_b2_{n}.png'), os.path.join(WT, 'godot', '.shots', f'lamp_b2_self_{n}.png'))
shutil.copyfile(os.path.join(S, 'lamp_b2_zoom.png'), os.path.join(WT, 'godot', '.shots', 'lamp_b2_zoom3x.png'))
p = os.path.join(WT, 'tools', 'uiforge', 'kit.py')
s = open(p, encoding='utf-8').read()
s = s.replace('''             "embers": ["hud/spark.png", "hud/glint.png", "hud/pointer_legendary.png"]}''', '''             "embers": ["hud/spark.png", "hud/glint.png", "hud/pointer_legendary.png"],
             "lamp": ["lamp/lamp.png", "lamp/lamp_lit.png", "lamp/light.png"]}''')
open(p, 'w', encoding='utf-8').write(s)
print(s.count('"lamp": ["lamp/lamp.png"'))
