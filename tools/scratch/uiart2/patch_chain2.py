p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge\blender_chainline.py'
s = open(p, encoding='utf-8').read()
s = s.replace('''    base.inputs[6].default_value = B.hexc("#1f1b1b")
    base.inputs[7].default_value = B.hexc("#3a2214")''', '''    base.inputs[6].default_value = B.hexc(SPEC.get("iron", "#1f1b1b"))
    base.inputs[7].default_value = B.hexc(SPEC.get("rust", "#3a2214"))''')
s = s.replace('''    worn.inputs[7].default_value = B.hexc("#9c96a2")''', '''    worn.inputs[7].default_value = B.hexc(SPEC.get("worn", "#9c96a2"))''')
s = s.replace('''    rough2.inputs[3].default_value = 0.22''', '''    rough2.inputs[3].default_value = SPEC.get("worn_rough", 0.22)''')
s = s.replace('''U = B.U
''', '''U = B.U
SPEC = {}
''')
s = s.replace('''    spec = json.load(open(argv[0], encoding="utf-8"))
    out = argv[1]''', '''    spec = json.load(open(argv[0], encoding="utf-8"))
    SPEC.update(spec.get("material", {}))
    out = argv[1]''')
open(p, 'w', encoding='utf-8').write(s)

p2 = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge\chain.py'
t = open(p2, encoding='utf-8').read()
t = t.replace('''def title(side="r", samples=64, length=240, link=(28, 16, 2.3), gap=9.0, fade=80.0):''',
              '''# The iron's look, shared by every chain: dark in its hollows, rubbed bright where it is worked,
# so each link reads crisp at 1:1 (the coordinator: "slightly soft").
IRON = {"iron": "#161314", "rust": "#2c180e", "worn": "#d2ccd6", "worn_rough": 0.16}


def title(side="r", samples=96, length=270, link=(32, 19, 2.6), gap=10.0, fade=90.0, ss=3):''')
t = t.replace('''    spec = {"size": [W * 2, H * 2], "ss": 2, "samples": samples,
            "link": {"length": link[0] * 2, "width": link[1] * 2, "wire": link[2] * 2},
            "chains": [{"from": [min(near, far) * 2, y * 2], "to": [max(near, far) * 2, y * 2], "sag": 4,
                        "open": "first" if side == "r" else "last", "gap": gap * 2, "where": "end"}],
            "staples": [], "ember": 6.0}''', '''    spec = {"size": [W * 2, H * 2], "ss": ss, "samples": samples, "material": IRON,
            "link": {"length": link[0] * 2, "width": link[1] * 2, "wire": link[2] * 2},
            "chains": [{"from": [min(near, far) * 2, y * 2], "to": [max(near, far) * 2, y * 2], "sag": 4,
                        "open": "first" if side == "r" else "last", "gap": gap * 2, "where": "end"}],
            "staples": [], "ember": 6.0}''')
t = t.replace('''    W, H = int(length), 40
    y = H / 2''', '''    W, H = int(length), 44
    y = H / 2''')
open(p2, 'w', encoding='utf-8').write(t)
print('ok')
