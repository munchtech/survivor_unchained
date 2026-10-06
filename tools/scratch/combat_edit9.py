W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09c5a65f5a84319e\godot'

def edit(path, pairs):
    p = W + '\\' + path
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert a in s, (path, a[:70])
        s = s.replace(a, b, 1)
    open(p, 'w', encoding='utf-8').write(s)

edit(r'logic\Play\Zones\ArenaRun.cs', [
('''        if (!runUp && !won && Seconds >= End - 120) RunUp();''',
'''        if (!runUp && !won && Seconds >= End - 120) RunUp();
        if (makingWay.Count > 0) MakingWay();'''),
('''        boss = Spawn(BossDef, at.X, at.Z, true, SpawnStyle.Walk);
        script = ArenaBosses.For(BossDef, this);''',
'''        MakeWay();
        boss = Spawn(BossDef, at.X, at.Z, true, SpawnStyle.Walk);
        script = ArenaBosses.For(BossDef, this);'''),
('''    /* ------------------------------------------------- the boss's arena -- */''',
'''    /// <summary>Those falling back for their ruler, until they are out of sight.</summary>
    readonly HashSet<int> makingWay = new();

    /// <summary>The people make way for what rules them: past the share the horde is held
    /// at while the boss lives, the crowd falls back into the dark, the farthest first
    /// (gone once out of sight), so the boss does not arrive inside a crowd it cannot be
    /// seen in, and the share is the fight's from its first second, not once the survivor
    /// has mown down the half-hour's horde.</summary>
    void MakeWay()
    {
        var p = B!.Player;
        var crowd = B.Enemies.Living().Where(o => o.Disposition == Disposition.Hostile && !o.Elite && o.State != EnemyState.Dying).ToList();
        int keep = (int)(Target() * bossShare);
        foreach (var o in crowd.OrderByDescending(o => (o.X - p.X) * (o.X - p.X) + (o.Z - p.Z) * (o.Z - p.Z)).Take(Math.Max(0, crowd.Count - keep)))
        {
            o.Status[StatusKind.Fear] = new StatusSlot(5, 1, 1, 0);
            makingWay.Add(o.Id);
        }
    }

    void MakingWay()
    {
        var p = B!.Player;
        foreach (var id in makingWay.ToList())
        {
            var o = B.Enemies.Items[id];
            double d2 = (o.X - p.X) * (o.X - p.X) + (o.Z - p.Z) * (o.Z - p.Z);
            if (!o.Alive || o.State == EnemyState.Dying) makingWay.Remove(id);
            else if (d2 > 25 * 25) { B.Enemies.Release(o); makingWay.Remove(id); }
            // Cornered or slow, it turns back and is one of the share.
            else if (!o.Status.Has(StatusKind.Fear)) makingWay.Remove(id);
        }
    }

    /* ------------------------------------------------- the boss's arena -- */'''),
])
print("ok")
