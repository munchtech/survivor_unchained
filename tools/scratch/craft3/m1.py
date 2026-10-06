"""Resolve Arena.cs: my Night call (minibosses, the cure) with the loot lead's tally after it, as they asked."""
from ed import sub
sub("logic/Arena/Arena.cs", [
    ("""<<<<<<< HEAD
        var carry = Crafting.Night(spec.People, spec.Tier, spec.Story, b.EmberLevel, Math.Max(0, b.Time / 60 - spec.Minutes), won, fell, b.ChampionsByFamily, b.MinibossesByFamily,
            cured: j.World.Fact("stream.clear").Truthy || j.World.Fact("beasts.outcome").Str == "cured");
=======
        var carry = Crafting.Night(spec.People, spec.Tier, spec.Story, b.EmberLevel, Math.Max(0, b.Time / 60 - spec.Minutes), won, fell, b.ChampionsByFamily);
        // What the carriers left""",
     """        var carry = Crafting.Night(spec.People, spec.Tier, spec.Story, b.EmberLevel, Math.Max(0, b.Time / 60 - spec.Minutes), won, fell, b.ChampionsByFamily, b.MinibossesByFamily,
            cured: j.World.Fact("stream.clear").Truthy || j.World.Fact("beasts.outcome").Str == "cured");
        // What the carriers left"""),
    ("""        j.NightTally.Clear();
>>>>>>> origin/claude/vigilant-galileo-l6jqyx
""", """        j.NightTally.Clear();
"""),
    ("""<<<<<<< HEAD
            TomeChoices = choices, Recorded = recorded, Carried = carry.Kept, Spilled = carry.Spilled, HaulSeen = glassSeen,
=======
            TomeChoices = choices, Recorded = recorded, Carried = carry.Kept, Spilled = carry.Spilled, Gathered = gathered,
>>>>>>> origin/claude/vigilant-galileo-l6jqyx
""", """            TomeChoices = choices, Recorded = recorded, Carried = carry.Kept, Spilled = carry.Spilled, Gathered = gathered, HaulSeen = glassSeen,
"""),
])
