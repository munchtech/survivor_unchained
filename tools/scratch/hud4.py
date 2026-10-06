R = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src'
def edit(name, pairs):
    p = R + '\\' + name
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert old in s, (name, old[:90])
        s = s.replace(old, new, 1)
    open(p, 'w', encoding='utf-8', newline='').write(s)

edit(r'Game\Game.cs', [
("""                for (int i = 0; i < n; i++)
                {
                    double a = Rng.NextDouble() * Math.Tau, d = Args.Num("dist", 9) + Rng.NextDouble() * Args.Num("spread", 20);
                    hb.SpawnEnemy(parts.Length > 1 ? parts[1] : "risen", hb.Player.X + Math.Cos(a) * d, hb.Player.Z + Math.Sin(a) * d);
                }""",
"""                // A kind ending in ! comes as elites (pictures of the edge marks, elite fights).
                string kind = parts.Length > 1 ? parts[1].TrimEnd('!') : "risen";
                bool elite = parts.Length > 1 && parts[1].EndsWith('!');
                for (int i = 0; i < n; i++)
                {
                    double a = Rng.NextDouble() * Math.Tau, d = Args.Num("dist", 9) + Rng.NextDouble() * Args.Num("spread", 20);
                    hb.SpawnEnemy(kind, hb.Player.X + Math.Cos(a) * d, hb.Player.Z + Math.Sin(a) * d, elite ? new Battle.SpawnOpts { Elite = true } : null);
                }"""),
])
edit(r'Ui\GameHud.cs', [
("""Style.H(3, Glyphs.Icon(glyph, 17, col), Style.Label($"{Math.Ceiling(left)}", Style.UiBold, Style.Badge, col)));""",
"""Style.H(3, Glyphs.Icon(glyph, 17, col), Style.Label(left > 600 ? "" : $"{Math.Ceiling(left)}", Style.UiBold, Style.Badge, col)));"""),
])
print('done')
