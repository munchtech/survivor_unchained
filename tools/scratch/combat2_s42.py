W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "tests/ArenaTests.cs": [
        ("""        // The fifteenth minute: a second, which may be the first deepened.
        s.B.Player.Iframes = 1e9;
        s.B.Time = 15 * 60;
        Run(s, 0.1);
        Assert.Equal(1, s.B.GreatOwed);""",
         """        // The fifteenth minute: a second, which may be the first deepened (the Kindling's minute
        // passed with its core left standing).
        s.B.Player.Iframes = 1e9;
        s.B.Time = 14.5 * 60;
        Run(s, 61);
        Assert.Equal(1, s.B.GreatOwed);"""),
        ("""    /// <summary>The boss's fall is the night's peak:""",
         """    /// <summary>The Kindling (docs/bosses/SURVIVORS_BOSSES.md 9): in the breath before the fifteenth
    /// minute an ember-core comes up, and beside it the ruler's own creature with a verb of its
    /// ruler's. Broken within the minute, the great blessing comes a card richer; the keeper carries
    /// a chest; the blessing is owed either way.</summary>
    [Theory]
    [InlineData("pack", "lt_pack")]
    [InlineData("dead", "lt_dead")]
    [InlineData("lamplings", "lt_lamplings")]
    [InlineData("kerchiefs", "lt_kerchiefs")]
    public void The_kindling_puts_a_core_and_the_rulers_keeper_before_the_great_blessing(string people, string keeperDef)
    {
        var s = Make(Spec(people));
        s.B.GreatOwed = 0;
        s.B.Player.Iframes = 1e9;
        s.B.Time = 14.5 * 60;
        Run(s, 0.2);
        var core = s.B.Enemies.Living().Single(e => e.Def.Id == "ember_core");
        var keeper = s.B.Enemies.Living().Single(e => e.Def.Id == keeperDef);
        Assert.Equal(keeper.MaxHp, core.MaxHp, 3);
        Assert.Equal(0, s.B.GreatOwed);
        Assert.Contains(keeperDef, s.Zone.Creatures);
        // Broken in time: the blessing is owed, and a card richer.
        s.B.HitEnemy(core, core.MaxHp * 2, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true });
        Run(s, 0.2);
        Assert.Equal(1, s.B.GreatOwed);
        Assert.True(s.Zone.CoreBroken);
        int cards = LevelUp.Count(s.B);
        Assert.Equal(4, cards);
        // Left standing, it cools after its minute, and the blessing is the night's as it was.
        var t = Make(Spec(people));
        t.B.GreatOwed = 0;
        t.B.Player.Iframes = 1e9;
        t.B.Time = 14.5 * 60;
        Run(t, 61);
        Assert.Equal(1, t.B.GreatOwed);
        Assert.False(t.Zone.CoreBroken);
        Assert.DoesNotContain(t.B.Enemies.Living(), e => e.Def.Id == "ember_core");
        Assert.Equal(3, LevelUp.Count(t.B));
    }

    /// <summary>The boss's fall is the night's peak:"""),
    ],
}
