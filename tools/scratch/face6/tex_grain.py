"""The grain in her paint as laid in UV space (face_paint.png) and as baked into her head's texture (heroine_head*.jpg),
over her face (the paint's alpha), at a few scales: std of luminance less its blur, over the mean."""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

w = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2f7b0f1283f6144a'
a = np.asarray(Image.open(w + r'\tools\assets\heroine_face\face_paint.png').convert('RGBA')).astype(np.float32) / 255
m = ndimage.binary_erosion(a[..., 3] > 0.95, iterations=40)
# (her cheeks and forehead only: no eyes, brows, lips: those in features)
f = np.asarray(Image.open(w + r'\godot\art\people\head_tex\heroine_features.png').convert('RGB').resize((4096, 4096))).astype(np.float32) / 255
m &= ndimage.binary_dilation(f[..., :2].max(-1) < 0.05, iterations=-1) if False else (ndimage.maximum_filter(f[..., :2].max(-1), 60) < 0.05)
print('mask texels', m.sum())


def lin(x):
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


for name, img in [('face_paint.png', a[..., :3])] + [(p.split('\\')[-1], np.asarray(Image.open(p).convert('RGB')).astype(np.float32) / 255) for p in sys.argv[1:]]:
    L = lin(img) @ [0.2126, 0.7152, 0.0722]
    out = []
    for s in (1.5, 3, 6, 12):
        hp = L - ndimage.gaussian_filter(L, s)
        out.append('s%-4g %.4f' % (s, hp[m].std() / L[m].mean()))
    print('%-28s' % name, '  '.join(out))
