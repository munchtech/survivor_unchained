W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "logic/Maps/Charts.cs": [
        ("""using System.Linq;
using SurvivorUnchained.Core;""", """using System.Linq;
using System.Text.Json.Serialization;
using SurvivorUnchained.Core;"""),
        ("""    public int Level => 8 + 2 * Tier;""", """    [JsonIgnore] public int Level => 8 + 2 * Tier;"""),
        ("""    public int ItemLevel => Math.Min(40, Level);""", """    [JsonIgnore] public int ItemLevel => Math.Min(40, Level);"""),
        ("""    public IEnumerable<ChartMod> Rolled => Mods.Select(Charts.Mod);
    public double Quantity => 1 + Rolled.Sum(m => m.Quantity) + Quality * 0.01;
    public double RarityBonus => 1 + Rolled.Sum(m => m.Rarity);
    public double PackSize => 1 + Rolled.Sum(m => m.PackSize);""",
         """    [JsonIgnore] public IEnumerable<ChartMod> Rolled => Mods.Select(Charts.Mod);
    [JsonIgnore] public double Quantity => 1 + Rolled.Sum(m => m.Quantity) + Quality * 0.01;
    [JsonIgnore] public double RarityBonus => 1 + Rolled.Sum(m => m.Rarity);
    [JsonIgnore] public double PackSize => 1 + Rolled.Sum(m => m.PackSize);"""),
        ("""    public MapSpec Map => new()""", """    [JsonIgnore] public MapSpec Map => new()"""),
    ],
    W + "logic/Rpg/Character.cs": [
        ("""    /// <summary>How often its three coals have been drawn again today.</summary>
    public int? Draw;
}""", """    /// <summary>How often its three coals have been drawn again today.</summary>
    public int? Draw;
    /// <summary>A Wayfinder's chart: the map it opens (docs/SKILLS_DESIGN.md §17.2).</summary>
    public Maps.Chart? Chart;
}"""),
    ],
    W + "logic/Play/Journey.cs": [
        ("""        if (p.Kind is PickupKind.Item or PickupKind.Material or PickupKind.Quest && p.Ref != null)
        {""", """        // A chart carries its map in its name until it is in the pack.
        if (p.Kind == PickupKind.Item && p.Ref != null && Maps.Charts.FromRef(p.Ref) is { } chart)
            return GiveChart(chart);
        if (p.Kind is PickupKind.Item or PickupKind.Material or PickupKind.Quest && p.Ref != null)
        {"""),
        ("""    public bool GiveItem(string defId, int qty = 1, int? rarity = null, IReadOnlyCollection<string>? lean = null, bool dropped = false)
    {""", """    /// <summary>A Wayfinder's chart into the pack.</summary>
    public bool GiveChart(Maps.Chart chart)
    {
        var it = Inventory.Make(Ch, Maps.Charts.Item, 1, chart.Rarity);
        it.Chart = chart;
        it.Name = Maps.Charts.Title(chart);
        if (!Inventory.AddToPack(Ch, it)) { OnToast(new Toast(ToastKind.Warning, "Your pack is full", it.Name)); return false; }
        OnToast(new Toast(ToastKind.Loot, it.Name, Items.Get(Maps.Charts.Item).Description, Items.Get(Maps.Charts.Item).Icon, it.Rarity));
        OnTouch();
        return true;
    }

    public bool GiveItem(string defId, int qty = 1, int? rarity = null, IReadOnlyCollection<string>? lean = null, bool dropped = false)
    {"""),
    ],
}
