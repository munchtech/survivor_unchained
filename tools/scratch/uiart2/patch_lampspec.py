p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748\tools\uiforge\lamp.py'
s = open(p, encoding='utf-8').read()
old = '''SPEC = {"cell": [240, 400], "ss": 3, "samples": 128,
        "material": {"iron": "#262122", "rust": "#3a2012", "worn": "#e2dce6", "worn_rough": 0.14},
        "cage": {"y": 270, "h": 130, "r": 40, "bars": 6, "bar": 3.4},
        "chain": {"links": 8, "length": 38, "width": 23, "wire": 3.8}, "heat": [10, 28]}'''
assert old in s
s = s.replace(old, '''SPEC = {"cell": [440, 360], "ss": 3, "samples": 128,
        "material": {"iron": "#262122", "rust": "#3a2012", "worn": "#e2dce6", "worn_rough": 0.14},
        "cage": {"y": 230, "h": 130, "r": 40, "bars": 6, "bar": 3.4},
        "chain": {"links": 3, "length": 38, "width": 23, "wire": 3.8}, "heat": [10, 28],
        # Hung from a forged bracket on the panel's frame (Self is a side panel over the world).
        "bracket": {"arm": 150, "drop": 60, "bar": 4.2}}''')
s = s.replace('''  lamp/lamp.png       the lamp at rest, 120x200 shown, its chain running up off its top edge's middle
                      (draw it under the head band, so the chain goes up behind the rail)''', '''  lamp/lamp.png       the lamp at rest, 220x180 shown: the cage at x 110, hung by three links from a
                      forged bracket whose plate (x 186) is nailed to the side panel's left frame''')
open(p, 'w', encoding='utf-8').write(s)
print('ok')
