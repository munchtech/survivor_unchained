W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "logic/Play/Zones/ArenaRun.cs": [
        ("""        if (!great15 && Minute >= 15 && !bossUp)
        {
            great15 = true;
            B.GreatOwed++;
            // And a banish with it: by now the build knows what it does not want.
            B.Banishes++;
            G.Announce(new Announcement(Middle, "A great blessing", "reward", 2.6));
        }
        Minibosses();""",
         """        // The Kindling: at the fourteen and a half minute's breath, the ember-core and its keeper.
        if (!kindled && !great15 && Minute >= 14.5 && !bossUp && !won) Kindle();
        if (kindled && !great15) Kindling();
        // (No core where one could not stand: the great blessing comes all the same.)
        if (!great15 && !kindled && Minute >= 15 && !bossUp) Midnight(false);
        Minibosses();"""),
        ("""    /// <summary>The minute's turn: a ring, a champion, a stampede, a swarm.</summary>
    void Event(int kind)""",
         """    /* ---------------------------------------------------- the Kindling -- */

    /* The fifteenth minute's great blessing was an announcement; it is a moment now, and the
     * boss's first verse (docs/bosses/SURVIVORS_BOSSES.md 9). In the breath before it an
     * ember-core comes up out of the scar the arena was opened from, and beside it what rules
     * the people's own creature, wearing one of its ruler's verbs: the night teaches its boss's
     * language before the boss. Broken within the minute, the core makes the great blessing a
     * card richer; the keeper carries a full chest. The blessing is owed whatever happens. */

    Enemy? core, keeper;
    double coreSeed, kindledAt;
    bool kindled;
    IOrb? coreOrb;
    int coreLight = -1;
    /// <summary>Broken in time (null: not yet, or never came).</summary>
    public bool? CoreBroken { get; private set; }

    /// <summary>A fifth of what its ruler will have at the half hour, at this minute's level: the
    /// keeper's health, and the core's.</summary>
    double KeeperHealth() =>
        Enemies.Get(BossDef).Health * Enemies.ScaleFor(Level()).Health * (ArenaBosses.For(BossDef, this)?.HealthMul(Spec.Tier) ?? 12 + 2 * Spec.Tier) / 5;

    static string KeeperOf(string people) => people switch { "dead" => "lt_dead", "lamplings" => "lt_lamplings", "kerchiefs" => "lt_kerchiefs", _ => "lt_pack" };

    void Kindle()
    {
        kindled = true;
        kindledAt = Seconds;
        var p = B!.Player;
        // Toward the middle of the arena from where she stands, a little way off.
        if (Around(Math.Atan2(-p.Z, -p.X), 11) is not var (x, z)) { kindled = false; Midnight(false); return; }
        core = B.SpawnEnemy("ember_core", x, z, new Battle.SpawnOpts { Level = Level(), Style = SpawnStyle.Rise, Faction = Enemies.Get(people.Champion).Faction });
        if (core == null) { kindled = false; Midnight(false); return; }
        double hp = KeeperHealth();
        core.MaxHp = core.Hp = hp;
        core.AttackT = 1e9;
        core.Named = new Named { Title = "The ember-core" };
        coreSeed = core.Seed;
        if (Around(Math.Atan2(z - p.Z, x - p.X) + 0.5, 14) is var (kx, kz) && Spawn(KeeperOf(people.Id), kx, kz, true) is { } k)
        {
            k.MaxHp = k.Hp = hp;
            k.Named = new Named { Title = k.Def.Name };
            chests.Add(k.Id);
            keeper = k;
        }
        coreOrb = G.Look.Orb("#ff7a2a", 1.5);
        coreLight = G.Look.AddLight(x, 1.6, z, "#ff8a3a", 3.4, 12, 0.3, 0.14, "#ffb060");
        B.Charges.Calm(B, 8);
        B.Events.Emit(new Ev.Focus { X = x, Z = z, Duration = 1.4 });
        B.Events.Emit(new Ev.Shake { Amount = 0.3 });
        G.Announce(new Announcement("The ember-core", "Break it within the minute, and the great blessing comes richer", "reward", 3.2, keeper?.Def.Name));
    }

    bool CoreUp => core is { Alive: true } c && c.Seed == coreSeed && c.State != EnemyState.Dying;

    void Kindling()
    {
        if (!CoreUp) { CoreBroken = true; B!.GreatExtra = 1; Midnight(true); return; }
        if (Seconds - kindledAt >= 60)
        {
            // It cools, and goes back into the ground: the blessing is the night's as it was.
            B!.Events.Emit(new Ev.Explosion { X = core!.X, Z = core.Z, Radius = 2.5, School = School.Fire, Power = 0.6 });
            B.Enemies.Release(core);
            CoreBroken = false;
            Midnight(false);
        }
    }

    /// <summary>The night's great blessing, and a banish with it (by now the build knows what it does not want).</summary>
    void Midnight(bool rich)
    {
        great15 = true;
        B!.GreatOwed++;
        B.Banishes++;
        coreOrb?.Dispose();
        coreOrb = null;
        if (coreLight >= 0) G.Look.SetLit(coreLight, false);
        if (rich && core != null) B.Events.Emit(new Ev.Explosion { X = core.X, Z = core.Z, Radius = 4, School = School.Fire, Power = 1.4 });
        G.Announce(new Announcement(Middle, rich ? "The core broken: a great blessing, and a choice more" : "A great blessing", "reward", 2.6));
    }

    /// <summary>The minute's turn: a ring, a champion, a stampede, a swarm.</summary>
    void Event(int kind)"""),
        ("""        herald10 = Minute >= 10; herald20 = Minute >= 20; great15 = Minute >= 15;""",
         """        herald10 = Minute >= 10; herald20 = Minute >= 20; great15 = Minute >= 15; kindled = Minute >= 14.5;"""),
        ("""        else if (herald is { Alive: true } h && h.State != EnemyState.Dying)""",
         """        else if (CoreUp && core is { } cc)
            G.SetBoss(new BossBar("The ember-core", $"Break it: {Math.Max(0, 60 - (Seconds - kindledAt)):0} s", cc.Hp, cc.MaxHp, IsBoss: false));
        else if (herald is { Alive: true } h && h.State != EnemyState.Dying)"""),
        ("""        else if (MinibossUp && miniboss is { } mb)""",
         """        else if (keeper is { Alive: true } kp && kp.State != EnemyState.Dying && kp.Named != null)
            G.SetBoss(new BossBar(kp.Def.Name, kp.Def.Lesson, kp.Hp, kp.MaxHp, IsBoss: false));
        else if (MinibossUp && miniboss is { } mb)"""),
        ("""        if (boss is { Alive: true } b && b.State != EnemyState.Dying)
            G.SetBoss(""", """        // The core: a lump of raw ember, pulsing, brighter as it is broken.
        if (coreOrb != null && core != null)
        {
            double t = Seconds, hurt = 1 - core.Hp / Math.Max(1, core.MaxHp);
            coreOrb.Visible = true;
            coreOrb.Place(core.X, 0.7 + 0.08 * Math.Sin(t * 2.4), core.Z, t * 0.4, 1 + 0.06 * Math.Sin(t * 5.1) + 0.25 * hurt);
            coreOrb.Light = 1.2 + 0.4 * Math.Sin(t * 5.1) + 1.4 * hurt;
        }
        if (boss is { Alive: true } b && b.State != EnemyState.Dying)
            G.SetBoss("""),
        ("""    public override IReadOnlyList<string> Creatures => people.Arena.Select(h => h.Def).Concat(people.Stretches.Select(s => s.Miniboss))
        .Append(people.Champion).Append(BossDef).Distinct().ToList();""",
         """    public override IReadOnlyList<string> Creatures => people.Arena.Select(h => h.Def).Concat(people.Stretches.Select(s => s.Miniboss))
        .Append(people.Champion).Append(BossDef).Append(KeeperOf(people.Id)).Distinct().ToList();"""),
    ],
}
