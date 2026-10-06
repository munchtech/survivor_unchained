W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09c5a65f5a84319e\godot'

def edit(path, pairs):
    p = W + '\\' + path
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert s.count(a) == 1, (path, s.count(a), a[:80])
        s = s.replace(a, b, 1)
    open(p, 'w', encoding='utf-8').write(s)

edit(r'tests\BossTests.cs', [
('''    static Fight At30(string people, int seed = 3, int tier = 1, bool game = false, string? boss = null, string? bossName = null)
    {''',
'''    static Fight At30(string people, int seed = 3, int tier = 1, bool game = false, string? boss = null, string? bossName = null, bool spare = false)
    {'''),
('''People = people, Boss = boss, BossName = bossName };''',
'''People = people, Boss = boss, BossName = bossName, Spare = spare };'''),
('''    [Fact]
    public void The_barrow_lord_rises_unless_he_is_laid_down()''',
'''    /// <summary>Greymuzzle let go (the story bible, narrowly): brought down, he does not die;
    /// he gets up and goes, and the fight is won without a kill.</summary>
    [Fact]
    public void Greymuzzle_spared_goes_down_gets_up_and_goes()
    {
        var f = At30("pack", boss: "boss_pack", bossName: "Greymuzzle", spare: true);
        var boss = Boss(f);
        bool killed = false;
        Step(f, 260, _ =>
        {
            if (boss.Alive && boss.Boss && boss.TakenMul > 0) f.B.HitEnemy(boss, boss.MaxHp * 0.05, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true });
            foreach (var ev in f.B.Events.Drain()) killed |= ev is Ev.Kill { Boss: true };
        });
        Assert.True(f.Zone.Won);
        Assert.False(killed);
        Assert.Contains(f.B.Pickups.Items, p => p.Alive && p.Kind == PickupKind.Chest && p.Ref == "boss");
        // Not spared, the same fight ends in a kill.
        var g = At30("pack", boss: "boss_pack", bossName: "Greymuzzle");
        var b2 = Boss(g);
        killed = false;
        Step(g, 260, _ =>
        {
            if (b2.Alive && b2.Boss && b2.TakenMul > 0) g.B.HitEnemy(b2, b2.MaxHp * 0.05, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true });
            foreach (var ev in g.B.Events.Drain()) killed |= ev is Ev.Kill { Boss: true };
        });
        Assert.True(g.Zone.Won);
        Assert.True(killed);
    }

    [Fact]
    public void The_barrow_lord_rises_unless_he_is_laid_down()'''),
])
print("ok")
