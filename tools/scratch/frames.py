import sys, imageio.v3 as iio
from PIL import Image
# frames.py VIDEO OUT.jpg [N] : N evenly spaced frames tiled 4 across
src, out = sys.argv[1], sys.argv[2]; n = int(sys.argv[3]) if len(sys.argv) > 3 else 12
fr = list(iio.imiter(src)); print(len(fr), 'frames', fr[0].shape)
pick = [fr[round(i * (len(fr) - 1) / (n - 1))] for i in range(n)]
ims = [Image.fromarray(f) for f in pick]; w, h = ims[0].size; s = 400 / w; tw, th = int(w * s), int(h * s)
G = Image.new('RGB', (4 * tw + 12, ((n + 3) // 4) * (th + 4)), (255, 255, 255))
for i, im in enumerate(ims): G.paste(im.resize((tw, th)), ((i % 4) * (tw + 4), (i // 4) * (th + 4)))
G.save(out, quality=88)
