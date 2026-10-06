import sys
sys.path.insert(0, r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid3')
from edlib import edit

edit('tools/assets/heroine_paint.py', [
    ('''def hexc(h):''', '''def firm(L, k):
    """Paint laid thick: its body opaque (the skin showing through a thin coat
    turns blue to violet and blood to rust), its dry, broken edges still thin."""
    L[..., 3] = np.clip(L[..., 3] * k, 0, 1)
    return L


def hexc(h):'''),
    ('''    lay(L, cov, blue, 0.96, grain, through=0.3)
    return L''', '''    lay(L, cov, blue, 0.96, grain, through=0.3)
    return firm(L, 1.45)'''),
    ('''    lay(L, cov, red, 0.95, grain, through=0.35)
    return L''', '''    lay(L, cov, red, 0.95, grain, through=0.35)
    return firm(L, 1.4)'''),
    ('''    lay(L, cov, grey, 1.0, pigment(shape, seed + 5, 9, 0.35), through=0.3)
    return L''', '''    lay(L, cov, grey, 1.0, pigment(shape, seed + 5, 9, 0.35), through=0.3)
    return firm(L, 1.2)'''),
    ('''        lay(L, blur(rim.astype(np.float32), 2.0), hexc('#3a0406'), 0.35)
    return L''', '''        lay(L, blur(rim.astype(np.float32), 2.0), hexc('#3a0406'), 0.35)
    return firm(L, 1.35)'''),
])
