from PIL import Image, ImageDraw, ImageFont
S = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aab47bfdab5955dac\godot\.shots'
box = (600, 90, 1380, 950)
rows = ['default', 'vixen', 'sunborn']
w, h = (box[2] - box[0]) // 2, (box[3] - box[1]) // 2
o = Image.new('RGB', (w * 2 + 10, (h + 24) * 3), (16, 14, 18))
d = ImageDraw.Draw(o)
for r, n in enumerate(rows):
    for c, when in enumerate(['before', 'after']):
        im = Image.open(f'{S}\\{when}_{n}.png').convert('RGB').crop(box).resize((w, h))
        o.paste(im, (c * (w + 10), r * (h + 24) + 24))
        d.text((c * (w + 10) + 6, r * (h + 24) + 6), f'{n}: {when}', fill=(230, 210, 170))
o.save(r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid5\look_light_ba.jpg', quality=92)
