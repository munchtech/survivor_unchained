from ed import sub
sub('logic/Rpg/Crafting.cs', [
("""    public string? Def;
    public int Count = 1;""",
"""    public string? Def;
    public int Count = 1;
    /// <summary>The grade an affix goes in at (work in), when the crafter's standing lifts it.</summary>
    public int Grade = -1;"""),
("""    /// <summary>Why a crafter will not work for the survivor now (null: they will).</summary>
    public static string? Closed(string crafter, Ctx c)
    {
        var d = Crafter(crafter);
        if (d == null) return "Nobody here does that.";
        if (!World.Rules.Test(d.When, c)) return d.ClosedLine ?? $"{d.Name} will not work for you yet.";
        if (d.Closed != null && World.Rules.Test(d.Closed, c)) return d.ClosedLine ?? $"{d.Name} is not working now.";
        return null;
    }""",
"""    /// <summary>Why a crafter will not work for the survivor now, or not at that verb yet (null: they will).</summary>
    public static string? Closed(string crafter, Ctx c, Verb? v = null)
    {
        var d = Crafter(crafter);
        if (d == null) return "Nobody here does that.";
        if (!World.Rules.Test(d.When, c)) return d.ClosedLine ?? $"{d.Name} will not work for you yet.";
        if (d.Closed != null && World.Rules.Test(d.Closed, c)) return d.ClosedLine ?? $"{d.Name} is not working now.";
        if (v is Verb verb && d.Gates.TryGetValue(verb.Key(), out var g) && !World.Rules.Test(g.When, c)) return g.Line ?? $"{d.Name} will not do that yet.";
        return null;
    }"""),
("""    public static Said? Speak(CraftCtx x, string crafter, Verb v)
    {
        if (Crafter(crafter) is null) return null;
        string key = v.Key();
        var n = x.World.Npc(crafter);""",
"""    public static Said? Speak(CraftCtx x, string crafter, Verb v, string? moment = null)
    {
        if (Crafter(crafter) is null) return null;
        string key = v.Key();
        var n = x.World.Npc(crafter);
        // A moment of its own, said once ("brew.moonpetal": the first moonpetal draught).
        if (moment != null && !n.Flag($"said.{moment}").Truthy && Line(crafter, moment) is { } once)
        {
            n.Flags[$"said.{moment}"] = true;
            n.Flags[$"first.{key}"] = true;
            return new Said(Line(crafter, $"{moment}.before"), once, Line(crafter, $"{moment}.after"));
        }"""),
("""    static (int HeatTop, int TemperIron) Terms(string crafter, Ctx c)
    {
        int h = 0, i = 0;
        foreach (var e in Crafter(crafter)?.Easier ?? new())
            if (World.Rules.Test(e.When, c)) { h += e.HeatTop; i += e.TemperIron; }
        return (h, i);
    }""",
"""    static (int HeatTop, int TemperIron, int EntryGrade) Terms(string crafter, Ctx c)
    {
        int h = 0, i = 0, g = 0;
        foreach (var e in Crafter(crafter)?.Easier ?? new())
            if (World.Rules.Test(e.When, c)) { h += e.HeatTop; i += e.TemperIron; g += e.EntryGrade; }
        return (h, i, g);
    }"""),
("""            if (e.TemperIron < 0) fx.Add($"tempering takes {Items.Several(Iron, -e.TemperIron)} less");
            string? needs = e.When?.Rel is { Gte: double g } r ? $"{r.Axis.ToString().ToLowerInvariant()} {g:0}" : null;""",
"""            if (e.TemperIron < 0) fx.Add($"tempering takes {Items.Several(Iron, -e.TemperIron)} less");
            if (e.EntryGrade > 0) fx.Add($"what is worked in goes in {e.EntryGrade} grade{(e.EntryGrade > 1 ? "s" : "")} finer");
            string? needs = e.Needs ?? (e.When?.Rel is { Gte: double g } r ? $"{r.Axis.ToString().ToLowerInvariant()} {g:0}" : null);"""),
("""        // A banked forge quotes, so the survivor can plan by night, but does nothing.
        if (q.Crafter != "" && Closed(q.Crafter, x.Ctx) is { } shut) { q.Blocked = shut; return; }""",
"""        // A banked forge quotes, so the survivor can plan by night, but does nothing.
        if (q.Crafter != "" && Closed(q.Crafter, x.Ctx, q.Verb) is { } shut) { q.Blocked = shut; return; }"""),
("""        var (top, less) = Terms(crafter, x.Ctx);
        if (index < 0 || index >= it.Affixes.Count) { q.Blocked = "Choose what to temper."; return q; }""",
"""        var (top, less, _) = Terms(crafter, x.Ctx);
        if (index < 0 || index >= it.Affixes.Count) { q.Blocked = "Choose what to temper."; return q; }"""),
("""        int tier = EntryGrade(it);
        q.Title = $"Work in {Items.Find(material)?.Name ?? material}";""",
"""        var (top, _, finer) = Terms(crafter, x.Ctx);
        int tier = q.Grade = Math.Min(Math.Max(Cap(it), EntryGrade(it)), EntryGrade(it) + finer);
        q.Title = $"Work in {Items.Find(material)?.Name ?? material}";"""),
("""        if (it.Affixes.Where((a, i) => i != replace).Any(a => a.Id == affix)) q.Blocked ??= "It already has that.";
        var (top, _) = Terms(crafter, x.Ctx);""",
"""        if (it.Affixes.Where((a, i) => i != replace).Any(a => a.Id == affix)) q.Blocked ??= "It already has that.";"""),
("""        q.After = a?.Text(0);
        var (top, _) = Terms(crafter, x.Ctx);""",
"""        q.After = a?.Text(0);
        var (top, _, _) = Terms(crafter, x.Ctx);"""),
("""                var roll = new AffixRoll { Id = q.Affix!, Tier = EntryGrade(it) };""",
"""                var roll = new AffixRoll { Id = q.Affix!, Tier = q.Grade >= 0 ? q.Grade : EntryGrade(it) };"""),
])
