"""features_blue.py: heroine_features.png's blue laid as heroine_features.py now lays it (the face paint's alpha,
softened), without a Blender run: red and green kept as they are."""
import numpy as np
from PIL import Image
from scipy import ndimage

w = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2'
p = w + r'\godot\art\people\head_tex\heroine_features.png'
f = np.asarray(Image.open(p).convert('RGBA')).copy()
SIZE = f.shape[0]
a = np.asarray(Image.open(w + r'\tools\assets\heroine_face\face_paint.png').convert('RGBA').resize((SIZE, SIZE), Image.BILINEAR), np.float32)[..., 3] / 255
# (heroine_features.py works bottom-up and flips as it saves: the same result in the image's own rows)
b = np.clip(ndimage.gaussian_filter(a, 6), 0, 1)
f[..., 2] = (b * 255 + 0.5).astype(np.uint8)
Image.fromarray(f).save(p)
print('blue laid: mean %.3f, >0.5 %.3f' % (b.mean(), (b > 0.5).mean()))
