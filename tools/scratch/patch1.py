import re

p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a1a394643aabfb169\tools\uiforge\emblems.py'
s = open(p, encoding='utf-8').read()
zooms = {
    'mirror': ('arcane', 0.9, (53, 52)), 'wraith': ('shadow', 0.92, (46, 52)), 'leap': ('physical', 0.95, (50, 51)),
    'blink': ('frost', 0.95, (50, 52)), 'smoke': ('shadow', 0.92, (50, 48)), 'echo': ('arcane', 0.9, (50, 52)),
    'embers': ('fire', 0.95, (52, 50)),
    'howl': ('blood', 0.95, (50, 50)), 'retaura': ('holy', 0.88, (50, 50)),
    'frostaura': ('frost', 0.95, (50, 50)), 'pyre': ('fire', 0.88, (50, 50)), 'risen': ('shadow', 0.9, (52, 54)),
    'herd': ('nature', 0.82, (50, 48)), 'tether': ('shadow', 0.88, (58, 52)), 'consecrate': ('holy', 0.95, (50, 54)),
    'drain': ('blood', 0.85, (56, 48)), 'static': ('storm', 0.9, (50, 50)), 'book': ('arcane', 0.95, (51, 51)),
}
for k, (sch, z, at) in zooms.items():
    m = re.search(r'def d_%s\(\):\n    """.*?"""\n    e = Emblem\("%s"\)' % (k, sch), s, re.S)
    assert m, k
    old = m.group(0)
    s = s.replace(old, old.replace('e = Emblem("%s")' % sch, 'e = Emblem("%s", %s, %s)' % (sch, z, at)))


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b)


rep('''    for x, y0 in ((26, 4), (74, 4), (34, 0), (66, 0)):
        e.lay(stroke([(x, y0), (x, y0 + 30)], 0.4, 2.4), "glow", 1, 1, light=0.8)''', '''    for x, y0 in ((26, 12), (74, 12), (33, 6), (67, 6)):
        e.lay(stroke([(x, y0), (x, y0 + 26)], 0.4, 2.4), "glow", 1, 1, light=0.8)''')
rep('for k, (rr, li) in enumerate(((r + 9, 0.35), (r + 16, 0.2))):', 'for k, (rr, li) in enumerate(((r + 7, 0.35), (r + 13, 0.2))):')
rep('''    for x in (26, 74):
        e.rope([(x, 12), (x, 88)], 4.4, "gold_dim", 5)
    for y in (10, 90):
        e.lay(stroke([(20, y), (80, y)], 7.5), "gold", 6, 3, grain=0.4, kind="hammer")
        for x in (26, 74):
            e.lay(circle(x, y, 3), "gold", 8, 2)''', '''    for x in (28, 72):
        e.rope([(x, 14), (x, 86)], 4.4, "gold_dim", 5)
    for y in (12, 88):
        e.lay(stroke([(25, y), (75, y)], 7.5), "gold", 6, 3, grain=0.4, kind="hammer")
        for x in (28, 72):
            e.lay(circle(x, y, 3), "gold", 8, 2)''')
rep('''    for r, w, li in ((44, 2.2, 0.55), (37, 1.4, 0.35)):
        e.lay(stroke(arc(50, 54, r, 0, 360, 160), w), "glow", 1, 1, light=li)''', '''    for r, w, li in ((41, 2.2, 0.55), (35, 1.4, 0.35)):
        e.lay(stroke(arc(50, 52, r, 0, 360, 160), w), "glow", 1, 1, light=li)''')

i0 = s.index('def d_feint():')
i1 = s.index('def d_hourglass():')
s = s[:i0] + '''def d_feint():
    """Fen Step: the thrust that meets nothing: a blade driven in, and where the body was, a
    curl of fen-mist turning away round its point."""
    e = Emblem("physical", 0.85, (48, 52))
    curl = bez((58, 30), (64, 8), (94, 10), (92, 34), 30) + bez((92, 34), (90, 52), (68, 54), (70, 40), 24)[1:]
    e.lay(swell(curl, 8.5, 0.6), "glow", 1, 3, light=1.0)
    e.lay(swell(bez((92, 34), (100, 58), (92, 80), (74, 90), 30), 5.0, 0.4), "glow", 1, 2, light=0.8)
    e.lay(swell(bez((80, 20), (92, 26), (96, 40), (90, 50), 20), 2.0, 0.3), "glow", 0.5, 1, light=0.5)
    blade = poly([(26, 80), (21, 75), (60, 40), (70, 33), (65, 45)])
    e.lay(blade, "steel", 5, 3, grain=0.3, kind="hammer")
    e.lay(stroke([(23, 78), (62, 43)], 1.2), "iron_dark", 5.5, 0.6)
    e.lay(stroke([(14, 70), (30, 86)], 5.5), "gold_dim", 6, 2.5, grain=0.4, kind="hammer")
    e.lay(stroke([(22, 78), (12, 88)], 6, 5), "leather", 5, 3, grain=0.5, kind="fine")
    e.rope([(20, 80), (13, 87)], 2.0, "gold_dim", 6)
    e.lay(circle(10, 90, 4), "gold_dim", 6, 2.5, grain=0.4, kind="hammer")
    return e


''' + s[i1:]

i0 = s.index('def d_umbral():')
i1 = s.index('def d_consecrate():')
s = s[:i0] + '''def d_umbral():
    """Umbral Bolt: a bolt of shadow tearing straight through, barbed in black iron, the dark
    streaming behind it and the air torn round it in rings."""
    e = Emblem("shadow", 0.95, (50, 50))
    o, d, n = np.array([60.0, 40.0]), np.array([1, -1]) / math.sqrt(2), np.array([1, 1]) / math.sqrt(2)

    def P(*uv):
        return [tuple(o + u * d + v * n) for u, v in uv]

    for v, w in ((0, 6), (-6, 3), (6, 3)):
        e.lay(stroke(P((-30, v), (-62, v * 1.6)), w, 0.4), "glow", 1, 1, light=0.9)
    for u, r in ((-18, 11), (-32, 8)):
        c = P((u, 0))[0]
        e.lay(cut(ellipse(c[0], c[1], 3.2, r, -45), ellipse(c[0], c[1], 1.8, r - 1.8, -45)), "glow", 0.5, 0.6, light=0.8)
    e.lay(stroke(P((-46, 0), (-4, 0)), 4.4), mat("#141020", 0.4, 0.4), 5, 2, grain=0.4, kind="hammer")
    for v in (-1, 1):
        e.lay(poly(P((-46, 0), (-40, 7 * v), (-30, 7 * v), (-34, 0))), mat("#241a34", 0.0, 0.7), 4, 1.5, grain=0.6)
    head = poly(P((26, 0), (2, -10), (6, -3.5), (-6, -3), (-6, 3), (6, 3.5), (2, 10)))
    e.lay(head, mat("#141020", 0.6, 0.3), 6, 3.5, grain=0.4, kind="hammer", light=0.12)
    for v in (-1, 1):
        e.lay(stroke(P((25, 0), (3, 9.2 * v)), 1.6, 0.8), "glow", 1, 0.8, light=1.8, z=6)
    e.lay(stroke(P((22, 0), (-2, 0)), 1.2, 0.4), "glow", 1, 0.6, light=1.2, z=6)
    return e


''' + s[i1:]
open(p, 'w', encoding='utf-8').write(s)
print(len(re.findall(r'e = Emblem\(', s)))
