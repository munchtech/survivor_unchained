from PIL import Image, ImageDraw
import os, sys
d = r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid2\paintprev'
names = sys.argv[1:] or ['kohl', 'rouge', 'woad', 'ochre', 'ash', 'blood', 'gilt', 'brows']
W = 500
ims = [Image.open(os.path.join(d, n + '.jpg')).crop((380, 560, 1720, 1620)) for n in names]
h = int(W * ims[0].height / ims[0].width)
cols = min(4, len(ims))
rows = (len(ims) + cols - 1) // cols
s = Image.new('RGB', (cols * W, rows * (h + 20)), (20, 20, 20))
dr = ImageDraw.Draw(s)
for i, (n, im) in enumerate(zip(names, ims)):
    x, y = (i % cols) * W, (i // cols) * (h + 20)
    s.paste(im.resize((W, h), Image.LANCZOS), (x, y + 20))
    dr.text((x + 5, y + 4), n, fill=(230, 220, 200))
s.save(os.path.join(d, '_all.jpg'), quality=90)
print(s.size)
