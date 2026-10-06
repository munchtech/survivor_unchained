"""Render the tab chain's motion over the dressed Self's head band: frames, a strip, a GIF."""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

WT = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748'
sys.path.insert(0, os.path.join(WT, 'tools', 'uiforge'))
import chainanim  # noqa: E402
import forge as F  # noqa: E402
import kitboard as KB  # noqa: E402

S = os.path.dirname(os.path.abspath(__file__))
scale = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
redo_links = "--links" in sys.argv
if redo_links:
    import chain
    for rel, img in chain.links().items():
        p = os.path.join(chain.OUT, 'sprites', rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        F.save(F.to_pil(np.clip(img, 0, 1)), p)
W, H = int(620 * scale), int(100 * scale)


def band(sel):
    cv = KB.self2(KB.Canvas(1920, 1080, scale), "kit", chain="tabs", sel=sel)
    full = np.asarray(cv.image(), np.float32) / 255
    return np.dstack([full[:H, :W], np.ones((H, W), np.float32)])


bg, bg2 = band(1), band(3)
tabs = list(KB.TABS)
frames = chainanim.run(tabs, 1, 3, scale, bg=bg, y0=57.0, bg_after=bg2)
out = os.path.join(chainanim.CH, 'anim', f's{scale:g}')
os.makedirs(out, exist_ok=True)
pics = []
for i, f in enumerate(frames):
    im = F.to_pil(np.clip(f, 0, 1)).convert('RGB')
    im.save(os.path.join(out, f'f{i:03d}.png'))
    pics.append(im)
# A strip: every third frame, stacked, each labelled with its time.
pick = list(range(0, len(pics), 3))[:16]
strip = Image.new('RGB', (W, (H + 2) * len(pick)), (0, 0, 0))
for j, i in enumerate(pick):
    im = pics[i].copy()
    ImageDraw.Draw(im).text((W - 60, 4), f"{i / 60:.2f}s", fill=(230, 220, 200))
    strip.paste(im, (0, j * (H + 2)))
strip.save(os.path.join(S, f'tabchain_strip_{scale:g}.png'))
pics[0].save(os.path.join(S, f'tabchain_{scale:g}.gif'), save_all=True, append_images=pics[1:], duration=17, loop=0)
print(len(pics), 'frames', tabs)
