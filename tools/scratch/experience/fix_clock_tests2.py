"""Clock tests: the waking on Chid's bench, rises counted, straight on (run from godot/)."""
p = "tests/DayClockTests.cs"
s = open(p, encoding="utf-8").read()
start = s.index("    [Fact]\n    public void A_night_seen_out_is_not_a_rest")
end = s.index("    [Fact]\n    public void The_inn_and_waiting_for_nightfall")
new = '''    [Fact]
    public void A_night_seen_out_is_not_a_rest_and_a_story_night_lost_wakes_her_on_chids_bench()
    {
        var j = Arrived();
        j.Expedition = new Expedition { Hp = 12 };
        j.Nightfall();
        j.SeeNightOut(() => 0.5);
        Assert.Equal(12, j.Expedition!.Hp);
        // Lost: a day on, no wound, and Chid tells the waking for that fight (not the clock).
        j.World.Facts["dig.hostile"] = true;
        var spec = StoryFights.Spec("dig", j.Ctx, "verge", 0, 0, 0);
        var lines = j.WakeAfterLoss(spec, null, () => 0.5);
        Assert.Null(j.Expedition);
        Assert.Equal(3, j.World.Day);
        Assert.Equal(TimeOfDay.Dawn, j.World.Time);
        Assert.Equal("dig_boils", j.World.Fact("player.carried_home").Str);
        Assert.True(j.World.Fact("player.just_died").Truthy);
        Assert.DoesNotContain(lines, l => l.Contains("Chid"));
        Assert.Equal("carried", new DialogueRunner(Dialogue.Find("chid")!, j.Ctx).Start()!.Node.Id);
    }

    [Fact]
    public void Her_first_rise_is_the_prologues_words_and_every_later_one_takes_less()
    {
        var j = Arrived();
        Assert.Equal(Journey.DayLines.Rise, j.RiseLine());
        Assert.Equal(Journey.DayLines.RiseAgain, j.RiseLine());
        Assert.Equal(Journey.DayLines.RiseAgain, j.RiseLine());
    }

    [Fact]
    public void Back_from_one_fight_she_has_fought_tonight_and_a_new_night_forgets_it()
    {
        var j = Arrived();
        j.Nightfall();
        Assert.False(j.FoughtTonight);
        j.BackFromFight();
        Assert.True(j.FoughtTonight);
        j.SeeNightOut(() => 0.5);
        j.Nightfall();
        Assert.False(j.FoughtTonight);
    }

'''
s = s[:start] + new + s[end:]
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")
