W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09c5a65f5a84319e\godot'

def edit(path, pairs):
    p = W + '\\' + path
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert a in s, (path, a[:70])
        s = s.replace(a, b, 1)
    open(p, 'w', encoding='utf-8').write(s)

edit(r'tests\BossTests.cs', [
('''    static Fight At30(string people, int seed = 3, int tier = 1, bool game = false)
    {''',
'''    static Fight At30(string people, int seed = 3, int tier = 1, bool game = false, string? boss = null, string? bossName = null)
    {'''),
('''        var spec = new ArenaSpec { Id = "table:test", Name = "Test", Seed = seed, Tier = tier, People = people };''',
'''        var spec = new ArenaSpec { Id = "table:test", Name = "Test", Seed = seed, Tier = tier, People = people, Boss = boss, BossName = bossName };'''),
('''    public void Grimtunnel_goes_back_down_the_hole_and_never_dies()
    {
        var f = At30("lamplings");''',
'''    public void Grimtunnel_goes_back_down_the_hole_and_never_dies()
    {
        // His own night (the Dig Boils Over): the table's Lamplings field the Ganger.
        var f = At30("lamplings", boss: "grimtunnel_roused", bossName: "Grimtunnel");'''),
('''    [Fact]
    public void The_barrow_lord_rises_unless_he_is_laid_down()''',
'''    /// <summary>The story keeps Grimtunnel and his name for his own night and Act 3
    /// (docs/STORY_BIBLE.md): a table arena fields a foreman of the Dig, who can die.</summary>
    [Fact]
    public void The_tables_lamplings_field_the_ganger_never_grimtunnel()
    {
        var f = At30("lamplings");
        var boss = Boss(f);
        Assert.Equal("boss_lamplings", boss.Def.Id);
        Assert.DoesNotContain("Grimtunnel", boss.Named?.Title ?? "");
        Assert.True(((Grimtunnel)f.Zone.BossScript!).Ganger);
        bool killed = false;
        Step(f, 260, _ =>
        {
            if (boss.Alive && boss.Boss) f.B.HitEnemy(boss, boss.MaxHp * 0.05, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true });
            foreach (var ev in f.B.Events.Drain()) killed |= ev is Ev.Kill { Boss: true };
        });
        Assert.True(f.Zone.Won);
        Assert.True(killed);
    }

    [Fact]
    public void The_barrow_lord_rises_unless_he_is_laid_down()'''),
])
print("ok")
