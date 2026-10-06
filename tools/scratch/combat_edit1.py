p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09c5a65f5a84319e\godot\tests\BossTests.cs'
s = open(p, encoding='utf-8').read()
old = '''    /// <summary>An arena of `people` brought to the edge of the half hour, the survivor kept alive.</summary>
    static Fight At30(string people, int seed = 3, int tier = 1)
    {'''
new = '''    /// <summary>An arena of `people` brought to the edge of the half hour, the survivor kept alive.
    /// `game`: the battle's hooks wired as the game wires them (BattleHooks.Following), not shared.</summary>
    static Fight At30(string people, int seed = 3, int tier = 1, bool game = false)
    {'''
assert old in s; s = s.replace(old, new)
old = '''        b.Hooks = zone.Hooks;
        host.Battle = b;
        zone.Begin(b);
        b.GreatOwed = 0;
        b.Time = 30 * 60 - 0.05;'''
new = '''        b.Hooks = game ? BattleHooks.Following(zone.Hooks) : zone.Hooks;
        host.Battle = b;
        zone.Begin(b);
        b.GreatOwed = 0;
        b.Time = 30 * 60 - 0.05;'''
assert old in s; s = s.replace(old, new)
old = '''    [Fact]
    public void A_herald_is_not_a_boss_and_has_no_boss_music()'''
new = '''    /// <summary>The game copied the zone's hooks when the battle began, before the boss
    /// came, so no boss script ran on screen while every test passed.</summary>
    [Theory]
    [InlineData("pack")]
    [InlineData("kerchiefs")]
    public void The_boss_fights_its_own_fight_in_the_game_too(string people)
    {
        var f = At30(people, game: true);
        var boss = Boss(f);
        var s = f.Zone.BossScript!;
        Step(f, 12, _ =>
        {
            if (boss.Alive && boss.TakenMul > 0) f.B.HitEnemy(boss, boss.MaxHp * 0.002, School.Fire, [Tag.Fire], new HitOpts { NoCrit = true });
        });
        Assert.True(s.FightT > 10);
        Assert.True(boss.HpFloor > 0);
        // A stagger reaches the script through the game's hooks.
        for (int i = 0; i < 12 && boss.StaggeredT <= 0; i++) f.B.ApplyStatus(boss, new StatusPayload(StatusKind.Stun, 1, 1, 2), 10);
        Assert.True(boss.StaggeredT > 0);
    }

    [Fact]
    public void Every_hook_the_game_wraps_asks_the_zone_when_called()
    {
        var zone = new BattleHooks();
        var h = BattleHooks.Following(zone);
        foreach (var field in typeof(BattleHooks).GetFields()) Assert.NotNull(field.GetValue(h));
        bool ticked = false, hit = false, staggered = false;
        zone.BossTick = (_, _) => ticked = true;
        zone.OnBossHit = (_, _, _) => hit = true;
        zone.OnBossStagger = _ => staggered = true;
        var b = BattleTests.Arena(31);
        var e = b.SpawnEnemy("wolf", b.Player.X + 5, b.Player.Z, new Battle.SpawnOpts())!;
        Assert.True(h.BossTick!(e, 0.1));
        h.OnBossHit!(e, School.Fire, 1);
        h.OnBossStagger!(e);
        Assert.True(ticked && hit && staggered);
    }

    [Fact]
    public void A_herald_is_not_a_boss_and_has_no_boss_music()'''
assert old in s; s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)
print("ok")
