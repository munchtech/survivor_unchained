"""3-up strips of the tier frames at 1:1: the crop round the region where plain and gilded differ (the piece), padded."""
import sys, numpy as np
from PIL import Image
O = "godot/.shots/armor2/"
for cam in ("play", "look"):
    ims = [np.asarray(Image.open(f"{O}tier_plate_top_{t}_{cam}.png").convert("RGB")).astype(int) for t in ("plain", "etched", "gilded")]
    d = np.abs(ims[0] - ims[2]).sum(2) > 30
    ys, xs = np.nonzero(d)
    cy, cx = int(np.median(ys)), int(np.median(xs))
    h = max(160, int((np.percentile(ys, 98) - np.percentile(ys, 2)) * 1.6))
    w = max(160, int((np.percentile(xs, 98) - np.percentile(xs, 2)) * 1.6))
    y0, x0 = max(0, cy - h // 2), max(0, cx - w // 2)
    crops = [Image.fromarray(im[y0:y0 + h, x0:x0 + w].astype(np.uint8)) for im in ims]
    strip = Image.new("RGB", (sum(c.width for c in crops) + 8, max(c.height for c in crops)), (0, 0, 0))
    x = 0
    for c in crops:
        strip.paste(c, (x, 0)); x += c.width + 4
    strip.save(f"{O}tier_strip_{cam}.png")
    print(cam, "crop", (x0, y0, w, h), "differing px", int(d.sum()))
