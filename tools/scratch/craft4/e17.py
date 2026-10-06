from ed import sub

sub("data/content/crafting.json", [
("""    "breakDown": ["Back to iron.", "Scrap."],
""",
"""    "breakDown": ["Back to iron.", "Scrap."],
    "breakDown.legendary": ["Somebody made this. ...Fire, then.", "Good work, that. Was.", "Light comes out last. Always does."],
"""),
])
sub("tests/CraftingTests.cs", [
("""        Assert.True(j.Work(it.Uid, q, null));
        Assert.Equal(3, Inventory.Count(j.Ch, Crafting.Shard));
    }""",
"""        Assert.True(j.Work(it.Uid, q, null));
        Assert.Equal(3, Inventory.Count(j.Ch, Crafting.Shard));
        // At the forge, his own words over somebody's named work going back to the fire (the story lead's).
        var again = Piece(j, legendary.Id, 4);
        j.World.Npc("brannoc").Flags["first.breakDown"] = true;
        Assert.True(j.Work(again.Uid, Crafting.BreakDown(j.Craft, again, "brannoc"), null));
        Assert.Contains(j.CraftSaid?.Line, new[] { "Somebody made this. ...Fire, then.", "Good work, that. Was.", "Light comes out last. Always does." });
    }"""),
])
