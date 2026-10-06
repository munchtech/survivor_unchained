from ed import sub
sub('logic/Rpg/Crafting.cs', [
("""    public static Quote Steep(CraftCtx x, ItemInstance it)
    {
        var s = Rules.Slurry;
        var q = Begin(Verb.Steep, "", "Steep in slurry");""",
"""    public static Quote Steep(CraftCtx x, ItemInstance it, string crafter = "")
    {
        var s = Rules.Slurry;
        // At Snib's bench he does it, in his words; from the pack, by the survivor's own hand (a jar
        // kept past the cure still steeps).
        var q = Begin(Verb.Steep, crafter, "Steep in slurry");"""),
("""        else if (Inventory.Count(x.Ch, s.Jar) < 1) q.Blocked = "You have no slurry.";
        q.HeatLo = q.HeatHi = it.Heat ?? 0;
        q.After = "It is set for good after, whatever it comes to.";
        return q;""",
"""        else if (Inventory.Count(x.Ch, s.Jar) < 1) q.Blocked = "You have no slurry.";
        q.HeatLo = q.HeatHi = it.Heat ?? 0;
        q.After = "It is set for good after, whatever it comes to.";
        if (q.Blocked == null && crafter != "" && Closed(crafter, x.Ctx, Verb.Steep) is { } shut) q.Blocked = shut;
        return q;"""),
("""        if (q.Verb == Verb.Steep)
        {
            if (Inventory.Count(ch, Rules.Slurry.Jar) < 1 || Slurried(it)) return false;""",
"""        if (q.Verb == Verb.Steep)
        {
            if (Inventory.Count(ch, Rules.Slurry.Jar) < 1 || Slurried(it) || q.Crafter != "" && Closed(q.Crafter, x.Ctx, q.Verb) is not null) return false;"""),
])
sub('logic/Play/JourneyCrafting.cs', [
("""        if (q.Crafter != "") CraftSaid = Crafting.Speak(Craft, q.Crafter, q.Verb, moment);
        var def = Items.Get(it.Def);
        string? sub = q.Verb switch
        {
            Verb.BreakDown => string.Join(", ", q.Gives.Select(kv => $"{kv.Value} {Items.Get(kv.Key).Name}")),""",
"""        if (q.Crafter != "") CraftSaid = Crafting.Speak(Craft, q.Crafter, q.Verb, moment);
        // The slurry's outcome is said as what the survivor sees (the story lead's narration), after
        // whatever Snib says over it.
        string? seen = q.Verb == Verb.Steep ? Crafting.Line(Crafting.Rules.Slurry.Crafter, $"steep.{q.Outcome}") : null;
        if (seen != null) CraftSaid = (CraftSaid ?? new Said(null, null, null)) with { After = seen };
        var def = Items.Get(it.Def);
        string? sub = q.Verb switch
        {
            Verb.BreakDown => string.Join(" and ", q.Gives.Select(kv => Items.Several(kv.Key, kv.Value))),
            Verb.Steep => seen ?? "Steeped: it is set for good.",
            Verb.Bind => $"{q.After}. What it came from is gone.","""),
])
