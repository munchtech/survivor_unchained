p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge\valueglyphs.py'
s = open(p, encoding='utf-8').read()
old = s[s.index('    elif kind == "link_broken":'):s.index('    return fill, cut\n\n\ndef mark(')]
new = '''    elif kind in ("link_closed", "link_broken"):
        # Locked: a chain link hung shut on an iron staple, the staple's legs going down into
        # it, so it stands like a lock made of the chain. Unlocked: the staple's one leg pulled
        # out and swung up, the link left open below it.
        body_c = (12, 15.4)
        dB, _, _ = _link_sd(X, Y, body_c, (1.0, 0.0), 2.6, 4.6)
        body = cov(np.abs(dB) - bar * 1.05)

        def stroke(pts, w):
            d = np.full(X.shape, 1e9, np.float32)
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                dx, dy = bx - ax, by - ay
                t = np.clip(((X - ax) * dx + (Y - ay) * dy) / (dx * dx + dy * dy + 1e-9), 0, 1)
                d = np.minimum(d, np.hypot(X - ax - t * dx, Y - ay - t * dy))
            return cov(d - w)
        # The staple: a U of round bar, its legs at x 8.6 and 15.4.
        arc = [(8.6 + 6.8 * (0.5 - 0.5 * math.cos(a)), 7.6 - 3.6 * math.sin(a)) for a in np.linspace(0, math.pi, 24)]
        if kind == "link_closed":
            staple = stroke([(8.6, 13.2)] + arc + [(15.4, 13.2)], bar * 0.95)
            # Where the legs go into the link, the link's bar is cut so they pass behind it.
            fill = np.maximum(body, staple)
            cut = np.clip(cov(np.abs(dB) - bar * 1.05 - 0.75) - body, 0, 1) * 0 + \\
                (staple * (1 - stroke([(8.6, 14.0), (8.6, 12.0)], bar * 0.95)) * 0)
        else:
            # Swung up about its left leg by 35 degrees, its right leg out of the link.
            ang = math.radians(-35)
            ox, oy = 8.6, 11.0

            def rot(p):
                x, y = p[0] - ox, p[1] - oy
                return (ox + x * math.cos(ang) - y * math.sin(ang), oy + x * math.sin(ang) + y * math.cos(ang))
            pts = [rot(p) for p in [(8.6, 11.0)] + arc + [(15.4, 10.6)]]
            staple = stroke([(8.6, 13.2)] + pts, bar * 0.95)
            fill = np.maximum(body, staple)
'''
s = s.replace(old, new)
s = s.replace('''    if key in ("link_set", "link_broken"):''', '''    if key in ("link_set", "link_closed", "link_broken"):''')
s = s.replace('''        "zone", "zone_fire_enemy", "zone_venom", "link_set"]''', '''        "zone", "zone_fire_enemy", "zone_venom", "link_set", "link_closed", "link_broken"]''')
open(p, 'w', encoding='utf-8').write(s)
print('ok')
