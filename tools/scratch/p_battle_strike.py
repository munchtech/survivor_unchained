PAIRS = [
("""    public void ScheduleStrike(double x, double z, double r, double dmg, School school, Tag[] tags, double delay, WeaponInst? weapon, Side owner = Side.Player, int depth = 0)""",
"""    /// <summary>A creature's blow on the ground after `delay` (its own mark already shown):
    /// the survivor if she is still in it, and the horde round it at a little over half.</summary>
    public void EnemyStrike(double x, double z, double r, double dmg, School school, double delay) =>
        strikes.Add(new StrikeSpec(x, z, r, dmg, school, BlastTag, delay, null, Side.Enemy, 0));

    public void ScheduleStrike(double x, double z, double r, double dmg, School school, Tag[] tags, double delay, WeaponInst? weapon, Side owner = Side.Player, int depth = 0)"""),
("""    /// <summary>A boss's stagger bar filled.</summary>
    public Action<Enemy>? OnBossStagger;
""",
"""    /// <summary>A boss's stagger bar filled.</summary>
    public Action<Enemy>? OnBossStagger;
    /// <summary>A creature called up by one of its own (a summon), and who called it: the
    /// zone softens or hardens it as it does the rest of its horde.</summary>
    public Action<Enemy, Enemy>? OnCalled;
"""),
("""        OnBossStagger = e => zone.OnBossStagger?.Invoke(e),
    };""",
"""        OnBossStagger = e => zone.OnBossStagger?.Invoke(e),
        OnCalled = (e, by) => zone.OnCalled?.Invoke(e, by),
    };"""),
]
