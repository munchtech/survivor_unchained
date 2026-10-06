"""Join renders into one sheet: python sheet.py out.jpg height a.png b.png ..."""
import sys
from PIL import Image
out, h = sys.argv[1], int(sys.argv[2])
ims = [Image.open(f).convert("RGB") for f in sys.argv[3:]]
ims = [i.resize((int(i.width * h / i.height), h), Image.LANCZOS) for i in ims]
s = Image.new("RGB", (sum(i.width for i in ims), h))
x = 0
for i in ims:
    s.paste(i, (x, 0))
    x += i.width
s.save(out, quality=92)
print(out, s.size)
