"""Before and after of a hand-over, side by side, aligned on the moment play begins.
python ba.py OUT BEFORE_GLOB BEFORE_END_INDEX AFTER_GLOB AFTER_END_INDEX [N_BEFORE_END] [N_AFTER_END]"""
import glob, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

FF = r"C:\Users\munch\AppData\Roaming\Python\Python314\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
out, bg, be, ag, ae = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], int(sys.argv[5])
pre = int(sys.argv[6]) if len(sys.argv) > 6 else 15
post = int(sys.argv[7]) if len(sys.argv) > 7 else 24
B, A = sorted(glob.glob(bg)), sorted(glob.glob(ag))
font = ImageFont.truetype("C:/Windows/Fonts/georgia.ttf", 30)
seq = os.path.join(HERE, out + "_seq")
os.makedirs(seq, exist_ok=True)
for f in glob.glob(os.path.join(seq, "*.png")):
    os.remove(f)
keys = []
for k in range(-pre, post):
    bi, ai = min(max(be + k, 0), len(B) - 1), min(max(ae + k, 0), len(A) - 1)
    im = Image.new("RGB", (1920, 600), (12, 12, 12))
    im.paste(Image.open(B[bi]).convert("RGB").resize((960, 540)), (0, 60))
    im.paste(Image.open(A[ai]).convert("RGB").resize((960, 540)), (960, 60))
    d = ImageDraw.Draw(im)
    t = k / 10
    d.text((20, 14), f"Before  ({'play' if k >= 0 else 'cinematic'} {t:+.1f} s)", fill=(235, 220, 200), font=font)
    d.text((980, 14), f"After  ({'play' if k >= 0 else 'cinematic'} {t:+.1f} s)", fill=(235, 220, 200), font=font)
    p = os.path.join(seq, f"{k + pre:04d}.png")
    im.save(p)
    if k in (-10, -1, 0, 1, 3, 10):
        keys.append(p)
subprocess.run([FF, "-y", "-loglevel", "error", "-framerate", "10", "-i", os.path.join(seq, "%04d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", os.path.join(HERE, out + ".mp4")])
sheet = Image.new("RGB", (1920, 600 * len(keys)))
for i, p in enumerate(keys):
    sheet.paste(Image.open(p), (0, 600 * i))
sheet.save(os.path.join(HERE, out + ".jpg"), quality=88)
print(os.path.join(HERE, out + ".mp4"), os.path.join(HERE, out + ".jpg"))
