"""strips.py: 1:1 tier strips (plain | etched | gilded) at the close and Calling cameras, from godot/.shots/armor4/."""
import os
from PIL import Image
O = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "godot", ".shots", "armor4")
for cam, box in (("close", (780, 560, 1220, 860)), ("look", (860, 360, 1080, 560))):
    cs = [Image.open(os.path.join(O, f"j_{t}_{cam}.png")).convert("RGB").crop(box) for t in ("plain", "etched", "gilded")]
    w, h = box[2] - box[0], box[3] - box[1]
    s = Image.new("RGB", (3 * w + 12, h))
    for i, c in enumerate(cs):
        s.paste(c, (i * (w + 6), 0))
    s.save(os.path.join(O, f"tier_strip_{cam}.png"))
    print("tier_strip_%s.png" % cam, box)
