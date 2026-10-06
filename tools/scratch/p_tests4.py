import os
ROOT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ac4ec5bbd2763a0df\godot\tests"
FILES = {
os.path.join(ROOT, "ArenaTests.cs"): [
("""    [Fact]
    public void Fallen_after_the_win_it_is_still_won()""",
"""    /* -------------------------------------------- the night's stretches -- */

    /// <summary>The owner: mechanics "don't appear till certain mini bosses and minion types show
    /// up". The Pack's tuskers do not run in the horde until Old Tusk has come, named, his lesson
    /// said; then they do.</summary>
    [Fact]
    public void The_tuskers_come_only_after_Old_Tusk_has_shown_them()
    {
        var s = Make(Spec("pack"));
        s.B.Player.Iframes = 1e9;
        s.B.Time = 2.6 * 60;
        bool boarBefore = false;
        for (double t = 0; t < 90 && !s.Host.Announced.Any(a => a.Title == "Old Tusk"); t += 1)
        {
            Run(s, 1);
            boarBefore |= s.B.Enemies.Living().Any(e => e.Def.Id == "boar");
        }
        Assert.False(boarBefore);
        var came = s.Host.Announced.Single(a => a.Title == "Old Tusk");
        Assert.Equal(Enemies.Get("mb_old_tusk").Lesson, came.Subtitle);
        Assert.Contains(s.B.Enemies.Living(), e => e.Def.Id == "mb_old_tusk" && e.Elite);
        // Its bar, as a herald's, and then its kind in the crowd.
        Run(s, 1);
        Assert.Equal("Old Tusk", s.Host.Boss?.Title);
        Run(s, 40);
        Assert.Contains(s.B.Enemies.Living(), e => e.Def.Id == "boar" && !e.Elite);
    }

    /// <summary>Champions from the second tier wear their people's Signs: named for them,
    /// coloured, with the verb.</summary>
    [Fact]
    public void A_champions_turn_brings_a_signed_champion_from_the_second_tier()
    {
        var spec = Spec("dead");
        spec.Tier = 2;
        var s = Make(spec);
        s.B.Player.Iframes = 1e9;
        s.B.Time = 8 * 60;
        for (int i = 0; i < 16 && !s.B.Enemies.Living().Any(e => e.Elite && e.Def.Signs.Length > 0); i++) Run(s, 30);
        var champ = s.B.Enemies.Living().First(e => e.Elite && e.Def.Signs.Length > 0);
        Assert.Contains(Signs.Get(champ.Def.Signs[0]).Name, champ.Def.Name);
        Assert.NotNull(champ.Def.Tint);
    }

    /// <summary>Crafting's measure: the Kerchiefs' horde paid tens of thousands of gold a night and
    /// the crowd's champions hundreds of pieces of gear. Now the rank and file drop a fiftieth of
    /// their gold, and gear comes only from what carries a chest.</summary>
    [Fact]
    public void An_arenas_horde_pays_a_little_gold_and_its_crowd_champions_no_gear()
    {
        var s = Make(Spec("kerchiefs"));
        var b = s.B;
        int gold = 0, items = 0;
        for (int i = 0; i < 400; i++)
        {
            var e = b.SpawnEnemy("footpad", b.Player.X + 30, b.Player.Z, new Battle.SpawnOpts { Elite = i % 20 == 0 })!;
            b.KillEnemy(e, true, null);
        }
        foreach (var k in b.Pickups.Living()) { if (k.Kind == PickupKind.Gold) gold++; if (k.Kind == PickupKind.Item) items++; }
        // 380 footpads at the day's rate would drop about 250 purses; 20 champions keep theirs.
        Assert.InRange(gold, 1, 40);
        Assert.Equal(0, items);
    }

    /// <summary>The story's nights are twenty minutes: the same night told quicker. Its boss comes at
    /// the twentieth minute, the ember comes half again as fast, and when the boss falls the night
    /// is over: no long night after it, its people drawing back.</summary>
    [Fact]
    public void A_story_night_is_twenty_minutes_and_ends_on_its_boss()
    {
        var spec = Spec(story: true);
        spec.Minutes = 20;
        var s = Make(spec);
        s.B.Player.Iframes = 1e9;
        s.B.AddWeapon("seeking_motes", 2);
        s.B.AddBoon("might");
        Assert.Equal(1.5, s.B.Rules.EmberGain, 6);
        s.B.Time = 19.99 * 60;
        Run(s, 1);
        Assert.NotNull(s.Host.Boss);
        Assert.Contains(s.Host.Announced, a => a.Kicker == "The night's end");
        Defeat(s);
        Assert.True(s.Zone.Won);
        Assert.Equal(1.0, s.B.Rules.EmberGain, 6);
        Run(s, 6 * 60 + 30);
        Assert.DoesNotContain(s.Host.Announced, a => a.Kicker == "The long night");
        Assert.True(Hostile(s.B) < 20, $"{Hostile(s.B)} still in the field");
    }

    [Fact]
    public void Fallen_after_the_win_it_is_still_won()"""),
],
}
