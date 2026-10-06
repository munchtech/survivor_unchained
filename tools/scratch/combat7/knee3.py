W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a427a874da78cba8b\godot\logic\Play\Bosses"
def sub(path, old, new, count=1):
    t = open(path, encoding="utf-8").read()
    n = t.count(old)
    assert n == count, (path, old[:60], n)
    t = t.replace(old, new)
    open(path, "w", encoding="utf-8", newline="").write(t)

r = W + r"\Redcowl.cs"
sub(r, """    readonly List<(Enemy E, double Seed)> lot = new();
""", """    readonly List<(Enemy E, double Seed)> lot = new();
    /// <summary>The men of a broken levy, loose in the yard: his people still, though not his lot's count.</summary>
    readonly List<(Enemy E, double Seed)> loose = new();
""")
sub(r, """            if (levy.Broken) levy = null;""", """            if (levy.Broken) { foreach (var m in levy.Men) loose.Add((m, m.Seed)); levy = null; }""")
sub(r, """        // The levy breaks, and its men are his lot now: they keep back from her with the rest while she
        // chooses (broken, they turned on her, and a player weighing his life fought a line of pikes).
        if (levy != null)
        {
            foreach (var m in levy.Men) lot.Add((m, m.Seed));
            levy.Break();
        }
        foreach (var l in lot) if (l.E.Alive && l.E.Seed == l.Seed) l.E.Status[StatusKind.Fear] = new StatusSlot(6, 1, 1, 0);""",
"""        // The levy breaks, and its men keep back from her with his lot while she chooses (broken, they
        // turned on her, and a player weighing his life fought a line of pikes).
        if (levy != null)
        {
            foreach (var m in levy.Men) loose.Add((m, m.Seed));
            levy.Break();
        }
        foreach (var l in lot.Concat(loose)) if (l.E.Alive && l.E.Seed == l.Seed) l.E.Status[StatusKind.Fear] = new StatusSlot(6, 1, 1, 0);""")
sub(r, """        if (goT < 0) foreach (var l in lot) if (""", """        if (goT < 0) foreach (var l in lot.Concat(loose)) if (""")
sub(r, """        foreach (var l in lot) if (l.E.Alive && l.E.Seed == l.Seed && l.E.State != EnemyState.Dying) l.E.Status[StatusKind.Fear] = new StatusSlot(6, 1, 1, 0);
        lot.Clear();""", """        foreach (var l in lot.Concat(loose)) if (l.E.Alive && l.E.Seed == l.Seed && l.E.State != EnemyState.Dying) l.E.Status[StatusKind.Fear] = new StatusSlot(6, 1, 1, 0);
        lot.Clear();
        loose.Clear();""")
print("ok")
