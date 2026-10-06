from ed import sub
from js import load, save
sub('tests/CraftingTests.cs', [
("""    [Fact]
    public void Wenna_will_not_work_gear_while_the_stream_is_green()
    {
        var j = Make();
        j.World.Npc("wenna").Flags["met"] = true;
        Assert.NotNull(Crafting.Closed("wenna", j.Ctx));
        j.World.Facts["stream.clear"] = true;
        Assert.Null(Crafting.Closed("wenna", j.Ctx));
    }""",
"""    [Fact]
    public void Wenna_brews_from_the_start_but_will_not_work_gear_while_the_stream_is_green()
    {
        var j = Make();
        j.World.Npc("wenna").Flags["met"] = true;
        Assert.Null(Crafting.Closed("wenna", j.Ctx, Verb.Brew));
        Assert.NotNull(Crafting.Closed("wenna", j.Ctx, Verb.WorkIn));
        j.World.Facts["stream.clear"] = true;
        Assert.Null(Crafting.Closed("wenna", j.Ctx, Verb.WorkIn));
    }"""),
])
sub('tests/ContentTests.cs', [
("""    static readonly HashSet<string> Actions = ["trade", "rest", "stash", "maps", "sell", "craft", "leave", "fortune", "bounty", "sellpelts", "reforge", "travel_verge"];""",
"""    static readonly HashSet<string> Actions = ["trade", "rest", "stash", "maps", "sell", "craft", "still", "leave", "fortune", "bounty", "sellpelts", "reforge", "travel_verge"];"""),
])
sub('logic/Rpg/Crafting.cs', [
("""            w.Facts["commission.ready"] = ready;
            // Ready by morning: then it shows over the smith's head.
            w.Scheduled.Add(new ScheduledChange { Day = ready, Id = "commission.done", Effect = new() { new Change { Set = new() { ["commission.done"] = true } } } });
        }""",
"""            w.Facts["commission.ready"] = ready;
        }"""),
("""    /// <summary>The morning after: what was ordered, handed over""",
"""    /// <summary>A new morning: a commission due today is done, and shows over the smith's head.</summary>
    public static void Morning(WorldState w)
    {
        if (Ordered(w) is { } o && w.Day >= o.Ready) w.Facts["commission.done"] = true;
    }

    /// <summary>The morning after: what was ordered, handed over"""),
])
sub('logic/Play/Journey.cs', [
("""        if (Flask() is { } flask) lines.Add(flask);""",
"""        if (Flask() is { } flask) lines.Add(flask);
        Crafting.Morning(World);"""),
])
d = load("items")
d["items"]["greymuzzle_fang"]["tags"] = ["greymuzzle_fang"]
save("items", d)
sub('src/Ui/ItemViews.cs', [
("""        ["wolf_fang"] = "A statement to any wolf that sees it.",""",
"""        ["wolf_fang"] = "A statement to any wolf that sees it.",
        ["greymuzzle_fang"] = "The Pack knows it by sight.","""),
])
