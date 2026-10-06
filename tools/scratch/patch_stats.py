import os
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a72467cac33063d3a"
p = os.path.join(W, "tools", "uiforge", "valueglyphs.py")
s = open(p, encoding="utf-8").read()

# 1. The stats' marks: by the Stat enum's name, lower case (icons/glyph/stat_maxhealth.png ...).
a = s.index("def custom_mask(")
s = s[:a] + '''# The standing's lines (Book.cs, by Stat, lower case: stat_maxhealth ...), each a mark of the
# house: a line glyph where one says it, else a shape of our own (24-unit paths).
CIRCLE = "A{r} {r} 0 1 1 {x2} {y} A{r} {r} 0 1 1 {x1} {y} Z"


def ring(cx, cy, r):
    return f"M{cx - r} {cy} " + CIRCLE.format(r=r, x1=cx - r, x2=cx + r, y=cy)


STATS = {
    "stat_maxhealth": "heart",
    "stat_armor": [("fill", "M3.5 6 L8 2.5 L10 4.8 L14 4.8 L16 2.5 L20.5 6 L19 13.5 L17 19.5 L12 22 L7 19.5 L5 13.5 Z"),
                   ("cut", "M11.2 7.5 L12.8 7.5 L12.8 19.5 L11.2 19.5 Z"),
                   ("cut", "M6.5 8.5 L9.5 10.5 L9 12 L6 10.2 Z"), ("cut", "M17.5 8.5 L14.5 10.5 L15 12 L18 10.2 Z")],
    "stat_regen": [("fill", "M12 21.5 C3.5 15.5 2.5 10 4.5 6.5 C6.5 3.2 10.5 3.8 12 7 C13.5 3.8 17.5 3.2 19.5 6.5 "
                            "C21.5 10 20.5 15.5 12 21.5 Z"),
                   ("cut", "M12 7.6 L16 12 L13.4 12 L13.4 17 L10.6 17 L10.6 12 L8 12 Z")],
    "stat_healing": [("fill", "M9.8 2 L14.2 2 L14.2 4 L13.4 4 L13.4 8.4 C17.6 9.7 20.2 12.8 20.2 16.4 C20.2 20.4 16.6 22.6 "
                              "12 22.6 C7.4 22.6 3.8 20.4 3.8 16.4 C3.8 12.8 6.4 9.7 10.6 8.4 L10.6 4 L9.8 4 Z"),
                     ("cut", "M10.9 12.4 L13.1 12.4 L13.1 15 L15.7 15 L15.7 17.2 L13.1 17.2 L13.1 19.8 L10.9 19.8 "
                             "L10.9 17.2 L8.3 17.2 L8.3 15 L10.9 15 Z")],
    "stat_dodge": [("fill", "M3 19.5 C4.5 9.5 11.5 4.5 18.2 5.4 L18.6 2.4 L23 8.6 L16.4 11.6 L17 8.6 C12 8 7.4 11.6 6.3 20.2 Z"),
                   ("fill", ring(15.5, 16.5, 3.4))],
    "stat_damage": "sword",
    "stat_critchance": "crosshair",
    "stat_critdamage": [("fill", "M12 1.5 L14 8.5 L20.5 4 L16.5 10.5 L23 12 L16.5 13.8 L20.5 20 L14 15.6 L12 22.5 L10 15.6 "
                                 "L3.5 20 L7.5 13.8 L1 12 L7.5 10.5 L3.5 4 L10 8.5 Z"),
                        ("cut", ring(12, 12, 2.6))],
    "stat_cooldown": [("fill", "M9.5 10.8 L19.5 10.8 L22.8 12 L19.5 13.2 L9.5 13.2 Z"),
                      ("fill", "M8 8 L9.8 8 L9.8 16 L8 16 Z"), ("fill", "M4.2 11.1 L8 11.1 L8 12.9 L4.2 12.9 Z"),
                      ("fill", "M1.5 5.4 L11 5.4 L11 7 L1.5 7 Z"), ("fill", "M3 17 L12.5 17 L12.5 18.6 L3 18.6 Z")],
    "stat_area": [("fill", ring(12, 12, 3.2)), ("fill", ring(12, 12, 7.6)), ("cut", ring(12, 12, 6.0)),
                  ("fill", ring(12, 12, 11.4)), ("cut", ring(12, 12, 9.8))],
    "stat_movespeed": "boot",
    "stat_dashcharges": "dash",
    "stat_pickupradius": "magnet",
    "stat_xpgain": "sun",
    "stat_goldgain": [("fill", "M12 1.5 L22.5 12 L12 22.5 L1.5 12 Z"), ("cut", ring(12, 12, 3.4))],
}


''' + s[a:]

# 2. mark() knows them.
x = '''    if key in CUSTOM:
        body, cut = custom_mask(CUSTOM[key], S)'''
y = '''    if key in STATS:
        v = STATS[key]
        if isinstance(v, str):
            body, cut = G.bold(v, S, stroke=stroke)
        else:
            body, cut = custom_mask(v, S)
    elif key in CUSTOM:
        body, cut = custom_mask(CUSTOM[key], S)'''
assert x in s
s = s.replace(x, y)

# 3. Built with the rest.
x = '''def build(out_dir, keys=KEYS):'''
y = '''def build(out_dir, keys=KEYS + list(STATS)):'''
assert x in s
s = s.replace(x, y)
open(p, "w", encoding="utf-8").write(s)
print("ok")
