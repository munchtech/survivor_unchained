W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a427a874da78cba8b\godot\logic\Play\Bosses"
def sub(path, old, new, count=1):
    t = open(path, encoding="utf-8").read()
    n = t.count(old)
    assert n == count, (path, old[:60], n)
    t = t.replace(old, new)
    open(path, "w", encoding="utf-8", newline="").write(t)

g = W + r"\Greymuzzle.cs"
sub(g, """    readonly List<Wolf> ring = new(), guard = new();
""", """    readonly List<Wolf> ring = new(), guard = new();
    /// <summary>The ring's wolves once it has broken and come in: ordinary wolves, but still his Pack.</summary>
    readonly List<(Enemy E, double Seed)> loose = new();
""")
sub(g, """            if (n++ < 12) { w.E.Scripted = false; w.E.Disposition = Disposition.Hostile; w.E.Target = -1; }""",
"""            if (n++ < 12) { w.E.Scripted = false; w.E.Disposition = Disposition.Hostile; w.E.Target = -1; loose.Add((w.E, w.Seed)); }""")
sub(g, """        S.Bark(e.X, e.Z, "His legs go. He lies on his side, breathing hard, and the ring lies down where it stands.", null);
""", """        S.Bark(e.X, e.Z, "His legs go. He lies on his side, breathing hard, and the ring lies down where it stands.", null);
        // A broken ring's wolves lie down where they stand too: the fight is over, however long she takes to
        // choose (they fought on, and a player weighing his life was bitten while she did).
        foreach (var (le, seed) in loose)
        {
            if (!le.Alive || le.Seed != seed || le.State == EnemyState.Dying) continue;
            le.Scripted = true;
            le.Target = -1;
            S.Script(le, (x, _) =>
            {
                x.Provoked = false;
                x.Disposition = Disposition.Neutral;
                x.Vx = x.Vz = 0;
                x.State = EnemyState.Idle;
                x.Anim = EnemyAnim.Idle;
                return true;
            });
        }
""")
sub(g, """        foreach (var w in ring.Concat(guard)) if (Here(w)) B.Enemies.Release(w.E);
        ring.Clear();
        guard.Clear();""", """        foreach (var w in ring.Concat(guard)) if (Here(w)) B.Enemies.Release(w.E);
        foreach (var (le, seed) in loose) if (le.Alive && le.Seed == seed && le.State != EnemyState.Dying) B.Enemies.Release(le);
        ring.Clear();
        guard.Clear();
        loose.Clear();""")
print("ok")
