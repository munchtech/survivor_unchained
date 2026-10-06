p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge\blender_links.py'
s = open(p, encoding='utf-8').read()
s = s.replace('''    jobs = [("face", k) for k in range(spec["variants"])] + [("edge", k) for k in range(spec["variants"])] + [("open", 0)]''',
              '''    jobs = [] if spec.get("only_eye") else \\
        [("face", k) for k in range(spec["variants"])] + [("edge", k) for k in range(spec["variants"])] + [("open", 0)]''')
open(p, 'w', encoding='utf-8').write(s)

p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge\chain.py'
s = open(p, encoding='utf-8').read()
s = s.replace('''def links(variants=6, samples=64, link=(30, 19, 3.2), cell=(52, 44), ss=3):''',
              '''def links(variants=6, samples=64, link=(30, 19, 3.2), cell=(52, 44), ss=3, only_eye=False):''')
s = s.replace('''            "eye": {"r": 11.5 * 2, "bar": 2.7 * 2, "lean": 35}}''', '''            "eye": {"r": 11.5 * 2, "bar": 2.7 * 2, "lean": 35}, "only_eye": only_eye}''')
s = s.replace('''    for f in os.listdir(d):
        if f.endswith(".png"):
            os.remove(os.path.join(d, f))
    r = subprocess.run([BLENDER, "-b", "-P", os.path.join(HERE, "blender_links.py"), "--", sp, d],
                       capture_output=True, text=True, timeout=3600)
    names = [f"{pre}{kind}_{k}" for pre in ("", "warm_", "hot_") for kind in ("face", "edge") for k in range(variants)] + ["open", "eye_back", "eye_front"]''', '''    names = [f"{pre}{kind}_{k}" for pre in ("", "warm_", "hot_") for kind in ("face", "edge") for k in range(variants)] + ["open"]
    names = ["eye_back", "eye_front"] + ([] if only_eye else names)
    for f in names:
        if os.path.exists(os.path.join(d, f + ".png")):
            os.remove(os.path.join(d, f + ".png"))
    r = subprocess.run([BLENDER, "-b", "-P", os.path.join(HERE, "blender_links.py"), "--", sp, d],
                       capture_output=True, text=True, timeout=3600)''')
s = s.replace('''        img = deepen_shadow(F.downsample(img, (cell[0] * 2, cell[1] * 2)))''', '''        img = F.downsample(img, (cell[0] * 2, cell[1] * 2))
        img = img if nm == "eye_front" else deepen_shadow(img)''')
open(p, 'w', encoding='utf-8').write(s)

p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge\chainanim.py'
s = open(p, encoding='utf-8').read()
s = s.replace('''    for k in ("eyelet_left", "eyelet_right", "eyelet_hole"):
        S[k] = ld(k)''', '''    for k in ("eye_back", "eye_front", "tab"):
        S[k] = ld(k)''')
