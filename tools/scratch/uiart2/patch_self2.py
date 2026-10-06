p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge\kitboard.py'
s = open(p, encoding='utf-8').read()
old_bd = '''def backdrop(cv: Canvas, src):
    """Backdrop(page: true): the vellum at 0.9, the bands' shades, the edges, the grain, the dark."""
    world(cv)
    vel = load("page/vellum.png", src)
    cv.tiled(vel, 0, 0, 1920, 1080, (1, 1, 1, 0.9))
    s = cv.s
    ys = np.arange(cv.H, dtype=np.float32)[:, None] / s
    for y0, hgt, down, depth in ((90, 70, True, 0.6), (975, 50, False, 0.45)):'''
new_bd = '''def backdrop(cv: Canvas, src, taper=None):
    """Backdrop(page: true): the vellum at 0.9, the bands' shades, the edges, the grain, the dark.
    `taper` (y0, y1): the page ends at its contents and fades into the world between them."""
    world(cv)
    vel = load("page/vellum.png", src)
    s = cv.s
    ys = np.arange(cv.H, dtype=np.float32)[:, None] / s
    if taper:
        under_ = cv.rgb.copy()
    cv.tiled(vel, 0, 0, 1920, 1080, (1, 1, 1, 0.9))
    if taper:
        t = np.clip((ys - taper[0]) / (taper[1] - taper[0]), 0, 1)
        f = (t * t * (3 - 2 * t))[..., None]
        cv.rgb[:] = cv.rgb * (1 - f) + under_ * f
    for y0, hgt, down, depth in ((90, 70, True, 0.6),) + (((975, 50, False, 0.45),) if not taper else ()):'''
assert old_bd in s
s = s.replace(old_bd, new_bd)
self2 = open(r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uiart2\self2_src.py', encoding='utf-8').read()
s = s.replace('def main():\n    args = sys.argv[1:]', self2 + '\n\ndef main():\n    args = sys.argv[1:]')
s = s.replace('''    cv = {"specimen": specimen, "pack": pack, "self": self_}[page](Canvas(1920, 1080, scale), src)''',
              '''    cv = {"specimen": specimen, "pack": pack, "self": self_, "self2": self2,
          "self2_plain": lambda c, s_: self2(c, s_, chain=False)}[page](Canvas(1920, 1080, scale), src)''')
open(p, 'w', encoding='utf-8').write(s)
print('patched')
