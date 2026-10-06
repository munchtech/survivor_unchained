from ed import sub
sub('logic/Rpg/Crafting.cs', [
("""public enum Verb { Temper, WorkIn, Cage, Remake, Rekindle, BreakDown, Brew, Buy, Commission, Set }""",
"""public enum Verb { Temper, WorkIn, Cage, Remake, Rekindle, BreakDown, Brew, Buy, Commission, Set, Bind, Steep }"""),
("""public sealed class Easier { public Cond? When; public int HeatTop, TemperIron, EntryGrade; public string? Line, Needs; }""",
"""public sealed class Easier { public Cond? When; public int HeatTop, TemperIron, EntryGrade, Gold; public string? Line, Needs; }
/// <summary>The binder's terms: a shard and gold a grade bound, and the heat it costs the piece that takes it.</summary>
public sealed class BindRules { public int ShardsPerGrade = 1, GoldPerGrade = 40; public int[] Heat = { 5, 7 }; public string Crafter = "vonnra"; }
/// <summary>The one gamble (design 9): jars sold while the pump runs, and what steeping does, by weight.</summary>
public sealed class SlurryRules
{
    public string Jar = "slurry_jar", Crafter = "snib", Mark = "slurried";
    public int Gold = 30, PerDay = 3;
    public Cond? Sold;
    public Dictionary<string, int> Odds = new() { ["up"] = 25, ["slurry"] = 25, ["nothing"] = 30, ["down"] = 20 };
    public List<string> Affixes = new();
}"""),
("""    public Dictionary<string, SettingRule> Settings = new();""",
"""    public Dictionary<string, SettingRule> Settings = new();
    public BindRules Bind = new();
    public SlurryRules Slurry = new();"""),
("""    public string? Material;
    /// <summary>What is made""",
"""    public string? Material;
    /// <summary>The piece a binding unmakes for its power.</summary>
    public string? Donor;
    /// <summary>What a gamble came to, once done ("up", "slurry", "nothing", "down").</summary>
    public string? Outcome;
    /// <summary>What is made"""),
("""    static (int HeatTop, int TemperIron, int EntryGrade) Terms(string crafter, Ctx c)
    {
        int h = 0, i = 0, g = 0;
        foreach (var e in Crafter(crafter)?.Easier ?? new())
            if (World.Rules.Test(e.When, c)) { h += e.HeatTop; i += e.TemperIron; g += e.EntryGrade; }
        return (h, i, g);
    }""",
"""    static (int HeatTop, int TemperIron, int EntryGrade) Terms(string crafter, Ctx c)
    {
        int h = 0, i = 0, g = 0;
        foreach (var e in Crafter(crafter)?.Easier ?? new())
            if (World.Rules.Test(e.When, c)) { h += e.HeatTop; i += e.TemperIron; g += e.EntryGrade; }
        return (h, i, g);
    }

    /// <summary>What the crafter's terms take off their prices, as a share (-0.1: a tenth less).</summary>
    static double GoldTerms(string crafter, Ctx c) =>
        (Crafter(crafter)?.Easier ?? new()).Where(e => e.Gold != 0 && World.Rules.Test(e.When, c)).Sum(e => e.Gold) / 100.0;"""),
("""            if (e.EntryGrade > 0) fx.Add($"what is worked in goes in {e.EntryGrade} grade{(e.EntryGrade > 1 ? "s" : "")} finer");""",
"""            if (e.EntryGrade > 0) fx.Add($"what is worked in goes in {e.EntryGrade} grade{(e.EntryGrade > 1 ? "s" : "")} finer");
            if (e.Gold < 0) fx.Add(e.Gold == -10 ? "a tenth off every price" : $"{-e.Gold}% off every price");"""),
("""    static int Price(CraftCtx x, string crafter, int gold) => gold <= 0 ? 0 : Math.Max(1, (int)Math.Ceiling(gold * x.PriceMod(crafter)));""",
"""    static int Price(CraftCtx x, string crafter, int gold) =>
        gold <= 0 ? 0 : Math.Max(1, (int)Math.Ceiling(gold * x.PriceMod(crafter) * (1 + GoldTerms(crafter, x.Ctx))));"""),
])
