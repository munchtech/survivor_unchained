L = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a427a874da78cba8b\godot\logic"
def sub(path, old, new, count=1):
    t = open(path, encoding="utf-8").read()
    n = t.count(old)
    assert n == count, (path, old[:70], n)
    t = t.replace(old, new)
    open(path, "w", encoding="utf-8", newline="").write(t)

v = L + r"\Play\Story\Vault.cs"
sub(v, "double decSeed, rankT = 14;", "double decSeed, rankT = 18;")
sub(v, """decurion = A.Foe("mb_decurion", bx, bz, 4.5);""", """decurion = A.Foe("mb_decurion", bx, bz, 6);""")
sub(v, """if (line is { Broken: true } && lines < 2 && d.Hp > d.MaxHp * 0.3)""", """if (line is { Broken: true } && lines < 3 && d.Hp > d.MaxHp * 0.25)""")
sub(v, """            // Worked from its ends early, it forms again once.""", """            // Worked from its ends early, it forms again (twice).""")
sub(v, """scorpion = A.Foe("mb_old_quarrel", x, z, 3.2);""", """scorpion = A.Foe("mb_old_quarrel", x, z, 6);""")
sub(v, """            var s = scorpion!;
            var p = B.Player;
            A.Goal = (s.X, s.Z);""", """            var s = scorpion!;
            var p = B.Player;
            A.Goal = (s.X, s.Z);
            // Kneeling behind his engine's mantlet, little reaches him from down the hall: close on him under his
            // bolts, from cover to cover.
            s.TakenMul = Dist(p.X, p.Z, s.X, s.Z) > Mantlet ? 0.3 : 1;""")
sub(v, """        double scSeed, volleyT = 3, twosT = 6;
        int volleys;""", """        double scSeed, volleyT = 3, twosT = 6;
        int volleys;
        /// <summary>How near she must be to reach him past his engine.</summary>
        const double Mantlet = 9;""")
sub(v, """            ? new BossBar(scorpion!.Def.Name, scorpion.Def.Lesson, scorpion.Hp, scorpion.MaxHp, IsBoss: false)""",
"""            ? new BossBar(scorpion!.Def.Name, scorpion.TakenMul < 1 ? "Behind his engine: close on him from cover to cover" : scorpion.Def.Lesson, scorpion.Hp, scorpion.MaxHp, IsBoss: false, Shielded: scorpion.TakenMul < 1)""")
sub(v, """            double t = 0;
            foreach (var id in new[] { "std_a", "std_b", "std_c" })
            {
                var (x, z) = A.Place[id];
                if (Standard.Plant(A, x, z, 900) is { } s) { standards.Add(s); fileT.Add(4 + t); }""", """            double t = 0;
            // Each standard about as stout as a named foe of its stage (holy and fire break it the sooner).
            double hp = signifer != null ? signifer.MaxHp * 0.7 : 4000;
            foreach (var id in new[] { "std_a", "std_b", "std_c" })
            {
                var (x, z) = A.Place[id];
                if (Standard.Plant(A, x, z, hp) is { } s) { standards.Add(s); fileT.Add(4 + t); }""")

b = L + r"\Play\Bosses\BarrowLordStory.cs"
sub(b, "public override double HealthMul(int tier) => 96;", "public override double HealthMul(int tier) => 135;")
print("ok")