s = s.replace('''The chain is anchored, not faded (an alpha fade reads as an effect, not a thing): each end runs
into a forged eyelet set in the band, `run` px past the end tabs, and the links feed through it
as the chain slides, going into the dark of its hole; the eyelets are what the sag hangs from.''', '''The chain is anchored, not faded (an alpha fade reads as an effect, not a thing): each end runs
through an eye-bolt driven into the band, `run` px past the end tabs (under the ring's near arc,
over its far one), then straight on `tail` px to where a riveted tab of the band's goatskin
covers it; the links slide under the leather and are gone, nothing popping. The sag hangs
between the eyes.''')
a = s.index('    # The ember\'s light on the band under the heated links')
b = s.index('    return img\n\n\ndef run(')
new = '''    tail = meta.get("tail", 20)
    e0, e1 = x0, x1                       # the eyes; the chain runs on to the tabs beyond them
    t0x, t1x = e0 - tail, e1 + tail

    def yy(x):
        return y_at(x) if e0 <= x <= e1 else y0

    # The ember's light on the band under the heated links, flickering a little.
    cx = phase + chosen * p
    fl = 1 + 0.12 * math.sin(t * 23 + flicker_seed) + 0.08 * math.sin(t * 37.3 + 1.7 * flicker_seed)
    glow(img, cx, yy(cx) + 5, p * (heat + 0.9), 9, heat_colour(0.55), 0.14 * fl, s)
    n0 = int(math.floor((t0x - phase) / p)) - 1
    n1 = int(math.ceil((t1x - phase) / p)) + 1
    order = []
    for n in range(n0, n1 + 1):
        x = phase + n * p
        if x < t0x - p or x > t1x + p:
            continue
        ang = math.atan2(yy(x + 1) - yy(x - 1), 2)
        kind = "face" if n % 2 == 0 else "edge"
        k = (n * 7 + 3) % var
        d = abs(n - chosen)
        h = 1 - d / (heat + 1) if d <= heat else 0.0
        order.append((0 if kind == "face" else 1, n, x, yy(x), ang, kind, k, h))
    clip = (t0x, t1x)
    # The eyes' far arcs, shanks and shadows lie under the links.
    for ex in (e0, e1):
        lay(img, shrink("eye_back", S["eye_back"], s), ex, y0, 0.0, 1.0, s)
    # Face-on links first; those on edge pass through them and lie over their ends.
    for _, n, x, y, ang, kind, k, h in sorted(order, key=lambda o: o[0]):
        if n == chosen:
            lay(img, shrink("open", S["open"], s), x, y, ang, 1.0, s, clip)
        else:
            lay(img, shrink(f"{kind}_{k}", S[f"{kind}_{k}"], s), x, y, ang, 1.0, s, clip)
            if h > 0:
                # Cold to warm to hot: the same link drawn in each state.
                if h < 0.6:
                    lay(img, shrink(f"warm_{kind}_{k}", S[f"warm_{kind}_{k}"], s), x, y, ang, h / 0.6, s, clip)
                else:
                    lay(img, shrink(f"warm_{kind}_{k}", S[f"warm_{kind}_{k}"], s), x, y, ang, 1.0, s, clip)
                    lay(img, shrink(f"hot_{kind}_{k}", S[f"hot_{kind}_{k}"], s), x, y, ang, (h - 0.6) / 0.4, s, clip)
        if h > 0 and t0x < x < t1x:
            glow(img, x, y, p * 0.7, p * 0.45, heat_colour(h), 0.24 * h * fl, s)
    # The eyes' near arcs over the links passing through them; the tabs over the chain's ends.
    for ex in (e0, e1):
        lay(img, shrink("eye_front", S["eye_front"], s), ex, y0, 0.0, 1.0, s)
    for tx in (t0x, t1x):
        lay(img, shrink("tab", S["tab"], s), tx, y0, 0.0, 1.0, s)
'''
s = s[:a] + new + s[b:]
# remove the earlier, now unused, link loop bounds computed before (n0/n1 from x0/x1 stay harmless)
open(p, 'w', encoding='utf-8').write(s)

p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge\kit.py'
s = open(p, encoding='utf-8').read()
s = s.replace('''             ["chain/open.png", "chain/eyelet.png", "chain/eyelet_left.png", "chain/eyelet_right.png", "chain/eyelet_hole.png",
              "ornaments/title_chain_l.png", "ornaments/title_chain_r.png"])''', '''             ["chain/open.png", "chain/eye_back.png", "chain/eye_front.png", "chain/tab.png",
              "ornaments/title_chain_l.png", "ornaments/title_chain_r.png"])''')
s = s.replace('''GONE = ["chain/hot.png"]''', '''GONE = ["chain/hot.png", "chain/eyelet.png", "chain/eyelet_left.png", "chain/eyelet_right.png", "chain/eyelet_hole.png"]''')
open(p, 'w', encoding='utf-8').write(s)
print('ok')
