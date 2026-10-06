import os

from PIL import Image, ImageDraw

WT = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748'
K = os.path.join(WT, 'tools', 'comfy', 'out', 'uiforge', 'kit')
D = os.path.join(WT, 'godot', '.shots')


def lab(im, text):
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, len(text) * 7 + 12, 18), fill=(0, 0, 0))
    d.text((6, 4), text, fill=(235, 225, 205))
    return im


a = Image.open(os.path.join(K, 'board_self2_1080.png')).convert('RGB')
b = Image.open(os.path.join(K, 'board_self2_plain_1080.png')).convert('RGB')
q = Image.open(os.path.join(K, 'board_self2_1440.png')).convert('RGB')
box = (420, 0, 1500, 300)
w = Image.new('RGB', (1080, 612), (8, 8, 10))
w.paste(lab(b.crop(box), 'without the chain (1080, 1:1)'), (0, 0))
w.paste(lab(a.crop(box), 'with the chain (1080, 1:1)'), (0, 312))
w.save(os.path.join(D, 'motif_title_chain_1080.png'))
lab(q.crop((560, 0, 2000, 400)), 'with the chain (1440, 1:1)').save(os.path.join(D, 'motif_title_chain_1440.png'))
lab(a.copy(), 'Self, approved layout, dressed (board, 1080)').save(os.path.join(D, 'motif_self_board_1080.png'))
print('ok')
