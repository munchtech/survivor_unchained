"""heroine_hair.py: her hairline's fine hairs a material of their own (hair_fine, blended in the game), and her cap's
fade longer (blended, it no longer speckles)."""
p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2\tools\assets\heroine_hair.py'
s = open(p, encoding='utf-8').read()


def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (old, s.count(old))
    s = s.replace(old, new)


rep('''    (each card's alpha), a few astray. Two sets of cards."""''',
    '''    (each card's alpha), a few astray. Two sets of cards, of their own
    material (hair_fine: the game blends them over her skin, as faint as they
    are; cut by hashed alpha they were a scatter of dots)."""''')
rep('''    c = cards(P, RNG.uniform(0.003, 0.006, len(pts)), list(range(6, 16)), 0.0015)
    c["alpha"] = np.repeat(RNG.uniform(0.65, 1.0, len(pts)), 3 * points)
    out.append(c)''', '''    c = cards(P, RNG.uniform(0.003, 0.006, len(pts)), list(range(6, 16)), 0.0015)
    c["alpha"] = np.repeat(RNG.uniform(0.65, 1.0, len(pts)), 3 * points)
    c["mat"] = 3
    out.append(c)''')
rep('''    c = cards(P, RNG.uniform(0.0018, 0.0032, n), [14, 15], 0.0009, narrow=0.7)
    c["alpha"] = np.repeat(RNG.uniform(0.3, 0.55, n), 3 * k)
    out.append(c)''', '''    c = cards(P, RNG.uniform(0.0018, 0.0032, n), [14, 15], 0.0009, narrow=0.7)
    c["alpha"] = np.repeat(RNG.uniform(0.3, 0.55, n), 3 * k)
    c["mat"] = 3
    out.append(c)''')
rep('''        mat = c.get("mat", 0)                                # (0 cards; 1 a solid rope of hair, as the cap; 2 a tie)''',
    '''        mat = c.get("mat", 0)                                # (0 cards; 1 a solid rope of hair, as the cap; 2 a tie; 3 fine hairs)''')
rep('''        if mat == 0 and "arc" in c:''', '''        if mat in (0, 3) and "arc" in c:''')
rep('''    o.data.materials.append(tie_material())
    follow_head(o, at)''', '''    o.data.materials.append(tie_material())
    o.data.materials.append(hair_material("hair_fine", ATLAS))
    follow_head(o, at)''')
# the cap's fade: 6 mm was short to hide its hashed speckle; blended, it thins out over a centimetre
rep('''    2.5 cm; faded out over its first 6 mm over her hairline, unevenly (its
    alpha): her skin under it is darkened to her hair's colour there
    (People.HerScalp), and a long fade, its alpha hashed, read as a speckled,
    pixelated edge."""''', '''    2.5 cm; faded out over its first centimetre over her hairline, unevenly
    (its alpha), blended over her skin in the game (heroine_hair_soft.gdshader):
    cut by hashed alpha, a fade that long read as a speckled, pixelated edge,
    and one short enough not to, as a hard one."""''')
rep('''    fade = np.clip((V[:, 2] - hairline_z(theta) - 0.002 + 0.5 * wav) / 0.006, 0, 1)''',
    '''    fade = np.clip((V[:, 2] - hairline_z(theta) + 0.001 + 0.5 * wav) / 0.011, 0, 1)''')
open(p, 'w', encoding='utf-8', newline='').write(s)
print('ok')
