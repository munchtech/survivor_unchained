from ed import sub
sub('tests/ContentTests.cs', [
("""["trade", "rest", "stash", "maps", "sell", "craft", "still", "leave",""",
"""["trade", "rest", "stash", "maps", "sell", "craft", "still", "slurry", "leave","""),
])
sub('logic/Play/Journey.cs', [
("""    public bool Service(string action, Battle? b)
    {
        var w = World;
        switch (action)
        {""",
"""    public bool Service(string action, Battle? b)
    {
        var w = World;
        switch (action)
        {
            // Snib's jars, bought in his hearing (docs/CRAFTING_DESIGN.md 9): the talk goes on.
            case "slurry":
            {
                var q = Crafting.BuyJar(Craft);
                if (!q.Ok) { Warn(q.Blocked!); return true; }
                Make(q);
                return true;
            }"""),
])
sub('logic/Play/JourneyCrafting.cs', [
("""        CraftSaid = q.Verb switch
        {
            Verb.Buy => CraftSaid,""",
"""        CraftSaid = q.Verb switch
        {
            Verb.Buy when q.Def == Crafting.Rules.Slurry.Jar => Crafting.Line(q.Crafter, "jar.sale") is { } js ? new Said(null, js, null) : null,
            Verb.Buy => CraftSaid,"""),
("""        string? sub = q.Verb switch
        {
            Verb.Brew => $"You carry {Inventory.Count(Ch, q.Def!)}",""",
"""        string? sub = q.Verb switch
        {
            Verb.Brew => $"You carry {Inventory.Count(Ch, q.Def!)}",
            Verb.Buy when q.Def == Crafting.Rules.Slurry.Jar => CraftSaid?.Line ?? $"You carry {Inventory.Count(Ch, q.Def!)}","""),
])
