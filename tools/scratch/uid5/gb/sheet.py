import sys
sys.path.insert(0, r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid5\gb')
from PIL import Image, ImageDraw
from gb import font, UI_B, UI, TEXT_I
S = r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid5\gb\out'
names = [('self', 'Self: her large; attributes as one row with spend and preview; traits as a level track; stats in aligned columns'),
         ('pack', 'Pack: a side panel; the doll with slots where they are worn, beside a 6x4 grid; cards open on the world side'),
         ('storeroom', "Storeroom: Rook's shelf left, your pack right, the world between; room grows by shelves"),
         ('trader', 'Trader: the merchant as a strip over a priced grid; buy back as a tab; the card and its compare'),
         ('bench', 'Bench: the person as a strip, the anvil, your gear; break down is held; the smith in the world')]
W, H, CAP = 960, 540, 46
o = Image.new('RGB', (W * 2, (H + CAP) * 3), (14, 14, 16))
d = ImageDraw.Draw(o)
for i, (n, cap) in enumerate(names):
    x, y = (i % 2) * W, (i // 2) * (H + CAP)
    o.paste(Image.open(f'{S}\\greybox_{n}.png').resize((W, H)), (x, y + CAP))
    d.text((x + 14, y + 12), cap, font=font(UI_B, 17), fill=(230, 220, 200))
x, y = W, 2 * (H + CAP) + CAP
notes = ['Greyboxes, 1920x1080, before any art. One frame per screen (the band or the panel);',
         'inside it only tone, spacing, type and thin rules. Empty slots are quiet recessed tiles',
         'naming what goes there; only filled slots carry colour (rarity). No empty panels:',
         'empty sections are one line. No "Read closely": hover or focus shows the card beside',
         'the thing, with the worn piece beside it and the changes marked.', '',
         'Research and the reason for each choice: docs/design/UI_RESEARCH.md']
for k, t in enumerate(notes):
    d.text((x + 30, y + 30 + k * 30), t, font=font(UI, 18), fill=(200, 196, 188))
o.save(r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid5\gb\greybox_sheet.jpg', quality=90)
