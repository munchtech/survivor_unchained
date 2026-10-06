W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09c5a65f5a84319e\godot'

def edit(path, pairs):
    p = W + '\\' + path
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert s.count(a) == 1, (path, s.count(a), a[:80])
        s = s.replace(a, b, 1)
    open(p, 'w', encoding='utf-8').write(s)

edit(r'tests\ArenaTests.cs', [
('''    static int Hostile(Battle b) => b.Enemies.Living().Count(e => e.Disposition == Disposition.Hostile && e.State != EnemyState.Dying);
''',
'''    static int Hostile(Battle b) => b.Enemies.Living().Count(e => e.Disposition == Disposition.Hostile && e.State != EnemyState.Dying);

    /* ------------------------------------------------- the long night -- */

    /// <summary>The owner: "endless is truly endless - just keep ramping up till its
    /// impossible". No ceiling and no cliff: every minute harder than the last, smooth for
    /// the first three quarters of an hour, compounding after, so nothing holds for ever;
    /// their pace rises only to what can still be read.</summary>
    [Fact]
    public void The_long_night_climbs_without_a_ceiling_or_a_cliff()
    {
        var last = ArenaRun.Hardening(0);
        Assert.Equal((1.0, 1.0, 1.0), last);
        for (double m = 0.5; m <= 300; m += 0.5)
        {
            var h = ArenaRun.Hardening(m);
            Assert.True(h.Health > last.Health && h.Damage > last.Damage, $"flat at {m}");
            // No cliff: no minute more than a tenth harder than the one before.
            Assert.True(h.Damage / last.Damage < 1.1 && h.Health / last.Health < 1.1, $"a cliff at {m}");
            Assert.True(h.Pace <= 1.3);
            last = h;
        }
        // Two hours past the half hour, blows land many times as hard as at the half hour:
        // past what any armour, dodge or mending answers.
        Assert.True(ArenaRun.Hardening(120).Damage > 20);
    }

    /// <summary>Every five minutes past the win the dark swears one more of the table's
    /// oaths (its rule from then on, announced, listed), never one already sworn and never
    /// the moonless (the night must stay readable); out of them, it deepens.</summary>
    [Fact]
    public void The_dark_swears_an_oath_every_five_minutes_and_never_the_moonless()
    {
        var s = Make(Spec("pack", false, "iron"));
        s.B.Player.Iframes = 1e9;
        s.B.Time = 1800;
        Run(s, 1);
        Defeat(s);
        Assert.True(s.Zone.Won);
        double light = s.B.Rules.Light;
        for (int k = 1; k <= 11; k++)
        {
            s.B.Time += 300;
            Run(s, 0.2);
            Assert.Equal(k, s.Zone.DarkSworn);
        }
        var sworn = s.Host.Announced.Where(a => a.Kicker == "The long night").Select(a => a.Title).ToList();
        Assert.Contains("The dark swears the Oath of the Hunt", sworn);
        Assert.DoesNotContain(sworn, t => t.Contains("Iron") || t.Contains("Moonless"));
        Assert.Contains("The dark deepens", sworn);
        // Their rules hold from then on, and what they pay is paid.
        Assert.Equal(1.2, s.B.Rules.FoeSpeed, 3);
        Assert.True(s.B.Rules.DeathFire && s.B.Rules.HitChill && s.B.Rules.HitPoison);
        Assert.Equal(light, s.B.Rules.Light);
        Assert.True(s.B.Rules.EmberGain > 2);
    }

    /// <summary>What rules the people comes again every quarter hour past the win, its sign a
    /// minute before: its own fight, a part stronger each time, its chest a card richer; the
    /// arena stays won and goes on.</summary>
    [Fact]
    public void What_rules_them_comes_again_each_quarter_hour_stronger()
    {
        var s = Make(Spec());
        s.B.Player.Iframes = 1e9;
        s.B.Time = 1800;
        Run(s, 1);
        double first = Boss(s).MaxHp;
        Defeat(s);
        Assert.True(s.Zone.Won);
        s.B.Time += 900 - 70;
        Run(s, 12);
        Assert.Contains(s.Host.Announced, a => a.Title.EndsWith("stirs again"));
        Run(s, 60);
        Assert.Equal(1, s.Zone.Returns);
        var again = Boss(s);
        Assert.True(again.Boss);
        Assert.Equal(first * (1 + ArenaRun.ReturnGrowth), again.MaxHp, 0);
        Assert.Contains(s.Host.Announced, a => a.Kicker == "Again");
        int chests = s.B.Pickups.Items.Count(p => p.Alive && p.Kind == PickupKind.Chest && p.Ref == "boss");
        for (int i = 0; i < 400 && again.Alive && again.State != EnemyState.Dying; i++)
        {
            s.B.HitEnemy(again, again.MaxHp * 0.25, School.Physical, [Tag.Physical]);
            Run(s, 0.5);
        }
        Assert.Contains(s.Host.Announced, a => a.Title.EndsWith("is beaten again"));
        Assert.Null(s.Host.ArenaResult);
        Assert.True(s.B.Pickups.Items.Count(p => p.Alive && p.Kind == PickupKind.Chest && p.Ref == "boss") > chests);
    }

    /// <summary>An oath's pay in ember ("half again the ember") was never paid: the dead left
    /// the same stones under any oath.</summary>
    [Fact]
    public void An_oath_that_pays_in_ember_pays()
    {
        double Dropped(params string[] oaths)
        {
            var s = Make(Spec("pack", false, oaths));
            var wolf = s.B.SpawnEnemy("wolf", s.B.Player.X + 6, s.B.Player.Z, new Battle.SpawnOpts { Level = 1 })!;
            s.B.KillEnemy(wolf, true, null);
            return s.B.Pickups.Items.Where(p => p.Alive && p.Kind == PickupKind.Ember).Sum(p => p.Value);
        }
        Assert.Equal(Dropped() * 1.5, Dropped("swarm"), 3);
    }
'''),
])
print("ok")
