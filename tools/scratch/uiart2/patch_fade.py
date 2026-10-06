p2 = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge\chain.py'
t = open(p2, encoding='utf-8').read()
a = t.index('def title(')
b = t.index('MAKE = {')
new = '''def title(side="r", samples=64, length=220, link=(24, 14, 2.0), gap=8.0, fade=70.0):
    """ornaments/title_chain_SIDE.png, length x 40 shown: the chain either side of a page's
    title, as if the name had broken it. It runs in from beyond the plaque, fading as it goes
    out, and ends at the title in a link pried open at its end, ember in the break. Rendered for
    each side, so both are lit from the upper left (a mirrored one would cast its shadow the
    wrong way)."""
    W, H = int(length), 40
    y = H / 2
    near, far = (12.0, W + 30.0) if side == "r" else (W - 12.0, -30.0)
    spec = {"size": [W * 2, H * 2], "ss": 2, "samples": samples,
            "link": {"length": link[0] * 2, "width": link[1] * 2, "wire": link[2] * 2},
            "chains": [{"from": [min(near, far) * 2, y * 2], "to": [max(near, far) * 2, y * 2], "sag": 4,
                        "open": "first" if side == "r" else "last", "gap": gap * 2, "where": "end"}],
            "staples": [], "ember": 6.0}
    img = ember_glow(render(spec, f"title_{side}"))
    # Its outer end fades into the band, as a chain running on out of sight.
    x = (np.arange(img.shape[1], dtype=np.float32) + 0.5) / 2
    d = (W - x) if side == "r" else x
    img[..., 3] *= np.clip(d / fade, 0, 1) ** 1.4
    return img


'''
t = t[:a] + new + t[b:]
open(p2, 'w', encoding='utf-8').write(t)

p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge\blender_chainline.py'
s = open(p, encoding='utf-8').read()
s = s.replace('''    ao.inputs["Distance"].default_value = 3.0 * U''', '''    ao.inputs["Distance"].default_value = 6.0 * U''')
s = s.replace('''    rk.inputs[1].default_value = 2.2''', '''    rk.inputs[1].default_value = 3.0''')
s = s.replace('''    base.inputs[6].default_value = B.hexc("#1c191e")''', '''    base.inputs[6].default_value = B.hexc("#1f1b1b")''')
open(p, 'w', encoding='utf-8').write(s)
print('ok')
