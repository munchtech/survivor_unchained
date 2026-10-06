"""A lost story fight waits at its place, not at the table (run from godot/)."""
import re
p = "logic/Arena/Arena.cs"
s = open(p, encoding="utf-8").read()
old = """            w.Rematches.RemoveAll(r => r.Id == spec.Id);
            if (spec.Story) w.Rematches.Add(spec);"""
assert old in s
s = s.replace(old, """            // A story fight lost waits for another night at its own place, where the night calls it
            // by name (the owner's decision); the table no longer keeps a second copy of it.
            w.Rematches.RemoveAll(r => r.Id == spec.Id);""", 1)
open(p, "w", encoding="utf-8", newline="").write(s)

p = "tests/ArenaTests.cs"
s = open(p, encoding="utf-8").read()
old_start = s.index("    public void Falling_keeps_what_was_earned_and_a_story_fight_waits_to_be_taken_again()")
old_end = s.index("    [Fact]\n    public void Kills_in_an_arena_teach_nothing_until_it_is_over()")
new = '''    public void Falling_keeps_what_was_earned_and_a_story_fight_waits_at_its_place_not_the_table()
    {
        var s = Make(Spec(story: true));
        s.B.Time = 540;
        s.B.GoldGained = 40;
        double gold = s.J.Ch.Gold;
        // There is no way out before the win.
        s.Zone.Leave();
        Assert.False(s.Zone.Over);
        Assert.True(s.Zone.OnDeath("a wolf"));
        Run(s, 3);
        var r = s.Host.ArenaResult!;
        Assert.False(r.Won);
        Assert.InRange(r.Xp, 200, 400);
        Assert.Equal(gold + 40, s.J.Ch.Gold);
        Assert.True(s.J.World.Fact("test.lost").Truthy);
        // Lost, it waits for another night where it stands (the night calls it), not at the table.
        Assert.Empty(s.J.World.Rematches);
        Assert.True(r.WakesInTown);
        // A rematch an older save kept is still the same fight: won, it is gone from the table.
        s.J.World.Rematches.Add(r.Spec);
        var again = Arenas.Again(s.J.World.Rematches[0], "waystation", 1, 2, 0);
        Assert.Null(again.OnLose);
        Assert.NotNull(again.OnWin);
        Assert.Null(again.EndLost);
        var next = Make(again, s.J);
        next.B.Player.Iframes = 1e9;
        next.B.Time = 1800;
        Run(next, 1);
        Defeat(next);
        Run(next, 1);
        Assert.Empty(s.J.World.Rematches);
        Assert.True(s.J.World.Fact("test.won").Truthy);
    }

'''
s = s[:old_start] + new + s[old_end:]
open(p, "w", encoding="utf-8", newline="").write(s)

p = "tests/DayClockTests.cs"
s = open(p, encoding="utf-8").read()
old = """        Assert.Contains(j.World.Rematches, r => r.Id == "dig_boils");"""
assert old in s
s = s.replace(old, """        Assert.DoesNotContain(j.World.Rematches, r => r.Id == "dig_boils");
        Assert.Contains(StoryFights.Open(j.Ctx), f => f.Id == "dig");""", 1)
open(p, "w", encoding="utf-8", newline="").write(s)

p = "tests/VergeTests.cs"
s = open(p, encoding="utf-8").read()
old = """        Assert.Contains(s.J.World.Rematches, r => r.Id == "roost_raid");"""
assert old in s
s = s.replace(old, """        // Lost, it waits at the Roost for another night (not at the table).
        Assert.DoesNotContain(s.J.World.Rematches, r => r.Id == "roost_raid");
        Assert.True(Make(TimeOfDay.Night, s.J).Zone.Interactables.Single(i => i.Id == "night:roost").When!());""", 1)
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")
