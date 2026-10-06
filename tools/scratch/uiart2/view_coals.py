import os

import numpy as np
from PIL import Image

D = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\comfy\out\uiforge\coal\coal'
S = os.path.dirname(os.path.abspath(__file__))


def ld(n):
    return Image.open(os.path.join(D, n + '.png')).convert('RGBA')


bg = Image.new('RGBA', (240, 120), (30, 23, 24, 255))
dish = ld('dish')
rim = ld('dish_rim')
ox, oy = 36, 20
bg.alpha_composite(dish.resize((84, 36), Image.LANCZOS), (ox, oy))
for i, k in enumerate((0, 1, 2, 3, 1)):
    c = ld(f'coal_{k}').resize((18, 14), Image.LANCZOS)
    bg.alpha_composite(c, (ox + 12 + i * 12, oy + 9 + (i % 2) * 2))
bg.alpha_composite(rim.resize((84, 36), Image.LANCZOS), (ox, oy))
for k in range(4):
    bg.alpha_composite(ld(f'coal_{k}').resize((18, 14), Image.LANCZOS), (140 + k * 22, 80))
g = ld('numeral_glow').resize((60, 60), Image.LANCZOS)
bg.alpha_composite(g, (10, 58))
bg.save(os.path.join(S, 'coals_1to1.png'))
bg.resize((960, 480), Image.NEAREST).save(os.path.join(S, 'coals_4x.png'))
big = Image.new('RGBA', (900, 260), (30, 23, 24, 255))
big.alpha_composite(dish, (10, 10))
for k in range(4):
    big.alpha_composite(ld(f'coal_{k}').resize((108, 84), Image.LANCZOS), (200 + k * 120, 150))
big.alpha_composite(rim, (10, 120))
big.save(os.path.join(S, 'coals_file.png'))
print('ok')
