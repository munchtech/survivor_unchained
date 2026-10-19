"""Luma stats: python lumstats.py [--crop x0,y0,x1,y1] files...  (crop applies to all after it until next --crop)
p5/p50/p95 luma (Rec.709 on sRGB 0-255), clip% (any channel >=250), sat (mean HSV S of pixels with luma>20),
pool = std/mean of luma on a 32x18 box-downsample (large-scale light pools vs flat), warmcool = mean (R-B) in top 10% vs bottom 30% luma."""
import sys, os
import numpy as np
from PIL import Image
args = sys.argv[1:]; crop = None
print(f"{'file':28s} {'p5':>4s} {'p50':>4s} {'p95':>4s} {'clip%':>6s} {'sat':>5s} {'pool':>5s} {'hiR-B':>6s} {'loR-B':>6s}")
i = 0
while i < len(args):
    a = args[i]
    if a == "--crop":
        crop = tuple(int(v) for v in args[i+1].split(",")); i += 2; continue
    im = Image.open(a).convert("RGB")
    if crop: im = im.crop(crop)
    x = np.asarray(im).astype(np.float32)
    L = 0.2126*x[...,0] + 0.7152*x[...,1] + 0.0722*x[...,2]
    p5, p50, p95 = np.percentile(L, [5, 50, 95])
    clip = (x.max(axis=2) >= 250).mean()*100
    mx = x.max(axis=2); mn = x.min(axis=2)
    S = np.where(mx > 0, (mx-mn)/np.maximum(mx, 1), 0)
    sat = S[L > 20].mean() if (L > 20).any() else 0
    small = np.asarray(Image.fromarray(L.astype(np.uint8)).resize((32, 18), Image.BOX)).astype(np.float32)
    pool = small.std()/max(small.mean(), 1)
    t = np.percentile(L, 90); b = np.percentile(L, 30)
    rb = x[...,0]-x[...,2]
    hi = rb[L >= t].mean(); lo = rb[L <= b].mean()
    print(f"{os.path.basename(a)[:28]:28s} {p5:4.0f} {p50:4.0f} {p95:4.0f} {clip:6.2f} {sat:5.2f} {pool:5.2f} {hi:6.1f} {lo:6.1f}")
    i += 1
