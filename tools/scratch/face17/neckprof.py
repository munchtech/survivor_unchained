"""neckprof.py IMG...: Oklab L down her neck's middle (a strip at the chin's x, 0.1 pupil-chin wide) from the chin to
1.0 pupil-chin below, in steps of 0.1, and the cheek's L, to see whether her neck is dark all down or only near the jaw."""
import sys, os
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
import meas
for n in sys.argv[1:]:
    p = next(q for q in (os.path.join(meas.S, n + '.png'), os.path.join(meas.R, n + '.png')) if os.path.exists(q))
    im = Image.open(p).convert('RGB'); a = np.asarray(im, np.float32) / 255
    up = 2 if im.height < 900 else 1
    L = meas.ff.detect(np.asarray(im.resize((im.width * up, im.height * up))))[:, :2] / up
    pup = (L[468] + L[473]) / 2; chin = L[152]; u = chin[1] - pup[1]; w = int(0.05 * u)
    out = []
    for t in np.arange(0.1, 1.01, 0.1):
        y = int(chin[1] + t * u)
        if y + 2 >= a.shape[0]: out.append('  -- '); continue
        c = np.median(a[y - 2:y + 3, int(chin[0]) - w:int(chin[0]) + w].reshape(-1, 3), 0)
        out.append('%.2f' % meas.ok(c)[0])
    ck = meas.spots(p)[0]['cheek']
    print('%-16s cheek %.2f | neck from chin: %s' % (n, ck[0], ' '.join(out)))
