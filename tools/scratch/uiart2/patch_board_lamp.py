p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge\kitboard.py'
s = open(p, encoding='utf-8').read()
s = s.replace('''    def fill(self, x, y, w, h, rgb, a):''', '''    def add(self, img, x, y, gain=1.0):
        """Light added (straight-alpha img's colour times its alpha) at screen (x, y)."""
        x, y = int(round(x)), int(round(y))
        h, w = img.shape[:2]
        x0, y0, x1, y1 = max(0, x), max(0, y), min(self.W, x + w), min(self.H, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        part = img[y0 - y:y1 - y, x0 - x:x1 - x]
        self.rgb[y0:y1, x0:x1] = np.clip(self.rgb[y0:y1, x0:x1] + part[..., :3] * part[..., 3:4] * gain, 0, 1)

    def fill(self, x, y, w, h, rgb, a):''')
s = s.replace('''def self2(cv: Canvas, src="kit", chain="title", sel=1):''', '''LAMP = {"x": 470, "top": 86, "lit": False}


def lamp(cv: Canvas, src="kit", lit=False):
    """The lamp-iron (lamp/lamp.png, 60x140 shown, hung from its top edge's middle) at LAMP, and
    the light it throws on the page (lamp/light.png, its source at (260, 96) of 520x420)."""
    s = cv.s
    lp = load("lamp/lamp_lit.png" if lit else "lamp/lamp.png", src)
    li = load("lamp/light.png", src)
    if lp is None or li is None:
        return
    cx, top = LAMP["x"], LAMP["top"]
    coal_y = top + 95 + 5.5
    cv.add(resize(li, 520 * s, 420 * s), (cx - 260) * s, (coal_y - 96) * s, 1.6 if lit else 1.0)
    cv.over(resize(lp, 60 * s, 140 * s), (cx - 30) * s, top * s)


def self2(cv: Canvas, src="kit", chain="title", sel=1):''')
s = s.replace('''    cv.text(290, 520, "her figure, live 3D", "alegreya-400-italic", 15, "#4a423c", "ms", shadow=False)''', '''    cv.text(290, 520, "her figure, live 3D", "alegreya-400-italic", 15, "#4a423c", "ms", shadow=False)
    if LAMP.get("on"):
        lamp(cv, src, LAMP.get("lit", False))''')
s = s.replace('''          "self2_tabs": lambda c, s_: self2(c, s_, chain="tabs")}''', '''          "self2_tabs": lambda c, s_: self2(c, s_, chain="tabs"),
          "self2_lamp": lambda c, s_: (LAMP.update(on=True, lit=False), self2(c, s_, chain="tabs"))[1],
          "self2_lamp_lit": lambda c, s_: (LAMP.update(on=True, lit=True), self2(c, s_, chain="tabs"))[1]}''')
open(p, 'w', encoding='utf-8').write(s)
print('ok')
