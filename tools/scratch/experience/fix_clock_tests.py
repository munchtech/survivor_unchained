"""The clock tests: no spare test (the story lead's), the Roost as the road open by default."""
p = "tests/DayClockTests.cs"
s = open(p, encoding="utf-8").read()
start = s.index("    [Fact]\n    public void The_night_calls_the_storys_fight_from_anywhere")
end = s.index("    [Fact]\n    public void A_story_fight_lost_wakes_her_in_town")
new = '''    [Fact]
    public void The_night_calls_the_storys_fight_from_anywhere_and_its_spec_is_the_verges()
    {
        var j = Arrived();
        // The Roost stands open from the start (the violent road), but the night does not call it
        // until the story has pointed her at it.
        Assert.Contains(StoryFights.Open(j.Ctx), f => f.Id == "roost");
        Assert.Null(j.Tonight);
        j.Apply("""[{ "quest": { "id": "caravan", "status": "active", "entry": "roost_found" } }]""");
        Assert.Equal("roost", j.Tonight?.Id);
        var spec = StoryFights.Spec("roost", j.Ctx, "waystation", 3, 4, 0);
        Assert.True(spec.Story);
        Assert.Equal("roost_raid", spec.Id);
        Assert.Equal(("waystation", 3.0, 4.0), (spec.ReturnZone, spec.ReturnX, spec.ReturnZ));
        // The Dig turned on her is called at once, whatever else is open.
        j.World.Facts["dig.hostile"] = true;
        Assert.Contains(StoryFights.Called(j.Ctx), f => f.Id == "dig");
        // Every fight has a line for dusk, and so has a night with none.
        foreach (var f in StoryFights.All) Assert.True(Journey.DayLines.Tonight.ContainsKey(f.Id), f.Id);
        Assert.True(Journey.DayLines.Tonight.ContainsKey(""));
    }

'''
s = s[:start] + new + s[end:]
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")
