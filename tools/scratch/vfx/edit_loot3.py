p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abc6bbe020c7fe287\godot\src\Fx\BattleFx.Loot.cs"
s = open(p, encoding="utf-8").read()
pairs = [
    ('''                Column(p.X, gy, p.Z, 2.5f, 0.16f, Palette.Rarity[2], 0.6f);''',
     '''                Column(p.X, gy, p.Z, 2.5f, 0.2f, Palette.Rarity[2], 0.5f);'''),
    ('''                Column(p.X, gy, p.Z, 5f, 0.2f, Palette.Rarity[3], 0.8f * breath);
                Column(p.X, gy, p.Z, 5f * (0.9f + 0.1f * breath), 0.42f, Palette.Rarity[3], 0.2f * breath);''',
     '''                Column(p.X, gy, p.Z, 5f, 0.26f, Palette.Rarity[3], 0.75f * breath);'''),
    ('''        Column(p.X, gy, p.Z, H, 0.42f, colour, 0.55f * flicker);
        Column(p.X, gy, p.Z, H, 0.13f, new Color(colour.R, colour.G * 1.25f, colour.B * 1.6f), 0.9f * flicker);''',
     '''        Column(p.X, gy, p.Z, H, 0.6f, colour, 0.6f * flicker);
        Column(p.X, gy, p.Z, H, 0.2f, new Color(colour.R, colour.G * 1.2f, colour.B * 1.4f), 0.6f * flicker);'''),
]
for a, b in pairs:
    assert a in s, a[:60]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8").write(s)
print("ok")
