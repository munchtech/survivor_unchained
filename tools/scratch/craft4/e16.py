from ed import sub

sub("logic/Play/JourneyCrafting.cs", [
("""        string before = Inventory.Name(it);
        int heat = it.Heat ?? 0;
        if (!Crafting.Do(Craft, it, q, craftRng)) { Warn("It could not be done."); return false; }
        // A trophy set has its own words, said the once ("fang.set").
        string? moment = q.Verb == Verb.Set && Crafting.Rules.Settings.GetValueOrDefault(q.Def ?? "") is { } s ? $"{s.Moment}.set" : null;
        if (q.Crafter != "") CraftSaid = Crafting.Speak(Craft, q.Crafter, q.Verb, moment);""",
"""        string before = Inventory.Name(it);
        int heat = it.Heat ?? 0;
        // A Legendary broken has the smith's own words over it, where there are any ("Scrap." would not do).
        bool legendary = q.Verb == Verb.BreakDown && Rpg.Drops.TierOf(it) == LootTier.Legendary;
        if (!Crafting.Do(Craft, it, q, craftRng)) { Warn("It could not be done."); return false; }
        // A trophy set has its own words, said the once ("fang.set").
        string? moment = q.Verb == Verb.Set && Crafting.Rules.Settings.GetValueOrDefault(q.Def ?? "") is { } s ? $"{s.Moment}.set" : null;
        if (q.Crafter != "") CraftSaid = Crafting.Speak(Craft, q.Crafter, q.Verb, moment, legendary ? "breakDown.legendary" : null);"""),
])
