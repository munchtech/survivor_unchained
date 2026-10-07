"""irisw.py img[@crop] ...: each eye's iris (MediaPipe's iris landmarks) against the eye: its diameter over the eye's
width (corner to corner), the aperture's height over its width, and how much of the iris the upper lid hides (the
iris's top above the upper lid's middle, over its diameter; negative: white shows above it)."""
import sys
import numpy as np
from PIL import Image
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aed215ba3ca60cc29\tools\assets")
import face_fit as ff  # noqa: E402

# (right eye: corners 33, 133; lids 159, 145; iris 468 centre, 469..472 round it. Left: 263, 362; 386, 374; 473; 474..477)
EYES = ((33, 133, 159, 145, 468, (469, 470, 471, 472)), (263, 362, 386, 374, 473, (474, 475, 476, 477)))
for p in sys.argv[1:]:
    crop = None
    if '@' in p:
        p, c = p.split('@')
        crop = [int(v) for v in c.split(',')]
    im = Image.open(p).convert('RGB')
    if crop:
        im = im.crop(crop)
    if im.height < 900:
        im = im.resize((im.width * 2, im.height * 2), Image.LANCZOS)
    L = ff.detect(np.asarray(im))
    if L is None or len(L) < 478:
        print(p, 'no face or no irises')
        continue
    L = L[:, :2]
    out = []
    for a, b, up, lo, c, ring in EYES:
        ew = np.linalg.norm(L[a] - L[b])
        q = L[list(ring)]
        d = np.linalg.norm(q[0] - q[2])            # (across)
        dv = np.linalg.norm(q[1] - q[3])           # (up and down)
        r = (d + dv) / 4
        top = L[c, 1] - r
        hidden = (L[up, 1] - top) / (2 * r)
        out.append((2 * r / ew, np.linalg.norm(L[up] - L[lo]) / ew, hidden))
    o = np.mean(out, 0)
    name = '/'.join(p.replace('\\', '/').split('/')[-2:])[-30:]
    print('%-30s iris/eye width %.3f  aperture h/w %.3f  iris hidden by upper lid %+.3f' % (name, *o))
