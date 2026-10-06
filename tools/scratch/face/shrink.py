"""shrink.py <out dir> <max width> img ... : copies at most that wide, JPEG 80."""
import os
import sys

from PIL import Image

out, w = sys.argv[1], int(sys.argv[2])
os.makedirs(out, exist_ok=True)
for p in sys.argv[3:]:
    im = Image.open(p).convert("RGB")
    if im.width > w:
        im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    dst = os.path.join(out, os.path.splitext(os.path.basename(p))[0] + ".jpg")
    im.save(dst, quality=80)
    print(dst, os.path.getsize(dst) // 1024, "KB")
