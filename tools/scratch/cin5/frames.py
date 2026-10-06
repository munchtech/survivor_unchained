"""Pull frames from the animatic at given times; tile into sheets.
python frames.py VIDEO OUTPREFIX t1 t2 ... [--cols 2 --w 960]"""
import subprocess, sys, os
from PIL import Image, ImageDraw
FF = r"C:\Users\munch\vo-tools\ffmpeg\bin\ffmpeg.exe"
args = sys.argv[1:]
cols, w = 2, 960
if "--cols" in args:
    i = args.index("--cols"); cols = int(args[i+1]); del args[i:i+2]
if "--w" in args:
    i = args.index("--w"); w = int(args[i+1]); del args[i:i+2]
video, out = args[0], args[1]
times = [float(t) for t in args[2:]]
tmp = out + "_tmp"
os.makedirs(tmp, exist_ok=True)
ims = []
for t in times:
    p = os.path.join(tmp, f"{t:07.2f}.png")
    subprocess.run([FF, "-v", "error", "-y", "-ss", str(t), "-i", video, "-frames:v", "1", p], check=True)
    im = Image.open(p).convert("RGB")
    h = int(im.height * w / im.width)
    im = im.resize((w, h), Image.LANCZOS)
    ImageDraw.Draw(im).text((8, 8), f"{t:.2f}", fill=(255, 255, 0))
    ims.append(im)
rows = (len(ims) + cols - 1) // cols
h = ims[0].height
sheet = Image.new("RGB", (cols * w, rows * h), (40, 40, 40))
for i, im in enumerate(ims):
    sheet.paste(im, ((i % cols) * w, (i // cols) * h))
sheet.save(out + ".jpg", quality=88)
print(out + ".jpg", sheet.size)
