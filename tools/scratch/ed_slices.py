p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\godot\src\Ui\UiArt.cs'
s = open(p, encoding='utf-8').read()
tile = ["paper", "tooltip", "tooltip_worn", "button", "button_hover", "button_pressed", "button_disabled", "button_primary",
        "button_primary_hover", "button_primary_pressed", "row_on", "toast", "prompt", "bar_track", "map_frame"]
import re
for name in tile:
    pat = re.compile(r'(\["' + name + r'"\] = new\("[^"]+", \d+, \d+, \d+, \d+)\),')
    s, n = pat.subn(r'\1, Tile: true),', s)
    assert n == 1, name
old = '["hint"] = new("frames/hint.png", 16, 16, 16, 16),'
assert old in s
s = s.replace(old, '// The note: its nail and its drop of wax in corners wider than the text keeps from.\n        ["hint"] = new("frames/hint.png", 40, 40, 40, 40, Tile: true, Clear: 14),')
open(p, 'w', encoding='utf-8').write(s)
print("ok")
