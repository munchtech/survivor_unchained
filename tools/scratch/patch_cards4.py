p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a1a394643aabfb169\tools\uiforge\cardcolour.py'
s = open(p, encoding='utf-8').read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b)


rep('''DENOISE = {"uncommon": (0.46, 0.54), "rare": (0.3, 0.38)}''', '''DENOISE = {"uncommon": (0.46, 0.54), "rare": (0.3, 0.38)}
# Even at 0.3 the paint cleans most of the rime away: the rare's painting is laid back over
# its dressing's light and colour (merge, keeping 0.6 of the dressing's). The bramble needs none.
KEEP = {"uncommon": None, "rare": 0.6}''')
rep('''    made = []
    for tag, paths in res.items():
        k = tag.split("_")[1]
        base = np.asarray(Image.open(guides[k]).convert("RGB"), np.float32) / 255
        for p in paths:
            out = p.replace("card3po_", "card3m_")
            Image.fromarray((np.clip(merge(base, p), 0, 1) * 255 + 0.5).astype(np.uint8)).save(out)
            made.append(out)
    return made''', '''    made = []
    for tag, paths in res.items():
        k = tag.split("_")[1]
        if KEEP[k] is None:
            made += paths
            continue
        base = np.asarray(Image.open(guides[k]).convert("RGB"), np.float32) / 255
        for p in paths:
            out = p.replace("card3po_", "card3m_")
            Image.fromarray((np.clip(merge(base, p, KEEP[k]), 0, 1) * 255 + 0.5).astype(np.uint8)).save(out)
            made.append(out)
    return made''')
rep('''def paint(kinds=None, n=2):
    """Every take of the dressed cards, painted over and saved on black as card3/NAME.png
    (what cards.fit cuts): the painting's detail on the guide's own colour and light."""''', '''def paint(kinds=None, n=2):
    """Every take of the dressed cards on black, as cards.fit cuts them: card3/card3po_* the
    paintings, card3/card3m_* the rare's laid back over its dressing."""''')
open(p, 'w', encoding='utf-8').write(s)

c = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a1a394643aabfb169\tools\uiforge\cards.py'
t = open(c, encoding='utf-8').read()
a = '''    "rare": ("card2_rare/card2_rare_650_1.png", ()),'''
assert t.count(a) == 1
t = t.replace(a, '''    # Louder: the common dressed with the Low Ford's rime, painted over (cardcolour.py).
    "rare": ("card3/card3m_rare_30_693_0.png", ()),''')
open(c, 'w', encoding='utf-8').write(t)
print('ok')
