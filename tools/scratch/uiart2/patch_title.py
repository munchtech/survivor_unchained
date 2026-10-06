p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge\kitboard.py'
s = open(p, encoding='utf-8').read()
s = s.replace('''def self2(cv: Canvas, src="kit", chain=True):''', '''def title_chain(cv: Canvas, cx, cy, text, font, size, src="kit", gap=8):
    """The broken chain either side of a title (ornaments/title_chain_l/_r.png), drawn at its
    own size from the title's ends outward, as Plaque lays it."""
    fnt = ImageFont.truetype(font_path(font), size)
    tw = fnt.getlength(text)
    s = cv.s
    for side in ("l", "r"):
        img = load(f"ornaments/title_chain_{side}.png", src)
        if img is None:
            continue
        w, h = img.shape[1] / 2, img.shape[0] / 2
        x = cx + tw / 2 + gap - 6 if side == "r" else cx - tw / 2 - gap - w + 6
        cv.over(resize(img, w * s, h * s), x * s, (cy - h / 2) * s)


def self2(cv: Canvas, src="kit", chain="title"):''')
s = s.replace('''    if chain:
        ch = load("frames/chain_band.png", src)''', '''    if chain == "band":
        ch = load("frames/chain_band.png", src)''')
s = s.replace('''    cv.text(960, 50, "WREN", "cinzel-700", 38, gold_hi, "ms")''', '''    if chain == "title":
        title_chain(cv, 960, 37, "WREN", "cinzel-700", 38, src)
    cv.text(960, 50, "WREN", "cinzel-700", 38, gold_hi, "ms")''')
s = s.replace('''          "self2_plain": lambda c, s_: self2(c, s_, chain=False)}''', '''          "self2_plain": lambda c, s_: self2(c, s_, chain=None),
          "self2_band": lambda c, s_: self2(c, s_, chain="band")}''')
open(p, 'w', encoding='utf-8').write(s)

import os
import shutil
R = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\comfy\out\uiforge'
os.makedirs(os.path.join(R, 'kit', 'ornaments'), exist_ok=True)
for side in 'lr':
    shutil.copyfile(os.path.join(R, 'chain', 'ornaments', f'title_chain_{side}.png'), os.path.join(R, 'kit', 'ornaments', f'title_chain_{side}.png'))
print('ok')
