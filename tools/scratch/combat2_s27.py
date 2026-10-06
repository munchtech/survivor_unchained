W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "tests/MapTests.cs": [
        ("""        Step(r, 1);
        // Only what is near the start is set down; nothing roused while she stands still.
        Assert.InRange(r.Zone.PacksPlaced, 1, 6);
        Assert.True(r.Zone.PackCount >= 20);
        Assert.DoesNotContain(r.B.Enemies.Living(), e => e.Roused);
        Assert.All(r.B.Enemies.Living(), e => Assert.Equal(r.Zone.Chart.Level, e.Level - (e.Elite ? 1 : 0)));
        // Walked to one, it wakes, and its own with it.
        var e = r.B.Enemies.Living().First();
        r.B.Player.X = e.X + 6; r.B.Player.Z = e.Z;
        Step(r, 0.5);
        Assert.Contains(r.B.Enemies.Living(), x => x.Roused);""",
         """        Step(r, 1);
        // Only what is near the start is set down.
        Assert.True(r.Zone.PackCount >= 20);
        Assert.True(r.Zone.PacksPlaced < r.Zone.PackCount / 4, $"{r.Zone.PacksPlaced} of {r.Zone.PackCount} set down at the start");
        // Come within sight of one: it is set down, resting, at the map's level (its leader a level up).
        var (sx, sz) = r.Zone.Standing.OrderBy(s => (s.X - r.Map.Start.X) * (s.X - r.Map.Start.X) + (s.Z - r.Map.Start.Z) * (s.Z - r.Map.Start.Z)).First();
        r.B.Player.X = sx + 30; r.B.Player.Z = sz;
        Step(r, 0.2);
        Assert.NotEmpty(r.B.Enemies.Living());
        Assert.DoesNotContain(r.B.Enemies.Living(), e => e.Roused);
        Assert.All(r.B.Enemies.Living(), e => Assert.Equal(r.Zone.Chart.Level, e.Level - (e.Elite ? 1 : 0)));
        // Walked up to, it wakes, and its own with it.
        var near = r.B.Enemies.Living().OrderBy(e => (e.X - sx) * (e.X - sx) + (e.Z - sz) * (e.Z - sz)).First();
        r.B.Player.X = near.X + 6; r.B.Player.Z = near.Z;
        Step(r, 0.5);
        Assert.True(r.B.Enemies.Living().Count(x => x.Roused) >= 3);"""),
        ("""        double start = r.B.Time;
        // An absurd build: the map's floors (10, 13 and 10 s, and the turns) still hold it.
        Step(r, 120, () =>
        {
            r.B.Player.Hp = r.B.MaxHp;
            if (boss.Alive && boss.Boss && boss.State != EnemyState.Dying) r.B.HitEnemy(boss, boss.MaxHp * 0.2, School.Storm, [Tag.Storm], new HitOpts { NoCrit = true });
        });
        Assert.True(r.Zone.Cleared);
        double took = r.B.Time - start;""",
         """        double start = r.B.Time, took = -1;
        // An absurd build: the map's floors (10, 13 and 10 s, and the turns) still hold it.
        Step(r, 120, () =>
        {
            r.B.Player.Hp = r.B.MaxHp;
            if (boss.Alive && boss.Boss && boss.State != EnemyState.Dying) r.B.HitEnemy(boss, boss.MaxHp * 0.2, School.Storm, [Tag.Storm], new HitOpts { NoCrit = true });
            if (r.Zone.Cleared && took < 0) took = r.B.Time - start;
        });
        Assert.True(r.Zone.Cleared);"""),
    ],
}
