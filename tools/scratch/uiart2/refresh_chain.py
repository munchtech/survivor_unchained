import os
import shutil
import subprocess
import sys

from PIL import Image

WT = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748'
R = os.path.join(WT, 'tools', 'comfy', 'out', 'uiforge')
S = os.path.dirname(os.path.abspath(__file__))
for rel in ('ornaments/title_chain_l.png', 'ornaments/title_chain_r.png', 'frames/chain_swag.png', 'frames/chain_band.png'):
    src = os.path.join(R, 'chain', rel)
    if os.path.exists(src):
        os.makedirs(os.path.dirname(os.path.join(R, 'kit', rel)), exist_ok=True)
        shutil.copyfile(src, os.path.join(R, 'kit', rel))
page = sys.argv[1] if len(sys.argv) > 1 else 'self2'
scale = sys.argv[2] if len(sys.argv) > 2 else '1'
subprocess.run([sys.executable, os.path.join(WT, 'tools', 'uiforge', 'kitboard.py'), '--page', page, '--scale', scale], check=True, cwd=WT)
q = int(1080 * float(scale))
im = Image.open(os.path.join(R, 'kit', f'board_{page}_{q}.png')).convert('RGB')
k = float(scale)
im.crop((int(560 * k), 0, int(1360 * k), int(200 * k))).save(os.path.join(S, 'chain_crop.png'))
z = im.crop((int(680 * k), int(10 * k), int(1240 * k), int(70 * k)))
z.resize((int(z.width * 2.5 / k), int(z.height * 2.5 / k)), Image.LANCZOS).save(os.path.join(S, 'chain_zoom.png'))
print('ok')
