W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "tests/BossTests.cs": [
        ("""    static Fight At30(string people, int seed = 3, int tier = 1, bool game = false, string? boss = null, string? bossName = null, bool spare = false)
    {""", """    static Fight At30(string people, int seed = 3, int tier = 1, bool game = false, string? boss = null, string? bossName = null, bool spare = false, string[]? oaths = null)
    {"""),
        ("""        var spec = new ArenaSpec { Id = "table:test", Name = "Test", Seed = seed, Tier = tier, People = people, Boss = boss, BossName = bossName, Spare = spare };""",
         """        var spec = new ArenaSpec { Id = "table:test", Name = "Test", Seed = seed, Tier = tier, People = people, Boss = boss, BossName = bossName, Spare = spare, Oaths = (oaths ?? []).ToList() };"""),
        ("""    [Fact]
    public void A_cone_is_a_cone()""", """    /// <summary>The oaths on a boss (docs/bosses/SURVIVORS_BOSSES.md 0.12): one visible change each,
    /// said on its card. The winter's chill rides its heavy blows, the embers' fire is left where
    /// they land, the iron slows its stagger, the vigil shortens its floors.</summary>
    [Fact]
    public void The_oaths_sworn_change_the_boss_and_its_card_says_so()
    {
        var f = At30("dead", oaths: ["winter", "embers", "iron", "vigil"]);
        var s = f.Zone.BossScript!;
        Assert.Contains("chill", s.Sworn());
        Assert.Contains("fire", s.Sworn());
        Assert.Equal(2 / 3.0, s.FloorScale, 3);
        Assert.Equal(2 / 3.0, f.B.Rules.StaggerTaken, 3);
        // Its marked blows: the heavy ones chill, and each leaves fire where it lands.
        bool chilled = false, fire = false;
        Step(f, 40, () =>
        {
            foreach (var bl in f.B.Blows) chilled |= bl.Slow > 0 && bl.Damage >= Boss(f).Damage * 1.5;
            fire |= f.B.Zones.Living().Any(z => z.Owner == Side.Enemy && z.School == School.Fire);
        });
        Assert.True(chilled);
        Assert.True(fire);
        // Unsworn, none of it.
        var g = At30("dead");
        Assert.Equal("", g.Zone.BossScript!.Sworn());
        Assert.Equal(1, g.Zone.BossScript.FloorScale);
    }

    [Fact]
    public void A_cone_is_a_cone()"""),
    ],
}
